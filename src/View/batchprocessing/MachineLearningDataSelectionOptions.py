import logging
from PySide6 import QtWidgets
from os.path import expanduser
import pandas as pd

from src.View.StyleSheetReader import StyleSheetReader

pd.options.mode.chained_assignment = None  # default='warn'


class MachineLearningDataSelectionOptions(QtWidgets.QWidget):
    def __init__(self):
        """
        Initialise the class
        """
        QtWidgets.QWidget.__init__(self)

        # Create the main layout
        self.main_layout = QtWidgets.QVBoxLayout()

        # Get the stylesheet
        stylesheet: StyleSheetReader = StyleSheetReader()

        label_dvh = QtWidgets.QLabel(
            "Please choose the input CSV file location for DVH Data:"
        )
        label_dvh.setStyleSheet(stylesheet.get_stylesheet())

        label_pyrad = QtWidgets.QLabel(
            "Please choose the input CSV file location for Pyradiomics Data:"
        )
        label_pyrad.setStyleSheet(stylesheet.get_stylesheet())

        self.directory_layout = QtWidgets.QFormLayout()

        # Directory text box for DVH Data
        self.directory_input_dvh_data = QtWidgets.QLineEdit(
            "No file selected")
        self.directory_input_dvh_data.setStyleSheet(stylesheet.get_stylesheet())
        self.directory_input_dvh_data.setEnabled(False)

        # Button For DVH Data to set location
        self.change_button_dvh_data = QtWidgets.QPushButton("Change")
        self.change_button_dvh_data.setMaximumWidth(100)
        self.change_button_dvh_data.clicked.connect(
            self.show_file_browser_dvh_data)
        self.change_button_dvh_data.setObjectName("NormalButton")
        self.change_button_dvh_data.setStyleSheet(stylesheet.get_stylesheet())

        # Directory text box for Pyradiomics Data
        self.directory_input_pyrad = QtWidgets.QLineEdit(
            "No file selected")
        self.directory_input_pyrad.setStyleSheet(stylesheet.get_stylesheet())
        self.directory_input_pyrad.setEnabled(False)

        # Button For Pyradiomics Data to set location
        self.change_button_pyradiomics_data = QtWidgets.QPushButton(
            "Change")
        self.change_button_pyradiomics_data.setMaximumWidth(100)
        self.change_button_pyradiomics_data.clicked.connect(
            self.show_file_browser_pyrad)
        self.change_button_pyradiomics_data.setObjectName("NormalButton")
        self.change_button_pyradiomics_data.setStyleSheet(stylesheet.get_stylesheet())

        # Set DVH data
        self.directory_layout.addWidget(label_dvh)
        self.directory_layout.addRow(self.directory_input_dvh_data)
        self.directory_layout.addRow(self.change_button_dvh_data)

        # Set Pyradiomics data
        self.directory_layout.addWidget(label_pyrad)
        self.directory_layout.addRow(self.directory_input_pyrad)
        self.directory_layout.addRow(self.change_button_pyradiomics_data)

        # create dropdown menu for dvh values to select from
        self.dvh_dropdown_menu = QtWidgets.QComboBox()
        self.dvh_dropdown_menu.setStyleSheet(stylesheet.get_stylesheet())
        self.dvh_dropdown_menu.setEditable(True)
        self.dvh_dropdown_menu.lineEdit().setReadOnly(True)

        # create dropdown menu for dvh values to select from
        self.pyrad_dropdown_menu = QtWidgets.QComboBox()
        self.pyrad_dropdown_menu.setStyleSheet(stylesheet.get_stylesheet())
        self.pyrad_dropdown_menu.setEditable(True)
        self.pyrad_dropdown_menu.lineEdit().setReadOnly(True)

        # create labels for dropdown menus
        self.dvh_dropdown_label = QtWidgets.QLabel(
            "Please select the DVH ROI to filter by:")
        self.dvh_dropdown_label.setStyleSheet(stylesheet.get_stylesheet())
        self.pyrad_dropdown_label = QtWidgets.QLabel(
            "Please select the PyRad ROI to filter by:")
        self.pyrad_dropdown_label.setStyleSheet(stylesheet.get_stylesheet())

        # add dropdowns to main_layout
        self.directory_layout.addRow(self.dvh_dropdown_label)
        self.directory_layout.addRow(self.dvh_dropdown_menu)
        self.directory_layout.addRow(self.pyrad_dropdown_label)
        self.directory_layout.addRow(self.pyrad_dropdown_menu)

        self.main_layout.addLayout(self.directory_layout)
        self.setLayout(self.main_layout)

    def set_dvh_dropdown_menu_data(self, options):
        self.dvh_dropdown_menu.clear()
        self.dvh_dropdown_menu.addItems(options)

    def set_pyrad_dropdown_menu_data(self, options):
        self.pyrad_dropdown_menu.clear()
        self.pyrad_dropdown_menu.addItems(options)

    def read_in_dvh_data(self):
        if self.get_csv_input_location_dvh_data() is not None:
            data_dvh = pd.read_csv(
                f'{self.get_csv_input_location_dvh_data()}',
                on_bad_lines='skip')
            return list(
                data_dvh[data_dvh['ROI'].str.contains('PTV')]['ROI'].unique()
            )
        else:
            return "-"

    def read_in_pyrad_data(self):
        if self.get_csv_input_location_pyrad() is not None:
            data_Py = pd.read_csv(
                f'{self.get_csv_input_location_pyrad()}')
            return list(
                data_Py[data_Py['ROI'].str.contains('GTV')]['ROI'].unique()
            )
        else:
            return "-"

    def _on_dvh_path_changed(self):
        options = self.read_in_dvh_data()
        self.set_dvh_dropdown_menu_data(options)

    def _on_pyrad_path_changed(self):
        options = self.read_in_pyrad_data()
        self.set_pyrad_dropdown_menu_data(options)

    # Function for DVH Data
    def set_csv_input_location_dvh_data(self, path, enable=True,
                                        change_if_modified=False):
        """
        Set the location for the dvh .csv file.
        :param path: desired path.
        :param enable: Enable the directory text bar.
        :param change_if_modified: Change the directory if already been
                                   changed.
        """
        if not self.directory_input_dvh_data.isEnabled():
            self.directory_input_dvh_data.setText(path)
            self.directory_input_dvh_data.setEnabled(enable)
        elif change_if_modified:
            self.directory_input_dvh_data.setText(path)
            self.directory_input_dvh_data.setEnabled(enable)

        self._on_dvh_path_changed()

    def get_csv_input_location_dvh_data(self):
        """
        Get the location of the desired output directory.
        """
        if (self.directory_input_dvh_data.text() != 'No file selected'
                and self.directory_input_dvh_data.text() != expanduser("~")):
            return self.directory_input_dvh_data.text()
        else:
            return None

    def show_file_browser_dvh_data(self):
        """
        Show the file browser for selecting a folder for the Onko
        default directory.
        """
        # Open a file dialog and return chosen directory
        path = QtWidgets.QFileDialog.getOpenFileName(
            None, "Open DVH File", "",
            "CSV data files (*.csv *.CSV)")[0]

        # If chosen directory is nothing (user clicked cancel) set to
        # user home
        if path == "" and \
                self.directory_input_dvh_data.text() == 'No file selected':
            path = expanduser("~")
        elif (path == ""
              and
              (self.directory_input_dvh_data.text() != 'No file selected'
               or self.directory_input_dvh_data.text() != expanduser("~"))):
            path = self.directory_input_dvh_data.text()

        # Update file path
        self.set_csv_input_location_dvh_data(path, change_if_modified=True)

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
        if (self.directory_input_pyrad.text() != 'No file selected'
                and self.directory_input_pyrad.text() != expanduser("~")):
            return self.directory_input_pyrad.text()
        else:
            return None

    def show_file_browser_pyrad(self):
        """
        Show the file browser for selecting a folder for the Onko
        default directory.
        """
        # Open a file dialog and return chosen directory
        path = QtWidgets.QFileDialog.getOpenFileName(
            None, "Open PyRad Data File", "",
            "CSV data files (*.csv *.CSV)")[0]

        # If chosen directory is nothing (user clicked cancel) set to
        # user home
        if path == "" and \
                self.directory_input_pyrad.text() == 'No file selected':
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
        selected_options = {
            "dvh_path": self.get_csv_input_location_dvh_data(),
            "pyrad_path": self.get_csv_input_location_pyrad(),
            "dvh_value": self.get_selected_dvh_value(),
            "pyrad_value": self.get_selected_pyrad_value()
        }

        logging.debug("MachineLearningDataSelectionOptions"
                      ".get_selected_options() called")
        logging.debug(f"returning: {selected_options}")
        return selected_options
