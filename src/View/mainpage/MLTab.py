import platform
import os
from os.path import expanduser
from src.Controller.PathHandler import resource_path
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtWidgets import QComboBox, QPushButton, QRadioButton, QMessageBox, QApplication, QDialog
import datetime

import pandas as pd
import numpy as np
#Skit Learn Modules
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler #standartiztion
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from sklearn.compose import ColumnTransformer
from sklearn.utils import resample
from collections import Counter
import logging
import ast
from joblib import Parallel, delayed
import joblib
# from src.Model.batchprocessing.batchprocessingMachineLearning.PreprocessingClass import Preprocessing

pd.options.mode.chained_assignment = None  # default='warn'

class Preprocessing:
    ##gets path of (Clinical Data,Pyrad,DVH), selected column name, type of the target, renamed columns
    def __init__(self
                 #Path
                ,pathClinicalData
                ,pathPyrData
                ,pathDVHData
                 #Selected Columns 
                ,columnNames=None
                 #Type of the Column (category/numerical)
                ,typeOfColumn=None
                 #Rename values list []
                ,target=None
                 #column Name for target
                ,renameValues=None):
        
        self.pathClinicalData = pathClinicalData
        self.pathPyrData = pathPyrData
        self.pathDVHData = pathDVHData
        self.columnNames = columnNames
        self.typeOfColumn = typeOfColumn
        self.renameValues = renameValues
        self.target = target
        self.scaling = None
    
    #read csv files and return 3 CSV files as pandas DF
    def read_csv(self):
        try:
            #Check if Path was provided for Clinical data and selected Columns Names
            if (self.columnNames != None):
                self.columnNames.append('HASHidentifier')
                
                #check if Target not NULL
                if (self.target != None):
                    self.columnNames.append(self.target)
            
                if self.pathClinicalData!=None:
                    data_Clinical = pd.read_csv(f'{self.pathClinicalData}',usecols=self.columnNames)
            else:
                if self.pathClinicalData!=None:
                    data_Clinical = pd.read_csv(f'{self.pathClinicalData}')
                
            
        #Check if Path was provided for DVH data        
            if self.pathDVHData!=None:
                data_DVH = pd.read_csv(f'{self.pathDVHData}',on_bad_lines='skip').rename(columns={"Patient ID":"HASHidentifier"})
            
        #Check if Path was provided for PyRad data    
            if self.pathPyrData!=None:
                data_Py = pd.read_csv(f'{self.pathPyrData}').rename(columns={"Hash ID":"HASHidentifier"})
                              
        except:
            logging.warning('Error in loading Files')
            
        return data_Clinical, data_DVH, data_Py
        
    
    """
    following function get 3 parameters Clinical Data pandas DF, Target Column, list of Values
    to be renamed and type of Column.
    If type of the column is catergory and List of values not null then it renames to set values.
    If it is numeric or list is empty it return initial pandas DF that was provided.
    """
    def rename(self,clinicalData):
        if (self.typeOfColumn=='category' and self.renameValues!=None):
            for i in range(len(self.renameValues)):
                clinicalData.loc[clinicalData[self.target]==i, self.target] = self.renameValues[i]
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
    def preProcessingClinicalData(self,clinicalData):
        
        #Function checks % of missing values in a column. Those Columns that are less than 5% will be removed from DF
        def check_percentage_ofMissingValues(data):
            dropColumns = []
            for x in data.columns:
                percentage = (100 - (data[x].isna().sum()/len(data)*100))
                if percentage < 5:
                    dropColumns.append(x)
    
            return dropColumns
        
        #Function to replace 2nd value in string
        def replace_nth_occurance(some_str, original, replacement, n):
            """ Replace nth occurance of a string with another string"""
            all_replaced = some_str.replace(original, replacement, n) # Replace all originals up to (including) nth occurance and assign it to the variable.
            for i in range(n):
                first_originals_back = all_replaced.replace(replacement, original, i) # Restore originals up to nth occurance (not including nth)
            return first_originals_back
        
        
        if (self.target !=None):
            clinicalData = self.rename(clinicalData)
                    
        listColumnsToRemove = ['Dist_Mets_1','Dist_Mets_2','Dist_Mets_3','DepthOfInvasion','Operation_DtTm',
                                   'OperationName','Chemo','ChemoDrug','Immuno','ImmunoDrug','Diag_Addendum',
                                   'PNI','SUVn','Birth_Place','Marital','Religion','Description','Diag_Code']
            
        diff1 = list((Counter(clinicalData.columns) - Counter(listColumnsToRemove)).elements())
            
        #Select columns that will be used in machined learning model
        data_Clinical = clinicalData[diff1]
        data_Clinical = data_Clinical.drop_duplicates(subset=['HASHidentifier'])
                  
        #preprocess
        try: 
            if 'Race' in data_Clinical.columns:
                data_Clinical['Race'] = data_Clinical['Race'].fillna("Not_Stated")
                
            if 'Marital' in data_Clinical.columns:
                data_Clinical['Marital'] = data_Clinical['Marital'].replace({"NevMarried": "Not_Stated", "Unknown": "Not_Stated"})
            
            if 'Religion' in data_Clinical.columns:
                data_Clinical['Religion'] = data_Clinical['Religion'].replace({"7101":"No Religion, so desc"})
                
            if 'Site_Name' in data_Clinical.columns:
                data_Clinical['Site_Name'] = data_Clinical['Site_Name'].apply(
                                            lambda x: replace_nth_occurance(x,".","_",2)).apply(
                                            lambda x: x.partition(".")[2])
            
            if 'SUVp' in data_Clinical.columns:
                data_Clinical['SUVp'] = data_Clinical['SUVp'].replace({" ":None})
                #Convert values to their type
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

    #Preprocessing DVH data    
    def preProcessingDVHData(self,dvhData):
        try:
            dvhData = dvhData.fillna(0)
            dvhData = dvhData.drop_duplicates(subset=['HASHidentifier', 'ROI'], keep='last')
    
        except:
            logging.warning('error in Preprocessing DVH Data columns')
            
        return dvhData
    
    #Preprocessing Pyrad data
    def preProcessingPyradData(self,Pyrad):
        listColumnsToRemove = ['diagnostics_Versions_PyRadiomics','diagnostics_Versions_Numpy',
                               'diagnostics_Versions_SimpleITK','diagnostics_Versions_PyWavelet',
                                'diagnostics_Versions_Python','diagnostics_Configuration_Settings',
                                'diagnostics_Image-original_Dimensionality','diagnostics_Image-original_Size',
                                'diagnostics_Mask-original_Hash','diagnostics_Mask-original_Spacing',
                                'diagnostics_Mask-original_Size','diagnostics_Configuration_EnabledImageTypes',
                                'diagnostics_Image-original_Hash','diagnostics_Image-original_Spacing']
        
        diff1 = list((Counter(Pyrad.columns) - Counter(listColumnsToRemove)).elements())
        
        Pyrad = Pyrad[diff1]
        
        try:
            if 'diagnostics_Mask-original_CenterOfMassIndex' in Pyrad.columns:
                Pyrad['diagnostics_Mask-original_CenterOfMassIndex'] = Pyrad['diagnostics_Mask-original_CenterOfMassIndex'].apply(lambda x :ast.literal_eval(x)).apply(lambda x:sum(x)/len(x))
            if 'diagnostics_Mask-original_BoundingBox' in Pyrad.columns: 
                Pyrad['diagnostics_Mask-original_BoundingBox'] = Pyrad['diagnostics_Mask-original_BoundingBox'].apply(lambda x :ast.literal_eval(x)).apply(lambda x:sum(x)/len(x))
            if 'diagnostics_Mask-original_CenterOfMass' in Pyrad.columns:    
                Pyrad['diagnostics_Mask-original_CenterOfMass'] = Pyrad['diagnostics_Mask-original_CenterOfMass'].apply(lambda x :ast.literal_eval(x)).apply(lambda x:sum(x)/len(x))
        except:
            logging.warning('error in Preprocessing Pyrad Data columns')
        
        return Pyrad
    
    
    #Reading Clinical,DVG,Pyrad and Preprocess it
    def preprocessingData(self):
        clinicalData,dvhData,pyradData = self.read_csv() #Reading Clinical,DVG,Pyrad
        clinicalData = self.preProcessingClinicalData(clinicalData)  #Preprocessing ClinicalData
        dvhData = self.preProcessingDVHData(dvhData) #Preprocessing DVH
        pyradData = self.preProcessingPyradData(pyradData) #Preprocessing Pyrad
        
        return clinicalData,dvhData,pyradData
    
    #Following function Merge 3 DFs into 1 Data Frame
    def mergingData(self,clinicalData,dvhData,pyradData):
        #get all List of unique IDs in Clinical Data
        Clinical_data = clinicalData['HASHidentifier'].unique().tolist()
        DVH_data = dvhData['HASHidentifier'].unique().tolist() 
        #Find Missing IDs
        diff1 = list((Counter(Clinical_data) - Counter(DVH_data)).elements())
        #Need to use here Logging to display IDs which is missing
        #logging.warning(data_Clinical[data_Clinical['HASHidentifier'].isin(diff1)][['HASHidentifier']])
        #merge
        clinicalData = clinicalData[clinicalData['HASHidentifier'].isin(dvhData['HASHidentifier'])]
        clnical_DVH = clinicalData.merge(dvhData, how="left", on="HASHidentifier")
        clnical_DVH_Pyrad = clnical_DVH.merge(pyradData, how="left", on=["HASHidentifier",'ROI'])
        clnical_DVH_Pyrad = clnical_DVH_Pyrad.drop_duplicates()
            
        return clnical_DVH_Pyrad
    
    """
    Following functions checks if we need to do upsampling for DataFrame to prevent imbalanced data
    This Function Should Take only selected target column.
    """
    def check_percentage_value_counts(self,data):
        count=0
        minP = 100.0 #find min % of the values in DF
        minV = None #to set this Value for upsampling
        for i, y in zip(data.value_counts().index, data.value_counts()):
            percentage = round(y/len(data),2)*100
            if count>=2:
                return False,count
                break
            else:
                if percentage<minP:
                    minP = percentage
                    minV = i
            count+=1
    
        if minP < 10:
            return True,minV
        else:
            return False,minV
        

    #Following Function does upsampling for dataset Only if it is needed
    def upSampling(self,data):
        result = self.check_percentage_value_counts(data[self.target])
        if result[0]:
            
            # Separate majority and minority classes
            df_majority = data[data[self.target]!=result[1]]
            df_minority = data[data[self.target]==result[1]]
 
            # Upsample minority class
            df_minority_upsampled = resample(df_minority, 
                                replace=True,     # sample with replacement
                                n_samples=len(df_majority),    # to match majority class
                                random_state=123) # reproducible results
 
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
        ClinicalData,DVH,Pyr = self.preprocessingData()
        #Used only for Training if it is Testing Then returns Merged DF
        if (self.target!=None):
            X_train, X_test = train_test_split(ClinicalData, test_size=0.3, random_state=42)
            X_train = self.mergingData(X_train,DVH,Pyr)
            X_test = self.mergingData(X_test,DVH,Pyr)
            
            X_train = X_train.drop(['HASHidentifier'],axis=1)
            X_test = X_test.drop(['HASHidentifier'],axis=1)

            result = self.check_percentage_value_counts(X_train[self.target])
            
            final_cat = X_train.select_dtypes(include=['object']).columns.tolist()
            final_num = X_train.select_dtypes(exclude=['object']).columns.tolist()
            
            if self.target in final_num:
                final_num.remove(self.target)
            else:
                final_cat.remove(self.target)
            #Scaling
            full_pipeline = ColumnTransformer([
            ("num", StandardScaler(), final_num),
            ("cat", OneHotEncoder(handle_unknown = 'ignore'), final_cat)
            ])
            
            #Check if label is inbalanced, if so, then it does Upsampling on train
            if result[0]:X_train = self.upSampling(X_train) 
                
            #Split on Test and Train Dataset
            y_train = X_train[self.target]
            y_test = X_test[self.target]       
            X_train = full_pipeline.fit_transform(X_train)
            X_test = full_pipeline.transform(X_test)
            self.scaling = full_pipeline

            
            return X_train, X_test, y_train, y_test            
        else:
            data = self.mergingData(ClinicalData,DVH,Pyr)
            IDs = data['HASHidentifier']
            data = data.drop(['HASHidentifier'],axis=1)
            return data,IDs
        
    #Should be saved in txt (columnNames), 2 value name of the Model (self.target+'_ML')
    def saveParam(self):
        #if columnNames not empty 
        if  self.columnNames != None:
            self.columnNames.remove(self.target)
            self.columnNames.remove('HASHidentifier')
       
        #If columnNames is Empty    
        else:
            
            data1,data2,data3 = self.read_csv()
            self.columnNames = list(data1.columns)
            self.columnNames.remove(self.target)
            self.columnNames.remove('HASHidentifier')
        return {"columns": self.columnNames,
                "saveModel":self.target}

class MLTab(QtWidgets.QWidget):
    """
    Tab for testing Machine learning model
    """

    def __init__(self):
        """
        Initialise the class
        """
        QtWidgets.QWidget.__init__(self)

        # Create the main layout
        self.main_layout = QtWidgets.QVBoxLayout()

        self.selected_model_directory = ""

        # Get the stylesheet
        if platform.system() == 'Darwin':
            self.stylesheet_path = "res/stylesheet.qss"
        else:
            self.stylesheet_path = "res/stylesheet-win-linux.qss"
        self.stylesheet = open(resource_path(self.stylesheet_path)).read()

        self.current_widgets = []

        self.clinical_data_csv_path = ""
        self.dvh_data_csv_path = ""
        self.pyrad_data_csv_path = ""

        self.directory_layout = QtWidgets.QFormLayout()
        self.main_layout.addLayout(self.directory_layout)

        self.navigate_to_select_csvs()

        self.setLayout(self.main_layout)

    # Function for Clinical Data
    def set_csv_output_location_clinical_data(self, path, enable=True,
                                             change_if_modified=False):
        """
        Set the location for the clinical_data-SR2CSV resulting .csv file.
        :param path: desired path.
        :param enable: Enable the directory text bar.
        :param change_if_modified: Change the directory if already been
                                   changed.
        """
        if not self.directory_input_clinical_data.isEnabled():
            self.directory_input_clinical_data.setText(path)
            self.directory_input_clinical_data.setEnabled(enable)
        elif change_if_modified:
            self.directory_input_clinical_data.setText(path)
            self.directory_input_clinical_data.setEnabled(enable)

        self.clinical_data_csv_path = path

    def get_csv_output_location_clinical_data(self):
        """
        Get the location of the desired output directory.
        """
        return self.directory_input_clinical_data.text()

    def show_file_browser_clinical_data(self):
        """
        Show the file browser for selecting a folder for the Onko
        default directory.
        """
        # Open a file dialog and return chosen directory
        path = QtWidgets.QFileDialog.getOpenFileName(
            None, "Open Clinical Data File", "",
            "CSV data files (*.csv *.CSV)")[0]

        # If chosen directory is nothing (user clicked cancel) set to
        # user home
        if path == "" and self.directory_input_clinical_data.text() == 'No file selected':
            path = expanduser("~")
        elif (path == ""
              and
              (self.directory_input_clinical_data.text() != 'No file selected'
               or self.directory_input_clinical_data.text() != expanduser("~"))):
            path = self.directory_input_clinical_data.text()

        # Update file path
        self.set_csv_output_location_clinical_data(path, change_if_modified=True)

    def show_file_browser_saved_model(self):
        """
        Show the file browser for selecting a folder for the Onko
        default directory.
        """
        # Open a file dialog and return chosen directory
        path = QtWidgets.QFileDialog.getExistingDirectory(
            None, "Open Directory")

        self.selected_model_directory = path

        # If chosen directory is nothing (user clicked cancel) set to
        # user home
        if path == "" and self.directory_input_ml_model.text() == 'No file selected':
            path = expanduser("~")
        elif (path == ""
              and
              (self.directory_input_ml_model.text() != 'No file selected'
               or self.directory_input_ml_model.text() != expanduser("~"))):
            path = self.directory_input_ml_model.text()

        # Update file path
        self.directory_input_ml_model.setText(path)
        self.on_model_directory_changed()

    # Function for DVH Data
    def set_csv_output_location_dvh_data(self, path, enable=True,
                                        change_if_modified=False):
        """
        Set the location for the clinical_data-SR2CSV resulting .csv file.
        :param path: desired path.
        :param enable: Enable the directory text bar.
        :param change_if_modified: Change the directory if already been
                                   changed.
        """
        if not self.directory_input_dvh_data.isEnabled():
            self.directory_input_dvh_data.setText(path)
            self.directory_input_dvh_data.setEnabled(enable)
        elif change_if_modified:
            self.directory_input_dvh_data.setText(path)
            self.directory_input_dvh_data.setEnabled(enable)

        self.dvh_data_csv_path = path

    def get_csv_output_location_dvh_data(self):
        """
        Get the location of the desired output directory.
        """
        return self.directory_input_dvh_data.text()

    def show_file_browser_dvh_data(self):
        """
        Show the file browser for selecting a folder for the Onko
        default directory.
        """
        # Open a file dialog and return chosen directory
        path = QtWidgets.QFileDialog.getOpenFileName(
            None, "Open Clinical Data File", "",
            "CSV data files (*.csv *.CSV)")[0]

        # If chosen directory is nothing (user clicked cancel) set to
        # user home
        if path == "" and self.directory_input_dvh_data.text() == 'No file selected':
            path = expanduser("~")
        elif (path == ""
              and
              (self.directory_input_dvh_data.text() != 'No file selected'
               or self.directory_input_dvh_data.text() != expanduser("~"))):
            path = self.directory_input_dvh_data.text()

        # Update file path
        self.set_csv_output_location_dvh_data(path, change_if_modified=True)

    # Function for Pyrad Data
    def set_csv_output_location_pyrad(self, path, enable=True,
                                      change_if_modified=False):
        """
        Set the location for the clinical_data-SR2CSV resulting .csv file.
        :param path: desired path.
        :param enable: Enable the directory text bar.
        :param change_if_modified: Change the directory if already been
                                   changed.
        """
        if not self.directory_input_pyrad.isEnabled():
            self.directory_input_pyrad.setText(path)
            self.directory_input_pyrad.setEnabled(enable)
        elif change_if_modified:
            self.directory_input_pyrad.setText(path)
            self.directory_input_pyrad.setEnabled(enable)
        
        self.pyrad_data_csv_path = path

    def get_csv_output_location_pyrad(self):
        """
        Get the location of the desired output directory.
        """
        return self.directory_input_pyrad.text()

    def show_file_browser_pyrad(self):
        """
        Show the file browser for selecting a folder for the Onko
        default directory.
        """
        # Open a file dialog and return chosen directory
        path = QtWidgets.QFileDialog.getOpenFileName(
            None, "Open Clinical Data File", "",
            "CSV data files (*.csv *.CSV)")[0]

        # If chosen directory is nothing (user clicked cancel) set to
        # user home
        if path == "" and self.directory_input_pyrad.text() == 'No file selected':
            path = expanduser("~")
        elif (path == ""
              and
              (self.directory_input_pyrad.text() != 'No file selected'
               or self.directory_input_pyrad.text() != expanduser("~"))):
            path = self.directory_input_pyrad.text()

        # Update file path
        self.set_csv_output_location_pyrad(path, change_if_modified=True)
    
    def navigate_to_select_csvs(self):
        self.clear_current_widgets()

        self.label_clinical_data = QtWidgets.QLabel("Please choose the CSV file location for Clinical Data:")
        self.label_clinical_data.setStyleSheet(self.stylesheet)
        self.current_widgets.append(self.label_clinical_data)

        self.label_DVG = QtWidgets.QLabel("Please choose the CSV file location for DVH Data:")
        self.label_DVG.setStyleSheet(self.stylesheet)
        self.current_widgets.append(self.label_DVG)

        self.label_Pyrad = QtWidgets.QLabel("Please choose the CSV file location for Pyradiomics Data:")
        self.label_Pyrad.setStyleSheet(self.stylesheet)
        self.current_widgets.append(self.label_Pyrad)

        # Directory text box for clinical Data
        self.directory_input_clinical_data = QtWidgets.QLineEdit("No file selected")
        self.directory_input_clinical_data.setStyleSheet(self.stylesheet)
        self.directory_input_clinical_data.setEnabled(False)
        self.current_widgets.append(self.directory_input_clinical_data)

        # Button For clinical Data to set location
        self.change_button_clinical_data = QtWidgets.QPushButton("Change")
        self.change_button_clinical_data.setMaximumWidth(100)
        self.change_button_clinical_data.clicked.connect(self.show_file_browser_clinical_data)
        self.change_button_clinical_data.setObjectName("NormalButton")
        self.change_button_clinical_data.setStyleSheet(self.stylesheet)
        self.current_widgets.append(self.change_button_clinical_data)

        # Directory text box for DVH Data
        self.directory_input_dvh_data = QtWidgets.QLineEdit("No file selected")
        self.directory_input_dvh_data.setStyleSheet(self.stylesheet)
        self.directory_input_dvh_data.setEnabled(False)
        self.current_widgets.append(self.directory_input_dvh_data)

        # Button For DVH Data to set location
        self.change_button_dvh_data = QtWidgets.QPushButton("Change")
        self.change_button_dvh_data.setMaximumWidth(100)
        self.change_button_dvh_data.clicked.connect(self.show_file_browser_dvh_data)
        self.change_button_dvh_data.setObjectName("NormalButton")
        self.change_button_dvh_data.setStyleSheet(self.stylesheet)
        self.current_widgets.append(self.change_button_dvh_data)

        # Directory text box for Pyradiomics Data
        self.directory_input_pyrad = QtWidgets.QLineEdit("No file selected")
        self.directory_input_pyrad.setStyleSheet(self.stylesheet)
        self.directory_input_pyrad.setEnabled(False)
        self.current_widgets.append(self.directory_input_pyrad)

        # Button For Pyradiomics Data to set location
        self.change_button_pyradiomicsData = QtWidgets.QPushButton("Change")
        self.change_button_pyradiomicsData.setMaximumWidth(100)
        self.change_button_pyradiomicsData.clicked.connect(self.show_file_browser_pyrad)
        self.change_button_pyradiomicsData.setObjectName("NormalButton")
        self.change_button_pyradiomicsData.setStyleSheet(self.stylesheet)
        self.current_widgets.append(self.change_button_pyradiomicsData)

        # Set Clinical Data
        self.directory_layout.addWidget(self.label_clinical_data)
        self.directory_layout.addRow(self.directory_input_clinical_data)
        self.directory_layout.addRow(self.change_button_clinical_data)

        # Set DVH data
        self.directory_layout.addWidget(self.label_DVG)
        self.directory_layout.addRow(self.directory_input_dvh_data)
        self.directory_layout.addRow(self.change_button_dvh_data)

        # Set Pyradiomics data
        self.directory_layout.addWidget(self.label_Pyrad)
        self.directory_layout.addRow(self.directory_input_pyrad)
        self.directory_layout.addRow(self.change_button_pyradiomicsData)

        # Initialise Next Button
        self.next_button = QPushButton()
        self.next_button.setText("Next")
        self.next_button.clicked.connect(self.navigate_to_model_selection)
        self.directory_layout.addWidget(self.next_button)
        self.current_widgets.append(self.next_button)

    def clear_current_widgets(self):
        for widget in self.current_widgets:
            widget.setParent(None)

    def navigate_to_model_selection(self):
        if not all((self.get_csv_output_location_clinical_data(),
                    self.get_csv_output_location_dvh_data(),
                    self.get_csv_output_location_pyrad())):
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Error!")
            dlg.setText("Please Provide a path for each file")
            button = dlg.exec_()

            if button == QMessageBox.Ok:
                print("Try Again")

            return

        self.clear_current_widgets()

        # Create what directory to select model from
        self.label_ml_model = QtWidgets.QLabel("Please choose the directory where the Machine learning models have been stored:")
        self.current_widgets.append(self.label_ml_model)
        self.directory_layout.addWidget(self.label_ml_model)

        # Directory text box for clinical Data
        self.directory_input_ml_model = QtWidgets.QLineEdit("No file selected")
        self.directory_input_ml_model.setEnabled(False)
        self.current_widgets.append(self.directory_input_ml_model)
        self.directory_layout.addRow(self.directory_input_ml_model)

        # Button For clinical Data to set location
        self.change_button_ml_model = QtWidgets.QPushButton("Change")
        self.change_button_ml_model.setMaximumWidth(100)
        self.change_button_ml_model.clicked.connect(self.show_file_browser_saved_model)
        # self.change_button_clinical_data.setStyleSheet(self.stylesheet)
        self.current_widgets.append(self.change_button_clinical_data)
        self.directory_layout.addRow(self.change_button_ml_model)

        # create dropdown menu
        self.label_combobox = QtWidgets.QLabel("Select model:")
        self.current_widgets.append(self.label_combobox)
        self.directory_layout.addWidget(self.label_combobox)

        self.combobox = QComboBox()
        self.directory_layout.addRow(self.combobox)
        self.combobox.setEnabled(False)
        self.current_widgets.append(self.combobox)

        # Initialise Next Button
        self.next_button = QPushButton()
        self.next_button.setText("Run model")
        self.next_button.clicked.connect(self.run_prediction)
        self.current_widgets.append(self.next_button)
        self.directory_layout.addWidget(self.next_button)
        
        # add back button
        self.back_button = QPushButton()
        self.back_button.setText("Back")
        self.back_button.clicked.connect(self.navigate_to_select_csvs)
        self.current_widgets.append(self.back_button)
        self.directory_layout.addWidget(self.back_button)

    def on_model_directory_changed(self):
        # search directory for all necessary files
        model_options = []

        directories = [self.selected_model_directory]

        for directory in os.listdir(self.selected_model_directory):
            subdirectory = f"{self.selected_model_directory}/{directory}"
            
            if os.path.isdir(subdirectory):
                directories.append(subdirectory)

        for directory in directories:
            if not os.path.isdir(directory):
                continue
            
            save_file_suffixes = {"_ml.pkl": 0,
                                  "_params.txt": 0,
                                  "_scaler.pkl": 0}
            save_file_names = []
            
            for file in os.listdir(directory):
                for suffix in save_file_suffixes:
                    if str(file).endswith(suffix):
                        save_file_names.append(file)
                        save_file_suffixes[suffix]+=1
            
            valid = True
            for key, value in save_file_suffixes.items():
                if value != 1:
                    valid = False

            if valid:
                model_name = "".join(save_file_names[0].split("_")[:-1])
                model_options.append(model_name)

        # display all found models in dropdown to be selected from
        self.combobox.clear()

        if len(model_options) > 0:
            self.combobox.setEnabled(True)
        else:
            self.combobox.setEnabled(False)
        
        self.combobox.addItems(model_options)

    def get_selected_model(self):
        if self.combobox.isEnabled():
            return self.combobox.currentText()

    def get_model_path(self):
        if self.directory_input_ml_model.text().endswith(self.get_selected_model()):
            return self.directory_input_ml_model.text()
        else:
            return f"{self.directory_input_ml_model.text()}/{self.get_selected_model()}"

    def run_prediction(self):
        model_path = self.get_model_path()

        # trigger ML model to run
        # requires the directory for the 3 csvs + selected model directory
        ml_tester = MachineLearningTester(
            self.clinical_data_csv_path,
            self.dvh_data_csv_path,
            self.pyrad_data_csv_path,
            model_path,
            self.get_selected_model()
        )

        ml_tester.predict_values() # return True/False if successful or error

        # once run will trigger results popup window

        results = f"According to the '{ml_tester.get_model_name()}' " \
            f"model located in '{self.get_model_path()}', the following values " \
            f"have been predicted: '{ml_tester.get_predicted_values()}' " \
            f"for the column: '{ml_tester.get_target()}'"

        ml_results_window = MLResultsWindow()
        ml_results_window.set_results_values(results)
        ml_results_window.set_ml_tester(ml_tester)

        ml_results_window.exec_()

class MachineLearningTester:
    def __init__(self,
                 clinical_data_csv_path,
                 dvh_csv_path, 
                 pyrad_csv_path, 
                 saved_model_path, 
                 model_name):
        self.clinical_data_csv_path = clinical_data_csv_path
        self.dvh_csv_path = dvh_csv_path
        self.pyrad_csv_path = pyrad_csv_path
        self.saved_model_path = saved_model_path
        self.model_name = model_name
        self.predicted_column_name = ""

    def get_predicted_values(self):
        return self.predictions

    def get_target(self):
        return self.predicted_column_name

    def get_model_name(self):
        return self.model_name

    def predict_values(self):
        scaler_file_name = f"{self.saved_model_path}/{self.model_name}_scaler.pkl"
        params_file_name = f"{self.saved_model_path}/{self.model_name}_params.txt"
        ml_file_name = f"{self.saved_model_path}/{self.model_name}_ml.pkl"

        my_columns, self.predicted_column_name = self.read_txt_ml_params(params_file_name)

        testing_data = Preprocessing(
            pathClinicalData = self.clinical_data_csv_path,
            pathPyrData = self.pyrad_csv_path,
            pathDVHData = self.dvh_csv_path,
            columnNames = my_columns
        )

        self.data, self.ID = testing_data.prepareforML()

        scaler = self.get_saved_model(scaler_file_name)

        scaled_data = self.scale(scaler, self.data)

        saved_model = self.get_model_file(ml_file_name)

        self.predictions = self.predict(saved_model, scaled_data)

        return True

    def save_into_csv(self, path_to_save):
        # TODO: is all this necessary?
        new_data = pd.read_csv(self.clinical_data_csv_path)
        new_data = new_data[['HASHidentifier']]
        pyrad = pd.read_csv(self.pyrad_csv_path).rename(columns={"Hash ID":"HASHidentifier"})[['HASHidentifier','ROI']]
        self.data['HASHidentifier'] = self.ID
        self.data[self.predicted_column_name] = self.predictions
        self.data = self.data[['HASHidentifier',self.predicted_column_name]]
        final_data = pyrad.merge(self.data,how='left',on='HASHidentifier')
        final_data = new_data.merge(final_data,how='left',on='HASHidentifier')
        final_data = final_data.drop_duplicates(subset=['HASHidentifier','ROI']).reset_index(drop=True)
        final_data.to_csv(f"{path_to_save}/Clinical_data_with_predicted_{self.get_target()}.csv", index=False)

    def read_txt_ml_params(self, path):
        my_file = open(f"{path}", "r")
        content = my_file.read()
        content = content.replace('[','').replace(']','').replace("'","").replace('\n',"").replace(" ","")
        content_list = content.split(",")
        
        return content_list[:-1],content_list[len(content_list)-1]

    def get_saved_model(self, path_pipline):
        try:
            pipline_joblib = joblib.load(path_pipline)
            return pipline_joblib 
        except:
            logging.warning('error in getting file for pipline')

    def scale(self, pipline_joblib, data):
        try:
            scaled_data = pipline_joblib.transform(data)  # this returns the scaled data
            return scaled_data
        except:
            logging.warning('error in transformation of data throught pipline')

    def get_model_file(self, ml_modelfile):
        try:
            ml_model = joblib.load(ml_modelfile)   # this is the file saves for ML_model
            return ml_model
        except:
            logging.warning('error in getting file for Saved Model')

    def predict(self, save_model, scaledata):
        try:
            predicted = predict = save_model.predict(scaledata)   # predict the value
            return predicted
        except:
            logging.warning('error while predicting data from Save ML model')

class MLResultsWindow(QtWidgets.QDialog):
    """
    This class creates a GUI window for displaying a summary of batch
    processing. It inherits from QDialog.
    """

    def __init__(self):
        QtWidgets.QDialog.__init__(self)
        self.ml_tester = None
        self.params = None
        self.scaling = None

        # # Set maximum width, icon, and title
        self.setFixedSize(450, 450)
        self.setWindowTitle("Machine Learning Model Test Results")
        window_icon = QtGui.QIcon()
        window_icon.addPixmap(
            QtGui.QPixmap(resource_path("res/images/icon.ico")),
            QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(window_icon)

        # Create widgets
        self.summary_label = QtWidgets.QLabel()
        self.summary_label.setWordWrap(True)
        self.scroll_area = QtWidgets.QScrollArea()
        self.save_ml_predicted_txt = QtWidgets.QPushButton("Save Txt file with above information")
        self.save_ml_predicted_csv = QtWidgets.QPushButton("Save CSV with predicted values")

        # # Get stylesheet
        if platform.system() == 'Darwin':
            self.stylesheet_path = "res/stylesheet.qss"
        else:
            self.stylesheet_path = "res/stylesheet-win-linux.qss"
        self.stylesheet = open(resource_path(self.stylesheet_path)).read()

        # Set stylesheet
        self.summary_label.setStyleSheet(self.stylesheet)
        self.scroll_area.setStyleSheet(self.stylesheet)
        self.save_ml_predicted_txt.setStyleSheet(self.stylesheet)
        self.save_ml_predicted_csv.setStyleSheet(self.stylesheet)

        # Make QLabel wrap text
        self.summary_label.setWordWrap(True)

        # Set scroll area properties
        self.scroll_area.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.summary_label)

        # Create layout
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.scroll_area)
        self.layout.addStretch(1)
        self.layout.addWidget(self.save_ml_predicted_txt)
        self.layout.addWidget(self.save_ml_predicted_csv)

        # Connect button to functions
        self.save_ml_predicted_txt.clicked.connect(self.save_ml_txt_with_predicted_values_clicked)
        self.save_ml_predicted_csv.clicked.connect(self.save_ml_csv_with_predicted_values_clicked)

        # Set layout of window
        self.setLayout(self.layout)

    def set_results_values(self, results_string):
        """
        Sets the summary text.
        :param batch_summary: List where first index is a dictionary where key
                              is a patient, and value is a dictionary of
                              process name and status key-value pairs, and
                              second index is a batch ROI name cleaning summary
        """

        self.summary_label.setText(results_string)

    def set_ml_tester(self, ml_tester):
        self.ml_tester = ml_tester

    def save_ml_csv_with_predicted_values_clicked(self):
        file_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Open Directory", "",
                                                               QtWidgets.QFileDialog.ShowDirsOnly | QtWidgets.QFileDialog.DontResolveSymlinks)
        if file_path:
            self.ml_tester.save_into_csv(f'{file_path}/')

    def save_ml_txt_with_predicted_values_clicked(self):
        file_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Open Directory", "",
                                                               QtWidgets.QFileDialog.ShowDirsOnly | QtWidgets.QFileDialog.DontResolveSymlinks)
        if file_path:
            with open(f"{file_path}/Prediction_summary_{self.create_timestamp()}.txt", "w") as output_file:
                output_file.write(self.summary_label.text())

    def create_timestamp(self):
        """
        Create a unique timestamp as a string.
        returns string
        """
        cur_time = datetime.datetime.now()
        year = cur_time.year
        month = cur_time.month
        day = cur_time.day
        hour = cur_time.hour
        mins = cur_time.minute
        sec = cur_time.second

        return f"{year}{month}{day}{hour}{mins}{sec}"
