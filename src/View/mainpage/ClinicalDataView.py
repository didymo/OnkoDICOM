import platform
from PySide6 import QtCore, QtGui, QtWidgets
from src.Controller.PathHandler import resource_path
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
        except KeyError:
            print("No DICOM SR containing clinical data in dataset.")
            return

        # Get text from clinical data dataset
        text = clinical_data.ContentSequence[0].TextValue

        # Split text into dictionary
        data_dict = {}
        text_data = text.splitlines()
        for row in text_data:
            key, value = row.split(":")
            data_dict[key] = value

        for i, key in enumerate(data_dict):
            attrib = QtWidgets.QTableWidgetItem(key)
            value = QtWidgets.QTableWidgetItem(data_dict[key])
            self.table_cd.insertRow(i)
            self.table_cd.setItem(i, 0, attrib)
            self.table_cd.setItem(i, 1, value)

        print("")

    def import_clinical_data(self):
        """
        Opens a file select dialog to open a CSV file containing patient
        clinical data, then a window to select which patient the user
        wants to import. Imports clinical data for that patient, and
        displays it in the table.
        """
        print("importing")

    def save_clinical_data(self):
        """
        Saves clinical data to a DICOM-SR file. Overwrites any existing
        clinical data SR files in the dataset.
        """
        print("Saving")