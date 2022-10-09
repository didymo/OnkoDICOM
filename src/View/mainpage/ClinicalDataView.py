import csv
import os
import platform
from pathlib import Path
from PySide6 import QtCore, QtWidgets
from src.Controller.PathHandler import resource_path
from src.Model.DICOM import DICOMStructuredReport
from src.Model.Configuration import Configuration, SqlError
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
        self.table_populated = False

        # Create the main layout
        self.main_layout = QtWidgets.QVBoxLayout()

        # Get the stylesheet
        if platform.system() == 'Darwin':
            self.stylesheet_path = "res/stylesheet.qss"
        else:
            self.stylesheet_path = "res/stylesheet-win-linux.qss"
        self.stylesheet = open(resource_path(self.stylesheet_path)).read()

        self.create_cd_table()
        self.setLayout(self.main_layout)
        self.import_clinical_data()

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
            # See if data has been imported
            if self.data_dict:
                pass
            else:
                return

        # Populate table with loaded values
        for i, key in enumerate(self.data_dict):
            attrib = QtWidgets.QTableWidgetItem(key)
            value = QtWidgets.QTableWidgetItem(self.data_dict[key])
            self.table_cd.insertRow(i)
            self.table_cd.setItem(i, 0, attrib)
            self.table_cd.setItem(i, 1, value)
        self.table_populated = True

    def clear_table(self):
        """
        Clears the table of all data.
        """
        if self.table_cd.rowCount() > 0:
            for i in range(self.table_cd.rowCount()):
                self.table_cd.removeRow(i)

    def import_clinical_data(self):
        """
        Attempt to import clinical data from the CSV stored in the
        program's settings database.
        """
        # Return if there is no RTDOSE in the dataset
        patient_dict_container = PatientDictContainer()
        if 'rtdose' not in list(patient_dict_container.dataset.keys()):
            message = "No RTDOSE found. Clinical data is only imported for " \
                      "datasets that include an RTDOSE."
            attrib = QtWidgets.QTableWidgetItem("Warning")
            value = QtWidgets.QTableWidgetItem(message)
            self.table_cd.insertRow(0)
            self.table_cd.setItem(0, 0, attrib)
            self.table_cd.setItem(0, 1, value)
            return

        # Return if data has been imported from DICOM SR
        if self.table_populated:
            return

        # Clear data dictionary and table
        self.data_dict = {}
        self.clear_table()

        # Current patient's ID
        patient_id = patient_dict_container.dataset[0].PatientID

        # Try get the clinical data CSV file path
        try:
            config = Configuration()
            file_path = config.get_clinical_data_csv_dir()
        except SqlError:
            # Write warning to table
            message = "Failed to access configuration file."
            attrib = QtWidgets.QTableWidgetItem("Warning")
            value = QtWidgets.QTableWidgetItem(message)
            self.table_cd.insertRow(0)
            self.table_cd.setItem(0, 0, attrib)
            self.table_cd.setItem(0, 1, value)
            return

        # Get CSV data
        if file_path == "" or file_path is None \
                or not os.path.exists(file_path):
            # Clear table
            self.clear_table()

            # Write warning to table
            message = "Clinical data CSV could not be found."
            attrib = QtWidgets.QTableWidgetItem("Warning")
            value = QtWidgets.QTableWidgetItem(message)
            self.table_cd.insertRow(0)
            self.table_cd.setItem(0, 0, attrib)
            self.table_cd.setItem(0, 1, value)
            return

        with open(file_path, newline="") as stream:
            data = list(csv.reader(stream))

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

        # Save clinical data to DICOM SR
        self.save_clinical_data()

    def save_clinical_data(self):
        """
        Saves clinical data to a DICOM-SR file. Overwrites any existing
        clinical data SR files in the dataset.
        """
        # Only save if there is at least one row in the table
        if self.table_cd.rowCount() <= 0:
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
        dicom_sr = DICOMStructuredReport.generate_dicom_sr(file_path, ds, text,
                                                           "CLINICAL-DATA")
        dicom_sr.save_as(file_path)

        # Update patient dict container
        patient_dict_container.dataset['sr-cd'] = dicom_sr
        patient_dict_container.filepaths['sr-cd'] = file_path
