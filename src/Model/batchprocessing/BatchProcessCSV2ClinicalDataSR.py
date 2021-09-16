import os
from src.Model import CalculateDVHs
from src.Model import ImageLoading
from src.Model.batchprocessing.BatchProcess import BatchProcess
from src.Model.PatientDictContainer import PatientDictContainer
import pandas as pd


class BatchProcessCSV2ClinicalDataSR(BatchProcess):
    """
    This class handles batch processing for the DVH2CSV process.
    Inherits from the BatchProcess class.
    """
    # Allowed classes for CSV2ClinicalDataSR
    allowed_classes = {
        # CT Image
        "1.2.840.10008.5.1.4.1.1.2": {
            "name": "ct",
            "sliceable": True
        }
    }

    def __init__(self, progress_callback, interrupt_flag, patient_files,
                 input_path):
        """
        Class initialiser function.
        :param progress_callback: A signal that receives the current
                                  progress of the loading.
        :param interrupt_flag: A threading.Event() object that tells the
                               function to stop loading.
        :param patient_files: List of patient files.
        :param output_path: Path of the input CSV file.
        """
        # Call the parent class
        super(BatchProcessCSV2ClinicalDataSR, self).__init__(progress_callback,
                                                             interrupt_flag,
                                                             patient_files)

        # Set class variables
        self.patient_dict_container = PatientDictContainer()
        self.required_classes = ['ct']
        self.ready = self.load_images(patient_files, self.required_classes)
        self.input_path = input_path

    def start(self):
        """
        Goes through the steps of the CSV2ClinicalData-SR conversion.
        :return: True if successful, False if not.
        """
        # Stop loading
        if self.interrupt_flag.is_set():
            # TODO: convert print to logging
            print("Stopped CSV2ClinicalData-SR")
            self.patient_dict_container.clear()
            return False

        if not self.ready:
            return

        # Check if the dataset is complete
        # TODO
        self.progress_callback.emit(("Checking dataset...", 40))

        # Import CSV data
        # TODO
        self.progress_callback.emit(("Importing CSV data...", 60))

        # Stop loading
        if self.interrupt_flag.is_set():
            # TODO: convert print to logging
            print("Stopped CSV2ClinicalData-SR")
            self.patient_dict_container.clear()
            return False

        # Save clinical data to an SR
        # TODO
        self.progress_callback.emit(("Exporting Clinical Data to DICOM-SR...",
                                     90))

        # Get path to save to and generate SR
        path = self.patient_dict_container.path

        # Save SR
