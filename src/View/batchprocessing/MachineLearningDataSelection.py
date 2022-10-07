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
        self.change_button_pyradiomicsData.clicked.connect(self.show_file_browser_payrad)
        self.change_button_pyradiomicsData.setObjectName("NormalButton")
        self.change_button_pyradiomicsData.setStyleSheet(self.stylesheet)

        # Set button read DVH and Pyradiomics
        self.read_button_dvh_pyrad = QtWidgets.QPushButton("Read DVH and Pyradiomics")
        self.read_button_dvh_pyrad.clicked.connect(self.read_dvh_payrad)
        self.read_button_dvh_pyrad.setObjectName("NormalButton")
        self.read_button_dvh_pyrad.setStyleSheet(self.stylesheet)

        # Set DVH data
        self.directory_layout.addWidget(label_DVG)
        self.directory_layout.addRow(self.directory_input_dvhData)
        self.directory_layout.addRow(self.change_button_dvhData)

        # Set Pyradiomics data
        self.directory_layout.addWidget(label_Pyrad)
        self.directory_layout.addRow(self.directory_input_pyrad)
        self.directory_layout.addRow(self.change_button_pyradiomicsData)

        self.directory_layout.addRow(self.read_button_dvh_pyrad)


        self.main_layout.addLayout(self.directory_layout)


        self.setLayout(self.main_layout)


    def read_dvh_payrad(self):
        unique_name_dvh = None
        try:
            data_dvh = pd.read_csv(f'{self.get_csv_output_location_dvhData()}', on_bad_lines='skip').rename(
                columns={"Patient ID": "HASHidentifier"})
        except:
            logging.debug("Wrong path for DVH")
        try:
            data_Py = pd.read_csv(f'{self.get_csv_output_location_payrad()}').rename(columns={"Hash ID": "HASHidentifier"})
        except:
            logging.debug("Wrong path for pyRadiomics")

        try:
            unique_name_dvh = {
                "DVH ROI": list(data_dvh[data_dvh['ROI'].str.contains('PTV')]['ROI'].unique()),
                "PyRadiomics ROI": list(data_Py[data_Py['ROI'].str.contains('GTV')]['ROI'].unique())
            }
        except:
            logging.debug("Error in loading pyRadiomics ROI and DVH ROI ")

        if unique_name_dvh!=None:
            # Table
            self.filter_table = QtWidgets.QTableWidget(0, 0)
            self.filter_table.setStyleSheet(self.stylesheet)

            self.main_layout.addWidget(self.filter_table)

            # Modify Table
            titleListofHeaders = ["DVH ROI", "PyRadiomics ROI"]
            for title in titleListofHeaders:
                col = self.filter_table.columnCount()
                self.filter_table.insertColumn(col)
                self.filter_table.setColumnWidth(col, 600)
                for row in range(0, len(unique_name_dvh[title])):
                    str_value = str(unique_name_dvh[title][row])
                    # filters out blank options
                    if str_value == "":
                        continue
                    filter_value = QtWidgets.QTableWidgetItem(str_value)

                    if row >= self.filter_table.rowCount():
                        self.filter_table.insertRow(row)

                    self.filter_table.setItem(row, col, filter_value)


        # set column Names
            self.filter_table.setHorizontalHeaderLabels(titleListofHeaders)
        else:
            logging.debug("Can not load DVH and pyRadiomics ROI to table")


    def select_value_cell(self, row, column):
        """
        Allows user to rename values of the target
        :param row: row index that was clicked
        :param column: column index that was clicked
        """
        header = self.filter_table.horizontalHeaderItem(column).text()
        if header == "Selected Value":
            if (row == 3):
                if self.combox_target.currentText() != "":
                    rename = self.rename_values(self.combox_target.currentText())
                    comment = QtWidgets.QTableWidgetItem(rename)
                    self.filter_table.setItem(3, 1, comment)
        if header == "Function Name":
                if (row == 3):
                    self.get_rename()

    # Function for DVH Data
    def set_csv_output_location_dvhData(self, path, enable=True,
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

    # Function for Pyrad Data
    def set_csv_output_location_pyrad(self, path, enable=True,
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


