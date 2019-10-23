#####################################################################################################################
#                                                                                                                   #
#   This file handles all the processes done when opening a new patient or opening the program for the first time   #
#                                                                                                                   #
#####################################################################################################################
import sys
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import QMessageBox, QDesktopWidget
import glob
import re
from src.View.mainPage import *
from src.View.openpage import WelcomePage
from src.Model.CalculateImages import *
from src.Model.LoadPatients import *
from src.Model.form_UI import *
from src.View.ProgressBar import *

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

    #initialisation function
    def __init__(self, path):
        super().__init__()

        # Instance attribute defined later in on_button_click()
        self.ext = None
        self.path = path
        # Creating the UI of the progress bar
        self.w = QtWidgets.QWidget()
        self.setWindowTitle("Opening patient")
        qtRectangle = self.w.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.w.move(qtRectangle.topLeft())
        self.setGeometry(300, 300, 360, 100)
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
        #start the loading of the patient
        self.ext.start()

    # this function is responsible for updating the bar % and the label
    def on_count_change(self, value):
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

    # If selected directory does not contain DICOM files
    def on_incorrect_directory(self):
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

    # Function to handle the Open patient button being clicked
    def patientHandler(self):
        # Browse directories
        path = QtWidgets.QFileDialog.getExistingDirectory(
            None, 'Select patient folder...', '')
        self.open_patient_window.emit(path)

#####################################################################################################################
#                                                                                                                   #
#   This class creates an instance of the Main Window Page of OnkoDICOM                                             #
#                                                                                                                   #
#####################################################################################################################

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    # When a new patient file is opened from the main window
    open_patient_window = QtCore.pyqtSignal(str)

    # Initialising the main window and setting up the UI
    def __init__(self, path, dataset, filepaths, rois, raw_dvh, dvhxy, raw_contour, num_points, pixluts):
        QtWidgets.QMainWindow.__init__(self)
        self.setupUi(self, path, dataset, filepaths, rois, raw_dvh,
                     dvhxy, raw_contour, num_points, pixluts)
        self.actionOpen.triggered.connect(self.patientHandler)

    # Function to handle the Open patient button being clicked
    def patientHandler(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(
            None, 'Select patient folder...', '/home')
        self.open_patient_window.emit(path)

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

    # Display welcome page
    def show_welcome(self):
        # If an error was displayed, close existing progress bar window
        if self.bar_window.isVisible():
            self.bar_window.close()
        self.welcome_window = Welcome()
        # After this window the progress bar will be displayed if a path is provided
        self.welcome_window.open_patient_window.connect(self.show_bar)
        self.welcome_window.show()

    # Display progress bar
    def show_bar(self, path):
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

    # Display patient data
    def show_patient(self, path):
        #Loads the main window  by providing the necessary data obtained by the progress bar
        self.patient_window = MainWindow(path, self.bar_window.ext.read_data_dict, self.bar_window.ext.file_names_dict,
                                         self.bar_window.ext.rois, self.bar_window.ext.raw_dvh,
                                         self.bar_window.ext.dvh_x_y, self.bar_window.ext.dict_raw_ContourData,
                                         self.bar_window.ext.dict_NumPoints, self.bar_window.ext.dict_pixluts)
        self.patient_window.open_patient_window.connect(self.show_bar)
        self.bar_window.close()
        self.patient_window.show()
