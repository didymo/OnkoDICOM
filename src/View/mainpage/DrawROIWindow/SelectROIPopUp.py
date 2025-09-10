import csv
import platform

from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import QDialog, QLabel, QLineEdit, \
    QWidget, QPushButton, QHBoxLayout, QListWidget, QVBoxLayout

from src.Controller.PathHandler import data_path, resource_path

"""
This Class handles the ROI Pop Up functionalities       
"""


class SelectROIPopUp(QDialog):
    signal_roi_name = QtCore.Signal(str)

    def __init__(self):
        QDialog.__init__(self)

        if platform.system() == 'Darwin':
            self.stylesheet_path = "res/stylesheet.qss"
        else:
            self.stylesheet_path = "res/stylesheet-win-linux.qss"
        stylesheet = open(resource_path(self.stylesheet_path)).read()
        self.setStyleSheet(stylesheet)
        self.standard_names = []
        self.init_standard_names()

        self.setWindowTitle("Select A Region of Interest To Draw")
        self.setMinimumSize(350, 180)

        self.icon = QtGui.QIcon()
        self.icon.addPixmap(
            QtGui.QPixmap(resource_path("res/images/icon.ico")),
            QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(self.icon)

        self.explanation_text = QLabel("Search for ROI:")

        self.input_field = QLineEdit()
        self.input_field.textChanged.connect(self.on_text_edited)

        self.button_area = QWidget()
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.on_cancel_clicked)
        self.select_roi_button = QPushButton("Select ROI")

        self.select_roi_button.clicked.connect(self.on_select_roi_clicked)

        self.button_layout = QHBoxLayout()
        self.button_layout.addWidget(self.cancel_button)
        self.button_layout.addWidget(self.select_roi_button)
        self.button_area.setLayout(self.button_layout)

        self.list_label = QLabel()
        self.list_label.setText(
            "Select a Standard Region of Interest")

        self.list_of_ROIs = QListWidget()
        for standard_name in self.standard_names:
            self.list_of_ROIs.addItem(standard_name)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.explanation_text)
        self.layout.addWidget(self.input_field)
        self.layout.addWidget(self.list_label)
        self.layout.addWidget(self.list_of_ROIs)
        self.layout.addWidget(self.button_area)
        self.setLayout(self.layout)

        self.list_of_ROIs.clicked.connect(self.on_roi_clicked)

    def init_standard_names(self):
        """
        Create two lists containing standard organ
        and standard volume names as set by the Add-On options.
        """
        with open(data_path('organName.csv'), 'r') as f:
            standard_organ_names = []

            csv_input = csv.reader(f)
            header = next(f)  # Ignore the "header" of the column
            for row in csv_input:
                standard_organ_names.append(row[0])

        with open(data_path('volumeName.csv'), 'r') as f:
            standard_volume_names = []

            csv_input = csv.reader(f)
            next(f)  # Ignore the "header" of the column
            for row in csv_input:
                standard_volume_names.append(row[1])

        self.standard_names = standard_organ_names + standard_volume_names

    def on_text_edited(self, text):
        """
        function triggered when text in
        the ROI popup is edited
        -------
        :param text: text in the pop up
        """
        self.list_of_ROIs.clear()
        text_upper_case = text.upper()
        for item in self.standard_names:
            if item.startswith(text) or item.startswith(text_upper_case):
                self.list_of_ROIs.addItem(item)

    def on_roi_clicked(self):
        """
        function triggered when an ROI is clicked
        """
        self.select_roi_button.setEnabled(True)
        self.select_roi_button.setFocus()

    def on_select_roi_clicked(self):
        """
        function to start the draw ROI function
        """
        # If there is a ROI Selected
        if self.list_of_ROIs.currentItem() is not None:
            roi = self.list_of_ROIs.currentItem()
            self.roi_name = str(roi.text())

            # Call function on UIDrawWindow so it has selected ROI
            #self.signal_roi_name.emit(self.roi_name)
            self.close()

    def on_cancel_clicked(self):
        """
        function to cancel the operation
        """
        self.close()
