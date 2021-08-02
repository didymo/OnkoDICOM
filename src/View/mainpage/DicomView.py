from PySide6 import QtWidgets, QtCore, QtGui

from src.Model.PatientDictContainer import PatientDictContainer
from src.constants import INITIAL_ONE_VIEW_ZOOM


class DicomView(QtWidgets.QWidget):

    def __init__(self, roi_color=None, iso_color=None):
        QtWidgets.QWidget.__init__(self)
        self.patient_dict_container = PatientDictContainer()
        self.iso_color = iso_color
        self.roi_color = roi_color
        self.zoom = INITIAL_ONE_VIEW_ZOOM
        self.current_slice_number = None
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

    def init_slider(self):
        """
        Create a slider for the DICOM Image View.
        """
        pixmaps = self.patient_dict_container.get("pixmaps_" + self.slice_view)
        self.slider.setMinimum(0)
        self.slider.setMaximum(len(pixmaps) - 1)
        self.slider.setValue(int(len(pixmaps) / 2))
        self.slider.setTickPosition(QtWidgets.QSlider.TicksLeft)
        self.slider.setTickInterval(1)
        self.slider.valueChanged.connect(self.value_changed)

    def init_view(self):
        """
        Create a view widget for DICOM image.
        """
        self.view.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.SmoothPixmapTransform)
        background_brush = QtGui.QBrush(QtGui.QColor(0, 0, 0), QtCore.Qt.SolidPattern)
        self.view.setBackgroundBrush(background_brush)

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

        # If roi colours are set and rois are selected then update the display
        if self.roi_color and self.patient_dict_container.get("selected_rois"):
            self.roi_display()

        # If isodose colours are set and doses are selected then update the display
        if self.iso_color and self.patient_dict_container.get("selected_doses"):
            self.isodose_display()

        if zoom_change:
            self.view.setTransform(QtGui.QTransform().scale(self.zoom, self.zoom))

        self.view.setScene(self.scene)

    def image_display(self):
        """
        Update the image to be displayed on the DICOM View.
        """
        pixmaps = self.patient_dict_container.get("pixmaps_" + self.slice_view)
        slider_id = self.slider.value()
        image = pixmaps[slider_id]
        label = QtWidgets.QGraphicsPixmapItem(image)
        self.scene = QtWidgets.QGraphicsScene()
        self.scene.addItem(label)

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
        pen.setStyle(QtCore.Qt.PenStyle(style))
        pen.setWidthF(widthF)
        return pen

    def zoom_in(self):
        self.zoom *= 1.05
        self.update_view(zoom_change=True)

    def zoom_out(self):
        self.zoom /= 1.05
        self.update_view(zoom_change=True)
