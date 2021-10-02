import os
import platform
from radiomics import featureextractor
from src.Model import Radiomics
from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.batchprocessing.BatchProcess import BatchProcess
import pandas as pd


class BatchProcessPyRad2CSV(BatchProcess):
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
        super(BatchProcessPyRad2CSV, self).__init__(progress_callback,
                                                   interrupt_flag,
                                                   patient_files)

        # Set class variables
        self.patient_dict_container = PatientDictContainer()
        self.required_classes = 'rtss'.split()
        self.ready = self.load_images(patient_files, self.required_classes)
        self.output_path = output_path
        self.filename = "Pyradiomics_.csv"

    def start(self):
        """
        Goes through the steps of the PyRadCSV conversion.
        """
        # Stop loading
        if self.interrupt_flag.is_set():
            self.patient_dict_container.clear()
            self.summary = "INTERRUPT"
            return False

        if not self.ready:
            self.summary = "SKIP"
            return False

        rtss_path = self.patient_dict_container.filepaths.get('rtss')
        patient_id = self.patient_dict_container.dataset.get('rtss').PatientID
        patient_id = Radiomics.clean_patient_id(patient_id)
        patient_path = self.patient_dict_container.path
        file_name = Radiomics.clean_patient_id(patient_id) + '.nrrd'
        patient_nrrd_folder_path = patient_path + '/nrrd/'
        patient_nrrd_file_path = patient_nrrd_folder_path + file_name

        output_csv_path = self.output_path.joinpath('CSV')

        # If folder does not exist
        if not os.path.exists(patient_nrrd_folder_path):
            # Create folder
            os.makedirs(patient_nrrd_folder_path)

        # If folder does not exist
        if not os.path.exists(output_csv_path):
            # Create folder
            os.makedirs(output_csv_path)

        self.progress_callback.emit(("Converting dicom to nrrd..", 25))

        # Convert dicom files to nrrd for pyradiomics processing
        Radiomics.convert_to_nrrd(patient_path, patient_nrrd_file_path)

        # Stop loading
        if self.interrupt_flag.is_set():
            self.patient_dict_container.clear()
            self.summary = "INTERRUPT"
            return False

        # Location of folder where converted masks saved
        mask_folder_path = patient_nrrd_folder_path + 'structures'
        if not os.path.exists(mask_folder_path):
            os.makedirs(mask_folder_path)

        self.progress_callback.emit(("Converting ROIs to nrrd..", 45))

        # Convert ROIs to nrrd
        Radiomics.convert_rois_to_nrrd(
            patient_path, rtss_path, mask_folder_path)

        # Stop loading
        if self.interrupt_flag.is_set():
            self.patient_dict_container.clear()
            self.summary = "INTERRUPT"
            return False

        self.progress_callback.emit(("Running pyradiomics..", 70))

        # Run pyradiomics, convert to dataframe
        radiomics_df = Radiomics.get_radiomics_df(
            patient_path, patient_id, patient_nrrd_file_path, mask_folder_path)

        # Stop loading
        if self.interrupt_flag.is_set():
            self.patient_dict_container.clear()
            self.summary = "INTERRUPT"
            return False

        if radiomics_df is None:
            self.summary = "PYRAD_NO_DF"
            return False

        # Convert the dataframe to CSV file
        self.progress_callback.emit(("Converting to CSV..", 90))
        Radiomics.convert_df_to_csv(radiomics_df, output_csv_path, patient_id)
        return True

    def set_filename(self, name):
        if name != '':
            self.filename = name
        else:
            self.filename = "Pyradiomics_.csv"
