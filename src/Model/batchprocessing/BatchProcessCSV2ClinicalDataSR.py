import csv
import os
from pathlib import Path
from src.Model.DICOM import DICOMStructuredReport
from src.Model.batchprocessing.BatchProcess import BatchProcess
from src.Model.PatientDictContainer import PatientDictContainer


class BatchProcessCSV2ClinicalDataSR(BatchProcess):
    """
    This class handles batch processing for the CSV2ClinicalData-SR
    process. Inherits from the BatchProcess class.
    """
    # Allowed classes for CSV2ClinicalDataSR
    allowed_classes = {
        # CT Image
        "1.2.840.10008.5.1.4.1.1.2": {
            "name": "ct",
            "sliceable": True
        },
        # PET Image
        "1.2.840.10008.5.1.4.1.1.128": {
            "name": "pet",
            "sliceable": True
        },
        # RT Dose
        "1.2.840.10008.5.1.4.1.1.481.2": {
            "name": "rtdose",
            "sliceable": False
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
        self.required_classes = ['ct', 'rtdose']
        self.required_classes_2 = ['pet', 'rtdose']

        # Only need one of either ct or pet (and rtdose)
        self.ready = False
        ready = self.load_images(patient_files, self.required_classes)
        if ready:
            self.ready = True
        else:
            self.ready = \
                self.load_images(patient_files, self.required_classes_2)
        self.input_path = input_path

    def start(self):
        """
        Goes through the steps of the CSV2ClinicalData-SR conversion.
        :return: True if successful, False if not.
        """
        # Stop loading
        if self.interrupt_flag.is_set():
            self.patient_dict_container.clear()
            self.summary = "INTERRUPT"
            return False

        if not self.ready:
            self.summary = "SKIP"
            return

        # Import CSV data
        self.progress_callback.emit(("Importing CSV data...", 60))
        data_dict = self.import_clinical_data()
        if data_dict is None:
            self.summary = "CSV_NO_PATIENT"
            return

        # Stop loading
        if self.interrupt_flag.is_set():
            self.patient_dict_container.clear()
            self.summary = "INTERRUPT"
            return False

        # Save clinical data to an SR
        self.progress_callback.emit(("Exporting Clinical Data to DICOM-SR...",
                                     90))
        self.save_clinical_data(data_dict)
        return True

    def import_clinical_data(self):
        """
        Attempt to import clinical data from the CSV stored in the
        program's settings database.
        """
        # Clear data dictionary and table
        data_dict = {}

        # Current patient's ID
        patient_dict_container = PatientDictContainer()
        patient_id = patient_dict_container.dataset[0].PatientID

        # Check that the clinical data CSV exists, load data if so
        if self.input_path == "" or self.input_path is None \
                or not os.path.exists(self.input_path):
            return None

        with open(self.input_path, newline="") as stream:
            data = list(csv.reader(stream))

        # See if CSV data matches patient ID
        patient_in_file = False
        row_num = 0
        for i, row in enumerate(data):
            if row[0] == patient_id:
                patient_in_file = True
                row_num = i
                break

        # Return if patient's data not in the CSV file
        if not patient_in_file:
            return None

        # Put patient data into dictionary
        headings = data[0]
        attribs = data[row_num]
        for i, heading in enumerate(headings):
            data_dict[heading] = attribs[i]

        # Return clinical data dictionary
        return data_dict

    def save_clinical_data(self, data_dict):
        """
        Saves clinical data to a DICOM-SR file. Overwrites any existing
        clinical data SR files in the dataset.
        """
        # Create string from clinical data dictionary
        text = ""
        for key in data_dict:
            text += str(key) + ": " + str(data_dict[key]) + "\n"

        # Create and save DICOM SR file
        file_path = self.patient_dict_container.path
        file_path = Path(file_path).joinpath("Clinical-Data-SR.dcm")
        ds = self.patient_dict_container.dataset[0]
        dicom_sr = DICOMStructuredReport.generate_dicom_sr(file_path, ds, text,
                                                           "CLINICAL-DATA")
        dicom_sr.save_as(file_path)