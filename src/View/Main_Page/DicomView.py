from PyQt5 import QtWidgets

try:
	from matplotlib import _cntr as cntr
except ImportError:
	import legacycontour._cntr as cntr
from src.Model.GetPatientInfo import *
from src.Model.ROI import *
from src.Model.Isodose import *
from copy import deepcopy


class DicomView(object):
	"""
	Manage all functionalities related to the DICOM View tab.
	- Create and update the DICOM Image View and its metadata.
	- Manage display of ROI contour.
	- Manage display of isodose contour.
	- Zoom In and Zoom Out functionalities.
	"""

	def __init__(self, mainWindow):
		"""
		Create the components (slider, view, metadata) for the DICOM View tab.
		Add the DICOM View tab to the window of the main page.

		:param mainWindow:
		 the window of the main page
		"""

		self.main_window = mainWindow
		if self.main_window.has_rtss:
			self.roi_color = mainWindow.structures_tab.color_dict
		if self.main_window.has_rtdose:
			self.isod_color = mainWindow.isodoses_tab.color_dict
		mainWindow.tab2_view = QtWidgets.QWidget()
		mainWindow.tab2_view.setFocusPolicy(QtCore.Qt.NoFocus)
		self.init_slider()
		self.init_view()
		self.init_metadata()
		self.update_view()
		self.init_layout()


	def init_layout(self):
		"""
		Initialize the layout for the DICOM View tab.
		Add the view widget and the slider in the layout.
		Add the whole container 'tab2_view' as a tab in the main page.
		"""

		self.gridLayout_view = QtWidgets.QHBoxLayout(self.main_window.tab2_view)
		self.gridLayout_view.setContentsMargins(0, 0, 0, 0)

		self.gridLayout_view.addWidget(self.view)
		self.gridLayout_view.addWidget(self.slider)
		self.main_window.tab2.addTab(self.main_window.tab2_view, "DICOM View")


	def init_slider(self):
		"""
		Create a slider for the DICOM Image View.
		"""
		self.slider = QtWidgets.QSlider(QtCore.Qt.Vertical)
		self.slider.setMinimum(0)
		self.slider.setMaximum(len(self.main_window.pixmaps) - 1)
		if self.main_window.patient_HFS:
			self.slider.setInvertedControls(True)
			self.slider.setInvertedAppearance(True)
		self.slider.setValue(int(len(self.main_window.pixmaps) / 2))
		self.slider.setTickPosition(QtWidgets.QSlider.TicksLeft)
		self.slider.setTickInterval(1)
		self.slider.setStyleSheet("QSlider::handle:vertical:hover {background: qlineargradient(x1:0, y1:0, x2:1, "
								  "y2:1, stop:0 #fff, stop:1 #ddd);border: 1px solid #444;border-radius: 4px;}")
		self.slider.valueChanged.connect(self.value_changed)
		self.slider.setGeometry(QtCore.QRect(0, 0, 50, 500))
		self.slider.setFocusPolicy(QtCore.Qt.NoFocus)


	def value_changed(self):
		"""
		Function triggered when the value of the slider has changed.
		Update the view.
		"""
		self.update_view()


	def init_view(self):
		"""
		Create a view widget for DICOM image.
		"""
		self.view = QtWidgets.QGraphicsView(self.main_window.tab2_view)
		# Add antialiasing and smoothing when zooming in
		self.view.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.SmoothPixmapTransform)
		background_brush = QtGui.QBrush(QtGui.QColor(0, 0, 0), QtCore.Qt.SolidPattern)
		self.view.setBackgroundBrush(background_brush)
		self.view.setGeometry(QtCore.QRect(0, 0, 877, 517))
		# Set event filter on the DICOM View area
		self.view.viewport().installEventFilter(self.main_window)


	def init_metadata(self):
		"""
		Create and place metadata on the view widget.
		"""
		self.layout_view = QtWidgets.QGridLayout(self.view)
		self.layout_view.setHorizontalSpacing(0)

		# Initialize text on DICOM View
		self.text_imageID = QtWidgets.QLabel(self.view)
		self.text_imagePos = QtWidgets.QLabel(self.view)
		self.text_WL = QtWidgets.QLabel(self.view)
		self.text_imageSize = QtWidgets.QLabel(self.view)
		self.text_zoom = QtWidgets.QLabel(self.view)
		self.text_patientPos = QtWidgets.QLabel(self.view)
		# # Position of the texts on DICOM View
		self.text_imageID.setAlignment(QtCore.Qt.AlignTop)
		self.text_imagePos.setAlignment(QtCore.Qt.AlignTop)
		self.text_WL.setAlignment(QtCore.Qt.AlignRight)
		self.text_imageSize.setAlignment(QtCore.Qt.AlignBottom)
		self.text_zoom.setAlignment(QtCore.Qt.AlignBottom)
		self.text_patientPos.setAlignment(QtCore.Qt.AlignRight)
		# Set all the texts in white
		self.text_imageID.setStyleSheet("QLabel { color : white; }")
		self.text_imagePos.setStyleSheet("QLabel { color : white; }")
		self.text_WL.setStyleSheet("QLabel { color : white; }")
		self.text_imageSize.setStyleSheet("QLabel { color : white; }")
		self.text_zoom.setStyleSheet("QLabel { color : white; }")
		self.text_patientPos.setStyleSheet("QLabel { color : white; }")

		# Horizontal Spacer to put metadata on the left and right of the screen
		hspacer = QtWidgets.QSpacerItem(10, 100, hPolicy=QtWidgets.QSizePolicy.Expanding,
										vPolicy=QtWidgets.QSizePolicy.Expanding)
		# Vertical Spacer to put metadata on the top and bottom of the screen
		vspacer = QtWidgets.QSpacerItem(100, 10, hPolicy=QtWidgets.QSizePolicy.Expanding,
										vPolicy=QtWidgets.QSizePolicy.Expanding)
		# Spacer of fixed size to make the metadata still visible when the scrollbar appears
		fixed_spacer = QtWidgets.QSpacerItem(13, 15, hPolicy=QtWidgets.QSizePolicy.Fixed,
											 vPolicy=QtWidgets.QSizePolicy.Fixed)

		self.layout_view.addWidget(self.text_imageID, 0, 0, 1, 1)
		self.layout_view.addWidget(self.text_imagePos, 1, 0, 1, 1)
		self.layout_view.addItem(vspacer, 2, 0, 1, 4)
		self.layout_view.addWidget(self.text_imageSize, 3, 0, 1, 1)
		self.layout_view.addWidget(self.text_zoom, 4, 0, 1, 1)
		self.layout_view.addItem(fixed_spacer, 5, 0, 1, 4)

		self.layout_view.addItem(hspacer, 0, 1, 6, 1)
		self.layout_view.addWidget(self.text_WL, 0, 2, 1, 1)
		self.layout_view.addWidget(self.text_patientPos, 4, 2, 1, 1)
		self.layout_view.addItem(fixed_spacer, 0, 3, 6, 1)


	def update_view(self, zoomChange=False, eventChangedWindow=False):
		"""
		Update the view of the DICOM Image.

		:param zoomChange:
		 Boolean indicating whether the user wants to change the zoom.
		 False by default.

		:param eventChangedWindow:
		 Boolean indicating if the user is altering the window and level values through mouse movement and button press
		 events in the DICOM View area.
		 False by default.
		"""

		if eventChangedWindow:
			self.image_display(eventChangedWindow=True)
		else:
			self.image_display()

		if zoomChange:
			self.view.setTransform(QtGui.QTransform().scale(self.main_window.zoom, self.main_window.zoom))

		# If the list of ROIs selected is not empty
		if self.main_window.selected_rois:
			self.ROI_display()

		# If the list of isodoses selected is not empty
		if self.main_window.selected_doses:
			self.isodose_display()

		self.update_metadata()
		self.view.setScene(self.scene)


	# Display the DICOM image on the DICOM View tab

	def image_display(self, eventChangedWindow=False):
		"""
		Update the image to be displayed on the DICOM View.

		:param eventChangedWindow:
		 Boolean indicating if the user is altering the window and level values through mouse movement and button press
		 events in the DICOM View area.
		 False by default.
		"""
		slider_id = self.slider.value()
		if eventChangedWindow:
			image = self.main_window.pixmapChangedWindow
		else:
			image = self.main_window.pixmaps[slider_id]
		image = image.scaled(512, 512, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
		label = QtWidgets.QLabel()
		label.setPixmap(image)
		self.scene = QtWidgets.QGraphicsScene()
		self.scene.addWidget(label)


	def update_metadata(self):
		"""
		Update metadata displayed on the DICOM Image view.
		"""
		_translate = QtCore.QCoreApplication.translate

		# Retrieve dictionary from the dataset of the slice
		id = self.slider.value()
		filename = self.main_window.filepaths[id]
		dicomtree_slice = DicomTree(filename)
		dict_slice = dicomtree_slice.dict

		# Information to display
		current_slice = dict_slice['Instance Number'][0]
		total_slices = len(self.main_window.pixmaps)
		row_img = dict_slice['Rows'][0]
		col_img = dict_slice['Columns'][0]
		patient_pos = dict_slice['Patient Position'][0]
		window = self.main_window.window
		level = self.main_window.level
		try:
			slice_pos = dict_slice['Slice Location'][0]
		except:
			imagePosPatient = dict_slice['Image Position (Patient)']
			# logging.error('Image Position (Patient):' + str(imagePosPatient))
			imagePosPatientCoordinates = imagePosPatient[0]
			# logging.error('Image Position (Patient) coordinates :' + str(imagePosPatientCoordinates))
			slice_pos = imagePosPatientCoordinates[2]

		# For formatting
		if self.main_window.zoom == 1:
			zoom = 1
		else:
			zoom = float("{0:.2f}".format(self.main_window.zoom))

		self.text_imageID.setText(_translate("MainWindow", "Image: " + str(current_slice) + " / " + str(total_slices)))
		self.text_imagePos.setText(_translate("MainWindow", "Position: " + str(slice_pos) + " mm"))
		self.text_WL.setText(_translate("MainWindow", "W/L: " + str(window) + "/" + str(level)))
		self.text_imageSize.setText(_translate("MainWindow", "Image Size: " + str(row_img) + "x" + str(col_img) + "px"))
		self.text_zoom.setText(_translate("MainWindow", "Zoom: " + str(zoom) + ":" + str(zoom)))
		self.text_patientPos.setText(_translate("MainWindow", "Patient Position: " + patient_pos))


	def get_qpen(self, color, style=1, widthF=1):
		"""
		The color and style for ROI structure and isodose display.
		:param color:
		 Color of the region. QColor type.
		:param style:
		 Style of the contour line. NoPen: 0  SolidLine: 1  DashLine: 2  DotLine: 3  DashDotLine: 4  DashDotDotLine: 5
		:param widthF:
		 Width of the contour line.
		:return: QPen object.
		"""
		pen = QPen(color)
		pen.setStyle(style)
		pen.setWidthF(widthF)
		return pen


	def ROI_display(self):
		"""
		Display ROI structures on the DICOM Image.
		"""
		slider_id = self.slider.value()
		curr_slice = self.main_window.dict_UID[slider_id]

		selected_rois_name = []
		for roi in self.main_window.selected_rois:
			selected_rois_name.append(self.main_window.rois[roi]['name'])

		for roi in self.main_window.selected_rois:
			roi_name = self.main_window.rois[roi]['name']

			if roi_name not in self.main_window.dict_polygons.keys():
				self.main_window.dict_polygons[roi_name] = {}
				self.dict_rois_contours = get_contour_pixel(self.main_window.dict_raw_ContourData, selected_rois_name,
															self.main_window.dict_pixluts, curr_slice)
				polygons = self.calc_roi_polygon(roi_name, curr_slice)
				self.main_window.dict_polygons[roi_name][curr_slice] = polygons

			elif curr_slice not in self.main_window.dict_polygons[roi_name].keys():
				self.dict_rois_contours = get_contour_pixel(self.main_window.dict_raw_ContourData, selected_rois_name,
															self.main_window.dict_pixluts, curr_slice)
				polygons = self.calc_roi_polygon(roi_name, curr_slice)
				self.main_window.dict_polygons[roi_name][curr_slice] = polygons

			else:
				polygons = self.main_window.dict_polygons[roi_name][curr_slice]

			color = self.roi_color[roi]
			with open('src/data/line&fill_configuration', 'r') as stream:
				elements = stream.readlines()
				if len(elements) > 0:
					roi_line = int(elements[0].replace('\n', ''))
					roi_opacity = int(elements[1].replace('\n', ''))
					line_width = float(elements[4].replace('\n', ''))
				else:
					roi_line = 1
					roi_opacity = 10
					line_width = 2.0
				stream.close()
			roi_opacity = int((roi_opacity / 100) * 255)
			color.setAlpha(roi_opacity)
			pen = self.get_qpen(color, roi_line, line_width)
			for i in range(len(polygons)):
				self.scene.addPolygon(polygons[i], pen, QBrush(color))


	def calc_roi_polygon(self, curr_roi, curr_slice):
		"""
		Calculate a list of polygons to display for a given ROI and a given slice.
		:param curr_roi:
		 the ROI structure
		:param curr_slice:
		 the current slice
		:return: List of polygons of type QPolygonF.
		"""
		list_polygons = []
		pixel_list = self.dict_rois_contours[curr_roi][curr_slice]
		for i in range(len(pixel_list)):
			list_qpoints = []
			contour = pixel_list[i]
			for point in contour:
				curr_qpoint = QPoint(point[0], point[1])
				list_qpoints.append(curr_qpoint)
			curr_polygon = QPolygonF(list_qpoints)
			list_polygons.append(curr_polygon)
		return list_polygons


	def isodose_display(self):
		"""
		Display isodoses on the DICOM Image.
		"""
		slider_id = self.slider.value()
		curr_slice_uid = self.main_window.dict_UID[slider_id]
		z = self.main_window.dataset[slider_id].ImagePositionPatient[2]
		grid = get_dose_grid(self.main_window.dataset['rtdose'], float(z))

		if not (grid == []):
			x, y = np.meshgrid(
				np.arange(grid.shape[1]), np.arange(grid.shape[0]))

			# Instantiate the isodose generator for this slice
			isodosegen = cntr.Cntr(x, y, grid)

			# sort selected_doses in ascending order so that the high dose isodose washes
			# paint over the lower dose isodose washes
			for sd in sorted(self.main_window.selected_doses):
				dose_level = sd * self.main_window.rxdose / \
							 (self.main_window.dataset['rtdose'].DoseGridScaling * 10000)
				contours = isodosegen.trace(dose_level)
				contours = contours[:len(contours) // 2]

				polygons = self.calc_dose_polygon(
					self.main_window.dose_pixluts[curr_slice_uid], contours)

				brush_color = self.isod_color[sd]
				with open('src/data/line&fill_configuration', 'r') as stream:
					elements = stream.readlines()
					if len(elements) > 0:
						iso_line = int(elements[2].replace('\n', ''))
						iso_opacity = int(elements[3].replace('\n', ''))
						line_width = float(elements[4].replace('\n', ''))
					else:
						iso_line = 2
						iso_opacity = 5
						line_width = 2.0
					stream.close()
				iso_opacity = int((iso_opacity / 100) * 255)
				brush_color.setAlpha(iso_opacity)
				pen_color = QtGui.QColor(brush_color.red(), brush_color.green(), brush_color.blue())
				pen = self.get_qpen(pen_color, iso_line, line_width)
				for i in range(len(polygons)):
					self.scene.addPolygon(polygons[i], pen, QBrush(brush_color))


	def calc_dose_polygon(self, dose_pixluts, contours):
		"""
		Calculate a list of polygons to display for a given isodose.
		:param dose_pixluts:
		 lookup table (LUT) to get the image pixel values
		:param contours:
		  trace outline of the isodose to be displayed
		:return: List of polygons of type QPolygonF.
		"""
		list_polygons = []
		for contour in contours:
			list_qpoints = []
			# Slicing controls how many points considered for visualization
			# Essentially effects sharpness of edges, fewer points equals "smoother" edges
			for point in contour[::2]:
				curr_qpoint = QPoint(dose_pixluts[0][int(point[0])], dose_pixluts[1][int(point[1])])
				list_qpoints.append(curr_qpoint)
			curr_polygon = QPolygonF(list_qpoints)
			list_polygons.append(curr_polygon)
		return list_polygons


	def eventFilter(self, source, event):
		"""
		Handle mouse movement and button press events in the dicom_view area. Used for altering window and level values.
		:param source: The source.
		:param event: Nature of the event on the view.
		:return: QObject event.
		"""
		# If mouse moved while the right mouse button was pressed, change window and level values
		# if event.type() == QtCore.QEvent.MouseMove and event.type() == QtCore.QEvent.MouseButtonPress:
		if event.type() == QtCore.QEvent.MouseMove and event.buttons() == QtCore.Qt.RightButton:
			# Values of x increase from left to right
			# Window value should increase when mouse pointer moved to right, decrease when moved to left
			# If the x value of the new mouse position is greater than the x value of
			# the previous position, then increment the window value by 5,
			# otherwise decrement it by 5
			if event.x() > self.main_window.x1:
				self.main_window.window += 1
			elif event.x() < self.main_window.x1:
				self.main_window.window -= 1

			# Values of y increase from top to bottom
			# Level value should increase when mouse pointer moved upwards, decrease when moved downwards
			# If the y value of the new mouse position is greater than the y value of
			# the previous position then decrement the level value by 5,
			# otherwise increment it by 5
			if event.y() > self.main_window.y1:
				self.main_window.level -= 1
			elif event.y() < self.main_window.y1:
				self.main_window.level += 1

			# Update previous position values
			self.main_window.x1 = event.x()
			self.main_window.y1 = event.y()

			# Get id of current slice
			id = self.slider.value()

			# Create a deep copy as the pixel values are a list of list
			np_pixels = deepcopy(self.main_window.pixel_values[id])

			# Update current image based on new window and level values
			self.main_window.pixmapChangedWindow = scaled_pixmap(
				np_pixels, self.main_window.window, self.main_window.level)
			self.update_view(eventChangedWindow=True)

		# When mouse button released, update all the slices based on the new values
		elif event.type() == QtCore.QEvent.MouseButtonRelease:
			self.main_window.pixmaps = get_pixmaps(self.main_window.pixel_values, self.main_window.window, self.main_window.level)

		return QtCore.QObject.event(source, event)


	def zoomIn(self):
		"""
		Zoom In the image on the DICOM View.
		"""
		self.main_window.zoom *= 1.05
		self.update_view(zoomChange=True)


	def zoomOut(self):
		"""
		Zoom Out the image on the DICOM View.
		"""
		self.main_window.zoom /= 1.05
		self.update_view(zoomChange=True)
