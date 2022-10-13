import pandas as pd
import numpy as np

# scroing
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
    def __init__(self,
                 train_feature,
                 test_feature,
                 train_label,
                 test_label,
                 target,
                 type_model,
                 tunning=False,
                 permission=None):
        self.train_feature = train_feature
        self.test_feature = test_feature
        self.train_label = train_label
        self.test_label = test_label
        self.target = target
        self.type_model = type_model
        self.tunning = tunning
        self.permission = permission
        self.confusion_matrix = None
        self.model = None
        self.score = None
        self.accuracy = {
            "accuracy": '',
            "model": ''
        }

    """
    Below 3 Functions that helps identify
    what perfomance calculation should be used for the Model
    """

    def cal_perfomance_gm(self,
                          predictions):
        return 'geometric mean', geometric_mean_score(self.test_label,
                                                      predictions)

    def cal_perfomance_f1_macro(self, predictions):
        return 'f1_macro', f1_score(self.test_label,
                                    predictions,
                                    average='macro')

    def cal_perfomance_accuracy(self, predictions):
        return 'accuracy', accuracy_score(self.test_label, predictions)

        # Check if Our Test Label is Balanced

    def calculate_balance(self):

        balance = True

        for i in range(len(self.test_label.unique())):
            if round(self.test_label.value_counts()[i] /
                     len(self.test_label) * 100, 2) < 15:
                balance = False

        return balance

    def castom_confusion_matrix(self,
                                predictions):
        unique_label = np.unique([self.test_label,
                                  predictions])
        cmtx = pd.DataFrame(
            confusion_matrix(self.test_label,
                             predictions,
                             labels=unique_label),
            index=['true:{:}'.format(x) for x in unique_label],
            columns=['pred:{:}'.format(x) for x in unique_label]
        )
        return cmtx

    """
    Following function Tunnes and Runs All Classification Models
    Then among all models it picks the best one
    """

    def classification_ml_tunned(self):
        # Tunning Random Forest
        param_grid_rf = [
            {'n_estimators': [400, 500, 600],
             'max_depth': [5, None],
             'criterion': ['gini', 'entropy', 'log_loss']},
            {'bootstrap': [False],
             'n_estimators': [400, 500, 600],
             'criterion': ['gini', 'entropy', 'log_loss'],
             'max_depth': [5, None]}]

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

            perfomance = self.cal_perfomance_gm

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

            perfomance = self.cal_perfomance_f1_macro

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
            perfomance = self.cal_perfomance_accuracy

        # RANDOM FOREST
        grid_search_rf.fit(self.train_feature, self.train_label)
        rf_tree = grid_search_rf.best_estimator_
        random_forest_pred = rf_tree.predict(self.test_feature)
        random_forest_score = perfomance(random_forest_pred)

        # MLP
        grid_search_mlp.fit(self.train_feature, self.train_label)
        mlp_model = grid_search_mlp.best_estimator_
        mlp_pred = mlp_model.predict(self.test_feature)
        mlp_score = perfomance(mlp_pred)

        if mlp_score > random_forest_score:
            self.confusion_matrix = self.castom_confusion_matrix(
                mlp_pred)
            self.score = mlp_score
            self.accuracy['accuracy'] = f'{self.score}'
            return mlp_model

        self.confusion_matrix = self.castom_confusion_matrix(
            random_forest_pred)
        self.score = random_forest_score
        self.accuracy['accuracy'] = f'{self.score}'
        return rf_tree

    """
    Following function does classification
    """

    def classification_ml(self):
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
            self.confusion_matrix = self.castom_confusion_matrix(mlp_pred)
            self.score = mlp_score
            self.accuracy['accuracy'] = f'{self.score}'
            return mlp_cla

        self.confusion_matrix = self.castom_confusion_matrix(
            random_forest_pred)
        self.score = random_forest_score
        self.accuracy['accuracy'] = f'{self.score}'
        return forest_clas

    def regression_ml_tunned(self):
        # Tunning Random Forest
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

        rmse_rf = np.sqrt(np.mean((self.test_label - random_forest_pred) ** 2))
        score_rf = rf_tree.score(self.test_feature, self.test_label)

        # MLP
        grid_search_mlp.fit(self.train_feature, self.train_label)
        mlp_model = grid_search_mlp.best_estimator_
        mlp_pred = mlp_model.predict(self.test_feature)

        rmse_mlp = np.sqrt(np.mean((self.test_label - mlp_pred) ** 2))
        mlp_score = mlp_model.score(self.test_feature, self.test_label)

        if rmse_mlp < rmse_rf:
            self.score = mlp_score
            self.accuracy['accuracy'] = f'{self.score}'
            return mlp_model

        self.score = score_rf
        self.accuracy['accuracy'] = f'{self.score}'
        return rf_tree

    def regression_ml(self):
        # RANDOM FOREST
        forest_clas_reg = RandomForestRegressor(random_state=42)
        forest_clas_reg.fit(self.train_feature, self.train_label)
        random_forest_pred = forest_clas_reg.predict(self.test_feature)

        rmse_rf = np.sqrt(np.mean((self.test_label - random_forest_pred) ** 2))
        score_rf = forest_clas_reg.score(self.test_feature, self.test_label)

        # MLP
        mlp_reg = MLPRegressor(random_state=42, max_iter=5000)
        mlp_reg.fit(self.train_feature, self.train_label)
        mlp_pred = mlp_reg.predict(self.test_feature)

        rmse_mlp = np.sqrt(np.mean((self.test_label - mlp_pred) ** 2))
        mlp_score = mlp_reg.score(self.test_feature, self.test_label)

        if rmse_mlp < rmse_rf:
            self.score = mlp_score
            self.accuracy['accuracy'] = f'{self.score}'
            return mlp_reg

        self.score = score_rf
        self.accuracy['accuracy'] = f'{self.score}'
        return forest_clas_reg

    def save_ml_model(self, params_model_name, path, scaling):
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
        path += f'{self.target}_ML_params.txt'
        count = 0
        with open(path, 'w') as f:
            for key, value in self.model.get_params().items():
                count += 1
                print(f'{count}. {key} = {value}', file=f)

    def save_confusion_matrix(self, path):
        path += f'{self.target}_ML_RiskTable.txt'
        headers = ['RISK TABLE', 'ML PERFOMANCE']
        with open(path, 'w') as f:
            print(f'{headers[0]}\n',
                  file=f)
            df_as_string = self.confusion_matrix.to_string(header=True,
                                                           index=True)
            f.write(df_as_string)
            print(f'\n\n{headers[1]}\n', file=f)
            print(f'{self.score[0]}: {self.score[1]}', file=f)

    def run_model(self):
        if self.permission is False:
            self.accuracy['model'] = 'None'
            self.accuracy['accuracy'] = 'None'
            return

        if self.type_model == 'category':
            if self.tunning:
                self.model = self.classification_ml_tunned()
            else:
                self.model = self.classification_ml()
        else:
            if self.tunning:
                self.model = self.regression_ml_tunned()
            else:
                self.model = self.regression_ml()

        self.accuracy['model'] = type(self.model).__name__
