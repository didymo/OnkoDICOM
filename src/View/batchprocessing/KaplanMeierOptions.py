import platform
from PySide6 import QtWidgets
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QComboBox, QLabel
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
        # creates layouts
        self.target_layout = QtWidgets.QFormLayout()
        self.duration_layout = QtWidgets.QFormLayout()
        self.alive_or_dead_layout = QtWidgets.QFormLayout()

        # target column widgets
        self.combobox_target = QComboBox()
        self.combobox_target.setStyleSheet(self.stylesheet)
        target_label = QtWidgets.QLabel(
            "Target Column")
        target_label.setStyleSheet(self.stylesheet)
        self.target_layout.addWidget(target_label)
        self.target_layout.addRow(self.combobox_target)

        # life duration widgets
        self.combobox_duration = QComboBox()
        self.combobox_duration.setStyleSheet(self.stylesheet)
        duration_label = QtWidgets.QLabel(
            "Duration of Life Column")
        duration_label.setStyleSheet(self.stylesheet)
        self.duration_layout.addWidget(duration_label)
        self.duration_layout.addRow(self.combobox_duration)

        # alive or dead widgets
        self.combobox_alive_or_dead = QComboBox()
        self.combobox_alive_or_dead.setStyleSheet(self.stylesheet)
        alive_or_dead_label = QtWidgets.QLabel(
            "Alive or Dead Column")
        alive_or_dead_label.setStyleSheet(self.stylesheet)
        self.alive_or_dead_layout.addWidget(alive_or_dead_label)
        self.alive_or_dead_layout.addRow(self.combobox_alive_or_dead)

        # adds Layout
        self.main_layout.addLayout(self.target_layout)
        self.main_layout.addLayout(self.duration_layout)
        self.main_layout.addLayout(self.alive_or_dead_layout)
        self.setLayout(self.main_layout)

    def store_data(self, data_dic):
        """
                Gets User Selected Columns
        """
        self.data_dictionary = data_dic
        self.combobox_target.addItems(self.data_dictionary.keys())
        self.combobox_duration.addItems(self.data_dictionary.keys())
        self.combobox_alive_or_dead.addItems(self.data_dictionary.keys())

    def get_target_col(self):
        return self.combobox_target.currentText()

    def get_duration_of_life_col(self):
        return self.combobox_duration.currentText()

    def get_alive_or_dead_col(self):
        return self.combobox_alive_or_dead.currentText()

class plot_window(QtWidgets.QWidget):
    """
        ClinicalData-SR2CSV options for batch processing.
        """

    def __init__(self, image_path):

        QtWidgets.QWidget.__init__(self)
        self.dataDictionary = {}
        self.image_path = image_path

        # Create the main layout
        self.main_layout = QtWidgets.QVBoxLayout()

        # Get the stylesheet
        if platform.system() == 'Darwin':
            self.stylesheet_path = "res/stylesheet.qss"
        else:
            self.stylesheet_path = "res/stylesheet-win-linux.qss"
        self.stylesheet = open(resource_path(self.stylesheet_path)).read()

        label = QLabel(self)
        pximap = QPixmap("")



