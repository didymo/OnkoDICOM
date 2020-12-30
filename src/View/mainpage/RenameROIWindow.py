import pydicom
from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QListWidget

from src.Model import ROI
from src.Controller.PathHandler import resource_path
import platform

from src.Model.Worker import Worker


class RenameROIWindow(QDialog):

    def __init__(self, standard_volume_names, standard_organ_names, rtss, roi_id, roi_name, rename_signal,
                 suggested_text="", *args, **kwargs):
        super(RenameROIWindow, self).__init__(*args, **kwargs)

        if platform.system() == 'Darwin':
            self.stylesheet_path = "src/res/stylesheet.qss"
        else:
            self.stylesheet_path = "src/res/stylesheet-win-linux.qss"
        stylesheet = open(resource_path(self.stylesheet_path)).read()
        self.setStyleSheet(stylesheet)

        self.standard_volume_names = standard_volume_names
        self.standard_organ_names = standard_organ_names
        self.rtss = rtss
        self.roi_id = roi_id
        self.roi_name = roi_name
        self.rename_signal = rename_signal
        self.suggested_text = suggested_text

        self.setWindowTitle("Rename Region of Interest")
        self.setMinimumSize(300, 90)

        self.icon = QtGui.QIcon()
        self.icon.addPixmap(QtGui.QPixmap(resource_path("src/res/images/icon.ico")), QtGui.QIcon.Normal, QtGui.QIcon.Off)  # adding icon
        self.setWindowIcon(self.icon)

        self.explanation_text = QLabel("Enter a new name:")

        self.input_field = QLineEdit()
        self.input_field.setText(self.suggested_text)
        self.input_field.textChanged.connect(self.on_text_edited)

        self.feedback_text = QLabel()

        self.button_area = QWidget()
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.close)
        self.rename_button = QPushButton("Rename")
        self.rename_button.clicked.connect(self.on_rename_clicked)

        self.button_layout = QHBoxLayout()
        self.button_layout.addWidget(self.cancel_button)
        self.button_layout.addWidget(self.rename_button)
        self.button_area.setLayout(self.button_layout)

        self.list_label = QLabel()
        self.list_label.setText("List of Standard Region of Interests")

        # Populating the table of ROIs
        self.list_of_ROIs = QListWidget()
        self.list_of_ROIs.addItem("------------Standard Organ Names------------")
        for organ in self.standard_organ_names:
            self.list_of_ROIs.addItem(organ)

        self.list_of_ROIs.addItem("------------Standard Volume Names------------")
        for volume in self.standard_volume_names:
            self.list_of_ROIs.addItem(volume)

        self.list_of_ROIs.clicked.connect(self.on_ROI_clicked)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.explanation_text)
        self.layout.addWidget(self.input_field)
        self.layout.addWidget(self.feedback_text)
        self.layout.addWidget(self.button_area)
        self.layout.addWidget(self.list_label)
        self.layout.addWidget(self.list_of_ROIs)
        self.setLayout(self.layout)


    def on_text_edited(self, text):
        if text in self.standard_volume_names or text in self.standard_organ_names:
            self.feedback_text.setStyleSheet("color: green")
            self.feedback_text.setText("Entered text is in standard names")
        elif text.upper() in self.standard_volume_names or text.upper() in self.standard_organ_names:
            self.feedback_text.setStyleSheet("color: orange")
            self.feedback_text.setText("Entered text exists but should be in capitals")
        elif text == "":
            self.feedback_text.setText("")
        else:
            self.feedback_text.setStyleSheet("color: red")
            self.feedback_text.setText("Entered text is not in standard names")

        for item in self.standard_volume_names:
            if text.startswith(item):
                self.feedback_text.setStyleSheet("color: green")
                self.feedback_text.setText("Entered text is in standard names")
            else:
                upper_text = text.upper()
                if upper_text.startswith(item):
                    self.feedback_text.setStyleSheet("color: orange")
                    self.feedback_text.setText("Entered text exists but should be in capitals")

    def on_rename_clicked(self):
        self.new_name = self.input_field.text()
        progress_window = RenameROIProgressWindow(self, QtCore.Qt.WindowTitleHint)
        progress_window.signal_roi_renamed.connect(self.on_roi_renamed)
        progress_window.start_renaming(self.rtss, self.roi_id, self.new_name)
        progress_window.show()

    def on_roi_renamed(self, new_rtss):
        self.rename_signal.emit((new_rtss, {"rename": [self.roi_name, self.new_name]}))
        QtWidgets.QMessageBox.about(self, "Saved", "Region of interest successfully renamed!")
        self.close()

    def on_ROI_clicked(self):
        clicked_ROI = self.list_of_ROIs.currentItem()
        # Excluding headers from being clicked.
        if not str(clicked_ROI.text()).startswith("------------Standard"):
            self.input_field.setText(str(clicked_ROI.text()))


class RenameROIProgressWindow(QtWidgets.QDialog):
    """
    This class displays a window that advises the user that the RTSTRUCT is being modified, and then creates a new
    thread where the new RTSTRUCT is modified.
    """

    signal_roi_renamed = QtCore.pyqtSignal(pydicom.Dataset)   # Emits the new dataset

    def __init__(self, *args, **kwargs):
        super(RenameROIProgressWindow, self).__init__(*args, **kwargs)
        layout = QtWidgets.QVBoxLayout()
        text = QtWidgets.QLabel("Renaming ROI...")
        layout.addWidget(text)
        self.setWindowTitle("Please wait...")
        self.setFixedWidth(150)
        self.setLayout(layout)

        self.threadpool = QtCore.QThreadPool()

    def start_renaming(self, dataset_rtss, roi_id, new_name):
        """
        Creates a thread that generates the new dataset object.
        :param dataset_rtss: Dataset of RTSS.
        :param roi_id: ID of the ROI to be renamed.
        :param new_name: The name the ROI will be changed to.
        """
        worker = Worker(ROI.rename_roi, dataset_rtss, roi_id, new_name)
        worker.signals.result.connect(self.roi_renamed)
        self.threadpool.start(worker)

    def roi_renamed(self, result):
        """
        This method is called when the second thread completes generation of the new dataset object.
        :param result: The resulting dataset from the ROI.rename_roi function.
        """
        self.signal_roi_renamed.emit(result)
        self.close()
