import csv
import platform

from pydicom import dcmread
from PySide6 import QtCore, QtWidgets
from src.Controller.PathHandler import resource_path


class ROINameCleaningOptionComboBox(QtWidgets.QComboBox):
    """
    This class inherits QComboBox to create a custom widget for the Name
    Cleaning ROI table that includes two options - modify and delete.
    """

    def __init__(self):
        QtWidgets.QComboBox.__init__(self)
        self.addItem("Ignore")
        self.addItem("Modify")
        self.addItem("Delete")


class ROINameCleaningOrganComboBox(QtWidgets.QComboBox):
    """
    This class inherits QComboBox to create a custom widget for the Name
    Cleaning ROI table that includes a list of standard organ names.
    """

    def __init__(self, organs):
        """
        Initialises the object, setting the combo box options to be a
        list of the standard organ names.
        :param organs: a list of standard organ names.
        """
        QtWidgets.QComboBox.__init__(self)

        # Populate combo box options
        for organ in organs:
            self.addItem(organ)

    @QtCore.Slot(int)
    def change_enabled(self, index):
        """
        A slot for changing whether this combo box is enabled or
        disabled depending on whether "Modify" or "Delete" has been
        selected for the associated ROI.
        """
        if index == 0:
            self.setEnabled(True)
        elif index == 1:
            self.setEnabled(False)


class ROINameCleaningLineEdit(QtWidgets.QLineEdit):
    """
    This class inherits QLineEdit to create a custom widget for the Name
    Cleaning ROI table that allows it to be enabled or disabled when the
    QComboBox in the same row changes.

    Currently unused.
    """

    @QtCore.Slot(int)
    def change_enabled(self, index):
        print(index)
        if index == 0:
            self.setEnabled(True)
        elif index == 1:
            self.setEnabled(False)


class ROINameCleaningOptions(QtWidgets.QWidget):
    """
    ROI Name Cleaning options for batch processing.
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

        # Class variables
        self.organ_names = []
        self.volume_prefixes = []

        self.get_standard_names()
        self.create_table_view()
        self.setLayout(self.main_layout)

    def get_standard_names(self):
        """
        Get standard organ names and prefix types.
        """
        # Get standard organ names
        with open(resource_path('data/csv/organName.csv'), 'r') as f:
            csv_input = csv.reader(f)
            header = next(f)  # Ignore the "header" of the column
            for row in csv_input:
                self.organ_names.append(row[0])

        # Get standard volume prefixes
        with open(resource_path('data/csv/volumeName.csv'), 'r') as f:
            csv_input = csv.reader(f)
            header = next(f)  # Ignore the "header" of the column
            for row in csv_input:
                self.volume_prefixes.append(row[1])

    def create_table_view(self):
        """
        Create a table to display all of the non-standard ROIs and
        options for what to do with them.
        """
        # Create table
        self.table_roi = QtWidgets.QTableWidget(self)
        self.table_roi.setStyleSheet(
            "background-color: rgb(255, 255, 255);")
        self.table_roi.setColumnCount(4)
        self.table_roi.verticalHeader().hide()
        # Note - "New Name" is only enabled if the option "Rename" is
        # selected.
        self.table_roi.setHorizontalHeaderLabels(
            [" ROI Name ", " Option ", " New Name ", " Dataset Location "])

        self.table_roi.horizontalHeaderItem(0).setTextAlignment(
            QtCore.Qt.AlignLeft)
        self.table_roi.horizontalHeaderItem(1).setTextAlignment(
            QtCore.Qt.AlignLeft)
        self.table_roi.horizontalHeaderItem(2).setTextAlignment(
            QtCore.Qt.AlignLeft)
        self.table_roi.horizontalHeaderItem(3).setTextAlignment(
            QtCore.Qt.AlignLeft)

        roi_name_header = self.table_roi.horizontalHeader()
        roi_name_header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        roi_name_header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        roi_name_header.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        roi_name_header.setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch)

        # Removing the ability to edit tables with immediate click
        self.table_roi.setEditTriggers(
            QtWidgets.QTreeView.NoEditTriggers |
            QtWidgets.QTreeView.NoEditTriggers)

        # Add table to the main layout
        self.main_layout.addWidget(self.table_roi)

    def populate_table(self, dicom_structure):
        """
        Populates the table with ROI names and options once datasets
        have been loaded. Called when datasets have finished loading.
        :param dicom_structure: DICOM structure object representing all
                                patients loaded.
        """
        # List of non-standard ROI names

        # Loop through each patient
        rtstructs = []
        for patient in dicom_structure.patients:
            studies = dicom_structure.patients[patient].studies
            for study in studies:
                serieses = studies[study].series
                for series in serieses:
                    images = serieses[series].images
                    for image in images:
                        if images[image].class_id == \
                                '1.2.840.10008.5.1.4.1.1.481.3':
                            rtstructs.append(images[image].path)

        # Return if no RT Structs found
        if not len(rtstructs):
            self.table_roi.setRowCount(0)
            return

        # Loop through each RT Struct
        rois = {}
        for rtss in rtstructs:
            rtstruct = dcmread(rtss)
            roi_names = []
            # Loop through each ROI in the RT Struct
            for i in range(len(rtstruct.StructureSetROISequence)):
                # Get the ROI name, determine if it is a standard organ
                # name or has a standard prefix
                roi_name = rtstruct.StructureSetROISequence[i].ROIName
                if roi_name not in self.organ_names and \
                        roi_name[0:3] not in self.volume_prefixes:
                    roi_names.append(roi_name)
            # Append ROI names to dictionary
            if len(roi_names):
                rois[rtss] = roi_names

        # Return if no ROIs found
        if not len(rois):
            self.table_roi.setRowCount(0)
            return

        # Populate table
        self.table_roi.setRowCount(0)

        # Loop through each RTSS
        for rtss in rois:
            # Loop through each ROI
            roi_list = rois[rtss]
            for i in range(len(roi_list)):
                # Create QComboBox and QLineEdit
                combo_box = ROINameCleaningOptionComboBox()
                combo_box.setStyleSheet(self.stylesheet)
                organ_combo_box = \
                    ROINameCleaningOrganComboBox(self.organ_names)
                organ_combo_box.setStyleSheet(self.stylesheet)
                combo_box.currentIndexChanged.connect(
                    organ_combo_box.change_enabled)

                # Add row to table
                self.table_roi.insertRow(i)
                self.table_roi.setRowHeight(i, 50)
                self.table_roi.setItem(i, 0,
                                       QtWidgets.QTableWidgetItem(roi_list[i]))
                self.table_roi.setCellWidget(i, 1, combo_box)
                self.table_roi.setCellWidget(i, 2, organ_combo_box)
                self.table_roi.setItem(i, 3, QtWidgets.QTableWidgetItem(rtss))
