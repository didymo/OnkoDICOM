from PySide6 import QtWidgets, QtCore, QtGui
from os.path import expanduser
import numpy as np

from src.View.StyleSheetReader import StyleSheetReader


class CheckableCombox(QtWidgets.QComboBox):
    def __init__(self):
        super().__init__()
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)

        self.lineEdit().installEventFilter(self)
        self.closeOnLineEditClick = False

        self.view().viewport().installEventFilter(self)

    def eventFilter(self, widget, event):
        if widget == self.lineEdit():
            if event.type() == QtCore.QEvent.MouseButtonRelease:
                if self.closeOnLineEditClick:
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
        self.update_line_edit_filed()
        self.closeOnLineEditClick = False

    def showPopup(self):
        super().showPopup()
        # When the popup is displayed, a click on the lineedit should close it
        self.closeOnLineEditClick = True

    def addItems(self, items, item_list=None):
        for indx, text in enumerate(items):
            try:
                data = item_list[indx]
            except (TypeError, IndexError):
                data = None
            self.addItem(text, data)

    def addItem(self, text, user_data=None):
        item = QtGui.QStandardItem()
        item.setText(text)
        if user_data is not None:
            item.setData(user_data)
        # enable checkbox setting
        item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsUserCheckable)
        item.setData(QtCore.Qt.Unchecked, QtCore.Qt.CheckStateRole)
        self.model().appendRow(item)

    def update_line_edit_filed(self):
        text_container = []

        for i in range(self.model().rowCount()):
            if self.model().item(i).checkState() == QtCore.Qt.Checked:
                text_container.append(self.model().item(i).text())
        if len(text_container) > 0:
            text_string = ", ".join(text_container)
            self.lineEdit().setText(text_string)
        else:
            self.lineEdit().setText("Not Selected")


class MachineLearningOptions(QtWidgets.QWidget):
    """
    Machine Learning options for batch processing.
    """

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
        stylesheet: StyleSheetReader = StyleSheetReader()

        label_clinical_data = QtWidgets.QLabel("Please choose the CSV file"
                                               " location for Clinical Data:")
        label_clinical_data.setStyleSheet(stylesheet.get_stylesheet())

        label_dvg = QtWidgets.QLabel("Please choose the CSV"
                                     " file location for DVH Data:")
        label_dvg.setStyleSheet(stylesheet.get_stylesheet())

        label_pyrad = QtWidgets.QLabel("Please choose the CSV"
                                       " file location for Pyradiomics Data:")
        label_pyrad.setStyleSheet(stylesheet.get_stylesheet())

        self.directory_layout = \
            QtWidgets.QFormLayout()

        # Directory text box for clinical Data
        self.directory_input_clinicalData = \
            QtWidgets.QLineEdit("No file selected")
        self.directory_input_clinicalData. \
            setStyleSheet(stylesheet.get_stylesheet())
        self.directory_input_clinicalData.setEnabled(False)

        # Button For clinical Data to set location
        self.change_button_clinicalData = QtWidgets.QPushButton("Change")
        self.change_button_clinicalData.setMaximumWidth(100)
        self.change_button_clinicalData.clicked. \
            connect(self.show_file_browser_clinical_data)
        self.change_button_clinicalData.setObjectName("NormalButton")
        self.change_button_clinicalData.setStyleSheet(stylesheet.get_stylesheet())

        # Directory text box for DVH Data
        self.directory_input_dvhData = \
            QtWidgets.QLineEdit("No file selected")
        self.directory_input_dvhData.setStyleSheet(stylesheet.get_stylesheet())
        self.directory_input_dvhData.setEnabled(False)

        # Button For DVH Data to set location
        self.change_button_dvhData = \
            QtWidgets.QPushButton("Change")
        self.change_button_dvhData.\
            setMaximumWidth(100)
        self.change_button_dvhData.clicked.\
            connect(self.show_file_browser_dvh_data)
        self.change_button_dvhData.setObjectName("NormalButton")
        self.change_button_dvhData.setStyleSheet(stylesheet.get_stylesheet())

        # Directory text box for Pyradiomics Data
        self.directory_input_pyrad = \
            QtWidgets.QLineEdit("No file selected")
        self.directory_input_pyrad.setStyleSheet(stylesheet.get_stylesheet())
        self.directory_input_pyrad.setEnabled(False)

        # Button For Pyradiomics Data to set location
        self.change_button_pyradiomicsData = \
            QtWidgets.QPushButton("Change")
        self.change_button_pyradiomicsData.\
            setMaximumWidth(100)
        self.change_button_pyradiomicsData.\
            clicked.connect(self.show_file_browser_payrad)
        self.change_button_pyradiomicsData.\
            setObjectName("NormalButton")
        self.change_button_pyradiomicsData.\
            setStyleSheet(stylesheet.get_stylesheet())

        # Set Clinical Data
        self.directory_layout.addWidget(label_clinical_data)
        self.directory_layout.addRow(self.directory_input_clinicalData)
        self.directory_layout.addRow(self.change_button_clinicalData)

        # Set DVH data
        self.directory_layout.addWidget(label_dvg)
        self.directory_layout.addRow(self.directory_input_dvhData)
        self.directory_layout.addRow(self.change_button_dvhData)

        # Set Pyradiomics data
        self.directory_layout.addWidget(label_pyrad)
        self.directory_layout.addRow(self.directory_input_pyrad)
        self.directory_layout.addRow(self.change_button_pyradiomicsData)

        self.main_layout.addLayout(self.directory_layout)

        # Table
        self.filter_table = QtWidgets.QTableWidget(0, 0)
        self.filter_table.setStyleSheet(stylesheet.get_stylesheet())

        # Modify Table
        title_listof_headers = ["Function Name", "Selected Value", "Comment"]
        for title in title_listof_headers:
            col = self.filter_table.columnCount()
            self.filter_table.insertColumn(col)
            self.filter_table.setColumnWidth(col, 600)
        # set column Names
        self.filter_table.setHorizontalHeaderLabels(title_listof_headers)

        # Set 1st Column
        function_names = ["Features", "Target",
                          "Choose Type of the"
                          " Target Column",
                          "Rename Values "
                          "in Target",
                          "ML with Tuning"]
        # set 3rd Column
        comments = ["Please select columns "
                    "to pass to the ML model."
                    "If you won't select any columns "
                    "then it takes all columns and passes to ML",
                    "Please select a column "
                    "for the target to ML model",
                    "Please select a column type "
                    "for the ML model based on that column"
                    " will be chosen ML",
                    "Only if the Category type"
                    " is binary [0,1]!",
                    "Usually, Running improves the model,"
                    " but it takes between 20 - 40 min"
                    " to Tune the Model."
                    "It does not guarantee better "
                    "performance compared to default ML"
                    ]

        for i in range(len(function_names)):
            function_name = QtWidgets.QTableWidgetItem(function_names[i])
            comment = QtWidgets.QTableWidgetItem(comments[i])
            self.filter_table.insertRow(i)
            self.filter_table.setRowHeight(i, 50)
            self.filter_table.setItem(i, 0, function_name)
            self.filter_table.setItem(i, 2, comment)

        # add features
        self.combox_feature = CheckableCombox()
        comment = QtWidgets.QTableWidgetItem("No Clinical-data-SR"
                                             "files located in current"
                                             "selected directory")
        self.filter_table.setItem(0, 1, comment)

        # add target
        self.combox_target = QtWidgets.QComboBox()
        self.combox_target.setStyleSheet(stylesheet.get_stylesheet())
        self.combox_target.setEditable(True)
        self.combox_target.lineEdit().setReadOnly(True)
        comment = QtWidgets.QTableWidgetItem("No Clinical-data-SR"
                                             "files located in current"
                                             "selected directory")
        self.filter_table.setItem(1, 1, comment)

        # add Type
        self.combox_type = QtWidgets.QComboBox()
        self.combox_type.setStyleSheet(stylesheet.get_stylesheet())
        self.combox_type.setEditable(True)
        self.combox_type.lineEdit().setReadOnly(True)
        self.combox_type.addItems(["category", "numerical"])
        self.filter_table.setCellWidget(2, 1, self.combox_type)

        # add Tune
        self.combox_tune = QtWidgets.QComboBox()
        self.combox_tune.setStyleSheet(stylesheet.get_stylesheet())
        self.combox_tune.setEditable(True)
        self.combox_tune.lineEdit().setReadOnly(True)
        self.combox_tune.addItems(["no", "yes"])
        self.filter_table.setCellWidget(4, 1, self.combox_tune)

        self.main_layout.addWidget(self.filter_table)
        self.setLayout(self.main_layout)

        self.filter_table.cellClicked.connect(self.select_rename_value_cell)

    def store_data(self, data_dic):
        """
                Gets User Selected Columns
        """
        # removes the Patient Identifier (assumed to be first column
        # in the dataset)
        # As the column name may be changing we cannot hard code the
        # column name
        # not a necessary filter option as specified in requirements
        if len(data_dic) > 0:
            self.dataDictionary = data_dic.copy()
            self.dataDictionary.pop(list(self.dataDictionary)[0])

            self.combox_feature.addItems(self.dataDictionary.keys())
            self.combox_target.addItems(self.dataDictionary.keys())

            self.filter_table.setCellWidget(0, 1, self.combox_feature)
            self.combox_feature.update_line_edit_filed()

            self.filter_table.setCellWidget(1, 1, self.combox_target)
        else:
            pass

    def check_binary(self, dict):
        """
        checks if the selected target is binary
        """
        str_list = dict
        # Remove None Values
        if None in str_list:
            str_list.remove(None)

        arr = np.array(str_list)
        arr = arr[arr != ""]
        arr = arr[arr != " "]

        # Check if binary
        if np.isin(arr, [0, 1]).all() or np.isin(arr, ['0', '1']).all():
            self.binaryData = True
            return True
        else:
            self.binaryData = False
            return False

    def rename_values(self, target_name):
        self.binaryData = self.check_binary(self.dataDictionary[target_name])
        if self.binaryData:
            output = set()
            for x in self.dataDictionary[target_name]:
                output.add(str(x))
            text_rename = str(sorted(list(output)))
            return text_rename
        else:
            return f"Selected column is not Binary {target_name}"

    def select_rename_value_cell(self,
                                 row, column):
        """
        Allows user to rename values of the target
        :param row: row index that was clicked
        :param column: column index that was clicked
        """

        header = self.filter_table.horizontalHeaderItem(column).text()
        if header == "Selected Value":
            if row == 3:
                if self.combox_target.currentText() != "":
                    rename = self.rename_values(
                        self.combox_target.currentText())
                    comment = QtWidgets.QTableWidgetItem(rename)
                    self.filter_table.setItem(3, 1, comment)

    # Function for Clinical Data
    def set_csv_output_location_clinical_data(self,
                                              path, enable=True,
                                              change_if_modified=False):
        """
        Set the location for the ClinicalData .csv file.
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

    def get_csv_output_location_clinical_data(self):
        """
        Get the location of the desired output directory.
        """
        return self.directory_input_clinicalData.text()

    def show_file_browser_clinical_data(self):
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
        if path == "" and \
                self.directory_input_clinicalData.text() \
                == 'No file selected':
            path = expanduser("~")
        elif (path == ""
              and
              (self.directory_input_clinicalData.text() != 'No file'
                                                           ' selected'
               or self.directory_input_clinicalData.text() != expanduser(
                          "~"))):
            path = self.directory_input_clinicalData.text()

        # Update file path
        self.set_csv_output_location_clinical_data(path,
                                                   change_if_modified=True)

    # Function for DVH Data
    def set_csv_output_location_dvh_data(self, path, enable=True,
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

    def get_csv_output_location_dvh_data(self):
        """
        Get the location of the desired output directory.
        """
        return self.directory_input_dvhData.text()

    def show_file_browser_dvh_data(self):
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
        if path == "" and self.directory_input_dvhData.text() == 'No file' \
                                                                 ' selected':
            path = expanduser("~")
        elif (path == ""
              and
              (self.directory_input_dvhData.text() != 'No file '
                                                      'selected'
               or self.directory_input_dvhData.text() != expanduser("~"))):
            path = self.directory_input_dvhData.text()

        # Update file path
        self.set_csv_output_location_dvh_data(path, change_if_modified=True)

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
        if path == "" and self.directory_input_pyrad.text() == 'No file ' \
                                                               'selected':
            path = expanduser("~")
        elif (path == ""
              and
              (self.directory_input_pyrad.text() != 'No file selected'
               or self.directory_input_pyrad.text() != expanduser("~"))):
            path = self.directory_input_pyrad.text()

        # Update file path
        self.set_csv_output_location_pyrad(path, change_if_modified=True)

    def get_feature(self):
        """
        get selected columns
        """
        features = self.combox_feature.currentText()
        features = features.replace('[', '').\
            replace(']', '').\
            replace("'", "").\
            replace('\n', "").\
            replace(" ", "")
        features = features.split(',')
        # if user do not select any features then it reads all features
        if 'NotSelected' in features:
            return None

        return features

    def get_target(self):
        """
        get selected target
        """
        return self.combox_target.currentText()

    def get_type(self):
        """
        get selected type
        """
        return self.combox_type.currentText()

    def get_rename(self):
        """
        get selected values
        """
        if self.binaryData:
            rename = self.filter_table.item(3, 1).text()
            rename = rename.replace('[', '').replace(']', '').replace("'", "")
            rename = rename.split(',')
            return rename
        return None

    def get_tune(self):
        """
        get selected value
        """
        if self.combox_tune.currentText() == 'no':
            return False
        else:
            return True
