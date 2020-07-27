import csv

from PyQt5 import QtWidgets, QtGui, QtCore
from random import randint, seed
import numpy as np


class StructureTab(object):
	"""
	Manage all functionalities related to the ROI Structures (first tab of left column).
	- Create a dictionary of ROI-colors where the key is the ROI structure and the value a QColor (color_dict).
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
		self.color_dict = self.init_color_roi()
		self.tab1_structures = QtWidgets.QWidget()
		self.tab1_structures.setFocusPolicy(QtCore.Qt.NoFocus)
		self.init_content()
		self.init_standard_names()
		self.update_content()
		self.init_layout()

	def init_layout(self):
		"""
		Initialize the layout for the Structure tab.
		Add the scroll area widget in the layout.
		Add the whole container 'tab1_structures' as a tab in the main page.
		"""
		self.layout = QtWidgets.QHBoxLayout(self.tab1_structures)
		self.layout.setContentsMargins(0, 0, 0, 0)
		self.layout.addWidget(self.scroll_area)
		self.main_window.tab1.addTab(self.tab1_structures, "Structures")

	def init_color_roi(self):
		"""
		Create a dictionary containing the colors for each structure.

		:return: Dictionary where the key is the ROI number and the value a QColor object.
		"""
		roiColor = dict()

		# The RTSS file may contain information about the color of the ROI
		roiContourInfo = self.main_window.dictDicomTree_rtss['ROI Contour Sequence']

		# There is at least one ROI listed in the RTSS file.
		if len(roiContourInfo) > 0:
			for item, roi_dict in roiContourInfo.items():
				# Note: the keys of roiContourInfo are "item 0", "item 1", etc.
				# As all the ROI structures are identified by the ROI numbers in the whole code,
				# we get the ROI number 'roi_id' by using the member 'list_roi_numbers'
				id = item.split()[1]
				roi_id = self.main_window.list_roi_numbers[int(id)]

				if 'ROI Display Color' in roiContourInfo[item]:
					RGB_list = roiContourInfo[item]['ROI Display Color'][0]
					red = RGB_list[0]
					green = RGB_list[1]
					blue = RGB_list[2]
				else:
					seed(1)
					red = randint(0, 255)
					green = randint(0, 255)
					blue = randint(0, 255)

				roiColor[roi_id] = QtGui.QColor(red, green, blue)

		return roiColor

	def init_content(self):
		"""
		Create scrolling area widget which will contain the content.
		"""
		# Scroll Area
		self.scroll_area = QtWidgets.QScrollArea(self.tab1_structures)
		self.scroll_area.setWidgetResizable(True)
		self.scroll_area.setFocusPolicy(QtCore.Qt.NoFocus)
		# Scroll Area Content
		self.scroll_area_content = QtWidgets.QWidget(self.scroll_area)
		self.scroll_area.ensureWidgetVisible(self.scroll_area_content)
		self.scroll_area_content.setFocusPolicy(QtCore.Qt.NoFocus)
		# Layout which will contain the color squares and the checkboxes
		self.layout_content = QtWidgets.QGridLayout(self.scroll_area_content)
		self.layout_content.setContentsMargins(3, 3, 3, 3)
		self.layout_content.setVerticalSpacing(0)
		self.layout_content.setHorizontalSpacing(10)

	def init_standard_names(self):
		with open('src/data/csv/organName.csv', 'r') as f:
			self.standard_organ_names = []

			csv_input = csv.reader(f)
			header = next(f)
			for row in csv_input:
				self.standard_organ_names.append(row[0])

		with open('src/data/csv/volumeName.csv', 'r') as f:
			self.standard_volume_names = []

			csv_input = csv.reader(f)
			header = next(f)
			for row in csv_input:
				self.standard_volume_names.append(row[1])

	def update_content(self):
		"""
		Add the contents (color square and checkbox) in the scrolling area widget.
		"""
		row = 0
		for roi_id, roi_dict in self.main_window.rois.items():
			# Create color square
			color_square_label = QtWidgets.QLabel()
			color_square_pix = QtGui.QPixmap(15, 15)
			color_square_pix.fill(self.color_dict[roi_id])
			color_square_label.setPixmap(color_square_pix)
			self.layout_content.addWidget(color_square_label, row, 0, 1, 1)

			# Create checkbox
			text = roi_dict['name']
			checkbox = QtWidgets.QCheckBox()
			checkbox.setFocusPolicy(QtCore.Qt.NoFocus)
			checkbox.clicked.connect(lambda state, text=roi_id: self.structure_checked(state, text))
			if text in self.standard_organ_names or text in self.standard_volume_names:
				checkbox.setStyleSheet("font: 10pt \"Laksaman\";")
			else:
				checkbox.setStyleSheet("font: 10pt \"Laksaman\"; color: red;")
			checkbox.setText(text)
			self.layout_content.addWidget(checkbox, row, 1, 1, 1)

			row += 1

		self.scroll_area.setStyleSheet("QScrollArea {background-color: #ffffff; border-style: none;}")
		self.scroll_area_content.setStyleSheet("QWidget {background-color: #ffffff; border-style: none;}")

		# Add spacer at the end of the list
		vspacer = QtWidgets.QSpacerItem(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
		# Add spacer on the right side of the list
		hspacer = QtWidgets.QSpacerItem(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
		self.layout_content.addItem(vspacer, row + 1, 0, 1, -1)
		self.layout_content.addItem(hspacer, 0, 2, -1, 1)

		self.scroll_area.setWidget(self.scroll_area_content)

	def structure_checked(self, state, roi_id):
		"""
		Function triggered when the checkbox of a structure is checked / unchecked.
		Update the list of selected structures.
		Update the plot of the DVH and the DICOM view.

		:param state: True if the checkbox is checked, False otherwise.
		:param roi_id: ROI number
		"""
		# Checkbox of the structure checked
		if state:
			# Add the structure in the list of selected ROIS
			self.main_window.selected_rois.append(roi_id)
			# Select the corresponding item in Structure Info selector
			# Here, we select the real index from the ROI number
			np_list_roi_numbers = np.array(self.main_window.list_roi_numbers)
			index = np.where(np_list_roi_numbers == roi_id)
			index = index[0][0] + 1
			if hasattr(self.main_window, 'struct_info'):
				self.main_window.struct_info.combobox.setCurrentIndex(index)
				self.main_window.struct_info.item_selected(index)

		# Checkbox of the structure unchecked
		else:
			# Remove the structure from the list of selected ROIS
			self.main_window.selected_rois.remove(roi_id)

		# Update the DVH and DICOM view
		if hasattr(self.main_window, 'dvh'):
			self.main_window.dvh.update_plot(self.main_window)
		self.main_window.dicom_view.update_view()
