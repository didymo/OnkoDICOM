import os

from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QVBoxLayout, QWidget, QHBoxLayout, QPushButton
from pydicom import dcmread

from src.Model import ROI


class RenameROIWindow(QDialog):

    def __init__(self, standard_names, file_rtss, roi_id, rename_signal, *args, **kwargs):
        super(RenameROIWindow, self).__init__(*args, **kwargs)

        self.standard_names = standard_names
        self.file_rtss = file_rtss
        self.roi_id = roi_id
        self.rename_signal = rename_signal

        self.path = os.path.dirname(self.file_rtss)
        self.filename = os.path.splitext(os.path.basename(self.file_rtss))[0]

        self.rtss = dcmread(self.file_rtss, force=True)

        self.setWindowTitle("Rename Region of Interest")
        self.resize(300, 80)

        self.explanation_text = QLabel("Enter a new name:")

        self.input_field = QLineEdit()
        self.input_field.textChanged.connect(self.on_text_edited)

        self.error_text = QLabel()
        self.error_text.setStyleSheet("color: red")

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
        self.layout.addWidget(self.error_text)
        self.layout.addWidget(self.button_area)
        self.setLayout(self.layout)

    def on_text_edited(self, text):
        if text in self.standard_names:
            self.error_text.setText("")
            #self.rename_button.setDisabled(False)
        else:
            self.error_text.setText("Entered name is not in standard names")
            #self.rename_button.setDisabled(True)

    def on_rename_clicked(self):
        new_name = self.input_field.text()
        new_dataset = ROI.rename_roi(self.rtss, self.roi_id, new_name)
        new_filepath = self.path + os.sep + self.filename + '_modified.dcm'
        new_dataset.save_as(new_filepath)
        # TODO rather than save this so a file straight away, the dataset should be sent as part of the signal further
        # up towards the main page and then 'replaces' the current rtss. at some point the user should be given the
        # option of saving this new rtss file. when the rtss file is replaced it should also recalculate the rois and
        # reload the structure widget's structures.
        self.rename_signal.emit()
        self.close()
