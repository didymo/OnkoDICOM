import os
import platform

from PyQt5 import QtCore
from PyQt5.QtCore import QObject
from pydicom import dcmread

from src.Model import ImageLoading
from src.Model.PatientDictContainer import PatientDictContainer


class ImageLoader(QObject):

    def __init__(self, selected_files, *args, **kwargs):
        super(ImageLoader, self).__init__(*args, **kwargs)
        self.selected_files = selected_files

    def load(self, progress_callback):
        progress_callback.emit(("Creating datasets...", 0))
        try:
            path = os.path.dirname(os.path.commonprefix(self.selected_files))  # Gets the common root folder.
        except ImageLoading.NotAllowedClassError:
            raise ImageLoading.NotAllowedClassError
        read_data_dict, file_names_dict = ImageLoading.get_datasets(self.selected_files)
        # if not ImageLoading.is_dataset_dicom_rt(read_data_dict):
        #    raise ImageLoading.NotRTSetError

        if 'rtss' in file_names_dict:
            dataset_rtss = dcmread(file_names_dict['rtss'])

            progress_callback.emit(("Getting ROI info...", 10))
            rois = ImageLoading.get_roi_info(dataset_rtss)

            progress_callback.emit(("Getting contour data...", 30))
            dict_raw_contour_data, dict_numpoints = ImageLoading.get_raw_contour_data(dataset_rtss)

            progress_callback.emit(("Getting pixel LUTs...", 50))
            dict_pixluts = ImageLoading.get_pixluts(read_data_dict)

            if 'rtdose' in file_names_dict:
                dataset_rtdose = dcmread(file_names_dict['rtdose'])

                # Spawn-based platforms (i.e Windows and MacOS) have a large overhead when creating a new process, which
                # ends up making multiprocessing on these platforms more expensive than linear calculation. As such,
                # multiprocessing is only available on Linux until a better solution is found.
                fork_safe_platforms = ['Linux']
                if platform.system() in fork_safe_platforms:
                    progress_callback.emit(("Calculating DVHs...", 60))
                    raw_dvh = ImageLoading.multi_calc_dvh(dataset_rtss, dataset_rtdose, rois)
                else:
                    progress_callback.emit(("Calculating DVHs... (This may take a while)", 60))
                    raw_dvh = ImageLoading.calc_dvhs(dataset_rtss, dataset_rtdose, rois)

                progress_callback.emit(("Converging to zero...", 80))
                dvh_x_y = ImageLoading.converge_to_0_dvh(raw_dvh)

                return PatientDictContainer(path, read_data_dict, file_names_dict, rois=rois, raw_dvh=raw_dvh,
                                            dvh_x_y=dvh_x_y, raw_contour=dict_raw_contour_data,
                                            num_points=dict_numpoints, pixluts=dict_pixluts)

            else:
                return PatientDictContainer(path, read_data_dict, file_names_dict, rois=rois,
                                            raw_contour=dict_raw_contour_data, num_points=dict_numpoints,
                                            pixluts=dict_pixluts)

        return PatientDictContainer(path, read_data_dict, file_names_dict)
