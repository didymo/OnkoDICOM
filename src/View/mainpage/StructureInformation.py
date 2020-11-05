from PyQt5 import QtWidgets, QtCore, QtGui


class StructureInformation(object):
	"""
	Manage all functionalities related to the Structure Information section (bottom left of the main page).
	- Retrieve information of the ROI structures.
	- Set up the UI.
	"""

	def __init__(self, mainWindow):
		"""
		Retrieve information for all ROI structures and set up the UI.

		:param mainWindow:
		 the window of the main page
		"""
		self.window = mainWindow
		self.widget = QtWidgets.QWidget(self.window.left_widget)
		self.combobox = self.selector_combobox()
		self.list_info = self.get_struct_info()
		self.setup_ui()


	def setup_ui(self):
		"""
		Set up the UI for the Structure Information section.
		"""

		layout = QtWidgets.QGridLayout(self.widget)
		layout.setContentsMargins(0, 0, 0, 0)

		# Structure Information: Information Icon
		icon = QtWidgets.QLabel(self.widget)
		icon.setText("")
		icon.setPixmap(QtGui.QPixmap(":/images//res/images/btn-icons/info.png"))

		# Structure Information: Header
		label = QtWidgets.QLabel(self.widget)
		label.setFont(QtGui.QFont("Laksaman", weight=QtGui.QFont.Bold, pointSize=10))


		# Structure Information: "Volume"
		volume_label = QtWidgets.QLabel(self.widget)
		volume_label.setGeometry(QtCore.QRect(10, 70, 68, 29))
		volume_label.setStyleSheet("font: 10pt \"Laksaman\";")
		self.volume_value = QtWidgets.QLabel(self.widget)
		self.volume_value.setGeometry(QtCore.QRect(95, 70, 81, 31))
		self.volume_value.setStyleSheet("font: 10pt \"Laksaman\";")
		volume_unit = QtWidgets.QLabel(self.widget)
		volume_unit.setGeometry(QtCore.QRect(160, 70, 81, 31))
		volume_unit.setStyleSheet("font: 10pt \"Laksaman\";")

		# Structure Information: "Min Dose"
		min_dose_label = QtWidgets.QLabel(self.widget)
		min_dose_label.setGeometry(QtCore.QRect(10, 100, 68, 31))
		min_dose_label.setStyleSheet("font: 10pt \"Laksaman\";")
		self.min_dose_value = QtWidgets.QLabel(self.widget)
		self.min_dose_value.setGeometry(QtCore.QRect(95, 100, 81, 31))
		self.min_dose_value.setStyleSheet("font: 10pt \"Laksaman\";")
		min_dose_unit = QtWidgets.QLabel(self.widget)
		min_dose_unit.setGeometry(QtCore.QRect(160, 100, 81, 31))
		min_dose_unit.setStyleSheet("font: 10pt \"Laksaman\";")

		# Structure Information: "Max Dose"
		max_dose_label = QtWidgets.QLabel(self.widget)
		max_dose_label.setGeometry(QtCore.QRect(10, 130, 68, 31))
		max_dose_label.setStyleSheet("font: 10pt \"Laksaman\";")
		self.max_dose_value = QtWidgets.QLabel(self.widget)
		self.max_dose_value.setGeometry(QtCore.QRect(95, 130, 81, 31))
		self.max_dose_value.setStyleSheet("font: 10pt \"Laksaman\";")
		max_dose_unit = QtWidgets.QLabel(self.widget)
		max_dose_unit.setGeometry(QtCore.QRect(160, 130, 81, 31))
		max_dose_unit.setStyleSheet("font: 10pt \"Laksaman\";")

		# Structure Information: "Mean Dose"
		mean_dose_label = QtWidgets.QLabel(self.widget)
		mean_dose_label.setGeometry(QtCore.QRect(10, 160, 81, 31))
		mean_dose_label.setStyleSheet("font: 10pt \"Laksaman\";")
		self.mean_dose_value = QtWidgets.QLabel(self.widget)
		self.mean_dose_value.setGeometry(QtCore.QRect(95, 160, 81, 31))
		self.mean_dose_value.setStyleSheet("font: 10pt \"Laksaman\";")
		mean_dose_unit = QtWidgets.QLabel(self.widget)
		mean_dose_unit.setGeometry(QtCore.QRect(160, 160, 81, 31))
		mean_dose_unit.setStyleSheet("font: 10pt \"Laksaman\";")

		layout.addWidget(icon, 0, 0, 1, 1)
		layout.addWidget(label, 0, 1, 1, 3)
		layout.addWidget(self.combobox, 1, 0, 1, 4)
		layout.addWidget(volume_label, 2, 0, 1, 2)
		layout.addWidget(self.volume_value, 2, 2, 1, 1)
		layout.addWidget(volume_unit, 2, 3, 1, 1)
		layout.addWidget(min_dose_label, 3, 0, 1, 2)
		layout.addWidget(self.min_dose_value, 3, 2, 1, 1)
		layout.addWidget(min_dose_unit, 3, 3, 1, 1)
		layout.addWidget(max_dose_label, 4, 0, 1, 2)
		layout.addWidget(self.max_dose_value, 4, 2, 1, 1)
		layout.addWidget(max_dose_unit, 4, 3, 1, 1)
		layout.addWidget(mean_dose_label, 5, 0, 1, 2)
		layout.addWidget(self.mean_dose_value, 5, 2, 1, 1)
		layout.addWidget(mean_dose_unit, 5, 3, 1, 1)

		icon.raise_()
		label.raise_()
		self.combobox.raise_()
		volume_label.raise_()
		min_dose_label.raise_()
		max_dose_label.raise_()
		mean_dose_label.raise_()
		self.volume_value.raise_()
		self.min_dose_value.raise_()
		self.max_dose_value.raise_()
		self.mean_dose_value.raise_()
		volume_unit.raise_()
		min_dose_unit.raise_()
		max_dose_unit.raise_()
		mean_dose_unit.raise_()
		self.widget.raise_()

		_translate = QtCore.QCoreApplication.translate

		# Set structure information labels
		label.setText(_translate("MainWindow", "Structure Information"))
		volume_label.setText(_translate("MainWindow", "Volume:"))
		min_dose_label.setText(_translate("MainWindow", "Min Dose:"))
		max_dose_label.setText(_translate("MainWindow", "Max Dose:"))
		mean_dose_label.setText(_translate("MainWindow", "Mean Dose:"))

		# # Set structure information units
		volume_unit.setText(_translate("MainWindow", "cm³"))
		min_dose_unit.setText(_translate("MainWindow", "cGy"))
		max_dose_unit.setText(_translate("MainWindow", "cGy"))
		mean_dose_unit.setText(_translate("MainWindow", "cGy"))


	def get_struct_info(self):
		"""
		Dictionary for all the ROI structures containing information about the volume, the min, max and mean doses.

		:return:
		 Dictionary where:
		  - the key is the id of the ROI structure
		  - the value is a dictionary whose keys are volume, min, max and mean.
		"""

		res = dict()
		for roi_id, _ in self.window.rois.items():
			struct_info = dict()
			dvh = self.window.raw_dvh[roi_id]
			# counts is an array of values indicating the volume at each dose (in cGy)
			counts = self.window.dvh_x_y[roi_id]['counts']

			struct_info['volume'] = float("{0:.3f}".format(dvh.volume))

			# The volume of the ROI is equal to 0
			if dvh.volume == 0:
				struct_info['min'] = '-'
				struct_info['max'] = '-'
				struct_info['mean'] = '-'


			# The volume of the ROI is greater than 0
			else:
				"""
				The min dose is the last dose (in cGy) where the percentage of volume
				 receiving this dose is equal to 100%.
				The mean dose is the last dose (in cGy) where the percentage of volume
				 receiving this dose is greater than 50%.
				The max dose is the last dose (in cGy) where the percentage of volume
				 receiving this dose is greater than 0%.
				"""
				volume_percent = 100 * counts / dvh.volume
				# index is used as a cursor to get the min, mean and max doses.
				index = 0

				# Get the min dose of the ROI
				while index < len(volume_percent) and int(volume_percent.item(index)) == 100:
					index += 1
				if index == 0:
					struct_info['min'] = 0
				else:
					struct_info['min'] = index - 1

				# Get the mean dose of the ROI
				while index < len(volume_percent) and volume_percent.item(index) > 50:
					index += 1
				if index == 0:
					struct_info['mean'] = 0
				else:
					struct_info['mean'] = index - 1

				# Get the max dose of the ROI
				while index < len(volume_percent) and volume_percent.item(index) != 0:
					index += 1
				if index == 0:
					struct_info['max'] = 0
				else:
					struct_info['max'] = index - 1

			res[roi_id] = struct_info

		return res



	def selector_combobox(self):
		"""
		:return: Combobox to select the ROI structure.
		"""
		combobox = QtWidgets.QComboBox(self.widget)
		combobox.setStyleSheet("QComboBox {font: 75 10pt \"Laksaman\";"
									"combobox-popup: 0;"
									"background-color: #efefef; }")
		combobox.addItem("Select...")
		for key, value in self.window.rois.items():
			combobox.addItem(value['name'])
		combobox.activated.connect(self.item_selected)
		combobox.setGeometry(QtCore.QRect(5, 35, 188, 31))
		combobox.setFocusPolicy(QtCore.Qt.NoFocus)
		
		return combobox


	def item_selected(self, index):
		"""
		Function triggered when an item of the combobox is selected.
		Show the information of the ROI structure selected.

		:param index:
		 index of the item selected
		"""
		_translate = QtCore.QCoreApplication.translate

		if index == 0:
			self.volume_value.setText(_translate("MainWindow", "-"))
			self.min_dose_value.setText(_translate("MainWindow", "-"))
			self.max_dose_value.setText(_translate("MainWindow", "-"))
			self.mean_dose_value.setText(_translate("MainWindow", "-"))

		else:
			struct_id = self.window.list_roi_numbers[index - 1]
			self.volume_value.setText(_translate("MainWindow", str(self.list_info[struct_id]['volume'])))
			self.min_dose_value.setText(_translate("MainWindow", str(self.list_info[struct_id]['min'])))
			self.max_dose_value.setText(_translate("MainWindow", str(self.list_info[struct_id]['max'])))
			self.mean_dose_value.setText(_translate("MainWindow", str(self.list_info[struct_id]['mean'])))