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

message = ""

def calculate_years(year1, year2):
    return year2.year() - year1.year() - ((year2.month(), year2.day()) < (year1.month(), year1.day()))

class ProgressBar(QtWidgets.QWidget):
    open_patient_window = QtCore.pyqtSignal(str)
    open_welcome_window = QtCore.pyqtSignal()

    def __init__(self,path):
        super().__init__()

        # Instance attribute defined later in on_button_click()
        self.ext = None
        self.path = path
        self.w = QtWidgets.QWidget()
        self.setWindowTitle("Opening patient")
        qtRectangle = self.w.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.w.move(qtRectangle.topLeft())

        self.setGeometry(300, 300, 360, 100)
        self.label = QtWidgets.QLabel(self)
        self.label.setGeometry(30,15,300,20)
        self.progress_bar = QtWidgets.QProgressBar(self)
        self.progress_bar.setGeometry(30, 40, 300, 25)
        self.progress_bar.setMaximum(100)
        self.ext = Extended(path)
        self.ext.copied_percent_signal.connect(self.on_count_change)
        self.ext.missing_files_signal.connect(self.on_missing_files)
        self.ext.incorrect_directory_signal.connect(self.on_incorrect_directory)
        self.ext.start()


    def on_count_change(self, value):
        if value in range(0,30):
            self.label.setText("Importing patient data...")
        elif value in range(30,70):
            self.label.setText("Calculating the DVH...")
        elif value in range (70,85):
            self.label.setText("Loading patient...")
        elif value in range (85,100):
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


class Welcome(QtWidgets.QMainWindow, WelcomePage):
    # If patient directory selected, open patient display window
    open_patient_window = QtCore.pyqtSignal(str)

    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.setupUi(self)
        self.pushButton.clicked.connect(self.patientHandler)

    def patientHandler(self):
        # Browse directories
        path = QtWidgets.QFileDialog.getExistingDirectory(None, 'Select patient folder...', '')
        self.open_patient_window.emit(path)


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    # When a new patient file is opened from the main window
    open_patient_window = QtCore.pyqtSignal(str)

    def __init__(self, path, dataset, filepaths, rois, raw_dvh, dvhxy):
        QtWidgets.QMainWindow.__init__(self)
        self.setupUi(self, path, dataset, filepaths, rois, raw_dvh, dvhxy )
        self.actionOpen.triggered.connect(self.patientHandler)

    def patientHandler(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(None, 'Select patient folder...', '/home')
        self.open_patient_window.emit(path)



class Controller:

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
        self.bar_window.open_patient_window.connect(self.show_patient)
        self.bar_window.open_welcome_window.connect(self.show_welcome)
        self.bar_window.show()

    # Display patient data 
    def show_patient(self, path):
        self.patient_window = MainWindow(path, self.bar_window.ext.read_data_dict, self.bar_window.ext.file_names_dict, self.bar_window.ext.rois, self.bar_window.ext.raw_dvh, self.bar_window.ext.dvh_x_y)
        self.patient_window.open_patient_window.connect(self.show_bar)
        self.bar_window.close() 
        self.patient_window.show()


