#####################################################################################################################
#                                                                                                                   #
# This file contains the Clinical Data Display UI for this software                                                 #
#                                                                                                                   #
#####################################################################################################################
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QStringListModel
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QCompleter, QLineEdit
from country_list import countries_for_language
from array import *
import numpy as np
import csv

#####################################################################################################################
#                                                                                                                   #
#   The following code are global data/variables used by Clinical Data Display class                                #
#                                                                                                                   #
#####################################################################################################################

# Load the list of countries
countries = dict(countries_for_language('en'))
data = []
for i, v in enumerate(countries):
    data.append(countries[v])

# Load the diseases and format them
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

#####################################################################################################################
#                                                                                                                   #
#   The following code builds the UI od Clinical data in display mode                                               #
#                                                                                                                   #
#####################################################################################################################

class Ui_CD_Display(object):

    # set up the ui
    def setupUi(self, MainWindow):

        self.hLayout_structures = QtWidgets.QHBoxLayout(MainWindow)
        self.hLayout_structures.setContentsMargins(0, 0, 0, 0)
        self.scrollArea_cd = QtWidgets.QScrollArea()
        self.scrollArea_cd.setWidgetResizable(True)
        self.scrollArea_cd.setFocusPolicy(Qt.NoFocus)
        self.scrollArea_cd.setObjectName("scrollArea_cd")
        self.scrollArea_cd.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOn)
        self.scrollArea_cd.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOff)
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setFixedSize(1000,900)
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.scrollArea_cd.ensureWidgetVisible(self.scrollAreaWidgetContents)
        self.label_4 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_4.setGeometry(QtCore.QRect(20, 8, 961, 65))
        self.label_4.setStyleSheet("color: rgb(0,0,0) ")
        self.label_4.setObjectName("label_4")
        # gender components
        self.label_3 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_3.setGeometry(QtCore.QRect(20, 70, 81, 21))
        self.label_3.setObjectName("label_3")
        self.gender = QtWidgets.QComboBox(self.scrollAreaWidgetContents)
        self.gender.setGeometry(QtCore.QRect(150, 70, 171, 25))
        self.gender.setObjectName("gender")
        self.gender.addItem("")
        self.gender.addItem("")
        self.gender.addItem("")
        self.gender.addItem("")
        # birth place components
        self.label_BP = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_BP.setGeometry(QtCore.QRect(350, 70, 121, 21))
        self.label_BP.setObjectName("label_BP")
        self.line_BP = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.line_BP.setGeometry(QtCore.QRect(460, 70, 171, 25))
        self.line_BP.setObjectName("line_BP")
        completer = QCompleter(data, self.line_BP)
        completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.line_BP.setCompleter(completer)
        # age at diagnosis components
        self.label_AD = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_AD.setGeometry(QtCore.QRect(20, 120, 121, 21))
        self.label_AD.setObjectName("label_AD")
        self.age_at_diagnosis = QtWidgets.QLineEdit(
            self.scrollAreaWidgetContents)
        self.age_at_diagnosis.setGeometry(QtCore.QRect(150, 115, 171, 31))
        self.age_at_diagnosis.setObjectName("age_at_diagnosis")
        # Dx year components
        self.label_Dx_year = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_Dx_year.setGeometry(QtCore.QRect(350, 120, 101, 21))
        self.label_Dx_year.setObjectName("label_Dx_year")
        self.line_Dx_Year = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.line_Dx_Year.setGeometry(QtCore.QRect(460, 120, 171, 25))
        self.line_Dx_Year.setObjectName("line_Dx_Year")
        # icd components
        self.label_icd = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_icd.setGeometry(QtCore.QRect(20, 165, 81, 21))
        self.label_icd.setObjectName("label_icd")
        self.line_icd = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.line_icd.setGeometry(QtCore.QRect(150, 165, 601, 25))
        self.line_icd.setObjectName("line_icd")
        completer_5 = QCompleter(new_icd, self.line_icd)
        completer_5.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        completer_5.setFilterMode(QtCore.Qt.MatchContains)
        self.line_icd.setCompleter(completer_5)
        # histology components
        self.label_histology = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_histology.setGeometry(QtCore.QRect(20, 220, 81, 21))
        self.label_histology.setObjectName("label_histology")
        self.line_histology = QtWidgets.QLineEdit(
            self.scrollAreaWidgetContents)
        self.line_histology.setGeometry(QtCore.QRect(150, 220, 601, 25))
        self.line_histology.setObjectName("line_histology")
        completer_4 = QCompleter(new_hist, self.line_histology)
        completer_4.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        completer_4.setFilterMode(QtCore.Qt.MatchContains)
        self.line_histology.setCompleter(completer_4)
        #T stage components
        self.label_T_stage = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_T_stage.setGeometry(QtCore.QRect(20, 270, 81, 21))
        self.label_T_stage.setObjectName("label_T_stage")
        self.T_stage = QtWidgets.QComboBox(self.scrollAreaWidgetContents)
        self.T_stage.setGeometry(QtCore.QRect(90, 270, 81, 25))
        self.T_stage.setObjectName("T_stage")
        self.T_stage.addItem("")
        self.T_stage.addItem("")
        self.T_stage.addItem("")
        self.T_stage.addItem("")
        self.T_stage.addItem("")
        self.T_stage.addItem("")
        self.T_stage.addItem("")
        # N stage components
        self.N_stage = QtWidgets.QComboBox(self.scrollAreaWidgetContents)
        self.N_stage.setGeometry(QtCore.QRect(270, 270, 81, 25))
        self.N_stage.setObjectName("N_stage")
        self.N_stage.addItem("")
        self.N_stage.addItem("")
        self.N_stage.addItem("")
        self.N_stage.addItem("")
        self.N_stage.addItem("")
        self.label_N_Stage = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_N_Stage.setGeometry(QtCore.QRect(200, 270, 81, 21))
        self.label_N_Stage.setObjectName("label_N_Stage")
        # M stage components
        self.M_stage = QtWidgets.QComboBox(self.scrollAreaWidgetContents)
        self.M_stage.setGeometry(QtCore.QRect(450, 270, 81, 25))
        self.M_stage.setObjectName("M_stage")
        self.M_stage.addItem("")
        self.M_stage.addItem("")
        self.M_stage.addItem("")
        self.label_M_Stage = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_M_Stage.setGeometry(QtCore.QRect(380, 270, 81, 21))
        self.label_M_Stage.setObjectName("label_M_Stage")
        # Overall stage components
        self.label_Overall_Stage = QtWidgets.QLabel(
            self.scrollAreaWidgetContents)
        self.label_Overall_Stage.setGeometry(QtCore.QRect(560, 270, 101, 21))
        self.label_Overall_Stage.setObjectName("label_Overall_Stage")
        self.Overall_Stage = QtWidgets.QComboBox(self.scrollAreaWidgetContents)
        self.Overall_Stage.setGeometry(QtCore.QRect(670, 270, 81, 25))
        self.Overall_Stage.setObjectName("Overall_Stage")
        self.Overall_Stage.addItem("")
        self.Overall_Stage.addItem("")
        self.Overall_Stage.addItem("")
        self.Overall_Stage.addItem("")
        self.Overall_Stage.addItem("")
        self.Overall_Stage.addItem("")
        self.Overall_Stage.addItem("")
        self.Overall_Stage.addItem("")
        self.Overall_Stage.addItem("")
        self.Overall_Stage.addItem("")
        self.Overall_Stage.addItem("")
        self.Overall_Stage.addItem("")
        self.Overall_Stage.addItem("")
        self.Overall_Stage.addItem("")
        self.Overall_Stage.addItem("")
        self.Overall_Stage.addItem("")
        # Tx intent components
        self.Tx_intent = QtWidgets.QComboBox(self.scrollAreaWidgetContents)
        self.Tx_intent.setGeometry(QtCore.QRect(150, 320, 171, 25))
        self.Tx_intent.setObjectName("Tx_intent")
        self.Tx_intent.addItem("")
        self.Tx_intent.addItem("")
        self.Tx_intent.addItem("")
        self.Tx_intent.addItem("")
        self.Tx_intent.addItem("")
        self.Tx_intent.addItem("")
        self.label_Tx_intent = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_Tx_intent.setGeometry(QtCore.QRect(20, 320, 81, 21))
        self.label_Tx_intent.setObjectName("label_Tx_intent")
        # Surgery components
        self.label_Surgery = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_Surgery.setGeometry(QtCore.QRect(20, 370, 81, 21))
        self.label_Surgery.setObjectName("label_Surgery")
        self.Surgery = QtWidgets.QComboBox(self.scrollAreaWidgetContents)
        self.Surgery.setGeometry(QtCore.QRect(150, 370, 171, 25))
        self.Surgery.setObjectName("Surgery")
        self.Surgery.addItem("")
        self.Surgery.addItem("")
        self.Surgery.addItem("")
        self.Surgery.addItem("")
        self.Surgery.addItem("")
        self.Surgery.addItem("")
        self.Surgery.addItem("")
        self.Surgery.addItem("")
        self.Surgery.addItem("")
        self.Surgery.addItem("")
        self.Surgery.addItem("")
        self.Surgery.addItem("")
        self.Surgery.addItem("")
        # Rad components
        self.label_Rad = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_Rad.setGeometry(QtCore.QRect(350, 370, 81, 21))
        self.label_Rad.setObjectName("label_Rad")
        self.Rad = QtWidgets.QComboBox(self.scrollAreaWidgetContents)
        self.Rad.setGeometry(QtCore.QRect(440, 370, 171, 25))
        self.Rad.setObjectName("Rad")
        self.Rad.addItem("")
        self.Rad.addItem("")
        self.Rad.addItem("")
        self.Rad.addItem("")
        self.Rad.addItem("")
        self.Rad.addItem("")
        self.Rad.addItem("")
        self.Rad.addItem("")
        self.Rad.addItem("")
        self.Rad.addItem("")
        self.Rad.addItem("")
        self.Rad.addItem("")
        self.Rad.addItem("")
        # Immuno components
        self.label_Immuno = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_Immuno.setGeometry(QtCore.QRect(350, 420, 81, 21))
        self.label_Immuno.setObjectName("label_Immuno")
        self.Immuno = QtWidgets.QComboBox(self.scrollAreaWidgetContents)
        self.Immuno.setGeometry(QtCore.QRect(440, 420, 171, 25))
        self.Immuno.setObjectName("Immuno")
        self.Immuno.addItem("")
        self.Immuno.addItem("")
        self.Immuno.addItem("")
        self.Immuno.addItem("")
        self.Immuno.addItem("")
        self.Immuno.addItem("")
        self.Immuno.addItem("")
        self.Immuno.addItem("")
        self.Immuno.addItem("")
        self.Immuno.addItem("")
        self.Immuno.addItem("")
        self.Immuno.addItem("")
        self.Immuno.addItem("")
        # Chemo components
        self.Chemo = QtWidgets.QComboBox(self.scrollAreaWidgetContents)
        self.Chemo.setGeometry(QtCore.QRect(150, 420, 171, 25))
        self.Chemo.setObjectName("Chemo")
        self.Chemo.addItem("")
        self.Chemo.addItem("")
        self.Chemo.addItem("")
        self.Chemo.addItem("")
        self.Chemo.addItem("")
        self.Chemo.addItem("")
        self.Chemo.addItem("")
        self.Chemo.addItem("")
        self.Chemo.addItem("")
        self.Chemo.addItem("")
        self.Chemo.addItem("")
        self.Chemo.addItem("")
        self.Chemo.addItem("")
        self.label_Chemo = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_Chemo.setGeometry(QtCore.QRect(20, 420, 81, 21))
        self.label_Chemo.setObjectName("label_Chemo")
        # Hormone components
        self.label_Hormone = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_Hormone.setGeometry(QtCore.QRect(350, 470, 81, 21))
        self.label_Hormone.setObjectName("label_Hormone")
        self.Hormone = QtWidgets.QComboBox(self.scrollAreaWidgetContents)
        self.Hormone.setGeometry(QtCore.QRect(440, 470, 171, 25))
        self.Hormone.setObjectName("Hormone")
        self.Hormone.addItem("")
        self.Hormone.addItem("")
        self.Hormone.addItem("")
        self.Hormone.addItem("")
        self.Hormone.addItem("")
        self.Hormone.addItem("")
        self.Hormone.addItem("")
        self.Hormone.addItem("")
        self.Hormone.addItem("")
        self.Hormone.addItem("")
        self.Hormone.addItem("")
        self.Hormone.addItem("")
        self.Hormone.addItem("")
        # Branchy components
        self.label_Branchy = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_Branchy.setGeometry(QtCore.QRect(20, 470, 81, 21))
        self.label_Branchy.setObjectName("label_Branchy")
        self.Branchy = QtWidgets.QComboBox(self.scrollAreaWidgetContents)
        self.Branchy.setGeometry(QtCore.QRect(150, 470, 171, 25))
        self.Branchy.setObjectName("Branchy")
        self.Branchy.addItem("")
        self.Branchy.addItem("")
        self.Branchy.addItem("")
        self.Branchy.addItem("")
        self.Branchy.addItem("")
        self.Branchy.addItem("")
        self.Branchy.addItem("")
        self.Branchy.addItem("")
        self.Branchy.addItem("")
        self.Branchy.addItem("")
        self.Branchy.addItem("")
        self.Branchy.addItem("")
        self.Branchy.addItem("")
        # Survival duration components
        self.label_SD = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_SD.setGeometry(QtCore.QRect(20, 520, 121, 21))
        self.label_SD.setObjectName("label_SD")
        self.survival_duration = QtWidgets.QLineEdit(
            self.scrollAreaWidgetContents)
        self.survival_duration.setGeometry(QtCore.QRect(150, 520, 171, 25))
        self.survival_duration.setObjectName("survival_duration")
        self.label_Cancer_death = QtWidgets.QLabel(
            self.scrollAreaWidgetContents)
        # Cancer death components
        self.Cancer_death = QtWidgets.QComboBox(self.scrollAreaWidgetContents)
        self.Cancer_death.setGeometry(QtCore.QRect(460, 565, 171, 25))
        self.Cancer_death.setObjectName("Cancer_death")
        self.Cancer_death.addItem("")
        self.Cancer_death.addItem("")
        self.Cancer_death.addItem("")
        self.label_Cancer_death.setGeometry(QtCore.QRect(350, 565, 121, 21))
        self.label_Cancer_death.setObjectName("label_Cancer_death")
        # Death components
        self.label_Death = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_Death.setGeometry(QtCore.QRect(20, 565, 81, 21))
        self.label_Death.setObjectName("label_Death")
        self.Death = QtWidgets.QComboBox(self.scrollAreaWidgetContents)
        self.Death.setGeometry(QtCore.QRect(150, 565, 171, 25))
        self.Death.setObjectName("Death")
        self.Death.addItem("")
        self.Death.addItem("")
        self.Death.addItem("")
        # Local control Duration components
        self.label_LCD = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_LCD.setGeometry(QtCore.QRect(20, 620, 101, 21))
        self.label_LCD.setObjectName("label_LCD")
        self.LC_duration = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.LC_duration.setGeometry(QtCore.QRect(150, 620, 101, 25))
        self.LC_duration.setObjectName("LC_duration")
        # Regional control duration components
        self.label_RCD = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_RCD.setGeometry(QtCore.QRect(280, 620, 101, 21))
        self.label_RCD.setObjectName("label_RCD")
        self.RC_duration = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.RC_duration.setGeometry(QtCore.QRect(410, 620, 101, 25))
        self.RC_duration.setObjectName("RC_duration")
        # Distance control duration components
        self.label_DCD = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_DCD.setGeometry(QtCore.QRect(540, 620, 101, 21))
        self.label_DCD.setObjectName("label_DCD")
        self.DC_duration = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.DC_duration.setGeometry(QtCore.QRect(670, 620, 101, 25))
        self.DC_duration.setObjectName("DC_duration")
        # Regional constrol components
        self.label_Regional_control = QtWidgets.QLabel(
            self.scrollAreaWidgetContents)
        self.label_Regional_control.setGeometry(QtCore.QRect(20, 720, 121, 21))
        self.label_Regional_control.setObjectName("label_Regional_control")
        self.Regional_Control = QtWidgets.QComboBox(
            self.scrollAreaWidgetContents)
        self.Regional_Control.setGeometry(QtCore.QRect(150, 720, 171, 25))
        self.Regional_Control.setObjectName("Regional_Control")
        self.Regional_Control.addItem("")
        self.Regional_Control.addItem("")
        self.Regional_Control.addItem("")
        # Distant control components
        self.label_Distant_Control = QtWidgets.QLabel(
            self.scrollAreaWidgetContents)
        self.label_Distant_Control.setGeometry(QtCore.QRect(20, 770, 121, 21))
        self.label_Distant_Control.setObjectName("label_Distant_Control")
        self.Distant_Control = QtWidgets.QComboBox(
            self.scrollAreaWidgetContents)
        self.Distant_Control.setGeometry(QtCore.QRect(150, 770, 171, 25))
        self.Distant_Control.setObjectName("Distant_Control")
        self.Distant_Control.addItem("")
        self.Distant_Control.addItem("")
        self.Distant_Control.addItem("")
        # Local constrol components
        self.label_Local_control = QtWidgets.QLabel(
            self.scrollAreaWidgetContents)
        self.label_Local_control.setGeometry(QtCore.QRect(20, 670, 101, 21))
        self.label_Local_control.setObjectName("label_Local_control")
        self.Local_control = QtWidgets.QComboBox(self.scrollAreaWidgetContents)
        self.Local_control.setGeometry(QtCore.QRect(150, 670, 171, 25))
        self.Local_control.setObjectName("Local_control")
        self.Local_control.addItem("")
        self.Local_control.addItem("")
        self.Local_control.addItem("")
        # Edit button
        self.Edit_button = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.Edit_button.setGeometry(QtCore.QRect(20, 820, 89, 25))
        self.Edit_button.setStyleSheet("background-color: rgb(238, 238, 236);\n"
                                       "color:rgb(75,0,130);\n"
                                       "font-weight: bold;\n")
        self.Edit_button.setObjectName("Edit_button")
        self.Edit_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        # Date of local failure components
        self.label_Dt_Local_failure = QtWidgets.QLabel(
            self.scrollAreaWidgetContents)
        self.label_Dt_Local_failure.setGeometry(
            QtCore.QRect(350, 675, 151, 21))
        self.label_Dt_Local_failure.setObjectName("label_Dt_Local_failure")
        self.Dt_local_failure = QtWidgets.QDateEdit(
            self.scrollAreaWidgetContents)
        self.Dt_local_failure.setDisplayFormat("dd/MM/yyyy")
        self.Dt_local_failure.setGeometry(QtCore.QRect(530, 670, 171, 31))
        self.Dt_local_failure.setObjectName("Dt_local_failure")
        self.Dt_local_failure.setCalendarPopup(True)
        self.Dt_local_failure.setDisabled(True)
        # Date of regional failure components
        self.label_Dt_Regional_Failure = QtWidgets.QLabel(
            self.scrollAreaWidgetContents)
        self.label_Dt_Regional_Failure.setGeometry(
            QtCore.QRect(350, 725, 171, 21))
        self.label_Dt_Regional_Failure.setObjectName(
            "label_Dt_Regional_Failure")
        self.Dt_REgional_failure = QtWidgets.QDateEdit(
            self.scrollAreaWidgetContents)
        self.Dt_REgional_failure.setDisplayFormat("dd/MM/yyyy")
        self.Dt_REgional_failure.setGeometry(QtCore.QRect(530, 720, 171, 31))
        self.Dt_REgional_failure.setObjectName("Dt_REgional_failure")
        self.Dt_REgional_failure.setCalendarPopup(True)
        self.Dt_REgional_failure.setDisabled(True)
        # Date of distant failure components
        self.Dt_Distant_Failure = QtWidgets.QDateEdit(
            self.scrollAreaWidgetContents)
        self.Dt_Distant_Failure.setDisplayFormat("dd/MM/yyyy")
        self.Dt_Distant_Failure.setGeometry(QtCore.QRect(530, 765, 171, 31))
        self.Dt_Distant_Failure.setObjectName("Dt_Distant_Failure")
        self.Dt_Distant_Failure.setCalendarPopup(True)
        self.Dt_Distant_Failure.setDisabled(True)
        self.label_Dt_Distant_Failure = QtWidgets.QLabel(
            self.scrollAreaWidgetContents)
        self.label_Dt_Distant_Failure.setGeometry(
            QtCore.QRect(350, 770, 171, 21))
        self.label_Dt_Distant_Failure.setObjectName("label_Dt_Distant_Failure")
        self.hLayout_structures.addWidget(self.scrollArea_cd)
        self.scrollArea_cd.setWidget(self.scrollAreaWidgetContents)
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    # this function adds the appropriate names for each element of the class
    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        self.label_Dx_year.setText(_translate("MainWindow", "Dx_Year:"))
        self.label_AD.setText(_translate("MainWindow", "Age of Diagnosis:"))
        self.label_3.setText(_translate("MainWindow", "Gender:"))
        self.label_4.setText(_translate(
            "MainWindow", "Note: The following Clinical Data was found for this patient."))
        self.label_BP.setText(_translate("MainWindow", "Birth Country:"))
        self.label_SD.setText(_translate("MainWindow", "Survival Duration:"))
        self.label_LCD.setText(_translate("MainWindow", "LC Duration:"))
        self.label_RCD.setText(_translate("MainWindow", "RC Duration:"))
        self.label_DCD.setText(_translate("MainWindow", "DC Duration:"))
        self.label_icd.setText(_translate("MainWindow", "ICD10:"))
        self.label_histology.setText(_translate("MainWindow", "Histology:"))
        self.label_T_stage.setText(_translate("MainWindow", "T Stage:"))
        self.T_stage.setItemText(0, _translate("MainWindow", "Select..."))
        self.T_stage.setItemText(1, _translate("MainWindow", "T0"))
        self.T_stage.setItemText(2, _translate("MainWindow", "Tis"))
        self.T_stage.setItemText(3, _translate("MainWindow", "T1"))
        self.T_stage.setItemText(4, _translate("MainWindow", "T2"))
        self.T_stage.setItemText(5, _translate("MainWindow", "T3"))
        self.T_stage.setItemText(6, _translate("MainWindow", "T4"))
        self.N_stage.setItemText(0, _translate("MainWindow", "Select..."))
        self.N_stage.setItemText(1, _translate("MainWindow", "N0"))
        self.N_stage.setItemText(2, _translate("MainWindow", "N1"))
        self.N_stage.setItemText(3, _translate("MainWindow", "N2"))
        self.N_stage.setItemText(4, _translate("MainWindow", "N3"))
        self.label_N_Stage.setText(_translate("MainWindow", "N Stage:"))
        self.M_stage.setItemText(0, _translate("MainWindow", "Select..."))
        self.M_stage.setItemText(1, _translate("MainWindow", "M0"))
        self.M_stage.setItemText(2, _translate("MainWindow", "M1"))
        self.label_Overall_Stage.setText(
            _translate("MainWindow", "Overall Stage:"))
        self.Overall_Stage.setItemText(
            0, _translate("MainWindow", "Select..."))
        self.Overall_Stage.setItemText(1, _translate("MainWindow", "O"))
        self.Overall_Stage.setItemText(2, _translate("MainWindow", "I"))
        self.Overall_Stage.setItemText(3, _translate("MainWindow", "IA"))
        self.Overall_Stage.setItemText(4, _translate("MainWindow", "IB"))
        self.Overall_Stage.setItemText(5, _translate("MainWindow", "II"))
        self.Overall_Stage.setItemText(6, _translate("MainWindow", "IIA"))
        self.Overall_Stage.setItemText(7, _translate("MainWindow", "IIB"))
        self.Overall_Stage.setItemText(8, _translate("MainWindow", "III"))
        self.Overall_Stage.setItemText(9, _translate("MainWindow", "IIIA"))
        self.Overall_Stage.setItemText(10, _translate("MainWindow", "IIIB"))
        self.Overall_Stage.setItemText(11, _translate("MainWindow", "IIIC"))
        self.Overall_Stage.setItemText(12, _translate("MainWindow", "IV"))
        self.Overall_Stage.setItemText(13, _translate("MainWindow", "IVA"))
        self.Overall_Stage.setItemText(14, _translate("MainWindow", "IVB"))
        self.Overall_Stage.setItemText(15, _translate("MainWindow", "IVC"))
        self.label_M_Stage.setText(_translate("MainWindow", "M Stage:"))
        self.Tx_intent.setItemText(0, _translate("MainWindow", "Select..."))
        self.Tx_intent.setItemText(1, _translate("MainWindow", "Cure"))
        self.Tx_intent.setItemText(2, _translate("MainWindow", "Palliation"))
        self.Tx_intent.setItemText(3, _translate("MainWindow", "Surveillance"))
        self.Tx_intent.setItemText(4, _translate("MainWindow", "Refused"))
        self.Tx_intent.setItemText(5, _translate("MainWindow", "DiedB4"))
        self.label_Tx_intent.setText(_translate("MainWindow", "Tx_Intent:"))
        self.label_Surgery.setText(_translate("MainWindow", "Surgery:"))
        self.Surgery.setItemText(0, _translate("MainWindow", "Select..."))
        self.Surgery.setItemText(1, _translate("MainWindow", "No"))
        self.Surgery.setItemText(2, _translate("MainWindow", "Primary (Pri)"))
        self.Surgery.setItemText(3, _translate("MainWindow", "Refused (Ref)"))
        self.Surgery.setItemText(4, _translate("MainWindow", "Denied (Den)"))
        self.Surgery.setItemText(5, _translate("MainWindow", "DiedB4 (Die)"))
        self.Surgery.setItemText(6, _translate(
            "MainWindow", "Neoadjuvant (Neo)"))
        self.Surgery.setItemText(7, _translate(
            "MainWindow", "Concurrent (Con)"))
        self.Surgery.setItemText(8, _translate("MainWindow", "Adjuvant (Adj)"))
        self.Surgery.setItemText(9, _translate("MainWindow", "Neo&Con"))
        self.Surgery.setItemText(10, _translate("MainWindow", "Neo&Adj"))
        self.Surgery.setItemText(11, _translate("MainWindow", "Con&Adj"))
        self.Surgery.setItemText(12, _translate("MainWindow", "Neo&Con&Adj"))
        self.label_Rad.setText(_translate("MainWindow", "Rad:"))
        self.label_Immuno.setText(_translate("MainWindow", "Immuno:"))
        self.label_Chemo.setText(_translate("MainWindow", "Chemo:"))
        self.label_Hormone.setText(_translate("MainWindow", "Hormone:"))
        self.label_Branchy.setText(_translate("MainWindow", "Brachy:"))
        self.gender.setItemText(0, _translate("MainWindow", "Select..."))
        self.gender.setItemText(1, _translate("MainWindow", "Female"))
        self.gender.setItemText(2, _translate("MainWindow", "Male"))
        self.gender.setItemText(3, _translate("MainWindow", "Other"))
        self.label_Cancer_death.setText(
            _translate("MainWindow", "Cancer Death:"))
        self.label_Death.setText(_translate("MainWindow", "Death:"))
        self.label_Regional_control.setText(
            _translate("MainWindow", "Regional Control:"))
        self.label_Distant_Control.setText(
            _translate("MainWindow", "Distant Control:"))
        self.label_Local_control.setText(
            _translate("MainWindow", "Local Control:"))
        self.Edit_button.setText(_translate("MainWindow", "Edit"))
        self.Death.setItemText(0, _translate("MainWindow", "Select..."))
        self.Death.setItemText(1, _translate("MainWindow", "Alive"))
        self.Death.setItemText(2, _translate("MainWindow", "Dead"))
        self.Cancer_death.setItemText(0, _translate("MainWindow", "Select..."))
        self.Cancer_death.setItemText(
            1, _translate("MainWindow", "Non-cancer death"))
        self.Cancer_death.setItemText(
            2, _translate("MainWindow", "Cancer death"))
        self.Local_control.setItemText(
            0, _translate("MainWindow", "Select..."))
        self.Local_control.setItemText(1, _translate("MainWindow", "Control"))
        self.Local_control.setItemText(2, _translate("MainWindow", "Failure"))
        self.Regional_Control.setItemText(
            0, _translate("MainWindow", "Select..."))
        self.Regional_Control.setItemText(
            1, _translate("MainWindow", "Control"))
        self.Regional_Control.setItemText(
            2, _translate("MainWindow", "Failure"))
        self.Distant_Control.setItemText(
            0, _translate("MainWindow", "Select..."))
        self.Distant_Control.setItemText(
            1, _translate("MainWindow", "Control"))
        self.Distant_Control.setItemText(
            2, _translate("MainWindow", "Failure"))
        self.Chemo.setItemText(0, _translate("MainWindow", "Select..."))
        self.Chemo.setItemText(1, _translate("MainWindow", "No"))
        self.Chemo.setItemText(2, _translate("MainWindow", "Primary (Pri)"))
        self.Chemo.setItemText(3, _translate("MainWindow", "Refused (Ref)"))
        self.Chemo.setItemText(4, _translate("MainWindow", "Denied (Den)"))
        self.Chemo.setItemText(5, _translate("MainWindow", "DiedB4 (Die)"))
        self.Chemo.setItemText(6, _translate(
            "MainWindow", "Neoadjuvant (Neo)"))
        self.Chemo.setItemText(7, _translate("MainWindow", "Concurrent (Con)"))
        self.Chemo.setItemText(8, _translate("MainWindow", "Adjuvant (Adj)"))
        self.Chemo.setItemText(9, _translate("MainWindow", "Neo&Con"))
        self.Chemo.setItemText(10, _translate("MainWindow", "Neo&Adj"))
        self.Chemo.setItemText(11, _translate("MainWindow", "Con&Adj"))
        self.Chemo.setItemText(12, _translate("MainWindow", "Neo&Con&Adj"))
        self.Branchy.setItemText(0, _translate("MainWindow", "Select..."))
        self.Branchy.setItemText(1, _translate("MainWindow", "No"))
        self.Branchy.setItemText(2, _translate("MainWindow", "Primary (Pri)"))
        self.Branchy.setItemText(3, _translate("MainWindow", "Refused (Ref)"))
        self.Branchy.setItemText(4, _translate("MainWindow", "Denied (Den)"))
        self.Branchy.setItemText(5, _translate("MainWindow", "DiedB4 (Die)"))
        self.Branchy.setItemText(6, _translate(
            "MainWindow", "Neoadjuvant (Neo)"))
        self.Branchy.setItemText(7, _translate(
            "MainWindow", "Concurrent (Con)"))
        self.Branchy.setItemText(8, _translate("MainWindow", "Adjuvant (Adj)"))
        self.Branchy.setItemText(9, _translate("MainWindow", "Neo&Con"))
        self.Branchy.setItemText(10, _translate("MainWindow", "Neo&Adj"))
        self.Branchy.setItemText(11, _translate("MainWindow", "Con&Adj"))
        self.Branchy.setItemText(12, _translate("MainWindow", "Neo&Con&Adj"))
        self.Rad.setItemText(0, _translate("MainWindow", "Select..."))
        self.Rad.setItemText(1, _translate("MainWindow", "No"))
        self.Rad.setItemText(2, _translate("MainWindow", "Primary (Pri)"))
        self.Rad.setItemText(3, _translate("MainWindow", "Refused (Ref)"))
        self.Rad.setItemText(4, _translate("MainWindow", "Denied (Den)"))
        self.Rad.setItemText(5, _translate("MainWindow", "DiedB4 (Die)"))
        self.Rad.setItemText(6, _translate("MainWindow", "Neoadjuvant (Neo)"))
        self.Rad.setItemText(7, _translate("MainWindow", "Concurrent (Con)"))
        self.Rad.setItemText(8, _translate("MainWindow", "Adjuvant (Adj)"))
        self.Rad.setItemText(9, _translate("MainWindow", "Neo&Con"))
        self.Rad.setItemText(10, _translate("MainWindow", "Neo&Adj"))
        self.Rad.setItemText(11, _translate("MainWindow", "Con&Adj"))
        self.Rad.setItemText(12, _translate("MainWindow", "Neo&Con&Adj"))
        self.Immuno.setItemText(0, _translate("MainWindow", "Select..."))
        self.Immuno.setItemText(1, _translate("MainWindow", "No"))
        self.Immuno.setItemText(2, _translate("MainWindow", "Primary (Pri)"))
        self.Immuno.setItemText(3, _translate("MainWindow", "Refused (Ref)"))
        self.Immuno.setItemText(4, _translate("MainWindow", "Denied (Den)"))
        self.Immuno.setItemText(5, _translate("MainWindow", "DiedB4 (Die)"))
        self.Immuno.setItemText(6, _translate(
            "MainWindow", "Neoadjuvant (Neo)"))
        self.Immuno.setItemText(7, _translate(
            "MainWindow", "Concurrent (Con)"))
        self.Immuno.setItemText(8, _translate("MainWindow", "Adjuvant (Adj)"))
        self.Immuno.setItemText(9, _translate("MainWindow", "Neo&Con"))
        self.Immuno.setItemText(10, _translate("MainWindow", "Neo&Adj"))
        self.Immuno.setItemText(11, _translate("MainWindow", "Con&Adj"))
        self.Immuno.setItemText(12, _translate("MainWindow", "Neo&Con&Adj"))
        self.Hormone.setItemText(0, _translate("MainWindow", "Select..."))
        self.Hormone.setItemText(1, _translate("MainWindow", "No"))
        self.Hormone.setItemText(2, _translate("MainWindow", "Primary (Pri)"))
        self.Hormone.setItemText(3, _translate("MainWindow", "Refused (Ref)"))
        self.Hormone.setItemText(4, _translate("MainWindow", "Denied (Den)"))
        self.Hormone.setItemText(5, _translate("MainWindow", "DiedB4 (Die)"))
        self.Hormone.setItemText(6, _translate(
            "MainWindow", "Neoadjuvant (Neo)"))
        self.Hormone.setItemText(7, _translate(
            "MainWindow", "Concurrent (Con)"))
        self.Hormone.setItemText(8, _translate("MainWindow", "Adjuvant (Adj)"))
        self.Hormone.setItemText(9, _translate("MainWindow", "Neo&Con"))
        self.Hormone.setItemText(10, _translate("MainWindow", "Neo&Adj"))
        self.Hormone.setItemText(11, _translate("MainWindow", "Con&Adj"))
        self.Hormone.setItemText(12, _translate("MainWindow", "Neo&Con&Adj"))
        self.label_Dt_Local_failure.setText(
            _translate("MainWindow", "Date of Local Failure:"))
        self.label_Dt_Regional_Failure.setText(
            _translate("MainWindow", "Date of Regional Failure:"))
        self.label_Dt_Distant_Failure.setText(
            _translate("MainWindow", "Date of Distant Failure:"))
