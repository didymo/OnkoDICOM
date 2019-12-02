#####################################################################################################################
#                                                                                                                   #
#   This file handles all the processes done when opening a new patient or opening the program for the first time   #
#                                                                                                                   #
#####################################################################################################################
import sys
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import QMessageBox, QDesktopWidget
from shutil import which
import glob
import re
from src.View.mainPage import *
from src.View.openpage import WelcomePage
from src.Model.CalculateImages import *
from src.Model.form_UI import *
from src.View.ProgressBar import *
from src.View.PyradiProgressBar import *

#####################################################################################################################
#                                                                                                                   #
#   This class creates an instance of the progress bar that is used while running pyradiomics                       #
#                                                                                                                   #
#####################################################################################################################

class PyradiProgressBar(QtWidgets.QWidget):
    progress_complete = QtCore.pyqtSignal()

    def __init__(self, path, filepaths, target_path):
        super().__init__()

        self.w = QtWidgets.QWidget()
        self.setWindowTitle("Running Pyradiomics")
        self.setWindowFlags(
            QtCore.Qt.Window |
            QtCore.Qt.CustomizeWindowHint |
            QtCore.Qt.WindowTitleHint |
            QtCore.Qt.WindowMinimizeButtonHint)
        qtRectangle = self.w.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.w.move(qtRectangle.topLeft())
        self.setWindowIcon(QtGui.QIcon("src/Icon/DONE.png"))

        self.setGeometry(300, 300, 460, 100)
        self.label = QtWidgets.QLabel(self)
        self.label.setGeometry(30, 15, 400, 20)
        self.progress_bar = QtWidgets.QProgressBar(self)
        self.progress_bar.setGeometry(30, 40, 400, 25)
        self.progress_bar.setMaximum(100)
        self.ext = PyradiExtended(path, filepaths, target_path)
        self.ext.copied_percent_signal.connect(self.on_update)
        self.ext.start()

    def on_update(self, value, text=''):
        """
        Update percentage and text of progress bar. 

        :param value:   Percentage value to be displayed

        :param text:    To display what ROI currently being processed
        """

        # When generating the nrrd file, the percentage starts at 0
        # and reaches 25
        if value == 0:
            self.label.setText("Generating nrrd file")
        # The segmentation masks are generated between the range 25 and 50
        elif value == 25:
            self.label.setText("Generating segmentation masks")
        # Above 50, pyradiomics analysis is carried out over each segmentation mask
        elif value in range(50, 100):
            self.label.setText("Calculating features for " + text)
        # Set the percentage value
        self.progress_bar.setValue(value)

        # When the percentage reaches 100, send a signal to close progress bar
        if value == 100:
            completion = QMessageBox.information(self, "Complete",
                                                 "Task has been completed successfully")
            self.progress_complete.emit()

#####################################################################################################################
#                                                                                                                   #
#   This class creates an instance of the progress bar that will load the patient into the system                   #
#                                                                                                                   #
#####################################################################################################################

class ProgressBar(QtWidgets.QWidget):
    # the signals send to the other windows
    # the patient one gets the path
    open_patient_window = QtCore.pyqtSignal(str)
    open_welcome_window = QtCore.pyqtSignal()

    # initialisation function
    def __init__(self, path):
        super().__init__()

        # Instance attribute defined later in on_button_click()
        self.ext = None
        self.path = path
        self.value = 0
        # Creating the UI of the progress bar
        self.w = QtWidgets.QWidget()
        self.setWindowTitle("Opening patient")
        self.setWindowIcon(QtGui.QIcon("src/Icon/DONE.png"))
        qtRectangle = self.w.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.w.move(qtRectangle.topLeft())
        self.setGeometry(300, 300, 360, 100)
        self.setFixedSize(360, 100)
        self.label = QtWidgets.QLabel(self)
        self.label.setGeometry(30, 15, 300, 20)
        self.progress_bar = QtWidgets.QProgressBar(self)
        self.progress_bar.setGeometry(30, 40, 300, 25)
        self.progress_bar.setMaximum(100)
        # Executing the progress bar by providing it with the path of the directory
        self.ext = Extended(path)
        # update the bar
        self.ext.copied_percent_signal.connect(self.on_count_change)
        # in case there are missing files
        self.ext.missing_files_signal.connect(self.on_missing_files)
        # in case the directory is not correct
        self.ext.incorrect_directory_signal.connect(
            self.on_incorrect_directory)
        # start the loading of the patient
        self.ext.start()

    def on_count_change(self, value):
        """
        Function responsible for updating the bar percentage and the label
        """
        if value in range(0, 30):
            self.label.setText("Importing patient data...")
        elif value in range(30, 70):
            self.label.setText("Calculating the DVH...")
        elif value in range(70, 85):
            self.label.setText("Loading patient...")
        elif value in range(85, 100):
            self.label.setText("Preparing the work space...")
        self.progress_bar.setValue(value)
        if value == 100:
            self.open_patient_window.emit(self.path)

    def on_incorrect_directory(self):
        """
        Displays an error if no valid DICOM files found
        """
        # Open welcome window
        self.open_welcome_window.emit()

        # Display error message
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Error")
        msg.setInformativeText('Invalid directory, no DICOM files found')
        msg.setWindowTitle("Error")
        msg.exec_()

    # If RTSS and RTDose files missing
    def on_missing_files(self, error):
        """
        Displays an error when the RT-Struct and RT-Dose files are missing from the patient directory
        """
        # Open welcome window
        self.open_welcome_window.emit()

        # Display error message
        # Error message highlights which file is missing
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText("Error")
        msg.setInformativeText(error)
        msg.setWindowTitle("Error")
        msg.exec_()

    # handles close event of progress bar mid processing
    def closeEvent(self, event):
        if self.progress_bar.value() < 100:
            self.ext.terminate()
            self.open_welcome_window.emit()

#####################################################################################################################
#                                                                                                                   #
#   This class creates an instance of the Welcome Page when firstly running the software                            #
#                                                                                                                   #
#####################################################################################################################


class Welcome(QtWidgets.QMainWindow, WelcomePage):
    # If patient directory selected, open patient display window
    open_patient_window = QtCore.pyqtSignal(str)

    # Initialisation function to display the UI
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.setupUi(self)
        self.pushButton.clicked.connect(self.patientHandler)

    def patientHandler(self):
        """
        Function to handle the Open patient button being clicked
        """
        # Browse directories
        path = QtWidgets.QFileDialog.getExistingDirectory(
            None, 'Select patient folder...', '')
        if (path != ''):
            self.open_patient_window.emit(path)


#####################################################################################################################
#                                                                                                                   #
#   This class creates an instance of the Main Window Page of OnkoDICOM                                             #
#                                                                                                                   #
#####################################################################################################################

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    # When a new patient file is opened from the main window
    open_patient_window = QtCore.pyqtSignal(str)
    # When the pyradiomics button is pressed
    run_pyradiomics = QtCore.pyqtSignal(str, dict, str)

    # Initialising the main window and setting up the UI
    def __init__(self, path, dataset, filepaths, rois, raw_dvh, dvhxy, raw_contour, num_points, pixluts):
        QtWidgets.QMainWindow.__init__(self)
        self.setupUi(self, path, dataset, filepaths, rois, raw_dvh,
                     dvhxy, raw_contour, num_points, pixluts)
        self.menu_bar.actionOpen.triggered.connect(self.patientHandler)
        self.menu_bar.actionPyradiomics.triggered.connect(self.pyradiomicsHandler)
        self.pyradi_trigger.connect(self.pyradiomicsHandler)

    def patientHandler(self):
        """
        Function to handle the Open patient button being clicked
        """
        path = QtWidgets.QFileDialog.getExistingDirectory(
            None, 'Select patient folder...', '/home')
        if (path != ''):
            self.open_patient_window.emit(path)

    def pyradiomicsHandler(self):
        """
        Sends signal to initiate pyradiomics analysis
        """
        if which('plastimatch') is not None:
            if self.hashed_path == '':
                confirm_pyradi = QMessageBox.information(self, "Confirmation",
                                                    "Are you sure you want to perform pyradiomics? Once started the process cannot be terminated until it finishes.",
                                                    QMessageBox.Yes, QMessageBox.No)
                if confirm_pyradi == QMessageBox.Yes:
                    self.run_pyradiomics.emit(self.path, self.filepaths, self.hashed_path)
                if confirm_pyradi == QMessageBox.No:
                    pass
            else:
                self.run_pyradiomics.emit(self.path, self.filepaths, self.hashed_path)
        else:
            exe_not_found = QMessageBox.information(self, "Error",
                                                 "Plastimatch not installed. Please install Plastimatch (https://sourceforge.net/projects/plastimatch/) to carry out pyradiomics analysis.")
        


#####################################################################################################################
#                                                                                                                   #
#   This class controlls which window to be shown at each time according to users requests                          #
#                                                                                                                   #
#####################################################################################################################

class Controller:

    # Initialisation function that creates an instance of each window
    def __init__(self):
        self.welcome_window = QtWidgets.QMainWindow()
        self.patient_window = QtWidgets.QMainWindow()
        self.bar_window = QtWidgets.QWidget()
        self.pyradi_progressbar = QtWidgets.QWidget()

    def show_welcome(self):
        """
        Display welcome page
        """
        # If an error was displayed, close existing progress bar window
        if self.bar_window.isVisible():
            self.bar_window.close()
        self.welcome_window = Welcome()
        # After this window the progress bar will be displayed if a path is provided
        self.welcome_window.open_patient_window.connect(self.show_bar)
        self.welcome_window.show()

    def show_bar(self, path):
        """
        Display progress bar
        """
        # Close all other open windows
        if self.welcome_window.isVisible():
            self.welcome_window.close()
        if self.patient_window.isVisible():
            self.patient_window.close()
        self.bar_window = ProgressBar(path)
        # Connects the bar with the two other windows
        self.bar_window.open_patient_window.connect(self.show_patient)
        self.bar_window.open_welcome_window.connect(self.show_welcome)
        self.bar_window.show()

    def show_patient(self, path):
        """
        Display patient data
        """
        # Loads the main window  by providing the necessary data obtained by the progress bar
        self.patient_window = MainWindow(path, self.bar_window.ext.read_data_dict, self.bar_window.ext.file_names_dict,
                                         self.bar_window.ext.rois, self.bar_window.ext.raw_dvh,
                                         self.bar_window.ext.dvh_x_y, self.bar_window.ext.dict_raw_ContourData,
                                         self.bar_window.ext.dict_NumPoints, self.bar_window.ext.dict_pixluts)
        self.patient_window.open_patient_window.connect(self.show_bar)
        self.patient_window.run_pyradiomics.connect(self.show_pyradi_progress)
        self.patient_window.menu_bar.actionExit.triggered.connect(
            self.patient_window.close)
        self.bar_window.close()
        if self.welcome_window.isVisible():
            self.welcome_window.close()
        self.patient_window.show()

    def show_pyradi_progress(self, path, filepaths, target_path):
        """
        Display pyradiomics progress bar
        """
        # confirm_pyradi = QMessageBox.information(self, "Confirmation",
        #                                          "Are you sure you want to perform pyradiomics? Once started the process cannot be terminated until it finishes.",
        #                                          QMessageBox.Yes, QMessageBox.No)
        # if confirm_pyradi == QMessageBox.Yes:
        self.pyradi_progressbar = PyradiProgressBar(
            path, filepaths, target_path)
        self.pyradi_progressbar.progress_complete.connect(
            self.close_pyradi_progress)
        self.pyradi_progressbar.show()
        # if confirm_pyradi == QMessageBox.No:
        #     pass

    def close_pyradi_progress(self):
        """
        Close pyradiomics progress bar
        """
        self.pyradi_progressbar.close()
