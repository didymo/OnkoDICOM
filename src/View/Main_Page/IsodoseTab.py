from PyQt5 import QtWidgets, QtCore, QtGui

class IsodosesTab(object):
	"""
	Manage all functionality related to Isodoses (second tab of left column).
	- Create a dictionary of Isodoses-colors where the key is the percentage of isodose and the value a QColor
	(color_dict).
	- Create the color squares and the checkboxes.
	- Place the widgets in the window of the main page.
	"""
	
	def __init__(self, main_window):
		"""
		Create the color squares and the checkboxes for the Structures tab.
		Add the widgets to the window of the main page.

		:param main_window:
		 the window of the main page
		"""
		self.main_window = main_window
		self.color_dict = self.init_color_isod()
		self.tab1_isodoses = QtWidgets.QWidget()
		self.tab1_isodoses.setFocusPolicy(QtCore.Qt.NoFocus)
		self.init_color_square()
		self.init_checkbox()
		self.init_layout()

	def init_layout(self):
		"""
		Initialize the layout for the Isodoses tab.
		Add the color squares and the checkboxes in the layout.
		Add the whole container 'tab2_isodoses' as a tab in the main page.
		"""
		self.layout = QtWidgets.QGridLayout(self.tab1_isodoses)
		self.layout.setContentsMargins(5, 5, 5, 5)

		# Add Color Squares
		self.layout.addWidget(self.color1_isod, 0, 0, 1, 1)
		self.layout.addWidget(self.color2_isod, 1, 0, 1, 1)
		self.layout.addWidget(self.color3_isod, 2, 0, 1, 1)
		self.layout.addWidget(self.color4_isod, 3, 0, 1, 1)
		self.layout.addWidget(self.color5_isod, 4, 0, 1, 1)
		self.layout.addWidget(self.color6_isod, 5, 0, 1, 1)
		self.layout.addWidget(self.color7_isod, 6, 0, 1, 1)
		self.layout.addWidget(self.color8_isod, 7, 0, 1, 1)
		self.layout.addWidget(self.color9_isod, 8, 0, 1, 1)
		self.layout.addWidget(self.color10_isod, 9, 0, 1, 1)

		# Add Checkboxes
		self.layout.addWidget(self.checkbox1, 0, 2)
		self.layout.addWidget(self.checkbox2, 1, 2)
		self.layout.addWidget(self.checkbox3, 2, 2)
		self.layout.addWidget(self.checkbox4, 3, 2)
		self.layout.addWidget(self.checkbox5, 4, 2)
		self.layout.addWidget(self.checkbox6, 5, 2)
		self.layout.addWidget(self.checkbox7, 6, 2)
		self.layout.addWidget(self.checkbox8, 7, 2)
		self.layout.addWidget(self.checkbox9, 8, 2)
		self.layout.addWidget(self.checkbox10, 9, 2)

		# Add Spacers
		vspacer = QtWidgets.QSpacerItem(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
		hspacer = QtWidgets.QSpacerItem(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
		self.layout.addItem(vspacer, 10, 0, 3, -1)
		self.layout.addItem(hspacer, 0, 3, -1, 11)

		self.main_window.tab1.addTab(self.tab1_isodoses, "Isodoses")


	def init_checkbox(self):
		"""
		Initialize the checkbox objects.
		"""
		# Values of Isodoses
		val1 = int(1.07 * self.main_window.rxdose)
		val2 = int(1.05 * self.main_window.rxdose)
		val3 = int(1.00 * self.main_window.rxdose)
		val4 = int(0.95 * self.main_window.rxdose)
		val5 = int(0.90 * self.main_window.rxdose)
		val6 = int(0.80 * self.main_window.rxdose)
		val7 = int(0.70 * self.main_window.rxdose)
		val8 = int(0.60 * self.main_window.rxdose)
		val9 = int(0.30 * self.main_window.rxdose)
		val10 = int(0.10 * self.main_window.rxdose)

		# Checkboxes
		self.checkbox1 = QtWidgets.QCheckBox("107 % / " + str(val1) + " cGy [Max]")
		self.checkbox2 = QtWidgets.QCheckBox("105 % / " + str(val2) + " cGy")
		self.checkbox3 = QtWidgets.QCheckBox("100 % / " + str(val3) + " cGy")
		self.checkbox4 = QtWidgets.QCheckBox("95 % / " + str(val4) + " cGy")
		self.checkbox5 = QtWidgets.QCheckBox("90 % / " + str(val5) + " cGy")
		self.checkbox6 = QtWidgets.QCheckBox("80 % / " + str(val6) + " cGy")
		self.checkbox7 = QtWidgets.QCheckBox("70 % / " + str(val7) + " cGy")
		self.checkbox8 = QtWidgets.QCheckBox("60 % / " + str(val8) + " cGy")
		self.checkbox9 = QtWidgets.QCheckBox("30 % / " + str(val9) + " cGy")
		self.checkbox10 = QtWidgets.QCheckBox("10 % / " + str(val10) + " cGy")

		self.checkbox1.clicked.connect(lambda state, text=107: self.checked_dose(state, text))
		self.checkbox2.clicked.connect(lambda state, text=105: self.checked_dose(state, text))
		self.checkbox3.clicked.connect(lambda state, text=100: self.checked_dose(state, text))
		self.checkbox4.clicked.connect(lambda state, text=95: self.checked_dose(state, text))
		self.checkbox5.clicked.connect(lambda state, text=90: self.checked_dose(state, text))
		self.checkbox6.clicked.connect(lambda state, text=80: self.checked_dose(state, text))
		self.checkbox7.clicked.connect(lambda state, text=70: self.checked_dose(state, text))
		self.checkbox8.clicked.connect(lambda state, text=60: self.checked_dose(state, text))
		self.checkbox9.clicked.connect(lambda state, text=30: self.checked_dose(state, text))
		self.checkbox10.clicked.connect(lambda state, text=10: self.checked_dose(state, text))

		self.checkbox1.setStyleSheet("font: 10pt \"Laksaman\";")
		self.checkbox2.setStyleSheet("font: 10pt \"Laksaman\";")
		self.checkbox3.setStyleSheet("font: 10pt \"Laksaman\";")
		self.checkbox4.setStyleSheet("font: 10pt \"Laksaman\";")
		self.checkbox5.setStyleSheet("font: 10pt \"Laksaman\";")
		self.checkbox6.setStyleSheet("font: 10pt \"Laksaman\";")
		self.checkbox7.setStyleSheet("font: 10pt \"Laksaman\";")
		self.checkbox8.setStyleSheet("font: 10pt \"Laksaman\";")
		self.checkbox9.setStyleSheet("font: 10pt \"Laksaman\";")
		self.checkbox10.setStyleSheet("font: 10pt \"Laksaman\";")

	# Function triggered when a dose level selected
	# Updates the list of selected isodoses and dicom view
	def checked_dose(self, state, isod_value):
		"""
		Function triggered when the checkbox of a structure is checked / unchecked.
		Update the list of selected structures.
		Update the DICOM view.
		
		:param state: True if the checkbox is checked, False otherwise.
		:param isod_value: Percentage of isodose.
		"""
		if state:
			# Add the dose to the list of selected doses
			self.main_window.selected_doses.append(isod_value)
		else:
			# Remove dose from list of previously selected doses
			self.main_window.selected_doses.remove(isod_value)
		# Update the dicom view
		self.main_window.dicom_view.update_view()

	def init_color_square(self):
		"""
		Initialize the color squares.
		"""
		self.color1_isod = self.draw_color_square(131, 0, 0)
		self.color2_isod = self.draw_color_square(185, 0, 0)
		self.color3_isod = self.draw_color_square(255, 46, 0)
		self.color4_isod = self.draw_color_square(255, 161, 0)
		self.color5_isod = self.draw_color_square(253, 255, 0)
		self.color6_isod = self.draw_color_square(0, 255, 0)
		self.color7_isod = self.draw_color_square(0, 143, 0)
		self.color8_isod = self.draw_color_square(0, 255, 255)
		self.color9_isod = self.draw_color_square(33, 0, 255)
		self.color10_isod = self.draw_color_square(11, 0, 134)


	def init_color_isod(self):
		"""
		Create a dictionary containing the colors for each isodose.

		:return: Dictionary where the key is the percentage of isodose and the value a QColor object.
		"""
		roiColor = dict()
		roiColor[107] = QtGui.QColor(131, 0, 0)
		roiColor[105] = QtGui.QColor(185, 0, 0)
		roiColor[100] = QtGui.QColor(255, 46, 0)
		roiColor[95] = QtGui.QColor(255, 161, 0)
		roiColor[90] = QtGui.QColor(253, 255, 0)
		roiColor[80] = QtGui.QColor(0, 255, 0)
		roiColor[70] = QtGui.QColor(0, 143, 0)
		roiColor[60] = QtGui.QColor(0, 255, 255)
		roiColor[30] = QtGui.QColor(33, 0, 255)
		roiColor[10] = QtGui.QColor(11, 0, 134)
		return roiColor


	def draw_color_square(self, red, green, blue):
		"""
		Create a color square.
		:param red: Red component of the color.
		:param green: Green component of the color.
		:param blue: Blue component of the color.

		:return: Color square widget.
		"""
		color_square_label = QtWidgets.QLabel()
		color_square_pix = QtGui.QPixmap(15, 15)
		color_square_pix.fill(QtGui.QColor(red, green, blue))
		color_square_label.setPixmap(color_square_pix)
		return color_square_label