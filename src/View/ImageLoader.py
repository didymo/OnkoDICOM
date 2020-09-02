import os
import platform

from PyQt5 import QtCore
from PyQt5.QtCore import QObject
from pydicom import dcmread

from src.Model import ImageLoading
from src.Model.PatientDictContainer import PatientDictContainer


class ImageLoader(QObject):
    """
    This class is responsible for initializing and creating all the values required to create an instance of
    the PatientDictContainer, that is used to store all the DICOM-related data used to create the patient window.
    """

    def __init__(self, selected_files, parent_window, *args, **kwargs):
        super(ImageLoader, self).__init__(*args, **kwargs)
        self.selected_files = selected_files
        self.parent_window = parent_window

    def load(self, interrupt_flag, progress_callback):
        """
        :param interrupt_flag: A threading.Event() object that tells the function to stop loading.
        :param progress_callback: A signal that receives the current progress of the loading.
        :return: PatientDictContainer object containing all values related to the loaded DICOM files.
        """
        progress_callback.emit(("Creating datasets...", 0))
        try:
            path = os.path.dirname(os.path.commonprefix(self.selected_files))  # Gets the common root folder.
        except ImageLoading.NotAllowedClassError:
            raise ImageLoading.NotAllowedClassError
        read_data_dict, file_names_dict = ImageLoading.get_datasets(self.selected_files)
        # if not ImageLoading.is_dataset_dicom_rt(read_data_dict):
        #    raise ImageLoading.NotRTSetError

        # As there is no way to interrupt a QRunnable, this method must check after every step whether or not the
        # interrupt flag has been set, in which case it will interrupt this method after the currently processing
        # function has finished running. It's not very pretty, and the thread will still run some functions for, in some
        # cases, up to a couple seconds after the close button on the Progress Window has been clicked, however it's
        # the best solution I could come up with. If you have a cleaner alternative, please make your contribution.
        if interrupt_flag.is_set():
            print("stopped")
            return

        if 'rtss' in file_names_dict:
            dataset_rtss = dcmread(file_names_dict['rtss'])

            progress_callback.emit(("Getting ROI info...", 10))
            rois = ImageLoading.get_roi_info(dataset_rtss)

            if interrupt_flag.is_set():  # Stop loading.
                print("stopped")
                return

            progress_callback.emit(("Getting contour data...", 30))
            dict_raw_contour_data, dict_numpoints = ImageLoading.get_raw_contour_data(dataset_rtss)

            if interrupt_flag.is_set():  # Stop loading.
                print("stopped")
                return

            progress_callback.emit(("Getting pixel LUTs...", 50))
            dict_pixluts = ImageLoading.get_pixluts(read_data_dict)

            if interrupt_flag.is_set():  # Stop loading.
                print("stopped")
                return

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
                    raw_dvh = ImageLoading.calc_dvhs(dataset_rtss, dataset_rtdose, rois, interrupt_flag)

                if interrupt_flag.is_set():  # Stop loading.
                    print("stopped")
                    return

                progress_callback.emit(("Converging to zero...", 80))
                dvh_x_y = ImageLoading.converge_to_0_dvh(raw_dvh)

                if interrupt_flag.is_set():  # Stop loading.
                    print("stopped")
                    return

                return PatientDictContainer(path, read_data_dict, file_names_dict, rois=rois, raw_dvh=raw_dvh,
                                            dvh_x_y=dvh_x_y, raw_contour=dict_raw_contour_data,
                                            num_points=dict_numpoints, pixluts=dict_pixluts)

            else:
                return PatientDictContainer(path, read_data_dict, file_names_dict, rois=rois,
                                            raw_contour=dict_raw_contour_data, num_points=dict_numpoints,
                                            pixluts=dict_pixluts)

        return PatientDictContainer(path, read_data_dict, file_names_dict)
