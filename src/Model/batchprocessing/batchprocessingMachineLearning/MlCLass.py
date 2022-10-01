import pandas as pd
import numpy as np

# scroing
from sklearn.metrics import (classification_report, confusion_matrix, accuracy_score,
                             f1_score, make_scorer, roc_curve,
                             balanced_accuracy_score)

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

# Save model
from joblib import Parallel, delayed
import joblib


class MlModeling():
    def __init__(self,
                 trainFeature
                 , testFeature
                 , trainLabel
                 , testLabel
                 , target
                 , typeofModel
                 , tunning=False):
        self.trainFeature = trainFeature
        self.testFeature = testFeature
        self.trainLabel = trainLabel
        self.testLabel = testLabel
        self.target = target
        self.typeofModel = typeofModel
        self.tunning = tunning
        self.confusionMatrix = None
        self.model = None
        self.score = None
        self.accuracy = {"accuracy": ''}

    """
    Below 3 Functions that helps identify what perfomance calculation should be used for the Model
    """

    def calPerfomanceGM(self, predictions):
        return 'geometric mean', geometric_mean_score(self.testLabel, predictions)

    def calPerfomanceF1_Sample(self, predictions):
        return 'f1_macro', f1_score(self.testLabel, predictions, average='macro')

    def calPerfomanceAccuracy(self, predictions):
        return 'accuracy', accuracy_score(self.testLabel, predictions)

        # Check if Our Test Label is Balanced

    def calculateBalance(self):

        balance = True

        for i in range(len(self.testLabel.unique())):
            if round(self.testLabel.value_counts()[i] / len(self.testLabel) * 100, 2) < 15:
                balance = False

        return balance

    def CastomConfusion_matrix(self, predictions):
        unique_label = np.unique([self.testLabel, predictions])
        cmtx = pd.DataFrame(
            confusion_matrix(self.testLabel, predictions, labels=unique_label),
            index=['true:{:}'.format(x) for x in unique_label],
            columns=['pred:{:}'.format(x) for x in unique_label]
        )
        return cmtx

    """
    Following function Tunnes and Runs All Classification Models
    Then among all models it picks the best one
    """

    def ClassificationMLTunned(self):
        print('Selected Mode Tunning Model')
        print('Please be aware that it takes time Appx 10-20 min')

        # Tunning Random Forest
        param_grid_RF = [
            {'n_estimators': [400, 500, 600], 'max_depth': [5, None], 'criterion': ['gini', 'entropy', 'log_loss']},
            {'bootstrap': [False], 'n_estimators': [400, 500, 600], 'criterion': ['gini', 'entropy', 'log_loss'],
             'max_depth': [5, None]}]

        param_grid_MLP = [
            {'hidden_layer_sizes': [(100,), (200,), (300,)], 'activation': ['identity', 'logistic', 'tanh', 'relu']
                , 'solver': ['sgd', 'adam'], 'alpha': [0.01, 0.1], 'learning_rate_init': [0.01, 0.1]},
            {'hidden_layer_sizes': [(100,), (200,), (300,)], 'activation': ['identity', 'logistic', 'tanh', 'relu']
                , 'solver': ['lbfgs'], 'alpha': [0.01, 0.1]}]

        # Call Random Forest
        forest_clas = RandomForestClassifier(random_state=42)
        # Call MLP
        mlp_cla = MLPClassifier(random_state=42, max_iter=5000)

        # check if it is binary labels (2 classes)
        if len(self.testLabel.unique()) == 2:
            print('running self.testLabel.unique()) == 2')
            f1_scorer = make_scorer(f1_score, pos_label=self.testLabel[0])
            grid_search_rf = GridSearchCV(forest_clas, param_grid_RF, cv=5
                                          , scoring=f1_scorer, return_train_score=True)

            grid_search_mlp = GridSearchCV(mlp_cla, param_grid_MLP, cv=5
                                           , scoring=f1_scorer, return_train_score=True)

            perfomance = self.calPerfomanceGM

        # check it is not Balanced
        elif not self.calculateBalance():
            print('running not self.calculateBalance()')
            grid_search_rf = GridSearchCV(forest_clas, param_grid_RF, cv=5
                                          , scoring='f1_macro', return_train_score=True)

            grid_search_mlp = GridSearchCV(mlp_cla, param_grid_MLP, cv=5
                                           , scoring='f1_macro', return_train_score=True)

            perfomance = self.calPerfomanceF1_Sample

        # if Balanced
        else:
            print('else')
            grid_search_rf = GridSearchCV(forest_clas, param_grid_RF, cv=5
                                          , scoring='accuracy', return_train_score=True)

            grid_search_mlp = GridSearchCV(mlp_cla, param_grid_MLP, cv=5
                                           , scoring='accuracy', return_train_score=True)
            perfomance = self.calPerfomanceAccuracy

        # RANDOM FOREST
        grid_search_rf.fit(self.trainFeature, self.trainLabel)
        rf_tree = grid_search_rf.best_estimator_
        RandomForest_pred = rf_tree.predict(self.testFeature)
        random_forest_score = perfomance(RandomForest_pred)

        # MLP
        grid_search_mlp.fit(self.trainFeature, self.trainLabel)
        print(grid_search_mlp.best_params_)
        mlpModel = grid_search_mlp.best_estimator_
        mlp_pred = mlpModel.predict(self.testFeature)
        mlp_score = perfomance(mlp_pred)

        if mlp_score > random_forest_score:
            self.confusionMatrix = self.CastomConfusion_matrix(mlp_pred)
            self.score = mlp_score
            self.accuracy['accuracy'] = f'{self.score}'
            return mlpModel

        self.confusionMatrix = self.CastomConfusion_matrix(RandomForest_pred)
        self.score = random_forest_score
        self.accuracy['accuracy'] = f'{self.score}'
        return rf_tree

    """
    Following function does classification
    """

    def ClassificationML(self):
        # check if it is binary labels (2 classes)
        if len(self.testLabel.unique()) == 2:
            perfomance = self.calPerfomanceGM

        # check it is not Balanced
        elif not self.calculateBalance():
            perfomance = self.calPerfomanceF1_Sample

        # if Balanced
        else:
            perfomance = self.calPerfomanceAccuracy

        # Call Random Forest
        forest_clas = RandomForestClassifier(random_state=42)
        forest_clas.fit(self.trainFeature, self.trainLabel)
        RandomForest_pred = forest_clas.predict(self.testFeature)
        random_forest_score = perfomance(RandomForest_pred)

        # Call MLP
        mlp_cla = MLPClassifier(random_state=42)
        mlp_cla.fit(self.trainFeature, self.trainLabel)
        mlp_pred = mlp_cla.predict(self.testFeature)
        mlp_score = perfomance(mlp_pred)

        if mlp_score > random_forest_score:
            self.confusionMatrix = self.CastomConfusion_matrix(mlp_pred)
            self.score = mlp_score
            self.accuracy['accuracy'] = f'{self.score}'
            return mlp_cla

        self.confusionMatrix = self.CastomConfusion_matrix(RandomForest_pred)
        self.score = random_forest_score
        self.accuracy['accuracy'] = f'{self.score}'
        return forest_clas

    def RegressionMLTunned(self):
        print('Selected Mode Tunning Model')
        print('Please be aware that it takes time Appx 20-30 min')
        # Tunning Random Forest
        param_grid_RF = [
            {'n_estimators': [400, 500, 600], 'max_depth': [5, None], 'criterion': ['gini', 'entropy', 'log_loss']},
            {'bootstrap': [False], 'n_estimators': [400, 500, 600], 'criterion': ['gini', 'entropy', 'log_loss'],
             'max_depth': [5, None]}]

        param_grid_MLP = [{'hidden_layer_sizes': [(100,), (200,), (300,)
                                                  ], 'activation': ['identity', 'logistic', 'tanh', 'relu']
                              , 'solver': ['sgd', 'adam'], 'alpha': [0.0001, 0.001, 0.01, 0.1],
                           'learning_rate_init': [0.001, 0.01, 0.1, 1]},
                          {'hidden_layer_sizes': [(100,), (200,), (300,)
                                                  ], 'activation': ['identity', 'logistic', 'tanh', 'relu']
                              , 'solver': ['lbfgs'], 'alpha': [0.0001, 0.001, 0.01, 0.1]}]

        # Random Forest Regression
        forest_clas = RandomForestRegressor(random_state=42)
        # MLP Regression
        mlp_cla = MLPRegressor(random_state=42, max_iter=5000)

        grid_search_rf = GridSearchCV(forest_clas, param_grid_RF, cv=5,
                                      scoring='neg_mean_squared_error',
                                      return_train_score=True)

        grid_search_mlp = GridSearchCV(mlp_cla, param_grid_MLP, cv=5,
                                       scoring='neg_mean_squared_error',
                                       return_train_score=True)

        # RANDOM FOREST
        grid_search_rf.fit(self.trainFeature, self.trainLabel)
        rf_tree = grid_search_rf.best_estimator_
        random_forest_pred = rf_tree.predict(self.testFeature)

        rmse_rf = np.sqrt(np.mean((self.testLabel - random_forest_pred) ** 2))
        score_rf = rf_tree.score(self.testFeature, self.testLabel)

        # MLP
        grid_search_mlp.fit(self.trainFeature, self.trainLabel)
        mlp_model = grid_search_mlp.best_estimator_
        mlp_pred = mlp_model.predict(self.testFeature)

        rmse_mlp = np.sqrt(np.mean((self.testLabel - mlp_pred) ** 2))
        mlp_score = mlp_cla.score(self.testFeature, self.testLabel)

        if rmse_mlp < rmse_rf:
            self.score = mlp_score
            self.accuracy['accuracy'] = f'{self.score}'
            return mlp_model

        self.score = score_rf
        self.accuracy['accuracy'] = f'{self.score}'
        return rf_tree

    def RegressionML(self):
        # RANDOM FOREST
        forest_clas_reg = RandomForestRegressor(random_state=42)
        forest_clas_reg.fit(self.trainFeature, self.trainLabel)
        random_forest_pred = forest_clas_reg.predict(self.testFeature)

        rmse_rf = np.sqrt(np.mean((self.testLabel - random_forest_pred) ** 2))
        score_rf = forest_clas_reg.score(self.testFeature, self.testLabel)

        # MLP
        mlp_reg = MLPRegressor(random_state=42, max_iter=5000)
        mlp_reg.fit(self.trainFeature, self.trainLabel)
        mlp_pred = mlp_reg.predict(self.testFeature)

        rmse_mlp = np.sqrt(np.mean((self.testLabel - mlp_pred) ** 2))
        mlp_score = mlp_reg.score(self.testFeature, self.testLabel)

        if rmse_mlp < rmse_rf:
            self.score = mlp_score
            self.accuracy['accuracy'] = f'{self.score}'
            return mlp_reg

        self.score = score_rf
        self.accuracy['accuracy'] = f'{self.score}'
        return forest_clas_reg

    def saveMLModel(self, paramsAndModelName, path, scaling):
        # Create directory
        list_ToSave = paramsAndModelName["columns"]
        list_ToSave.append(paramsAndModelName["saveModel"])
        dirName = f'{path}{paramsAndModelName["saveModel"]}'
        try:
            # Create target Directory
            os.mkdir(dirName)
            print("Directory ", dirName, " Created ")
        except FileExistsError:
            print("Directory ", dirName, " already exists")

            # Save Params for Clinical Data
        with open(f'{dirName}/{paramsAndModelName["saveModel"]}_PARAMS.txt', 'w') as f:
            print(list_ToSave, file=f)

        try:
            jobMLfileML = f'{dirName}/{paramsAndModelName["saveModel"]}_ML.pkl'  # the location, If you want to save in local directory then just add filename
            jobfileScale = f'{dirName}/{paramsAndModelName["saveModel"]}_Scale.pkl'
            joblib.dump(scaling, jobfileScale)
            ##  Save the model as a pickle in a file
            joblib.dump(self.model, jobMLfileML)  # model is the trained ML model , model = randomforestclassifier()
            # call this function after model is fit --- model.fit(X_train, y_train)
        except:
            logging.warning('error in Saving ML model')

    def saveModelParameters(self, path):
        path += f'{self.target}_ML_params.txt'
        count = 0
        with open(path, 'w') as f:
            for key, value in self.model.get_params().items():
                count += 1
                print(f'{count}. {key} = {value}', file=f)

    def saveConfusionMatrix(self, path):
        path += f'{self.target}_ML_RiskTable.txt'
        headers = ['RISK TABLE', 'ML PERFOMANCE']
        with open(path, 'w') as f:
            print(f'{headers[0]}\n', file=f)
            dfAsString = self.confusionMatrix.to_string(header=True, index=True)
            f.write(dfAsString)
            print(f'\n\n{headers[1]}\n', file=f)
            print(f'{self.score[0]}: {self.score[1]}', file=f)

    def runModel(self):
        if self.typeofModel == 'category':
            if self.tunning:
                self.model = self.ClassificationMLTunned()
            else:
                self.model = self.ClassificationML()
        else:
            if self.tunning:
                self.model = self.RegressionMLTunned()
            else:
                self.model = self.RegressionML()

        return self.model
