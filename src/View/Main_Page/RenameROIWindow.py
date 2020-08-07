import os

from PyQt5 import QtGui
from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QVBoxLayout, QWidget, QHBoxLayout, QPushButton
from pydicom import dcmread

from src.Model import ROI


class RenameROIWindow(QDialog):

    def __init__(self, standard_volume_names, standard_organ_names, rtss, roi_id, rename_signal, suggested_text="", *args, **kwargs):
        super(RenameROIWindow, self).__init__(*args, **kwargs)

        self.standard_volume_names = standard_volume_names
        self.standard_organ_names = standard_organ_names
        self.rtss = rtss
        self.roi_id = roi_id
        self.rename_signal = rename_signal
        self.suggested_text = suggested_text

        self.setWindowTitle("Rename Region of Interest")
        self.resize(300, 80)

        self.icon = QtGui.QIcon()
        self.icon.addPixmap(QtGui.QPixmap("src/res/images/icon.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)  # adding icon
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
        #self.rename_button.setDisabled(True)
        self.rename_button.clicked.connect(self.on_rename_clicked)

        self.button_layout = QHBoxLayout()
        self.button_layout.addWidget(self.cancel_button)
        self.button_layout.addWidget(self.rename_button)
        self.button_area.setLayout(self.button_layout)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.explanation_text)
        self.layout.addWidget(self.input_field)
        self.layout.addWidget(self.feedback_text)
        self.layout.addWidget(self.button_area)
        self.setLayout(self.layout)

    def on_text_edited(self, text):
        if text in self.standard_volume_names or text in self.standard_organ_names:
            self.feedback_text.setStyleSheet("color: green")
            self.feedback_text.setText("Entered text is in standard names")
            #self.rename_button.setDisabled(False)
        elif text.upper() in self.standard_volume_names or text.upper() in self.standard_organ_names:
            self.feedback_text.setStyleSheet("color: orange")
            self.feedback_text.setText("Entered text exists but should be in capitals")
        elif text == "":
            self.feedback_text.setText("")
        else:
            self.feedback_text.setStyleSheet("color: red")
            self.feedback_text.setText("Entered text is not in standard names")
            #self.rename_button.setDisabled(True)

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
        self.rename_signal.emit(new_dataset)
        self.close()
