from PySide6 import QtCore, QtGui, QtWidgets
from src.Controller.PathHandler import resource_path
from src.View.StyleSheetReader import StyleSheetReader


class BatchMLResultsWindow(QtWidgets.QDialog):
    """
    This class creates a GUI window for displaying a summary of batch
    processing. It inherits from QDialog.
    """

    def __init__(self):
        QtWidgets.QDialog.__init__(self)
        self.ml_model = None
        self.params = None
        self.scaling = None

        # # Set maximum width, icon, and title
        self.setFixedSize(450, 450)
        self.setWindowTitle("Machine Learning Model Training Results")
        window_icon = QtGui.QIcon()
        window_icon.addPixmap(
            QtGui.QPixmap(resource_path("res/images/icon.ico")),
            QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(window_icon)

        # Create widgets
        self.summary_label = QtWidgets.QLabel()
        self.summary_label.setWordWrap(True)
        self.scroll_area = QtWidgets.QScrollArea()
        self.export_risk_table_button = QtWidgets. \
            QPushButton("Export 'Risk table'"
                        " to Text File")
        self.save_ml_model_button = QtWidgets.QPushButton("Save model")
        self.save_ml_parameters_button = QtWidgets.QPushButton("Save model"
                                                               " parameters")
        self.results_table = QtWidgets.QTableWidget(0, 0)

        # # Get stylesheet
        stylesheet: StyleSheetReader = StyleSheetReader()

        # Set stylesheet
        self.summary_label.setStyleSheet(stylesheet.get_stylesheet())
        self.scroll_area.setStyleSheet(stylesheet.get_stylesheet())
        self.export_risk_table_button.setStyleSheet(stylesheet.get_stylesheet())
        self.save_ml_model_button.setStyleSheet(stylesheet.get_stylesheet())
        self.save_ml_parameters_button.setStyleSheet(stylesheet.get_stylesheet())

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
        self.layout.addWidget(self.results_table)
        self.layout.addWidget(self.export_risk_table_button)
        self.layout.addWidget(self.save_ml_model_button)
        self.layout.addWidget(self.save_ml_parameters_button)

        # Connect buttons to functions
        self.export_risk_table_button.clicked.connect(
            self.export_risk_table_clicked)
        self.save_ml_model_button.clicked.connect(
            self.save_ml_model_clicked)
        self.save_ml_parameters_button.clicked.connect(
            self.save_ml_model_paramaters_clicked)

        # Set layout of window
        self.setLayout(self.layout)

    def set_results_values(self, results_values):
        """
        Sets the summary text.
        :param batch_summary: List where first index is a dictionary where key
                              is a patient, and value is a dictionary of
                              process name and status key-value pairs, and
                              second index is a batch ROI name cleaning summary
        """
        # Create summary text
        summary_text = ""
        for key, value in results_values.items():
            summary_text += f"{key.upper()}: {value}\n"

        # Set summary text
        # self.summary_label.setWordWrap(True)
        self.summary_label.setText(summary_text)

    def set_ml_model(self, ml_model):
        self.ml_model = ml_model

    def set_df_parameters(self, params):
        self.params = params

    def set_df_scaling(self, scaling):
        self.scaling = scaling

    def export_risk_table_clicked(self):
        """
        Function to handle the export button being clicked. Opens a file
        save dialog and saves the summary text to this text file.
        """
        file_path = QtWidgets.QFileDialog. \
            getExistingDirectory(self,
                                 "Open Directory",
                                 "",
                                 QtWidgets.QFileDialog.ShowDirsOnly |
                                 QtWidgets.QFileDialog.DontResolveSymlinks)
        if file_path:
            self.ml_model.save_confusion_matrix(f'{file_path}/')

    def save_ml_model_clicked(self):
        """
        Function to handle the ok button being clicked. Closes this
        window.
        :return: True when the window has closed.
        """
        file_path = QtWidgets.QFileDialog. \
            getExistingDirectory(self,
                                 "Open Directory",
                                 "",
                                 QtWidgets.QFileDialog.ShowDirsOnly |
                                 QtWidgets.QFileDialog.DontResolveSymlinks)
        if file_path:
            self.ml_model.save_ml_model(self.params, f'{file_path}/', self.scaling)

    def save_ml_model_paramaters_clicked(self):
        file_path = QtWidgets.QFileDialog. \
            getExistingDirectory(self,
                                 "Open Directory", "",
                                 QtWidgets.QFileDialog.ShowDirsOnly |
                                 QtWidgets.QFileDialog.DontResolveSymlinks)
        if file_path:
            self.ml_model.save_model_parameters(f'{file_path}/')
