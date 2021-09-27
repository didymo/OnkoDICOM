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
        self.export_button = QtWidgets.QPushButton("Export to Text File")
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
        self.export_button.setStyleSheet(self.stylesheet)
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
        self.layout.addStretch(1)
        self.layout.addWidget(self.export_button)
        self.layout.addWidget(self.ok_button)

        # Connect buttons to functions
        self.export_button.clicked.connect(self.export_button_clicked)
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
                # Success
                if patient_summary[process] == "SUCCESS":
                    summary_text += "Completed " + process.upper()
                # Skipped due to missing files
                elif patient_summary[process] == "SKIP":
                    summary_text += process.upper\
                        + " skipped as one or more required files missing"
                # Process interrupted
                elif patient_summary[process] == "INTERRUPT":
                    summary_text += process.upper() \
                        + " skipped as it was interrupted."
                # ISO2ROI no RX Dose value exists
                elif patient_summary[process] == "ISO_NO_RX_DOSE":
                    summary_text += process.upper() \
                        + " skipped as no RX Dose value was found."
                summary_text += "\n"
            summary_text += "\n"

        summary_text += "\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n"
        # Set summary text
        self.summary_label.setText(summary_text)

    def export_button_clicked(self):
        """
        Function to handle the export button being clicked. Opens a file
        save dialog and saves the summary text to this text file.
        """
        file_path = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save As...", '', 'Text Files (*.txt)')

        if file_path:
            text = self.summary_label.text()
            f = open(file_path[0], "w")
            f.write(text)
            f.close()

    def ok_button_clicked(self):
        """
        Function to handle the ok button being clicked. Closes this
        window.
        :return: True when the window has closed.
        """
        self.close()
