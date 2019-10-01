import sys
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import QMessageBox
import glob
import re
from src.View.mainPage import *
from src.View.openpage import WelcomePage
from src.Model.CalculateImages import *
from src.Model.LoadPatients import *
from src.Model.form_UI import *

message = ""

def calculate_years(year1, year2):
    return year2.year() - year1.year() - ((year2.month(), year2.day()) < (year1.month(), year1.day()))


class Welcome(QtWidgets.QMainWindow, WelcomePage):
    open_patient_window = QtCore.pyqtSignal(str)

    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.setupUi(self)

        self.pushButton.clicked.connect(self.patientHandler)

    def patientHandler(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(None, 'Select patient folder...', '/home')
        self.open_patient_window.emit(path)


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    open_patient_window = QtCore.pyqtSignal(str)

    def __init__(self, path):
        QtWidgets.QMainWindow.__init__(self)
       # self.path = path
        self.setupUi(self, path)

        self.actionOpen.triggered.connect(self.patientHandler)

    def patientHandler(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(None, 'Select patient folder...', '/home')
        self.open_patient_window.emit(path)



class Controller:

    def __init__(self):
        pass

    def show_welcome(self):
        self.welcome_window = Welcome()
        self.welcome_window.open_patient_window.connect(self.show_patient)
        self.welcome_window.show()


    def show_patient(self, path):
        self.patient_window = MainWindow(path)
        self.patient_window.open_patient_window.connect(self.show_patient)
        self.welcome_window.close()
        if self.patient_window.isVisible():
            self.patient_window.close()
        self.patient_window.show()


