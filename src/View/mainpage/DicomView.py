from PySide6 import QtWidgets, QtCore, QtGui

from src.View.mainpage.DicomGraphicsScene import GraphicsScene
from src.Model.PatientDictContainer import PatientDictContainer
from src.constants import INITIAL_ONE_VIEW_ZOOM
from src.Controller.PathHandler import data_path

class CustomGraphicsView(QtWidgets.QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        # self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)

    def wheelEvent(self, event: QtGui.QWheelEvent):
        modifiers = event.modifiers()
        if modifiers == QtCore.Qt.ShiftModifier:
            super().wheelEvent(event)
        elif modifiers == QtCore.Qt.AltModifier:
            super().wheelEvent(event)
        elif modifiers == QtCore.Qt.ControlModifier:
            event.ignore()
        else:
            event.ignore()

class DicomView(QtWidgets.QWidget):

    def __init__(self, roi_color=None, iso_color=None, cut_line_color=None):
        QtWidgets.QWidget.__init__(self)
        self.patient_dict_container = PatientDictContainer()
        self.iso_color = iso_color
        self.roi_color = roi_color
        self.zoom = INITIAL_ONE_VIEW_ZOOM
        self.current_slice_number = None
        self.horizontal_view = None
        self.vertical_view = None
        self.cut_lines_color = cut_line_color
        self.dicom_view_layout = QtWidgets.QHBoxLayout()
        self.windowing_slider = None

        # Create components
        self.slider = QtWidgets.QSlider(QtCore.Qt.Vertical)
        self.init_slider()
        self.view = CustomGraphicsView()
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
        self.view.setRenderHints(
            QtGui.QPainter.Antialiasing | QtGui.QPainter.SmoothPixmapTransform)
        background_brush = QtGui.QBrush(
            QtGui.QColor(0, 0, 0), QtCore.Qt.SolidPattern)
        self.view.setBackgroundBrush(background_brush)
    
    def wheelEvent(self, event: QtGui.QWheelEvent):
        degree = 8
        step = 15
        #https://doc.qt.io/qt-6/qwheelevent.html#angleDelta
        modifiers = event.modifiers()
        if modifiers == QtCore.Qt.ShiftModifier:
            super().wheelEvent(event)
        elif modifiers == QtCore.Qt.AltModifier:
            super().wheelEvent(event)
        elif modifiers == QtCore.Qt.ControlModifier:
            angle = event.angleDelta() / degree
            delta = angle.y() / step
            if delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
        else:
            num_degrees = event.angleDelta() / degree
            num_steps = num_degrees / step
            delta = int(num_steps.y())
            self.change_slice(delta)

    def change_slice(self, delta):
        current_value = self.slider.value()
        new_value = current_value + delta

        if new_value < self.slider.minimum():
            new_value = self.slider.minimum()
        elif new_value > self.slider.maximum():
            new_value = self.slider.maximum()

        self.slider.setValue(new_value)
        self.value_changed()

    def value_changed(self):
        self.update_view()
        if self.horizontal_view is not None and self.vertical_view is not None:
            self.horizontal_view.update_view()
            self.vertical_view.update_view()
        if self.windowing_slider is not None:
            self.windowing_slider.update_density_histogram()

    def update_view(self, zoom_change=False):
        """
        Update the view of the DICOM Image.
        :param zoom_change: Boolean indicating whether the user wants to change the zoom. False by default.
        """
        self.image_display()
        # Update roi colours if they are not explicitly set to None
        if self.roi_color is not None:
            self.roi_color = self.patient_dict_container.get("roi_color_dict")

        # If roi colours are set and rois are selected then update the display
        if self.roi_color and self.patient_dict_container.get("selected_rois"):
            self.roi_display()

        # If isodose colours are set and doses are selected then update the display
        if self.iso_color and self.patient_dict_container.get("selected_doses"):
            self.isodose_display()

        if zoom_change:
            self.view.setTransform(
                QtGui.QTransform().scale(self.zoom, self.zoom))

        self.view.setScene(self.scene)

    def image_display(self):
        """
        Update the image to be displayed on the DICOM View.
        """
        pixmaps = self.patient_dict_container.get("pixmaps_" + self.slice_view)
        slider_id = self.slider.value()
        image = pixmaps[slider_id]
        label = QtWidgets.QGraphicsPixmapItem(image)
        self.scene = GraphicsScene(
            label, self.horizontal_view, self.vertical_view)

    def draw_roi_polygons(self, roi_id, polygons, roi_color=None):
        """
        Draw ROI polygons on the image slice
        :param roi_id: ROI number
        :param polygons: List of ROI polygons
        :param roi_color: colors for ROIs used when displaying selected rois in
        manipulate ROI window
        """
        if roi_color is None:
            color = self.roi_color[roi_id]
        else:
            color = roi_color[roi_id]
        with open(data_path('line&fill_configuration'), 'r') as stream:
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
        pen_color = QtGui.QColor(color.red(), color.green(), color.blue())
        pen = self.get_qpen(pen_color, roi_line, line_width)
        for i in range(len(polygons)):
            self.scene.addPolygon(polygons[i], pen, QtGui.QBrush(color))

    def get_qpen(self, color, style=1, widthF=1.):
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

    def set_views(self, horizontal_view, vertical_view):
        """
        Set the views represented by the horizontal and vertical cut lines respectively
        """
        self.horizontal_view = horizontal_view
        self.vertical_view = vertical_view
        self.update_view()

    def set_slider_value(self, value):
        """
        Set the value of the slider of this view
        """
        self.slider.setValue(value*self.slider.maximum())
        self.update_view()
