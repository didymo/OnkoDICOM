import logging
import platform
from PySide6 import QtWidgets
from os.path import expanduser
from src.Controller.PathHandler import resource_path
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'

class MachineLearningDataSelection(QtWidgets.QWidget):
    def __init__(self):
        """
        Initialise the class
        """
        QtWidgets.QWidget.__init__(self)
        self.dataDictionary = {}
        self.binaryData = False

        # Create the main layout
        self.main_layout = QtWidgets.QVBoxLayout()

        # Get the stylesheet
        if platform.system() == 'Darwin':
            self.stylesheet_path = "res/stylesheet.qss"
        else:
            self.stylesheet_path = "res/stylesheet-win-linux.qss"
        self.stylesheet = open(resource_path(self.stylesheet_path)).read()


        label_DVG = QtWidgets.QLabel("Please choose the CSV file location for DVH Data:")
        label_DVG.setStyleSheet(self.stylesheet)

        label_Pyrad = QtWidgets.QLabel("Please choose the CSV file location for Pyradiomics Data:")
        label_Pyrad.setStyleSheet(self.stylesheet)

        self.directory_layout = QtWidgets.QFormLayout()

        # Directory text box for DVH Data
        self.directory_input_dvhData = QtWidgets.QLineEdit("No file selected")
        self.directory_input_dvhData.setStyleSheet(self.stylesheet)
        self.directory_input_dvhData.setEnabled(False)

        # Button For DVH Data to set location
        self.change_button_dvhData = QtWidgets.QPushButton("Change")
        self.change_button_dvhData.setMaximumWidth(100)
        self.change_button_dvhData.clicked.connect(self.show_file_browser_dvhData)
        self.change_button_dvhData.setObjectName("NormalButton")
        self.change_button_dvhData.setStyleSheet(self.stylesheet)

        # Directory text box for Pyradiomics Data
        self.directory_input_pyrad = QtWidgets.QLineEdit("No file selected")
        self.directory_input_pyrad.setStyleSheet(self.stylesheet)
        self.directory_input_pyrad.setEnabled(False)

        # Button For Pyradiomics Data to set location
        self.change_button_pyradiomicsData = QtWidgets.QPushButton("Change")
        self.change_button_pyradiomicsData.setMaximumWidth(100)
        self.change_button_pyradiomicsData.clicked.connect(self.show_file_browser_pyrad)
        self.change_button_pyradiomicsData.setObjectName("NormalButton")
        self.change_button_pyradiomicsData.setStyleSheet(self.stylesheet)

        # Set DVH data
        self.directory_layout.addWidget(label_DVG)
        self.directory_layout.addWidget(self.directory_input_dvhData)
        self.directory_layout.addWidget(self.change_button_dvhData)

        # Set Pyradiomics data
        self.directory_layout.addWidget(label_Pyrad)
        self.directory_layout.addWidget(self.directory_input_pyrad)
        self.directory_layout.addWidget(self.change_button_pyradiomicsData)

        # create dropdown menu for dvh values to select from
        self.dvh_dropdown_menu = QtWidgets.QComboBox()
        self.dvh_dropdown_menu.setStyleSheet(self.stylesheet)
        
        # create dropdown menu for dvh values to select from
        self.pyrad_dropdown_menu = QtWidgets.QComboBox()
        self.pyrad_dropdown_menu.setStyleSheet(self.stylesheet)

        # add dropdowns to main_layout
        self.directory_layout.addWidget(self.dvh_dropdown_menu)
        self.directory_layout.addWidget(self.pyrad_dropdown_menu)

        self.main_layout.addLayout(self.directory_layout)
        self.setLayout(self.main_layout)

        # storing the currently selected filter options
        self._selected_DVH_ROI = ""
        self._selected_pyrad_ROI = ""

    def set_dvh_dropdown_menu_data(self, options):
        self.dvh_dropdown_menu.clear()
        self.dvh_dropdown_menu.addItems(options)

    def set_pyrad_dropdown_menu_data(self, options):
        self.pyrad_dropdown_menu.clear()
        self.pyrad_dropdown_menu.addItems(options)

    def read_in_dvh_data(self):
        data_dvh = pd.read_csv(f'{self.get_csv_input_location_dvh_data()}', on_bad_lines='skip')
        return list(data_dvh[data_dvh['ROI'].str.contains('PTV')]['ROI'].unique())

    def read_in_pyrad_data(self):
        data_Py = pd.read_csv(f'{self.get_csv_input_location_pyrad()}')
        return list(data_Py[data_Py['ROI'].str.contains('GTV')]['ROI'].unique())

    def _on_dvh_path_changed(self):
        options = self.read_in_dvh_data()
        self.set_dvh_dropdown_menu_data(options)

    def _on_pyrad_path_changed(self):
        options = self.read_in_pyrad_data()
        self.set_pyrad_dropdown_menu_data(options)

    # Function for DVH Data
    def set_csv_input_location_dvhData(self, path, enable=True,
                                        change_if_modified=False):
        """
        Set the location for the dvh .csv file.
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
        
        self._on_dvh_path_changed()

    def get_csv_input_location_dvh_data(self):
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
        self.set_csv_input_location_dvhData(path, change_if_modified=True)

    # Function for Pyrad Data
    def set_csv_input_location_pyrad(self, path, enable=True,
                                      change_if_modified=False):
        """
        Set the location for the pyradiomics .csv file.
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

        self._on_pyrad_path_changed()

    def get_csv_input_location_pyrad(self):
        """
        Get the location of the desired output directory.
        """
        return self.directory_input_pyrad.text()

    def show_file_browser_pyrad(self):
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
        self.set_csv_input_location_pyrad(path, change_if_modified=True)

    def get_selected_dvh_value(self):
        return self.dvh_dropdown_menu.currentText()

    def get_selected_pyrad_value(self):
        return self.pyrad_dropdown_menu.currentText()

    def get_selected_options(self):
        return {"dvh_path": self.get_csv_input_location_dvh_data(),
                "pyrad_path": self.get_csv_input_location_pyrad(),
                "dvh_value": self.get_selected_dvh_value(),
                "pyrad_value": self.get_selected_pyrad_value()}
