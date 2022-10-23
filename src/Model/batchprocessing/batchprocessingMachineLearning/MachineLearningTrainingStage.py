import pandas as pd
import numpy as np

# scoring
from sklearn.metrics import (confusion_matrix, accuracy_score,
                             f1_score, make_scorer)

from imblearn.metrics import geometric_mean_score

from sklearn.model_selection import GridSearchCV  # Fine Tune Model

# classifiers Models
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier

# regression Models
from sklearn.ensemble import RandomForestRegressor  # Random Forest
from sklearn.neural_network import MLPRegressor  # MLP Regressor

import logging
import os
import joblib


class MlModeling():
    """
    This class Train ML model
    """

    def __init__(self,
                 train_feature,
                 test_feature,
                 train_feature_dataset_for_confusion_matrix,
                 train_label_dataset_for_confusion_matrix,
                 train_label,
                 test_label,
                 target,
                 type_model,
                 tuning=False,
                 permission=None):
        self.train_feature = train_feature
        self.test_feature = test_feature
        self.train_feature_dataset_for_confusion_matrix = train_feature_dataset_for_confusion_matrix
        self.train_label_dataset_for_confusion_matrix = train_label_dataset_for_confusion_matrix
        self.train_label = train_label
        self.test_label = test_label
        self.target = target
        self.type_model = type_model
        self.tuning = tuning
        self.permission = permission
        self.confusion_matrix = None
        self.train_dataset_confusion_matrix = None
        self.model = None
        self.score = None
        self.accuracy = {
            "accuracy": '',
            "model": ''
        }
        self.model_names = ['RandomForestClassifier', 'MLPClassifier']

    """
    Class initializer function.
    :param train_feature: List of train features that
                        will be used for training model.
    :param test_feature: List of test features that
                        will be used for testing trained model.
    :param train_label: list of values that indicate
                        labels for the target column
                        will be used for training model.
    :param test_label: list of values that indicate
                        labels for the target column
                        will be used for testing model
                        to compare predicted value with correct value.
    :param target: column name of the target.
    :param type_model: indicate if the ML model
                       should be classification or regression
    :param tuning: indicate if the ML model
                   should be tuned or not
    :param permission: Pass boolean type.
                       Indicate if ML is allowed
                       to be used for provided dataset
    """

    """
    Below 3 Functions that helps identify
    what performance calculation should be used for the Model
    """

    def cal_perfomance_gm(self,
                          predictions):
        """
        Use Geometric mean to calculate ML evaluation
        see here: https://glemaitre.github.io/imbalanced-learn
                    /generated/imblearn.metrics.geometric_mean_score.html
        """

        return 'geometric mean', geometric_mean_score(self.test_label,
                                                      predictions)

    def cal_perfomance_f1_macro(self, predictions):
        """
        Use f1_score (macro) to calculate ML evaluation
        see here: https://scikit-learn.org/stable/modules
                    /generated/sklearn.metrics.f1_score.html
        """
        return 'f1_macro', f1_score(self.test_label,
                                    predictions,
                                    average='macro')

    def cal_perfomance_accuracy(self, predictions):
        """
        use accuracy scoring to calculate ML evaluation
        see here: https://scikit-learn.org/stable/modules
                    /generated/sklearn.metrics.accuracy_score.html
        """
        return 'accuracy', accuracy_score(self.test_label, predictions)

        # Check if Our Test Label is Balanced

    def calculate_balance(self):
        """
        Function checks if Test Label is Balanced
        based on this function will be chosen evaluation metrics should be used
        """

        balance = True

        for i in range(len(self.test_label.unique())):
            if round(self.test_label.value_counts()[i] /
                     len(self.test_label) * 100, 2) < 15:
                balance = False

        return balance

    def custom_confusion_matrix(self,
                                test_label,
                                predictions):
        """
        The function creates a confusion matrix
        where it can be seen how many values
        were predicted correctly with indicators
        TF, FF, FT, FF.
        see here: https://towardsdatascience.com
                    /understanding-confusion-matrix-a9ad42dcfd62
        """
        unique_label = np.unique([test_label,
                                  predictions])
        cmtx = pd.DataFrame(
            confusion_matrix(test_label,
                             predictions,
                             labels=unique_label),
            index=['true:{:}'.format(x) for x in unique_label],
            columns=['pred:{:}'.format(x) for x in unique_label]
        )
        return cmtx

    def classification_ml_tuned(self):
        """
         Following function Tunes and
         Runs All Classification Models
         Then among all models picks the best one.

         Classification models used:

         1. Random Forest Classifier.
         see here: https://scikit-learn.org/stable/modules
                    /generated/sklearn.ensemble.RandomForestClassifier.html
         2. Multi-layer Perceptron Classifier.
         see here: https://scikit-learn.org/stable/modules
                    /generated/sklearn.neural_network.MLPClassifier.html

        For tuning used GridSearch.
        see here:https://scikit-learn.org/stable/modules
                    /generated/sklearn.model_selection.GridSearchCV.html
         """

        # parameters for Random Forest Model
        param_grid_rf = [
            {'n_estimators': [400, 500, 600],
             'max_depth': [5, None],
             'criterion': ['gini', 'entropy', 'log_loss']},
            {'bootstrap': [False],
             'n_estimators': [400, 500, 600],
             'criterion': ['gini', 'entropy', 'log_loss'],
             'max_depth': [5, None]}]

        # parameters for Multi-layer Perceptron Classifier
        param_grid_mlp = [
            {'hidden_layer_sizes': [(100,), (200,), (300,)],
             'activation': ['identity', 'logistic',
                            'tanh', 'relu'],
             'solver': ['sgd', 'adam'],
             'alpha': [0.01, 0.1],
             'learning_rate_init': [0.01, 0.1]},
            {'hidden_layer_sizes': [(100,), (200,), (300,)],
             'activation': ['identity', 'logistic', 'tanh', 'relu'],
             'solver': ['lbfgs'], 'alpha': [0.01, 0.1]}]

        # Call Random Forest
        forest_clas = RandomForestClassifier(random_state=42)
        # Call MLP
        mlp_cla = MLPClassifier(random_state=42, max_iter=5000)

        # check if it is binary labels (2 classes)
        if len(self.test_label.unique()) == 2:
            f1_scorer = make_scorer(f1_score, pos_label=self.test_label[0])
            grid_search_rf = GridSearchCV(forest_clas,
                                          param_grid_rf,
                                          cv=5,
                                          scoring=f1_scorer,
                                          return_train_score=True)

            grid_search_mlp = GridSearchCV(mlp_cla,
                                           param_grid_mlp,
                                           cv=5,
                                           scoring=f1_scorer,
                                           return_train_score=True)

            performance = self.cal_perfomance_gm

        # check it is not Balanced
        elif not self.calculate_balance():
            grid_search_rf = GridSearchCV(forest_clas,
                                          param_grid_rf,
                                          cv=5,
                                          scoring='f1_macro',
                                          return_train_score=True)

            grid_search_mlp = GridSearchCV(mlp_cla,
                                           param_grid_mlp,
                                           cv=5,
                                           scoring='f1_macro',
                                           return_train_score=True)

            performance = self.cal_perfomance_f1_macro

        # if Balanced
        else:
            grid_search_rf = GridSearchCV(forest_clas,
                                          param_grid_rf,
                                          cv=5,
                                          scoring='accuracy',
                                          return_train_score=True)

            grid_search_mlp = GridSearchCV(mlp_cla,
                                           param_grid_mlp,
                                           cv=5,
                                           scoring='accuracy',
                                           return_train_score=True)
            performance = self.cal_perfomance_accuracy

        # RANDOM FOREST
        grid_search_rf.fit(self.train_feature, self.train_label)
        rf_tree = grid_search_rf.best_estimator_
        random_forest_pred = rf_tree.predict(self.test_feature)
        random_forest_score = performance(random_forest_pred)

        # MLP
        grid_search_mlp.fit(self.train_feature, self.train_label)
        mlp_model = grid_search_mlp.best_estimator_
        mlp_pred = mlp_model.predict(self.test_feature)
        mlp_score = performance(mlp_pred)

        if mlp_score > random_forest_score:
            self.confusion_matrix = self.custom_confusion_matrix(
                self.test_label,
                mlp_pred)
            self.score = mlp_score
            self.accuracy['accuracy'] = f'{self.score}'
            return mlp_model

        self.confusion_matrix = self.custom_confusion_matrix(
            self.test_label,
            random_forest_pred)
        self.score = random_forest_score
        self.accuracy['accuracy'] = f'{self.score}'
        return rf_tree

    def classification_ml(self):
        """
         Following function
         Runs All Classification Models
         Then among all models picks the best one.

         Classification models used:

         1. Random Forest Classifier.
         see here: https://scikit-learn.org/stable/modules
         /generated/sklearn.ensemble.RandomForestClassifier.html
         2. Multi-layer Perceptron Classifier.
         see here: https://scikit-learn.org/stable
         /modules/generated/sklearn.neural_network.MLPClassifier.html

         """
        # check if it is binary labels (2 classes)
        if len(self.test_label.unique()) == 2:
            perfomance = self.cal_perfomance_gm

        # check it is not Balanced
        elif not self.calculate_balance():
            perfomance = self.cal_perfomance_f1_macro

        # if Balanced
        else:
            perfomance = self.cal_perfomance_accuracy

        # Call Random Forest
        forest_clas = RandomForestClassifier(random_state=42)
        forest_clas.fit(self.train_feature, self.train_label)
        random_forest_pred = forest_clas.predict(self.test_feature)
        random_forest_score = perfomance(random_forest_pred)

        # Call MLP
        mlp_cla = MLPClassifier(random_state=42)
        mlp_cla.fit(self.train_feature, self.train_label)
        mlp_pred = mlp_cla.predict(self.test_feature)
        mlp_score = perfomance(mlp_pred)

        if mlp_score > random_forest_score:
            self.confusion_matrix = self.custom_confusion_matrix(
                self.test_label,
                mlp_pred)
            self.score = mlp_score
            self.accuracy['accuracy'] = f'{self.score}'
            return mlp_cla

        self.confusion_matrix = self.custom_confusion_matrix(
            self.test_label,
            random_forest_pred)
        self.score = random_forest_score
        self.accuracy['accuracy'] = f'{self.score}'
        return forest_clas

    def regression_ml_tuned(self):
        """
         Following function Tunes and
         Runs All Regression Models
         Then among all models picks the best one.

         Regression models used:

         1. Random Forest Regression.
         see here: https://scikit-learn.org/stable/modules
         /generated/sklearn.ensemble.RandomForestRegressor.html
         2. Multi-layer Perceptron Regressor.
         see here: https://scikit-learn.org/stable/modules
         /generated/sklearn.neural_network.MLPRegressor.html

        For tuning used GridSearch.
        see here:https://scikit-learn.org/stable/modules
        /generated/sklearn.model_selection.GridSearchCV.html
         """

        # parameters for Random Forest Model
        param_grid_rf = [
            {'n_estimators': [400, 500, 600],
             'max_depth': [5, None],
             'criterion': ['gini',
                           'entropy',
                           'log_loss']},
            {'bootstrap': [False],
             'n_estimators': [400, 500, 600],
             'criterion': ['gini',
                           'entropy',
                           'log_loss'],
             'max_depth': [5, None]}]

        # parameters for Multi-layer Perceptron Classifier
        param_grid_mlp = [{'hidden_layer_sizes': [(100,),
                                                  (200,),
                                                  (300,)],
                           'activation': ['identity',
                                          'logistic',
                                          'tanh',
                                          'relu'],
                           'solver': ['sgd',
                                      'adam'],
                           'alpha': [0.0001, 0.001, 0.01, 0.1],
                           'learning_rate_init': [0.001,
                                                  0.01,
                                                  0.1,
                                                  1]},
                          {'hidden_layer_sizes': [(100,),
                                                  (200,),
                                                  (300,)],
                           'activation': ['identity',
                                          'logistic',
                                          'tanh',
                                          'relu'],
                           'solver': ['lbfgs'],
                           'alpha': [0.0001, 0.001, 0.01, 0.1]}]

        # Random Forest Regression
        forest_clas = RandomForestRegressor(random_state=42)
        # MLP Regression
        mlp_cla = MLPRegressor(random_state=42, max_iter=5000)

        grid_search_rf = GridSearchCV(forest_clas, param_grid_rf, cv=5,
                                      scoring='neg_mean_squared_error',
                                      return_train_score=True)

        grid_search_mlp = GridSearchCV(mlp_cla, param_grid_mlp, cv=5,
                                       scoring='neg_mean_squared_error',
                                       return_train_score=True)

        # RANDOM FOREST
        grid_search_rf.fit(self.train_feature, self.train_label)
        rf_tree = grid_search_rf.best_estimator_
        random_forest_pred = rf_tree.predict(self.test_feature)

        rms_error_rf = np.sqrt(np.mean((self.test_label - random_forest_pred) ** 2))
        score_rf = rf_tree.score(self.test_feature, self.test_label)

        # MLP
        grid_search_mlp.fit(self.train_feature, self.train_label)
        mlp_model = grid_search_mlp.best_estimator_
        mlp_pred = mlp_model.predict(self.test_feature)

        rms_error_mlp = np.sqrt(np.mean((self.test_label - mlp_pred) ** 2))
        mlp_score = mlp_model.score(self.test_feature, self.test_label)

        if rms_error_mlp < rms_error_rf:
            self.score = mlp_score
            self.accuracy['accuracy'] = f'{self.score}'
            return mlp_model

        self.score = score_rf
        self.accuracy['accuracy'] = f'{self.score}'
        return rf_tree

    def regression_ml(self):
        """
          Following function
          Runs All Regression Models
          Then among all models picks the best one.

          Regression models used:
          1. Random Forest Regression.
          see here: https://scikit-learn.org/stable/modules
          /generated/sklearn.ensemble.RandomForestRegressor.html
          2. Multi-layer Perceptron Regressor.
          see here: https://scikit-learn.org/stable/modules
          /generated/sklearn.neural_network.MLPRegressor.html
          """
        # RANDOM FOREST
        forest_clas_reg = RandomForestRegressor(random_state=42)
        forest_clas_reg.fit(self.train_feature, self.train_label)
        random_forest_pred = forest_clas_reg.predict(self.test_feature)

        rms_error_rf = np.sqrt(np.mean((self.test_label - random_forest_pred) ** 2))
        score_rf = forest_clas_reg.score(self.test_feature, self.test_label)

        # MLP
        mlp_reg = MLPRegressor(random_state=42, max_iter=5000)
        mlp_reg.fit(self.train_feature, self.train_label)
        mlp_pred = mlp_reg.predict(self.test_feature)

        rms_error_mlp = np.sqrt(np.mean((self.test_label - mlp_pred) ** 2))
        mlp_score = mlp_reg.score(self.test_feature, self.test_label)

        if rms_error_mlp < rms_error_rf:
            self.score = mlp_score
            self.accuracy['accuracy'] = f'{self.score}'
            return mlp_reg

        self.score = score_rf
        self.accuracy['accuracy'] = f'{self.score}'
        return forest_clas_reg

    def save_ml_model(self, params_model_name, path, scaling):
        """
        Following function creates folder
        and saves following files.

        1. ml model (pkl format).
        2. parameters of the model (txt format).
        3. scaling (pkl format).

        Those 3 files should be saved in 1 folder
        and reused for using machine learning model.

        :param params_model_name: List of parameters
                                 that were used to generate Model.
        :param path: path were file will be saved.
        :param scaling: to normalize testing dataset.

        Why we should use scaling.
        see here: https://towardsdatascience.com
        /all-about-feature-scaling-bcc0ad75cb35

        """
        # Create directory
        list_ToSave = params_model_name["columns"]
        list_ToSave.append(params_model_name["saveModel"])
        dir_name = f'{path}{params_model_name["saveModel"]}'
        try:
            # Create target Directory
            os.mkdir(dir_name)
            print("Directory ", dir_name, " Created ")
        except FileExistsError:
            logging.debug("Directory ", dir_name, " already exists")

            # Save Params for Clinical Data
        with open(f'{dir_name}/'
                  f'{params_model_name["saveModel"]}_params.txt',
                  'w') as f:
            print(list_ToSave, file=f)

            # save in local directory
            job_ml_file_ml = f'{dir_name}/' \
                             f'{params_model_name["saveModel"]}_ml.pkl'
            jobfile_scale = f'{dir_name}/' \
                            f'{params_model_name["saveModel"]}_scaler.pkl'
            joblib.dump(scaling, jobfile_scale)
            # Save the model as a pickle in a file
            joblib.dump(self.model, job_ml_file_ml)

    def save_model_parameters(self, path):
        """
        Function saves model parameters that were used to generate ML.

        :param path: path were file will be saved.
        """
        path += f'{self.target}_ML_params.txt'
        count = 0
        with open(path, 'w') as f:
            for key, value in self.model.get_params().items():
                count += 1
                print(f'{count}. {key} = {value}', file=f)

    def save_confusion_matrix(self, path):
        """
        Function saves custom confusion matrix.

        :param path: path were file will be saved.
        """
        path += f'{self.target}_ML_RiskTable.txt'
        headers = ['TRAIN DATASET RISK TABLE', 'TEST DATASET RISK TABLE', 'ML PERFOMANCE']
        if type(self.model).__name__ in self.model_names:
            with open(path, 'w') as f:
                print(f'{headers[0]}\n',
                    file=f)
                df_as_string_train = self.train_dataset_confusion_matrix.to_string(
                    header=True,
                    index=True)
                f.write(df_as_string_train)

                print(f'\n\n{headers[1]}\n',
                    file=f)
                df_as_string_test = self.confusion_matrix.to_string(header=True,
                                                           index=True)
                f.write(df_as_string_test)
                print(f'\n\n{headers[2]}\n', file=f)
                print(f'{self.score[0]}: {self.score[1]}', file=f)
        else:
            with open(path, 'w') as f:
                print(f'\n\n{headers[2]}\n', file=f)
                print(f'Accuracy: {self.score}', file=f)


    def run_model(self):
        """
        Function Runs machine learning Models
        """
        if self.permission is False:
            self.accuracy['model'] = 'None'
            self.accuracy['accuracy'] = 'None'
            return

        if self.type_model == 'category':
            if self.tuning:
                self.model = self.classification_ml_tuned()
            else:
                self.model = self.classification_ml()
        else:
            if self.tuning:
                self.model = self.regression_ml_tuned()
            else:
                self.model = self.regression_ml()
        if type(self.model).__name__ in self.model_names:
            train_predictions_for_confusion_matrix = self.model.predict(
                self.train_feature_dataset_for_confusion_matrix)

            self.train_dataset_confusion_matrix = self.custom_confusion_matrix(
                self.train_label_dataset_for_confusion_matrix,
                train_predictions_for_confusion_matrix)

        self.accuracy['model'] = type(self.model).__name__
