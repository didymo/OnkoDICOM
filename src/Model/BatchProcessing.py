from src.View.ImageLoader import ImageLoader
from pathlib import Path
import os
from src.Model.GetPatientInfo import DicomTree
from src.Model.ISO2ROI import ISO2ROI
from src.Model import ImageLoading
from src.Model import InitialModel
from src.Model import ROI
from src.View.ProgressWindow import ProgressWindow

from pydicom import dcmread
from src.Model.PatientDictContainer import PatientDictContainer


class BatchProcessingController:

    def __init__(self, dicom_structure, processes):
        self.dicom_structure = dicom_structure
        self.processes = processes

        self.progress_window = ProgressWindow(None)
        self.progress_window.signal_error.connect(self.on_loading_error)
        self.progress_window.signal_loaded.connect(self.on_loaded)

    def start_processing(self):
        #self.progress_window.start(self.perform_processes)
        self.perform_processes(None)

    def perform_processes(self, interrupt_flag, progress_callback=None):
        for patient in self.dicom_structure.patients.values():
            cur_patient_files = patient.get_files()

            #progress_callback.emit(("Setting up files .. ", 20))

            self.load_images(cur_patient_files)

            InitialModel.create_initial_model()

            pdc = PatientDictContainer()

            if "iso2roi" in self.processes:
                progress_callback.emit(("Performing ISO2ROI .. ", 70))
                self.start_process_iso2roi(PatientDictContainer(), progress_callback)
                progress_callback.emit(("Completed ISO2ROI .. ", 80))

            if "suv2roi" in self.processes:
                # Perform suv2roi on patient
                pass

    def on_loaded(self):
        self.progress_window.update_progress(("Loading complete!", 100))
        self.progress_window.close()

    def on_loading_error(self):
        print("Error performing batch processing.")

    def start_process_iso2roi(self, patient_dict_container, progress_callback):
        """
        Goes the the steps of the iso2roi conversion.
        :patient_dict_container: dictionary containing dataset
        """
        dataset_complete = ImageLoading.is_dataset_dicom_rt(patient_dict_container.dataset)
        iso2roi = ISO2ROI()

        if not dataset_complete:
            # Check if RT struct file is missing. If yes, create one and
            # add its data to the patient dict container
            if not patient_dict_container.get("file_rtss"):
                iso2roi.create_new_rtstruct(progress_callback)

        # Get isodose levels to turn into ROIs
        isodose_levels = iso2roi.get_iso_levels()

        boundaries = iso2roi.calculate_isodose_boundaries(isodose_levels)

        # Return if boundaries could not be calculated
        if not boundaries:
            print("Boundaries could not be calculated.")
            return

        iso2roi.generate_roi(boundaries, progress_callback)

    def load_images(self, files):
        try:
            path = os.path.dirname(os.path.commonprefix(files))  # Gets the common root folder.
            read_data_dict, file_names_dict = ImageLoading.get_datasets(files)
        except ImageLoading.NotAllowedClassError:
            raise ImageLoading.NotAllowedClassError

        # Populate the initial values in the PatientDictContainer singleton.
        patient_dict_container = PatientDictContainer()
        patient_dict_container.clear()
        patient_dict_container.set_initial_values(path, read_data_dict, file_names_dict)

        if 'rtss' in file_names_dict:
            dataset_rtss = dcmread(file_names_dict['rtss'])

            rois = ImageLoading.get_roi_info(dataset_rtss)

            dict_raw_contour_data, dict_numpoints = ImageLoading.get_raw_contour_data(dataset_rtss)

            dict_pixluts = ImageLoading.get_pixluts(read_data_dict)

            # Add RTSS values to PatientDictContainer
            patient_dict_container.set("rois", rois)
            patient_dict_container.set("raw_contour", dict_raw_contour_data)
            patient_dict_container.set("num_points", dict_numpoints)
            patient_dict_container.set("pixluts", dict_pixluts)

        return True