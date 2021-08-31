import csv
import platform
from pathlib import Path
from PySide6 import QtCore, QtGui, QtWidgets
from src.Controller.PathHandler import resource_path
from src.Model import DICOMStructuredReport
from src.Model.PatientDictContainer import PatientDictContainer


class ClinicalDataView(QtWidgets.QWidget):
    """
    This class creates a QtWidget for displaying clinical data from a
    DICOM-SR file. This QtWidget also has the ability to import clinical
    data from a CSV and save it to a DICOM-SR. Only compatible with
    DICOM-SR files generated with OnkoDICOM/this class.
    """
    def __init__(self):
        QtWidgets.QWidget.__init__(self)

        # Create class attributes
        self.data_dict = {}

        # Create the main layout
        self.main_layout = QtWidgets.QVBoxLayout()

        # Get the stylesheet
        if platform.system() == 'Darwin':
            self.stylesheet_path = "res/stylesheet.qss"
        else:
            self.stylesheet_path = "res/stylesheet-win-linux.qss"
        self.stylesheet = open(resource_path(self.stylesheet_path)).read()

        self.create_cd_table()
        self.create_buttons()
        self.setLayout(self.main_layout)

    def create_cd_table(self):
        """
        Creates the Clinical Data table, for viewing clinical data
        read in from a DICOM-SR.
        """
        # Create table
        self.table_cd = QtWidgets.QTableWidget(self)
        self.table_cd.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.table_cd.setColumnCount(2)
        self.table_cd.verticalHeader().hide()
        self.table_cd.setHorizontalHeaderLabels([" Attribute ", " Value "])

        self.table_cd.horizontalHeaderItem(0).setTextAlignment(
            QtCore.Qt.AlignLeft)
        self.table_cd.horizontalHeaderItem(1).setTextAlignment(
            QtCore.Qt.AlignLeft)

        # Remove ability to edit table
        self.table_cd.setEditTriggers(
            QtWidgets.QTreeView.NoEditTriggers |
            QtWidgets.QTreeView.NoEditTriggers)

        # Populate table data
        self.populate_table()

        # Resize table columns
        self.table_cd.setColumnWidth(0, self.width() * 0.3)
        self.table_cd.horizontalHeader().setStretchLastSection(True)

        # Add table to layout
        self.main_layout.addWidget(self.table_cd)

        print("")

    def create_buttons(self):
        """
        Creates a button for importing CSV data, and a button for
        manually saving clinical data to a DICOM-SR.
        """
        # Layout for buttons
        self.button_layout = QtWidgets.QHBoxLayout()

        # Buttons
        self.import_button = QtWidgets.QPushButton(self)
        self.save_button = QtWidgets.QPushButton(self)

        # Set cursor
        self.import_button.setCursor(
            QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.save_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

        # set button stylesheet
        self.import_button.setStyleSheet(self.stylesheet)
        self.save_button.setStyleSheet(self.stylesheet)

        # Set text
        _translate = QtCore.QCoreApplication.translate
        self.import_button.setText(_translate("Clinical_Data",
                                              "Import CSV Data"))
        self.save_button.setText(_translate("Clinical_Data",
                                            "Save to DICOM SR"))

        # Connect button clicked events to functions
        self.import_button.clicked.connect(self.import_clinical_data)
        self.save_button.clicked.connect(self.save_clinical_data)

        # Add buttons to layout
        self.button_layout.addWidget(self.import_button)
        self.button_layout.addWidget(self.save_button)
        self.main_layout.addLayout(self.button_layout)

    def populate_table(self):
        """
        Populates the table with data from the DICOM-SR file, if it
        exists.
        """
        # Attempt to get clinical data dataset
        patient_dict_container = PatientDictContainer()
        try:
            clinical_data = patient_dict_container.dataset['sr-cd']

            # Get text from clinical data dataset
            text = clinical_data.ContentSequence[0].TextValue

            # Split text into dictionary
            text_data = text.splitlines()
            for row in text_data:
                key, value = row.split(":")
                self.data_dict[key] = value
        except KeyError:
            print("No DICOM SR containing clinical data in dataset.")

            # See if data has been imported
            if self.data_dict:
                pass
            else:
                return

        for i, key in enumerate(self.data_dict):
            attrib = QtWidgets.QTableWidgetItem(key)
            value = QtWidgets.QTableWidgetItem(self.data_dict[key])
            self.table_cd.insertRow(i)
            self.table_cd.setItem(i, 0, attrib)
            self.table_cd.setItem(i, 1, value)

        print("")

    def clear_table(self):
        """
        Clears the table of all data.
        """
        if self.table_cd.rowCount() > 0:
            for i in range(self.table_cd.rowCount()):
                self.table_cd.removeRow(i)

    def import_clinical_data(self):
        """
        Opens a file select dialog to open a CSV file containing patient
        clinical data. Imports clinical data for that patient (matches
        patient ID in the dataset to patient ID in the CSV file), and
        displays it in the table.
        """
        # Clear data dictionary
        self.data_dict = {}

        # Current patient's ID
        patient_dict_container = PatientDictContainer()
        patient_id = patient_dict_container.dataset[0].PatientID

        file_path = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open Data File", "", "CSV data files (*.csv)")[0]

        # Get CSV data
        if file_path != "":
            with open(file_path, newline="") as stream:
                data = list(csv.reader(stream))
        else:
            # Clear table
            self.clear_table()

            # Write warning to table
            message = "No clinical data CSV selected."
            attrib = QtWidgets.QTableWidgetItem("Warning")
            value = QtWidgets.QTableWidgetItem(message)
            self.table_cd.insertRow(0)
            self.table_cd.setItem(0, 0, attrib)
            self.table_cd.setItem(0, 1, value)
            
            return

        # See if CSV data matches patient ID
        patient_in_file = False
        row_num = 0
        for i, row in enumerate(data):
            if row[0] == patient_id:
                patient_in_file = True
                row_num = i
                break

        # Return if patient's data not in the CSV file
        if not patient_in_file:
            # Clear table
            self.clear_table()

            # Write warning to table
            message = "Patient clinical data not found in CSV."
            attrib = QtWidgets.QTableWidgetItem("Warning")
            value = QtWidgets.QTableWidgetItem(message)
            self.table_cd.insertRow(0)
            self.table_cd.setItem(0, 0, attrib)
            self.table_cd.setItem(0, 1, value)

            return

        # Put patient data into dictionary
        headings = data[0]
        attribs = data[row_num]
        for i, heading in enumerate(headings):
            self.data_dict[heading] = attribs[i]

        # Update table
        self.populate_table()

    def save_clinical_data(self):
        """
        Saves clinical data to a DICOM-SR file. Overwrites any existing
        clinical data SR files in the dataset.
        """
        # Only save if there is at least one row in the table
        if self.table_cd.rowCount() <= 0:
            print("Not saving.")
            return

        # Create string from clinical data dictionary
        text = ""
        for key in self.data_dict:
            text += str(key) + ": " + str(self.data_dict[key]) + "\n"

        # Create and save DICOM SR file
        patient_dict_container = PatientDictContainer()
        file_path = patient_dict_container.path
        file_path = Path(file_path).joinpath("Clinical-Data-SR.dcm")
        ds = patient_dict_container.dataset[0]
        dicom_sr = DICOMStructuredReport.generate_dicom_sr(file_path, ds, text)
        dicom_sr.save_as(file_path)
        print("Saved")
