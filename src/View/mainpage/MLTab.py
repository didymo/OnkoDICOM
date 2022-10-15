import platform
import os
from os.path import expanduser
from src.Controller.PathHandler import resource_path
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtWidgets import QComboBox, QPushButton, QMessageBox
import datetime
import pandas as pd
import logging
from src.Model.MachineLearningTester import MachineLearningTester
pd.options.mode.chained_assignment = None  # default='warn'


class MLTab(QtWidgets.QWidget):
    """
    Tab for testing Machine learning model
    """

    def __init__(self):
        """
        Initialise the class
        """
        QtWidgets.QWidget.__init__(self)

        # Create the main layout
        self.main_layout = QtWidgets.QVBoxLayout()

        self.selected_model_directory = ""

        # Get the stylesheet
        if platform.system() == 'Darwin':
            self.stylesheet_path = "res/stylesheet.qss"
        else:
            self.stylesheet_path = "res/stylesheet-win-linux.qss"
        self.stylesheet = open(resource_path(self.stylesheet_path)).read()

        self.current_widgets = []

        self.clinical_data_csv_path = ""
        self.dvh_data_csv_path = ""
        self.pyrad_data_csv_path = ""

        self.directory_layout = QtWidgets.QFormLayout()
        self.main_layout.addLayout(self.directory_layout)

        self.navigate_to_select_csvs()

        self.setLayout(self.main_layout)

    def set_csv_input_location_clinical_data(self,
                                             path,
                                             enable=True,
                                             change_if_modified=False):
        """
        Set the location for the clinical_data-SR2CSV resulting .csv file.
        :param path: desired path.
        :param enable: Enable the directory text bar.
        :param change_if_modified: Change the directory if already been
                                   changed.
        """
        if not self.directory_input_clinical_data.isEnabled():
            self.directory_input_clinical_data.setText(path)
            self.directory_input_clinical_data.setEnabled(enable)
        elif change_if_modified:
            self.directory_input_clinical_data.setText(path)
            self.directory_input_clinical_data.setEnabled(enable)

        self.clinical_data_csv_path = path

    def get_csv_input_location_clinical_data(self):
        """
        Get the location of the desired output directory.
        """
        return self.directory_input_clinical_data.text()

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
        if (path == ""
                and self.directory_input_clinical_data.text()
                == 'No file selected'):
            path = expanduser("~")
        elif (path == ""
              and
              (self.directory_input_clinical_data.text() != 'No file selected'
               or
               self.directory_input_clinical_data.text() != expanduser("~"))):
            path = self.directory_input_clinical_data.text()

        # Update file path
        self.set_csv_input_location_clinical_data(
            path, change_if_modified=True)

    def show_file_browser_saved_model(self):
        """
        Show the file browser for selecting a folder for the Onko
        default directory.
        """
        # Open a file dialog and return chosen directory
        path = QtWidgets.QFileDialog.getExistingDirectory(
            None, "Open Directory")

        # Update file path
        self.directory_input_ml_model.setText(path)
        self.selected_model_directory = path

        self.on_model_directory_changed()

    def set_csv_output_location_dvh_data(self, path, enable=True,
                                         change_if_modified=False):
        """
        Set the location for the clinical_data-SR2CSV resulting .csv file.
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

        self.dvh_data_csv_path = path

    def get_csv_output_location_dvh_data(self):
        """
        Get the location of the desired output directory.
        """
        return self.directory_input_dvh_data.text()

    def show_file_browser_dvh_data(self):
        """
        Show the file browser for selecting a folder for the Onko
        default directory.
        """
        # Open a file dialog and return chosen directory
        path = QtWidgets.QFileDialog.getOpenFileName(
            None, "Open DVH Data File", "",
            "CSV data files (*.csv *.CSV)")[0]

        # If chosen directory is nothing (user clicked cancel) set to
        # user home
        if (path == "" and
                self.directory_input_dvh_data.text() == 'No file selected'):
            path = expanduser("~")
        elif (path == ""
              and
              (self.directory_input_dvh_data.text() != 'No file selected'
               or self.directory_input_dvh_data.text() != expanduser("~"))):
            path = self.directory_input_dvh_data.text()

        # Update file path
        self.set_csv_output_location_dvh_data(path, change_if_modified=True)

    def set_csv_output_location_pyrad(self, path, enable=True,
                                      change_if_modified=False):
        """
        Set the location for the clinical_data-SR2CSV resulting .csv file.
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

        self.pyrad_data_csv_path = path

    def get_csv_output_location_pyrad(self):
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
            None, "Open Pyrad File", "",
            "CSV data files (*.csv *.CSV)")[0]

        # If chosen directory is nothing (user clicked cancel) set to
        # user home
        if (path == "" and
                self.directory_input_pyrad.text() == 'No file selected'):
            path = expanduser("~")
        elif (path == ""
              and
              (self.directory_input_pyrad.text() != 'No file selected'
               or self.directory_input_pyrad.text() != expanduser("~"))):
            path = self.directory_input_pyrad.text()

        # Update file path
        self.set_csv_output_location_pyrad(path, change_if_modified=True)

    def navigate_to_select_csvs(self):
        """
        Updates UI to show all options to select csv data inputs.
        """
        self.clear_current_widgets()

        self.label_clinical_data = QtWidgets.QLabel(
            "Please choose the CSV file location for Clinical Data:")
        self.label_clinical_data.setStyleSheet(self.stylesheet)
        self.current_widgets.append(self.label_clinical_data)

        self.label_DVG = QtWidgets.QLabel(
            "Please choose the CSV file location for DVH Data:")
        self.label_DVG.setStyleSheet(self.stylesheet)
        self.current_widgets.append(self.label_DVG)

        self.label_Pyrad = QtWidgets.QLabel(
            "Please choose the CSV file location for Pyradiomics Data:")
        self.label_Pyrad.setStyleSheet(self.stylesheet)
        self.current_widgets.append(self.label_Pyrad)

        # Directory text box for clinical Data
        self.directory_input_clinical_data = QtWidgets.QLineEdit(
            "No file selected")
        self.directory_input_clinical_data.setStyleSheet(self.stylesheet)
        self.directory_input_clinical_data.setEnabled(False)
        self.current_widgets.append(self.directory_input_clinical_data)

        # Button For clinical Data to set location
        self.change_button_clinical_data = QtWidgets.QPushButton(
            "Change")
        self.change_button_clinical_data.setMaximumWidth(100)
        self.change_button_clinical_data.clicked.connect(
            self.show_file_browser_clinical_data
            )
        self.change_button_clinical_data.setObjectName("NormalButton")
        self.change_button_clinical_data.setStyleSheet(self.stylesheet)
        self.current_widgets.append(self.change_button_clinical_data)

        # Directory text box for DVH Data
        self.directory_input_dvh_data = QtWidgets.QLineEdit(
            "No file selected")
        self.directory_input_dvh_data.setStyleSheet(self.stylesheet)
        self.directory_input_dvh_data.setEnabled(False)
        self.current_widgets.append(self.directory_input_dvh_data)

        # Button For DVH Data to set location
        self.change_button_dvh_data = QtWidgets.QPushButton("Change")
        self.change_button_dvh_data.setMaximumWidth(100)
        self.change_button_dvh_data.clicked.connect(
            self.show_file_browser_dvh_data
            )
        self.change_button_dvh_data.setObjectName("NormalButton")
        self.change_button_dvh_data.setStyleSheet(self.stylesheet)
        self.current_widgets.append(self.change_button_dvh_data)

        # Directory text box for Pyradiomics Data
        self.directory_input_pyrad = QtWidgets.QLineEdit(
            "No file selected")
        self.directory_input_pyrad.setStyleSheet(self.stylesheet)
        self.directory_input_pyrad.setEnabled(False)
        self.current_widgets.append(self.directory_input_pyrad)

        # Button For Pyradiomics Data to set location
        self.change_button_pyradiomicsData = QtWidgets.QPushButton(
            "Change")
        self.change_button_pyradiomicsData.setMaximumWidth(100)
        self.change_button_pyradiomicsData.clicked.connect(
            self.show_file_browser_pyrad
            )
        self.change_button_pyradiomicsData.setObjectName("NormalButton")
        self.change_button_pyradiomicsData.setStyleSheet(self.stylesheet)
        self.current_widgets.append(self.change_button_pyradiomicsData)

        # Set Clinical Data
        self.directory_layout.addWidget(self.label_clinical_data)
        self.directory_layout.addRow(self.directory_input_clinical_data)
        self.directory_layout.addRow(self.change_button_clinical_data)

        # Set DVH data
        self.directory_layout.addWidget(self.label_DVG)
        self.directory_layout.addRow(self.directory_input_dvh_data)
        self.directory_layout.addRow(self.change_button_dvh_data)

        # Set Pyradiomics data
        self.directory_layout.addWidget(self.label_Pyrad)
        self.directory_layout.addRow(self.directory_input_pyrad)
        self.directory_layout.addRow(self.change_button_pyradiomicsData)

        # Initialise Next Button
        self.next_button = QPushButton()
        self.next_button.setText("Next")
        self.next_button.clicked.connect(
            self.navigate_to_model_selection
            )
        self.directory_layout.addWidget(self.next_button)
        self.current_widgets.append(self.next_button)

    def clear_current_widgets(self):
        """
        Clears all widgets in self.current_widgets.
        This should be all widgets within this tab
        but requires they are all added to self.current_widgets
        when created.
        """
        for widget in self.current_widgets:
            widget.setParent(None)

    def navigate_to_model_selection(self):
        """
        Checks if something has been selected for each directory input
        and will open a message box if not all paths are supplied.
        Then will update UI with model selection options.
        """
        if any(
            (self.get_csv_input_location_clinical_data() == "No file selected",
                self.get_csv_output_location_dvh_data() == "No file selected",
                self.get_csv_output_location_pyrad() == "No file selected")):
            dlg = QMessageBox(self)
            dlg.setWindowTitle("Error!")
            dlg.setText("Please Provide a path for each file")
            button = dlg.exec_()

            if button == QMessageBox.Ok:
                print("Try Again")
            return

        self.clear_current_widgets()

        # Create what directory to select model from
        self.label_ml_model = QtWidgets.QLabel(
            "Please choose the directory where the Machine"
            "learning models have been stored:")
        self.current_widgets.append(self.label_ml_model)
        self.directory_layout.addWidget(self.label_ml_model)

        # Directory text box for clinical Data
        self.directory_input_ml_model = QtWidgets.QLineEdit("No file selected")
        self.directory_input_ml_model.setEnabled(False)
        self.current_widgets.append(self.directory_input_ml_model)
        self.directory_layout.addRow(self.directory_input_ml_model)

        # Button For clinical Data to set location
        self.change_button_ml_model = QtWidgets.QPushButton("Change")
        self.change_button_ml_model.setMaximumWidth(100)
        self.change_button_ml_model.clicked.connect(
            self.show_file_browser_saved_model)
        self.current_widgets.append(self.change_button_ml_model)
        self.directory_layout.addRow(self.change_button_ml_model)

        # create dropdown menu
        self.label_combobox = QtWidgets.QLabel("Select model:")
        self.current_widgets.append(self.label_combobox)
        self.directory_layout.addWidget(self.label_combobox)

        self.combobox = QComboBox()
        self.directory_layout.addRow(self.combobox)
        self.combobox.setEnabled(False)
        self.current_widgets.append(self.combobox)

        # Initialise Next Button
        self.next_button = QPushButton()
        self.next_button.setText("Run model")
        self.next_button.clicked.connect(self.run_prediction)
        self.current_widgets.append(self.next_button)
        self.directory_layout.addWidget(self.next_button)

        # add back button
        self.back_button = QPushButton()
        self.back_button.setText("Back")
        self.back_button.clicked.connect(self.navigate_to_select_csvs)
        self.current_widgets.append(self.back_button)
        self.directory_layout.addWidget(self.back_button)

    def on_model_directory_changed(self):
        """
        Called when model directory changed. Searches the
        selected directory and any directorys at a depth of 1
        below this selected directory for folders containing
        the necessary model files. ["_ml.pkl", "_params.txt",
        "_scaler.pkl"]. Updates the dropdown with these model
        names.
        """
        # search directory for all necessary files
        model_options = []

        directories = [self.selected_model_directory]

        logging.debug(
            f"MLTab.selected_model_directory: {self.selected_model_directory}")

        if not os.path.isdir(self.selected_model_directory):
            self.combobox.clear()
            self.combobox.setEnabled(False)
            return

        for directory in os.listdir(self.selected_model_directory):
            subdirectory = f"{self.selected_model_directory}/{directory}"

            if os.path.isdir(subdirectory):
                directories.append(subdirectory)

        for directory in directories:
            if not os.path.isdir(directory):
                continue

            save_file_suffixes = {"_ml.pkl": 0,
                                  "_params.txt": 0,
                                  "_scaler.pkl": 0}
            save_file_names = []

            for file in os.listdir(directory):
                for suffix in save_file_suffixes:
                    if str(file).endswith(suffix):
                        save_file_names.append(file)
                        save_file_suffixes[suffix] += 1

            valid = True
            for key, value in save_file_suffixes.items():
                if value != 1:
                    valid = False

            if valid:
                model_name = "_".join(save_file_names[0].split("_")[:-1])
                model_options.append(model_name)

        # display all found models in dropdown to be selected from
        self.combobox.clear()

        if len(model_options) > 0:
            self.combobox.setEnabled(True)
        else:
            self.combobox.setEnabled(False)

        logging.debug(
            f"Model_options found in selected directory: {model_options}"
        )

        self.combobox.addItems(model_options)

    def get_selected_model(self):
        """
        Gets the selected model string in the dropdown
        Returns:
            string of the model name selected from the dropdown
        """
        if self.combobox.isEnabled():
            return self.combobox.currentText()

    def get_model_path(self):
        """
        Gets the model path that was selected
        Returns:
            string of the directory that contains the saved model
            files
        """
        if (self.directory_input_ml_model.text().endswith(
                self.get_selected_model()
                )):
            return self.directory_input_ml_model.text()
        else:
            return f"{self.directory_input_ml_model.text()}/" \
                f"{self.get_selected_model()}"

    def run_prediction(self):
        """
        Predict values for specified target column using
        specified csv datasets provided and opens window with
        results
        """
        model_path = self.get_model_path()
        logging.debug(f"MLTab.get_model_path(): {model_path}")

        # trigger ML model to run
        # requires the directory for the 3 csvs + selected model directory
        ml_tester = MachineLearningTester(
            self.clinical_data_csv_path,
            self.dvh_data_csv_path,
            self.pyrad_data_csv_path,
            model_path,
            self.get_selected_model()
        )

        try:
            ml_tester.predict_values()
            results = f"According to the '{ml_tester.get_model_name()}' " \
                f"model located in '{self.get_model_path()}'," \
                "the following values " \
                f"have been predicted: '{ml_tester.get_predicted_values()}' " \
                f"for the column: '{ml_tester.get_target()}'"
        except Exception as e:
            results = f"Failed to predict value because of: {e}"

        logging.debug(f"Results: {results}")

        # once run will trigger results popup window
        ml_results_window = MLResultsWindow()
        ml_results_window.set_results_values(results)
        ml_results_window.set_ml_tester(ml_tester)

        ml_results_window.exec_()


class MLResultsWindow(QtWidgets.QDialog):
    """
    This class creates a GUI window for displaying a summary of batch
    processing. It inherits from QDialog.
    """

    def __init__(self):
        """
        Initialises class.
        """
        QtWidgets.QDialog.__init__(self)
        self.ml_tester = None
        self.params = None
        self.scaling = None

        # # Set maximum width, icon, and title
        self.setFixedSize(450, 450)
        self.setWindowTitle("Machine Learning Model Test Results")
        window_icon = QtGui.QIcon()
        window_icon.addPixmap(
            QtGui.QPixmap(resource_path("res/images/icon.ico")),
            QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(window_icon)

        # Create widgets
        self.summary_label = QtWidgets.QLabel()
        self.summary_label.setWordWrap(True)
        self.scroll_area = QtWidgets.QScrollArea()
        self.save_ml_predicted_txt = QtWidgets.QPushButton(
            "Save Txt file with above information"
            )
        self.save_ml_predicted_csv = QtWidgets.QPushButton(
            "Save CSV with predicted values"
            )

        # # Get stylesheet
        if platform.system() == 'Darwin':
            self.stylesheet_path = "res/stylesheet.qss"
        else:
            self.stylesheet_path = "res/stylesheet-win-linux.qss"
        self.stylesheet = open(
            resource_path(self.stylesheet_path)
            ).read()

        # Set stylesheet
        self.summary_label.setStyleSheet(self.stylesheet)
        self.scroll_area.setStyleSheet(self.stylesheet)
        self.save_ml_predicted_txt.setStyleSheet(self.stylesheet)
        self.save_ml_predicted_csv.setStyleSheet(self.stylesheet)

        # Make QLabel wrap text
        self.summary_label.setWordWrap(True)

        # Set scroll area properties
        self.scroll_area.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarAsNeeded)
        self.scroll_area.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.summary_label)

        # Create layout
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.scroll_area)
        self.layout.addStretch(1)
        self.layout.addWidget(self.save_ml_predicted_txt)
        self.layout.addWidget(self.save_ml_predicted_csv)

        # Connect button to functions
        self.save_ml_predicted_txt.clicked.connect(
            self.save_ml_txt_with_predicted_values_clicked
            )
        self.save_ml_predicted_csv.clicked.connect(
            self.save_ml_csv_with_predicted_values_clicked
            )

        # Set layout of window
        self.setLayout(self.layout)

    def set_results_values(self, results_string):
        """
        Sets the summary text.
        :param results_string: text string describing the prediction
        results
        """

        self.summary_label.setText(results_string)

    def set_ml_tester(self, ml_tester):
        """
        Sets model intance in popup.
        """
        self.ml_tester = ml_tester

    def save_ml_csv_with_predicted_values_clicked(self):
        """
        Saves a csv including the predicted values.
        """
        file_path = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Open Directory",
            "",
            QtWidgets.QFileDialog.ShowDirsOnly
            | QtWidgets.QFileDialog.DontResolveSymlinks
            )
        if file_path:
            self.ml_tester.save_into_csv(f'{file_path}/')

    def save_ml_txt_with_predicted_values_clicked(self):
        """
        Saves a text file with the results_string.
        """
        file_path = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Open Directory",
            "",
            QtWidgets.QFileDialog.ShowDirsOnly
            | QtWidgets.QFileDialog.DontResolveSymlinks
            )
        if file_path:
            with open(
                    f"{file_path}/Prediction_summary_"
                    f"{self.create_timestamp()}.txt",
                    "w") as output_file:
                output_file.write(self.summary_label.text())

    def create_timestamp(self):
        """
        Create a unique timestamp as a string.
        returns string
        """
        cur_time = datetime.datetime.now()
        year = cur_time.year
        month = cur_time.month
        day = cur_time.day
        hour = cur_time.hour
        mins = cur_time.minute
        sec = cur_time.second

        return f"{year}{month}{day}{hour}{mins}{sec}"
