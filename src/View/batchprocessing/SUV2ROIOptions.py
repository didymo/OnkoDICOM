import platform
from pydicom import dcmread
from PySide6 import QtCore, QtGui, QtWidgets
from src.Controller.PathHandler import resource_path


class SUV2ROIOptions(QtWidgets.QWidget):
    """
    SUV2ROI options for batch processing. A simple description of the
    current requirements for SUV2ROI in OnkoDICOM.
    """

    def __init__(self):
        """
        Initialise the class
        """
        QtWidgets.QWidget.__init__(self)

        # Create the main layout
        self.main_layout = QtWidgets.QVBoxLayout()

        # Get the stylesheet
        if platform.system() == 'Darwin':
            self.stylesheet_path = "res/stylesheet.qss"
        else:
            self.stylesheet_path = "res/stylesheet-win-linux.qss"
        self.stylesheet = open(resource_path(self.stylesheet_path)).read()

        # Create QLabel to display information, and text and font
        self.info_label = QtWidgets.QLabel()
        self.text_font = QtGui.QFont()
        text_info = "SUV2ROI can currently only be performed on PET images " \
                    "that are stored in units of Bq/mL and that are decay " \
                    "corrected. For best results, please ensure only one set " \
                    "of compliant PET images is present in each dataset that " \
                    "you wish to perform SUV2ROI on. For more information " \
                    "on SUV2ROI functionality, see the User Manual."
        self.text_font.setPointSize(12)
        self.info_label.setText(text_info)
        self.info_label.setFont(self.text_font)
        self.info_label.setWordWrap(True)

        self.main_layout.addWidget(self.info_label)
        self.create_table_view()
        self.setLayout(self.main_layout)

    def create_table_view(self):
        """
        Create a table to display all of the datasets containing PET images
        without a patient weight and give the user the ability to set the
        patient weight for these datasets.
        """
        # Create table
        self.table_pet_weight = QtWidgets.QTableWidget(self)
        self.table_pet_weight.setStyleSheet(
            "background-color: rgb(255, 255, 255);")
        self.table_pet_weight.setColumnCount(2)
        self.table_pet_weight.verticalHeader().hide()
        # Note - "New Name" is only enabled if the option "Rename" is
        # selected.
        self.table_pet_weight.setHorizontalHeaderLabels(
            [" Patient ID ", " Weight "])

        self.table_pet_weight.horizontalHeaderItem(0).setTextAlignment(
            QtCore.Qt.AlignLeft)
        self.table_pet_weight.horizontalHeaderItem(1).setTextAlignment(
            QtCore.Qt.AlignLeft)

        pet_weight_header = self.table_pet_weight.horizontalHeader()
        pet_weight_header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        pet_weight_header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)

        # Removing the ability to edit tables with immediate click
        self.table_pet_weight.setEditTriggers(
            QtWidgets.QTreeView.NoEditTriggers |
            QtWidgets.QTreeView.NoEditTriggers)

        # Add table to the main layout
        self.main_layout.addWidget(self.table_pet_weight)

    def populate_table(self, dicom_structure):
        """
        Populates the table with patient IDs and line edits once datasets
        have been loaded. Called when datasets have finished loading.
        :param dicom_structure: DICOM structure object representing all
                                patients loaded.
        """
        # Loop through each patient, get every RTSTRUCT
        pet_image_list = []
        for patient in dicom_structure.patients:
            studies = dicom_structure.patients[patient].studies
            for study in studies:
                image_serieses = studies[study].image_series
                for image_series in image_serieses:
                    images = image_serieses[image_series].images
                    for image in images:
                        if images[image].class_id == \
                                '1.2.840.10008.5.1.4.1.1.128':
                            pet_image_list.append(images[image].path)
                            break

        # Return if no RT Structs found
        if not len(pet_image_list):
            self.table_pet_weight.setRowCount(0)
            return

        # Loop through each PET image, try to get the patient weight
        patient_ids = {}
        for pet_image in pet_image_list:
            pet_data = dcmread(pet_image)
            if pet_data.PatientID not in patient_ids:
                if not hasattr(pet_data, 'PatientWeight'):
                    patient_ids[pet_data.PatientID] = None
                else:
                    patient_ids[pet_data.PatientID] = pet_data.PatientWeight

        # Return if all patients have weights, or no patients found
        if not len(patient_ids.keys()):
            self.table_pet_weight.setRowCount(0)
            return

        # Populate table
        self.table_pet_weight.setRowCount(0)

        # Loop through each patient ID
        i = 0
        for patient_id in patient_ids.keys():
            patient_weight_widget = None
            if patient_ids[patient_id] is None:
                # Create line edit
                patient_weight_widget = QtWidgets.QLineEdit()
                patient_weight_widget.setStyleSheet(self.stylesheet)
            else:
                # Create label
                patient_weight_widget = \
                    QtWidgets.QLabel(patient_ids[patient_id])
                patient_weight_widget.setStyleSheet(self.stylesheet)

            # Add row to table
            self.table_pet_weight.insertRow(i)
            self.table_pet_weight.setRowHeight(i, 50)
            self.table_pet_weight.setItem(
                i, 0, QtWidgets.QTableWidgetItem(patient_id))
            self.table_pet_weight.setCellWidget(i, 1, patient_weight_widget)
            i += 1

    def get_patient_weights(self):
        """
        Returns a dictionary of patient IDs and patient weights.
        :return: patient_weights, a dictionary of patient ID and patient
                 weight key-value pairs.
        """
        # Create dictionary
        patient_weights = {}

        # Loop through table
        for i in range(self.table_pet_weight.rowCount()):
            # Get patient ID and weight
            patient_id = self.table_pet_weight.item(i, 0).text()
            weight = self.table_pet_weight.cellWidget(i, 1).text()

            # Make sure weight is not empty and is a valid (> 0) number
            if weight != '':
                try:
                    num = float(weight)
                    if num < 0:
                        raise ValueError
                except ValueError:
                    num = None
            else:
                num = None

            patient_weights[patient_id] = num

        return patient_weights
