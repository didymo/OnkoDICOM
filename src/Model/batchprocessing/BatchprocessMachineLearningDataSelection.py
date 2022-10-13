from src.Model.batchprocessing.BatchProcess import BatchProcess
from src.Model.PatientDictContainer import PatientDictContainer
import logging
import pandas as pd
import os
import re


class BatchprocessMachineLearningDataSelection(BatchProcess):
    """
    This class handles batch processing for the machine learning
    data selection process. Inherits from the BatchProcessing class.
    """

    def __init__(self, progress_callback, interrupt_flag,
                  dvh_data_path,pyrad_data_path,dvh_value,pyrad_value):
        """
        Class initialiser function.
        :param progress_callback: A signal that receives the current
                                  progress of the loading.
        :param interrupt_flag: A threading.Event() object that tells the
                               function to stop loading.
        :param dvh_data_path: dvh path to file.
        :param pyrad_data_path: pyradiomics path to file.
        :param pyrad_value: selected value for Pyradiomics
        :param dvh_value: selected value for DVH
        """
        # Call the parent class
        super(BatchprocessMachineLearningDataSelection, self).__init__(progress_callback,
                                                          interrupt_flag, 
                                                          None)
        self.dvh_data_path = dvh_data_path
        self.pyrad_data_path = pyrad_data_path

        self.pyrad_value = pyrad_value
        self.dvh_value = dvh_value

        self.dvh_data = None
        self.pyrad_data = None

    def start(self):
        """
        Goes through the steps of the ClinicalData filtering.
        :return: True if successful, False if not.
        """
        # reading file
        self.progress_callback.emit(("Reading Pyradiomics and DVH Data..", 20))
        self.read_csv()
        
        # Machine learning
        self.progress_callback.emit(("Filtering DVH and Pyradiomics Model..", 50))
        self.filter_data()
        self.progress_callback.emit(("Saving results...", 80))
        self.save_files()

        # Set summary
        self.summary = "Completed Machine learning data selection Process"

        return True

    def read_csv(self):
        if self.dvh_data_path != None and self.pyrad_data_path != None:
            self.dvh_data = pd.read_csv(f'{self.dvh_data_path}', on_bad_lines='skip')
            self.pyrad_data = pd.read_csv(f'{self.pyrad_data_path}')
        else:
            logging.warning('DVH and Pyradiomics Path not selected')

    def filter_data(self):
        self.dvh_data = self.dvh_data[self.dvh_data['ROI'] == self.pyrad_value]
        self.pyrad_data = self.pyrad_data[self.pyrad_data['ROI'] == self.dvh_value]

    def split_path(self, path_to_file):
        pattern = r'/'
        path = re.split(pattern, path_to_file)[:-1]
        modified_path = "/".join(path)
        return modified_path

    def save_files(self):
        # Create directory
        dir_name_dvh = f'{self.split_path(self.dvh_data_path)}/dvh_modifed'
        dir_name_pyrad = f'{self.split_path(self.pyrad_data_path)}/pyradiomics_modifed'
        filename_dvh = "OnkoDICOM.DVH_Clinical_Data.csv"
        filename_pyrard = "OnkoDICOM.Pyradiomics_Clinical_Data.csv"

        try:
            # Create Pyradiomics Directory
            os.mkdir(dir_name_pyrad)
        except FileExistsError:
            logging.debug('Directory already exists')
        try:
            # Create dvh Directory
            os.mkdir(dir_name_dvh)
        except FileExistsError:
            logging.debug('Directory already exists')

        self.dvh_data.to_csv(f'{dir_name_dvh}/{filename_dvh}', sep=',')
        self.pyrad_data.to_csv(f'{dir_name_pyrad}/{filename_pyrard}', sep=',')
