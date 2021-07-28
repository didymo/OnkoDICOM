# This file contains the Clinical Data Display UI for this software
import csv

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import QCompleter
from country_list import countries_for_language
from src.Controller.PathHandler import resource_path

# Load the list of countries
countries = dict(countries_for_language('en'))
data = []
for i, v in enumerate(countries):
    data.append(countries[v])

# Load the diseases and format them
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


class UiCDDisplay(object):
    """
    Build the UI of Clinical Data in Display mode.
    """

    def setupUi(self, tab_window):
        """
        Set up the UI.
        """
        self.tabWindow = tab_window
        
        # Create the scrolling area widget
        self.init_content()

        # Add components
        self.create_note()
        self.add_gender()
        self.add_birth_place()
        self.add_age_at_diagnosis()
        self.add_dx_year()
        self.add_icd()
        self.add_histology()
        self.add_t_stage()
        self.add_n_stage()
        self.add_m_stage()
        self.add_overall_stage()
        self.add_tx_intent()
        self.add_surgery()
        self.add_rad()
        self.add_immuno()
        self.add_chemo()
        self.add_hormone()
        self.add_brachy()
        self.add_survival_duration()
        self.add_cancer_death()
        self.add_death()
        self.add_local_control_duration()
        self.add_regional_control_duration()
        self.add_distance_control_duration()
        self.add_regional_control()
        self.add_distant_control()
        self.add_local_control()
        self.add_date_local_failure()
        self.add_date_regional_failure()
        self.add_date_distant_failure()
        self.create_edit_button()

        # Add the component in a layout to be displayed.
        self.set_layout()

        self.retranslate_ui()
        QtCore.QMetaObject.connectSlotsByName(tab_window)

    def retranslate_ui(self):
        """
        Add the appropriate names for each element of the class.
        """
        _translate = QtCore.QCoreApplication.translate
        self.label_dx_year.setText(_translate("MainWindow", "Dx_Year:"))
        self.label_ad.setText(_translate("MainWindow", "Age of Diagnosis:"))
        self.label_gender.setText(_translate("MainWindow", "Gender:"))
        self.note.setText(_translate(
            "MainWindow",
            "Note: The following Clinical Data was found for this patient."))
        self.label_bp.setText(_translate("MainWindow", "Birth Country:"))
        self.label_sd.setText(_translate("MainWindow", "Survival Duration:"))
        self.label_lcd.setText(_translate("MainWindow", "LC Duration:"))
        self.label_rcd.setText(_translate("MainWindow", "RC Duration:"))
        self.label_dcd.setText(_translate("MainWindow", "DC Duration:"))
        self.label_icd.setText(_translate("MainWindow", "ICD10:"))
        self.label_histology.setText(_translate("MainWindow", "Histology:"))
        self.label_t_stage.setText(_translate("MainWindow", "T Stage:"))
        self.t_stage.setItemText(0, _translate("MainWindow", "Select..."))
        self.t_stage.setItemText(1, _translate("MainWindow", "T0"))
        self.t_stage.setItemText(2, _translate("MainWindow", "Tis"))
        self.t_stage.setItemText(3, _translate("MainWindow", "T1"))
        self.t_stage.setItemText(4, _translate("MainWindow", "T2"))
        self.t_stage.setItemText(5, _translate("MainWindow", "T3"))
        self.t_stage.setItemText(6, _translate("MainWindow", "T4"))
        self.n_stage.setItemText(0, _translate("MainWindow", "Select..."))
        self.n_stage.setItemText(1, _translate("MainWindow", "N0"))
        self.n_stage.setItemText(2, _translate("MainWindow", "N1"))
        self.n_stage.setItemText(3, _translate("MainWindow", "N2"))
        self.n_stage.setItemText(4, _translate("MainWindow", "N3"))
        self.label_n_Stage.setText(_translate("MainWindow", "N Stage:"))
        self.m_stage.setItemText(0, _translate("MainWindow", "Select..."))
        self.m_stage.setItemText(1, _translate("MainWindow", "M0"))
        self.m_stage.setItemText(2, _translate("MainWindow", "M1"))
        self.label_overall_stage.setText(_translate(
            "MainWindow", "Overall Stage:"))
        self.overall_stage.setItemText(
            0, _translate("MainWindow", "Select..."))
        self.overall_stage.setItemText(1, _translate("MainWindow", "O"))
        self.overall_stage.setItemText(2, _translate("MainWindow", "I"))
        self.overall_stage.setItemText(3, _translate("MainWindow", "IA"))
        self.overall_stage.setItemText(4, _translate("MainWindow", "IB"))
        self.overall_stage.setItemText(5, _translate("MainWindow", "II"))
        self.overall_stage.setItemText(6, _translate("MainWindow", "IIA"))
        self.overall_stage.setItemText(7, _translate("MainWindow", "IIB"))
        self.overall_stage.setItemText(8, _translate("MainWindow", "III"))
        self.overall_stage.setItemText(9, _translate("MainWindow", "IIIA"))
        self.overall_stage.setItemText(10, _translate("MainWindow", "IIIB"))
        self.overall_stage.setItemText(11, _translate("MainWindow", "IIIC"))
        self.overall_stage.setItemText(12, _translate("MainWindow", "IV"))
        self.overall_stage.setItemText(13, _translate("MainWindow", "IVA"))
        self.overall_stage.setItemText(14, _translate("MainWindow", "IVB"))
        self.overall_stage.setItemText(15, _translate("MainWindow", "IVC"))
        self.label_m_Stage.setText(_translate("MainWindow", "M Stage:"))
        self.tx_intent.setItemText(0, _translate("MainWindow", "Select..."))
        self.tx_intent.setItemText(1, _translate("MainWindow", "Cure"))
        self.tx_intent.setItemText(2, _translate("MainWindow", "Palliation"))
        self.tx_intent.setItemText(3, _translate("MainWindow", "Surveillance"))
        self.tx_intent.setItemText(4, _translate("MainWindow", "Refused"))
        self.tx_intent.setItemText(5, _translate("MainWindow", "DiedB4"))
        self.label_tx_intent.setText(_translate("MainWindow", "Tx_Intent:"))
        self.label_surgery.setText(_translate("MainWindow", "Surgery:"))
        self.surgery.setItemText(0, _translate("MainWindow", "Select..."))
        self.surgery.setItemText(1, _translate("MainWindow", "No"))
        self.surgery.setItemText(2, _translate("MainWindow", "Primary (Pri)"))
        self.surgery.setItemText(3, _translate("MainWindow", "Refused (Ref)"))
        self.surgery.setItemText(4, _translate("MainWindow", "Denied (Den)"))
        self.surgery.setItemText(5, _translate("MainWindow", "DiedB4 (Die)"))
        self.surgery.setItemText(
            6, _translate("MainWindow", "Neoadjuvant (Neo)"))
        self.surgery.setItemText(
            7, _translate("MainWindow", "Concurrent (Con)"))
        self.surgery.setItemText(8, _translate("MainWindow", "Adjuvant (Adj)"))
        self.surgery.setItemText(9, _translate("MainWindow", "Neo&Con"))
        self.surgery.setItemText(10, _translate("MainWindow", "Neo&Adj"))
        self.surgery.setItemText(11, _translate("MainWindow", "Con&Adj"))
        self.surgery.setItemText(12, _translate("MainWindow", "Neo&Con&Adj"))
        self.label_rad.setText(_translate("MainWindow", "Rad:"))
        self.label_immuno.setText(_translate("MainWindow", "Immuno:"))
        self.label_chemo.setText(_translate("MainWindow", "Chemo:"))
        self.label_hormone.setText(_translate("MainWindow", "Hormone:"))
        self.label_brachy.setText(_translate("MainWindow", "Brachy:"))
        self.gender.setItemText(0, _translate("MainWindow", "Select..."))
        self.gender.setItemText(1, _translate("MainWindow", "Female"))
        self.gender.setItemText(2, _translate("MainWindow", "Male"))
        self.gender.setItemText(3, _translate("MainWindow", "Other"))
        self.label_cancer_death.setText(
            _translate("MainWindow", "Cancer Death:"))
        self.label_death.setText(_translate("MainWindow", "Death:"))
        self.label_regional_control.setText(
            _translate("MainWindow", "Regional Control:"))
        self.label_distant_control.setText(
            _translate("MainWindow", "Distant Control:"))
        self.label_Local_control.setText(
            _translate("MainWindow", "Local Control:"))
        self.edit_button.setText(
            _translate("MainWindow", "Edit"))
        self.death.setItemText(0, _translate("MainWindow", "Select..."))
        self.death.setItemText(1, _translate("MainWindow", "Alive"))
        self.death.setItemText(2, _translate("MainWindow", "Dead"))
        self.cancer_death.setItemText(0, _translate("MainWindow", "Select..."))
        self.cancer_death.setItemText(
            1, _translate("MainWindow", "Non-cancer death"))
        self.cancer_death.setItemText(
            2, _translate("MainWindow", "Cancer death"))
        self.Local_control.setItemText(
            0, _translate("MainWindow", "Select..."))
        self.Local_control.setItemText(1, _translate("MainWindow", "Control"))
        self.Local_control.setItemText(2, _translate("MainWindow", "Failure"))
        self.regional_control.setItemText(
            0, _translate("MainWindow", "Select..."))
        self.regional_control.setItemText(
            1, _translate("MainWindow", "Control"))
        self.regional_control.setItemText(
            2, _translate("MainWindow", "Failure"))
        self.distant_control.setItemText(0, _translate(
            "MainWindow", "Select..."))
        self.distant_control.setItemText(
            1, _translate("MainWindow", "Control"))
        self.distant_control.setItemText(
            2, _translate("MainWindow", "Failure"))
        self.chemo.setItemText(0, _translate("MainWindow", "Select..."))
        self.chemo.setItemText(1, _translate("MainWindow", "No"))
        self.chemo.setItemText(2, _translate("MainWindow", "Primary (Pri)"))
        self.chemo.setItemText(3, _translate("MainWindow", "Refused (Ref)"))
        self.chemo.setItemText(4, _translate("MainWindow", "Denied (Den)"))
        self.chemo.setItemText(5, _translate("MainWindow", "DiedB4 (Die)"))
        self.chemo.setItemText(
            6, _translate("MainWindow", "Neoadjuvant (Neo)"))
        self.chemo.setItemText(7, _translate("MainWindow", "Concurrent (Con)"))
        self.chemo.setItemText(8, _translate("MainWindow", "Adjuvant (Adj)"))
        self.chemo.setItemText(9, _translate("MainWindow", "Neo&Con"))
        self.chemo.setItemText(10, _translate("MainWindow", "Neo&Adj"))
        self.chemo.setItemText(11, _translate("MainWindow", "Con&Adj"))
        self.chemo.setItemText(12, _translate("MainWindow", "Neo&Con&Adj"))
        self.brachy.setItemText(0, _translate("MainWindow", "Select..."))
        self.brachy.setItemText(1, _translate("MainWindow", "No"))
        self.brachy.setItemText(2, _translate("MainWindow", "Primary (Pri)"))
        self.brachy.setItemText(3, _translate("MainWindow", "Refused (Ref)"))
        self.brachy.setItemText(4, _translate("MainWindow", "Denied (Den)"))
        self.brachy.setItemText(5, _translate("MainWindow", "DiedB4 (Die)"))
        self.brachy.setItemText(
            6, _translate("MainWindow", "Neoadjuvant (Neo)"))
        self.brachy.setItemText(7
                                , _translate("MainWindow", "Concurrent (Con)"))
        self.brachy.setItemText(8, _translate("MainWindow", "Adjuvant (Adj)"))
        self.brachy.setItemText(9, _translate("MainWindow", "Neo&Con"))
        self.brachy.setItemText(10, _translate("MainWindow", "Neo&Adj"))
        self.brachy.setItemText(11, _translate("MainWindow", "Con&Adj"))
        self.brachy.setItemText(12, _translate("MainWindow", "Neo&Con&Adj"))
        self.rad.setItemText(0, _translate("MainWindow", "Select..."))
        self.rad.setItemText(1, _translate("MainWindow", "No"))
        self.rad.setItemText(2, _translate("MainWindow", "Primary (Pri)"))
        self.rad.setItemText(3, _translate("MainWindow", "Refused (Ref)"))
        self.rad.setItemText(4, _translate("MainWindow", "Denied (Den)"))
        self.rad.setItemText(5, _translate("MainWindow", "DiedB4 (Die)"))
        self.rad.setItemText(6, _translate("MainWindow", "Neoadjuvant (Neo)"))
        self.rad.setItemText(7, _translate("MainWindow", "Concurrent (Con)"))
        self.rad.setItemText(8, _translate("MainWindow", "Adjuvant (Adj)"))
        self.rad.setItemText(9, _translate("MainWindow", "Neo&Con"))
        self.rad.setItemText(10, _translate("MainWindow", "Neo&Adj"))
        self.rad.setItemText(11, _translate("MainWindow", "Con&Adj"))
        self.rad.setItemText(12, _translate("MainWindow", "Neo&Con&Adj"))
        self.immuno.setItemText(0, _translate("MainWindow", "Select..."))
        self.immuno.setItemText(1, _translate("MainWindow", "No"))
        self.immuno.setItemText(2, _translate("MainWindow", "Primary (Pri)"))
        self.immuno.setItemText(3, _translate("MainWindow", "Refused (Ref)"))
        self.immuno.setItemText(4, _translate("MainWindow", "Denied (Den)"))
        self.immuno.setItemText(5, _translate("MainWindow", "DiedB4 (Die)"))
        self.immuno.setItemText(
            6, _translate("MainWindow", "Neoadjuvant (Neo)"))
        self.immuno.setItemText(
            7, _translate("MainWindow", "Concurrent (Con)"))
        self.immuno.setItemText(8, _translate("MainWindow", "Adjuvant (Adj)"))
        self.immuno.setItemText(9, _translate("MainWindow", "Neo&Con"))
        self.immuno.setItemText(10, _translate("MainWindow", "Neo&Adj"))
        self.immuno.setItemText(11, _translate("MainWindow", "Con&Adj"))
        self.immuno.setItemText(12, _translate("MainWindow", "Neo&Con&Adj"))
        self.hormone.setItemText(0, _translate("MainWindow", "Select..."))
        self.hormone.setItemText(1, _translate("MainWindow", "No"))
        self.hormone.setItemText(2, _translate("MainWindow", "Primary (Pri)"))
        self.hormone.setItemText(3, _translate("MainWindow", "Refused (Ref)"))
        self.hormone.setItemText(4, _translate("MainWindow", "Denied (Den)"))
        self.hormone.setItemText(5, _translate("MainWindow", "DiedB4 (Die)"))
        self.hormone.setItemText(
            6, _translate("MainWindow", "Neoadjuvant (Neo)"))
        self.hormone.setItemText(
            7, _translate("MainWindow", "Concurrent (Con)"))
        self.hormone.setItemText(8, _translate("MainWindow", "Adjuvant (Adj)"))
        self.hormone.setItemText(9, _translate("MainWindow", "Neo&Con"))
        self.hormone.setItemText(10, _translate("MainWindow", "Neo&Adj"))
        self.hormone.setItemText(11, _translate("MainWindow", "Con&Adj"))
        self.hormone.setItemText(12, _translate("MainWindow", "Neo&Con&Adj"))
        self.label_dt_Local_failure.setText(
            _translate("MainWindow", "Date of Local Failure:"))
        self.label_dt_regional_failure.setText(
            _translate("MainWindow", "Date of Regional Failure:"))
        self.label_dt_distant_failure.setText(
            _translate("MainWindow", "Date of Distant Failure:"))

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
        self.layout_content = \
            QtWidgets.QGridLayout(self.scrollAreaWidgetContents)
        self.layout_content.setContentsMargins(10, 10, 10, 10)
        self.layout_content.setVerticalSpacing(7)

        # Create horizontal spacer in the middle of the grid
        hspacer = QtWidgets.QSpacerItem(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        # The grid layout here is of size 17 * 11
        self.layout_content.addItem(hspacer, 0, 5, 16, 1)
        self.layout_content.addWidget(self.note, 0, 0, 1, 8)
        self.layout_content.addWidget(self.label_gender, 1, 0)
        self.layout_content.addWidget(self.gender, 1, 1, 1, 4)
        self.layout_content.addWidget(self.label_bp, 1, 6)
        self.layout_content.addWidget(self.line_bp, 1, 7, 1, 4)
        self.layout_content.addWidget(self.label_ad, 2, 0)
        self.layout_content.addWidget(self.age_at_diagnosis, 2, 1, 1, 4)
        self.layout_content.addWidget(self.label_dx_year, 2, 6)
        self.layout_content.addWidget(self.line_Dx_Year, 2, 7, 1, 4)
        self.layout_content.addWidget(self.label_icd, 3, 0)
        self.layout_content.addWidget(self.line_icd, 3, 1, 1, 9)
        self.layout_content.addWidget(self.label_histology, 4, 0)
        self.layout_content.addWidget(self.line_histology, 4, 1, 1, 8)
        self.layout_content.addWidget(self.label_t_stage, 5, 0)
        self.layout_content.addWidget(self.t_stage, 5, 1)
        self.layout_content.addWidget(self.label_n_Stage, 5, 3)
        self.layout_content.addWidget(self.n_stage, 5, 4)
        self.layout_content.addWidget(self.label_m_Stage, 5, 6)
        self.label_m_Stage.setAlignment(
            QtCore.Qt.AlignCenter | QtCore.Qt.AlignCenter)
        self.layout_content.addWidget(self.m_stage, 5, 7)
        self.layout_content.addWidget(self.label_overall_stage, 5, 9)
        self.layout_content.addWidget(self.overall_stage, 5, 10)
        self.layout_content.addWidget(self.label_tx_intent, 6, 0)
        self.layout_content.addWidget(self.tx_intent, 6, 1, 1, 4)
        self.layout_content.addWidget(self.label_surgery, 7, 0)
        self.layout_content.addWidget(self.surgery, 7, 1, 1, 4)
        self.layout_content.addWidget(self.label_rad, 7, 6)
        self.layout_content.addWidget(self.rad, 7, 7, 1, 4)
        self.layout_content.addWidget(self.label_chemo, 8, 0)
        self.layout_content.addWidget(self.chemo, 8, 1, 1, 4)
        self.layout_content.addWidget(self.label_immuno, 8, 6)
        self.layout_content.addWidget(self.immuno, 8, 7, 1, 4)
        self.layout_content.addWidget(self.label_brachy, 9, 0)
        self.layout_content.addWidget(self.brachy, 9, 1, 1, 4)
        self.layout_content.addWidget(self.label_hormone, 9, 6)
        self.layout_content.addWidget(self.hormone, 9, 7, 1, 4)
        self.layout_content.addWidget(self.label_sd, 10, 0)
        self.layout_content.addWidget(self.survival_duration, 10, 1, 1, 4)
        self.layout_content.addWidget(self.label_death, 11, 0)
        self.layout_content.addWidget(self.death, 11, 1, 1, 4)
        self.layout_content.addWidget(self.label_cancer_death, 11, 6)
        self.layout_content.addWidget(self.cancer_death, 11, 7, 1, 4)
        self.layout_content.addWidget(self.label_lcd, 12, 0)
        self.layout_content.addWidget(self.lc_duration, 12, 1, 1, 2)
        self.layout_content.addWidget(self.label_rcd, 12, 4)
        self.layout_content.addWidget(self.rc_duration, 12, 5, 1, 2)
        self.layout_content.addWidget(self.label_dcd, 12, 8)
        self.layout_content.addWidget(self.dc_duration, 12, 9, 1, 2)
        self.layout_content.addWidget(self.label_Local_control, 13, 0)
        self.layout_content.addWidget(self.Local_control, 13, 1, 1, 4)
        self.layout_content.addWidget(self.label_dt_Local_failure, 13, 6)
        self.layout_content.addWidget(self.dt_local_failure, 13, 7, 1, 4)
        self.layout_content.addWidget(self.label_regional_control, 14, 0)
        self.layout_content.addWidget(self.regional_control, 14, 1, 1, 4)
        self.layout_content.addWidget(self.label_dt_regional_failure, 14, 6)
        self.layout_content.addWidget(self.dt_regional_failure, 14, 7, 1, 4)
        self.layout_content.addWidget(self.label_distant_control, 15, 0)
        self.layout_content.addWidget(self.distant_control, 15, 1, 1, 4)
        self.layout_content.addWidget(self.label_dt_distant_failure, 15, 6)
        self.layout_content.addWidget(self.dt_distant_failure, 15, 7, 1, 4)
        self.layout_content.addWidget(self.edit_button, 16, 0)

        self.scrollArea_cd.setWidget(self.scrollAreaWidgetContents)

        self.layout = QtWidgets.QHBoxLayout(self.tabWindow)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.scrollArea_cd)

    def create_note(self):
        """
        Create a note to tell the user a csv file containing Clinical Data is
        found.
        """
        self.note = QtWidgets.QLabel()

    def add_gender(self):
        """
        Create gender components.
        """
        self.label_gender = QtWidgets.QLabel()
        self.gender = QtWidgets.QComboBox()
        self.gender.addItem("")
        self.gender.addItem("")
        self.gender.addItem("")
        self.gender.addItem("")

    def add_birth_place(self):
        """
        Create birth place components.
        """
        self.label_bp = QtWidgets.QLabel()
        self.line_bp = QtWidgets.QLineEdit()
        completer = QCompleter(data, self.line_bp)
        completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self.line_bp.setCompleter(completer)

    def add_age_at_diagnosis(self):
        """
        Create age at diagnosis components.
        """
        self.label_ad = QtWidgets.QLabel()
        self.age_at_diagnosis = QtWidgets.QLineEdit()

    def add_dx_year(self):
        """
        Create Dx year components.
        """
        self.label_dx_year = QtWidgets.QLabel()
        self.line_Dx_Year = QtWidgets.QLineEdit()

    def add_icd(self):
        """
        Create ICD10 components.
        """
        self.label_icd = QtWidgets.QLabel()
        self.line_icd = QtWidgets.QLineEdit()
        completer_5 = QCompleter(new_icd, self.line_icd)
        completer_5.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        completer_5.setFilterMode(QtCore.Qt.MatchContains)
        self.line_icd.setCompleter(completer_5)

    def add_histology(self):
        """
        Create histology components.
        """
        self.label_histology = QtWidgets.QLabel()
        self.line_histology = QtWidgets.QLineEdit()
        completer_4 = QCompleter(new_hist, self.line_histology)
        completer_4.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        completer_4.setFilterMode(QtCore.Qt.MatchContains)
        self.line_histology.setCompleter(completer_4)

    def add_t_stage(self):
        """
        Create T stage components.
        """
        self.label_t_stage = QtWidgets.QLabel()
        self.t_stage = QtWidgets.QComboBox()
        self.t_stage.addItem("")
        self.t_stage.addItem("")
        self.t_stage.addItem("")
        self.t_stage.addItem("")
        self.t_stage.addItem("")
        self.t_stage.addItem("")
        self.t_stage.addItem("")

    def add_n_stage(self):
        """
        Create N stage components.
        """
        self.label_n_Stage = QtWidgets.QLabel()
        self.n_stage = QtWidgets.QComboBox()
        self.n_stage.addItem("")
        self.n_stage.addItem("")
        self.n_stage.addItem("")
        self.n_stage.addItem("")
        self.n_stage.addItem("")

    def add_m_stage(self):
        """
        Create M stage components.
        """
        self.label_m_Stage = QtWidgets.QLabel()
        self.m_stage = QtWidgets.QComboBox()
        self.m_stage.addItem("")
        self.m_stage.addItem("")
        self.m_stage.addItem("")

    def add_overall_stage(self):
        """
        Create overall stage components.
        """
        self.label_overall_stage = QtWidgets.QLabel()
        self.overall_stage = QtWidgets.QComboBox()
        self.overall_stage.addItem("")
        self.overall_stage.addItem("")
        self.overall_stage.addItem("")
        self.overall_stage.addItem("")
        self.overall_stage.addItem("")
        self.overall_stage.addItem("")
        self.overall_stage.addItem("")
        self.overall_stage.addItem("")
        self.overall_stage.addItem("")
        self.overall_stage.addItem("")
        self.overall_stage.addItem("")
        self.overall_stage.addItem("")
        self.overall_stage.addItem("")
        self.overall_stage.addItem("")
        self.overall_stage.addItem("")
        self.overall_stage.addItem("")

    def add_tx_intent(self):
        """
        Create tx intent components.
        """
        self.tx_intent = QtWidgets.QComboBox()
        self.tx_intent.addItem("")
        self.tx_intent.addItem("")
        self.tx_intent.addItem("")
        self.tx_intent.addItem("")
        self.tx_intent.addItem("")
        self.tx_intent.addItem("")
        self.label_tx_intent = QtWidgets.QLabel()

    def add_surgery(self):
        """
        Create surgery components.
        """
        self.label_surgery = QtWidgets.QLabel()
        self.surgery = QtWidgets.QComboBox()
        self.surgery.addItem("")
        self.surgery.addItem("")
        self.surgery.addItem("")
        self.surgery.addItem("")
        self.surgery.addItem("")
        self.surgery.addItem("")
        self.surgery.addItem("")
        self.surgery.addItem("")
        self.surgery.addItem("")
        self.surgery.addItem("")
        self.surgery.addItem("")
        self.surgery.addItem("")
        self.surgery.addItem("")

    def add_rad(self):
        """
        Create rad components.
        """
        self.label_rad = QtWidgets.QLabel()
        self.rad = QtWidgets.QComboBox()
        self.rad.addItem("")
        self.rad.addItem("")
        self.rad.addItem("")
        self.rad.addItem("")
        self.rad.addItem("")
        self.rad.addItem("")
        self.rad.addItem("")
        self.rad.addItem("")
        self.rad.addItem("")
        self.rad.addItem("")
        self.rad.addItem("")
        self.rad.addItem("")
        self.rad.addItem("")

    def add_immuno(self):
        """
        Create immuno components.
        """
        self.label_immuno = QtWidgets.QLabel()
        self.immuno = QtWidgets.QComboBox()
        self.immuno.addItem("")
        self.immuno.addItem("")
        self.immuno.addItem("")
        self.immuno.addItem("")
        self.immuno.addItem("")
        self.immuno.addItem("")
        self.immuno.addItem("")
        self.immuno.addItem("")
        self.immuno.addItem("")
        self.immuno.addItem("")
        self.immuno.addItem("")
        self.immuno.addItem("")
        self.immuno.addItem("")

    def add_chemo(self):
        """
        Create chemo components.
        """
        self.chemo = QtWidgets.QComboBox()
        self.chemo.addItem("")
        self.chemo.addItem("")
        self.chemo.addItem("")
        self.chemo.addItem("")
        self.chemo.addItem("")
        self.chemo.addItem("")
        self.chemo.addItem("")
        self.chemo.addItem("")
        self.chemo.addItem("")
        self.chemo.addItem("")
        self.chemo.addItem("")
        self.chemo.addItem("")
        self.chemo.addItem("")
        self.label_chemo = QtWidgets.QLabel()

    def add_hormone(self):
        """
        Create hormone components.
        """
        self.label_hormone = QtWidgets.QLabel()
        self.hormone = QtWidgets.QComboBox()
        self.hormone.addItem("")
        self.hormone.addItem("")
        self.hormone.addItem("")
        self.hormone.addItem("")
        self.hormone.addItem("")
        self.hormone.addItem("")
        self.hormone.addItem("")
        self.hormone.addItem("")
        self.hormone.addItem("")
        self.hormone.addItem("")
        self.hormone.addItem("")
        self.hormone.addItem("")
        self.hormone.addItem("")

    def add_brachy(self):
        """
        Create brachy components.
        """
        self.label_brachy = QtWidgets.QLabel()
        self.brachy = QtWidgets.QComboBox()
        self.brachy.addItem("")
        self.brachy.addItem("")
        self.brachy.addItem("")
        self.brachy.addItem("")
        self.brachy.addItem("")
        self.brachy.addItem("")
        self.brachy.addItem("")
        self.brachy.addItem("")
        self.brachy.addItem("")
        self.brachy.addItem("")
        self.brachy.addItem("")
        self.brachy.addItem("")
        self.brachy.addItem("")

    def add_survival_duration(self):
        """
        Create survival duration components.
        """
        self.label_sd = QtWidgets.QLabel()
        self.survival_duration = QtWidgets.QLineEdit()

    def add_cancer_death(self):
        """
        Create cancer death components.
        """
        self.label_cancer_death = QtWidgets.QLabel()
        self.cancer_death = QtWidgets.QComboBox()
        self.cancer_death.addItem("")
        self.cancer_death.addItem("")
        self.cancer_death.addItem("")


    def add_death(self):
        """
        Create death components.
        """
        self.label_death = QtWidgets.QLabel()
        self.death = QtWidgets.QComboBox()
        self.death.addItem("")
        self.death.addItem("")
        self.death.addItem("")

    def add_local_control_duration(self):
        """
        Create local control duration components.
        """
        self.label_lcd = QtWidgets.QLabel()
        self.lc_duration = QtWidgets.QLineEdit()

    def add_regional_control_duration(self):
        """
        Create regional control duration components.
        """
        self.label_rcd = QtWidgets.QLabel()
        self.rc_duration = QtWidgets.QLineEdit()

    def add_distance_control_duration(self):
        """
        Create distance control duration components.
        """
        self.label_dcd = QtWidgets.QLabel()
        self.dc_duration = QtWidgets.QLineEdit()

    def add_regional_control(self):
        """
        Create regional control components.
        """
        self.label_regional_control = QtWidgets.QLabel()
        self.regional_control = QtWidgets.QComboBox()
        self.regional_control.addItem("")
        self.regional_control.addItem("")
        self.regional_control.addItem("")

    def add_distant_control(self):
        """
        Create distant control components.
        """
        self.label_distant_control = QtWidgets.QLabel()
        self.distant_control = QtWidgets.QComboBox()
        self.distant_control.addItem("")
        self.distant_control.addItem("")
        self.distant_control.addItem("")

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
        self.label_dt_Local_failure = QtWidgets.QLabel()
        self.dt_local_failure = QtWidgets.QDateEdit()
        self.dt_local_failure.setDisplayFormat("dd/MM/yyyy")
        self.dt_local_failure.setCalendarPopup(True)
        self.dt_local_failure.setDisabled(True)

    def add_date_regional_failure(self):
        """
        Create date regional failure components.
        """
        self.label_dt_regional_failure = QtWidgets.QLabel()
        self.dt_regional_failure = QtWidgets.QDateEdit()
        self.dt_regional_failure.setDisplayFormat("dd/MM/yyyy")
        self.dt_regional_failure.setCalendarPopup(True)
        self.dt_regional_failure.setDisabled(True)

    def add_date_distant_failure(self):
        """
        Create date distant failure components.
        """
        self.dt_distant_failure = QtWidgets.QDateEdit()
        self.dt_distant_failure.setDisplayFormat("dd/MM/yyyy")
        self.dt_distant_failure.setCalendarPopup(True)
        self.dt_distant_failure.setDisabled(True)
        self.label_dt_distant_failure = QtWidgets.QLabel()

    def create_edit_button(self):
        """
        Create Edit button.
        """
        self.edit_button = QtWidgets.QPushButton()
        self.edit_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        icon_edit = QtGui.QIcon()
        icon_edit.addPixmap(
            QtGui.QPixmap(resource_path('res/images/btn-icons/draw_icon.png')),
            QtGui.QIcon.Normal,
            QtGui.QIcon.On
        )
        self.edit_button.setIcon(icon_edit)
