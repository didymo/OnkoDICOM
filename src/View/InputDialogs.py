"""This file holds all the user input pop up dialogs used from the software"""
import re

from PyQt5 import QtGui
from PyQt5.QtWidgets import QLabel, QDialogButtonBox, QFormLayout, QLineEdit, \
    QDialog, \
    QMessageBox
from src.Controller.PathHandler import resource_path

""" This class creates the user input dialog for when Modifying or Adding a Windowing option """

class Dialog_Windowing(QDialog):

    def __init__(self, win_name, scan, upper_level, lower_level):
        super(Dialog_Windowing, self).__init__()

        # Passing the current values if it is an existing option or empty if its a new one
        self.win_name = win_name
        self.setWindowIcon(QtGui.QIcon(resource_path("res/images/btn-icons/onkodicom_icon.png")))
        self.scan = scan
        self.upper_level = upper_level
        self.lower_level = lower_level

        # Create the ui components for the inputs
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.name = QLineEdit()
        self.name.setText(self.win_name)
        self.scan_text = QLineEdit()
        self.scan_text.setText(self.scan)
        self.upper_level_text = QLineEdit()
        self.upper_level_text.setText(self.upper_level)
        self.lower_level_text = QLineEdit()
        self.lower_level_text.setText(self.lower_level)
        layout = QFormLayout(self)
        layout.addRow(QLabel("Window Name:"), self.name)
        layout.addRow(QLabel("Scan:"), self.scan_text)
        layout.addRow(QLabel("Upper Value:"), self.upper_level_text)
        layout.addRow(QLabel("Lower Value:"), self.lower_level_text)
        layout.addWidget(button_box)
        button_box.accepted.connect(self.accepting)
        button_box.rejected.connect(self.reject)
        self.setWindowTitle("Image Windowing")

    # This function returns the user inputs in case of a OK being pressed
    def getInputs(self):
        return (self.name.text(), self.scan_text.text(), self.upper_level_text.text(), self.lower_level_text.text())

    # This function does the validation of the inputs and gives the corresponding errors if needed
    def accepting(self):

        # Check that no mandatory input is empty
        if self.name.text() != '' and self.scan_text.text() != '' and self.upper_level_text.text() != '' and self.lower_level_text.text() != '':

            # Check validation
            if re.match(r'^([\s\d]+)$', self.upper_level_text.text()) and re.match(r'^([\s\d]+)$',
                                                                                   self.lower_level_text.text()):
                self.accept()

            # The level fields do not contain just numbers
            else:
                button_reply = QMessageBox.warning(self, "Error Message",
                                                   "The level fields need to be numbers!", QMessageBox.Ok)
                if button_reply == QMessageBox.Ok:
                    pass

        # Atleast one input field was left empty
        else:
            button_reply = QMessageBox.warning(self, "Error Message",
                                               "None of the fields should be empty!", QMessageBox.Ok)
            if button_reply == QMessageBox.Ok:
                pass


""" This class creates the user input dialog for when Modifying or Adding a Standard Organ name option """

class Dialog_Organ(QDialog):

    def __init__(self, standard_name, fma_id, organ, url):
        super(Dialog_Organ, self).__init__()

        # Passing the current values if it is an existing option or empty if its a new one
        self.standard_name = standard_name
        self.setWindowIcon(QtGui.QIcon(resource_path("res/images/btn-icons/onkodicom_icon.png")))
        self.fma_id = fma_id
        self.organ = organ
        self.url = url

        # Creating the UI components
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.standard_name_header = QLineEdit()
        self.standard_name_header.setText(self.standard_name)
        self.fma_id_header = QLineEdit()
        self.fma_id_header.setText(self.fma_id)
        self.organ_header = QLineEdit()
        self.organ_header.setText(self.organ)
        self.url_header = QLineEdit()
        self.url_header.setText(self.url)
        layout = QFormLayout(self)
        layout.addRow(QLabel("Standard Name:"), self.standard_name_header)
        layout.addRow(QLabel("FMA ID:"), self.fma_id_header)
        layout.addRow(QLabel("Organ:"), self.organ_header)
        layout.addRow(QLabel("Url:"), self.url_header)
        layout.addWidget(button_box)
        button_box.accepted.connect(self.accepting)
        button_box.rejected.connect(self.reject)
        self.setWindowTitle("Standard Organ Names")

    # This function returns the user inputs in case of a OK being pressed
    def getInputs(self):
        return (
            self.standard_name_header.text(), self.fma_id_header.text(), self.organ_header.text(),
            self.url_header.text())

    # This function does the validation of the inputs and gives the corresponding errors if needed
    def accepting(self):

        # Check that no mandatory input is empty
        if self.standard_name_header.text() != '' and self.fma_id_header.text() != '' and self.organ_header.text() != '':
            # Check validation
            if re.match(r'^([\s\d]+)$', self.fma_id_header.text()):
                self.accept()

            # The FMA ID field do not contain just numbers
            else:
                button_reply = QMessageBox.warning(self, "Error Message",
                                                   "The FMA ID field should to be a number!", QMessageBox.Ok)
                if button_reply == QMessageBox.Ok:
                    pass

        # Atleast one input field was left empty
        else:
            button_reply = QMessageBox.warning(self, "Error Message",
                                               "None of the fields should be empty!", QMessageBox.Ok)
            if button_reply == QMessageBox.Ok:
                pass


""" This class creates the user input dialog for when Modifying or Adding a Standard Organ name option  """

class Dialog_Volume(QDialog):

    def __init__(self, standard_name, volume_name):
        super(Dialog_Volume, self).__init__()

        # Passing the current values if it is an existing option or empty if its a new one
        self.standard_name = standard_name
        self.volume_name = volume_name

        # Creating the UI components
        self.setWindowIcon(QtGui.QIcon(resource_path("res/images/btn-icons/onkodicom_icon.png")))
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.standard_name_text = QLineEdit()
        self.standard_name_text.setText(self.standard_name)
        self.volume = QLineEdit()
        self.volume.setText(self.volume_name)
        layout = QFormLayout(self)
        layout.addRow(QLabel("Standard Name:"), self.standard_name_text)
        layout.addRow(QLabel("Volume Name:"), self.volume)
        layout.addWidget(button_box)
        button_box.accepted.connect(self.accepting)
        button_box.rejected.connect(self.reject)
        self.setWindowTitle("Standard Volume Names")

    # This function returns the user inputs in case of a OK being pressed
    def getInputs(self):
        return (self.standard_name_text.text(), self.volume.text())

    # This function does the validation of the inputs and gives the corresponding errors if needed
    def accepting(self):

        # Check that no mandatory input is empty
        if self.standard_name_text.text() != '' and self.volume.text() != '':
            self.accept()

        # Atleast one input field was left empty
        else:
            button_reply = QMessageBox.warning(self, "Error Message",
                                              "None of the fields should be empty!", QMessageBox.Ok)
            if button_reply == QMessageBox.Ok:
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
#         self.setWindowIcon(QtGui.QIcon("res/images/btn-icons/onkodicom_icon.png"))
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
