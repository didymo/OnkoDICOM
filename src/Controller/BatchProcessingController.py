import datetime
import threading
from PySide6.QtCore import QThreadPool
from src.Model import DICOMDirectorySearch
from src.Model.batchprocessing.BatchProcessISO2ROI import BatchProcessISO2ROI
from src.Model.batchprocessing.BatchProcessSUV2ROI import BatchProcessSUV2ROI
from src.Model.DICOMStructure import Image, Series
from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.Worker import Worker
from src.View.batchprocessing.BatchSummaryWindow import BatchSummaryWindow
from src.View.ProgressWindow import ProgressWindow


class BatchProcessingController:
    """
    This class is the controller for batch processing. It starts and
    ends processes, and controls the progress window.
    """
    def __init__(self):
        """
        Class initialiser function.
        """
        self.batch_path = ""
        self.processes = []
        self.dicom_structure = None
        self.patient_files_loaded = False
        self.progress_window = ProgressWindow(None)
        self.timestamp = ""
        self.batch_summary = {}

        # Threadpool for file loading
        self.threadpool = QThreadPool()
        self.interrupt_flag = threading.Event()

    def set_file_paths(self, file_paths):
        """
        Sets all the required paths
        :param file_paths: dict of directories
        """
        self.batch_path = file_paths.get('batch_path')

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
            for series_type in study.series.values():
                for series in series_type.values():

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

                # Add rtss to patient in case it is needed in future
                # processes
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
                    reason = "SUCCESS"
                else:
                    reason = process.summary

                # Append process summary
                if patient not in self.batch_summary.keys():
                    self.batch_summary[patient] = {}
                self.batch_summary[patient]["iso2roi"] = reason
                progress_callback.emit(("Completed ISO2ROI", 100))

            # Perform SUV2ROI on patient
            if 'suv2roi' in self.processes:
                # Get patient files
                cur_patient_files = self.get_patient_files(patient)
                patient_weight = None  # TODO remove
                process = BatchProcessSUV2ROI(progress_callback,
                                              interrupt_flag,
                                              cur_patient_files,
                                              patient_weight)
                success = process.start()

                # Add rtss to patient in case it is needed in future
                # processes
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
                    reason = "SUCCESS"
                else:
                    reason = process.summary

                # Append process summary
                if patient not in self.batch_summary.keys():
                    self.batch_summary[patient] = {}
                self.batch_summary[patient]["suv2roi"] = reason
                progress_callback.emit(("Completed SUV2ROI", 100))

        PatientDictContainer().clear()

    def completed_processing(self):
        """
        Runs when batch processing has been completed.
        """
        self.progress_window.update_progress(("Processing complete!", 100))
        self.progress_window.close()

        # Create window to store summary info
        batch_summary_window = BatchSummaryWindow()
        batch_summary_window.set_summary_text(self.batch_summary)
        batch_summary_window.exec_()

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
