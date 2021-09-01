from src.View.ProgressWindow import ProgressWindow
from src.Model.batchprocessing.BatchProcessDVH2CSV import BatchProcessDVH2CSV
from src.Model.batchprocessing.BatchProcessISO2ROI import BatchProcessISO2ROI
from src.Model.DICOMStructure import Image, Series
from src.Model.PatientDictContainer import PatientDictContainer


class BatchProcessingController:
    """
    This class is the controller for batch processing. It starts and
    ends processes, and controls the progress window.
    """
    def __init__(self, dicom_structure, processes):
        """
        Class initialiser function.
        :param dicom_structure: DICOMStructure object containing each
                                patient in selected directory.
        :param processes: list of processes to be done to the patients
                          selected.
        """
        self.dicom_structure = dicom_structure
        self.processes = processes

        # Create progress window and connect signals
        self.progress_window = ProgressWindow(None)
        self.progress_window.signal_error.connect(self.processing_error)
        self.progress_window.signal_loaded.connect(self.processing_completed)

    def start_processing(self):
        """
        Starts the batch process.
        """
        self.progress_window.start(self.perform_processes)

    def get_patient_files(self, patient):
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
        # Loop through each patient
        for patient in self.dicom_structure.patients.values():
            # Stop loading
            if interrupt_flag.is_set():
                # TODO: convert print to logging
                print("Stopped Batch Processing")
                PatientDictContainer().clear()
                return False

            progress_callback.emit(("Loading dataset .. ", 20))

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

                    progress_callback.emit(("Completed ISO2ROI .. ", 90))

            # Perform SUV2ROI on patient
            if "suv2roi" in self.processes:
                pass

            # Perform DVH2CSV on patient
            if "dvh2csv" in self.processes:
                cur_patient_files = self.get_patient_files(patient)
                process = BatchProcessDVH2CSV(progress_callback,
                                              interrupt_flag,
                                              cur_patient_files)
                process.start()

                progress_callback.emit(("Completed DVH2CSV", 90))

        PatientDictContainer().clear()

    def processing_completed(self):
        """
        Runs when batch processing has been completed.
        """
        self.progress_window.update_progress(("Processing complete!", 100))
        print("Processing completed!")
        self.progress_window.close()

    def processing_error(self):
        """
        Runs when there is an error during batch processing.
        """
        print("Error performing batch processing.")
        return


