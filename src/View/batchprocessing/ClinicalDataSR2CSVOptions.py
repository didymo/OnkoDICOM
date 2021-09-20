import platform
from os.path import expanduser
from PySide6 import QtWidgets
from src.Controller.PathHandler import resource_path


class ClinicalDataSR2CSVOptions(QtWidgets.QWidget):
    """
    ClinicalData-SR2CSV options for batch processing.
    """

    def __init__(self):
        """
        Initialise the class.
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

        label = QtWidgets.QLabel(
            "Please choose the location for the resulting CSV file:")
        label.setStyleSheet(self.stylesheet)

        self.directory_layout = QtWidgets.QFormLayout()

        # Directory text box
        self.directory_input = QtWidgets.QLineEdit("No directory selected")
        self.directory_input.setStyleSheet(self.stylesheet)
        self.directory_input.setEnabled(False)

        # Change button
        self.change_button = QtWidgets.QPushButton("Change")
        self.change_button.setMaximumWidth(100)
        self.change_button.clicked.connect(self.show_file_browser)
        self.change_button.setObjectName("NormalButton")
        self.change_button.setStyleSheet(self.stylesheet)

        self.directory_layout.addWidget(label)
        self.directory_layout.addRow(self.directory_input)
        self.directory_layout.addRow(self.change_button)

        self.main_layout.addLayout(self.directory_layout)
        self.setLayout(self.main_layout)

    def set_csv_output_location(self, path, enable=True,
                                         change_if_modified=False):
        """
        Set the location for the ClinicalData-SR2CSV resulting .csv file.
        :param path: desired path.
        :param enable: Enable the directory text bar.
        :param change_if_modified: Change the directory if already been
                                   changed.
        """
        if not self.directory_input.isEnabled():
            self.directory_input.setText(path)
            self.directory_input.setEnabled(enable)
        elif change_if_modified:
            self.directory_input.setText(path)
            self.directory_input.setEnabled(enable)

    def get_csv_output_location(self):
        """
        Get the location of the desired output directory.
        """
        return self.directory_input.text()

    def show_file_browser(self):
        """
        Show the file browser for selecting a folder for the Onko
        default directory.
        """
        # Open a file dialog and return chosen directory
        path = QtWidgets.QFileDialog.getExistingDirectory(
            None,
            'Choose '
            'Directory ..', '')

        # If chosen directory is nothing (user clicked cancel) set to
        # user home
        if path == "":
            path = expanduser("~")

        # Update file path
        self.set_csv_output_location(path, change_if_modified=True)
