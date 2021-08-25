from src.View.ProgressWindow import ProgressWindow
from src.Model.BatchProcesses import BatchProcessISO2ROI
from src.Model.PatientDictContainer import PatientDictContainer

class BatchProcessingController:

    def __init__(self, dicom_structure, processes):
        self.dicom_structure = dicom_structure
        self.processes = processes

        self.progress_window = ProgressWindow(None)
        self.progress_window.signal_error.connect(self.processing_error)
        self.progress_window.signal_loaded.connect(self.processing_completed)

    def start_processing(self):
        self.progress_window.start(self.perform_processes)

    def perform_processes(self, interrupt_flag, progress_callback):
        for patient in self.dicom_structure.patients.values():
            cur_patient_files = {}
            for study in patient.studies.values():
                for series in study.series.values():
                    image = list(series.images.values())[0]
                    class_id = image.class_id
                    series_size = len(series.images)

                    if cur_patient_files.get(class_id):
                        if len(cur_patient_files.get(class_id).images) < series_size:
                            cur_patient_files[class_id] = series
                    else:
                        cur_patient_files[class_id] = series

            # Stop loading
            if interrupt_flag.is_set():
                # TODO: convert print to logging
                print("Stopped ISO2ROI")
                PatientDictContainer().clear()
                return False

            progress_callback.emit(("Loading dataset .. ", 20))

            # Perform iso2roi on patient
            if "iso2roi" in self.processes:
                process = BatchProcessISO2ROI(progress_callback, interrupt_flag,
                                              cur_patient_files)
                process.start()

                progress_callback.emit(("Completed ISO2ROI .. ", 90))

            if "suv2roi" in self.processes:
                # Perform suv2roi on patient
                pass

        PatientDictContainer().clear()

    def processing_completed(self):
        self.progress_window.update_progress(("Processing complete!", 100))
        print("Processing completed!")
        self.progress_window.close()

    def processing_error(self):
        print("Error performing batch processing.")
        return


