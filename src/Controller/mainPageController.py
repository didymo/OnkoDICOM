import matplotlib.cbook
from src.Model.ROI import *
from src.Model.CalculateImages import *
from src.Model.Anon import *
from dateutil.relativedelta import relativedelta
from pathlib import Path
from src.Model.GetPatientInfo import *
from src.Model.Display_CD_UI import *
from src.Model.form_UI import *
from src.Model.Pyradiomics import pyradiomics
from PyQt5.QtWidgets import QMessageBox
import math
from PyQt5.QtWidgets import QGraphicsPixmapItem
from PyQt5.QtCore import Qt, QPoint, QPointF, QRectF
import matplotlib.pyplot as plt1
import glob
import sys

import warnings
warnings.filterwarnings("ignore")


matplotlib.cbook.handle_exceptions = "print"  # default

matplotlib.cbook.handle_exceptions = "raise"
matplotlib.cbook.handle_exceptions = "ignore"


# matplotlib.cobook.handle_exceptions = my_logger  # will be called with exception as argument

######################################################
#               CLINICAL DATA CODE                   #
######################################################
message = ""

with open('src/data/ICD10_Topography.csv', 'r') as f:
    reader = csv.reader(f)
    icd = list(reader)
    icd.pop(0)
with open('src/data/ICD10_Topography_C.csv', 'r') as f:
    reader = csv.reader(f)
    icdc = list(reader)
    icdc.pop(0)
with open('src/data/ICD10_Morphology.csv', 'r') as f:
    reader = csv.reader(f)
    hist = list(reader)
    hist.pop(0)

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


def calculate_years(year1, year2):
    difference_years = relativedelta(year2.toPyDate(), year1.toPyDate()).years
    difference_months = relativedelta(
        year2.toPyDate(), year1.toPyDate()).months
    difference_in_days = relativedelta(year2.toPyDate(), year1.toPyDate()).days
    value = difference_years + \
        (difference_months / 12) + (difference_in_days / 365)
    return ("%.2f" % value)
    # return float(year2.year() - year1.year() - ((year2.month(), year2.day()) < (year1.month(), year1.day())))


class ClinicalDataForm(QtWidgets.QWidget, Ui_Form):
    open_patient_window = QtCore.pyqtSignal(str)

    def __init__(self, tabWindow, path, ds, fn):
        QtWidgets.QWidget.__init__(self)

        self.path = path
        self.dataset = ds
        self.filenames = fn
        self.pID = self.dataset[0].PatientID
        self.tabWindow = tabWindow
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        # setting tab order
        self.setTabOrder(self.ui.line_LN, self.ui.line_FN)
        self.setTabOrder(self.ui.line_FN, self.ui.date_of_birth)
        self.setTabOrder(self.ui.date_of_birth, self.ui.line_BP)
        self.setTabOrder(self.ui.line_BP, self.ui.dateEdit_2)
        self.setTabOrder(self.ui.dateEdit_2, self.ui.gender)
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
        self.setTabOrder(self.ui.Immuno, self.ui.Branchy)
        self.setTabOrder(self.ui.Branchy, self.ui.Hormone)
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

        self.ui.Local_control.activated.connect(self.LocalControl_Failure)
        self.ui.Regional_Control.activated.connect(
            self.RegionalControl_Failure)
        self.ui.Distant_Control.activated.connect(self.DistantControl_Failure)
        self.ui.Tx_intent.activated.connect(self.Tx_Intent_Refused)
        self.ui.Death.activated.connect(self.PatientDead)
        self.ui.Death.activated.connect(self.show_survival)
        self.ui.Save_button.clicked.connect(self.on_click)
        # self.ui.line_LN.setFocus(QtCore.Qt.TabFocusReason)

    # show survival
    def show_survival(self):
        Survival_years = str(calculate_years(
            self.ui.dateEdit_2.date(), self.ui.Dt_Last_Existence.date()))
        self.ui.Survival_dt.setText("Survival Length: " + Survival_years)
        self.ui.Survival_dt.setVisible(True)

    # check if patient is alive or not
    def PatientDead(self):
        status = str(self.ui.Death.currentText())
        if status == "Alive":
            self.ui.Cancer_death.setDisabled(True)
        else:
            self.ui.Cancer_death.setDisabled(False)

    # handles the case where Tx_intent is Refused
    def Tx_Intent_Refused(self):
        choice = str(self.ui.Tx_intent.currentText())
        if choice == 'Refused':
            self.ui.Surgery.setCurrentIndex(1)
            self.ui.Rad.setCurrentIndex(1)
            self.ui.Chemo.setCurrentIndex(1)
            self.ui.Immuno.setCurrentIndex(1)
            self.ui.Branchy.setCurrentIndex(1)
            self.ui.Hormone.setCurrentIndex(1)
            self.ui.Surgery.setDisabled(True)
            self.ui.Rad.setDisabled(True)
            self.ui.Chemo.setDisabled(True)
            self.ui.Immuno.setDisabled(True)
            self.ui.Branchy.setDisabled(True)
            self.ui.Hormone.setDisabled(True)
        elif choice != 'Refused':
            self.ui.Surgery.setDisabled(False)
            self.ui.Rad.setDisabled(False)
            self.ui.Chemo.setDisabled(False)
            self.ui.Immuno.setDisabled(False)
            self.ui.Branchy.setDisabled(False)
            self.ui.Hormone.setDisabled(False)
            self.ui.Surgery.setCurrentIndex(0)
            self.ui.Rad.setCurrentIndex(0)
            self.ui.Chemo.setCurrentIndex(0)
            self.ui.Immuno.setCurrentIndex(0)
            self.ui.Branchy.setCurrentIndex(0)
            self.ui.Hormone.setCurrentIndex(0)

    # get code for Surgery/Rad/Chemo/Immuno/Btrachy/Hormone
    def getCode(self, theChoice):
        if (theChoice == "Primary (Pri)"):
            return "Pri"
        elif (theChoice == "Refused (Ref)"):
            return "Ref"
        elif (theChoice == "Denied (Den)"):
            return "Den"
        elif (theChoice == "DiedB4 (Die)"):
            return "Die"
        elif (theChoice == "Neoadjuvant (Neo)"):
            return "Neo"
        elif (theChoice == "Concurrent (Con)"):
            return "Con"
        elif (theChoice == "Adjuvant (Adj)"):
            return "Adj"
        else:
            return theChoice

    def codeAlive(self, choice):
        if choice == "Alive":
            return 0
        else:
            return 1

    def codeControl(self, choice):
        if choice == "Control":
            return 0
        else:
            return 1

    def codeCancerDeath(self, choice):
        if choice == "Non-cancer death":
            return 0
        elif choice == "Cancer death":
            return 1
        else:
            return ""

    # handles the change in the date of local failure according on the option selected at the local failure combo box
    def LocalControl_Failure(self):
        local_failure = str(self.ui.Local_control.currentText())
        if (local_failure == "Control"):
            self.ui.Dt_local_failure.setDisabled(True)
        elif (local_failure == "Failure"):
            self.ui.Dt_local_failure.setDisabled(False)
            self.ui.Dt_local_failure.setReadOnly(False)
        elif (local_failure == "Select..."):
            self.ui.Dt_local_failure.setDisabled(True)

    # handles the change in date of regional failure according to the regional failure option selected
    def RegionalControl_Failure(self):
        regional_failure = str(self.ui.Regional_Control.currentText())
        if (regional_failure == "Control"):
            self.ui.Dt_REgional_failure.setDisabled(True)
        elif (regional_failure == "Failure"):
            self.ui.Dt_REgional_failure.setDisabled(False)
            self.ui.Dt_REgional_failure.setReadOnly(False)
        elif (regional_failure == "Select..."):
            self.ui.Dt_REgional_failure.setDisabled(True)

    # handles the change in date of distant failure according to the option chosen in distant control
    def DistantControl_Failure(self):
        distant_failure = str(self.ui.Distant_Control.currentText())
        if (distant_failure == "Control"):
            self.ui.Dt_Distant_Failure.setDisabled(True)
        elif (distant_failure == "Failure"):
            self.ui.Dt_Distant_Failure.setDisabled(False)
            self.ui.Dt_Distant_Failure.setReadOnly(False)
        elif (distant_failure == "Select..."):
            self.ui.Dt_Distant_Failure.setDisabled(True)

    def getDeseaseCode(self, string):
        return string[:string.index(" ")]

    # validating the data in the form
    def form_Validation(self):
        global message
        if (len(self.ui.line_LN.text()) == 0):
            message = message + "Input patient's last name. \n"
        if (len(self.ui.line_FN.text()) == 0):
            message = message + "Input patient's first name. \n"
        if (str(self.ui.gender.currentText()) == "Select..."):
            message = message + "Select patient's gender. \n"
        if (len(self.ui.line_BP.text()) == 0):
            message = message + "Input patient's birth place. \n"
        if (self.ui.date_of_birth.date() > QDate.currentDate()):
            message = message + "Patient's date of birth cannot be in the future. \n"
        if (self.ui.dateEdit_2.date() > QDate.currentDate()):
            message = message + "Patient's date of diagnosis cannot be in the future. \n"
        if (len(self.ui.line_icd.text()) == 0):
            message = message + "Input patient's ICD 10. \n"
        if (len(self.ui.line_histology.text()) == 0):
            message = message + "Input patient's Histology. \n"
        if (str(self.ui.T_stage.currentText()) == "Select..."):
            message = message + "Select patient's T Stage. \n"
        if (str(self.ui.N_stage.currentText()) == "Select..."):
            message = message + "Select patient's N Stage. \n"
        if (str(self.ui.M_stage.currentText()) == "Select..."):
            message = message + "Select patient's M Stage. \n"
        if (str(self.ui.Overall_Stage.currentText()) == "Select..."):
            message = message + "Select patient's Overall Stage. \n"
        if (str(self.ui.Tx_intent.currentText()) == "Select..."):
            message = message + "Select patient's Tx_Intent. \n"
        if (str(self.ui.Surgery.currentText()) == "Select..."):
            message = message + "Select patient's Surgery. \n"
        if (str(self.ui.Rad.currentText()) == "Select..."):
            message = message + "Select patient's Rad. \n"
        if (str(self.ui.Chemo.currentText()) == "Select..."):
            message = message + "Select patient's Chemo. \n"
        if (str(self.ui.Branchy.currentText()) == "Select..."):
            message = message + "Select patient's Brachy. \n"
        if (str(self.ui.Hormone.currentText()) == "Select..."):
            message = message + "Select patient's Hormone. \n"
        if (self.ui.Dt_Last_Existence.date() > QDate.currentDate()):
            message = message + "Patient's date of last existence cannot be in the future. \n"
        if (str(self.ui.Death.currentText()) == "Select..."):
            message = message + "Select patient's Death. \n"
        if ((str(self.ui.Cancer_death.currentText()) == "Select...") and (str(self.ui.Death.currentText()) == "Dead")):
            message = message + "Select patient's Cancer Death. \n"
        if (str(self.ui.Local_control.currentText()) == "Select..."):
            message = message + "Select patient's Local Control. \n"
        if (str(self.ui.Regional_Control.currentText()) == "Select..."):
            message = message + "Select patient's Regional Control. \n"
        if (str(self.ui.Distant_Control.currentText()) == "Select..."):
            message = message + "Select patient's Distant Control. \n"
        if (self.ui.Dt_local_failure.date() > QDate.currentDate()):
            message = message + "Patient's date of local failure cannot be in the future. \n"
        if (self.ui.Dt_REgional_failure.date() > QDate.currentDate()):
            message = message + "Patient's date of regional failure cannot be in the future. \n"
        if (self.ui.Dt_Distant_Failure.date() > QDate.currentDate()):
            message = message + "Patient's date of distant failure cannot be in the future. \n"

    # here handles the event of the button save being pressed
    def save_ClinicalData(self):
        global message
        self.form_Validation()
        if (len(message.strip()) == 0):
            # write csv file...
            new_file = os.path.join(str(self.path), 'clinicaldata.csv')
            f = open(new_file, 'w')
            columnNames = ['MD5Hash', 'Gender', 'Country_of_Birth',
                           'AgeAtDiagnosis', 'DxYear', 'Histology', 'ICD10', 'T_Stage',
                           'N_Stage', 'M_Stage', 'OverallStage', 'Tx_Intent', 'Surgery', 'Rad', 'Chemo',
                           'Immuno', 'Brachy', 'Hormone', 'Death', 'CancerDeath',
                           'Survival_Duration', 'LocalControl', 'DateOfLocalFailure', 'LC_Duration',
                           'RegionalControl', 'DateOfRegionalFailure', 'RC_Duration', 'DistantControl',
                           'DateOfDistantFailure', 'DC_Duration']
            CancerDeath = ''
            status = self.ui.Death.currentText()
            if status == "Dead":
                CancerDeath = str(self.ui.Cancer_death.currentText())

            ageAtDiagnosis = round(float(calculate_years(
                self.ui.date_of_birth.date(), self.ui.dateEdit_2.date())))

            # get the local failure duration
            local_failure = str(self.ui.Local_control.currentText())
            if (local_failure == "Control"):
                Lc_duration = str(calculate_years(
                    self.ui.dateEdit_2.date(), self.ui.Dt_Last_Existence.date()))
                Lc_date = ''
            elif (local_failure == "Failure"):
                Lc_duration = str(calculate_years(
                    self.ui.dateEdit_2.date(), self.ui.Dt_local_failure.date()))
                Lc_date = self.ui.Dt_local_failure.date().toString("dd/MM/yyyy")

            # get the regional failure duration
            regional_failure = str(self.ui.Regional_Control.currentText())
            if (regional_failure == "Control"):
                Rc_Duration = str(calculate_years(
                    self.ui.dateEdit_2.date(), self.ui.Dt_Last_Existence.date()))
                Rc_date = ''
            elif (regional_failure == "Failure"):
                Rc_Duration = str(calculate_years(
                    self.ui.dateEdit_2.date(), self.ui.Dt_REgional_failure.date()))
                Rc_date = self.ui.Dt_REgional_failure.date().toString("dd/MM/yyyy")

            # get the sistant failure duration
            distant_failure = str(self.ui.Distant_Control.currentText())
            if (distant_failure == "Control"):
                Dc_Duration = str(calculate_years(
                    self.ui.dateEdit_2.date(), self.ui.Dt_Last_Existence.date()))
                Dc_date = ''
            elif (distant_failure == "Failure"):
                Dc_Duration = str(calculate_years(
                    self.ui.dateEdit_2.date(), self.ui.Dt_Distant_Failure.date()))
                Dc_date = self.ui.Dt_Distant_Failure.date().toString("dd/MM/yyyy")

            Survival_years = str(calculate_years(
                self.ui.dateEdit_2.date(), self.ui.Dt_Last_Existence.date()))

            dataRow = [self.pID, self.ui.gender.currentText(), self.ui.line_BP.text(),
                       ageAtDiagnosis, self.ui.dateEdit_2.date().year(),
                       self.getDeseaseCode(self.ui.line_histology.text(
                       )), self.getDeseaseCode(self.ui.line_icd.text()),
                       self.ui.T_stage.currentText(),
                       self.ui.N_stage.currentText(), self.ui.M_stage.currentText(),
                       self.ui.Overall_Stage.currentText(),
                       self.ui.Tx_intent.currentText(), self.getCode(self.ui.Surgery.currentText()),
                       self.getCode(self.ui.Rad.currentText()),
                       self.getCode(self.ui.Chemo.currentText()), self.getCode(
                           self.ui.Immuno.currentText()),
                       self.getCode(self.ui.Branchy.currentText()),
                       self.getCode(self.ui.Hormone.currentText()), self.codeAlive(
                           self.ui.Death.currentText()),
                       self.codeCancerDeath(CancerDeath), Survival_years,
                       self.codeControl(self.ui.Local_control.currentText()),
                       Lc_date,
                       Lc_duration, self.codeControl(
                           self.ui.Regional_Control.currentText()),
                       Rc_date, Rc_Duration,
                       self.codeControl(
                           self.ui.Distant_Control.currentText()), Dc_date,
                       Dc_Duration]

            with f:
                writer = csv.writer(f)
                writer.writerow(columnNames)
                writer.writerow(dataRow)

            # save the dates in binary file with patient ID/MDHash5
            fileName = Path('src/data/records.pkl')
            df = pd.DataFrame(columns=['PID', 'DOB', 'DOD', 'DOLE'])
            dt = [self.pID, self.ui.date_of_birth.date().toString("dd/MM/yyyy"),
                  self.ui.dateEdit_2.date().toString("dd/MM/yyyy"),
                  self.ui.Dt_Last_Existence.date().toString("dd/MM/yyyy")]
            df.loc[0] = dt
            if fileName.exists():

                new_df = pd.read_pickle('src/data/records.pkl')
                check = False
                for i in new_df.index:
                    if new_df.at[i, 'PID'] == self.pID:
                        new_df.at[i, 'DOB'] = self.ui.date_of_birth.date().toString(
                            "dd/MM/yyyy")
                        new_df.at[i, 'DOD'] = self.ui.dateEdit_2.date().toString(
                            "dd/MM/yyyy")
                        new_df.at[i, 'DOLE'] = self.ui.Dt_Last_Existence.date().toString(
                            "dd/MM/yyyy")
                        check = True

                if check:
                    new_df.append(df, ignore_index=True)
                    new_df.to_pickle('src/data/records.pkl')
            else:
                open('src/data/records.pkl', 'w+')
                df.to_pickle('src/data/records.pkl')

            SaveReply = QMessageBox.information(self, "Message",
                                                "The Clinical Data was saved successfully in your directory!",
                                                QMessageBox.Ok)
            if SaveReply == QMessageBox.Ok:
                self.display_cd_dat()

        else:
            buttonReply = QMessageBox.warning(self, "Error Message",
                                              "The following issues need to be addressed: \n" + message, QMessageBox.Ok)
            if buttonReply == QMessageBox.Ok:
                message = ""
                pass

    def display_cd_dat(self):
        self.tab_cd = ClinicalDataDisplay(self.tabWindow, self.path)
        self.tabWindow.removeTab(3)
        self.tabWindow.addTab(self.tab_cd, "Clinical Data")
        self.tabWindow.setCurrentIndex(3)

    def load_Data(self, filename):
        with open(filename, 'rt')as f:
            data = csv.reader(f)
            cd = list(data)
            cd.pop(0)
            li = []
            for i in cd[0]:
                li.append(i)
            return li

        # get code for Surgery/Rad/Chemo/Immuno/Btrachy/Hormone

    def getCodeReverse(self, theChoice):
        if (theChoice == "Pri"):
            return "Primary (Pri)"
        elif (theChoice == "Ref"):
            return "Refused (Ref)"
        elif (theChoice == "Den"):
            return "Denied (Den)"
        elif (theChoice == "Die"):
            return "DiedB4 (Die)"
        elif (theChoice == "Neo"):
            return "Neoadjuvant (Neo)"
        elif (theChoice == "Con"):
            return "Concurrent (Con)"
        elif (theChoice == "Adj"):
            return "Adjuvant (Adj)"
        else:
            return theChoice

    def completerFill(self, type, code):
        if type == 0:  # hist
            result = [i for i in new_hist if i.startswith(code)]
            return result[0]
        elif type == 1:  # icd
            result = [i for i in new_icd if i.startswith(code)]
            return result[0]

    def editing_mode(self):
        reg = '/[clinicaldata]*[.csv]'
        pathcd = glob.glob(self.path + reg)
        clinical_data = self.load_Data(pathcd[0])

        self.ui.label_4.setText(
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
            self.Tx_Intent_Refused()
        else:
            self.ui.Surgery.setCurrentText(
                self.getCodeReverse(clinical_data[12]))
            self.ui.Rad.setCurrentText(self.getCodeReverse(clinical_data[13]))
            self.ui.Chemo.setCurrentText(
                self.getCodeReverse(clinical_data[14]))
            self.ui.Immuno.setCurrentText(
                self.getCodeReverse(clinical_data[15]))
            self.ui.Branchy.setCurrentText(
                self.getCodeReverse(clinical_data[16]))
            self.ui.Hormone.setCurrentText(
                self.getCodeReverse(clinical_data[17]))

        self.ui.Death.setCurrentIndex(int(int(clinical_data[18]) + 1))
        if clinical_data[19] == '':
            self.ui.Cancer_death.setCurrentIndex(0)
            self.ui.Cancer_death.setDisabled(True)
        else:
            self.ui.Cancer_death.setCurrentText(
                int(int(clinical_data[19]) + 1))
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

        # add the sensitive data of dates from the binary file
        # date of birth
        # date of diagnosis
        # date of last existence
        # Create a dtype with the binary data format and the desired column names
        df = pd.read_pickle('src/data/records.pkl')
        for i in df.index:
            if df.at[i, 'PID'] == self.pID:
                self.ui.date_of_birth.setDate(
                    QtCore.QDate.fromString(df.at[i, 'DOB'], "dd/MM/yyyy"))
                self.ui.dateEdit_2.setDate(
                    QtCore.QDate.fromString(df.at[i, 'DOD'], "dd/MM/yyyy"))
                self.ui.Dt_Last_Existence.setDate(
                    QtCore.QDate.fromString(df.at[i, 'DOLE'], "dd/MM/yyyy"))

    def on_click(self):
        self.save_ClinicalData()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Return:
            self.on_click()


class ClinicalDataDisplay(QtWidgets.QWidget, Ui_CD_Display):
    open_patient_window = QtCore.pyqtSignal(str)

    def __init__(self, tabWindow, path):
        QtWidgets.QWidget.__init__(self)

        self.path = path
        self.tabWindow = tabWindow
        self.ui = Ui_CD_Display()
        self.ui.setupUi(self)
        self.load_cd()
        self.ui.Edit_button.clicked.connect(self.on_click)

    def on_click(self):
        self.edit_mode()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Return:
            self.on_click()

    def load_cd(self):
        reg = '/[clinicaldata]*[.csv]'
        pathcd = glob.glob(self.path + reg)
        clinical_data = self.load_Data(pathcd[0])

        self.ui.gender.setCurrentIndex(self.ui.gender.findText(
            clinical_data[1], QtCore.Qt.MatchFixedString))
        self.ui.gender.setDisabled(True)
        self.ui.line_BP.setText(clinical_data[2])
        self.ui.line_BP.setDisabled(True)
        self.ui.age_at_diagnosis.setText(clinical_data[3])
        self.ui.age_at_diagnosis.setDisabled(True)
        self.ui.line_Dx_Year.setText(clinical_data[4])
        self.ui.line_Dx_Year.setDisabled(True)
        self.ui.line_histology.setText(self.completerFill(0, clinical_data[5]))
        self.ui.line_histology.setDisabled(True)
        self.ui.line_icd.setText(self.completerFill(1, clinical_data[6]))
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
        self.ui.Surgery.setCurrentText(self.getCode(clinical_data[12]))
        self.ui.Surgery.setDisabled(True)
        self.ui.Rad.setCurrentText(self.getCode(clinical_data[13]))
        self.ui.Rad.setDisabled(True)
        self.ui.Chemo.setCurrentText(self.getCode(clinical_data[14]))
        self.ui.Chemo.setDisabled(True)
        self.ui.Immuno.setCurrentText(self.getCode(clinical_data[15]))
        self.ui.Immuno.setDisabled(True)
        self.ui.Branchy.setCurrentText(self.getCode(clinical_data[16]))
        self.ui.Branchy.setDisabled(True)
        self.ui.Hormone.setCurrentText(self.getCode(clinical_data[17]))
        self.ui.Hormone.setDisabled(True)
        self.ui.Death.setCurrentIndex(int(1 + int(clinical_data[18])))
        self.ui.Death.setDisabled(True)
        if clinical_data[19] == '':
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

    def load_Data(self, filename):
        with open(filename, 'rt')as f:
            data = csv.reader(f)
            cd = list(data)
            cd.pop(0)
            li = []
            for i in cd[0]:
                li.append(i)
            return li

    def completerFill(self, type, code):
        if type == 0:  # hist
            result = [i for i in new_hist if i.startswith(code)]
            return result[0]
        elif type == 1:  # icd
            result = [i for i in new_icd if i.startswith(code)]
            return result[0]

    # get code for Surgery/Rad/Chemo/Immuno/Btrachy/Hormone
    def getCode(self, theChoice):
        if (theChoice == "Pri"):
            return "Primary (Pri)"
        elif (theChoice == "Ref"):
            return "Refused (Ref)"
        elif (theChoice == "Den"):
            return "Denied (Den)"
        elif (theChoice == "Die"):
            return "DiedB4 (Die)"
        elif (theChoice == "Neo"):
            return "Neoadjuvant (Neo)"
        elif (theChoice == "Con"):
            return "Concurrent (Con)"
        elif (theChoice == "Adj"):
            return "Adjuvant (Adj)"
        else:
            return theChoice

    def edit_mode(self):
        self.tab_cd = ClinicalDataForm(self.tabWindow, self.path)
        self.tab_cd.editing_mode()
        self.tabWindow.removeTab(3)
        self.tabWindow.addTab(self.tab_cd, "Clinical Data")
        self.tabWindow.setCurrentIndex(3)


######################################################
#             TRANSECT CLASS CODE                    #
######################################################

class Transect(QtWidgets.QGraphicsScene):
    def __init__(self, mainWindow, imagetoPaint, dataset, rowS, colS, tabWindow):
        super(Transect, self).__init__()

        self.addItem(QGraphicsPixmapItem(imagetoPaint))
        self.img = imagetoPaint
        self.values = []
        self.distances = []
        self.data = dataset
        self.pixSpacing = rowS / colS
        self._start = QPointF()
        self.drawing = True
        self._current_rect_item = None
        self.pos1 = QPoint()
        self.pos2 = QPoint()
        self.points = []
        self.tabWindow = tabWindow
        self.mainWindow = mainWindow

    def mousePressEvent(self, event):
        if self.drawing == True:
            self.pos1 = event.scenePos()
            self._current_rect_item = QtWidgets.QGraphicsLineItem()
            self._current_rect_item.setPen(QtCore.Qt.red)
            self._current_rect_item.setFlag(
                QtWidgets.QGraphicsItem.ItemIsMovable, False)
            self.addItem(self._current_rect_item)
            self._start = event.scenePos()
            r = QtCore.QLineF(self._start, self._start)
            self._current_rect_item.setLine(r)
        # super(Transect, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._current_rect_item is not None and self.drawing == True:
            r = QtCore.QLineF(self._start, event.scenePos())  # .normalized()
            self._current_rect_item.setLine(r)
        # super(Transect, self).mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.drawing == True:
            # print("pos1:", self.pos1.x(), self.pos1.y())
            self.pos2 = event.scenePos()
            # print("pos2:", self.pos2.x(), self.pos2.y())
            self.drawDDA(round(self.pos1.x()), round(self.pos1.y()),
                         round(self.pos2.x()), round(self.pos2.y()))
            # print(self.calculateDistance(round(self.pos1.x()), round(self.pos1.y()), round(self.pos2.x()), round(self.pos2.y())))

            self.drawing = False
            self.plotResult()
            self._current_rect_item = None
        # super(Transect, self).mouseReleaseEvent(event)

    def drawDDA(self, x1, y1, x2, y2):
        x, y = x1, y1
        length = abs(x2 - x1) if abs(x2 - x1) > abs(y2 - y1) else abs(y2 - y1)
        dx = (x2 - x1) / float(length)
        dy = (y2 - y1) / float(length)
        self.points.append((round(x), round(y)))

        for i in range(length):
            x += dx
            y += dy
            self.points.append((round(x), round(y)))
        # print(self.points)
        self.getValues()
        self.getDistances()

    def calculateDistance(self, x1, y1, x2, y2):
        dist = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        return dist

    def getValues(self):
        for i, j in self.points:
            if i in range(512) and j in range(512):
                self.values.append(self.data[i][j])

        # print(self.values)

    def getDistances(self):
        for i, j in self.points:
            if i in range(512) and j in range(512):
                self.distances.append(self.calculateDistance(
                    i, j, round(self.pos2.x()), round(self.pos2.y())))
        self.distances.reverse()
        # print(self.distances)

    def on_close(self, event):

        plt1.close()
        self.mainWindow.DICOM_image_display()
        self.mainWindow.updateText_View()
        self.tabWindow.setScene(self.mainWindow.DICOM_image_scene)
        event.canvas.figure.axes[0].has_been_closed = True

    def plotResult(self):
        plt1.close('all')
        newList = [(x * self.pixSpacing) for x in self.distances]
        # adding a dummy manager
        fig1 = plt1.figure(num='Transect Graph')
        new_manager = fig1.canvas.manager
        new_manager.canvas.figure = fig1
        fig1.set_canvas(new_manager.canvas)
        ax1 = fig1.add_subplot(111)
        ax1.has_been_closed = False
        ax1.step(newList, self.values, where='mid')
        plt1.xlabel('Distance mm')
        plt1.ylabel('CT #')
        plt1.grid(True)
        fig1.canvas.mpl_connect('close_event', self.on_close)
        plt1.show()


######################################################
#              MAIN PAGE CONTROLLER                  #
######################################################
class MainPage:

    def __init__(self, path, datasets, filepaths,raw_dvh):
        self.path = path
        self.dataset = datasets
        self.filepaths = filepaths 
        self.raw_dvh = raw_dvh

    def runPyradiomics(self):
        pyradiomics(self.path, self.filepaths)

    def runAnonymization(self, raw_dvh):
        anonymize(self.path, self.dataset, self.filepaths, self.raw_dvh)

    def display_cd_form(self, tabWindow, file_path):
        self.tab_cd = ClinicalDataForm(
            tabWindow, file_path, self.dataset, self.filepaths)
        tabWindow.addTab(self.tab_cd, "")

    def display_cd_dat(self, tabWindow, file_path):
        self.tab_cd = ClinicalDataDisplay(tabWindow, file_path)
        tabWindow.addTab(self.tab_cd, "")

    def runTransect(self, mainWindow, tabWindow, imagetoPaint, dataset, rowS, colS):
        self.tab_ct = Transect(mainWindow, imagetoPaint,
                               dataset, rowS, colS, tabWindow)
        tabWindow.setScene(self.tab_ct)
