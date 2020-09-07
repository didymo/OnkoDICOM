import csv
from pathlib import Path

from PyQt5 import QtWidgets, QtGui, QtCore
from random import randint, seed
import numpy as np
from PyQt5.QtCore import Qt

from src.Model import ImageLoading
from src.View.mainpage.StructureWidget import StructureWidget
from src.Controller.ROIOptionsController import *


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
		self.layout = QtWidgets.QVBoxLayout(self.tab1_structures)
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
		self.layout_content = QtWidgets.QVBoxLayout(self.scroll_area_content)
		self.layout_content.setContentsMargins(0, 0, 0, 0)
		self.layout_content.setSpacing(0)
		self.layout_content.setAlignment(Qt.AlignTop)

	def init_standard_names(self):
		"""
		Create two lists containing standard organ and standard volume names as set by the Add-On options.
		"""
		with open('src/data/csv/organName.csv', 'r') as f:
			self.standard_organ_names = []

			csv_input = csv.reader(f)
			header = next(f)  # Ignore the "header" of the column
			for row in csv_input:
				self.standard_organ_names.append(row[0])

		with open('src/data/csv/volumeName.csv', 'r') as f:
			self.standard_volume_names = []

			csv_input = csv.reader(f)
			header = next(f)  # Ignore the "header" of the column
			for row in csv_input:
				self.standard_volume_names.append(row[1])

	def update_content(self):
		"""
		Add the contents (color square and checkbox) in the scrolling area widget.
		"""
		# Clear the children
		for i in reversed(range(self.layout_content.count())):
			self.layout_content.itemAt(i).widget().setParent(None)

		row = 0
		for roi_id, roi_dict in self.main_window.rois.items():
			# Creates a widget representing each ROI
			structure = StructureWidget(roi_id, self.color_dict[roi_id], roi_dict['name'], self)
			structure.structure_renamed.connect(self.structure_modified)
			self.layout_content.addWidget(structure)
			row += 1

		self.scroll_area.setStyleSheet("QScrollArea {background-color: #ffffff; border-style: none;}")
		self.scroll_area_content.setStyleSheet("QWidget {background-color: #ffffff; border-style: none;}")

		self.scroll_area.setWidget(self.scroll_area_content)

	def structure_modified(self, changes):
		"""
		Executes when a structure is renamed/deleted. Displays indicator that structure has changed.
		changes is a tuple of (new_dataset, description_of_changes)
		description_of_changes follows the format {"type_of_change": value_of_change}.
		Examples: {"rename": ["TOOTH", "TEETH"]} represents that the TOOTH structure has been renamed to TEETH.
		{"delete": ["TEETH", "MAXILLA"]} represents that the TEETH and MAXILLA structures have been deleted.
		"""

		print(changes)
		new_dataset = changes[0]
		change_description = changes[1]

		# If this is the first time the RTSS has been modified, create a modified indicator giving the user the option
		# to save their new file.
		if not self.main_window.rtss_modified:

			modified_indicator_widget = QtWidgets.QWidget()
			modified_indicator_widget.setContentsMargins(8, 5, 8, 5)
			modified_indicator_layout = QtWidgets.QHBoxLayout()
			modified_indicator_layout.setAlignment(Qt.AlignLeft)

			modified_indicator_icon = QtWidgets.QLabel()
			modified_indicator_icon.setPixmap(QtGui.QPixmap("src/Icon/alert.png"))
			modified_indicator_layout.addWidget(modified_indicator_icon)

			modified_indicator_text = QtWidgets.QLabel("Structures have been modified")
			modified_indicator_text.setStyleSheet("color: red")
			modified_indicator_layout.addWidget(modified_indicator_text)

			modified_indicator_widget.setLayout(modified_indicator_layout)
			modified_indicator_widget.mouseReleaseEvent = self.save_new_rtss  # When the widget is clicked, save the rtss
			self.layout.addWidget(modified_indicator_widget)

		# If this is the first change made to the RTSS file, update the dataset with the new one so that OnkoDICOM
		# starts working off this dataset rather than the original RTSS file.
		self.main_window.rtss_modified = True
		self.main_window.dataset_rtss = new_dataset

		# Refresh ROIs in main page
		self.main_window.rois = ImageLoading.get_roi_info(new_dataset)
		self.main_window.dict_raw_ContourData, self.main_window.dict_NumPoints = ImageLoading.get_raw_contour_data(new_dataset)
		self.main_window.list_roi_numbers = self.main_window.ordered_list_rois()
		self.main_window.selected_rois = []

		if self.main_window.raw_dvh is not None:
		# Rename structures in DVH list
			if "rename" in changes[1]:
				for key, dvh in self.main_window.raw_dvh.items():
					if dvh.name == change_description["rename"][0]:
						dvh.name = change_description["rename"][1]
						break

			# Remove structures from DVH list - the only visible effect of this section is the exported DVH csv
			if "delete" in changes[1]:
				list_of_deleted = []
				for key, dvh in self.main_window.raw_dvh.items():
					if dvh.name in change_description["delete"]:
						list_of_deleted.append(key)
				for key in list_of_deleted:
					self.main_window.raw_dvh.pop(key)

		# Refresh ROIs in DVH tab and DICOM View
		if hasattr(self.main_window, 'dvh'):
			self.main_window.dvh.update_plot(self.main_window)
		self.main_window.dicom_view.update_view()

		# Refresh structure tab
		self.update_content()

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

	def save_new_rtss(self, event=None):
		rtss_directory = str(Path(self.main_window.file_rtss).parent)
		save_filepath = QtWidgets.QFileDialog.getSaveFileName(self.main_window, "Save file", rtss_directory)[0]
		if save_filepath != "":
			self.main_window.dataset_rtss.save_as(save_filepath)
			QtWidgets.QMessageBox.about(self.main_window, "File saved", "The RTSTRUCT file has been saved.")
			self.main_window.rtss_modified = False
