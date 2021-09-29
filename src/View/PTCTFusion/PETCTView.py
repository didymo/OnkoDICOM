from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtWidgets import QRadioButton, QGridLayout, QWidget, \
    QApplication, QPushButton
from PySide6.QtGui import QPainter, QColor
from skimage import measure

from src.Model.Isodose import get_dose_grid
from src.Model.PTCTDictContainer import PTCTDictContainer
from src.Model.ROI import get_contour_pixel

from src.Controller.PathHandler import resource_path

import SimpleITK as sitk
import numpy as np


class PetCtView(QtWidgets.QWidget):

    load_pt_ct_signal = QtCore.Signal()

    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.initialised = False
        self.pet_ct_view_layout = QtWidgets.QVBoxLayout()

        self.load_pet_ct_button = QPushButton()
        self.load_pet_ct_button.setText("Start PT/CT")
        self.load_pet_ct_button.clicked.connect(self.go_to_patient)

        self.pet_ct_view_layout.addWidget(self.load_pet_ct_button)
        self.setLayout(self.pet_ct_view_layout)

    def go_to_patient(self):
        self.load_pet_ct_button.setEnabled(False)
        self.load_pt_ct_signal.emit()
        self.load_pet_ct_button.setEnabled(True)

    def load_pet_ct(self, roi_color=None, iso_color=None, slice_view="axial",
                    format_metadata=True):
        self.pt_ct_dict_container = PTCTDictContainer()
        self.iso_color = iso_color
        self.zoom = 1
        self.current_slice_number = None
        self.slice_view = slice_view
        self.overlay_view = slice_view

        self.display_metadata = False
        self.format_metadata = format_metadata

        self.dicom_view_layout = QtWidgets.QHBoxLayout()
        self.radio_button_layout = QtWidgets.QHBoxLayout()
        self.slider_layout = QtWidgets.QHBoxLayout()
        # self.radio_button_layout.setAlignment(QtCore.Qt.AlignCenter)

        # Create components
        self.slider = QtWidgets.QSlider(QtCore.Qt.Vertical)
        self.init_slider()
        self.view = QtWidgets.QGraphicsView()

        # Alpha slider
        self.alpha_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.init_alpha_slider()

        # Slider labels
        self.ct_label = QtWidgets.QLabel("CT")
        self.pt_label = QtWidgets.QLabel("PET")

        self.init_view()
        self.scene = QtWidgets.QGraphicsScene()
        # radio buttons
        self.coronal_button = QRadioButton("Coronal")
        self.coronal_button.setChecked(False)
        self.coronal_button.toggled.connect(self.update_axis)
        self.axial_button = QRadioButton("Axial")
        self.axial_button.setChecked(True)
        self.axial_button.toggled.connect(self.update_axis)
        self.sagittal_button = QRadioButton("Sagittal")
        self.sagittal_button.setChecked(False)
        self.sagittal_button.toggled.connect(self.update_axis)

        # Set layout
        self.dicom_view_layout.addWidget(self.view)
        self.dicom_view_layout.addWidget(self.slider)

        self.slider_layout.addWidget(self.ct_label)
        self.slider_layout.addWidget(self.alpha_slider)
        self.slider_layout.addWidget(self.pt_label)

        self.load_pet_ct_button.setVisible(False)
        self.pet_ct_view_layout.removeWidget(self.load_pet_ct_button)

        self.pet_ct_view_layout.addLayout(self.dicom_view_layout)
        self.pet_ct_view_layout.addLayout(self.slider_layout)
        self.pet_ct_view_layout.addLayout(self.radio_button_layout,
                                          QtCore.Qt.AlignBottom
                                          | QtCore.Qt.AlignCenter)

        self.radio_button_layout.addWidget(self.coronal_button)
        self.radio_button_layout.addWidget(self.axial_button)
        self.radio_button_layout.addWidget(self.sagittal_button)

        self.setLayout(self.pet_ct_view_layout)
        self.update_view()

        self.initialised = True

    def init_slider(self):
        """
        Create a slider for the DICOM Image View.
        """
        pixmaps = self.pt_ct_dict_container.get("ct_pixmaps_" + self.slice_view)
        self.slider.setMinimum(0)
        self.slider.setMaximum(len(pixmaps) - 1)
        self.slider.setValue(int(len(pixmaps) / 2))
        self.slider.setTickPosition(QtWidgets.QSlider.TicksLeft)
        self.slider.setTickInterval(1)
        self.slider.valueChanged.connect(self.value_changed)

    def init_alpha_slider(self):
        # alpha slider
        self.alpha_slider.setMinimum(0)
        self.alpha_slider.setMaximum(100)
        self.alpha_slider.setValue(50)
        self.alpha_slider.setTickPosition(QtWidgets.QSlider.TicksLeft)
        self.alpha_slider.setTickInterval(1)
        self.alpha_slider.valueChanged.connect(self.value_changed)

    def init_view(self):
        """
        Create a view widget for DICOM image.
        """
        self.view.setRenderHints(
            QtGui.QPainter.Antialiasing | QtGui.QPainter.SmoothPixmapTransform)
        background_brush = QtGui.QBrush(QtGui.QColor(0, 0, 0),
                                        QtCore.Qt.SolidPattern)
        self.view.setBackgroundBrush(background_brush)

    def update_axis(self):
        toggled = self.sender()
        if toggled.isChecked():
            self.slice_view = toggled.text().lower()
            pixmaps = self.pt_ct_dict_container.get(
                "ct_pixmaps_" + self.slice_view)
            self.slider.setMaximum(len(pixmaps) - 1)
            self.slider.setValue(int(len(pixmaps) / 2))

        self.update_view()

    def value_changed(self):
        self.update_view()

    def update_view(self, zoom_change=False):
        """
        Update the view of the DICOM Image.
        :param zoom_change: Boolean indicating whether the user wants to
        change the zoom. False by default.
        """
        self.image_display()

        if zoom_change:
            self.view.setTransform(
                QtGui.QTransform().scale(self.zoom, self.zoom))

        self.view.setScene(self.scene)

    def image_display(self):
        """
        Update the ct_image to be displayed on the DICOM View.
        """
        # Lead CT
        ct_pixmaps = self.pt_ct_dict_container.get("ct_pixmaps_" + self.slice_view)
        slider_id = self.slider.value()
        ct_image = ct_pixmaps[slider_id].toImage()

        # Load PT
        pt_pixmaps = self.pt_ct_dict_container.get("pt_pixmaps_" + self.slice_view)
        m = float(len(pt_pixmaps)) / len(ct_pixmaps)
        pt_image = pt_pixmaps[int(m * slider_id)].toImage()

        # Get alpha
        alpha = float(self.alpha_slider.value() / 100)

        # Merge Images
        painter = QPainter()
        painter.begin(ct_image)
        painter.setOpacity(alpha)
        painter.drawImage(0, 0, pt_image)
        painter.end()

        # Load merged images
        merged_pixmap = QtGui.QPixmap.fromImage(ct_image)
        label = QtWidgets.QGraphicsPixmapItem(merged_pixmap)
        self.scene = QtWidgets.QGraphicsScene()
        self.scene.addItem(label)

    def zoom_in(self):
        self.zoom *= 1.05
        self.update_view(zoom_change=True)

    def zoom_out(self):
        self.zoom /= 1.05
        self.update_view(zoom_change=True)
