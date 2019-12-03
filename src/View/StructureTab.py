from PyQt5 import QtWidgets, QtGui, QtCore
from random import randint, seed
import numpy as np

class StructureTab(object):
	def __init__(self, main_window):
		self.main_window = main_window
		self.color_dict = self.init_color_roi()
		self.tab1_structures = QtWidgets.QWidget()
		self.tab1_structures.setFocusPolicy(QtCore.Qt.NoFocus)
		self.init_content()
		self.update_content()
		self.init_layout()

	# Initialization of colors for ROIs
	def init_color_roi(self):
		roiColor = dict()

		# ROI Display color from RTSS file
		roiContourInfo = self.main_window.dictDicomTree_rtss['ROI Contour Sequence']
		if len(roiContourInfo) > 0:
			for item, roi_dict in roiContourInfo.items():
				id = item.split()[1]
				roi_id = self.main_window.listRoisID[int(id)]
				RGB_dict = dict()
				if 'ROI Display Color' in roiContourInfo[item]:
					RGB_list = roiContourInfo[item]['ROI Display Color'][0]
					RGB_dict['R'] = RGB_list[0]
					RGB_dict['G'] = RGB_list[1]
					RGB_dict['B'] = RGB_list[2]
				else:
					seed(1)
					RGB_dict['R'] = randint(0, 255)
					RGB_dict['G'] = randint(0, 255)
					RGB_dict['B'] = randint(0, 255)
				with open('src/data/line&fill_configuration', 'r') as stream:
					elements = stream.readlines()
					if len(elements) > 0:
						roi_line = int(elements[0].replace('\n', ''))
						roi_opacity = int(elements[1].replace('\n', ''))
						iso_line = int(elements[2].replace('\n', ''))
						iso_opacity = int(elements[3].replace('\n', ''))
					else:
						roi_line = 1
						roi_opacity = 10
						iso_line = 2
						iso_opacity = 5
					stream.close()
				roi_opacity = int((roi_opacity / 100) * 255)
				RGB_dict['QColor'] = QtGui.QColor(
					RGB_dict['R'], RGB_dict['G'], RGB_dict['B'])
				RGB_dict['QColor_ROIdisplay'] = QtGui.QColor(
					RGB_dict['R'], RGB_dict['G'], RGB_dict['B'], roi_opacity)
				roiColor[roi_id] = RGB_dict
		return roiColor

	# Initialization of the list of structures (left column of the main page)
	def init_layout(self):
		self.layout = QtWidgets.QHBoxLayout(self.tab1_structures)
		self.layout.setContentsMargins(0, 0, 0, 0)
		self.layout.addWidget(self.scroll_area)
		self.main_window.tab1.addTab(self.tab1_structures, "")

		_translate = QtCore.QCoreApplication.translate
		self.main_window.tab1.setTabText(self.main_window.tab1.indexOf(self.tab1_structures),
										 _translate("MainWindow", "Structures"))

	def init_content(self):
		# Scroll Area
		self.scroll_area = QtWidgets.QScrollArea(self.tab1_structures)
		self.scroll_area.setWidgetResizable(True)
		self.scroll_area.setFocusPolicy(QtCore.Qt.NoFocus)
		# Scroll Area Content
		self.scroll_area_content = QtWidgets.QWidget(self.scroll_area)
		self.scroll_area.ensureWidgetVisible(self.scroll_area_content)
		self.scroll_area_content.setFocusPolicy(QtCore.Qt.NoFocus)
		# Grid Layout containing the color squares and the checkboxes
		self.layout_content = QtWidgets.QGridLayout(self.scroll_area_content)
		self.layout_content.setContentsMargins(3, 3, 3, 3)
		self.layout_content.setVerticalSpacing(0)
		self.layout_content.setHorizontalSpacing(10)

	# Add the contents in the list of structures (left column of the main page)
	def update_content(self):
		index = 0
		for key, value in self.main_window.rois.items():
			# Create color square
			color_square_label = QtWidgets.QLabel()
			color_square_pix = QtGui.QPixmap(15, 15)
			color_square_pix.fill(self.color_dict[key]['QColor'])
			color_square_label.setPixmap(color_square_pix)
			self.layout_content.addWidget(color_square_label, index, 0, 1, 1)

			# QCheckbox
			text = value['name']
			checkbox = QtWidgets.QCheckBox()
			checkbox.setFocusPolicy(QtCore.Qt.NoFocus)
			checkbox.clicked.connect(lambda state, text=key: self.structure_checked(state, text))
			checkbox.setStyleSheet("font: 10pt \"Laksaman\";")
			checkbox.setText(text)
			self.layout_content.addWidget(checkbox, index, 1, 1, 1)

			index += 1

		self.scroll_area.setStyleSheet("QScrollArea {background-color: #ffffff; border-style: none;}")
		self.scroll_area_content.setStyleSheet("QWidget {background-color: #ffffff; border-style: none;}")

		vspacer = QtWidgets.QSpacerItem(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
		hspacer = QtWidgets.QSpacerItem(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
		self.layout_content.addItem(vspacer, index + 1, 0, 1, -1)
		self.layout_content.addItem(hspacer, 0, 2, -1, 1)

		self.scroll_area.setWidget(self.scroll_area_content)

	# Function triggered when the state of checkbox of a structure has changed
	#   Update the list of selected structures and DVH view
	def structure_checked(self, state, key):
		# Checkbox of the structure checked
		if state:
			# Add the structure in the list of selected ROIS
			self.main_window.selected_rois.append(key)
			# Select the corresponding item in Structure Info selector
			# select the real index from the np array since the keys differ
			index = np.where(self.main_window.np_listRoisID == key)
			index = index[0][0] + 1
			self.main_window.struct_info.combobox.setCurrentIndex(index)
			self.main_window.struct_info.item_selected(index)

		# Checkbox of the structure unchecked
		else:
			# Remove the structure from the list of selected ROIS
			self.main_window.selected_rois.remove(key)

		# Update the DVH view
		self.main_window.dvh.update_plot(self.main_window)
		self.main_window.dicom_view.update_view()
