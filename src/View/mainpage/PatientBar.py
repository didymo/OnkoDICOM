from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QHBoxLayout, QWidget, QLabel, QSizePolicy

from src.Model.PatientDictContainer import PatientDictContainer
from src.Controller.PathHandler import resource_path

class PatientBar(QtWidgets.QWidget):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.setObjectName("PatientBar")
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        patient_dict_container = PatientDictContainer()
        self.basic_info = patient_dict_container.get("basic_info")

        # Init layout
        self.patient_bar_layout = QHBoxLayout()
        self.patient_bar_layout.setObjectName("PatientBarLayout")
        self.patient_bar_layout.setSpacing(0)

        # Create patient icon
        self.patient_bar_icon = QLabel()
        self.patient_bar_icon.setObjectName("PatientBarIcon")
        self.patient_bar_icon.setText("")
        self.patient_bar_icon.setPixmap(QtGui.QPixmap(resource_path("src/res/images/btn-icons/patient.png")))

        # Create patient name
        self.patient_bar_name_info = QLabel()
        self.patient_bar_name_info.setObjectName("PatientBarNameInfo")
        self.patient_bar_name_info.setText(self.basic_info['name'])
        self.patient_bar_name_info.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.patient_bar_name_info.resize(self.patient_bar_name_info.sizeHint().width(),
                                          self.patient_bar_name_info.sizeHint().height())
        self.patient_bar_name_info.setProperty("PatientBarClass", "value")
        self.patient_bar_name_info_label = QLabel()
        self.patient_bar_name_info_label.setObjectName("PatientBarNameInfoLabel")
        self.patient_bar_name_info_label.setText("Name:")
        self.patient_bar_name_info_label.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        self.patient_bar_name_info_label.resize(self.patient_bar_name_info_label.sizeHint().width(),
                                          self.patient_bar_name_info_label.sizeHint().height())
        self.patient_bar_name_info_label.setProperty("PatientBarClass", "label")

        # # Create patient ID
        self.patient_bar_id_info = QLabel()
        self.patient_bar_id_info.setObjectName("PatientBarIdInfo")
        self.patient_bar_id_info.setText(self.basic_info['id'])
        self.patient_bar_id_info.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.patient_bar_id_info.resize(self.patient_bar_id_info.sizeHint().width(),
                                          self.patient_bar_id_info.sizeHint().height())
        self.patient_bar_id_info.setProperty("PatientBarClass", "value")
        self.patient_bar_id_info_label = QLabel()
        self.patient_bar_id_info_label.setObjectName("PatientBarIdInfoLabel")
        self.patient_bar_id_info_label.setText("ID:")
        self.patient_bar_id_info_label.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        self.patient_bar_id_info_label.resize(self.patient_bar_id_info_label.sizeHint().width(),
                                                self.patient_bar_id_info_label.sizeHint().height())
        self.patient_bar_id_info_label.setProperty("PatientBarClass", "label")

        # # Create patient gender
        self.patient_bar_gender_info = QLabel()
        self.patient_bar_gender_info.setObjectName("PatientBarGenderInfo")
        self.patient_bar_gender_info.setText(self.basic_info['gender'])
        self.patient_bar_gender_info.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.patient_bar_gender_info.resize(self.patient_bar_gender_info.sizeHint().width(),
                                        self.patient_bar_gender_info.sizeHint().height())
        self.patient_bar_gender_info.setProperty("PatientBarClass", "value")
        self.patient_bar_gender_info_label = QLabel()
        self.patient_bar_gender_info_label.setObjectName("PatientBarGenderInfoLabel")
        self.patient_bar_gender_info_label.setText("Gender:")
        self.patient_bar_gender_info_label.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        self.patient_bar_gender_info_label.resize(self.patient_bar_gender_info_label.sizeHint().width(),
                                              self.patient_bar_gender_info_label.sizeHint().height())
        self.patient_bar_gender_info_label.setProperty("PatientBarClass", "label")

        # # Create patient DOB
        self.patient_bar_dob_info = QLabel()
        self.patient_bar_dob_info.setObjectName("PatientBarDobInfo")
        self.patient_bar_dob_info.setText(self.basic_info['dob'])
        self.patient_bar_dob_info.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.patient_bar_dob_info.resize(self.patient_bar_dob_info.sizeHint().width(),
                                            self.patient_bar_dob_info.sizeHint().height())
        self.patient_bar_dob_info.setProperty("PatientBarClass", "value")
        self.patient_bar_dob_info_label = QLabel()
        self.patient_bar_dob_info_label.setObjectName("PatientBarDobInfoLabel")
        self.patient_bar_dob_info_label.setText("DoB:")
        self.patient_bar_dob_info_label.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        self.patient_bar_dob_info_label.resize(self.patient_bar_dob_info_label.sizeHint().width(),
                                                  self.patient_bar_dob_info_label.sizeHint().height())
        self.patient_bar_dob_info_label.setProperty("PatientBarClass", "label")
        # # Set layout
        self.patient_bar_layout.addWidget(self.patient_bar_icon)
        self.patient_bar_layout.addWidget(self.patient_bar_name_info_label)
        self.patient_bar_layout.addWidget(self.patient_bar_name_info)
        self.patient_bar_layout.addWidget(self.patient_bar_id_info_label)
        self.patient_bar_layout.addWidget(self.patient_bar_id_info)
        self.patient_bar_layout.addWidget(self.patient_bar_gender_info_label)
        self.patient_bar_layout.addWidget(self.patient_bar_gender_info)
        self.patient_bar_layout.addWidget(self.patient_bar_dob_info_label)
        self.patient_bar_layout.addWidget(self.patient_bar_dob_info)
        self.setLayout(self.patient_bar_layout)
        self.resize(self.sizeHint().width(), self.sizeHint().height())
