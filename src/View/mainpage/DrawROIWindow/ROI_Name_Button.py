import pydicom
from PySide6 import QtWidgets
from PySide6.QtCore import Signal
from PySide6.QtWidgets import  QLabel, QPushButton, QWidget, QMessageBox
from src.View.mainpage.DrawROIWindow.SelectROIPopUp import SelectROIPopUp
from src.Model.PatientDictContainer import PatientDictContainer

class ROIName(QWidget):
    roi_name_emit = Signal(str)
    def __init__(self,parent = None, roi_name = str):
        super().__init__(parent)
        self.roi_name = roi_name
        self.parent = parent
        layout = QtWidgets.QHBoxLayout(self)

        label = QLabel("Select ROI Name")
        self.select_roi_type = QPushButton()
        self.select_roi_type.clicked.connect(self.show_roi_type_options)

        layout.addWidget(label)
        layout.addWidget(self.select_roi_type)
        self.setLayout(layout)

    def show_roi_type_options(self):
        """Creates and displays roi type options popup"""
        self.choose_roi_name_window = SelectROIPopUp()
        self.choose_roi_name_window.signal_roi_name.connect(
            self.set_selected_roi_name)
        self.choose_roi_name_window.show()
        
    def set_selected_roi_name(self, roi_name):
        """
        function to set selected roi name
        :param roi_name: roi name selected
        """
        roi_exists = False

        patient_dict_container = PatientDictContainer()
        existing_rois = patient_dict_container.get("rois")

        # Check to see if the ROI already exists
        for _, value in existing_rois.items():
            if roi_name in value['name']:
                roi_exists = True

        if roi_exists:
            QMessageBox.about(self,
                              "ROI already exists in RTSS",
                              "Would you like to continue?")

        self.select_roi_type.setText(roi_name)
        self.roi_name_emit.emit(roi_name)