import os
from src.Model import ImageLoading
from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.batchprocessing.BatchProcess import BatchProcess
import pandas as pd


class BatchProcessPyRadCSV(BatchProcess):
    """
    This class handles batch processing for the PyRadCSV process.
    Inherits from the BatchProcess class.
    """
    # Allowed classes for PyRadCSV
    allowed_classes = {
        # RT Structure Set
        "1.2.840.10008.5.1.4.1.1.481.3": {
            "name": "rtss",
            "sliceable": False
        },
        # RT Dose
        "1.2.840.10008.5.1.4.1.1.481.2": {
            "name": "rtdose",
            "sliceable": False
        },
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
        :param output_path: output of the resulting .csv file.
        """
        # Call the parent class
        super(BatchProcessPyRadCSV, self).__init__(progress_callback,
                                                   interrupt_flag,
                                                   patient_files)

        # Set class variables
        self.patient_dict_container = PatientDictContainer()
        self.required_classes = ('rtss', 'rtdose')
        self.ready = self.load_images(patient_files, self.required_classes)
        self.output_path = output_path

    def start(self):
        """
        Goes through the steps of the PyRadCSV conversion.
        """
        
















