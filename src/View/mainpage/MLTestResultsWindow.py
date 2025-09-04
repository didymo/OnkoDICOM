from src.Controller.PathHandler import resource_path
from PySide6 import QtWidgets, QtCore, QtGui
import datetime

from src.View.StyleSheetReader import StyleSheetReader


class MLTestResultsWindow(QtWidgets.QDialog):
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
        self.stylesheet = StyleSheetReader()

        # Set stylesheet
        self.summary_label.setStyleSheet(self.stylesheet())
        self.scroll_area.setStyleSheet(self.stylesheet())
        self.save_ml_predicted_txt.setStyleSheet(self.stylesheet())
        self.save_ml_predicted_csv.setStyleSheet(self.stylesheet())

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
