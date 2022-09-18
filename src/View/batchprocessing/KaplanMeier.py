import platform
from PySide6 import QtWidgets
import kaplanmeier as km
import matplotlib.pyplot as plt
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

        # Dropdown list
        self.combobox = QComboBox()

        #self.patien

        self.main_layout.addWidget(self.combobox)
        self.setLayout(self.main_layout)

    #def show_headings_options(self, headings):

    def store_data(self, dataDic):
        self.dataDictionary = dataDic
        self.combobox.addItems(self.dataDictionary.keys())

    def getTargetCol(self):
        return self.combobox.currentText()

    def getDurationOfLifeCol(self):
        return self.combobox.currentText()

    def getAliveOrDeadCol(self):
        return self.combobox.currentText()
