import pandas as pd
import numpy as np
# Skit Learn Modules
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler  # standartiztion
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from sklearn.compose import ColumnTransformer
from sklearn.utils import resample
from collections import Counter
import logging
import ast
from joblib import Parallel, delayed
import joblib

pd.options.mode.chained_assignment = None  # default='warn'

"""
Following class does preprocessing of the data
it selectes all selected columns by ther Doctor.
It checks if the type is category and rename values in ratget is not null then it renames columns
if type is numerical or renamed values in target is null the it skips function.
Then it cleans and preprocess data for Machine learning
At the end it returns merged data
"""


class Preprocessing:

    ##gets path of (Clinical Data,Pyrad,DVH), selected column name, type of the target, renamed columns
    def __init__(self
                 # Path
                 , pathClinicalData=None  # clinical data
                 , pathPyrData=None  # Pyradiomics
                 , pathDVHData=None  # DVH
                 # Selected Columns
                 , columnNames=None
                 # Type of the Column (category/numerical)
                 , typeOfColumn=None
                 # Rename values list []
                 , target=None
                 # column Name for target
                 , renameValues=None):

        self.pathClinicalData = pathClinicalData
        self.pathPyrData = pathPyrData
        self.pathDVHData = pathDVHData
        self.columnNames = columnNames
        self.typeOfColumn = typeOfColumn
        self.renameValues = renameValues
        self.target = target
        self.scaling = None

    # read csv files and return 3 CSV files as pandas DF
    def read_csv(self):
        try:
            # Check if Path was provided for Clinical data and selected Columns Names
            if (self.columnNames != None):
                self.columnNames.append('HASHidentifier')

                # check if Target not NULL
                if (self.target != None):
                    self.columnNames.append(self.target)

                if self.pathClinicalData != None:
                    data_Clinical = pd.read_csv(f'{self.pathClinicalData}', usecols=self.columnNames)
            else:
                if self.pathClinicalData != None:
                    data_Clinical = pd.read_csv(f'{self.pathClinicalData}')

            # Check if Path was provided for DVH data
            if self.pathDVHData != None:
                data_DVH = pd.read_csv(f'{self.pathDVHData}', on_bad_lines='skip').rename(
                    columns={"Patient ID": "HASHidentifier"})

            # Check if Path was provided for PyRad data
            if self.pathPyrData != None:
                data_Py = pd.read_csv(f'{self.pathPyrData}').rename(columns={"Hash ID": "HASHidentifier"})

        except:
            logging.warning('Error in loading Files')

        return data_Clinical, data_DVH, data_Py

    """
    following function get 3 parameters Clinical Data pandas DF, Target Column, list of Values
    to be renamed and type of Column.
    If type of the column is catergory and List of values not null then it renames to set values.
    If it is numeric or list is empty it return initial pandas DF that was provided.
    """

    def rename(self, clinicalData):
        if (self.typeOfColumn == 'category' and self.renameValues != None):
            for i in range(len(self.renameValues)):
                clinicalData.loc[clinicalData[self.target] == i, self.target] = self.renameValues[i]
            return clinicalData
        else:
            logging.warning('Function rename is not allowed for numerical values')
            return clinicalData

    """
    Following function does preprocessing of the Clinical Data
    1.Rename -> if needed
    2.Clean -> if needed
    3.Fill missing values -> if needed
    4.Removes duplivates -> if needed
    5.Replace values ->if needed
    6.drop empty columns if exists
    """

    def preProcessingClinicalData(self, clinicalData):

        # Function checks % of missing values in a column. Those Columns that are less than 5% will be removed from DF
        def check_percentage_ofMissingValues(data):
            dropColumns = []
            for x in data.columns:
                percentage = (100 - (data[x].isna().sum() / len(data) * 100))
                if percentage < 5:
                    dropColumns.append(x)

            return dropColumns

        # Function to replace 2nd value in string
        def replace_nth_occurance(some_str, original, replacement, n):
            """ Replace nth occurance of a string with another string"""
            all_replaced = some_str.replace(original, replacement,
                                            n)  # Replace all originals up to (including) nth occurance and assign it to the variable.
            for i in range(n):
                first_originals_back = all_replaced.replace(replacement, original,
                                                            i)  # Restore originals up to nth occurance (not including nth)
            return first_originals_back

        if (self.target != None):
            clinicalData = self.rename(clinicalData)

        listColumnsToRemove = ['Dist_Mets_1', 'Dist_Mets_2', 'Dist_Mets_3', 'DepthOfInvasion', 'Operation_DtTm',
                               'OperationName', 'Chemo', 'ChemoDrug', 'Immuno', 'ImmunoDrug', 'Diag_Addendum',
                               'PNI', 'SUVn', 'Birth_Place', 'Marital', 'Religion', 'Description', 'Diag_Code']

        diff1 = list((Counter(clinicalData.columns) - Counter(listColumnsToRemove)).elements())

        # Select columns that will be used in machined learning model
        data_Clinical = clinicalData[diff1]
        data_Clinical = data_Clinical.drop_duplicates(subset=['HASHidentifier'])

        # preprocess
        try:
            if 'Race' in data_Clinical.columns:
                data_Clinical['Race'] = data_Clinical['Race'].fillna("Not_Stated")

            if 'Marital' in data_Clinical.columns:
                data_Clinical['Marital'] = data_Clinical['Marital'].replace(
                    {"NevMarried": "Not_Stated", "Unknown": "Not_Stated"})

            if 'Religion' in data_Clinical.columns:
                data_Clinical['Religion'] = data_Clinical['Religion'].replace({"7101": "No Religion, so desc"})

            if 'Site_Name' in data_Clinical.columns:
                data_Clinical['Site_Name'] = data_Clinical['Site_Name'].apply(
                    lambda x: replace_nth_occurance(x, ".", "_", 2)).apply(
                    lambda x: x.partition(".")[2])

            if 'SUVp' in data_Clinical.columns:
                data_Clinical['SUVp'] = data_Clinical['SUVp'].replace({" ": None})
                # Convert values to their type
                data_Clinical['SUVp'] = data_Clinical['SUVp'].astype(float)
                data_Clinical['SUVp'] = data_Clinical['SUVp'].fillna(0)

            if 'Surgery' in data_Clinical.columns:
                data_Clinical['Surgery'] = data_Clinical['Surgery'].str.strip()

            if 'Ext_Rad' in data_Clinical.columns:
                data_Clinical['Ext_Rad'] = data_Clinical['Ext_Rad'].str.strip()

            if 'AgeAtDeath' in data_Clinical.columns:
                data_Clinical['AgeAtDeath'] = data_Clinical['AgeAtDeath'].fillna(0)

            try:
                listTodrop = check_percentage_ofMissingValues(data_Clinical)
                if listTodrop:
                    data_Clinical = data_Clinical.drop(listTodrop, axis=1)
                    print(f'columns to drop : {listTodrop}')
            except:
                logging.warning('error in dropping empty columns ')



        except:
            logging.warning('error in Preprocessing Clinical Data columns')

        return data_Clinical

    # Preprocessing DVH data
    def preProcessingDVHData(self, dvhData):
        try:
            dvhData = dvhData.fillna(0)
            dvhData = dvhData.drop_duplicates(subset=['HASHidentifier', 'ROI'], keep='last')

        except:
            logging.warning('error in Preprocessing DVH Data columns')

        return dvhData

    # Preprocessing Pyrad data
    def preProcessingPyradData(self, Pyrad):
        listColumnsToRemove = ['diagnostics_Versions_PyRadiomics', 'diagnostics_Versions_Numpy',
                               'diagnostics_Versions_SimpleITK', 'diagnostics_Versions_PyWavelet',
                               'diagnostics_Versions_Python', 'diagnostics_Configuration_Settings',
                               'diagnostics_Image-original_Dimensionality', 'diagnostics_Image-original_Size',
                               'diagnostics_Mask-original_Hash', 'diagnostics_Mask-original_Spacing',
                               'diagnostics_Mask-original_Size', 'diagnostics_Configuration_EnabledImageTypes',
                               'diagnostics_Image-original_Hash', 'diagnostics_Image-original_Spacing']

        diff1 = list((Counter(Pyrad.columns) - Counter(listColumnsToRemove)).elements())

        Pyrad = Pyrad[diff1]

        try:
            if 'diagnostics_Mask-original_CenterOfMassIndex' in Pyrad.columns:
                Pyrad['diagnostics_Mask-original_CenterOfMassIndex'] = Pyrad[
                    'diagnostics_Mask-original_CenterOfMassIndex'].apply(lambda x: ast.literal_eval(x)).apply(
                    lambda x: sum(x) / len(x))
            if 'diagnostics_Mask-original_BoundingBox' in Pyrad.columns:
                Pyrad['diagnostics_Mask-original_BoundingBox'] = Pyrad['diagnostics_Mask-original_BoundingBox'].apply(
                    lambda x: ast.literal_eval(x)).apply(lambda x: sum(x) / len(x))
            if 'diagnostics_Mask-original_CenterOfMass' in Pyrad.columns:
                Pyrad['diagnostics_Mask-original_CenterOfMass'] = Pyrad['diagnostics_Mask-original_CenterOfMass'].apply(
                    lambda x: ast.literal_eval(x)).apply(lambda x: sum(x) / len(x))
        except:
            logging.warning('error in Preprocessing Pyrad Data columns')

        return Pyrad

    # Reading Clinical,DVG,Pyrad and Preprocess it
    def preprocessingData(self):
        clinicalData, dvhData, pyradData = self.read_csv()  # Reading Clinical,DVG,Pyrad
        clinicalData = self.preProcessingClinicalData(clinicalData)  # Preprocessing ClinicalData
        dvhData = self.preProcessingDVHData(dvhData)  # Preprocessing DVH
        pyradData = self.preProcessingPyradData(pyradData)  # Preprocessing Pyrad

        return clinicalData, dvhData, pyradData

    # Following function Merge 3 DFs into 1 Data Frame
    def mergingData(self, clinicalData, dvhData, pyradData):
        # get all List of unique IDs in Clinical Data
        Clinical_data = clinicalData['HASHidentifier'].unique().tolist()
        DVH_data = dvhData['HASHidentifier'].unique().tolist()
        # Find Missing IDs
        diff1 = list((Counter(Clinical_data) - Counter(DVH_data)).elements())
        # Need to use here Logging to display IDs which is missing
        # logging.warning(data_Clinical[data_Clinical['HASHidentifier'].isin(diff1)][['HASHidentifier']])
        # merge
        clinicalData = clinicalData[clinicalData['HASHidentifier'].isin(dvhData['HASHidentifier'])]
        clnical_DVH = clinicalData.merge(dvhData, how="left", on="HASHidentifier")
        clnical_DVH_Pyrad = clnical_DVH.merge(pyradData, how="left", on=["HASHidentifier", 'ROI'])
        clnical_DVH_Pyrad = clnical_DVH_Pyrad.drop_duplicates()

        return clnical_DVH_Pyrad

    """
    Following functions checks if we need to do upsampling for DataFrame to prevent imbalanced data
    This Function Should Take only selected target column.
    """

    def check_percentage_value_counts(self, data):
        count = 0
        minP = 100.0  # find min % of the values in DF
        minV = None  # to set this Value for upsampling
        for i, y in zip(data.value_counts().index, data.value_counts()):
            percentage = round(y / len(data), 2) * 100
            if count >= 2:
                return False, count
                break
            else:
                if percentage < minP:
                    minP = percentage
                    minV = i
            count += 1

        if minP < 10:
            return True, minV
        else:
            return False, minV

    # Following Function does upsampling for dataset Only if it is needed
    def upSampling(self, data):
        result = self.check_percentage_value_counts(data[self.target])
        if result[0]:
            # Separate majority and minority classes
            df_majority = data[data[self.target] != result[1]]
            df_minority = data[data[self.target] == result[1]]

            # Upsample minority class
            df_minority_upsampled = resample(df_minority,
                                             replace=True,  # sample with replacement
                                             n_samples=len(df_majority),  # to match majority class
                                             random_state=123)  # reproducible results

            # Combine majority class with upsampled minority class
            df_upsampled = pd.concat([df_majority, df_minority_upsampled])

            return df_upsampled

        return data

    """
    Following function Merge the data into 1 Dataset
    Then it checks if Target was specified for Use case 1 (Train Model)
    If so, then it does Scaling Data and Upsampling(if needed)
    """

    def prepareforML(self):
        ClinicalData, DVH, Pyr = self.preprocessingData()
        # Used only for Training if it is Testing Then returns Merged DF
        if (self.target != None):
            X_train, X_test = train_test_split(ClinicalData, test_size=0.3, random_state=42)
            X_train = self.mergingData(X_train, DVH, Pyr)
            X_test = self.mergingData(X_test, DVH, Pyr)

            X_train = X_train.drop(['HASHidentifier'], axis=1)
            X_test = X_test.drop(['HASHidentifier'], axis=1)

            result = self.check_percentage_value_counts(X_train[self.target])

            final_cat = X_train.select_dtypes(include=['object']).columns.tolist()
            final_num = X_train.select_dtypes(exclude=['object']).columns.tolist()

            if self.target in final_num:
                final_num.remove(self.target)
            else:
                final_cat.remove(self.target)
            # Scaling
            full_pipeline = ColumnTransformer([
                ("num", StandardScaler(), final_num),
                ("cat", OneHotEncoder(handle_unknown='ignore'), final_cat)
            ])

            # Check if label is inbalanced, if so, then it does Upsampling on train
            if result[0]: X_train = self.upSampling(X_train)

            # Split on Test and Train Dataset
            y_train = X_train[self.target]
            y_test = X_test[self.target]
            X_train = full_pipeline.fit_transform(X_train)
            X_test = full_pipeline.transform(X_test)
            self.scaling = full_pipeline

            return X_train, X_test, y_train, y_test
        else:
            data = self.mergingData(ClinicalData, DVH, Pyr)
            IDs = data['HASHidentifier']
            data = data.drop(['HASHidentifier'], axis=1)
            return data, IDs

    # Should be saved in txt (columnNames), 2 value name of the Model (self.target+'_ML')
    def saveParam(self):
        # if columnNames not empty
        if self.columnNames != None:
            self.columnNames.remove(self.target)
            self.columnNames.remove('HASHidentifier')

        # If columnNames is Empty
        else:

            data1, data2, data3 = self.read_csv()
            self.columnNames = list(data1.columns)
            self.columnNames.remove(self.target)
            self.columnNames.remove('HASHidentifier')
        return {"columns": self.columnNames,
                "saveModel": self.target}
