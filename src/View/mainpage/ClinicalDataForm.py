#####################################################################################################################
#                                                                                                                   #
#   This file handles all the processes done when opening a new patient or opening the program for the first time   #
#                                                                                                                   #
#####################################################################################################################

import csv

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import QCompleter
from country_list import countries_for_language
from src.Controller.PathHandler import resource_path


# Load the list of countries
countries = dict(countries_for_language('en'))
data = []
for i, v in enumerate(countries):
    data.append(countries[v])

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

# Creating the arrays containing the above data and formatting them appropriately
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


class Ui_Form(object):
    """
    Build the UI of Clinical Data in creation / editing mode.
    """
    def setupUi(self, tabWindow):
        """
        Set up the UI.
        """
        self.tabWindow = tabWindow

        # Create the scrolling area widget
        self.init_content()

        # Create Components
        self.create_note()
        self.add_last_name()
        self.add_first_name()
        self.add_gender()
        self.add_dob()
        self.add_birth_place()
        self.add_date_at_diagnosis()
        self.add_icd()
        self.add_histology()
        self.add_T_stage()
        self.add_N_stage()
        self.add_M_stage()
        self.add_overall_stage()
        self.add_Tx_intent()
        self.add_surgery()
        self.add_Rad()
        self.add_immuno()
        self.add_chemo()
        self.add_hormone()
        self.add_brachy()
        self.add_date_last_existence()
        self.add_survival_duration()
        self.add_cancer_death()
        self.add_death()
        self.add_regional_control()
        self.add_distant_control()
        self.add_local_control()
        self.add_date_local_failure()
        self.add_date_regional_failure()
        self.add_date_distant_failure()
        self.create_save_button()

        # Add the component in a layout to be displayed.
        self.set_layout()

        self.retranslateUi()
        QtCore.QMetaObject.connectSlotsByName(tabWindow)

    def retranslateUi(self):
        """
        Add the appropriate names for each element of the class.
        """
        _translate = QtCore.QCoreApplication.translate
        self.label_LN.setText(_translate("MainWindow", "Last Name:"))
        self.label_FN.setText(_translate("MainWindow", "First Name:"))
        self.label_gender.setText(_translate("MainWindow", "Gender:"))
        self.note.setText(_translate("MainWindow",
                                        "Note: There was no csv file containing \"ClinicalData\""
                                        " in its name located in the directory."))
        self.label_DB.setText(_translate("MainWindow", "Date of Birth:"))
        self.label_BP.setText(_translate("MainWindow", "Birth Country:"))
        self.label_date_diagnosis.setText(_translate("MainWindow", "Date of Diagnosis:"))
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
        self.label_Overall_Stage.setText(_translate("MainWindow", "Overall Stage:"))
        self.Overall_Stage.setItemText(0, _translate("MainWindow", "Select..."))
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
        self.Surgery.setItemText(6, _translate("MainWindow", "Neoadjuvant (Neo)"))
        self.Surgery.setItemText(7, _translate("MainWindow", "Concurrent (Con)"))
        self.Surgery.setItemText(8, _translate("MainWindow", "Adjuvant (Adj)"))
        self.Surgery.setItemText(9, _translate("MainWindow", "Neo&Con"))
        self.Surgery.setItemText(10, _translate("MainWindow", "Neo&Adj"))
        self.Surgery.setItemText(11, _translate("MainWindow", "Con&Adj"))
        self.Surgery.setItemText(12, _translate("MainWindow", "Neo&Con&Adj"))
        self.label_Rad.setText(_translate("MainWindow", "Rad:"))
        self.label_Immuno.setText(_translate("MainWindow", "Immuno:"))
        self.label_Chemo.setText(_translate("MainWindow", "Chemo:"))
        self.label_Hormone.setText(_translate("MainWindow", "Hormone:"))
        self.label_Brachy.setText(_translate("MainWindow", "Brachy:"))
        self.label_DT_Last_existence.setText(_translate("MainWindow", "Date of Last Existence:"))
        self.Survival_dt.setText(_translate("MainWindow", "Survival Length:"))
        self.gender.setItemText(0, _translate("MainWindow", "Select..."))
        self.gender.setItemText(1, _translate("MainWindow", "Female"))
        self.gender.setItemText(2, _translate("MainWindow", "Male"))
        self.gender.setItemText(3, _translate("MainWindow", "Other"))
        self.label_Cancer_death.setText(_translate("MainWindow", "Cancer Death:"))
        self.label_Death.setText(_translate("MainWindow", "Death:"))
        self.label_Regional_control.setText(_translate("MainWindow", "Regional Control:"))
        self.label_Distant_Control.setText(_translate("MainWindow", "Distant Control:"))
        self.label_Local_control.setText(_translate("MainWindow", "Local Control:"))
        self.Save_button.setText(_translate("MainWindow", "Save"))
        self.Death.setItemText(0, _translate("MainWindow", "Select..."))
        self.Death.setItemText(1, _translate("MainWindow", "Alive"))
        self.Death.setItemText(2, _translate("MainWindow", "Dead"))
        self.Cancer_death.setItemText(0, _translate("MainWindow", "Select..."))
        self.Cancer_death.setItemText(1, _translate("MainWindow", "Non-cancer death"))
        self.Cancer_death.setItemText(2, _translate("MainWindow", "Cancer death"))
        self.Local_control.setItemText(0, _translate("MainWindow", "Select..."))
        self.Local_control.setItemText(1, _translate("MainWindow", "Control"))
        self.Local_control.setItemText(2, _translate("MainWindow", "Failure"))
        self.Regional_Control.setItemText(0, _translate("MainWindow", "Select..."))
        self.Regional_Control.setItemText(1, _translate("MainWindow", "Control"))
        self.Regional_Control.setItemText(2, _translate("MainWindow", "Failure"))
        self.Distant_Control.setItemText(0, _translate("MainWindow", "Select..."))
        self.Distant_Control.setItemText(1, _translate("MainWindow", "Control"))
        self.Distant_Control.setItemText(2, _translate("MainWindow", "Failure"))
        self.Chemo.setItemText(0, _translate("MainWindow", "Select..."))
        self.Chemo.setItemText(1, _translate("MainWindow", "No"))
        self.Chemo.setItemText(2, _translate("MainWindow", "Primary (Pri)"))
        self.Chemo.setItemText(3, _translate("MainWindow", "Refused (Ref)"))
        self.Chemo.setItemText(4, _translate("MainWindow", "Denied (Den)"))
        self.Chemo.setItemText(5, _translate("MainWindow", "DiedB4 (Die)"))
        self.Chemo.setItemText(6, _translate("MainWindow", "Neoadjuvant (Neo)"))
        self.Chemo.setItemText(7, _translate("MainWindow", "Concurrent (Con)"))
        self.Chemo.setItemText(8, _translate("MainWindow", "Adjuvant (Adj)"))
        self.Chemo.setItemText(9, _translate("MainWindow", "Neo&Con"))
        self.Chemo.setItemText(10, _translate("MainWindow", "Neo&Adj"))
        self.Chemo.setItemText(11, _translate("MainWindow", "Con&Adj"))
        self.Chemo.setItemText(12, _translate("MainWindow", "Neo&Con&Adj"))
        self.Brachy.setItemText(0, _translate("MainWindow", "Select..."))
        self.Brachy.setItemText(1, _translate("MainWindow", "No"))
        self.Brachy.setItemText(2, _translate("MainWindow", "Primary (Pri)"))
        self.Brachy.setItemText(3, _translate("MainWindow", "Refused (Ref)"))
        self.Brachy.setItemText(4, _translate("MainWindow", "Denied (Den)"))
        self.Brachy.setItemText(5, _translate("MainWindow", "DiedB4 (Die)"))
        self.Brachy.setItemText(6, _translate("MainWindow", "Neoadjuvant (Neo)"))
        self.Brachy.setItemText(7, _translate("MainWindow", "Concurrent (Con)"))
        self.Brachy.setItemText(8, _translate("MainWindow", "Adjuvant (Adj)"))
        self.Brachy.setItemText(9, _translate("MainWindow", "Neo&Con"))
        self.Brachy.setItemText(10, _translate("MainWindow", "Neo&Adj"))
        self.Brachy.setItemText(11, _translate("MainWindow", "Con&Adj"))
        self.Brachy.setItemText(12, _translate("MainWindow", "Neo&Con&Adj"))
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
        self.Immuno.setItemText(6, _translate("MainWindow", "Neoadjuvant (Neo)"))
        self.Immuno.setItemText(7, _translate("MainWindow", "Concurrent (Con)"))
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
        self.Hormone.setItemText(6, _translate("MainWindow", "Neoadjuvant (Neo)"))
        self.Hormone.setItemText(7, _translate("MainWindow", "Concurrent (Con)"))
        self.Hormone.setItemText(8, _translate("MainWindow", "Adjuvant (Adj)"))
        self.Hormone.setItemText(9, _translate("MainWindow", "Neo&Con"))
        self.Hormone.setItemText(10, _translate("MainWindow", "Neo&Adj"))
        self.Hormone.setItemText(11, _translate("MainWindow", "Con&Adj"))
        self.Hormone.setItemText(12, _translate("MainWindow", "Neo&Con&Adj"))
        self.label_Dt_Local_failure.setText(_translate("MainWindow", "Date of Local Failure:"))
        self.label_Dt_Regional_Failure.setText(_translate("MainWindow", "Date of Regional Failure:"))
        self.label_Dt_Distant_Failure.setText(_translate("MainWindow", "Date of Distant Failure:"))

    def init_content(self):
        """
        Create scrolling area widget which will contain the content.
        """
        self.scrollArea_cd = QtWidgets.QScrollArea()
        self.scrollArea_cd.setWidgetResizable(True)
        self.scrollArea_cd.setFocusPolicy(QtCore.Qt.NoFocus)
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setObjectName("ScrollAreaWidgetContents")
        self.scrollArea_cd.ensureWidgetVisible(self.scrollAreaWidgetContents)

    def set_layout(self):
        """
        Add the components in the content layout.
        """
        self.layout_content = QtWidgets.QGridLayout(self.scrollAreaWidgetContents)
        self.layout_content.setContentsMargins(10, 10, 10, 10)
        self.layout_content.setVerticalSpacing(7)

        # Create horizontal spacer in the middle of the grid
        hspacer = QtWidgets.QSpacerItem(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        # The grid layout here is of size 17 * 11
        self.layout_content.addItem(hspacer, 0, 5, 16, 1)
        self.layout_content.addWidget(self.note, 0, 0, 1, 8)
        self.layout_content.addWidget(self.label_LN, 1, 0)
        self.layout_content.addWidget(self.line_LN, 1, 1, 1, 4)
        self.layout_content.addWidget(self.label_FN, 1, 6)
        self.layout_content.addWidget(self.line_FN, 1, 7, 1, 4)
        self.layout_content.addWidget(self.label_DB, 2, 0)
        self.layout_content.addWidget(self.date_of_birth, 2, 1, 1, 4)
        self.layout_content.addWidget(self.label_BP, 2, 6)
        self.layout_content.addWidget(self.line_BP, 2, 7, 1, 4)
        self.layout_content.addWidget(self.label_date_diagnosis, 3, 0)
        self.layout_content.addWidget(self.date_diagnosis, 3, 1, 1, 4)
        self.layout_content.addWidget(self.label_gender, 3, 6)
        self.layout_content.addWidget(self.gender, 3, 7, 1, 4)
        self.layout_content.addWidget(self.label_icd, 4, 0)
        self.layout_content.addWidget(self.line_icd, 4, 1, 1, 9)
        self.layout_content.addWidget(self.label_histology, 5, 0)
        self.layout_content.addWidget(self.line_histology, 5, 1, 1, 8)
        self.layout_content.addWidget(self.label_T_stage, 6, 0)
        self.layout_content.addWidget(self.T_stage, 6, 1)
        self.layout_content.addWidget(self.label_N_Stage, 6, 3)
        self.layout_content.addWidget(self.N_stage, 6, 4)
        self.layout_content.addWidget(self.label_M_Stage, 6, 6)
        self.label_M_Stage.setAlignment(QtCore.Qt.AlignCenter)
        self.layout_content.addWidget(self.M_stage, 6, 7)
        self.layout_content.addWidget(self.label_Overall_Stage, 6, 9)
        self.layout_content.addWidget(self.Overall_Stage, 6, 10)
        self.layout_content.addWidget(self.label_Tx_intent, 7, 0)
        self.layout_content.addWidget(self.Tx_intent, 7, 1, 1, 4)
        self.layout_content.addWidget(self.label_Surgery, 8, 0)
        self.layout_content.addWidget(self.Surgery, 8, 1, 1, 4)
        self.layout_content.addWidget(self.label_Rad, 8, 6)
        self.layout_content.addWidget(self.Rad, 8, 7, 1, 4)
        self.layout_content.addWidget(self.label_Chemo, 9, 0)
        self.layout_content.addWidget(self.Chemo, 9, 1, 1, 4)
        self.layout_content.addWidget(self.label_Immuno, 9, 6)
        self.layout_content.addWidget(self.Immuno, 9, 7, 1, 4)
        self.layout_content.addWidget(self.label_Brachy, 10, 0)
        self.layout_content.addWidget(self.Brachy, 10, 1, 1, 4)
        self.layout_content.addWidget(self.label_Hormone, 10, 6)
        self.layout_content.addWidget(self.Hormone, 10, 7, 1, 4)
        self.layout_content.addWidget(self.label_DT_Last_existence, 11, 0)
        self.layout_content.addWidget(self.Dt_Last_Existence, 11, 1, 1, 4)
        self.layout_content.addWidget(self.Survival_dt, 11, 6, 1, 5)
        self.layout_content.addWidget(self.label_Death, 12, 0)
        self.layout_content.addWidget(self.Death, 12, 1, 1, 4)
        self.layout_content.addWidget(self.label_Cancer_death, 12, 6)
        self.layout_content.addWidget(self.Cancer_death, 12, 7, 1, 4)
        self.layout_content.addWidget(self.label_Local_control, 13, 0)
        self.layout_content.addWidget(self.Local_control, 13, 1, 1, 4)
        self.layout_content.addWidget(self.label_Dt_Local_failure, 13, 6)
        self.layout_content.addWidget(self.Dt_local_failure, 13, 7, 1, 4)
        self.layout_content.addWidget(self.label_Regional_control, 14, 0)
        self.layout_content.addWidget(self.Regional_Control, 14, 1, 1, 4)
        self.layout_content.addWidget(self.label_Dt_Regional_Failure, 14, 6)
        self.layout_content.addWidget(self.Dt_REgional_failure, 14, 7, 1, 4)
        self.layout_content.addWidget(self.label_Distant_Control, 15, 0)
        self.layout_content.addWidget(self.Distant_Control, 15, 1, 1, 4)
        self.layout_content.addWidget(self.label_Dt_Distant_Failure, 15, 6)
        self.layout_content.addWidget(self.Dt_Distant_Failure, 15, 7, 1, 4)
        self.layout_content.addWidget(self.Save_button, 16, 0)

        self.scrollArea_cd.setWidget(self.scrollAreaWidgetContents)

        self.layout = QtWidgets.QHBoxLayout(self.tabWindow)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.scrollArea_cd)

    def create_note(self):
        """
        Create a note that indicates the form state.
        """
        self.note = QtWidgets.QLabel()

    def add_last_name(self):
        """
        Create last name components.
        """
        self.label_LN = QtWidgets.QLabel()
        self.line_LN = QtWidgets.QLineEdit()
        self.line_LN.setFocusPolicy(QtCore.Qt.StrongFocus)

    def add_first_name(self):
        """
        Create first name components.
        """
        self.line_FN = QtWidgets.QLineEdit()
        self.label_FN = QtWidgets.QLabel()

    def add_gender(self):
        """
        Create gender components.
        """
        self.gender = QtWidgets.QComboBox()
        self.gender.addItem("")
        self.gender.addItem("")
        self.gender.addItem("")
        self.gender.addItem("")
        self.label_gender = QtWidgets.QLabel()

    def add_dob(self):
        """
        Create date of birth components.
        """
        self.label_DB = QtWidgets.QLabel()
        self.label_DB.setObjectName("label_DB")
        self.date_of_birth = QtWidgets.QDateEdit()
        self.date_of_birth.setDisplayFormat("dd/MM/yyyy")
        self.date_of_birth.setDate(QDate.currentDate())
        self.date_of_birth.setCalendarPopup(True)

    def add_birth_place(self):
        """
        Create birth place components.
        """
        self.line_BP = QtWidgets.QLineEdit()
        completer = QCompleter(data, self.line_BP)
        completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.line_BP.setCompleter(completer)
        self.label_BP = QtWidgets.QLabel()

    def add_date_at_diagnosis(self):
        """
        Create date at diagnosis components.
        """
        self.date_diagnosis = QtWidgets.QDateEdit()
        self.date_diagnosis.setDisplayFormat("dd/MM/yyyy")
        self.date_diagnosis.setDate(QDate.currentDate())
        self.date_diagnosis.setCalendarPopup(True)
        self.label_date_diagnosis = QtWidgets.QLabel()

    def add_icd(self):
        """
        Create ICD10 components.
        """
        self.line_icd = QtWidgets.QLineEdit()
        completer_5 = QCompleter(new_icd, self.line_icd)
        completer_5.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        completer_5.setFilterMode(QtCore.Qt.MatchContains)
        self.line_icd.setCompleter(completer_5)
        self.label_icd = QtWidgets.QLabel()

    def add_histology(self):
        """
        Create histology components.
        """
        self.line_histology = QtWidgets.QLineEdit()
        completer_4 = QCompleter(new_hist, self.line_histology)
        completer_4.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        completer_4.setFilterMode(QtCore.Qt.MatchContains)
        self.line_histology.setCompleter(completer_4)
        self.label_histology = QtWidgets.QLabel()

    def add_T_stage(self):
        """
        Create T stage components.
        """
        self.label_T_stage = QtWidgets.QLabel()
        self.T_stage = QtWidgets.QComboBox()
        self.T_stage.addItem("")
        self.T_stage.addItem("")
        self.T_stage.addItem("")
        self.T_stage.addItem("")
        self.T_stage.addItem("")
        self.T_stage.addItem("")
        self.T_stage.addItem("")

    def add_N_stage(self):
        """
        Create N stage components.
        """
        self.N_stage = QtWidgets.QComboBox()
        self.N_stage.addItem("")
        self.N_stage.addItem("")
        self.N_stage.addItem("")
        self.N_stage.addItem("")
        self.N_stage.addItem("")
        self.label_N_Stage = QtWidgets.QLabel()

    def add_M_stage(self):
        """
        Create M stage components.
        """
        self.M_stage = QtWidgets.QComboBox()
        self.M_stage.addItem("")
        self.M_stage.addItem("")
        self.M_stage.addItem("")
        self.label_M_Stage = QtWidgets.QLabel()

    def add_overall_stage(self):
        """
        Create overall stage components.
        """
        self.label_Overall_Stage = QtWidgets.QLabel()
        self.Overall_Stage = QtWidgets.QComboBox()
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

    def add_Tx_intent(self):
        """
        Create Tx intent components.
        """
        self.Tx_intent = QtWidgets.QComboBox()
        self.Tx_intent.addItem("")
        self.Tx_intent.addItem("")
        self.Tx_intent.addItem("")
        self.Tx_intent.addItem("")
        self.Tx_intent.addItem("")
        self.Tx_intent.addItem("")
        self.label_Tx_intent = QtWidgets.QLabel()

    def add_surgery(self):
        """
        Create surgery components.
        """
        self.label_Surgery = QtWidgets.QLabel()
        self.Surgery = QtWidgets.QComboBox()
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

    def add_Rad(self):
        """
        Create Rad components.
        """
        self.label_Rad = QtWidgets.QLabel()
        self.Rad = QtWidgets.QComboBox()
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

    def add_immuno(self):
        """
        Create Immuno components.
        """
        self.label_Immuno = QtWidgets.QLabel()
        self.Immuno = QtWidgets.QComboBox()
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

    def add_chemo(self):
        """
        Create chemo components.
        """
        self.label_Chemo = QtWidgets.QLabel()
        self.Chemo = QtWidgets.QComboBox()
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

    def add_hormone(self):
        """
        Create hormone components.
        """
        self.label_Hormone = QtWidgets.QLabel()
        self.Hormone = QtWidgets.QComboBox()
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

    def add_brachy(self):
        """
        Create brachy components.
        """
        self.label_Brachy = QtWidgets.QLabel()
        self.Brachy = QtWidgets.QComboBox()
        self.Brachy.addItem("")
        self.Brachy.addItem("")
        self.Brachy.addItem("")
        self.Brachy.addItem("")
        self.Brachy.addItem("")
        self.Brachy.addItem("")
        self.Brachy.addItem("")
        self.Brachy.addItem("")
        self.Brachy.addItem("")
        self.Brachy.addItem("")
        self.Brachy.addItem("")
        self.Brachy.addItem("")
        self.Brachy.addItem("")

    def add_date_last_existence(self):
        """
        Create date of last existence components.
        """
        self.label_DT_Last_existence = QtWidgets.QLabel()
        self.Dt_Last_Existence = QtWidgets.QDateEdit()
        self.Dt_Last_Existence.setDisplayFormat("dd/MM/yyyy")
        self.Dt_Last_Existence.setDate(QDate.currentDate())
        self.Dt_Last_Existence.setCalendarPopup(True)

    def add_survival_duration(self):
        """
        Create survival duration indicator.
        """
        self.Survival_dt = QtWidgets.QLabel()
        self.Survival_dt.setVisible(False)

    def add_cancer_death(self):
        """
        Create cancer death components.
        """
        self.label_Cancer_death = QtWidgets.QLabel()
        self.Cancer_death = QtWidgets.QComboBox()
        self.Cancer_death.addItem("")
        self.Cancer_death.addItem("")
        self.Cancer_death.addItem("")

    def add_death(self):
        """
        Create death components.
        """
        self.label_Death = QtWidgets.QLabel()
        self.Death = QtWidgets.QComboBox()
        self.Death.addItem("")
        self.Death.addItem("")
        self.Death.addItem("")

    def add_regional_control(self):
        """
        Create regional control components.
        """
        self.label_Regional_control = QtWidgets.QLabel()
        self.Regional_Control = QtWidgets.QComboBox()
        self.Regional_Control.addItem("")
        self.Regional_Control.addItem("")
        self.Regional_Control.addItem("")

    def add_distant_control(self):
        """
        Create distant control components.
        """
        self.label_Distant_Control = QtWidgets.QLabel()
        self.Distant_Control = QtWidgets.QComboBox()
        self.Distant_Control.addItem("")
        self.Distant_Control.addItem("")
        self.Distant_Control.addItem("")

    def add_local_control(self):
        """
        Create local control components.
        """
        self.label_Local_control = QtWidgets.QLabel()
        self.Local_control = QtWidgets.QComboBox()
        self.Local_control.addItem("")
        self.Local_control.addItem("")
        self.Local_control.addItem("")

    def add_date_local_failure(self):
        """
        Create date local failure components.
        """
        self.label_Dt_Local_failure = QtWidgets.QLabel()
        self.Dt_local_failure = QtWidgets.QDateEdit()
        self.Dt_local_failure.setDisplayFormat("dd/MM/yyyy")
        self.Dt_local_failure.setDate(QDate.currentDate())
        self.Dt_local_failure.setCalendarPopup(True)
        self.Dt_local_failure.setDisabled(True)

    def add_date_regional_failure(self):
        """
        Create date regional failure components.
        """
        self.label_Dt_Regional_Failure = QtWidgets.QLabel()
        self.Dt_REgional_failure = QtWidgets.QDateEdit()
        self.Dt_REgional_failure.setDisplayFormat("dd/MM/yyyy")
        self.Dt_REgional_failure.setDate(QDate.currentDate())
        self.Dt_REgional_failure.setCalendarPopup(True)
        self.Dt_REgional_failure.setDisabled(True)

    def add_date_distant_failure(self):
        """
        Create date distant failure components.
        """
        self.Dt_Distant_Failure = QtWidgets.QDateEdit()
        self.Dt_Distant_Failure.setDisplayFormat("dd/MM/yyyy")
        self.Dt_Distant_Failure.setDate(QDate.currentDate())
        self.Dt_Distant_Failure.setCalendarPopup(True)
        self.Dt_Distant_Failure.setDisabled(True)
        self.label_Dt_Distant_Failure = QtWidgets.QLabel()

    def create_save_button(self):
        """
        Create Save Button.
        """
        self.Save_button = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.Save_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        icon_save = QtGui.QIcon()
        icon_save.addPixmap(
            QtGui.QPixmap(resource_path('src/res/images/btn-icons/save_icon.png')),
            QtGui.QIcon.Normal,
            QtGui.QIcon.On
        )
        self.Save_button.setIcon(icon_save)
