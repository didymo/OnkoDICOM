from PyQt5 import QtCore, QtGui, QtWidgets

from src.Model.PatientDictContainer import PatientDictContainer


class UINewMainWindow:
    pyradi_trigger = QtCore.pyqtSignal(str, dict, str)

    def setup_ui(self, main_window_instance):
        patient_dict_container = PatientDictContainer()
        self.dataset = patient_dict_container.dataset
        self.patient_name = self.dataset[0]['PatientName']
        self.rtss_modified = False

        main_window_instance.setMinimumSize(1080, 700)
        main_window_instance.setWindowTitle("OnkoDICOM")
        main_window_instance.setWindowIcon(QtGui.QIcon("src/Icon/DONE.png"))

        self.central_widget = QtWidgets.QWidget()
        self.central_widget_layout = QtWidgets.QVBoxLayout()

        self.label_patient_name = QtWidgets.QLabel(str(self.patient_name))
        self.button_open_patient = QtWidgets.QPushButton("Open new patient")

        self.central_widget_layout.addWidget(self.label_patient_name)
        self.central_widget_layout.addWidget(self.button_open_patient)

        self.central_widget.setLayout(self.central_widget_layout)
        main_window_instance.setCentralWidget(self.central_widget)
