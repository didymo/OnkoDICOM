import os, platform
from radiomics import featureextractor
from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.batchprocessing.BatchProcess import BatchProcess
import pandas as pd
from pathlib import Path


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
            # TODO: convert print to logging
            print("Stopped DVH2CSV")
            self.patient_dict_container.clear()
            return False

        if not self.ready:
            return False

        rtss_path = self.patient_dict_container.filepaths.get('rtss')
        patient_id = self.patient_dict_container.dataset.get('rtss').PatientID
        patient_id = self.clean_patient_id(patient_id)
        patient_path = self.patient_dict_container.path
        file_name = self.clean_patient_id(patient_id) + '.nrrd'
        patient_nrrd_folder_path = patient_path + '/nrrd/'
        patient_nrrd_file_path = patient_nrrd_folder_path + file_name

        output_csv_path = Path.joinpath(self.output_path, 'CSV')

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
            print("Stopped DVH2CSV")
            self.patient_dict_container.clear()
            return False

        # Location of folder where converted masks saved
        mask_folder_path = patient_nrrd_folder_path + 'structures'

        self.progress_callback.emit(("Converting ROIs to nrrd..", 45))

        # Convert ROIs to nrrd
        self.convert_rois_to_nrrd(patient_path, rtss_path, mask_folder_path)

        # Stop loading
        if self.interrupt_flag.is_set():
            # TODO: convert print to logging
            print("Stopped DVH2CSV")
            self.patient_dict_container.clear()
            return False

        self.progress_callback.emit(("Running pyradiomics..", 70))

        # Run pyradiomics, convert to dataframe
        radiomics_df = self.get_radiomics_df(
            patient_path, patient_id, patient_nrrd_file_path, mask_folder_path)

        # Stop loading
        if self.interrupt_flag.is_set():
            # TODO: convert print to logging
            print("Stopped DVH2CSV")
            self.patient_dict_container.clear()
            return False

        self.progress_callback.emit(("Converting to CSV..", 90))

        # Convert the dataframe to CSV file
        self.convert_df_to_csv(radiomics_df, output_csv_path)

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

        :param path:                Path to patient directory (str)
        :param patient_hash:        Patient hash ID generated from their
                                    identifiers
        :param nrrd_file_path:      Path to folder with converted nrrd file
        :param mask_folder_path:    Path to ROI nrrd files
        :return:                    Pandas dataframe
        """

        # Initialize feature extractor using default pyradiomics settings
        extractor = featureextractor.RadiomicsFeatureExtractor()

        # Contains the features for all the ROI
        all_features = []
        # CSV headers
        radiomics_headers = []
        feature_vector = ''

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

    def convert_df_to_csv(self, radiomics_df, csv_path):
        """ Export dataframe as a csv file.
            :param radiomics_df: dataframe containing radiomics data.
            :param csv_path: output folder path.
        """

        # If folder does not exist
        if not os.path.exists(csv_path):
            # Create folder
            os.makedirs(csv_path)

        target_path = Path.joinpath(csv_path, self.filename)

        create_header = not os.path.isfile(target_path)

        # Export dataframe as csv
        radiomics_df.to_csv(target_path, mode='a', header=create_header)

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

    def set_filename(self, name):
        if name != '':
            self.filename = name
        else:
            self.filename = "Pyradiomics_.csv"


