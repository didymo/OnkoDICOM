from shutil import which

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QMessageBox

from src.View.Main_Page.mainPage import Ui_MainWindow
from src.View.welcome_page import UIWelcomeWindow
from src.View.open_patient import UIOpenPatientWindow


class WelcomeWindow(QtWidgets.QMainWindow, UIWelcomeWindow):

    go_next_window = QtCore.pyqtSignal()

    # Initialisation function to display the UI
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.setup_ui(self)
        self.push_button.clicked.connect(self.go_open_patient_window)

    def go_open_patient_window(self):
        """
        Function to progress to the OpenPatientWindow
        """
        self.go_next_window.emit()


class OpenPatientWindow(QtWidgets.QMainWindow, UIOpenPatientWindow):

    go_next_window = QtCore.pyqtSignal(tuple)

    # Initialisation function to display the UI
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.setup_ui(self)
        self.patient_info_initialized.connect(self.open_patient)

    def open_patient(self, patient_attributes):
        self.go_next_window.emit(patient_attributes)


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):

    # When a new patient file is opened from the main window
    open_patient_window = QtCore.pyqtSignal()
    # When the pyradiomics button is pressed
    run_pyradiomics = QtCore.pyqtSignal(str, dict, str)

    # Initialising the main window and setting up the UI
    def __init__(self, patient_dict_container):
        QtWidgets.QMainWindow.__init__(self)
        self.setupUi(self, patient_dict_container)
        self.menu_bar.actionOpen.triggered.connect(self.open_new_patient)
        self.menu_bar.actionPyradiomics.triggered.connect(self.pyradiomics_handler)
        self.pyradi_trigger.connect(self.pyradiomics_handler)

    def open_new_patient(self):
        """
        Function to handle the Open patient button being clicked
        """
        confirmation_dialog = QMessageBox.information(self, 'Open new patient?',
                                                    'Opening a new patient will close the currently opened patient. '
                                                    'Would you like to continue?',
                                                    QMessageBox.Yes | QMessageBox.No)

        if confirmation_dialog == QMessageBox.Yes:
            self.open_patient_window.emit()

    def pyradiomics_handler(self):
        """
        Sends signal to initiate pyradiomics analysis
        """
        if which('plastimatch') is not None:
            if self.hashed_path == '':
                confirm_pyradi = QMessageBox.information(self, "Confirmation",
                                                    "Are you sure you want to perform pyradiomics? "
                                                    "Once started the process cannot be terminated until it finishes.",
                                                    QMessageBox.Yes, QMessageBox.No)
                if confirm_pyradi == QMessageBox.Yes:
                    self.run_pyradiomics.emit(self.path, self.filepaths, self.hashed_path)
                if confirm_pyradi == QMessageBox.No:
                    pass
            else:
                self.run_pyradiomics.emit(self.path, self.filepaths, self.hashed_path)
        else:
            exe_not_found = QMessageBox.information(self, "Error",
                                                 "Plastimatch not installed. Please install Plastimatch "
                                                 "(https://sourceforge.net/projects/plastimatch/) to carry out "
                                                 "pyradiomics analysis.")
