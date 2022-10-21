import datetime
import threading
from PySide6.QtCore import QThreadPool
from src.Model.DICOM import DICOMDirectorySearch
from src.Model.batchprocessing.BatchProcessClinicalDataSR2CSV import \
    BatchProcessClinicalDataSR2CSV
from src.Model.batchprocessing.BatchProcessCSV2ClinicalDataSR import \
    BatchProcessCSV2ClinicalDataSR
from src.Model.batchprocessing.BatchProcessDVH2CSV import BatchProcessDVH2CSV
from src.Model.batchprocessing.BatchProcessISO2ROI import BatchProcessISO2ROI
from src.Model.batchprocessing.BatchProcessPyRad2CSV import \
    BatchProcessPyRad2CSV
from src.Model.batchprocessing.BatchProcessPyrad2PyradSR import \
    BatchProcessPyRad2PyRadSR
from src.Model.batchprocessing.BatchProcessROIName2FMAID import \
    BatchProcessROIName2FMAID
from src.Model.batchprocessing.BatchProcessROINameCleaning import \
    BatchProcessROINameCleaning
from src.Model.batchprocessing.BatchProcessFMAID2ROIName import \
    BatchProcessFMAID2ROIName
from src.Model.batchprocessing.BatchProcessSUV2ROI import BatchProcessSUV2ROI
from src.Model.batchprocessing.BatchProcessKaplanMeier import \
    BatchProcessKaplanMeier
from src.Model.batchprocessing.BatchProcessSelectSubgroup import \
    BatchProcessSelectSubgroup
from src.Model.batchprocessing. \
    BatchprocessMachineLearningDataSelection \
    import BatchprocessMachineLearningDataSelection
from src.Model.batchprocessing.BatchProcessMachineLearning import \
    BatchProcessMachineLearning
from src.Model.DICOM.Structure.DICOMSeries import Series
from src.Model.DICOM.Structure.DICOMImage import Image
from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.Worker import Worker
from src.View.batchprocessing.BatchSummaryWindow import BatchSummaryWindow
from src.View.batchprocessing.BatchMLResultsWindow import BatchMLResultsWindow
from src.View.ProgressWindow import ProgressWindow
import logging
import pandas as pd
import kaplanmeier as km
import matplotlib.pyplot as plt


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
        self.dvh_output_path = ""
        self.pyrad_output_path = ""
        self.clinical_data_input_path = ""
        self.clinical_data_output_path = ""
        self.processes = []
        self.dicom_structure = None
        self.suv2roi_weights = None
        self.name_cleaning_options = None
        self.subgroup_filter_options = None
        self.ml_data_selection_options = None
        self.patient_files_loaded = False
        self.progress_window = ProgressWindow(None)
        self.timestamp = ""
        self.batch_summary = [{}, ""]
        self.kaplanmeier_target_col = ""
        self.kaplanmeier_duration_of_life_col = ""
        self.kaplanmeier_alive_or_dead_col = ""

        # Path
        self.clinical_data_path = ""
        self.dvh_data_path = ""
        self.pyrad_data_path = ""
        # Parameters
        self.machine_learning_features = []
        self.machine_learning_target = []
        self.machine_learning_type = ""
        self.machine_learning_rename = []
        self.machine_learning_tune = ""

        self.machine_learning_process = None

        # Threadpool for file loading
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

    def set_suv2roi_weights(self, suv2roi_weights):
        """
        Function used to set suv2roi_weights.
        :param suv2roi_weights: Dictionary of patient IDs and patient weight
                                in grams.
        """
        self.suv2roi_weights = suv2roi_weights

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

    def set_subgroup_filter_options(self, options):
        """
        Set subgroup filter options for batch subgroup selection.
        :param options: Dictionary of attributes with list of values
        to filter by in that column.
        """
        logging.debug(f"{self.__class__.__name__} \
        .set_subgroup_filter_options(options) called")
        logging.debug(f"'options' set to: {options}")
        self.subgroup_filter_options = options

    def set_ml_data_selection_options(self, options):
        """
        Set ml data selection options for batch process.
        :param options: Dictionary of:
        {"dvh_path": "",
        "pyrad_path": "",
        "dvh_value": "",
        "pyrad_value": ""}
        """
        logging.debug(f"{self.__class__.__name__} \
        .set_ml_data_selection_options(options) called")
        logging.debug(f"'options' set to: {options}")
        self.ml_data_selection_options = options

    # Path
    def set_clinical_data_path(self, clinical_path):
        self.clinical_data_path = clinical_path

    def set_dvh_data_path(self, dvh_path):
        self.dvh_data_path = dvh_path

    def set_pyrad_data_path(self, pyrad_path):
        self.pyrad_data_path = pyrad_path

    # Params
    def set_machine_learning_features(self, machine_learning_features):
        self.machine_learning_features = machine_learning_features

    def set_machine_learning_target(self, machine_learning_target):
        self.machine_learning_target = machine_learning_target

    def set_machine_learning_type(self, machine_learning_type):
        self.machine_learning_type = machine_learning_type

    def set_machine_learning_rename(self, machine_learning_rename):
        self.machine_learning_rename = machine_learning_rename

    def set_machine_learning_tune(self, machine_learning_tune):
        self.machine_learning_tune = machine_learning_tune

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

                    if class_id not in cur_patient_files:
                        cur_patient_files[class_id] = []

                    cur_patient_files[class_id].append(series)

        return cur_patient_files

    def perform_processes(self, interrupt_flag, progress_callback=None):
        """
        Performs each selected process to each selected patient.
        :param interrupt_flag: A threading.Event() object that tells the
                               function to stop loading.
        :param progress_callback: A signal that receives the current
                                  progress of the loading.
        """
        # Clear batch summary
        self.batch_summary = [{}, ""]

        # Dictionary of process names and functions
        self.process_functions = {
            "select_subgroup": self.batch_select_subgroup_handler,
            "iso2roi": self.batch_iso2roi_handler,
            "suv2roi": self.batch_suv2roi_handler,
            "dvh2csv": self.batch_dvh2csv_handler,
            "pyrad2csv": self.batch_pyrad2csv_handler,
            "pyrad2pyrad-sr": self.batch_pyrad2pyradsr_handler,
            "csv2clinicaldata-sr": self.batch_csv2clinicaldatasr_handler,
            "clinicaldata-sr2csv": self.batch_clinicaldatasr2csv_handler,
            "roiname2fmaid": self.batch_roiname2fmaid_handler,
            "fmaid2roiname": self.batch_fmaid2roiname_handler,
        }

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

            if "select_subgroup" in self.processes:
                in_subgroup = self.process_functions["select_subgroup"](
                    interrupt_flag,
                    progress_callback,
                    patient
                )

                if not in_subgroup:
                    # dont complete processes on this patient
                    continue

            # Perform processes on patient
            for process in self.processes:
                if process in ["roinamecleaning",
                               "select_subgroup",
                               "machine_learning",
                               "machine_learning_data_selection",
                               "kaplanmeier"]:
                    continue

                self.process_functions[process](interrupt_flag,
                                                progress_callback,
                                                patient)

        # Perform batch ROI Name Cleaning on all patients
        if 'roinamecleaning' in self.processes:
            if self.name_cleaning_options:
                # Start the process
                process = \
                    BatchProcessROINameCleaning(progress_callback,
                                                interrupt_flag,
                                                self.name_cleaning_options)
                process.start()

                # Append process summary
                self.batch_summary[1] = process.summary
                progress_callback.emit(("Completed ROI Name Cleaning", 100))

        ml_data = {
            "features": self.machine_learning_features,
            "target": self.machine_learning_target,
            "type": self.machine_learning_type,
            "tune": self.machine_learning_tune,
            "renameValues": self.machine_learning_rename
        }
        self.machine_learning_options = ml_data

        if "machine_learning" in self.processes:
            self.machine_learning_process = \
                BatchProcessMachineLearning(
                    progress_callback,
                    interrupt_flag,
                    self.machine_learning_options,
                    self.clinical_data_path,
                    self.dvh_data_path,
                    self.pyrad_data_path)
            self.machine_learning_process.start()
            self.batch_summary[1] = self.machine_learning_process.summary
            progress_callback.emit(("Completed ML Training Cleaning", 100))

        if "machine_learning_data_selection" in self.processes:
            process = BatchprocessMachineLearningDataSelection(
                progress_callback,
                self.ml_data_selection_options["dvh_path"],
                self.ml_data_selection_options["pyrad_path"],
                self.ml_data_selection_options["dvh_value"],
                self.ml_data_selection_options["pyrad_value"])

            process.start()
            self.batch_summary[1] = process.summary
            progress_callback.emit(("Completed ML Data selection", 100))

        PatientDictContainer().clear()

    def update_rtss(self, patient):
        """
        Updates the patient dict container with the newly created RTSS (if a
        process generates one), so it can be used by future processes.
        :param patient: The patient with the newly-created RTSS.
        """
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

    def batch_select_subgroup_handler(self,
                                      interrupt_flag,
                                      progress_callback,
                                      patient):
        """
        Handles creating, starting, and processing the results of batch
        select_subgroup.
        :param interrupt_flag: A threading.Event() object that tells the
                               function to stop loading.
        :param progress_callback: A signal that receives the current
                                  progress of the loading.
        :param patient: The patient to perform this process on.
        """
        logging.debug(f"{self.__class__.__name__}"
                      ".batch_select_subgroup_handler() called")
        cur_patient_files = \
            BatchProcessingController.get_patient_files(patient)
        process = \
            BatchProcessSelectSubgroup(progress_callback,
                                       interrupt_flag,
                                       cur_patient_files,
                                       self.subgroup_filter_options)
        success = process.start()

        # Update summary
        if success:
            reason = "SUCCESS"
        else:
            reason = process.summary

        if patient not in self.batch_summary[0].keys():
            self.batch_summary[0][patient] = {}
        self.batch_summary[0][patient]["select_subgroup"] = reason
        progress_callback.emit(("Completed Select Subgroup", 100))

        return process.within_filter

    def batch_iso2roi_handler(self, interrupt_flag,
                              progress_callback, patient):
        """
        Handles creating, starting, and processing the results of batch
        ISO2ROI.
        :param interrupt_flag: A threading.Event() object that tells the
                               function to stop loading.
        :param progress_callback: A signal that receives the current
                                  progress of the loading.
        :param patient: The patient to perform this process on.
        """
        # Get current patient files
        cur_patient_files = \
            BatchProcessingController.get_patient_files(patient)

        # Create and start process
        process = BatchProcessISO2ROI(progress_callback,
                                      interrupt_flag,
                                      cur_patient_files)
        success = process.start()

        # Add rtss to patient in case it is needed in future
        # processes
        if success:
            if PatientDictContainer().get("rtss_modified"):
                self.update_rtss(patient)
            reason = "SUCCESS"
        else:
            reason = process.summary

        # Append process summary
        if patient not in self.batch_summary[0].keys():
            self.batch_summary[0][patient] = {}
        self.batch_summary[0][patient]["iso2roi"] = reason
        progress_callback.emit(("Completed ISO2ROI", 100))

    def batch_suv2roi_handler(self, interrupt_flag,
                              progress_callback, patient):
        """
        Handles creating, starting, and processing the results of batch
        SUV2ROI.
        :param interrupt_flag: A threading.Event() object that tells the
                               function to stop loading.
        :param progress_callback: A signal that receives the current
                                  progress of the loading.
        :param patient: The patient to perform this process on.
        """
        # Get patient files
        cur_patient_files = \
            BatchProcessingController.get_patient_files(patient)

        # Get patient weight
        if patient.patient_id in self.suv2roi_weights.keys():
            if self.suv2roi_weights[patient.patient_id] is None:
                patient_weight = None
            else:
                patient_weight = \
                    self.suv2roi_weights[patient.patient_id] * 1000
        else:
            patient_weight = None

        process = BatchProcessSUV2ROI(progress_callback,
                                      interrupt_flag,
                                      cur_patient_files,
                                      patient_weight)
        success = process.start()

        # Add rtss to patient in case it is needed in future
        # processes
        if success:
            if PatientDictContainer().get("rtss_modified"):
                self.update_rtss(patient)
            reason = "SUCCESS"
        else:
            reason = process.summary

        # Append process summary
        if patient not in self.batch_summary[0].keys():
            self.batch_summary[0][patient] = {}
        self.batch_summary[0][patient]["suv2roi"] = reason
        progress_callback.emit(("Completed SUV2ROI", 100))

    def batch_dvh2csv_handler(self, interrupt_flag,
                              progress_callback, patient):
        """
        Handles creating, starting, and processing the results of batch
        DVH2CSV.
        :param interrupt_flag: A threading.Event() object that tells the
                               function to stop loading.
        :param progress_callback: A signal that receives the current
                                  progress of the loading.
        :param patient: The patient to perform this process on.
        """
        # Get current patient files
        cur_patient_files = \
            BatchProcessingController.get_patient_files(patient)

        # Create and start process
        process = BatchProcessDVH2CSV(progress_callback,
                                      interrupt_flag,
                                      cur_patient_files,
                                      self.dvh_output_path)
        process.set_filename('DVHs_' + self.timestamp + '.csv')
        success = process.start()

        # Set process summary
        if success:
            reason = "SUCCESS"
        else:
            reason = process.summary

        # Append process summary
        if patient not in self.batch_summary[0].keys():
            self.batch_summary[0][patient] = {}
        self.batch_summary[0][patient]['dvh2csv'] = reason
        progress_callback.emit(("Completed DVH2CSV", 100))

    def batch_pyrad2csv_handler(self, interrupt_flag,
                                progress_callback, patient):
        """
        Handles creating, starting, and processing the results of batch
        Pyrad2CSV.
        :param interrupt_flag: A threading.Event() object that tells the
                               function to stop loading.
        :param progress_callback: A signal that receives the current
                                  progress of the loading.
        :param patient: The patient to perform this process on.
        """
        # Get current files
        cur_patient_files = \
            BatchProcessingController.get_patient_files(patient)
        process = BatchProcessPyRad2CSV(progress_callback,
                                        interrupt_flag,
                                        cur_patient_files,
                                        self.pyrad_output_path)
        process.set_filename('PyRadiomics_' + self.timestamp + '.csv')
        success = process.start()

        # Set summary message
        if success:
            reason = "SUCCESS"
        else:
            reason = process.summary

        # Append process summary
        if patient not in self.batch_summary[0].keys():
            self.batch_summary[0][patient] = {}
        self.batch_summary[0][patient]['pyrad2csv'] = reason
        progress_callback.emit(("Completed PyRad-SR2CSV", 100))

    def batch_pyrad2pyradsr_handler(self, interrupt_flag,
                                    progress_callback, patient):
        """
        Handles creating, starting, and processing the results of batch
        PyRad2PyRad-SR.
        :param interrupt_flag: A threading.Event() object that tells the
                               function to stop loading.
        :param progress_callback: A signal that receives the current
                                  progress of the loading.
        :param patient: The patient to perform this process on.
        """
        # Get current files
        cur_patient_files = \
            BatchProcessingController.get_patient_files(patient)
        process = BatchProcessPyRad2PyRadSR(progress_callback,
                                            interrupt_flag,
                                            cur_patient_files)
        success = process.start()

        # Set summary message
        if success:
            reason = "SUCCESS"
        else:
            reason = process.summary

        # Append process summary
        if patient not in self.batch_summary[0].keys():
            self.batch_summary[0][patient] = {}
        self.batch_summary[0][patient]['pyrad2pyradSR'] = reason
        progress_callback.emit(("Completed PyRad2PyRad-SR", 100))

    def batch_csv2clinicaldatasr_handler(self, interrupt_flag,
                                         progress_callback, patient):
        """
        Handles creating, starting, and processing the results of batch
        CSV2ClinicalData-SR.
        :param interrupt_flag: A threading.Event() object that tells the
                               function to stop loading.
        :param progress_callback: A signal that receives the current
                                  progress of the loading.
        :param patient: The patient to perform this process on.
        """
        # Get current files
        cur_patient_files = \
            BatchProcessingController.get_patient_files(patient)
        process = \
            BatchProcessCSV2ClinicalDataSR(progress_callback, interrupt_flag,
                                           cur_patient_files,
                                           self.clinical_data_input_path)
        success = process.start()

        # Update summary
        if success:
            reason = "SUCCESS"
        else:
            reason = process.summary

        if patient not in self.batch_summary[0].keys():
            self.batch_summary[0][patient] = {}
        self.batch_summary[0][patient]["csv2clinicaldatasr"] = reason
        progress_callback.emit(("Completed CSV2ClinicalData-SR", 100))

    def batch_clinicaldatasr2csv_handler(self, interrupt_flag,
                                         progress_callback, patient):
        """
        Handles creating, starting, and processing the results of batch
        ClinicalData-SR2CSV.
        :param interrupt_flag: A threading.Event() object that tells the
                               function to stop loading.
        :param progress_callback: A signal that receives the current
                                  progress of the loading.
        :param patient: The patient to perform this process on.
        """
        cur_patient_files = \
            BatchProcessingController.get_patient_files(patient)
        process = \
            BatchProcessClinicalDataSR2CSV(progress_callback, interrupt_flag,
                                           cur_patient_files,
                                           self.clinical_data_output_path)
        success = process.start()

        # Update summary
        if success:
            reason = "SUCCESS"
        else:
            reason = process.summary

        if patient not in self.batch_summary[0].keys():
            self.batch_summary[0][patient] = {}
        self.batch_summary[0][patient]["clinicaldatasr2csv"] = reason
        progress_callback.emit(("Completed ClinicalData-SR2CSV", 100))

    def batch_roiname2fmaid_handler(self, interrupt_flag,
                                    progress_callback, patient):
        """
        Handles creating, starting, and processing the results of batch
        ROIName2FMA-ID.
        :param interrupt_flag: A threading.Event() object that tells the
                               function to stop loading.
        :param progress_callback: A signal that receives the current
                                  progress of the loading.
        :param patient: The patient to perform this process on.
        """
        # Get patient files and start process
        cur_patient_files = \
            BatchProcessingController.get_patient_files(patient)
        process = \
            BatchProcessROIName2FMAID(progress_callback,
                                      interrupt_flag,
                                      cur_patient_files)
        process.start()

        # Append process summary
        reason = process.summary
        if patient not in self.batch_summary[0].keys():
            self.batch_summary[0][patient] = {}
        self.batch_summary[0][patient]["roiname2fmaid"] = reason
        progress_callback.emit(("Completed ROI Name to FMA ID", 100))

    def batch_fmaid2roiname_handler(self, interrupt_flag,
                                    progress_callback, patient):
        """
        Handles creating, starting, and processing the results of batch
        FMA-ID2ROIName.
        :param interrupt_flag: A threading.Event() object that tells the
                               function to stop loading.
        :param progress_callback: A signal that receives the current
                                  progress of the loading.
        :param patient: The patient to perform this process on.
        """
        # Get patient files and start process
        cur_patient_files = \
            BatchProcessingController.get_patient_files(patient)
        process = \
            BatchProcessFMAID2ROIName(progress_callback,
                                      interrupt_flag,
                                      cur_patient_files)
        process.start()

        # Append process summary
        reason = process.summary
        if patient not in self.batch_summary[0].keys():
            self.batch_summary[0][patient] = {}
        self.batch_summary[0][patient]["fmaid2roiname"] = reason
        progress_callback.emit(("Completed FMA ID to ROI Name", 100))

    def completed_processing(self):
        """
        Runs when batch processing has been completed.
        """
        self.progress_window.update_progress(("Processing complete!", 100))
        self.progress_window.close()

        if "kaplanmeier" in self.processes:
            try:
                # creates dataframe based on patient records
                df = pd.DataFrame.from_dict(self.get_data_for_kaplan_meier())

                # creates input parameters for the km.fit() function

                time_event = df[self.kaplanmeier_duration_of_life_col]

                censoring = df[self.kaplanmeier_alive_or_dead_col]

                y = df[self.kaplanmeier_target_col]

                # create kaplanmeier plot
                results = km.fit(time_event, censoring, y)
                km.plot(results, cmap='Set1', cii_lines='dense',
                        cii_alpha=0.10)

                # specifies plot layout
                plt.tight_layout()
                plt.subplots_adjust(top=0.903,
                                    bottom=0.423,
                                    left=0.085,
                                    right=0.965,
                                    hspace=0.2,
                                    wspace=0.2)

                plt.show()
            except Exception as e:
                logging.debug(e)

        if self.machine_learning_process is not None \
                and self.machine_learning_process. \
                get_run_model_accept() is not False:
            # Create window to store ML results
            ml_results_window = BatchMLResultsWindow()
            ml_results_window. \
                set_results_values(self.machine_learning_process.
                                   get_results_values())
            ml_results_window.set_ml_model(self.machine_learning_process.
                                           ml_model)

            ml_results_window.set_df_parameters(self.machine_learning_process.
                                                params)
            ml_results_window.set_df_scaling(self.machine_learning_process.
                                             scaling)

            ml_results_window.exec_()

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

    def get_all_clinical_data(self):
        """
        Reads in all clinical data from a directory which may
        contain multiple patients.
        :return: only unique values in a dictionary with keys as the
        column name and a list of values found
        """
        logging.debug(f"{self.__class__.__name__}"
                      ".get_all_clinical_data() called")

        clinical_data_dict = {}

        for patient in self.dicom_structure.patients.values():
            logging.debug(f"{len(self.dicom_structure.patients.values())}"
                          "patient(s) in dicom_structure object")

            cur_patient_files = \
                BatchProcessingController.get_patient_files(patient)
            process = \
                BatchProcessSelectSubgroup(None, None, cur_patient_files, None)

            cd_sr = process.find_clinical_data_sr()

            # if they do then get the data
            if cd_sr:
                single_patient_data = process.read_clinical_data_from_sr(cd_sr)
                # adds all the current titles
                titles = list(single_patient_data)

                for title in titles:
                    data = single_patient_data[title]

                    if title not in clinical_data_dict.keys():
                        clinical_data_dict[title] = [data]
                    else:
                        combined_data = clinical_data_dict[title]
                        combined_data.append(data)

                        # removes duplicates
                        combined_data = list(dict.fromkeys(combined_data))

                        clinical_data_dict[title] = combined_data

        logging.debug(f"clinical_data_dict: {clinical_data_dict}")

        return clinical_data_dict

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

    def set_kaplanmeier_target_col(self, target):
        self.kaplanmeier_target_col = target

    def set_kaplanmeier_duration_of_life_col(self, duration):
        self.kaplanmeier_duration_of_life_col = duration

    def set_kaplanmeier_alive_or_dead_col(self, alive_or_dead):
        self.kaplanmeier_alive_or_dead_col = alive_or_dead

    def get_data_for_kaplan_meier(self):
        """
        Reads in all clinical data from a directory which may
        contain multiple patients.
        :return: only unique values in a dictionary with keys as the
        column name and a list of values found
        """
        logging.debug(f"{self.__class__.__name__}"
                      ".get_all_clinical_data() called")

        clinical_data_dict = {}

        for patient in self.dicom_structure.patients.values():
            logging.debug(f"{len(self.dicom_structure.patients.values())}"
                          "patient(s) in dicom_structure object")

            cur_patient_files = \
                BatchProcessingController.get_patient_files(patient)
            process = \
                BatchProcessKaplanMeier(None, None, cur_patient_files)

            cd_sr = process.find_clinical_data_sr()

            # if they do then get the data
            if cd_sr:
                single_patient_data = process.read_clinical_data_from_sr(cd_sr)
                # adds all the current titles
                titles = list(single_patient_data)

                for title in titles:
                    data = single_patient_data[title]

                    if title not in clinical_data_dict.keys():
                        clinical_data_dict[title] = [data]
                    else:
                        combined_data = clinical_data_dict[title]
                        combined_data.append(data)

                        clinical_data_dict[title] = combined_data

        logging.debug(f"clinical_data_dict: {clinical_data_dict}")
        return clinical_data_dict
