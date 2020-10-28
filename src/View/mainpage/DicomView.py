from PyQt5 import QtWidgets, QtCore, QtGui
from pandas import np

from src.Model.GetPatientInfo import DicomTree

try:
    from matplotlib import _cntr as cntr
except ImportError:
    import legacycontour._cntr as cntr

from src.Model.Isodose import get_dose_grid
from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.ROI import get_contour_pixel


class DicomView(QtWidgets.QWidget):

    def __init__(self, roi_color=None, iso_color=None):
        QtWidgets.QWidget.__init__(self)
        self.patient_dict_container = PatientDictContainer()
        self.iso_color = iso_color
        self.zoom = 1

        self.dicom_view_layout = QtWidgets.QHBoxLayout()

        # Create components
        self.slider = QtWidgets.QSlider(QtCore.Qt.Vertical)
        self.init_slider()
        self.view = QtWidgets.QGraphicsView()
        self.init_view()
        self.scene = QtWidgets.QGraphicsScene()

        # Set layout
        self.dicom_view_layout.addWidget(self.view)
        self.dicom_view_layout.addWidget(self.slider)
        self.setLayout(self.dicom_view_layout)

        # Init metadata widgets
        self.metadata_layout = QtWidgets.QGridLayout(self.view)
        self.label_image_id = QtWidgets.QLabel(self.view)
        self.label_image_pos = QtWidgets.QLabel(self.view)
        self.label_wl = QtWidgets.QLabel(self.view)
        self.label_image_size = QtWidgets.QLabel(self.view)
        self.label_zoom = QtWidgets.QLabel(self.view)
        self.label_patient_pos = QtWidgets.QLabel(self.view)
        self.init_metadata()

        self.update_view()

    def init_slider(self):
        """
        Create a slider for the DICOM Image View.
        """
        pixmaps = self.patient_dict_container.get("pixmaps")
        self.slider.setMinimum(0)
        self.slider.setMaximum(len(pixmaps) - 1)
        self.slider.setValue(int(len(pixmaps) / 2))
        self.slider.setTickPosition(QtWidgets.QSlider.TicksLeft)
        self.slider.setTickInterval(1)
        self.slider.setStyleSheet("QSlider::handle:vertical:hover {background: qlineargradient(x1:0, y1:0, x2:1, "
                                  "y2:1, stop:0 #fff, stop:1 #ddd);border: 1px solid #444;border-radius: 4px;}")
        self.slider.valueChanged.connect(self.value_changed)

    def init_view(self):
        """
        Create a view widget for DICOM image.
        """
        self.view.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.SmoothPixmapTransform)
        background_brush = QtGui.QBrush(QtGui.QColor(0, 0, 0), QtCore.Qt.SolidPattern)
        self.view.setBackgroundBrush(background_brush)
        self.view.setGeometry(QtCore.QRect(0, 0, 877, 517))

    def init_metadata(self):
        """
        Create and place metadata on the view widget.
        """
        # Position of the labels on the DICOM view.
        self.label_image_id.setAlignment(QtCore.Qt.AlignTop)
        self.label_image_pos.setAlignment(QtCore.Qt.AlignTop)
        self.label_wl.setAlignment(QtCore.Qt.AlignRight)
        self.label_image_size.setAlignment(QtCore.Qt.AlignBottom)
        self.label_zoom.setAlignment(QtCore.Qt.AlignBottom)
        self.label_patient_pos.setAlignment(QtCore.Qt.AlignBottom)

        # Set all labels to white
        stylesheet = "QLabel { color : white; }"
        self.label_image_id.setStyleSheet(stylesheet)
        self.label_image_pos.setStyleSheet(stylesheet)
        self.label_wl.setStyleSheet(stylesheet)
        self.label_image_size.setStyleSheet(stylesheet)
        self.label_zoom.setStyleSheet(stylesheet)
        self.label_patient_pos.setStyleSheet(stylesheet)

        # Horizontal Spacer to put metadata on the left and right of the screen
        h_spacer = QtWidgets.QSpacerItem(10, 100, hPolicy=QtWidgets.QSizePolicy.Expanding,
                                        vPolicy=QtWidgets.QSizePolicy.Expanding)
        # Vertical Spacer to put metadata on the top and bottom of the screen
        v_spacer = QtWidgets.QSpacerItem(100, 10, hPolicy=QtWidgets.QSizePolicy.Expanding,
                                        vPolicy=QtWidgets.QSizePolicy.Expanding)
        # Spacer of fixed size to make the metadata still visible when the scrollbar appears
        fixed_spacer = QtWidgets.QSpacerItem(13, 15, hPolicy=QtWidgets.QSizePolicy.Fixed,
                                             vPolicy=QtWidgets.QSizePolicy.Fixed)

        self.metadata_layout.addWidget(self.label_image_id, 0, 0, 1, 1)
        self.metadata_layout.addWidget(self.label_image_pos, 1, 0, 1, 1)
        self.metadata_layout.addItem(v_spacer, 2, 0, 1, 4)
        self.metadata_layout.addWidget(self.label_image_size, 3, 0, 1, 1)
        self.metadata_layout.addWidget(self.label_zoom, 4, 0, 1, 1)
        self.metadata_layout.addItem(fixed_spacer, 5, 0, 1, 4)

        self.metadata_layout.addItem(h_spacer, 0, 1, 6, 1)
        self.metadata_layout.addWidget(self.label_wl, 0, 2, 1, 1)
        self.metadata_layout.addWidget(self.label_patient_pos, 4, 2, 1, 1)
        self.metadata_layout.addItem(fixed_spacer, 0, 3, 6, 1)

    def value_changed(self):
        self.update_view()

    def update_view(self, zoom_change=False):
        """
        Update the view of the DICOM Image.
        :param zoom_change: Boolean indicating whether the user wants to change the zoom. False by default.
        """
        self.image_display()

        if zoom_change:
            self.view.setTransform(QtGui.QTransform().scale(self.zoom, self.zoom))

        if self.patient_dict_container.get("selected_rois"):
            self.roi_display()

        if self.patient_dict_container.get("selected_doses"):
            self.isodose_display()

        self.update_metadata()
        self.view.setScene(self.scene)

    def image_display(self):
        """
        Update the image to be displayed on the DICOM View.
        """
        pixmaps = self.patient_dict_container.get("pixmaps")
        slider_id = self.slider.value()
        image = pixmaps[slider_id]
        image = image.scaled(512, 512, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        label = QtWidgets.QLabel()
        label.setPixmap(image)
        self.scene = QtWidgets.QGraphicsScene()
        self.scene.addWidget(label)

    def roi_display(self):
        """
        Display ROI structures on the DICOM Image.
        """
        slider_id = self.slider.value()
        curr_slice = self.patient_dict_container.get("dict_uid")[slider_id]

        selected_rois = self.patient_dict_container.get("selected_rois")
        rois = self.patient_dict_container.get("rois")
        selected_rois_name = []
        for roi in selected_rois:
            selected_rois_name.append(rois[roi]['name'])

        for roi in selected_rois:
            roi_name = rois[roi]['name']

            if roi_name not in self.patient_dict_container.get("dict_polygons").keys():
                new_dict_polygons = self.patient_dict_container.get("dict_polygons")
                new_dict_polygons[roi_name] = {}
                dict_rois_contours = get_contour_pixel(self.patient_dict_container.get("raw_contour"),
                                                       selected_rois_name, self.patient_dict_container.get("pixluts"),
                                                       curr_slice)
                polygons = self.calc_roi_polygon(roi_name, curr_slice, dict_rois_contours)
                new_dict_polygons[roi_name][curr_slice] = polygons
                self.patient_dict_container.set("dict_polygons", new_dict_polygons)

            elif curr_slice not in self.patient_dict_container.get("dict_polygons")[roi_name].keys():
                new_dict_polygons = self.patient_dict_container.get("dict_polygons")
                dict_rois_contours = get_contour_pixel(self.patient_dict_container.get("raw_contour"),
                                                       selected_rois_name, self.patient_dict_container.get("pixluts"),
                                                       curr_slice)
                polygons = self.calc_roi_polygon(roi_name, curr_slice, dict_rois_contours)
                new_dict_polygons[roi_name][curr_slice] = polygons
                self.patient_dict_container.set("dict_polygons", new_dict_polygons)

            else:
                polygons = self.patient_dict_container.get("dict_polygons")[roi_name][curr_slice]

            color = self.patient_dict_container.get("roi_color_dict")[roi]
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
                self.scene.addPolygon(polygons[i], pen, QtGui.QBrush(color))

    def isodose_display(self):
        """
        Display isodoses on the DICOM Image.
        """
        slider_id = self.slider.value()
        curr_slice_uid = self.patient_dict_container.get("dict_uid")[slider_id]
        z = self.patient_dict_container.dataset[slider_id].ImagePositionPatient[2]
        dataset_rtdose = self.patient_dict_container.dataset['rtdose']
        grid = get_dose_grid(dataset_rtdose, float(z))

        if not (grid == []):
            x, y = np.meshgrid(
                np.arange(grid.shape[1]), np.arange(grid.shape[0]))

            # Instantiate the isodose generator for this slice
            isodosegen = cntr.Cntr(x, y, grid)

            # sort selected_doses in ascending order so that the high dose isodose washes
            # paint over the lower dose isodose washes
            for sd in sorted(self.patient_dict_container.get("selected_doses")):
                dose_level = sd * self.patient_dict_container.get("rx_dose_in_cgray") / \
                             (dataset_rtdose.DoseGridScaling * 10000)
                contours = isodosegen.trace(dose_level)
                contours = contours[:len(contours) // 2]

                polygons = self.calc_dose_polygon(
                    self.patient_dict_container.get("dose_pixluts")[curr_slice_uid], contours)

                brush_color = self.iso_color[sd]
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
                    self.scene.addPolygon(polygons[i], pen, QtGui.QBrush(brush_color))

    def update_metadata(self):
        """
        Update metadata displayed on the DICOM Image view.
        """
        # Retrieve dictionary from the dataset of the slice
        id = self.slider.value()
        filename = self.patient_dict_container.filepaths[id]
        dicom_tree_slice = DicomTree(filename)
        dict_slice = dicom_tree_slice.dict

        # Information to display
        current_slice = dict_slice['Instance Number'][0]
        total_slices = len(self.patient_dict_container.get("pixmaps"))
        row_img = dict_slice['Rows'][0]
        col_img = dict_slice['Columns'][0]
        patient_pos = dict_slice['Patient Position'][0]
        window = self.patient_dict_container.get("window")
        level = self.patient_dict_container.get("level")
        slice_pos = dict_slice['Slice Location'][0]

        # For formatting
        if self.zoom == 1:
            zoom = 1
        else:
            zoom = float("{0:.2f}".format(self.zoom))

        # Update labels
        self.label_image_id.setText("Image: %s / %s" % (str(current_slice), str(total_slices)))
        self.label_image_pos.setText("Position: %s mm" % (str(slice_pos)))
        self.label_wl.setText("W/L: %s/%s" % (str(window), str(level)))
        self.label_image_size.setText("Image Size: %sx%spx" % (str(row_img), str(col_img)))
        self.label_zoom.setText("Zoom: %s:%s" % (str(zoom), str(zoom)))
        self.label_patient_pos.setText("Patient Position: %s" % (str(current_slice)))

    def calc_roi_polygon(self, curr_roi, curr_slice, dict_rois_contours):
        """
        Calculate a list of polygons to display for a given ROI and a given slice.
        :param curr_roi:
         the ROI structure
        :param curr_slice:
         the current slice
        :return: List of polygons of type QPolygonF.
        """
        list_polygons = []
        pixel_list = dict_rois_contours[curr_roi][curr_slice]
        for i in range(len(pixel_list)):
            list_qpoints = []
            contour = pixel_list[i]
            for point in contour:
                curr_qpoint = QtCore.QPoint(point[0], point[1])
                list_qpoints.append(curr_qpoint)
            curr_polygon = QtGui.QPolygonF(list_qpoints)
            list_polygons.append(curr_polygon)
        return list_polygons

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
                curr_qpoint = QtCore.QPoint(dose_pixluts[0][int(point[0])], dose_pixluts[1][int(point[1])])
                list_qpoints.append(curr_qpoint)
            curr_polygon = QtGui.QPolygonF(list_qpoints)
            list_polygons.append(curr_polygon)
        return list_polygons

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
        pen = QtGui.QPen(color)
        pen.setStyle(style)
        pen.setWidthF(widthF)
        return pen

    def zoom_in(self):
        self.zoom *= 1.05
        self.update_view(zoom_change=True)

    def zoom_out(self):
        self.zoom /= 1.05
        self.update_view(zoom_change=True)
