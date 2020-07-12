import os
import platform

from PyQt5 import QtCore
from PyQt5.QtCore import QObject
from pydicom import dcmread

from src.Model import ImageLoading


class ImageLoader(QObject):
    signal_progress = QtCore.pyqtSignal(str)
    signal_finished = QtCore.pyqtSignal(tuple)

    def __init__(self, selected_files, *args, **kwargs):
        super(ImageLoader, self).__init__(*args, **kwargs)
        self.selected_files = selected_files

    def load(self):
        self.signal_progress.emit("Creating datasets...")
        path = os.path.dirname(os.path.commonprefix(self.selected_files))  # Gets the common root folder.
        read_data_dict, file_names_dict = ImageLoading.get_datasets(self.selected_files)
        if not ImageLoading.is_dataset_dicom_rt(read_data_dict):
            raise ImageLoading.NotRTSetError

        dataset_rtss = dcmread(file_names_dict['rtss'])
        dataset_rtdose = dcmread(file_names_dict['rtdose'])

        self.signal_progress.emit("Getting ROI info...")
        rois = ImageLoading.get_roi_info(dataset_rtss)

        # Spawn-based platforms (i.e Windows and MacOS) have a large overhead when creating a new process, which
        # ends up making multiprocessing on these platforms more expensive than linear calculation. As such,
        # multiprocessing is only available on Linux until a better solution is found.
        self.signal_progress.emit("Calculating DVHs...")
        fork_safe_platforms = ['Linux']
        if platform.system() in fork_safe_platforms:
            raw_dvh = ImageLoading.multi_calc_dvh(dataset_rtss, dataset_rtdose, rois)
        else:
            raw_dvh = ImageLoading.calc_dvhs(dataset_rtss, dataset_rtdose, rois)
        dvh_x_y = ImageLoading.converge_to_0_dvh(raw_dvh)

        self.signal_progress.emit("Getting contour data...")
        dict_raw_contour_data, dict_numpoints = ImageLoading.get_raw_contour_data(dataset_rtss)

        self.signal_progress.emit("Getting pixluts...")
        dict_pixluts = ImageLoading.get_pixluts(read_data_dict)

        return path, read_data_dict, file_names_dict, rois, raw_dvh, dvh_x_y, dict_raw_contour_data, dict_numpoints,\
            dict_pixluts
