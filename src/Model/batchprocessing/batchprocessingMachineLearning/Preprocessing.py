import pandas as pd
# Skit Learn Modules
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler  # standartiztion
from sklearn.preprocessing import OneHotEncoder

from sklearn.compose import ColumnTransformer
from sklearn.utils import resample
from collections import Counter
import logging
import ast

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

    # gets path of (Clinical Data,Pyrad,DVH), selected column name, type of the target, renamed columns
    def __init__(self
                 # Path
                 , path_clinical_data=None  # clinical data
                 , path_pyr_data=None  # Pyradiomics
                 , path_dvh_data=None  # DVH
                 # Selected Columns
                 , column_names=None
                 # Type of the Column (category/numerical)
                 , type_column=None
                 # Rename values list []
                 , target=None
                 # column Name for target
                 , rename_values=None):

        self.path_clinical_data = path_clinical_data
        self.path_pyr_data = path_pyr_data
        self.path_dvh_data = path_dvh_data
        self.column_names = column_names
        self.type_column = type_column
        self.rename_values = rename_values
        self.target = target
        self.scaling = None
        self.missing_id = []
        self.permission = None
        self.permission_ids = None

    # read csv files and return 3 CSV files as pandas DF
    def read_csv(self):
        # Check if Path was provided for Clinical data and selected Columns Names
        if self.column_names is not None:
            self.column_names.append('HASHidentifier')

            # check if Target not NULL
            if self.target is not None:
                self.column_names.append(self.target)

            if self.path_clinical_data is not None:
                data_clinical = pd.read_csv(f'{self.path_clinical_data}', usecols=self.column_names)
        else:
            if self.path_clinical_data is not None:
                data_clinical = pd.read_csv(f'{self.path_clinical_data}')

        # Check if Path was provided for DVH data
        if self.path_dvh_data is not None:
            data_dvh = pd.read_csv(f'{self.path_dvh_data}', on_bad_lines='skip').rename(
                columns={"Patient ID": "HASHidentifier"})

        # Check if Path was provided for PyRad data
        if self.path_pyr_data is not None:
            data_py = pd.read_csv(f'{self.path_pyr_data}').rename(columns={"Hash ID": "HASHidentifier"})
        return data_clinical, data_dvh, data_py

    """
    following function get 3 parameters Clinical Data pandas DF, Target Column, list of Values
    to be renamed and type of Column.
    If type of the column is catergory and List of values not null then it renames to set values.
    If it is numeric or list is empty it return initial pandas DF that was provided.
    """

    def rename(self, clinical_data):
        if self.type_column == 'category' and self.rename_values is not None:
            for i in range(len(self.rename_values)):
                clinical_data.loc[clinical_data[self.target] == i, self.target] = self.rename_values[i]
            return clinical_data
        else:
            logging.debug('Function rename is not allowed for numerical values')
            return clinical_data

    """
    Following function does preprocessing of the Clinical Data
    1.Rename -> if needed
    2.Clean -> if needed
    3.Fill missing values -> if needed
    4.Removes duplivates -> if needed
    5.Replace values ->if needed
    6.drop empty columns if exists
    """

    def pre_processing_clinical_data(self, clinical_data):

        # Function checks % of missing values in a column. Those Columns that are less than 5% will be removed from DF
        def check_percentage_missing_values(data):
            drop_columns = []
            for x in data.columns:
                percentage = (100 - (data[x].isna().sum() / len(data) * 100))
                if percentage < 5:
                    drop_columns.append(x)

            return drop_columns

        # Function to replace 2nd value in string
        def replace_nth_occurance(some_str, original, replacement, n):
            """ Replace nth occurance of a string with another string"""
            all_replaced = \
                some_str.replace(original,
                                 replacement, n)  # Replace all originals up to (including) nth
            for i in range(n):
                first_originals_back = \
                    all_replaced.replace(replacement,
                                         original, i)  # Restore originals up to nth occurance (not including nth)
            return first_originals_back

        if self.target is not None:
            clinical_data = self.rename(clinical_data)

        list_columns_remove = ['Dist_Mets_1', 'Dist_Mets_2', 'Dist_Mets_3', 'DepthOfInvasion', 'Operation_DtTm',
                               'OperationName', 'Chemo', 'ChemoDrug', 'Immuno', 'ImmunoDrug', 'Diag_Addendum',
                               'PNI', 'SUVn', 'Birth_Place', 'Marital', 'Religion', 'Description', 'Diag_Code']

        diff1 = list((Counter(clinical_data.columns) - Counter(list_columns_remove)).elements())

        # Select columns that will be used in machined learning model
        data_clinical = clinical_data[diff1]
        data_clinical = data_clinical.drop_duplicates(subset=['HASHidentifier'])

        # preprocess
        if 'Race' in data_clinical.columns:
            data_clinical['Race'] = data_clinical['Race'].fillna("Not_Stated")

        if 'Marital' in data_clinical.columns:
            data_clinical['Marital'] = data_clinical['Marital'].replace(
                {"NevMarried": "Not_Stated", "Unknown": "Not_Stated"})

        if 'Religion' in data_clinical.columns:
            data_clinical['Religion'] = data_clinical['Religion'].replace({"7101": "No Religion, so desc"})

        if 'Site_Name' in data_clinical.columns:
            data_clinical['Site_Name'] = data_clinical['Site_Name'].apply(
                lambda x: replace_nth_occurance(x, ".", "_", 2)).apply(
                lambda x: x.partition(".")[2])

        if 'SUVp' in data_clinical.columns:
            data_clinical['SUVp'] = data_clinical['SUVp'].replace({" ": None})
            # Convert values to their type
            data_clinical['SUVp'] = data_clinical['SUVp'].astype(float)
            data_clinical['SUVp'] = data_clinical['SUVp'].fillna(0)

        if 'Surgery' in data_clinical.columns:
            data_clinical['Surgery'] = data_clinical['Surgery'].str.strip()

        if 'Ext_Rad' in data_clinical.columns:
            data_clinical['Ext_Rad'] = data_clinical['Ext_Rad'].str.strip()

        if 'AgeAtDeath' in data_clinical.columns:
            data_clinical['AgeAtDeath'] = data_clinical['AgeAtDeath'].fillna(0)

        list_drop = check_percentage_missing_values(data_clinical)
        if list_drop:
            data_clinical = data_clinical.drop(list_drop, axis=1)

        return data_clinical

    # Preprocessing DVH data
    def pre_processing_dvh_data(self, dvh_data):
        dvh_data = dvh_data.fillna(0)
        dvh_data = dvh_data.drop_duplicates(subset=['HASHidentifier', 'ROI'], keep='last')
        return dvh_data

    # Preprocessing Pyrad data
    def pre_processing_pyrad_data(self, pyrad):
        list_columns_remove = ['diagnostics_Versions_PyRadiomics', 'diagnostics_Versions_Numpy',
                               'diagnostics_Versions_SimpleITK', 'diagnostics_Versions_PyWavelet',
                               'diagnostics_Versions_Python', 'diagnostics_Configuration_Settings',
                               'diagnostics_Image-original_Dimensionality', 'diagnostics_Image-original_Size',
                               'diagnostics_Mask-original_Hash', 'diagnostics_Mask-original_Spacing',
                               'diagnostics_Mask-original_Size', 'diagnostics_Configuration_EnabledImageTypes',
                               'diagnostics_Image-original_Hash', 'diagnostics_Image-original_Spacing']

        diff1 = list((Counter(pyrad.columns) - Counter(list_columns_remove)).elements())

        pyrad = pyrad[diff1]

        if 'diagnostics_Mask-original_CenterOfMassIndex' in pyrad.columns:
            pyrad['diagnostics_Mask-original_CenterOfMassIndex'] = pyrad[
                'diagnostics_Mask-original_CenterOfMassIndex'].apply(lambda x: ast.literal_eval(x)).apply(
                lambda x: sum(x) / len(x))
        if 'diagnostics_Mask-original_BoundingBox' in pyrad.columns:
            pyrad['diagnostics_Mask-original_BoundingBox'] = pyrad['diagnostics_Mask-original_BoundingBox'].apply(
                lambda x: ast.literal_eval(x)).apply(lambda x: sum(x) / len(x))
        if 'diagnostics_Mask-original_CenterOfMass' in pyrad.columns:
            pyrad['diagnostics_Mask-original_CenterOfMass'] = pyrad['diagnostics_Mask-original_CenterOfMass'].apply(
                lambda x: ast.literal_eval(x)).apply(lambda x: sum(x) / len(x))

        return pyrad

    def select_cross_id_in_dvh_and_payradiomics(self, clinical_data, dvh_data, pyrad_data):
        # get all List of unique IDs in Clinical Data
        clinical_data_id = clinical_data['HASHidentifier'].unique().tolist()
        dvh_data_id = dvh_data['HASHidentifier'].unique().tolist()
        pyrad_data_id = pyrad_data['HASHidentifier'].unique().tolist()
        # Find Missing IDs
        diff1 = list((Counter(clinical_data_id) - Counter(dvh_data_id)).elements())
        if len(diff1) != 0:
            self.missing_id.append(diff1)

        # check cross IDs in dvh and pyradiomics
        diff2 = list(set(dvh_data_id).intersection(pyrad_data_id))

        if len(diff2) <= 2:
            self.permission = False
            self.permission_ids = diff2
            logging.debug('According to DVH and Pyradiomics Datasets found less than 2 cross IDs')

        dvh_data = dvh_data[dvh_data['HASHidentifier'].isin(diff2)]
        clinical_data = clinical_data[clinical_data['HASHidentifier'].isin(dvh_data['HASHidentifier'])]
        return clinical_data

    # Reading Clinical,DVG,Pyrad and Preprocess it
    def pre_processing_data(self):
        clinical_data, dvh_data, pyrad_data = self.read_csv()  # Reading Clinical,DVG,Pyrad
        clinical_data = self.select_cross_id_in_dvh_and_payradiomics(clinical_data, dvh_data, pyrad_data)
        clinical_data = self.pre_processing_clinical_data(clinical_data)  # Preprocessing ClinicalData
        dvh_data = self.pre_processing_dvh_data(dvh_data)  # Preprocessing DVH
        pyrad_data = self.pre_processing_pyrad_data(pyrad_data)  # Preprocessing Pyrad

        return clinical_data, dvh_data, pyrad_data

    # Following function Merge 3 DFs into 1 Data Frame
    def merging_data(self, clinical_data, dvh_data, pyrad_data):
        # get all List of unique IDs in Clinical Data
        clinical_dvh = clinical_data.merge(dvh_data, how="left", on="HASHidentifier")
        clinical_dvh_pyrad = clinical_dvh.merge(pyrad_data, how="left", on="HASHidentifier")
        clinical_dvh_pyrad = clinical_dvh_pyrad.drop_duplicates()

        return clinical_dvh_pyrad

    """
    Following functions checks if we need to do upsampling for DataFrame to prevent imbalanced data
    This Function Should Take only selected target column.
    """

    def check_preprocessing_data(self):
        clinical_data, dvh, pyrad_data = self.pre_processing_data()
        if len(clinical_data) <= 1:
            return False

        return True

    def check_percentage_value_counts(self, data):
        count = 0
        min_p = 100.0  # find min % of the values in DF
        min_v = None  # to set this Value for upsampling
        for i, y in zip(data.value_counts().index, data.value_counts()):
            percentage = round(y / len(data), 2) * 100
            if count >= 2:
                return False, count
                break
            else:
                if percentage < min_p:
                    min_p = percentage
                    min_v = i
            count += 1

        if min_p < 10:
            return True, min_v
        else:
            return False, min_v

    # Following Function does upsampling for dataset Only if it is needed
    def up_sampling(self, data):
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

    def prepare_for_ml(self):
        clinical_data, dvh, pyrad_data = self.pre_processing_data()
        # Used only for Training if it is Testing Then returns Merged DF
        if self.target is not None and len(clinical_data) > 1:
            x_train, x_test = train_test_split(clinical_data, test_size=0.3, random_state=42)
            x_train = self.merging_data(x_train, dvh, pyrad_data)
            x_test = self.merging_data(x_test, dvh, pyrad_data)

            if self.missing_id != 0:
                logging.debug('Can not find ids in DVH and Pyradiomics')
                logging.debug(self.missing_id)

            x_train = x_train.drop(['HASHidentifier'], axis=1)
            x_test = x_test.drop(['HASHidentifier'], axis=1)

            result = self.check_percentage_value_counts(x_train[self.target])

            final_cat = x_train.select_dtypes(include=['object']).columns.tolist()
            final_num = x_train.select_dtypes(exclude=['object']).columns.tolist()

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
            if result[0]:
                x_train = self.up_sampling(x_train)

            # Split on Test and Train Dataset
            y_train = x_train[self.target]
            y_test = x_test[self.target]
            x_train = full_pipeline.fit_transform(x_train)
            x_test = full_pipeline.transform(x_test)
            self.scaling = full_pipeline

            return x_train, x_test, y_train, y_test
        # if DVH or Pyradiomics has only 1 id then return error
        elif self.target is not None and len(clinical_data) <= 1:
            return 1, 2, 3, 4

        else:
            data = self.merging_data(clinical_data, dvh, pyrad_data)
            ids = data['HASHidentifier']
            data = data.drop(['HASHidentifier'], axis=1)
            return data, ids

    # Should be saved in txt (columnNames), 2 value name of the Model (self.target+'_ML')
    def get_params_clinical_data(self):
        # if columnNames not empty
        if self.column_names is not None:
            self.column_names.remove(self.target)
            self.column_names.remove('HASHidentifier')

        # If columnNames is Empty
        else:
            data1, data2, data3 = self.read_csv()
            self.column_names = list(data1.columns)
            self.column_names.remove(self.target)
            self.column_names.remove('HASHidentifier')
        return {"columns": self.column_names,
                "saveModel": self.target}
