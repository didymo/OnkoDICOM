from src.Model.batchprocessing.BatchProcess import BatchProcess
import logging
import pandas as pd
import os
import re


class BatchprocessMachineLearningDataSelection(BatchProcess):
    """
    This class handles batch processing for the machine learning
    data selection process. Inherits from the BatchProcessing class.
    """

    def __init__(self, progress_callback,
                 dvh_data_path, pyrad_data_path,
                 dvh_value, pyrad_value):
        """
        Class initialiser function.
        :param progress_callback: A signal that receives the current
                                  progress of the loading.

        :param dvh_data_path: dvh path to file.
        :param pyrad_data_path: pyradiomics path to file.
        :param dvh_value: selected value for DVH
        :param pyrad_value: selected value for Pyradiomics
        """
        # Call the parent class
        super(BatchprocessMachineLearningDataSelection, self).__init__(
            progress_callback,
            None,
            None)
        self.dvh_data_path = dvh_data_path
        self.pyrad_data_path = pyrad_data_path

        self.dvh_value = dvh_value
        self.pyrad_value = pyrad_value

        self.dvh_data = None
        self.pyrad_data = None

        self.full_path_dvh = None
        self.full_path_pyrad = None

    def start(self):
        """
        Goes through the steps of the ClinicalData filtering.
        :return: True if successful, False if not.
        """
        # reading file
        self.progress_callback.emit(
            ("Reading Pyradiomics and DVH Data..", 20)
            )

        if not self.read_csv():
            self.summary = "Failed Machine learning data selection" \
                "Process. Files incorrectly selected."
            return False

        # Machine learning
        self.progress_callback.emit(
            ("Filtering DVH and Pyradiomics Model..", 50)
            )
        self.filter_data()
        self.progress_callback.emit(("Saving results...", 80))
        self.save_files()

        # Set summary
        self.summary = f"Completed Machine learning data selection Process\n" \
                       f"DVH path: {self.full_path_dvh}\n" \
                       f"Pyradiomics path {self.full_path_pyrad}"

        return True

    def read_csv(self):
        """
        Function reads DVH and Pyradiomics csv Files
        """
        if self.dvh_data_path is not None and self.pyrad_data_path is not None:
            self.dvh_data = pd.read_csv(
                f'{self.dvh_data_path}',
                on_bad_lines='skip'
                )
            self.pyrad_data = pd.read_csv(f'{self.pyrad_data_path}')
            return True
        else:
            return False

    def filter_data(self):
        """
        Function selects from DVH
        and Pyradiomcs Values that were selected for ROI
        """
        self.dvh_data = self.dvh_data[self.dvh_data['ROI'] == self.dvh_value]
        self.pyrad_data = \
            self.pyrad_data[self.pyrad_data['ROI'] == self.pyrad_value]

    def split_path(self, path_to_file):
        """
        Function split path
        provided for DVH and Pyradiomics
        """
        pattern = r'/'
        path = re.split(pattern, path_to_file)[:-1]
        modified_path = "/".join(path)
        return modified_path

    def save_files(self):
        """
        Function saves files DVH and Pyradiomics
        """
        # Create directory
        dir_name_dvh = f'{self.split_path(self.dvh_data_path)}' \
                       f'/dvh_modified'
        dir_name_pyrad = f'{self.split_path(self.pyrad_data_path)}' \
                         f'/pyradiomics_modified'

        filename_dvh = 'OnkoDICOM.DVH_Data.csv'
        filename_pyrard = 'OnkoDICOM.Pyradiomics_Data.csv'

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

        self.full_path_dvh = f'{dir_name_dvh}/{filename_dvh}'
        self.full_path_pyrad = f'{dir_name_pyrad}/{filename_pyrard}'

        self.dvh_data.to_csv(self.full_path_dvh, sep=',')
        self.pyrad_data.to_csv(self.full_path_pyrad, sep=',')
