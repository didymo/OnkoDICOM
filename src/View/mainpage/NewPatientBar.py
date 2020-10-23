from PyQt5 import QtWidgets, QtCore, QtGui

from src.Model.PatientDictContainer import PatientDictContainer


class NewPatientBar(QtWidgets.QWidget):

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
        self.icon.setPixmap(QtGui.QPixmap(":/images/Icon/patient.png"))

        # Create patient name
        self.name_widget = QtWidgets.QWidget()
        self.create_patient_name()

        # Create patient ID
        self.id_widget = QtWidgets.QWidget()
        self.create_patient_id()

        # Create patient gender
        self.gender_widget = QtWidgets.QWidget()
        self.create_patient_gender()

        # Create patient DOB
        self.dob_widget = QtWidgets.QWidget()
        self.create_patient_dob()

        # Set layout
        self.patient_bar_layout.addWidget(self.icon)
        self.patient_bar_layout.addWidget(self.name_widget)
        self.patient_bar_layout.addWidget(self.id_widget)
        self.patient_bar_layout.addWidget(self.gender_widget)
        self.patient_bar_layout.addWidget(self.dob_widget)
        self.setLayout(self.patient_bar_layout)

    def create_patient_name(self):
        self.name_widget.setGeometry(QtCore.QRect(50, 5, 370, 31))
        name_layout = QtWidgets.QHBoxLayout(self.name_widget)
        name_layout.setContentsMargins(0, 8, 0, 0)
        name_layout.setSpacing(5)
        name_layout.setAlignment(QtCore.Qt.AlignLeft)
        self.name_widget.setFocusPolicy(QtCore.Qt.NoFocus)

        # Label
        name_label = QtWidgets.QLabel(self.name_widget)
        name_label.setFont(QtGui.QFont("Laksaman", weight=QtGui.QFont.Bold, pointSize=10))
        name_label.setAlignment(QtCore.Qt.AlignLeft)
        name_label.setText("Name")
        name_layout.addWidget(name_label)

        # Value
        name_value = QtWidgets.QLabel(self.name_widget)
        name_value.setAlignment(QtCore.Qt.AlignLeft)
        name_value.setFont(QtGui.QFont("Laksaman", pointSize=10))
        name_value.setText(self.basic_info['name'])
        name_layout.addWidget(name_value)

    def create_patient_id(self):
        self.id_widget.setGeometry(QtCore.QRect(500, 5, 280, 31))
        id_layout = QtWidgets.QHBoxLayout(self.id_widget)
        id_layout.setContentsMargins(0, 8, 0, 0)
        id_layout.setSpacing(5)
        id_layout.setAlignment(QtCore.Qt.AlignLeft)
        self.id_widget.setFocusPolicy(QtCore.Qt.NoFocus)

        # Label
        id_label = QtWidgets.QLabel(self.id_widget)
        id_label.setFont(QtGui.QFont(
            "Laksaman", weight=QtGui.QFont.Bold, pointSize=10))
        id_label.setAlignment(QtCore.Qt.AlignLeft)
        id_label.setText("ID")
        id_layout.addWidget(id_label)

        # Value
        id_value = QtWidgets.QLabel(self.id_widget)
        id_value.setFont(QtGui.QFont("Laksaman", pointSize=10))
        id_value.setAlignment(QtCore.Qt.AlignLeft)
        id_value.setText(self.basic_info['id'])
        id_layout.addWidget(id_value)

    def create_patient_gender(self):
        self.gender_widget.setGeometry(QtCore.QRect(830, 5, 111, 31))
        self.gender_widget.setFocusPolicy(QtCore.Qt.NoFocus)
        gender_layout = QtWidgets.QHBoxLayout(self.gender_widget)
        gender_layout.setContentsMargins(0, 8, 0, 0)
        gender_layout.setSpacing(5)
        gender_layout.setAlignment(QtCore.Qt.AlignLeft)

        # Label
        gender_label = QtWidgets.QLabel(self.gender_widget)
        gender_label.setFont(QtGui.QFont("Laksaman", weight=QtGui.QFont.Bold, pointSize=10))
        gender_label.setAlignment(QtCore.Qt.AlignLeft)
        gender_label.setText("Gender")
        gender_layout.addWidget(gender_label)

        # Value
        gender_value = QtWidgets.QLabel(self.gender_widget)
        gender_value.setFont(QtGui.QFont("Laksaman", pointSize=10))
        gender_value.setAlignment(QtCore.Qt.AlignLeft)
        gender_value.setText(self.basic_info['gender'])
        gender_layout.addWidget(gender_value)

    def create_patient_dob(self):
        self.dob_widget.setGeometry(QtCore.QRect(950, 5, 95, 31))
        self.dob_widget.setFocusPolicy(QtCore.Qt.NoFocus)
        dob_layout = QtWidgets.QHBoxLayout(self.dob_widget)
        dob_layout.setContentsMargins(0, 8, 0, 0)
        dob_layout.setSpacing(5)
        dob_layout.setAlignment(QtCore.Qt.AlignLeft)

        # Label
        dob_label = QtWidgets.QLabel(self.dob_widget)
        dob_label.setFont(QtGui.QFont("Laksaman", weight=QtGui.QFont.Bold, pointSize=10))
        dob_label.setAlignment(QtCore.Qt.AlignLeft)
        dob_label.setText("DOB")
        dob_layout.addWidget(dob_label)

        # Value
        dob_value = QtWidgets.QLabel(self.dob_widget)
        dob_value.setFont(QtGui.QFont("Laksaman", pointSize=10))
        dob_value.setAlignment(QtCore.Qt.AlignLeft)
        dob_value.setText(self.basic_info['dob'])
        dob_layout.addWidget(dob_value)
