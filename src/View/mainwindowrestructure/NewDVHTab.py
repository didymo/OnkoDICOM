from PyQt5 import QtWidgets, QtCore

from src.Model.PatientDictContainer import PatientDictContainer


class NewDVHTab(QtWidgets.QWidget):

    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.patient_dict_container = PatientDictContainer()
        self.dvh_calculated = self.patient_dict_container.has("raw_dvh")

        self.raw_dvh = self.patient_dict_container.get("raw_dvh")
        self.dvh_x_y = self.patient_dict_container.get("dvh_x_y")
        self.selected_rois = self.patient_dict_container.get("selected_rois")
        self.roi_color = self.patient_dict_container.get("roi_color_dict")

        self.dvh_tab_layout = QtWidgets.QVBoxLayout()

        if self.dvh_calculated:
            self.init_layout_dvh()
        else:
            self.init_layout_no_dvh()

        self.setLayout(self.dvh_tab_layout)

    def init_layout_dvh(self):
        pass

    def init_layout_no_dvh(self):
        button_calc_dvh = QtWidgets.QPushButton("Calculate DVH")
        button_calc_dvh.clicked.connect(self.prompt_calc_dvh)

        self.dvh_tab_layout.setAlignment(QtCore.Qt.AlignCenter)
        self.dvh_tab_layout.addWidget(button_calc_dvh)

    def prompt_calc_dvh(self):
        # TODO this will confirm if DVH is to be calculated, then bring up a progress while the DVH calculates
        # once the DVH is calculated, clear the layout and call init_layout_dvh
        pass
