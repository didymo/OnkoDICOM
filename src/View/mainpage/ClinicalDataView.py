import platform
from PySide6 import QtCore, QtWidgets
from src.Controller.PathHandler import resource_path


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

        # Add table to layout
        self.main_layout.addWidget(self.table_cd)

        print("")

    def create_buttons(self):
        """
        Creates a button for importing CSV data, and a button for
        manually saving clinical data to a DICOM-SR.
        """
        print("")