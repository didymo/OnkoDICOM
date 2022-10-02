from pathlib import Path
from src.Model.batchprocessing.BatchProcess import BatchProcess
from src.Model.PatientDictContainer import PatientDictContainer
import logging
from src.Model.batchprocessing.batchprocessingMachineLearning.PreprocessingClass import Preprocessing
from src.Model.batchprocessing.batchprocessingMachineLearning.MlCLass import MlModeling


class BatchProcessMachineLearning(BatchProcess):
    """
    This class handles batch processing for the Selecting subgroup
    process. Inherits from the BatchProcessing class.
    """

    # Allowed classes for ClinicalDataSR2CSV
    # allowed_classes = {
    #     # Comprehensive SR
    #     "1.2.840.10008.5.1.4.1.1.88.33": {
    #         "name": "sr",
    #         "sliceable": False
    #     }
    # }

    def __init__(self, progress_callback, interrupt_flag,
                 options, clinical_data_path, dvh_data_path, pyrad_data_path):
        """
        Class initialiser function.
        :param progress_callback: A signal that receives the current
                                  progress of the loading.
        :param interrupt_flag: A threading.Event() object that tells the
                               function to stop loading.
        :param patient_files: List of patient files.
        :param selected_filters: dictionary of keys and lists of valid values
        to filter by in the patients clinical-data-sr file (if one exists)
        """
        # Call the parent class
        super(BatchProcessMachineLearning, self).__init__(progress_callback,
                                                          interrupt_flag,
                                                          options)

        # Set class variables
        self.patient_dict_container = PatientDictContainer()
        # self.required_classes = ['sr']
        self.machine_learning_options = options
        self.ml_model = None

        # path
        self.clinical_data_path = clinical_data_path
        self.dvh_data_path = dvh_data_path
        self.pyrad_data_path = pyrad_data_path

        self.preprocessing = None
        self.run_ml = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.params = None
        self.scaling = None

    def start(self):
        """
        Goes through the steps of the ClinicalData filtering.
        :return: True if successful, False if not.
        """
        # TODO: add all the necessary steps here to do machine learning
        # all options are in the self.machine_learning_options
        # Expected to set a variable:
        # 1) self.ml_model which is the ML model?
        # AND
        # 2) The variables needed in the results, eg. self.accuracy
        # Also needs a functions 'def get_results_values()'

        # Preprocessing
        self.preprocessing_for_ml()
        print("Run Start")
        self.run_model()
        self.machine_learning_options.update(self.run_ml.accuracy)
        # Machine learning

        # Stop loading
        # if self.interrupt_flag.is_set():
        #     self.patient_dict_container.clear()
        #     self.summary = "INTERRUPT"
        #     return False

        # if not self.ready:
        #     self.summary = "SKIP"
        #     return False

        # # See if SR contains clinical data
        # self.progress_callback.emit(("Checking SR file...", 20))
        # cd_sr = self.find_clinical_data_sr()

        # if cd_sr is None:
        #     self.summary = "CD_NO_SR"
        #     return False

        # # Stop loading
        # if self.interrupt_flag.is_set():
        #     self.patient_dict_container.clear()
        #     self.summary = "INTERRUPT"
        #     return False

        # # Read in clinical data from SR
        # self.progress_callback.emit(("Reading clinical data...", 50))
        # data_dict = self.read_clinical_data_from_sr(cd_sr)

        # # Stop loading
        # if self.interrupt_flag.is_set():
        #     self.patient_dict_container.clear()
        #     self.summary = "INTERRUPT"
        #     return False

        # Write clinical data to CSV
        # self.progress_callback.emit(("Writing clinical data to CSV...", 80))
        # self.check_if_patient_meets_filter_criteria(data_dict)

        return True

    def get_results_values(self):
        return self.machine_learning_options

    def find_clinical_data_sr(self):
        """
        Searches the patient dict container for any SR files containing
        clinical data. Returns the first SR with clinical data found.
        :return: ds, SR dataset containing clinical data, or None if
                 nothing found.
        """
        datasets = self.patient_dict_container.dataset

        if not datasets:
            return None

        for ds in datasets:
            # Check for SR files
            if datasets[ds].SOPClassUID == "1.2.840.10008.5.1.4.1.1.88.33":
                # Check to see if it is a clinical data SR
                if datasets[ds].SeriesDescription == "CLINICAL-DATA":
                    return datasets[ds]

        return None

    def read_clinical_data_from_sr(self, sr_cd):
        """
        Reads clinical data from the found SR file.
        :param sr_cd: the clinical data SR dataset.
        :return: dictionary of clinical data, where keys are attributes
                 and values are data.
        """
        data = sr_cd.ContentSequence[0].TextValue

        data_dict = {}

        data_list = data.split("\n")
        for row in range(len(data_list)):
            value = data_list[row].strip()
            if value == "":
                continue
            # Assumes neither data nor attributes have colons
            row_data = value.split(":")
            data_dict[row_data[0]] = row_data[1][1:]

        return data_dict

    def check_if_patient_meets_filter_criteria(self, data_dict):
        """
        Checks if data_dict from patients clinical data contains a match
        from the selected_filters dictionary.
        :param sr_cd: the patients clinical data SR dataset.
        """
        for filter_attribute, allowed_values in self.selected_filters.items():
            try:
                patient_value = data_dict[filter_attribute]

                if len(allowed_values) == 0:
                    continue

                if patient_value in allowed_values:
                    logging.debug("Patient within filter")
                    self.within_filter = True
                    break
            except KeyError:
                # they have an sr file that does not contain this trait
                continue

        logging.debug("Patient NOT within filter")

    def preprocessing_for_ml(self):
        self.preprocessing = Preprocessing(
            pathClinicalData=self.clinical_data_path  # Path to Clinical Data
            , pathPyrData=self.pyrad_data_path  # Path to Pyrad Data
            , pathDVHData=self.dvh_data_path  # Path to DVH Data
            , columnNames=self.machine_learning_options['features']  # DR. Selects Columns
            , typeOfColumn=self.machine_learning_options['type']  # Type of Column (Category/Numerical)
            , target=self.machine_learning_options['target']  # Target Column to be predicted for training
            , renameValues=self.machine_learning_options['renameValues']  # Dr. rename values in Target Column
        )
        self.X_train, self.X_test, self.y_train, self.y_test = self.preprocessing.prepareforML()
        self.params = self.preprocessing.saveParam()
        self.scaling = self.preprocessing.scaling

    def run_model(self):
        self.run_ml = MlModeling(self.X_train  # Dataset X_train that we got from preprocessing class
                                   , self.X_test  # Dataset X_test that we got from preprocessing class
                                   , self.y_train  # Dataset Y_train that we got from preprocessing class
                                   , self.y_test  # Dataset Y_train that we got from preprocessing class
                                   , self.preprocessing.target  # Label Column (can be exported from Preprocessing )
                                   , self.preprocessing.typeOfColumn #type of the ML
                                   , tunning=self.machine_learning_options['tune']  # Tunning
                                   )
        result = self.run_ml.runModel()
        self.ml_model = self.run_ml
        print('PRINTING ML MODEL NAME',self.ml_model)
        print('PRINTING ML ACCURACY', self.run_ml.accuracy)




