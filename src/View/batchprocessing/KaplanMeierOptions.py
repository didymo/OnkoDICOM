import platform
from PySide6 import QtWidgets
from PySide6.QtWidgets import QComboBox
from src.Controller.PathHandler import resource_path

class KaplanMeierOptions(QtWidgets.QWidget):
    """
    ClinicalData-SR2CSV options for batch processing.
    """

    def __init__(self):

        QtWidgets.QWidget.__init__(self)
        self.dataDictionary = {}

        # Create the main layout
        self.main_layout = QtWidgets.QVBoxLayout()

        # Button layout
        self.button_layout = QtWidgets.QHBoxLayout()

        # Get the stylesheet
        if platform.system() == 'Darwin':
            self.stylesheet_path = "res/stylesheet.qss"
        else:
            self.stylesheet_path = "res/stylesheet-win-linux.qss"
        self.stylesheet = open(resource_path(self.stylesheet_path)).read()

        # Info messages
        self.message = QtWidgets.QLabel(
            "No files located in current selected directory"
        )
        #creates layouts
        self.target_layout = QtWidgets.QFormLayout()
        self.duration_layout = QtWidgets.QFormLayout()
        self.AliveOrDead_layout = QtWidgets.QFormLayout()

        # target column widgets
        self.comboboxTarget = QComboBox()
        self.comboboxTarget.setStyleSheet(self.stylesheet)
        targetLabel = QtWidgets.QLabel(
            "Target Column")
        targetLabel.setStyleSheet(self.stylesheet)
        self.target_layout.addWidget(targetLabel)
        self.target_layout.addRow(self.comboboxTarget)

        # life duration widgets
        self.comboboxDuration = QComboBox()
        self.comboboxDuration.setStyleSheet(self.stylesheet)
        DurationLabel = QtWidgets.QLabel(
            "Duration of Life Column")
        DurationLabel.setStyleSheet(self.stylesheet)
        self.duration_layout.addWidget(DurationLabel)
        self.duration_layout.addRow(self.comboboxDuration)

        # alive or dead widgets
        self.comboboxAliveOrDead = QComboBox()
        self.comboboxAliveOrDead.setStyleSheet(self.stylesheet)
        AliveOrDeadLabel = QtWidgets.QLabel(
            "Alive or Dead Column")
        AliveOrDeadLabel.setStyleSheet(self.stylesheet)
        self.AliveOrDead_layout.addWidget(AliveOrDeadLabel)
        self.AliveOrDead_layout.addRow(self.comboboxAliveOrDead)

        #adds Layout
        self.main_layout.addLayout(self.target_layout)
        self.main_layout.addLayout(self.duration_layout)
        self.main_layout.addLayout(self.AliveOrDead_layout)
        self.setLayout(self.main_layout)

    def store_data(self, dataDic):
        """
                Gets User Selected Columns
        """
        self.dataDictionary = dataDic
        self.comboboxTarget.addItems(self.dataDictionary.keys())
        self.comboboxDuration.addItems(self.dataDictionary.keys())
        self.comboboxAliveOrDead.addItems(self.dataDictionary.keys())

    def getTargetCol(self):
        return self.comboboxTarget.currentText()

    def getDurationOfLifeCol(self):
        return self.comboboxDuration.currentText()

    def getAliveOrDeadCol(self):
        return self.comboboxAliveOrDead.currentText()
