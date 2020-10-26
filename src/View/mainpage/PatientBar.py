from PyQt5 import QtWidgets, QtCore, QtGui

from src.Model.PatientDictContainer import PatientDictContainer


def create_info_widget(label, value):
    info_widget = QtWidgets.QWidget()
    info_widget.setGeometry(QtCore.QRect(50, 5, 370, 31))
    info_widget_layout = QtWidgets.QHBoxLayout(info_widget)
    info_widget_layout.setContentsMargins(0, 8, 0, 0)
    info_widget_layout.setSpacing(5)
    info_widget_layout.setAlignment(QtCore.Qt.AlignLeft)
    info_widget.setFocusPolicy(QtCore.Qt.NoFocus)

    # Label
    info_label = QtWidgets.QLabel(info_widget)
    info_label.setFont(QtGui.QFont("Laksaman", weight=QtGui.QFont.Bold, pointSize=10))
    info_label.setAlignment(QtCore.Qt.AlignLeft)
    info_label.setText(label)
    info_widget_layout.addWidget(info_label)

    # Value
    info_value = QtWidgets.QLabel(info_widget)
    info_value.setAlignment(QtCore.Qt.AlignLeft)
    info_value.setFont(QtGui.QFont("Laksaman", pointSize=10))
    info_value.setText(value)
    info_widget_layout.addWidget(info_value)

    return info_widget


class PatientBar(QtWidgets.QWidget):

    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        patient_dict_container = PatientDictContainer()
        self.basic_info = patient_dict_container.get("basic_info")

        # Init layout
        self.patient_bar_layout = QtWidgets.QHBoxLayout()
        self.patient_bar_layout.setContentsMargins(0, 0, 0, 0)
        self.patient_bar_layout.setSpacing(5)
        self.setMaximumHeight(35)

        # Create patient icon
        self.icon = QtWidgets.QLabel()
        self.icon.setMaximumWidth(30)
        self.icon.setGeometry(QtCore.QRect(10, 0, 0, 0))
        self.icon.setText("")
        self.icon.setPixmap(QtGui.QPixmap("src/Icon/patient.png"))

        # Create patient name
        self.name_widget = create_info_widget("Name", self.basic_info['name'])

        # Create patient ID
        self.id_widget = create_info_widget("ID", self.basic_info['id'])

        # Create patient gender
        self.gender_widget = create_info_widget("Gender", self.basic_info['gender'])

        # Create patient DOB
        self.dob_widget = create_info_widget("DOB", self.basic_info['dob'])

        # Set layout
        self.patient_bar_layout.addWidget(self.icon)
        self.patient_bar_layout.addWidget(self.name_widget)
        self.patient_bar_layout.addWidget(self.id_widget)
        self.patient_bar_layout.addWidget(self.gender_widget)
        self.patient_bar_layout.addWidget(self.dob_widget)
        self.setLayout(self.patient_bar_layout)
