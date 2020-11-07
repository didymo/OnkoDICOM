from PyQt5 import QtGui
from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QListWidget

from src.Model import ROI
from src.Controller.PathHandler import resource_path
import platform

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
        new_name = self.input_field.text()
        new_dataset = ROI.rename_roi(self.rtss, self.roi_id, new_name)
        # TODO rather than save this so a file straight away, the dataset is sent as part of the signal further
        # up towards the main page and then 'replaces' the current rtss. at some point the user is given the
        # option of saving this new rtss file. when the rtss file is replaced it also recalculates the rois and
        # reload the structure widget's structures.
        print()
        self.rename_signal.emit((new_dataset, {"rename": [self.roi_name, new_name]}))
        self.close()

    def on_ROI_clicked(self):
        clicked_ROI = self.list_of_ROIs.currentItem()
        # Excluding headers from being clicked.
        if not str(clicked_ROI.text()).startswith("------------Standard"):
            self.input_field.setText(str(clicked_ROI.text()))
