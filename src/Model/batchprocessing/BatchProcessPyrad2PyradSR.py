import os, shutil, csv, platform
import pandas as pd
from pathlib import Path
from src.Model import DICOMStructuredReport
from radiomics import featureextractor
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
            # TODO: convert print to logging
            print("Stopped PyRad2Pyrad-SR")
            self.patient_dict_container.clear()
            self.summary = "INTERRUPT"
            return False

        if not self.ready:
            self.summary = "SKIP"
            return False

        rtss_path = self.patient_dict_container.filepaths.get('rtss')
        patient_id = self.patient_dict_container.dataset.get(
            'rtss').PatientID
        patient_id = self.clean_patient_id(patient_id)
        patient_path = self.patient_dict_container.path
        file_name = self.clean_patient_id(patient_id) + '.nrrd'
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
        self.convert_to_nrrd(patient_path, patient_nrrd_file_path)

        # Stop loading
        if self.interrupt_flag.is_set():
            # TODO: convert print to logging
            print("Stopped PyRad2Pyrad-SR")
            self.patient_dict_container.clear()
            self.summary = "INTERRUPT"
            return False

        # Location of folder where converted masks saved
        mask_folder_path = patient_nrrd_folder_path + 'structures'
        if not os.path.exists(mask_folder_path):
            os.makedirs(mask_folder_path)

        self.progress_callback.emit(("Converting ROIs to nrrd..", 45))

        # Convert ROIs to nrrd
        self.convert_rois_to_nrrd(patient_path, rtss_path,
                                  mask_folder_path)

        # Stop loading
        if self.interrupt_flag.is_set():
            # TODO: convert print to logging
            print("Stopped PyRad2Pyrad-SR")
            self.patient_dict_container.clear()
            self.summary = "INTERRUPT"
            return False

        self.progress_callback.emit(("Running pyradiomics..", 70))

        # Run pyradiomics, convert to dataframe
        radiomics_df = self.get_radiomics_df(
            patient_path, patient_id, patient_nrrd_file_path,
            mask_folder_path)

        # Stop loading
        if self.interrupt_flag.is_set():
            # TODO: convert print to logging
            print("Stopped PyRad2Pyrad-SR")
            self.patient_dict_container.clear()
            self.summary = "INTERRUPT"
            return False

        if radiomics_df is None:
            self.summary = "PYRAD_NO_DF"
            return False

        # Convert the dataframe to CSV file
        self.progress_callback.emit(("Converting to CSV..", 85))
        self.convert_df_to_csv(radiomics_df, output_csv_path, patient_id)

        # Convert resulting CSV to DICOM-SR
        self.progress_callback.emit(("Exporting to DICOM-SR..", 90))
        self.export_to_sr(output_csv_path, patient_id)

        # Delete CSV file and NRRD folder
        shutil.rmtree(patient_nrrd_folder_path)
        os.remove(output_csv_path + 'Pyradiomics_' + patient_id + '.csv')

        return True

    @staticmethod
    def convert_to_nrrd(path, nrrd_output_path):
        """
        Convert dicom files to nrrd.
        :param path:            Path to patient directory (str)
        :param nrrd_file_path:  Path to nrrd folder (str)
        """
        path = '"' + path + '"'
        nrrd_file_path = '"' + nrrd_output_path + '"'

        # Command to convert dicom files to nrrd
        # Writes the result from the processing into a temporary file
        # rather than the terminal
        cmd_for_nrrd = 'plastimatch convert --input ' + path + \
            ' --output-img ' + nrrd_file_path + ' 1>' + path + '/NUL'

        # Command to delete the temporary file generated before
        cmd_del_nul = 'rm ' + path + '/NUL'

        os.system(cmd_for_nrrd)

        if os.path.exists(path + '/NUL'):
            if platform.system() != "Windows":
                os.system(cmd_del_nul)
            else:
                cmd_del_nul = 'del ' + path + '/NUL'
                os.system(cmd_del_nul)

    @staticmethod
    def convert_rois_to_nrrd(path, rtss_path, mask_folder_path):
        """
        Generate an nrrd file for each region of interest using Plastimatch.
        :param path:                Path to patient directory (str)
        :param rtss_path:           Path to RT-Struct file (str)
        :param mask_folder_path:    Folder to which the segmentation masks
                                    will be saved(str)
        """
        path = '"' + path + '"'
        mask_folder_path = '"' + mask_folder_path + '"'
        rtss_path = '"' + rtss_path + '"'
        # Command for generating an nrrd file for each region of interest
        cmd_for_segmask = 'plastimatch convert --input ' + rtss_path + \
            ' --output-prefix ' + mask_folder_path + \
            ' --prefix-format nrrd --referenced-ct ' + path + ' 1>' + \
            path + '/NUL'
        cmd_del_nul = 'rm ' + path + '/NUL'
        os.system(cmd_for_segmask)

        if os.path.exists(path + '/NUL'):
            if platform.system() != "Windows":
                os.system(cmd_del_nul)
            else:
                cmd_del_nul = 'del ' + path + '/NUL'
                os.system(cmd_del_nul)

    @staticmethod
    def get_radiomics_df(path, patient_hash, nrrd_file_path,
                         mask_folder_path):
        """
        Run pyradiomics and return pandas dataframe with all the computed data.
        :param path: Path to patient directory (str).
        :param patient_hash: Patient hash ID generated from their
                             identifiers.
        :param nrrd_file_path: Path to folder with converted nrrd file.
        :param mask_folder_path: Path to ROI nrrd files.
        :return: Pandas dataframe.
        """

        # Initialize feature extractor using default pyradiomics settings
        extractor = featureextractor.RadiomicsFeatureExtractor()

        # Contains the features for all the ROI
        all_features = []
        # CSV headers
        radiomics_headers = []
        feature_vector = ''

        # If RTSS selected has no ROIS
        if not os.listdir(mask_folder_path):
            return None

        for file in os.listdir(mask_folder_path):
            # Contains features for current ROI
            roi_features = []
            roi_features.append(patient_hash)
            roi_features.append(path)
            # Full path of ROI nrrd file
            mask_name = mask_folder_path + '/' + file
            # Name of ROI
            image_id = file.split('.')[0]
            feature_vector = extractor.execute(nrrd_file_path, mask_name)
            roi_features.append(image_id)

            # Add first order features to list
            for feature_name in feature_vector.keys():
                roi_features.append(feature_vector[feature_name])

            all_features.append(roi_features)

        radiomics_headers.append('Hash ID')
        radiomics_headers.append('Directory Path')
        radiomics_headers.append('ROI')

        # Extract column/feature names
        for feature_name in feature_vector.keys():
            radiomics_headers.append(feature_name)

        # Convert into dataframe
        radiomics_df = pd.DataFrame(all_features, columns=radiomics_headers)

        radiomics_df.set_index('Hash ID', inplace=True)

        return radiomics_df

    def convert_df_to_csv(self, radiomics_df, csv_path, patient_hash):
        """
        Export dataframe as a csv file.
        :param radiomics_df: dataframe containing radiomics data.
        :param csv_path: output folder path.
        :param patient_hash: patient's hash
        """

        # If folder does not exist
        if not os.path.exists(csv_path):
            # Create folder
            os.makedirs(csv_path)

        target_path = csv_path + 'Pyradiomics_' + patient_hash + '.csv'

        create_header = not os.path.isfile(target_path)

        # Export dataframe as csv
        radiomics_df.to_csv(target_path, header=create_header)

    @staticmethod
    def clean_patient_id(patient_id):
        """
        Removes characters that cannot be used as part of file names.
        :param patient_id: patients ID
        return: cleaned up patient_id
        """
        invalid_characters = '/\:*?"<>|'

        filename = ''

        for c in patient_id:
            if c not in invalid_characters:
                filename += c

        return filename

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
        # TODO: create better implementation of this - requires
        #       generated SR files to be more structured.
        # Convert CSV data to text
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
