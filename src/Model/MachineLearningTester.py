from src.Model.batchprocessing \
    .batchprocessingMachineLearning.Preprocessing import Preprocessing
import pandas as pd
import logging
import joblib
pd.options.mode.chained_assignment = None  # default='warn'


class MachineLearningTester:
    """
    Machine Learning class that can load in a previously saved class,
    and use it with new csv data to predict a target column.
    """
    def __init__(self,
                 clinical_data_csv_path,
                 dvh_csv_path,
                 pyrad_csv_path,
                 saved_model_path,
                 model_name):
        """
        Initialises class.
        """
        self.clinical_data_csv_path = clinical_data_csv_path
        self.dvh_csv_path = dvh_csv_path
        self.pyrad_csv_path = pyrad_csv_path
        self.saved_model_path = saved_model_path
        self.model_name = model_name
        self.predicted_column_name = ""

    def get_predicted_values(self):
        """
        Gets the predicted values as a list
        Returns:
            list : predicted values for specified target
        """
        return self.predictions

    def get_target(self):
        """
        Gets the target that is the columnn named being
        predicted
        """
        return self.predicted_column_name

    def get_model_name(self):
        """
        Returns the model name being used
        """
        return self.model_name

    def predict_values(self):
        """
        Actually predicts the values using the supplied
        csv data and stores predictions in self.predictions
        """
        logging.debug("MachineLearningTester.predict_values() function called")
        scaler_file_name = \
            f"{self.saved_model_path}/{self.model_name}_scaler.pkl"
        params_file_name = \
            f"{self.saved_model_path}/{self.model_name}_params.txt"
        ml_file_name = \
            f"{self.saved_model_path}/{self.model_name}_ml.pkl"

        logging.debug(f"Scaler file name: {scaler_file_name}")
        logging.debug(f"Params file name: {params_file_name}")
        logging.debug(f"ML Model file name: {ml_file_name}")

        column_names_being_used, self.predicted_column_name = \
            self.read_txt_ml_params(
                params_file_name
            )

        logging.debug(f"Columns being used in ML: {column_names_being_used}")
        logging.debug(f"Predicted column name: {self.predicted_column_name}")

        testing_data = Preprocessing(
            path_clinical_data=self.clinical_data_csv_path,
            path_pyr_data=self.pyrad_csv_path,
            path_dvh_data=self.dvh_csv_path,
            column_names=column_names_being_used
        )

        self.data, self.ID = testing_data.prepare_for_ml()
        logging.debug(f"MachineLearningTester.data: {self.data}")
        logging.debug(f"MachineLearningTester.ID: {column_names_being_used}")

        scaler = self.get_saved_model(scaler_file_name)

        scaled_data = self.scale(scaler, self.data)

        saved_model = self.get_model_file(ml_file_name)

        self.predictions = self.predict(saved_model, scaled_data)
        logging.debug(f"MachineLearningTester.predictions: {self.predictions}")

        return True

    def save_into_csv(self, path_to_save):
        """
        Saves predicted values into csv.
        Parameters:
            str : path_to_save : location to save csv
        """
        # TODO: is all this necessary?
        new_data = pd.read_csv(self.clinical_data_csv_path)
        new_data = new_data[['HASHidentifier']]
        pyrad = pd.read_csv(self.pyrad_csv_path).rename(
            columns={"Hash ID": "HASHidentifier"}
            )[['HASHidentifier', 'ROI']]
        self.data['HASHidentifier'] = self.ID
        self.data[self.predicted_column_name] = self.predictions
        self.data = self.data[[
            'HASHidentifier',
            self.predicted_column_name
            ]]
        final_data = pyrad.merge(self.data, how='left', on='HASHidentifier')
        final_data = new_data.merge(
            final_data, how='left', on='HASHidentifier')
        final_data = final_data.drop_duplicates(
            subset=['HASHidentifier', 'ROI']).reset_index(drop=True)
        final_data.to_csv(
            f"{path_to_save}/Clinical_data_with_predicted_"
            f"{self.get_target()}.csv",
            index=False
            )

    def read_txt_ml_params(self, path):
        """
        Reads in txt machine learning params
        Parameters:
            str: path : location to read from
        """
        my_file = open(f"{path}", "r")
        content = my_file.read()
        content = content \
            .replace('[', '') \
            .replace(']', '') \
            .replace("'", "") \
            .replace('\n', "") \
            .replace(" ", "")
        content_list = content.split(",")

        return content_list[:-1], content_list[len(content_list)-1]

    def get_saved_model(self, path_pipline):
        """
        Reads in saved model
        Parameters:
            str: path_pipline : location to read from
        """
        pipline_joblib = joblib.load(path_pipline)
        return pipline_joblib

    def scale(self, pipline_joblib, data):
        """
        Transforms data to scaled data
        Parameters:
            pipline_joblib : saved model
            data : dato to be scaled
        """
        scaled_data = pipline_joblib.transform(data)
        return scaled_data

    def get_model_file(self, ml_modelfile):
        """
        Load in model file
        Parameters:
            ml_modelfile : model to load in
        """
        ml_model = joblib.load(ml_modelfile)
        return ml_model

    def predict(self, saved_model, scaledata):
        """
        Uses scaled data and model to predict values
        Parameters:
            save_model : the saved model
            scaledata : dato that has been scaled
        """
        predicted = saved_model.predict(scaledata)
        return predicted
