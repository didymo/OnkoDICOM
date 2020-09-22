import pydicom
from PyQt5 import QtCore, QtGui, QtWidgets

from src.Model.CalculateImages import convert_raw_data, get_pixmaps
from src.Model.GetPatientInfo import get_basic_info
from src.Model.PatientDictContainer import PatientDictContainer
from src.View.mainwindowrestructure.NewDicomView import NewDicomView
from src.View.mainwindowrestructure.NewPatientBar import NewPatientBar


class UINewMainWindow:
    pyradi_trigger = QtCore.pyqtSignal(str, dict, str)

    def setup_ui(self, main_window_instance):

        ##############################
        #  LOAD PATIENT INFORMATION  #
        ##############################
        patient_dict_container = PatientDictContainer()
        dataset = patient_dict_container.dataset
        self.rtss_modified = False

        if isinstance(dataset[0].WindowWidth, pydicom.valuerep.DSfloat):
            window = int(dataset[0].WindowWidth)
        elif isinstance(dataset[0].WindowWidth, pydicom.multival.MultiValue):
            window = int(dataset[0].WindowWidth[1])

        if isinstance(dataset[0].WindowCenter, pydicom.valuerep.DSfloat):
            level = int(dataset[0].WindowCenter)
        elif isinstance(dataset[0].WindowCenter, pydicom.multival.MultiValue):
            level = int(dataset[0].WindowCenter[1])

        patient_dict_container.add("window", window)
        patient_dict_container.add("level", level)

        pixel_values = convert_raw_data(dataset)
        pixmaps = get_pixmaps(pixel_values, window, level)
        patient_dict_container.add("pixmaps", pixmaps)

        basic_info = get_basic_info(dataset[0])
        patient_dict_container.add("basic_info", basic_info)

        ##########################################
        #  IMPLEMENTATION OF THE MAIN PAGE VIEW  #
        ##########################################
        main_window_instance.setMinimumSize(1080, 700)
        main_window_instance.setWindowTitle("OnkoDICOM")
        main_window_instance.setWindowIcon(QtGui.QIcon("src/Icon/DONE.png"))

        self.central_widget = QtWidgets.QWidget()
        self.central_widget_layout = QtWidgets.QVBoxLayout()

        self.patient_bar = NewPatientBar()
        self.button_open_patient = QtWidgets.QPushButton("Open new patient")
        self.dicom_view = NewDicomView()

        self.central_widget_layout.addWidget(self.patient_bar)
        self.central_widget_layout.addWidget(self.button_open_patient)
        self.central_widget_layout.addWidget(self.dicom_view)

        self.central_widget.setLayout(self.central_widget_layout)
        main_window_instance.setCentralWidget(self.central_widget)
