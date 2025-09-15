import os
import platform
from pathlib import Path

from PySide6 import QtCore
from pydicom import dcmread

from src.Model import ImageLoading
from src.Model.MovingDictContainer import MovingDictContainer
from src.Model.MovingModel import create_moving_model
from src.Model.ROI import create_initial_rtss_from_ct
from src.Model.GetPatientInfo import DicomTree

from src.View.ImageLoader import ImageLoader


class MovingImageLoader(ImageLoader):
    """
    Loader for moving image datasets.
    Provides modular methods to load specific pieces of data for
    both auto-fusion and manual fusion workflows.
    """

    signal_request_calc_dvh = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super(MovingImageLoader, self).__init__(*args, **kwargs)

    def get_common_path_and_datasets(self):
        path = os.path.dirname(os.path.commonprefix(self.selected_files))
        read_data_dict, file_names_dict = ImageLoading.get_datasets(
            self.selected_files
        )
        return path, read_data_dict, file_names_dict

    def init_container(self, path, read_data_dict, file_names_dict):
        moving_dict_container = MovingDictContainer()
        moving_dict_container.clear()
        moving_dict_container.set_initial_values(
            path,
            read_data_dict,
            file_names_dict,
            existing_rtss_files=self.existing_rtss
        )
        return moving_dict_container

    def handle_rtss(self, file_names_dict, read_data_dict, moving_dict_container):
        dataset_rtss = dcmread(file_names_dict['rtss'])

        rois = ImageLoading.get_roi_info(dataset_rtss)
        dict_raw_contour_data, dict_numpoints = ImageLoading.get_raw_contour_data(dataset_rtss)
        dict_thickness = ImageLoading.get_thickness_dict(dataset_rtss, read_data_dict)
        dict_pixluts = ImageLoading.get_pixluts(read_data_dict)

        moving_dict_container.set("rois", rois)
        moving_dict_container.set("raw_contour", dict_raw_contour_data)
        moving_dict_container.set("num_points", dict_numpoints)
        moving_dict_container.set("pixluts", dict_pixluts)

        return dataset_rtss, rois, dict_thickness

    def handle_dvh(self, dataset_rtss, rois, dict_thickness,
                   file_names_dict, moving_dict_container, interrupt_flag):
        dataset_rtdose = dcmread(file_names_dict['rtdose'])

        fork_safe_platforms = ['Linux']
        if platform.system() in fork_safe_platforms:
            raw_dvh = ImageLoading.multi_calc_dvh(dataset_rtss, dataset_rtdose, rois, dict_thickness)
        else:
            raw_dvh = ImageLoading.calc_dvhs(dataset_rtss, dataset_rtdose, rois,
                                             dict_thickness, interrupt_flag)

        dvh_x_y = ImageLoading.converge_to_0_dvh(raw_dvh)

        moving_dict_container.set("raw_dvh", raw_dvh)
        moving_dict_container.set("dvh_x_y", dvh_x_y)
        moving_dict_container.set("dvh_outdated", False)

        return True

    def create_model_and_rtss(self, path):
        create_moving_model()
        return self.load_temp_rtss(path)

    def load_temp_rtss(self, path):
        moving_dict_container = MovingDictContainer()
        rtss_path = Path(path).joinpath('rtss.dcm')
        uid_list = ImageLoading.get_image_uid_list(moving_dict_container.dataset)
        rtss = create_initial_rtss_from_ct(moving_dict_container.dataset[0], rtss_path, uid_list)

        rois = ImageLoading.get_roi_info(rtss)
        moving_dict_container.set("rois", rois)

        dict_pixluts = ImageLoading.get_pixluts(moving_dict_container.dataset)
        moving_dict_container.set("pixluts", dict_pixluts)

        moving_dict_container.filepaths['rtss'] = rtss_path
        moving_dict_container.dataset['rtss'] = rtss

        moving_dict_container.set("file_rtss", rtss_path)
        moving_dict_container.set("dataset_rtss", rtss)
        ordered_dict = DicomTree(None).dataset_to_dict(rtss)
        moving_dict_container.set("dict_dicom_tree_rtss", ordered_dict)
        moving_dict_container.set("selected_rois", [])

        return True

    # Main Loader
    def load(self, interrupt_flag, progress_callback):
        progress_callback.emit(("Creating datasets...", 0))
        try:
            path, read_data_dict, file_names_dict = self.get_common_path_and_datasets()
        except ImageLoading.NotAllowedClassError:
            raise ImageLoading.NotAllowedClassError

        moving_dict_container = self.init_container(path, read_data_dict, file_names_dict)

        if interrupt_flag.is_set():
            return False

        if 'rtss' in file_names_dict and 'rtdose' in file_names_dict:
            self.parent_window.signal_advise_calc_dvh.connect(self.update_calc_dvh)
            self.signal_request_calc_dvh.emit()
            while not self.advised_calc_dvh:
                pass

        if 'rtss' in file_names_dict:
            progress_callback.emit(("Getting ROI + Contour data...", 10))
            dataset_rtss, rois, dict_thickness = self.handle_rtss(
                file_names_dict, read_data_dict, moving_dict_container
            )

            if interrupt_flag.is_set():
                return False

            if 'rtdose' in file_names_dict and self.calc_dvh:
                progress_callback.emit(("Calculating DVHs...", 60))
                ok = self.handle_dvh(dataset_rtss, rois, dict_thickness,
                                     file_names_dict, moving_dict_container,
                                     interrupt_flag)
                if not ok or interrupt_flag.is_set():
                    return False
            create_moving_model()
        else:
            progress_callback.emit(("Generating temporary rtss...", 20))
            ok = self.create_model_and_rtss(path)
            if not ok or interrupt_flag.is_set():
                return False

        progress_callback.emit(("Loading Moving Model", 85))
        if interrupt_flag.is_set():
            progress_callback.emit(("Stopping", 85))
            return False

        return True

    # manual fusion loader
    def load_manual_mode(self, interrupt_flag, progress_callback):
            progress_callback.emit(("Generating Moving Model", 60))
            try:
                path, read_data_dict, file_names_dict = self.get_common_path_and_datasets()
            except ImageLoading.NotAllowedClassError:
                raise ImageLoading.NotAllowedClassError

            moving_dict_container = self.init_container(path, read_data_dict, file_names_dict)

            if interrupt_flag.is_set():
                return False

            if 'rtss' in file_names_dict and 'rtdose' in file_names_dict:
                self.parent_window.signal_advise_calc_dvh.connect(self.update_calc_dvh)
                self.signal_request_calc_dvh.emit()
                while not self.advised_calc_dvh:
                    pass

            if 'rtss' in file_names_dict:
                progress_callback.emit(("Getting ROI + Contour data...", 65))
                dataset_rtss, rois, dict_thickness = self.handle_rtss(
                    file_names_dict, read_data_dict, moving_dict_container
                )

                if interrupt_flag.is_set():
                    return False

                if 'rtdose' in file_names_dict and self.calc_dvh:
                    progress_callback.emit(("Calculating DVHs...", 75))
                    ok = self.handle_dvh(dataset_rtss, rois, dict_thickness,
                                        file_names_dict, moving_dict_container,
                                        interrupt_flag)
                    if not ok or interrupt_flag.is_set():
                        return False
                create_moving_model()
            else:
                progress_callback.emit(("Generating temporary rtss...", 80))
                ok = self.create_model_and_rtss(path)
                if not ok or interrupt_flag.is_set():
                    return False

            progress_callback.emit(("Loading Moving Model", 85))
            if interrupt_flag.is_set():
                progress_callback.emit(("Stopping", 85))
                return False

            return True
