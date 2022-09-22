import platform
from PySide6 import QtWidgets
from os.path import expanduser
from src.Controller.PathHandler import resource_path

class MachineLearning(QtWidgets.QWidget):
    """
    DVH2CSV options for batch processing.
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

        label_clinicalData = QtWidgets.QLabel("Please choose the CSV file location for Clinical Data:")
        label_clinicalData.setStyleSheet(self.stylesheet)

        label_DVG = QtWidgets.QLabel("Please choose the CSV file location for DVH Data:")
        label_DVG.setStyleSheet(self.stylesheet)

        label_Pyrad = QtWidgets.QLabel("Please choose the CSV file location for Pyradiomics Data:")
        label_Pyrad.setStyleSheet(self.stylesheet)

        self.directory_layout = QtWidgets.QFormLayout()

        # Directory text box for clinical Data
        self.directory_input_clinicalData = QtWidgets.QLineEdit("No file selected")
        self.directory_input_clinicalData.setStyleSheet(self.stylesheet)
        self.directory_input_clinicalData.setEnabled(False)

        #Button For clinical Data to set location
        self.change_button_clinicalData = QtWidgets.QPushButton("Change")
        self.change_button_clinicalData.setMaximumWidth(100)
        self.change_button_clinicalData.clicked.connect(self.show_file_browser_clinicalData)
        self.change_button_clinicalData.setObjectName("NormalButton")
        self.change_button_clinicalData.setStyleSheet(self.stylesheet)

        # Directory text box for DVH Data
        self.directory_input_dvhData = QtWidgets.QLineEdit("No file selected")
        self.directory_input_dvhData.setStyleSheet(self.stylesheet)
        self.directory_input_dvhData.setEnabled(False)

        #Button For DVH Data to set location
        self.change_button_dvhData = QtWidgets.QPushButton("Change")
        self.change_button_dvhData.setMaximumWidth(100)
        self.change_button_dvhData.clicked.connect(self.show_file_browser_dvhData)
        self.change_button_dvhData.setObjectName("NormalButton")
        self.change_button_dvhData.setStyleSheet(self.stylesheet)

        # Directory text box for Pyradiomics Data
        self.directory_input_pyrad = QtWidgets.QLineEdit("No file selected")
        self.directory_input_pyrad.setStyleSheet(self.stylesheet)
        self.directory_input_pyrad.setEnabled(False)

        #Button For Pyradiomics Data to set location
        self.change_button_pyradiomicsData = QtWidgets.QPushButton("Change")
        self.change_button_pyradiomicsData.setMaximumWidth(100)
        self.change_button_pyradiomicsData.clicked.connect(self.show_file_browser_payrad)
        self.change_button_pyradiomicsData.setObjectName("NormalButton")
        self.change_button_pyradiomicsData.setStyleSheet(self.stylesheet)

        #Set Clinical Data
        self.directory_layout.addWidget(label_clinicalData)
        self.directory_layout.addRow(self.directory_input_clinicalData)
        self.directory_layout.addRow(self.change_button_clinicalData)

        #Set DVH data
        self.directory_layout.addWidget(label_DVG)
        self.directory_layout.addRow(self.directory_input_dvhData)
        self.directory_layout.addRow(self.change_button_dvhData)

        #Set Pyradiomics data
        self.directory_layout.addWidget(label_Pyrad)
        self.directory_layout.addRow(self.directory_input_pyrad)
        self.directory_layout.addRow(self.change_button_pyradiomicsData)


        self.main_layout.addLayout(self.directory_layout)
        self.setLayout(self.main_layout)

    #Function for Clinical Data
    def set_csv_output_location_clinicalData(self, path, enable=True,
                                change_if_modified=False):
        """
        Set the location for the ClinicalData-SR2CSV resulting .csv file.
        :param path: desired path.
        :param enable: Enable the directory text bar.
        :param change_if_modified: Change the directory if already been
                                   changed.
        """
        if not self.directory_input_clinicalData.isEnabled():
            self.directory_input_clinicalData.setText(path)
            self.directory_input_clinicalData.setEnabled(enable)
        elif change_if_modified:
            self.directory_input_clinicalData.setText(path)
            self.directory_input_clinicalData.setEnabled(enable)

    def get_csv_output_location_clinicalData(self):
        """
        Get the location of the desired output directory.
        """
        return self.directory_input_clinicalData.text()

    def show_file_browser_clinicalData(self):
        """
        Show the file browser for selecting a folder for the Onko
        default directory.
        """
        # Open a file dialog and return chosen directory
        path = QtWidgets.QFileDialog.getOpenFileName(
            None, "Open Clinical Data File", "",
            "CSV data files (*.csv *.CSV)")[0]

        # If chosen directory is nothing (user clicked cancel) set to
        # user home
        if path == "" and self.directory_input_clinicalData.text() == 'No file selected':
            path = expanduser("~")
        elif (path == ""
                and
                (self.directory_input_clinicalData.text() != 'No file selected'
                 or self.directory_input_clinicalData.text() != expanduser("~"))):
            path = self.directory_input_clinicalData.text()

        # Update file path
        self.set_csv_output_location_clinicalData(path, change_if_modified=True)

    #Function for DVH Data
    def set_csv_output_location_dvhData(self, path, enable=True,
                                change_if_modified=False):
        """
        Set the location for the ClinicalData-SR2CSV resulting .csv file.
        :param path: desired path.
        :param enable: Enable the directory text bar.
        :param change_if_modified: Change the directory if already been
                                   changed.
        """
        if not self.directory_input_dvhData.isEnabled():
            self.directory_input_dvhData.setText(path)
            self.directory_input_dvhData.setEnabled(enable)
        elif change_if_modified:
            self.directory_input_dvhData.setText(path)
            self.directory_input_dvhData.setEnabled(enable)

    def get_csv_output_location_dvhData(self):
        """
        Get the location of the desired output directory.
        """
        return self.directory_input_dvhData.text()

    def show_file_browser_dvhData(self):
        """
        Show the file browser for selecting a folder for the Onko
        default directory.
        """
        # Open a file dialog and return chosen directory
        path = QtWidgets.QFileDialog.getOpenFileName(
            None, "Open Clinical Data File", "",
            "CSV data files (*.csv *.CSV)")[0]

        # If chosen directory is nothing (user clicked cancel) set to
        # user home
        if path == "" and self.directory_input_dvhData.text() == 'No file selected':
            path = expanduser("~")
        elif (path == ""
                and
                (self.directory_input_dvhData.text() != 'No file selected'
                 or self.directory_input_dvhData.text() != expanduser("~"))):
            path = self.directory_input_dvhData.text()

        # Update file path
        self.set_csv_output_location_dvhData(path, change_if_modified=True)

    #Function for DVH Data
    def set_csv_output_location_dvhData(self, path, enable=True,
                                change_if_modified=False):
        """
        Set the location for the ClinicalData-SR2CSV resulting .csv file.
        :param path: desired path.
        :param enable: Enable the directory text bar.
        :param change_if_modified: Change the directory if already been
                                   changed.
        """
        if not self.directory_input_dvhData.isEnabled():
            self.directory_input_dvhData.setText(path)
            self.directory_input_dvhData.setEnabled(enable)
        elif change_if_modified:
            self.directory_input_dvhData.setText(path)
            self.directory_input_dvhData.setEnabled(enable)

    def get_csv_output_location_dvhData(self):
        """
        Get the location of the desired output directory.
        """
        return self.directory_input_dvhData.text()

    def show_file_browser_dvhData(self):
        """
        Show the file browser for selecting a folder for the Onko
        default directory.
        """
        # Open a file dialog and return chosen directory
        path = QtWidgets.QFileDialog.getOpenFileName(
            None, "Open Clinical Data File", "",
            "CSV data files (*.csv *.CSV)")[0]

        # If chosen directory is nothing (user clicked cancel) set to
        # user home
        if path == "" and self.directory_input_dvhData.text() == 'No file selected':
            path = expanduser("~")
        elif (path == ""
                and
                (self.directory_input_dvhData.text() != 'No file selected'
                 or self.directory_input_dvhData.text() != expanduser("~"))):
            path = self.directory_input_dvhData.text()

        # Update file path
        self.set_csv_output_location_dvhData(path, change_if_modified=True)

    #Function for Pyrad Data
    def set_csv_output_location_pyrad(self, path, enable=True,
                                change_if_modified=False):
        """
        Set the location for the ClinicalData-SR2CSV resulting .csv file.
        :param path: desired path.
        :param enable: Enable the directory text bar.
        :param change_if_modified: Change the directory if already been
                                   changed.
        """
        if not self.directory_input_pyrad.isEnabled():
            self.directory_input_pyrad.setText(path)
            self.directory_input_pyrad.setEnabled(enable)
        elif change_if_modified:
            self.directory_input_pyrad.setText(path)
            self.directory_input_pyrad.setEnabled(enable)

    def get_csv_output_location_payrad(self):
        """
        Get the location of the desired output directory.
        """
        return self.directory_input_pyrad.text()

    def show_file_browser_payrad(self):
        """
        Show the file browser for selecting a folder for the Onko
        default directory.
        """
        # Open a file dialog and return chosen directory
        path = QtWidgets.QFileDialog.getOpenFileName(
            None, "Open Clinical Data File", "",
            "CSV data files (*.csv *.CSV)")[0]

        # If chosen directory is nothing (user clicked cancel) set to
        # user home
        if path == "" and self.directory_input_pyrad.text() == 'No file selected':
            path = expanduser("~")
        elif (path == ""
                and
                (self.directory_input_pyrad.text() != 'No file selected'
                 or self.directory_input_pyrad.text() != expanduser("~"))):
            path = self.directory_input_pyrad.text()

        # Update file path
        self.set_csv_output_location_pyrad(path, change_if_modified=True)