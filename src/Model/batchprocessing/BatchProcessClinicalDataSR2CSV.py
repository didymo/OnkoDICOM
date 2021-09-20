from src.Model.batchprocessing.BatchProcess import BatchProcess
from src.Model.PatientDictContainer import PatientDictContainer


class BatchProcessClinicalDataSR2CSV(BatchProcess):
    """
    This class handles batch processing for the Clinical Data 2 CSV
    process. Inherits from the BatchProcessing class.
    """
    # Allowed classes for ClinicalDataSR2CSV
    allowed_classes = {
        # Comprehensive SR
        "1.2.840.10008.5.1.4.1.1.88.33": {
            "name": "sr",
            "sliceable": False
        }
    }

    def __init__(self, progress_callback, interrupt_flag, patient_files,
                 output_path):
        """
        Class initialiser function.
        :param progress_callback: A signal that receives the current
                                  progress of the loading.
        :param interrupt_flag: A threading.Event() object that tells the
                               function to stop loading.
        :param patient_files: List of patient files.
        :param output_path: Path of the output CSV file.
        """
        # Call the parent class
        super(BatchProcessClinicalDataSR2CSV, self).__init__(progress_callback,
                                                             interrupt_flag,
                                                             patient_files)

        # Set class variables
        self.patient_dict_container = PatientDictContainer()
        self.required_classes = ['sr']
        self.ready = self.load_images(patient_files, self.required_classes)
        self.output_path = output_path

    def start(self):
        """
        Goes through the steps of the ClinicalData-SR2CSV conversion.
        :return: True if successful, False if not.
        """
        # Stop loading
        if self.interrupt_flag.is_set():
            # TODO: convert print to logging
            print("Stopped ClinicalData-SR2CSV")
            self.patient_dict_container.clear()
            return False

        if not self.ready:
            return False

        # See if SR contains clinical data
        self.progress_callback.emit(("Checking SR file...", 20))
        # TODO

        # Read in clinical data from SR
        self.progress_callback.emit(("Reading clinical data...", 50))
        # TODO

        # Write clinical data to CSV
        self.progress_callback.emit(("Writing clinical data to CSV...", 80))
        # TODO