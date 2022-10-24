from src.Model.batchprocessing.BatchProcess import BatchProcess
from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.batchprocessing.batchprocessingMachineLearning.\
    Preprocessing import Preprocessing
from src.Model.batchprocessing.batchprocessingMachineLearning.\
    MachineLearningTrainingStage import MlModeling
import logging


class BatchProcessMachineLearning(BatchProcess):
    """
    This class handles batch processing for the machine learning
    process. Inherits from the BatchProcessing class.
    """

    def __init__(self, progress_callback, interrupt_flag,
                 options, clinical_data_path, dvh_data_path, pyrad_data_path):
        """
        Class initialiser function.
        :param progress_callback: A signal that receives the current
                                  progress of the loading.
        :param interrupt_flag: A threading.Event() object that tells the
                               function to stop loading.
        :param options: list of values for machine learning
        :param clinical_data_path: clinical data path to file.
        :param dvh_data_path: dvh path to file.
        :param pyrad_data_path: pyradiomics path to file.
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
        self.X_train_for_confusion_matrix = None
        self.X_test = None
        self.y_train = None
        self.y_train_for_confusion_matrix = None
        self.y_test = None
        self.params = None
        self.scaling = None
        self.run_model_accept = None

    def start(self):
        """
        Goes through the steps of the machine learning.
        :return: True if successful, False if not.
        """
        # Preprocessing
        self.progress_callback.emit(("Preprocessing Data..", 20))
        self.preprocessing_for_ml()

        # Machine learning
        self.progress_callback.emit(("Running Model..", 50))
        self.run_model()

        self.progress_callback.emit(("Writing results...", 80))

        if self.run_model_accept is not None:
            self.summary = "Failed Machine learning Process.\n" \
                           "Your Dataset is too small.\n" \
                           "According to DVH and Pyradiomics Datasets" \
                           "found less than 2 cross IDs:\n" \
                           f"{self.preprocessing.permission_ids}"
        else:
            self.summary = "Complete Machine learning Process"

        return True

    def get_results_values(self):
        """
        Function return result of Model.
        """
        return self.machine_learning_options

    def get_run_model_accept(self):
        """
        Function return if Training model function were used
        if so then it will display the result of the model.
        """
        return self.run_model_accept

    def preprocessing_for_ml(self):
        """
        Function does preprocessing of provided data
        for all descriptions of Preprocessing class and functions
        please refer to class Preprocessing.
        """
        self.preprocessing = Preprocessing(
            path_clinical_data=self.clinical_data_path,
            path_pyr_data=self.pyrad_data_path,
            path_dvh_data=self.dvh_data_path,
            column_names=self.machine_learning_options['features'],
            type_column=self.machine_learning_options['type'],
            target=self.machine_learning_options['target'],
            rename_values=self.machine_learning_options['renameValues']
        )
        if self.preprocessing.check_preprocessing_data():
            self.X_train, self.X_test, self.y_train, self.y_test =\
                self.preprocessing.prepare_for_ml()
            self.params =\
                self.preprocessing.get_params_clinical_data()
            self.scaling =\
                self.preprocessing.scaling
            self.machine_learning_options['features'] =\
                self.preprocessing.column_names
            self.X_train_for_confusion_matrix = self.preprocessing.x_train_for_confusion_matrix
            self.y_train_for_confusion_matrix = self.preprocessing.y_train_for_confusion_matrix
        self.run_model_accept =\
            self.preprocessing.permission

    def run_model(self):
        """
        Function train machine learning model
        for all descriptions of Machine learning class and functions
        please refer to class MachineLearningTrainingStage.py.
        """
        if self.run_model_accept is None:
            self.run_ml = MlModeling(
                self.X_train,
                self.X_test,
                self.X_train_for_confusion_matrix,
                self.y_train_for_confusion_matrix,
                self.y_train,
                self.y_test,
                self.preprocessing.target,
                self.preprocessing.type_column,
                tuning=self.machine_learning_options['tune'],
                permission=self.run_model_accept)

            self.run_ml.run_model()
            self.ml_model = self.run_ml
            # Set outputs
            self.machine_learning_options.update(self.run_ml.accuracy)

        else:
            logging.debug('Failed Run Ml Model')
