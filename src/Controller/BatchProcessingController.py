import datetime
from src.View.ProgressWindow import ProgressWindow
from src.Model.batchprocessing.BatchProcessClinicalDataSR2CSV import \
    BatchProcessClinicalDataSR2CSV
from src.Model.batchprocessing.BatchProcessCSV2ClinicalDataSR import \
    BatchProcessCSV2ClinicalDataSR
from src.Model.batchprocessing.BatchProcessDVH2CSV import BatchProcessDVH2CSV
from src.Model.batchprocessing.BatchProcessISO2ROI import BatchProcessISO2ROI
from src.Model.batchprocessing.BatchProcessROINameCleaning import \
    BatchProcessROINameCleaning
from src.Model.batchprocessing.BatchProcessPyRad2CSV import \
    BatchProcessPyRadCSV
from src.Model.DICOMStructure import Image, Series
from src.Model.PatientDictContainer import PatientDictContainer
from src.Model import DICOMDirectorySearch
import threading
from src.Model.Worker import Worker
from PySide6.QtCore import QThreadPool


class BatchProcessingController:
    """
    This class is the controller for batch processing. It starts and
    ends processes, and controls the progress window.
    """
    def __init__(self):
        """
        Class initialiser function.
        :param file_paths: dict containing paths needed for inputs and
        outputs during the batch processing
        :param processes: list of processes to be done to the patients
                          selected.
        """
        self.batch_path = ""
        self.dvh_output_path = ""
        self.pyrad_output_path = ""
        self.clinical_data_input_path = ""
        self.clinical_data_output_path = ""
        self.processes = []
        self.dicom_structure = None
        self.name_cleaning_options = None
        self.patient_files_loaded = False
        self.progress_window = ProgressWindow(None)
        self.timestamp = ""

        # threadpool for file loading
        self.threadpool = QThreadPool()
        self.interrupt_flag = threading.Event()

    def set_file_paths(self, file_paths):
        """
        Sets all the required paths
        :param file_paths: dict of directories
        """
        self.batch_path = file_paths.get('batch_path')
        self.dvh_output_path = file_paths.get('dvh_output_path')
        self.pyrad_output_path = file_paths.get('pyrad_output_path')
        self.clinical_data_input_path = \
            file_paths.get('clinical_data_input_path')
        self.clinical_data_output_path = \
            file_paths.get('clinical_data_output_path')

    def set_processes(self, processes):
        """
        Sets the selected processes
        :param processes: list of selected processes
        """
        self.processes = processes

    def start_processing(self):
        """
        Starts the batch process.
        """
        # Create new instance of ProgressWindow
        self.progress_window = ProgressWindow(None)

        # Connect callbacks
        self.progress_window.signal_error.connect(
            self.error_processing)
        self.progress_window.signal_loaded.connect(
            self.completed_processing)

        # Start performing processes on patient files
        self.progress_window.start(self.perform_processes)

    def load_patient_files(self, path, progress_callback,
                           search_complete_callback):
        """
        Load the patient files from directory.
        """
        # Set the interrup flag
        self.interrupt_flag.set()

        # Release the current thread, and create new threadpool
        self.threadpool.releaseThread()
        self.threadpool = QThreadPool()

        # Clear the interrupt flag
        self.interrupt_flag.clear()

        # Create new worker
        worker = Worker(DICOMDirectorySearch.get_dicom_structure,
                        path,
                        self.interrupt_flag,
                        progress_callback=True)

        # Connect callbacks
        worker.signals.result.connect(search_complete_callback)
        worker.signals.progress.connect(progress_callback)

        # Start the worker
        self.threadpool.start(worker)

    def set_dicom_structure(self, dicom_structure):
        """
        Function used to set dicom_structure
        :param dicom_structure: DICOMStructure
        """
        self.dicom_structure = dicom_structure

    def set_name_cleaning_options(self, options):
        """
        Set name cleaning options for batch ROI name cleaning.
        :param options: Dictionary of datasets, ROIs, and options for
                        cleaning the ROIs.
        """
        self.name_cleaning_options = options

    @staticmethod
    def get_patient_files(patient):
        """
        Get patient files.
        :param patient: patient data.
        :return: cur_patient_files, dictionary of classes and series'.
        """
        # Get files in patient
        cur_patient_files = {}
        for study in patient.studies.values():
            for series in study.series.values():
                image = list(series.images.values())[0]
                class_id = image.class_id
                series_size = len(series.images)

                if cur_patient_files.get(class_id):
                    if len(cur_patient_files.get(class_id).images) \
                            < series_size:
                        cur_patient_files[class_id] = series
                else:
                    cur_patient_files[class_id] = series

        return cur_patient_files

    def perform_processes(self, interrupt_flag, progress_callback):
        """
        Performs each selected process to each selected patient.
        :param interrupt_flag: A threading.Event() object that tells the
                               function to stop loading.
        :param progress_callback: A signal that receives the current
                                  progress of the loading.
        """
        patient_count = len(self.dicom_structure.patients)
        cur_patient_num = 0
        self.timestamp = self.create_timestamp()

        # Loop through each patient
        for patient in self.dicom_structure.patients.values():
            # Stop loading
            if interrupt_flag.is_set():
                # TODO: convert print to logging
                print("Stopped Batch Processing")
                PatientDictContainer().clear()
                return False

            cur_patient_num += 1

            progress_callback.emit(("Loading patient ({}/{}) .. ".format(
                                     cur_patient_num, patient_count), 20))

            # Perform ISO2ROI on patient
            if "iso2roi" in self.processes:
                # Get patient files
                cur_patient_files = self.get_patient_files(patient)
                process = BatchProcessISO2ROI(progress_callback,
                                              interrupt_flag,
                                              cur_patient_files)
                success = process.start()

                # Add rtss to patient
                if success:
                    if PatientDictContainer().get("rtss_modified"):
                        # Get new RTSS
                        rtss = PatientDictContainer().dataset['rtss']

                        # Create a series and image from the RTSS
                        rtss_series = Series(rtss.SeriesInstanceUID)
                        rtss_series.series_description = rtss.get(
                            "SeriesDescription")
                        rtss_image = Image(
                            PatientDictContainer().filepaths['rtss'],
                            rtss.SOPInstanceUID,
                            rtss.SOPClassUID,
                            rtss.Modality)
                        rtss_series.add_image(rtss_image)

                        # Add the new study to the patient
                        patient.studies[rtss.StudyInstanceUID].add_series(
                            rtss_series)

                        # Update the patient dict container
                        PatientDictContainer().set("rtss_modified", False)

                    progress_callback.emit(("Completed ISO2ROI", 100))

            # Perform SUV2ROI on patient
            if "suv2roi" in self.processes:
                pass

            # Perform DVH2CSV on patient
            if "dvh2csv" in self.processes:
                cur_patient_files = self.get_patient_files(patient)
                process = BatchProcessDVH2CSV(progress_callback,
                                              interrupt_flag,
                                              cur_patient_files,
                                              self.dvh_output_path)
                process.set_filename('DVHs_' + self.timestamp + '.csv')
                process.start()

                progress_callback.emit(("Completed DVH2CSV", 100))

            # Perform PyRad2CSV on patient
            if "pyrad2csv" in self.processes:
                # Get current files
                cur_patient_files = self.get_patient_files(patient)
                process = BatchProcessPyRadCSV(progress_callback,
                                               interrupt_flag,
                                               cur_patient_files,
                                               self.pyrad_output_path)
                process.set_filename('Pyradiomics_' + self.timestamp + '.csv')
                process.start()

                progress_callback.emit(("Completed PyRad2CSV", 100))

            # Perform batch ROI Name Cleaning on patient
            if "roinamecleaning" in self.processes:
                if self.name_cleaning_options:
                    # Get ROIs, dataset locations, options
                    process = \
                        BatchProcessROINameCleaning(progress_callback,
                                                    interrupt_flag,
                                                    self.name_cleaning_options)
                    process.start()
                    progress_callback.emit(("Completed ROI Name Cleaning", 100))

            # Perform CSV2ClinicalData-SR on patient
            if "csv2clinicaldatasr" in self.processes:
                # Get current files
                cur_patient_files = self.get_patient_files(patient)
                process = BatchProcessCSV2ClinicalDataSR(
                    progress_callback, interrupt_flag,
                    cur_patient_files, self.clinical_data_input_path)
                process.start()
                progress_callback.emit(("Completed CSV2ClinicalData-SR", 100))

            # Perform ClinicalData-SR2CSV on patient
            if "clinicaldatasr2csv" in self.processes:
                cur_patient_files = self.get_patient_files(patient)
                process = BatchProcessClinicalDataSR2CSV(
                    progress_callback, interrupt_flag,
                    cur_patient_files, self.clinical_data_output_path
                )
                process.start()
                progress_callback.emit(("Completed ClinicalData-SR2CSV", 100))

        PatientDictContainer().clear()

    def completed_processing(self):
        """
        Runs when batch processing has been completed.
        """
        self.progress_window.update_progress(("Processing complete!", 100))
        print("Processing completed!")
        self.progress_window.close()

    def error_processing(self):
        """
        Runs when there is an error during batch processing.
        """
        print("Error performing batch processing.")
        self.progress_window.close()
        return

    @classmethod
    def create_timestamp(cls):
        """
        Create a unique timestamp as a string.
        returns string
        """
        cur_time = datetime.datetime.now()
        year = cur_time.year
        month = cur_time.month
        day = cur_time.day
        hour = cur_time.hour
        min = cur_time.minute
        sec = cur_time.second

        time_stamp = str(year) + str(month) + str(day) + str(hour) + \
                     str(min) + str(sec)

        return time_stamp