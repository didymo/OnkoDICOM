from PyQt5 import QtWidgets, QtGui, QtCore

class PatientBar(object):
	"""
	Create the patient bar in the window of the main page.
	"""

	def __init__(self, main_window):
		"""
		Create and place the patient bar in the window of the main page.

		:param main_window:
		 the window of the main page
		"""
		self.window = main_window
		self.widget = QtWidgets.QWidget(main_window.main_widget)
		self.widget.setMaximumHeight(35)
		self.layout = QtWidgets.QHBoxLayout(self.widget)
		self.layout.setContentsMargins(0, 0, 0, 0)
		self.layout.setAlignment(QtCore.Qt.AlignTop)
		self.create_patient_icon()
		self.create_patient_name()
		self.create_patient_ID()
		self.create_patient_gender()
		self.create_patient_DOB()
		self.init_layout()

	def init_layout(self):
		"""
		Place the created widgets in the layout and add to the main page.
		"""
		self.layout.addWidget(self.icon)
		self.layout.addWidget(self.name_widget)
		self.layout.addWidget(self.id_widget)
		self.layout.addWidget(self.gender_widget)
		self.layout.addWidget(self.dob_widget)

		self.window.main_layout.addWidget(self.widget)

		self.icon.raise_()
		self.name_label.raise_()
		self.name_value.raise_()
		self.id_label.raise_()
		self.id_value.raise_()
		self.gender_label.raise_()
		self.gender_value.raise_()
		self.dob_label.raise_()
		self.dob_value.raise_()

		_translate = QtCore.QCoreApplication.translate
		self.name_label.setText(_translate("MainWindow", "Name"))
		self.name_value.setText(_translate("MainWindow", self.window.basicInfo['name']))
		self.id_label.setText(_translate("MainWindow", "ID"))
		self.id_value.setText(_translate("MainWindow", self.window.basicInfo['id']))
		self.gender_label.setText(_translate("MainWindow", "Gender"))
		self.gender_value.setText(_translate("MainWindow", self.window.basicInfo['gender']))
		self.dob_label.setText(_translate("MainWindow", "DOB"))
		self.dob_value.setText(_translate("MainWindow", self.window.basicInfo['dob']))

	def create_patient_icon(self):
		"""
		Create the icon on the left of the patient bar.
		"""
		self.icon = QtWidgets.QLabel(self.widget)
		self.icon.setMaximumWidth(30)
		self.icon.setGeometry(QtCore.QRect(10, 0, 0, 0))
		self.icon.setText("")
		self.icon.setPixmap(QtGui.QPixmap(":/images/Icon/patient.png"))

	def create_patient_name(self):
		"""
		Create the label and the value widgets for the patient name.
		"""
		# Container and layout
		self.name_widget = QtWidgets.QWidget(self.widget)
		self.name_widget.setGeometry(QtCore.QRect(50, 5, 370, 31))
		self.name_layout = QtWidgets.QHBoxLayout(self.name_widget)
		self.name_layout.setContentsMargins(0, 8, 0, 0)
		self.name_layout.setSpacing(5)
		self.name_layout.setAlignment(QtCore.Qt.AlignLeft)
		self.name_widget.setFocusPolicy(QtCore.Qt.NoFocus)

		# Label
		self.name_label = QtWidgets.QLabel(self.name_widget)
		self.name_label.setFont(QtGui.QFont("Laksaman", weight=QtGui.QFont.Bold, pointSize=10))
		self.name_label.setAlignment(QtCore.Qt.AlignLeft)
		self.name_layout.addWidget(self.name_label)

		# Value
		self.name_value = QtWidgets.QLabel(self.name_widget)
		self.name_value.setAlignment(QtCore.Qt.AlignLeft)
		self.name_value.setFont(QtGui.QFont("Laksaman", pointSize=10))
		self.name_layout.addWidget(self.name_value)

	def create_patient_ID(self):
		"""
		Create the label and the value widgets for the patient ID.
		"""
		# Container and layout
		self.id_widget = QtWidgets.QWidget(self.widget)
		self.id_widget.setGeometry(QtCore.QRect(500, 5, 280, 31))
		self.id_layout = QtWidgets.QHBoxLayout(self.id_widget)
		self.id_layout.setContentsMargins(0, 8, 0, 0)
		self.id_layout.setSpacing(5)
		self.id_layout.setAlignment(QtCore.Qt.AlignLeft)
		self.id_widget.setFocusPolicy(QtCore.Qt.NoFocus)

		# Label
		self.id_label = QtWidgets.QLabel(self.id_widget)
		self.id_label.setFont(QtGui.QFont(
			"Laksaman", weight=QtGui.QFont.Bold, pointSize=10))
		self.id_label.setAlignment(QtCore.Qt.AlignLeft)
		self.id_layout.addWidget(self.id_label)

		# Value
		self.id_value = QtWidgets.QLabel(self.id_widget)
		self.id_value.setFont(QtGui.QFont("Laksaman", pointSize=10))
		self.id_value.setAlignment(QtCore.Qt.AlignLeft)
		self.id_layout.addWidget(self.id_value)

	def create_patient_gender(self):
		"""
		Create the label and the value widgets for the patient gender.
		"""
		# Container and layout
		self.gender_widget = QtWidgets.QWidget(self.widget)
		self.gender_widget.setGeometry(QtCore.QRect(830, 5, 111, 31))
		self.gender_widget.setFocusPolicy(QtCore.Qt.NoFocus)
		self.gender_layout = QtWidgets.QHBoxLayout(self.gender_widget)
		self.gender_layout.setContentsMargins(0, 8, 0, 0)
		self.gender_layout.setSpacing(5)
		self.gender_layout.setAlignment(QtCore.Qt.AlignLeft)

		# Label
		self.gender_label = QtWidgets.QLabel(self.gender_widget)
		self.gender_label.setFont(QtGui.QFont("Laksaman", weight=QtGui.QFont.Bold, pointSize=10))
		self.gender_label.setAlignment(QtCore.Qt.AlignLeft)
		self.gender_layout.addWidget(self.gender_label)

		# Value
		self.gender_value = QtWidgets.QLabel(self.gender_widget)
		self.gender_value.setFont(QtGui.QFont("Laksaman", pointSize=10))
		self.gender_value.setAlignment(QtCore.Qt.AlignLeft)
		self.gender_layout.addWidget(self.gender_value)

	def create_patient_DOB(self):
		"""
		Create the label and the value widgets for the patient date of birth.
		"""
		# Container and layout
		self.dob_widget = QtWidgets.QWidget(self.widget)
		self.dob_widget.setGeometry(QtCore.QRect(950, 5, 95, 31))
		self.dob_widget.setFocusPolicy(QtCore.Qt.NoFocus)
		self.dob_layout = QtWidgets.QHBoxLayout(self.dob_widget)
		self.dob_layout.setContentsMargins(0, 8, 0, 0)
		self.dob_layout.setSpacing(5)
		self.dob_layout.setAlignment(QtCore.Qt.AlignLeft)

		# Label
		self.dob_label = QtWidgets.QLabel(self.dob_widget)
		self.dob_label.setFont(QtGui.QFont("Laksaman", weight=QtGui.QFont.Bold, pointSize=10))
		self.dob_label.setAlignment(QtCore.Qt.AlignLeft)
		self.dob_layout.addWidget(self.dob_label)

		# Value
		self.dob_value = QtWidgets.QLabel(self.dob_widget)
		self.dob_value.setFont(QtGui.QFont("Laksaman", pointSize=10))
		self.dob_value.setAlignment(QtCore.Qt.AlignLeft)
		self.dob_layout.addWidget(self.dob_value)
