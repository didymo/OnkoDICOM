# This file handles all the processes within the Main page window of the
# software
import csv
import glob
# removing warnings
import math
import os
from pathlib import Path

import matplotlib.cbook
import matplotlib.pyplot as plt1
from PySide6 import QtWidgets, QtCore, QtGui
from dateutil.relativedelta import relativedelta
from networkx.tests.test_convert_pandas import pd
from matplotlib.backend_bases import MouseEvent

import src.constants as constant
from src.View.mainpage.ClinicalDataDisplay import Ui_CD_Display
from src.View.mainpage.ClinicalDataForm import Ui_Form
from src.Model.Anon import anonymize
from src.Model.PatientDictContainer import PatientDictContainer
from src.Controller.PathHandler import resource_path

matplotlib.cbook.handle_exceptions = "print"  # default
matplotlib.cbook.handle_exceptions = "raise"
matplotlib.cbook.handle_exceptions = "ignore"

# matplotlib.cobook.handle_exceptions = my_logger
# will be called with exception as argument

# The following code are global functions and data/variables used by both
# Clinical Data form and Display classes

# This variable holds the errors messages of the Clinical data form
message = ""

# reading the csv files containing the available diseases
with open(resource_path('data/ICD10_Topography.csv'), 'r') as f:
    reader = csv.reader(f)
    icd = list(reader)
    icd.pop(0)
with open(resource_path('data/ICD10_Topography_C.csv'), 'r') as f:
    reader = csv.reader(f)
    icdc = list(reader)
    icdc.pop(0)
with open(resource_path('data/ICD10_Morphology.csv'), 'r') as f:
    reader = csv.reader(f)
    hist = list(reader)
    hist.pop(0)

# Creating the arrays containing the above data and formatting them
# appropriately
new_icd = []
new_hist = []
strg = ''

for items in icd:
    for item in items:
        strg = strg + item
    new_icd.append(strg)
    strg = ''

for items in icdc:
    for item in items:
        strg = strg + item
    new_icd.append(strg)
    strg = ''

for items in hist:
    for item in items:
        strg = strg + item
    new_hist.append(strg)
    strg = ''


# This function return the difference of two dates in decimal years
def calculate_years(year1, year2):
    difference_years = relativedelta(year2.toPython(), year1.toPython()).years

    difference_months = relativedelta(
        year2.toPython(), year1.toPython()).months
    difference_in_days = relativedelta(year2.toPython(), year1.toPython()).days
    value = difference_years \
            + (difference_months / 12) \
            + (difference_in_days / 365)
    return "%.2f" % value


# This Class handles the Clinical Data Form display in both new mode and
# editing mode of clinical data

class ClinicalDataForm(QtWidgets.QWidget, Ui_Form):
    open_patient_window = QtCore.Signal(str)

    # Initialisation function of the form's UI
    def __init__(self, tab_window, path, ds, fn):
        QtWidgets.QWidget.__init__(self)

        self.path = path
        self.dataset = ds
        self.filenames = fn
        self.pID = self.dataset[0].PatientID
        self.tabWindow = tab_window
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        # setting tab order
        self.setTabOrder(self.ui.line_LN, self.ui.line_FN)
        self.setTabOrder(self.ui.line_FN, self.ui.date_of_birth)
        self.setTabOrder(self.ui.date_of_birth, self.ui.line_BP)
        self.setTabOrder(self.ui.line_BP, self.ui.date_diagnosis)
        self.setTabOrder(self.ui.date_diagnosis, self.ui.gender)
        self.setTabOrder(self.ui.gender, self.ui.line_icd)
        self.setTabOrder(self.ui.line_icd, self.ui.line_histology)
        self.setTabOrder(self.ui.line_histology, self.ui.T_stage)
        self.setTabOrder(self.ui.T_stage, self.ui.N_stage)
        self.setTabOrder(self.ui.N_stage, self.ui.M_stage)
        self.setTabOrder(self.ui.M_stage, self.ui.Overall_Stage)
        self.setTabOrder(self.ui.Overall_Stage, self.ui.Tx_intent)
        self.setTabOrder(self.ui.Tx_intent, self.ui.Surgery)
        self.setTabOrder(self.ui.Surgery, self.ui.Rad)
        self.setTabOrder(self.ui.Rad, self.ui.Chemo)
        self.setTabOrder(self.ui.Chemo, self.ui.Immuno)
        self.setTabOrder(self.ui.Immuno, self.ui.Brachy)
        self.setTabOrder(self.ui.Brachy, self.ui.Hormone)
        self.setTabOrder(self.ui.Hormone, self.ui.Dt_Last_Existence)
        self.setTabOrder(self.ui.Dt_Last_Existence, self.ui.Death)
        self.setTabOrder(self.ui.Death, self.ui.Cancer_death)
        self.setTabOrder(self.ui.Cancer_death, self.ui.Local_control)
        self.setTabOrder(self.ui.Local_control, self.ui.Dt_local_failure)
        self.setTabOrder(self.ui.Dt_local_failure, self.ui.Regional_Control)
        self.setTabOrder(self.ui.Regional_Control, self.ui.Dt_REgional_failure)
        self.setTabOrder(self.ui.Dt_REgional_failure, self.ui.Distant_Control)
        self.setTabOrder(self.ui.Distant_Control, self.ui.Dt_Distant_Failure)
        self.setTabOrder(self.ui.Dt_Distant_Failure, self.ui.Save_button)
        # Linking different aspects of the form with each other since
        # different options cause other options to change
        self.ui.Local_control.activated.connect(self.local_control_failure)
        self.ui.Regional_Control.activated.connect(
            self.regional_control_failure)
        self.ui.Distant_Control.activated.connect(self.distant_control_failure)
        self.ui.Tx_intent.activated.connect(self.tx_intent_refused)
        self.ui.Death.activated.connect(self.patient_dead)
        self.ui.Death.activated.connect(self.show_survival)
        # Save button to activate csv creation
        self.ui.Save_button.clicked.connect(self.on_click)

    # The following functions retrieve the corresponding codes of the
    # selected options

    # get code for Surgery/Rad/Chemo/Immuno/Btrachy/Hormone
    def get_code(self, the_choice):
        if the_choice == "Primary (Pri)":
            return "Pri"
        elif the_choice == "Refused (Ref)":
            return "Ref"
        elif the_choice == "Denied (Den)":
            return "Den"
        elif the_choice == "DiedB4 (Die)":
            return "Die"
        elif the_choice == "Neoadjuvant (Neo)":
            return "Neo"
        elif the_choice == "Concurrent (Con)":
            return "Con"
        elif the_choice == "Adjuvant (Adj)":
            return "Adj"
        else:
            return the_choice

    # get the code for when saving the Alive option
    def code_alive(self, choice):
        if choice == "Alive":
            return 0
        else:
            return 1

    # get code for when saving the Control option
    def code_control(self, choice):
        if choice == "Control":
            return 0
        else:
            return 1

    # get code for when saving the Cancer Death option
    def code_cancer_death(self, choice):
        if choice == "Non-cancer death":
            return 0
        elif choice == "Cancer death":
            return 1
        else:
            return 0

    # get the code for the selected desease
    def get_desease_code(self, string):
        return string[:string.index(" ")]

    # The following functions handle changes on the form based on selected
    # otions of some elements

    # This function shows the survival of a patient without cancer since
    # last diagnosed
    def show_survival(self):
        survival_years = str(calculate_years(
            self.ui.date_diagnosis.date(), self.ui.Dt_Last_Existence.date()))
        self.ui.Survival_dt.setText("Survival Length: " + survival_years)
        self.ui.Survival_dt.setVisible(True)

    # check if patient is alive or not
    def patient_dead(self):
        status = str(self.ui.Death.currentText())
        if status == "Alive":
            self.ui.Cancer_death.setDisabled(True)
        else:
            self.ui.Cancer_death.setDisabled(False)

    # handles the case where Tx_intent is Refused
    def tx_intent_refused(self):
        choice = str(self.ui.Tx_intent.currentText())
        if choice == 'Refused':
            self.ui.Surgery.setCurrentIndex(1)
            self.ui.Rad.setCurrentIndex(1)
            self.ui.Chemo.setCurrentIndex(1)
            self.ui.Immuno.setCurrentIndex(1)
            self.ui.Brachy.setCurrentIndex(1)
            self.ui.Hormone.setCurrentIndex(1)
            self.ui.Surgery.setDisabled(True)
            self.ui.Rad.setDisabled(True)
            self.ui.Chemo.setDisabled(True)
            self.ui.Immuno.setDisabled(True)
            self.ui.Brachy.setDisabled(True)
            self.ui.Hormone.setDisabled(True)
        elif choice != 'Refused':
            self.ui.Surgery.setDisabled(False)
            self.ui.Rad.setDisabled(False)
            self.ui.Chemo.setDisabled(False)
            self.ui.Immuno.setDisabled(False)
            self.ui.Brachy.setDisabled(False)
            self.ui.Hormone.setDisabled(False)
            self.ui.Surgery.setCurrentIndex(0)
            self.ui.Rad.setCurrentIndex(0)
            self.ui.Chemo.setCurrentIndex(0)
            self.ui.Immuno.setCurrentIndex(0)
            self.ui.Brachy.setCurrentIndex(0)
            self.ui.Hormone.setCurrentIndex(0)

    # handles the change in the date of local failure according on the
    # option selected at the local failure combo box
    def local_control_failure(self):
        local_failure = str(self.ui.Local_control.currentText())
        if local_failure == "Control":
            self.ui.Dt_local_failure.setDisabled(True)
        elif local_failure == "Failure":
            self.ui.Dt_local_failure.setDisabled(False)
            self.ui.Dt_local_failure.setReadOnly(False)
        elif local_failure == "Select...":
            self.ui.Dt_local_failure.setDisabled(True)

    # handles the change in date of regional failure according to the
    # regional failure option selected
    def regional_control_failure(self):
        regional_failure = str(self.ui.Regional_Control.currentText())
        if regional_failure == "Control":
            self.ui.Dt_REgional_failure.setDisabled(True)
        elif regional_failure == "Failure":
            self.ui.Dt_REgional_failure.setDisabled(False)
            self.ui.Dt_REgional_failure.setReadOnly(False)
        elif regional_failure == "Select...":
            self.ui.Dt_REgional_failure.setDisabled(True)

    # handles the change in date of distant failure according to the option
    # chosen in distant control
    def distant_control_failure(self):
        distant_failure = str(self.ui.Distant_Control.currentText())
        if distant_failure == "Control":
            self.ui.Dt_Distant_Failure.setDisabled(True)
        elif distant_failure == "Failure":
            self.ui.Dt_Distant_Failure.setDisabled(False)
            self.ui.Dt_Distant_Failure.setReadOnly(False)
        elif distant_failure == "Select...":
            self.ui.Dt_Distant_Failure.setDisabled(True)

    # The following function function performs some form validations before
    # saving and records them for display if any

    # validating the data in the form
    def form_validation(self):
        global message
        if len(self.ui.line_LN.text()) == 0:
            message = message + "Input patient's last name. \n"
        if len(self.ui.line_FN.text()) == 0:
            message = message + "Input patient's first name. \n"
        if str(self.ui.gender.currentText()) == "Select...":
            message = message + "Select patient's gender. \n"
        if len(self.ui.line_BP.text()) == 0:
            message = message + "Input patient's birth place. \n"
        if self.ui.date_of_birth.date() > QtCore.QDate.currentDate():
            message = message + "Patient's date of birth cannot be in the " \
                                "future. \n "
        if self.ui.date_diagnosis.date() > QtCore.QDate.currentDate():
            message = message + "Patient's date of diagnosis cannot be in " \
                                "the future. \n "
        if len(self.ui.line_icd.text()) == 0:
            message = message + "Input patient's ICD 10. \n"
        if self.ui.line_icd.text() not in new_icd:
            message = message + "The ICD 10 value needs to be from the " \
                                "completer options. \n "
        if len(self.ui.line_histology.text()) == 0:
            message = message + "Input patient's Histology. \n"
        if self.ui.line_histology.text() not in new_hist:
            message = message + "The Histology value needs to be from the " \
                                "completer options. \n "
        if str(self.ui.T_stage.currentText()) == "Select...":
            message = message + "Select patient's T Stage. \n"
        if str(self.ui.N_stage.currentText()) == "Select...":
            message = message + "Select patient's N Stage. \n"
        if str(self.ui.M_stage.currentText()) == "Select...":
            message = message + "Select patient's M Stage. \n"
        if str(self.ui.Overall_Stage.currentText()) == "Select...":
            message = message + "Select patient's Overall Stage. \n"
        if str(self.ui.Tx_intent.currentText()) == "Select...":
            message = message + "Select patient's Tx_Intent. \n"
        if str(self.ui.Surgery.currentText()) == "Select...":
            message = message + "Select patient's Surgery. \n"
        if str(self.ui.Rad.currentText()) == "Select...":
            message = message + "Select patient's Rad. \n"
        if str(self.ui.Chemo.currentText()) == "Select...":
            message = message + "Select patient's Chemo. \n"
        if str(self.ui.Brachy.currentText()) == "Select...":
            message = message + "Select patient's Brachy. \n"
        if str(self.ui.Hormone.currentText()) == "Select...":
            message = message + "Select patient's Hormone. \n"
        if self.ui.Dt_Last_Existence.date() > QtCore.QDate.currentDate():
            message = message + "Patient's date of last existence cannot be " \
                                "in the future. \n "
        if str(self.ui.Death.currentText()) == "Select...":
            message = message + "Select patient's Death. \n"
        if ((str(self.ui.Cancer_death.currentText()) == "Select...") and (
                str(self.ui.Death.currentText()) == "Dead")):
            message = message + "Select patient's Cancer Death. \n"
        if str(self.ui.Local_control.currentText()) == "Select...":
            message = message + "Select patient's Local Control. \n"
        if str(self.ui.Regional_Control.currentText()) == "Select...":
            message = message + "Select patient's Regional Control. \n"
        if str(self.ui.Distant_Control.currentText()) == "Select...":
            message = message + "Select patient's Distant Control. \n"
        if self.ui.Dt_local_failure.date() > QtCore.QDate.currentDate():
            message = message + "Patient's date of local failure cannot be " \
                                "in the future. \n "
        if self.ui.Dt_REgional_failure.date() > QtCore.QDate.currentDate():
            message = message + "Patient's date of regional failure cannot " \
                                "be in the future. \n "
        if self.ui.Dt_Distant_Failure.date() > QtCore.QDate.currentDate():
            message = message + "Patient's date of distant failure cannot " \
                                "be in the future. \n "

    # The following function performs the saving of the clinical data csv
    # in the directory

    # here handles the event of the button save being pressed
    def save_clinical_data(self):
        global message
        # performs validation
        self.form_validation()
        if len(message.strip()) == 0:
            # check if the CSV directory exists and if not create it
            if not os.path.isdir(os.path.join(str(self.path), 'CSV')):
                os.mkdir(os.path.join(str(self.path), 'CSV'))
            new_file = os.path.join(str(self.path),
                                    'CSV/ClinicalData_' + self.pID + '.csv')
            # open the file to save the clinical data in
            csv_file = open(new_file, 'w', newline='')
            # The headers of the file
            column_names = ['PatientID', 'Gender', 'Country_of_Birth',
                            'AgeAtDiagnosis', 'DxYear', 'Histology', 'ICD10',
                            'T_Stage',
                            'N_Stage', 'M_Stage', 'OverallStage', 'Tx_Intent',
                            'Surgery', 'Rad', 'Chemo',
                            'Immuno', 'Brachy', 'Hormone', 'Death',
                            'cancer_death',
                            'Survival_Duration', 'LocalControl',
                            'DateOfLocalFailure', 'LC_Duration',
                            'RegionalControl', 'DateOfRegionalFailure',
                            'RC_Duration', 'DistantControl',
                            'DateOfDistantFailure', 'DC_Duration']

            # get the cancer death option and if alive leave empty
            cancer_death = ''
            status = self.ui.Death.currentText()
            if status == "Dead":
                cancer_death = str(self.ui.Cancer_death.currentText())

            # get the age of the patient
            age_at_diagnosis = round(float(calculate_years(
                self.ui.date_of_birth.date(), self.ui.date_diagnosis.date())))

            # get the local failure duration
            local_failure = str(self.ui.Local_control.currentText())
            if local_failure == "Control":
                lc_duration = str(calculate_years(
                    self.ui.date_diagnosis.date(),
                    self.ui.Dt_Last_Existence.date()))
                lc_date = ''
            elif local_failure == "Failure":
                lc_duration = str(calculate_years(
                    self.ui.date_diagnosis.date(),
                    self.ui.Dt_local_failure.date()))
                lc_date = self.ui.Dt_local_failure.date().toString(
                    "dd/MM/yyyy")

            # get the regional failure duration
            regional_failure = str(self.ui.Regional_Control.currentText())
            if regional_failure == "Control":
                rc_duration = str(calculate_years(
                    self.ui.date_diagnosis.date(),
                    self.ui.Dt_Last_Existence.date()))
                rc_date = ''
            elif regional_failure == "Failure":
                rc_duration = str(calculate_years(
                    self.ui.date_diagnosis.date(),
                    self.ui.Dt_REgional_failure.date()))
                rc_date = self.ui.Dt_REgional_failure.date().toString(
                    "dd/MM/yyyy")

            # get the distant failure duration
            distant_failure = str(self.ui.Distant_Control.currentText())
            if distant_failure == "Control":
                dc_duration = str(calculate_years(
                    self.ui.date_diagnosis.date(),
                    self.ui.Dt_Last_Existence.date()))
                dc_date = ''
            elif distant_failure == "Failure":
                dc_duration = str(calculate_years(
                    self.ui.date_diagnosis.date(),
                    self.ui.Dt_Distant_Failure.date()))
                dc_date = self.ui.Dt_Distant_Failure.date().toString(
                    "dd/MM/yyyy")

            # get the survival duration
            survival_years = str(calculate_years(
                self.ui.date_diagnosis.date(),
                self.ui.Dt_Last_Existence.date()))

            # the data array to be entered in the file
            data_row = [self.pID, self.ui.gender.currentText(),
                        self.ui.line_BP.text(),
                        age_at_diagnosis, self.ui.date_diagnosis.date().year(),
                        self.get_desease_code(self.ui.line_histology.text(
                        )), self.get_desease_code(self.ui.line_icd.text()),
                        self.ui.T_stage.currentText(),
                        self.ui.N_stage.currentText(),
                        self.ui.M_stage.currentText(),
                        self.ui.Overall_Stage.currentText(),
                        self.ui.Tx_intent.currentText(),
                        self.get_code(self.ui.Surgery.currentText()),
                        self.get_code(self.ui.Rad.currentText()),
                        self.get_code(self.ui.Chemo.currentText()),
                        self.get_code(
                            self.ui.Immuno.currentText()),
                        self.get_code(self.ui.Brachy.currentText()),
                        self.get_code(self.ui.Hormone.currentText()),
                        self.code_alive(
                            self.ui.Death.currentText()),
                        self.code_cancer_death(cancer_death), survival_years,
                        self.code_control(self.ui.Local_control.currentText()),
                        lc_date,
                        lc_duration, self.code_control(
                    self.ui.Regional_Control.currentText()),
                        rc_date, rc_duration,
                        self.code_control(
                            self.ui.Distant_Control.currentText()), dc_date,
                        dc_duration]

            # Insert the header array and data array into the file
            with csv_file:
                writer = csv.writer(csv_file)
                writer.writerow(column_names)
                writer.writerow(data_row)

            # save the dates in binary file with patient ID, for future editing
            file_name = Path(resource_path('data/records.pkl'))
            df = pd.DataFrame(columns=['PID', 'DOB', 'DOD', 'DOLE'])
            dt = [self.pID,
                  self.ui.date_of_birth.date().toString("dd/MM/yyyy"),
                  self.ui.date_diagnosis.date().toString("dd/MM/yyyy"),
                  self.ui.Dt_Last_Existence.date().toString("dd/MM/yyyy")]
            df.loc[0] = dt
            # check if the file is already created
            if file_name.exists():
                # Check to see if this patient has had a record saved in
                # this file before
                new_df = pd.read_pickle(resource_path('data/records.pkl'))
                check = False
                for i in new_df.index:
                    if new_df.at[i, 'PID'] == self.pID:
                        # get the new records
                        new_df.at[
                            i, 'DOB'] = self.ui.date_of_birth.date().toString(
                            "dd/MM/yyyy")
                        new_df.at[
                            i, 'DOD'] = self.ui.date_diagnosis.date().toString(
                            "dd/MM/yyyy")
                        new_df.at[
                            i, 'DOLE'] = self.ui.Dt_Last_Existence.date(). \
                            toString("dd/MM/yyyy")
                        check = True

                if check:
                    # save under the same PID
                    new_df.append(df, ignore_index=True)
                    new_df.to_pickle(resource_path('data/records.pkl'))
            else:
                # save new row of credentials
                open(resource_path('data/records.pkl', 'w+'))
                df.to_pickle(resource_path('data/records.pkl'))
            # display the successful saving message pop up
            save_reply = QtWidgets.QMessageBox.information(
                self, "Message",
                "The Clinical Data was saved successfully in your directory!",
                QtWidgets.QMessageBox.Ok)
            if save_reply == QtWidgets.QMessageBox.Ok:
                # when they press okay on the pop up, display the clinical
                # data entries
                self.display_cd_dat()

        else:
            # the form did not pass the validation so display the
            # corresponding errors to be fixed, no csv created
            button_reply = QtWidgets.QMessageBox.warning(
                self, "Error Message",
                "The following issues need to be addressed: \n" + message,
                QtWidgets.QMessageBox.Ok)
            if button_reply == QtWidgets.QMessageBox.Ok:
                message = ""
                pass

    # After saving the clinical data is displayed
    def display_cd_dat(self):
        self.tab_cd = ClinicalDataDisplay(self.tabWindow, self.path,
                                          self.dataset, self.filenames)
        current_index = self.tabWindow.currentIndex()
        self.tabWindow.removeTab(current_index)
        self.tabWindow.addTab(self.tab_cd, "Clinical Data")
        self.tabWindow.setCurrentIndex(current_index)

    # The following functions are used when the form is in editing mode of
    # the clinical data

    # reads the information from the csv
    def load_data(self, filename):
        with open(filename, 'rt') as f:
            data = csv.reader(f)
            cd = list(data)
            cd.pop(0)
            li = []
            for i in cd[0]:
                li.append(i)
            return li

    # get code for Surgery/Rad/Chemo/Immuno/Btrachy/Hormone
    def get_code_reverse(self, the_choice):
        if the_choice == "Pri":
            return "Primary (Pri)"
        elif the_choice == "Ref":
            return "Refused (Ref)"
        elif the_choice == "Den":
            return "Denied (Den)"
        elif the_choice == "Die":
            return "DiedB4 (Die)"
        elif the_choice == "Neo":
            return "Neoadjuvant (Neo)"
        elif the_choice == "Con":
            return "Concurrent (Con)"
        elif the_choice == "Adj":
            return "Adjuvant (Adj)"
        else:
            return the_choice

    # get the desease name based on the code in the csv
    def completerFill(self, type, code):
        if type == 0:  # hist
            result = [i for i in new_hist if i.startswith(code)]
            return result[0]
        elif type == 1:  # icd
            result = [i for i in new_icd if i.startswith(code)]
            return result[0]

    # This function alters the form UI and enters the corresponding data in
    # the specific fields
    def editing_mode(self):
        # add the sensitive data of dates from the binary file
        # date of birth
        # date of diagnosis
        # date of last existence
        # Create a dtype with the binary data format and the desired column
        # names
        df = pd.read_pickle(resource_path('data/records.pkl'))
        for i in df.index:
            if df.at[i, 'PID'] == self.pID:
                self.ui.date_of_birth.setDate(
                    QtCore.QDate.fromString(df.at[i, 'DOB'], "dd/MM/yyyy"))
                self.ui.date_diagnosis.setDate(
                    QtCore.QDate.fromString(df.at[i, 'DOD'], "dd/MM/yyyy"))
                self.ui.Dt_Last_Existence.setDate(
                    QtCore.QDate.fromString(df.at[i, 'DOLE'], "dd/MM/yyyy"))
        # read the clinical data
        reg = '/CSV/ClinicalData*[.csv]'
        pathcd = glob.glob(self.path + reg)
        clinical_data = self.load_data(pathcd[0])
        self.ui.note.setText(
            "You are editing the last known Clinical Data for this patient.")
        self.ui.line_FN.setVisible(False)
        self.ui.line_LN.setVisible(False)
        self.ui.line_FN.setText("...")
        self.ui.line_LN.setText("...")
        self.ui.date_of_birth.setVisible(False)
        self.ui.gender.setCurrentIndex(self.ui.gender.findText(
            clinical_data[1], QtCore.Qt.MatchFixedString))
        self.ui.line_BP.setText(clinical_data[2])
        self.ui.line_histology.setText(self.completerFill(0, clinical_data[5]))
        self.ui.line_icd.setText(self.completerFill(1, clinical_data[6]))
        self.ui.T_stage.setCurrentIndex(self.ui.T_stage.findText(
            clinical_data[7], QtCore.Qt.MatchFixedString))
        self.ui.N_stage.setCurrentText(clinical_data[8])
        self.ui.M_stage.setCurrentText(clinical_data[9])
        self.ui.Overall_Stage.setCurrentText(clinical_data[10])
        self.ui.Tx_intent.setCurrentText(clinical_data[11])
        if clinical_data[11] == "Refused":
            self.tx_intent_refused()
        else:
            self.ui.Surgery.setCurrentText(
                self.get_code_reverse(clinical_data[12]))
            self.ui.Rad.setCurrentText(
                self.get_code_reverse(clinical_data[13]))
            self.ui.Chemo.setCurrentText(
                self.get_code_reverse(clinical_data[14]))
            self.ui.Immuno.setCurrentText(
                self.get_code_reverse(clinical_data[15]))
            self.ui.Brachy.setCurrentText(
                self.get_code_reverse(clinical_data[16]))
            self.ui.Hormone.setCurrentText(
                self.get_code_reverse(clinical_data[17]))

        self.ui.Death.setCurrentIndex(int(int(clinical_data[18]) + 1))
        if int(clinical_data[18]) == 0:
            self.ui.Cancer_death.setCurrentIndex(0)
            self.ui.Cancer_death.setDisabled(True)
        else:
            self.ui.Cancer_death.setCurrentText(
                str(int(clinical_data[19]) + 1))
        self.ui.Survival_dt.setText("Survival Length: " + clinical_data[20])
        self.ui.Survival_dt.setVisible(True)
        self.ui.Local_control.setCurrentIndex(int(1 + int(clinical_data[21])))
        if clinical_data[22] == '':
            self.ui.Dt_local_failure.setDate(
                QtCore.QDate.fromString('01/01/1900', "dd/MM/yyyy"))
        else:
            self.ui.Dt_local_failure.setDate(
                QtCore.QDate.fromString(clinical_data[22], "dd/MM/yyyy"))
        self.ui.Regional_Control.setCurrentIndex(
            int(1 + int(clinical_data[24])))
        if clinical_data[25] == '':
            self.ui.Dt_REgional_failure.setDate(
                QtCore.QDate.fromString('01/01/1900', "dd/MM/yyyy"))
        else:
            self.ui.Dt_REgional_failure.setDate(
                QtCore.QDate.fromString(clinical_data[25], "dd/MM/yyyy"))
        self.ui.Distant_Control.setCurrentIndex(
            int(1 + int(clinical_data[27])))
        if clinical_data[28] == '':
            self.ui.Dt_Distant_Failure.setDate(
                QtCore.QDate.fromString('01/01/1900', "dd/MM/yyyy"))
        else:
            self.ui.Dt_Distant_Failure.setDate(
                QtCore.QDate.fromString(clinical_data[28], "dd/MM/yyyy"))

    # the following function anable the Enter keyboard button to act as an
    # activator of the button save
    def on_click(self):
        self.save_clinical_data()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Return:
            self.on_click()


#   This Class handles the Clinical Data display of information from a csv file

class ClinicalDataDisplay(QtWidgets.QWidget, Ui_CD_Display):
    open_patient_window = QtCore.Signal(str)

    # Initialisation function of the display of the clinical data of the
    # patient
    def __init__(self, tab_window, path, ds, fn):
        QtWidgets.QWidget.__init__(self)

        self.path = path
        self.tabWindow = tab_window
        self.dataset = ds
        self.filenames = fn
        self.ui = Ui_CD_Display()
        self.ui.setupUi(self)
        self.load_cd()
        self.ui.Edit_button.clicked.connect(self.on_click)

    # the following function enables the Enter keyboard button to act as an
    # activator of the button edit
    def on_click(self):
        self.edit_mode()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Return:
            self.on_click()

    # This function will load the data from the csv into the software and make
    # it uneditable as it is only for display

    def load_cd(self):
        reg = '/CSV/ClinicalData*[.csv]'
        pathcd = glob.glob(self.path + reg)
        clinical_data = self.load_data(pathcd[0])

        self.ui.gender.setCurrentIndex(self.ui.gender.findText(
            clinical_data[1], QtCore.Qt.MatchFixedString))
        self.ui.gender.setDisabled(True)
        self.ui.line_BP.setText(clinical_data[2])
        self.ui.line_BP.setDisabled(True)
        self.ui.age_at_diagnosis.setText(clinical_data[3])
        self.ui.age_at_diagnosis.setDisabled(True)
        self.ui.line_Dx_Year.setText(clinical_data[4])
        self.ui.line_Dx_Year.setDisabled(True)
        self.ui.line_histology.setText(
            self.completer_fill(0, clinical_data[5]))
        self.ui.line_histology.setDisabled(True)
        self.ui.line_icd.setText(self.completer_fill(1, clinical_data[6]))
        self.ui.line_icd.setDisabled(True)
        self.ui.T_stage.setCurrentIndex(self.ui.T_stage.findText(
            clinical_data[7], QtCore.Qt.MatchFixedString))
        self.ui.T_stage.setDisabled(True)
        self.ui.N_stage.setCurrentText(clinical_data[8])
        self.ui.N_stage.setDisabled(True)
        self.ui.M_stage.setCurrentText(clinical_data[9])
        self.ui.M_stage.setDisabled(True)
        self.ui.Overall_Stage.setCurrentText(clinical_data[10])
        self.ui.Overall_Stage.setDisabled(True)
        self.ui.Tx_intent.setCurrentText(clinical_data[11])
        self.ui.Tx_intent.setDisabled(True)
        self.ui.Surgery.setCurrentText(self.get_code(clinical_data[12]))
        self.ui.Surgery.setDisabled(True)
        self.ui.Rad.setCurrentText(self.get_code(clinical_data[13]))
        self.ui.Rad.setDisabled(True)
        self.ui.Chemo.setCurrentText(self.get_code(clinical_data[14]))
        self.ui.Chemo.setDisabled(True)
        self.ui.Immuno.setCurrentText(self.get_code(clinical_data[15]))
        self.ui.Immuno.setDisabled(True)
        self.ui.Brachy.setCurrentText(self.get_code(clinical_data[16]))
        self.ui.Brachy.setDisabled(True)
        self.ui.Hormone.setCurrentText(self.get_code(clinical_data[17]))
        self.ui.Hormone.setDisabled(True)
        self.ui.Death.setCurrentIndex(int(1 + int(clinical_data[18])))
        self.ui.Death.setDisabled(True)
        if int(clinical_data[18]) == 0:
            self.ui.Cancer_death.setCurrentIndex(-1)
        else:
            self.ui.Cancer_death.setCurrentIndex(
                int(1 + int(clinical_data[19])))
        self.ui.Cancer_death.setDisabled(True)
        self.ui.survival_duration.setText(clinical_data[20])
        self.ui.survival_duration.setDisabled(True)
        self.ui.Local_control.setCurrentIndex(int(1 + int(clinical_data[21])))
        self.ui.Local_control.setDisabled(True)
        if clinical_data[22] == '':
            self.ui.Dt_local_failure.setDate(
                QtCore.QDate.fromString('01/01/1900', "dd/MM/yyyy"))
        else:
            self.ui.Dt_local_failure.setDate(
                QtCore.QDate.fromString(clinical_data[22], "dd/MM/yyyy"))
        self.ui.LC_duration.setText(clinical_data[23])
        self.ui.LC_duration.setDisabled(True)
        self.ui.Regional_Control.setCurrentIndex(
            int(1 + int(clinical_data[24])))
        self.ui.Regional_Control.setDisabled(True)
        if clinical_data[25] == '':
            self.ui.Dt_REgional_failure.setDate(
                QtCore.QDate.fromString('01/01/1900', "dd/MM/yyyy"))
        else:
            self.ui.Dt_REgional_failure.setDate(
                QtCore.QDate.fromString(clinical_data[25], "dd/MM/yyyy"))
        self.ui.RC_duration.setText(clinical_data[26])
        self.ui.RC_duration.setDisabled(True)
        self.ui.Distant_Control.setCurrentIndex(
            int(1 + int(clinical_data[27])))
        self.ui.Distant_Control.setDisabled(True)
        if clinical_data[28] == '':
            self.ui.Dt_Distant_Failure.setDate(
                QtCore.QDate.fromString('01/01/1900', "dd/MM/yyyy"))
        else:
            self.ui.Dt_Distant_Failure.setDate(
                QtCore.QDate.fromString(clinical_data[28], "dd/MM/yyyy"))
        self.ui.DC_duration.setText(clinical_data[29])
        self.ui.DC_duration.setDisabled(True)

    # this function get the data from the csv into a list
    def load_data(self, filename):
        with open(filename, 'rt') as f:
            data = csv.reader(f)
            cd = list(data)
            cd.pop(0)
            li = []
            for i in cd[0]:
                li.append(i)
            return li

    # this function converts the code into a full name desease
    def completer_fill(self, code_type, code):
        if code_type == 0:  # hist
            result = [i for i in new_hist if i.startswith(code)]
            return result[0]
        elif code_type == 1:  # icd
            result = [i for i in new_icd if i.startswith(code)]
            return result[0]

    # get code for Surgery/Rad/Chemo/Immuno/Btrachy/Hormone
    def get_code(self, the_choice):
        if the_choice == "Pri":
            return "Primary (Pri)"
        elif the_choice == "Ref":
            return "Refused (Ref)"
        elif the_choice == "Den":
            return "Denied (Den)"
        elif the_choice == "Die":
            return "DiedB4 (Die)"
        elif the_choice == "Neo":
            return "Neoadjuvant (Neo)"
        elif the_choice == "Con":
            return "Concurrent (Con)"
        elif the_choice == "Adj":
            return "Adjuvant (Adj)"
        else:
            return the_choice

    # call edit mode when the edit button is pressed
    def edit_mode(self):
        # check if the sensitive data is saved to enable editing
        if os.path.exists(resource_path('data/records.pkl')):
            df = pd.read_pickle(resource_path('data/records.pkl'))
            check = False
            for i in df.index:
                if df.at[i, 'PID'] == self.dataset[0].PatientID:
                    check = True
            if not check:
                # the sensitive data for this patient is missing so no
                # editing can be performed
                button_reply = QtWidgets.QMessageBox.warning(
                    self,
                    "Error Message",
                    "The software has no previous records of this patient.\n"
                    "If you wish, you can create a new clinical data file by "
                    "\ndeleting the current one from the directory and "
                    "reloading \nthe patient files.",
                    QtWidgets.QMessageBox.Ok)
                if button_reply == QtWidgets.QMessageBox.Ok:
                    pass
            else:
                self.tab_cd = ClinicalDataForm(self.tabWindow, self.path,
                                               self.dataset, self.filenames)
                self.tab_cd.editing_mode()
                currentIndex = self.tabWindow.currentIndex()
                self.tabWindow.removeTab(currentIndex)
                self.tabWindow.addTab(self.tab_cd, "Clinical Data")
                self.tabWindow.setCurrentIndex(currentIndex)
        else:
            # the sensitive data file is missing so no editing can be performed
            button_reply = QtWidgets.QMessageBox.warning(
                self, "Error Message",
                "The software has no previous records of this patient.\n"
                "If you wish, you can create a new clinical data file by \n"
                "deleting the current one from the directory and reloading \n"
                "the patient files.",
                QtWidgets.QMessageBox.Ok)
            if button_reply == QtWidgets.QMessageBox.Ok:
                pass


# This Class handles the Transect functionality


class Transect(QtWidgets.QGraphicsScene):

    # Initialisation function  of the class
    def __init__(self, main_window, image_to_paint, dataset, row_s, col_s,
                 tab_window, is_roi_draw=False):
        super(Transect, self).__init__()

        # create the canvas to draw the line on and all its necessary
        # components
        self.addItem(QtWidgets.QGraphicsPixmapItem(image_to_paint))
        self.img = image_to_paint
        self.values = []
        self.distances = []
        self.data = dataset
        self.pix_spacing = row_s / col_s
        self._start = QtCore.QPointF()
        self.drawing = True
        self._current_rect_item = None
        self.pos1 = QtCore.QPoint()
        self.pos2 = QtCore.QPoint()
        self.points = []
        self.roi_values = []
        self.roi_list = []
        self.is_ROI_draw = is_roi_draw
        self.tabWindow = tab_window
        self.mainWindow = main_window
        self._figure, self._axes, self._line = None, None, None
        self.leftLine, self.rightLine = None, None
        self._dragging_point = None
        self._points = {}
        self._valueTuples = {}
        self.thresholds = [4, 10]
        self.upper_limit = None
        self.lower_limit = None

    # This function starts the line draw when the mouse is pressed into the
    # 2D view of the scan
    def mousePressEvent(self, event):
        # Clear the current transect first
        plt1.close()
        # If is the first time we can draw as we want a line per button press
        if self.drawing:
            self.pos1 = event.scenePos()
            self._current_rect_item = QtWidgets.QGraphicsLineItem()
            pen = QtGui.QPen(QtGui.QColor("red"))
            self._current_rect_item.setPen(pen)
            self._current_rect_item.setFlag(
                QtWidgets.QGraphicsItem.ItemIsMovable, False)
            self.addItem(self._current_rect_item)
            self._start = event.scenePos()
            r = QtCore.QLineF(self._start, self._start)
            self._current_rect_item.setLine(r)

        # Second time generate mouse position

    # This function tracks the mouse and draws the line from the original
    # press point
    def mouseMoveEvent(self, event):
        if self._current_rect_item is not None and self.drawing:
            r = QtCore.QLineF(self._start, event.scenePos())
            self._current_rect_item.setLine(r)

    # This function terminates the line drawing and initiates the plot
    def mouseReleaseEvent(self, event):
        if self.drawing:
            self.pos2 = event.scenePos()
            # If a user just clicked one position
            if self.pos1.x() == self.pos2.x() \
                    and self.pos1.y() == self.pos2.y():
                self.drawing = False
            else:
                self.draw_dda(round(self.pos1.x()), round(self.pos1.y()),
                              round(self.pos2.x()), round(self.pos2.y()))
                self.drawing = False
                self.plot_result()
                self._current_rect_item = None

    # This function performs the DDA algorithm that locates all the points in
    # the drawn line
    def draw_dda(self, x1, y1, x2, y2):
        x, y = x1, y1
        length = abs(x2 - x1) if abs(x2 - x1) > abs(y2 - y1) else abs(y2 - y1)
        dx = (x2 - x1) / float(length)
        dy = (y2 - y1) / float(length)
        self.points.append((round(x), round(y)))

        for i in range(length):
            x += dx
            y += dy
            self.points.append((round(x), round(y)))

        # get the values of these points from the dataset
        self.get_values()
        # get their distances for the plot
        self.get_distances()

    # This function calculates the distance between two points
    def calculate_distance(self, x1, y1, x2, y2):
        dist = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        return dist

    # This function gets the corresponding values of all the points in the
    # drawn line from the dataset
    def get_values(self):
        for i, j in self.points:
            if i in range(constant.DEFAULT_WINDOW_SIZE) and j in range(constant.DEFAULT_WINDOW_SIZE):
                x, y = self.transect_linear_transform(i, j)
                self.values.append(self.data[x][y])

    # This function performs a linear transformation on the transect input if
    # the default window size != pixel size
    def transect_linear_transform(self, x, y):
        m_x = float(len(self.data))/constant.DEFAULT_WINDOW_SIZE
        m_y = float(len(self.data[0]))/constant.DEFAULT_WINDOW_SIZE
        return int(m_x*x), int(m_y*y)

    # Get the distance of each point from the end of the line
    def get_distances(self):
        for i, j in self.points:
            if i in range(constant.DEFAULT_WINDOW_SIZE) and j in range(constant.DEFAULT_WINDOW_SIZE):
                x, y = self.transect_linear_transform(i, j)
                x_2, y_2 = self.transect_linear_transform(
                    round(self.pos2.x()), round(self.pos2.y()))
                self.distances.append(self.calculate_distance(
                    x, y, x_2, y_2))
        self.distances.reverse()

    # This function handles the closing event of the transect graph
    def on_close(self, event):
        plt1.close()

        # returns the main page back to a non-drawing environment
        if self.is_ROI_draw:
            self.mainWindow.upper_limit = self.upper_limit
            self.mainWindow.lower_limit = self.lower_limit
            self.mainWindow.on_transect_close()
        else:
            self.mainWindow.dicom_single_view.update_view()
            self.mainWindow.dicom_axial_view.update_view()

        event.canvas.figure.axes[0].has_been_closed = True

    def find_limits(self, roi_values):
        self.upper_limit = roi_values[len(roi_values) - 1]
        self.lower_limit = roi_values[0]
        temp = 0
        if self.lower_limit > self.upper_limit:
            temp = self.upper_limit
            self.upper_limit = self.lower_limit
            self.lower_limit = temp

    def return_limits(self):
        return [self.lower_limit, self.upper_limit]

    # This function plots the Transect graph into a pop up window
    def plot_result(self):
        plt1.close('all')
        new_list = [(x * self.pix_spacing) for x in self.distances]
        self.thresholds[0] = new_list[1]
        self.thresholds[1] = new_list[len(new_list) - 1]
        self._points[self.thresholds[0]] = 0
        self._points[self.thresholds[1]] = 0
        self._figure = plt1.figure(num='Transect Graph')
        new_manager = self._figure.canvas.manager
        new_manager.canvas.figure = self._figure
        self._figure.set_canvas(new_manager.canvas)
        self._axes = self._figure.add_subplot(111)
        self._axes.has_been_closed = False
        # new list is axis x, self.values is axis y
        self._axes.step(new_list, self.values, where='mid')
        if self.is_ROI_draw:
            for x in range(len(new_list)):
                self._valueTuples[new_list[x]] = self.values[x]
            self.leftLine = self._axes.axvline(self.thresholds[0], color='r')
            self.rightLine = self._axes.axvline(self.thresholds[1], color='r')
            # Recalculate the distance and CT# to show ROI in histogram
            self.roi_list.clear()
            self.roi_values.clear()
            for x in range(len(new_list)):
                if self.thresholds[0] <= new_list[x] <= self.thresholds[1]:
                    self.roi_list.append(new_list[x])
                    self.roi_values.append(self._valueTuples[new_list[x]])

        plt1.xlabel('Distance mm')
        plt1.ylabel('CT #')
        plt1.grid(True)
        self._figure.canvas.mpl_connect('close_event', self.on_close)
        self._figure.canvas.mpl_connect('button_press_event', self._on_click)
        self._figure.canvas.mpl_connect('button_release_event',
                                        self._on_release)
        self._figure.canvas.mpl_connect('motion_notify_event', self._on_motion)
        self._update_plot()
        plt1.show()

    def _update_plot(self):
        if self.is_ROI_draw:
            if not self._points:
                self._line.set_data([], [])
            else:
                x, y = zip(*sorted(self._points.items()))
                # Add new plot
                if not self._line:
                    self._line, = self._axes.plot(x, y, "b", marker="o",
                                                  markersize=10)
                # Update current plot
                else:
                    self._line.set_data(x, y)
                if len(x) >= 2:
                    self.leftLine.set_xdata(x[0])
                    self.rightLine.set_xdata(x[1])
                    self.thresholds[0] = x[0]
                    self.thresholds[1] = x[1]

                for i in self._axes.bar(self.distances, self.values):
                    i.set_color('white')
                for x in range(len(self.distances)):
                    self._valueTuples[self.distances[x]] = self.values[x]
                # Recalculate the distance and CT# to show ROI in histogram
                self.roi_list.clear()
                self.roi_values.clear()
                for x in range(len(self.distances)):
                    if self.thresholds[0] <= self.distances[x] \
                            <= self.thresholds[1]:
                        self.roi_list.append(self.distances[x])
                        self.roi_values.append(
                            self._valueTuples[self.distances[x]])
                self.find_limits(self.roi_values)
            self._figure.canvas.draw()

    def _add_point(self, x, y=None):
        if self.is_ROI_draw:
            if isinstance(x, MouseEvent):
                x = int(x.xdata)
            self._points[x] = 0
            return x, 0

    def _remove_point(self, x, _):
        if self.is_ROI_draw:
            if x in self._points:
                self._points.pop(x)

    def _find_neighbor_point(self, event):
        u""" Find point around mouse position

        :rtype: ((int, int)|None)
        :return: (x, y) if there are any point around mouse else None
        """
        if self.is_ROI_draw:
            distance_threshold = 50.0
            nearest_point = None
            min_distance = math.sqrt(2 * (100 ** 2))
            for x, y in self._points.items():
                distance = math.hypot(event.xdata - x, event.ydata - y)
                if distance < min_distance:
                    min_distance = distance
                    nearest_point = (x, y)
            if min_distance < distance_threshold:
                return nearest_point
            return None

    def _on_click(self, event):
        u""" callback method for mouse click event

        :type event: MouseEvent
        """
        if self.is_ROI_draw:
            # left click
            if event.button == 1 and event.inaxes in [self._axes]:
                point = self._find_neighbor_point(event)
                if point:
                    self._dragging_point = point
                self._update_plot()

    def _on_release(self, event):
        u""" callback method for mouse release event

        :type event: MouseEvent
        """
        if self.is_ROI_draw:
            if event.button == 1 \
                    and event.inaxes in [self._axes] \
                    and self._dragging_point:
                self._dragging_point = None
                self._update_plot()

    def _on_motion(self, event):
        u""" callback method for mouse motion event

        :type event: MouseEvent
        """
        if self.is_ROI_draw:
            if not self._dragging_point:
                return
            if event.xdata is None or event.ydata is None:
                return
            self._remove_point(*self._dragging_point)
            self._dragging_point = self._add_point(event)
            self._update_plot()


# This is the main page Controller class that handles all the activity
# in the main page

class MainPageCallClass:

    # Initialisation function of the controller
    def __init__(self):
        self.patient_dict_container = PatientDictContainer()

    # This function runs Anonymization on button click
    def run_anonymization(self, raw_dvh):
        path = self.patient_dict_container.path
        dataset = self.patient_dict_container.dataset
        filepaths = self.patient_dict_container.filepaths
        target_path = anonymize(path, dataset, filepaths, raw_dvh)
        return target_path

    # This function displays the clinical data form
    def display_cd_form(self, tab_window, file_path):
        dataset = self.patient_dict_container.dataset
        filepaths = self.patient_dict_container.filepaths
        self.tab_cd = ClinicalDataForm(tab_window, file_path, dataset,
                                       filepaths)
        tab_window.addTab(self.tab_cd, "Clinical Data")

    # This function displays the clinical data entries in view mode
    def display_cd_dat(self, tab_window, file_path):
        dataset = self.patient_dict_container.dataset
        filepaths = self.patient_dict_container.filepaths
        self.tab_cd = ClinicalDataDisplay(tab_window, file_path, dataset,
                                          filepaths)
        tab_window.addTab(self.tab_cd, "Clinical Data")

    # This function runs Transect on button click
    def run_transect(self, main_window, tab_window, imageto_paint, dataset,
                     row_s, col_s, is_roi_draw=False):
        self.tab_ct = Transect(main_window, imageto_paint,
                               dataset, row_s, col_s, tab_window, is_roi_draw)
        tab_window.setScene(self.tab_ct)
