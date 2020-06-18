#####################################################################################################################
#                                                                                                                   #
#   This file holds all the user input pop up dialogs used from the software                                        #
#                                                                                                                   #
#####################################################################################################################
import re
import sys
from PyQt5 import QtGui
from PyQt5.QtWidgets import QTableWidgetItem, QLabel, QDialogButtonBox, QVBoxLayout, QFormLayout, QSpinBox, QLineEdit, \
    QDialog, \
    QComboBox, QGroupBox, QMessageBox, QPlainTextEdit

#####################################################################################################################
#                                                                                                                   #
#   This class creates the user input dialog for when Modifying or Adding a Windowing option                        #
#                                                                                                                   #
#####################################################################################################################

class Dialog_Windowing(QDialog):

    def __init__(self, winName, scan, ULevel, LLevel):
        super(Dialog_Windowing, self).__init__()

        #passing the current values if it is an existing option or empty if its a new one
        self.winName = winName
        self.setWindowIcon(QtGui.QIcon("res/Icon/DONE.png"))
        self.scan = scan
        self.ULevel = ULevel
        self.LLevel = LLevel

        #create the ui components for the inputs
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.name = QLineEdit()
        self.name.setText(self.winName)
        self.sc = QLineEdit()
        self.sc.setText(self.scan)
        self.ul = QLineEdit()
        self.ul.setText(self.ULevel)
        self.ll = QLineEdit()
        self.ll.setText(self.LLevel)
        layout = QFormLayout(self)
        layout.addRow(QLabel("Window Name:"), self.name)
        layout.addRow(QLabel("Scan:"), self.sc)
        layout.addRow(QLabel("Upper Value:"), self.ul)
        layout.addRow(QLabel("Lower Value:"), self.ll)
        layout.addWidget(buttonBox)
        buttonBox.accepted.connect(self.accepting)
        buttonBox.rejected.connect(self.reject)
        self.setWindowTitle("Image Windowing")

    # this function returns the user inputs in case of a OK being pressed
    def getInputs(self):
        return (self.name.text(), self.sc.text(), self.ul.text(), self.ll.text())

    # this function does the validation of the inputs and gives the corresponding errors if needed
    def accepting(self):

        #check that no mandatory input is empty
        if (self.name.text() != '' and self.sc.text() != '' and self.ul.text() != '' and self.ll.text() != ''):

            # check validation
            if re.match(r'^([\s\d]+)$', self.ul.text()) and re.match(r'^([\s\d]+)$', self.ll.text()):
                self.accept()

            # the level fields do not contain just numbers
            else:
                buttonReply = QMessageBox.warning(self, "Error Message",
                                                  "The level fields need to be numbers!", QMessageBox.Ok)
                if buttonReply == QMessageBox.Ok:
                    pass

        # atleast one input field was left empty
        else:
            buttonReply = QMessageBox.warning(self, "Error Message",
                                              "None of the fields should be empty!", QMessageBox.Ok)
            if buttonReply == QMessageBox.Ok:
                pass

#####################################################################################################################
#                                                                                                                   #
#   This class creates the user input dialog for when Modifying or Adding a Standard Organ name option              #
#                                                                                                                   #
#####################################################################################################################

class Dialog_Organ(QDialog):

    def __init__(self, Name, id, organ, url):
        super(Dialog_Organ, self).__init__()

        #passing the current values if it is an existing option or empty if its a new one
        self.name = Name
        self.setWindowIcon(QtGui.QIcon("res/Icon/DONE.png"))
        self.id = id
        self.org = organ
        self.url = url

        #creating the UI components
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.S_name = QLineEdit()
        self.S_name.setText(self.name)
        self.oID = QLineEdit()
        self.oID.setText(self.id)
        self.organ = QLineEdit()
        self.organ.setText(self.org)
        self._url = QLineEdit()
        self._url.setText(self.url)
        layout = QFormLayout(self)
        layout.addRow(QLabel("Standard Name:"), self.S_name)
        layout.addRow(QLabel("FMA ID:"), self.oID)
        layout.addRow(QLabel("Organ:"), self.organ)
        layout.addRow(QLabel("Url:"), self._url)
        layout.addWidget(buttonBox)
        buttonBox.accepted.connect(self.accepting)
        buttonBox.rejected.connect(self.reject)
        self.setWindowTitle("Standard Organ Names")

    # this function returns the user inputs in case of a OK being pressed
    def getInputs(self):
        return (self.S_name.text(), self.oID.text(), self.organ.text(), self._url.text())

    # this function does the validation of the inputs and gives the corresponding errors if needed
    def accepting(self):

        # check that no mandatory input is empty
        if (self.S_name.text() != '' and self.oID.text() != '' and self.organ.text() != ''):
            # check validation
            if re.match(r'^([\s\d]+)$', self.oID.text()):
                self.accept()

            # the FMA ID field do not contain just numbers
            else:
                buttonReply = QMessageBox.warning(self, "Error Message",
                                                  "The FMA ID field should to be a number!", QMessageBox.Ok)
                if buttonReply == QMessageBox.Ok:
                    pass

        # atleast one input field was left empty
        else:
            buttonReply = QMessageBox.warning(self, "Error Message",
                                              "None of the fields should be empty!", QMessageBox.Ok)
            if buttonReply == QMessageBox.Ok:
                pass

#####################################################################################################################
#                                                                                                                   #
#   This class creates the user input dialog for when Modifying or Adding a Standard Organ name option              #
#                                                                                                                   #
#####################################################################################################################

class Dialog_Volume(QDialog):

    def __init__(self, Name, volume):
        super(Dialog_Volume, self).__init__()

        # passing the current values if it is an existing option or empty if its a new one
        self.name = Name
        self.vol = volume

        # creating the ui components
        self.setWindowIcon(QtGui.QIcon("res/Icon/DONE.png"))
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.S_name = QLineEdit()
        self.S_name.setText(self.name)
        self.volume = QLineEdit()
        self.volume.setText(self.vol)
        layout = QFormLayout(self)
        layout.addRow(QLabel("Standard Name:"), self.S_name)
        layout.addRow(QLabel("Volume Name:"), self.volume)
        layout.addWidget(buttonBox)
        buttonBox.accepted.connect(self.accepting)
        buttonBox.rejected.connect(self.reject)
        self.setWindowTitle("Standard Volume Names")

    # this function returns the user inputs in case of a OK being pressed
    def getInputs(self):
        return (self.S_name.text(), self.volume.text())

    # this function does the validation of the inputs and gives the corresponding errors if needed
    def accepting(self):

        # check that no mandatory input is empty
        if (self.S_name.text() != '' and self.volume.text() != ''):
            self.accept()

        # atleast one input field was left empty
        else:
            buttonReply = QMessageBox.warning(self, "Error Message",
                                              "None of the fields should be empty!", QMessageBox.Ok)
            if buttonReply == QMessageBox.Ok:
                pass

#####################################################################################################################
#                                                                                                                   #
#   This class creates the user input dialog for when Modifying or Adding an ROI from ISODOSE  (FUTURE FEATURE)     #
#                                                                                                                   #
#####################################################################################################################

# class Dialog_Dose(QDialog):
#
#     def __init__(self, dose, notes):
#         super(Dialog_Dose, self).__init__()
#
#         self.dose = dose
#         self.notes = notes
#         self.setWindowIcon(QtGui.QIcon("res/Icon/DONE.png"))
#         buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
#         self.iso_dose = QLineEdit()
#         self.iso_dose.setText(self.dose)
#         self.iso_notes = QLineEdit()
#         self.iso_notes.setText(self.notes)
#
#         layout = QFormLayout(self)
#         layout.addRow(QLabel("Isodose Level (cCy):"), self.iso_dose)
#         layout.addRow(QLabel("Notes:"), self.iso_notes)
#         layout.addWidget(buttonBox)
#         buttonBox.accepted.connect(self.accepting)
#         buttonBox.rejected.connect(self.reject)
#         self.setWindowTitle("Standard Volume Names")
#
#     def getInputs(self):
#         return (self.iso_dose.text(), str('ISO' + self.iso_dose.text()), self.iso_notes.text())
#
#     def accepting(self):
#         if (self.iso_dose.text() != ''):
#             if re.match(r'^\d+$', self.iso_dose.text()):
#                 self.accept()
#             else:
#                 buttonReply = QMessageBox.warning(self, "Error Message",
#                                                   "The Isodose level should to be a number!", QMessageBox.Ok)
#                 if buttonReply == QMessageBox.Ok:
#                     pass
#         else:
#             buttonReply = QMessageBox.warning(self, "Error Message",
#                                               "The Isodose field should not be empty!", QMessageBox.Ok)
#             if buttonReply == QMessageBox.Ok:
#                 pass

#####################################################################################################################
#                                                                                                                   #
#   This class creates the user input dialog for checking the RxDose when loading a new patient                     #
#                                                                                                                   #
#####################################################################################################################

class Rxdose_Check(QDialog):

    def __init__(self, rxdose):
        super(Rxdose_Check, self).__init__()

        # add the file dose
        self.rxdose = rxdose

        #create the ui components
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.rxdose_display = QLineEdit()
        self.rxdose_display.setText(str(self.rxdose))
        self.setWindowIcon(QtGui.QIcon("res/Icon/DONE.png"))
        layout = QFormLayout(self)
        layout.addRow(QLabel("RxDose: "), self.rxdose_display)
        layout.addWidget(buttonBox)
        buttonBox.accepted.connect(self.accepting)
        buttonBox.rejected.connect(self.reject)
        self.setWindowTitle("Verify RxDose")

    # this function returns the user input in case of a OK being pressed
    def get_dose(self):
        return self.rxdose

    # this function does the validation of the input and gives the corresponding errors if needed
    def accepting(self):

        # check that no mandatory input is empty and a non number
        if (self.rxdose_display.text != '' and self.rxdose_display.text().isdigit()):
            self.rxdose = int(self.rxdose_display.text())
            self.accept()

        # the input is empty or a non positive number
        else:
            buttonReply = QMessageBox.warning(self, "Error Message",
                                              "RxDose must be a positive number!", QMessageBox.Ok)
            if buttonReply == QMessageBox.Ok:
                pass
