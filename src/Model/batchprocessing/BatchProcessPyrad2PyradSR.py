import csv
import os
import shutil
from pathlib import Path
from src.Model import DICOMStructuredReport
from src.Model import Radiomics
from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.batchprocessing.BatchProcess import BatchProcess


class BatchProcessPyRad2PyRadSR(BatchProcess):
    """
    This class handles batch processing for the PyRad2PyRad-SR process.
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

    def __init__(self, progress_callback, interrupt_flag, patient_files):
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
        super(BatchProcessPyRad2PyRadSR, self).__init__(progress_callback,
                                                        interrupt_flag,
                                                        patient_files)

        # Set class variables
        self.patient_dict_container = PatientDictContainer()
        self.required_classes = 'rtss'.split()
        self.ready = self.load_images(patient_files, self.required_classes)
        self.output_path = ""

    def start(self):
        """
        Goes through the steps of the PyRad2Pyrad-SR conversion.
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
        patient_id = self.patient_dict_container.dataset.get(
            'rtss').PatientID
        patient_id = Radiomics.clean_patient_id(patient_id)
        patient_path = self.patient_dict_container.path
        file_name = Radiomics.clean_patient_id(patient_id) + '.nrrd'
        patient_nrrd_folder_path = patient_path + '/nrrd/'
        patient_nrrd_file_path = patient_nrrd_folder_path + file_name

        output_csv_path = patient_path + '/CSV/'

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
        Radiomics.convert_rois_to_nrrd(patient_path, rtss_path,
                                       mask_folder_path)

        # Stop loading
        if self.interrupt_flag.is_set():
            self.patient_dict_container.clear()
            self.summary = "INTERRUPT"
            return False

        self.progress_callback.emit(("Running pyradiomics..", 70))

        # Run pyradiomics, convert to dataframe
        radiomics_df = Radiomics.get_radiomics_df(
            patient_path, patient_id, patient_nrrd_file_path,
            mask_folder_path)

        # Stop loading
        if self.interrupt_flag.is_set():
            self.patient_dict_container.clear()
            self.summary = "INTERRUPT"
            return False

        if radiomics_df is None:
            self.summary = "PYRAD_NO_DF"
            return False

        # Convert the dataframe to CSV file
        self.progress_callback.emit(("Converting to CSV..", 85))
        Radiomics.convert_df_to_csv(radiomics_df, output_csv_path, patient_id)

        # Convert resulting CSV to DICOM-SR
        self.progress_callback.emit(("Exporting to DICOM-SR..", 90))
        self.export_to_sr(output_csv_path, patient_id)

        # Delete CSV file and NRRD folder
        shutil.rmtree(patient_nrrd_folder_path)
        os.remove(output_csv_path + 'Pyradiomics_' + patient_id + '.csv')

        return True

    def export_to_sr(self, csv_path, patient_hash):
        """
        Save CSV data into DICOM SR. Reads in CSV data and saves it to
        a DICOM SR file
        :param csv_path: the path that the CSV has been saved to.
        :param patient_hash: the patient's hash as a string.
        """
        # Check CSV path exists
        file_path = Path(csv_path).joinpath('Pyradiomics_' + patient_hash +
                                            ".csv")
        if file_path == "":
            return

        # Get CSV data
        with open(file_path, newline="") as stream:
            data = list(csv.reader(stream))

        # Write raw CSV data to DICOM SR
        text = ""
        for line in data:
            for item in line:
                text += str(item) + ","
            text += "\n"

        # Create and save DICOM SR file
        file_path = self.patient_dict_container.path
        file_path = Path(file_path).joinpath("Pyradiomics-SR.dcm")
        ds = next(iter(self.patient_dict_container.dataset.values()))
        dicom_sr = DICOMStructuredReport.generate_dicom_sr(file_path, ds, text,
                                                           "PYRADIOMICS")
        dicom_sr.save_as(file_path)

        # Update patient dict container
        self.patient_dict_container.dataset['sr-pyrad'] = dicom_sr
        self.patient_dict_container.filepaths['sr-pyrad'] = file_path
