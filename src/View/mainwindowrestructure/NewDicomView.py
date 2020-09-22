from PyQt5 import QtWidgets, QtCore, QtGui

from src.Model.PatientDictContainer import PatientDictContainer


class NewDicomView(QtWidgets.QWidget):

    def __init__(self, roi_color=None, iso_color=None):
        QtWidgets.QWidget.__init__(self)
        self.patient_dict_container = PatientDictContainer()
        self.roi_color = roi_color
        self.iso_color = iso_color
        self.pixmaps = self.patient_dict_container.get("pixmaps")
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

        self.update_view()

    def init_slider(self):
        self.slider.setMinimum(0)
        self.slider.setMaximum(len(self.pixmaps) - 1)
        self.slider.setValue(int(len(self.pixmaps) / 2))
        self.slider.setTickPosition(QtWidgets.QSlider.TicksLeft)
        self.slider.setTickInterval(1)
        self.slider.setStyleSheet("QSlider::handle:vertical:hover {background: qlineargradient(x1:0, y1:0, x2:1, "
                                  "y2:1, stop:0 #fff, stop:1 #ddd);border: 1px solid #444;border-radius: 4px;}")
        self.slider.valueChanged.connect(self.value_changed)

    def init_view(self):
        self.view.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.SmoothPixmapTransform)
        background_brush = QtGui.QBrush(QtGui.QColor(0, 0, 0), QtCore.Qt.SolidPattern)
        self.view.setBackgroundBrush(background_brush)
        self.view.setGeometry(QtCore.QRect(0, 0, 877, 517))

    def value_changed(self):
        self.update_view()

    def update_view(self, zoom_change=False):
        self.image_display()

        if zoom_change:
            self.view.setTransform(QtGui.QTransform().scale(self.zoom, self.zoom))

        # TODO display ROIs and Isodoses

        self.view.setScene(self.scene)

    def image_display(self):
        slider_id = self.slider.value()
        image = self.pixmaps[slider_id]
        image = image.scaled(512, 512, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        label = QtWidgets.QLabel()
        label.setPixmap(image)
        self.scene = QtWidgets.QGraphicsScene()
        self.scene.addWidget(label)

    def zoom_in(self):
        self.zoom *= 1.05
        self.update_view(zoom_change=True)

    def zoom_out(self):
        self.zoom /= 1.05
        self.update_view(zoom_change=True)
