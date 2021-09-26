import platform
from PySide6 import QtCore, QtGui, QtWidgets
from src.Controller.PathHandler import resource_path


class BatchSummaryWindow(QtWidgets.QDialog):
    """
    This class creates a GUI window for displaying a summary of batch
    processing. It inherits from QDialog.
    """

    def __init__(self):
        QtWidgets.QDialog.__init__(self)

        # Set maximum width, icon, and title
        self.setFixedSize(400, 450)
        self.setWindowTitle("Batch Processing Summary")
        window_icon = QtGui.QIcon()
        window_icon.addPixmap(
            QtGui.QPixmap(resource_path("res/images/icon.ico")),
            QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(window_icon)

        # Create widgets
        self.summary_label = QtWidgets.QLabel()
        self.scroll_area = QtWidgets.QScrollArea()
        self.ok_button = QtWidgets.QPushButton("Continue")

        # Get stylesheet
        if platform.system() == 'Darwin':
            self.stylesheet_path = "res/stylesheet.qss"
        else:
            self.stylesheet_path = "res/stylesheet-win-linux.qss"
        self.stylesheet = open(resource_path(self.stylesheet_path)).read()

        # Set stylesheet
        self.summary_label.setStyleSheet(self.stylesheet)
        self.scroll_area.setStyleSheet(self.stylesheet)
        self.ok_button.setStyleSheet(self.stylesheet)

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
        #self.layout.addWidget(self.summary_label)
        self.layout.addStretch(1)
        self.layout.addWidget(self.ok_button)

        # Connect ok button to function
        self.ok_button.clicked.connect(self.ok_button_clicked)

        # Set layout of window
        self.setLayout(self.layout)

    def set_summary_text(self, batch_summary):
        """
        Sets the summary text.
        :param batch_summary: Dictionary where key is a patient, and
                              value is a dictionary of process name and
                              status key-value pairs.
        """
        # Create summary text
        summary_text = ""
        for patient in batch_summary.keys():
            summary_text += "Patient ID: " + patient.patient_id + "\n"
            patient_summary = batch_summary[patient]
            for process in patient_summary.keys():
                if patient_summary[process] == "SUCCESS":
                    summary_text += "Completed " + process.upper()
                elif patient_summary[process] == "SKIP":
                    summary_text += process.upper\
                        + " skipped as one or more required files missing"
                summary_text += "\n"
            summary_text += "\n"

        # Set summary text
        self.summary_label.setText(summary_text)

    def ok_button_clicked(self):
        """
        Function to handle the ok button being clicked. Closes this
        window.
        :return: True when the window has closed.
        """
        self.close()
