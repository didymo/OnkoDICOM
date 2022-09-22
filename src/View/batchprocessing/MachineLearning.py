import platform
from PySide6 import QtWidgets, QtCore, QtGui
from os.path import expanduser
from src.Controller.PathHandler import resource_path

import pandas as pd


class CheckableCombox(QtWidgets.QComboBox):
    def __init__(self):
        super().__init__()
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self.closeOnlineEditClick = False

        self.lineEdit().installEventFilter(self)
        self.view().viewport().installEventFilter(self)
        self.model().dataChanged.connect(self.updateLineEditFiled())

    def eventFilter(self, widget, event):
        if widget == self.lineEdit():
            if event.type() == QtCore.QEvent.MouseButtonRelease:
                if self.closeOnlineEditClick:
                    self.hidePopup()
                else:
                    self.showPopup()
                return True
            return super().eventFilter(widget, event)

        if widget == self.view().viewport():
            if event.type == QtCore.QEvent.MouseButtonRelease:
                indx = self.view().indexAt(event.pos())
                item = self.model().item(indx.row())
                if item.checkState() == QtCore.Qt.Checked:
                    item.setCheckState(QtCore.Qt.Unchecked)
                else:
                    item.setCheckState(QtCore.Qt.Checked)
                return True
            return super().eventFilter(widget, event)

    def hidePopup(self):
        super().hidePopup()
        self.startTimer(100)

    def addItems(self, items, itemList=None):
        for indx, text in enumerate(items):
            try:
                data = itemList[indx]
            except (TypeError, IndexError):
                data = None
            self.addItem(text, data)

    def addItem(self, text, userData=None):
        item = QtGui.QStandardItem()
        item.setText(text)
        if not userData is None:
            item.setData(userData)
        # enable checkbox setting
        item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsUserCheckable)
        item.setData(QtCore.Qt.Unchecked, QtCore.Qt.CheckStateRole)
        self.model().appendRow(item)

    def updateLineEditFiled(self):
        text_container = []
        for i in range(self.model().rowCount()):
            if self.model().item(i).checkState() == QtCore.Qt.Checked:
                print(self.model().item(i))
                text_container.append(self.model().item(i).text())
        text_string = ", ".join(text_container)
        self.lineEdit().setText(text_string)


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

        # Button For clinical Data to set location
        self.change_button_clinicalData = QtWidgets.QPushButton("Change")
        self.change_button_clinicalData.setMaximumWidth(100)
        self.change_button_clinicalData.clicked.connect(self.show_file_browser_clinicalData)
        self.change_button_clinicalData.setObjectName("NormalButton")
        self.change_button_clinicalData.setStyleSheet(self.stylesheet)

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

        # Set Clinical Data
        self.directory_layout.addWidget(label_clinicalData)
        self.directory_layout.addRow(self.directory_input_clinicalData)
        self.directory_layout.addRow(self.change_button_clinicalData)

        # Set DVH data
        self.directory_layout.addWidget(label_DVG)
        self.directory_layout.addRow(self.directory_input_dvhData)
        self.directory_layout.addRow(self.change_button_dvhData)

        # Set Pyradiomics data
        self.directory_layout.addWidget(label_Pyrad)
        self.directory_layout.addRow(self.directory_input_pyrad)
        self.directory_layout.addRow(self.change_button_pyradiomicsData)

        self.main_layout.addLayout(self.directory_layout)

        # Table
        self.filter_table = QtWidgets.QTableWidget(0, 0)
        self.filter_table.setStyleSheet(self.stylesheet)

        # Modify Table
        titleListofHeaders = ["Function Name", "Selected Value", "Comment"]
        for title in titleListofHeaders:
            col = self.filter_table.columnCount()
            self.filter_table.insertColumn(col)
            self.filter_table.setColumnWidth(col, 600)
        # set column Names
        self.filter_table.setHorizontalHeaderLabels(titleListofHeaders)

        # Set 1st Column
        functionNames = ["Features", "Target",
                         "Choose Type of the Target Column",
                         "Rename Values in Target",
                         "ML with Tuning"]
        # set 3rd Column
        comments = ["Please select a column to pass to the ML model",
                    "Please select a column for the target to ML model",
                    "Please select a column type for the ML model based on that column will be chosen ML",
                    "Only if the Category type is binary [0,1]!",
                    "Usually, Running improves the model, but it takes from 20 - 40 min to Tune the Model."
                    "It does not guarantee better performance compared to default ML"
                    ]

        for i in range(len(functionNames)):
            function_names = QtWidgets.QTableWidgetItem(functionNames[i])
            comment = QtWidgets.QTableWidgetItem(comments[i])
            self.filter_table.insertRow(i)
            self.filter_table.setRowHeight(i, 50)
            self.filter_table.setItem(i, 0, function_names)
            self.filter_table.setItem(i, 2, comment)

        # add features
        self.combox_feature = CheckableCombox()
        comment = QtWidgets.QTableWidgetItem("Select Features")
        self.filter_table.setItem(0, 1, comment)

        # add target
        self.combox_target = QtWidgets.QComboBox()
        self.combox_target.setEditable(True)
        self.combox_target.lineEdit().setReadOnly(True)
        self.combox_target.closeOnlineEditClick = False
        comment = QtWidgets.QTableWidgetItem("Select Target")
        self.filter_table.setItem(1, 1, comment)

        # add Type
        self.combox_type = QtWidgets.QComboBox()
        self.combox_type.setEditable(True)
        self.combox_type.lineEdit().setReadOnly(True)
        self.combox_type.closeOnlineEditClick = False
        self.combox_type.addItems(["category", "numerical"])
        self.filter_table.setCellWidget(2, 1, self.combox_type)

        # add Tune
        self.combox_tune = QtWidgets.QComboBox()
        self.combox_tune.setEditable(True)
        self.combox_tune.lineEdit().setReadOnly(True)
        self.combox_tune.closeOnlineEditClick = False
        self.combox_tune.addItems(["yes", "no"])
        self.filter_table.setCellWidget(4, 1, self.combox_tune)

        self.main_layout.addWidget(self.filter_table)
        self.setLayout(self.main_layout)

        self.filter_table.cellClicked.connect(self.select_filter_option_cell)

    def addFeature(self):
        data = pd.read_csv(self.get_csv_output_location_clinicalData())
        columnNamesList = list(data.columns)

        self.combox_feature.addItems(columnNamesList)
        self.filter_table.setCellWidget(0, 1, self.combox_feature)

    def addTarget(self):
        data = pd.read_csv(self.get_csv_output_location_clinicalData())
        columnNamesList = list(data.columns)
        self.combox_target.addItems(columnNamesList)
        self.filter_table.setCellWidget(1, 1, self.combox_target)

    def renameValues(self,targetName):
        data = pd.read_csv(self.get_csv_output_location_clinicalData())
        values = list(sorted(data[targetName].unique()))
        text_rename = ", ".join(str(values))
        return text_rename




    def select_filter_option_cell(self, row, column):
        """
        Toggles the selected options green and stores value
        :param row: row index that was clicked
        :param column: column index that was clicked
        """
        item = self.filter_table.item(row, column)
        header = self.filter_table.horizontalHeaderItem(column).text()
        if header == "Selected Value":
            if (row == 1):
                self.addTarget()
            elif (row == 0):
                self.addFeature()
            elif (row == 3):
                if self.combox_target.currentText() != "":
                    rename = self.renameValues(self.combox_target.currentText())
                    comment = QtWidgets.QTableWidgetItem(rename)
                    self.filter_table.setItem(3, 1, comment)



        elif (header == "Function Name"):
            if (row == 1):
                print(self.combox_target.currentText())
                self.combox_feature.updateLineEditFiled()

    # Function for Clinical Data
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

    # Function for DVH Data
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

    # Function for DVH Data
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

    # Function for Pyrad Data
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
