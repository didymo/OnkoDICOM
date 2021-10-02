import os
import platform
from pathlib import Path

from PySide6 import QtCore
from pydicom import dcmread

from src.Model import ImageLoading
from src.Model.PTCTDictContainer import PTCTDictContainer
from src.Model.GetPatientInfo import DicomTree
from src.Model.PTCTModel import create_pt_ct_model

from src.View.ImageLoader import ImageLoader


class PTCTImageLoader(ImageLoader):
    """
    This class is responsible for initializing and creating all the values
    required to create an instance of the PatientDictContainer, that is
    used to store all the DICOM-related data used to create the patient window.
    """

    signal_request_calc_dvh = QtCore.Signal()

    def __init__(self, *args, **kwargs):
        super(PTCTImageLoader, self).__init__(*args, **kwargs)

    def load(self, interrupt_flag, progress_callback):
        """
        :param interrupt_flag: A threading.Event() object that tells the
        function to stop loading.

        :param progress_callback: A signal that receives the current
        progress of the loading.

        :return: PatientDictContainer object containing all values related
        to the loaded DICOM files.
        """
        progress_callback.emit(("Creating datasets...", 0))
        try:
            # Gets the common root folder.
            path = os.path.dirname(os.path.commonprefix(self.selected_files))
            read_data_dict, file_names_dict = ImageLoading.get_datasets(
                self.selected_files)
        except ImageLoading.NotAllowedClassError:
            raise ImageLoading.NotAllowedClassError

        # Populate the initial values in the PatientDictContainer singleton.
        progress_callback.emit(("Populate Dictionary...", 25))
        pt_ct_dict_container = PTCTDictContainer()
        pt_ct_dict_container.clear()
        pt_ct_dict_container.set_initial_values(
            path,
            read_data_dict,
            file_names_dict,
            existing_rtss_files=self.existing_rtss
        )

        if interrupt_flag.is_set():
            print("stopped")
            return False

        progress_callback.emit(("Finding PT Files...", 37.5))
        pt_data_dict, pt_names_dict = ImageLoading.get_datasets(
            self.selected_files, "PT")
        progress_callback.emit(("Finding CT Files...", 45))
        ct_data_dict, ct_names_dict = ImageLoading.get_datasets(
            self.selected_files, "CT")

        progress_callback.emit(("Storing PT and CT data...", 50))
        pt_ct_dict_container.set_sorted_files(pt_data_dict, ct_data_dict)
        progress_callback.emit(("Loading Images", 75))
        create_pt_ct_model()
        if interrupt_flag.is_set():  # Stop loading.
            progress_callback.emit(("Stopping", 85))
            return False

        return True
