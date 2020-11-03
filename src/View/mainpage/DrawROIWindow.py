import csv
import math

import numpy
import pydicom
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QIcon, QPixmap, QColor, QPen
from PyQt5.QtWidgets import QMessageBox, QHBoxLayout, QLineEdit, QSizePolicy, QPushButton, QDialog, QListWidget, \
    QGraphicsPixmapItem, QGraphicsEllipseItem, QVBoxLayout, QLabel, QWidget, QFormLayout
import alphashape
import keyboard
from shapely.geometry import MultiPolygon

from src.Controller.MainPageController import MainPageCallClass
from src.Model import ROI
from src.Model.GetPatientInfo import DicomTree
from src.Model.PatientDictContainer import PatientDictContainer


class UIDrawROIWindow:

    def setup_ui(self, draw_roi_window_instance, rois, dataset_rtss, signal_roi_drawn):

        self.patient_dict_container = PatientDictContainer()

        self.rois = rois
        self.dataset_rtss = dataset_rtss
        self.signal_roi_drawn = signal_roi_drawn

        self.current_slice = 0
        self.forward_pressed = None
        self.backward_pressed = None
        self.slider_changed = None
        self.standard_organ_names = []
        self.standard_volume_names = []
        self.standard_names = [] # Combination of organ and volume
        self.ROI_name = None  # Selected ROI name
        self.target_pixel_coords = []  # This will contain the new pixel coordinates specifed by the min and max pixel density
        self.target_pixel_coords_single_array = [] # 1D array
        self.draw_roi_window_instance = draw_roi_window_instance
        self.colour = None
        self.ds = None
        self.zoom = 1.0

        self.upper_limit = None
        self.lower_limit = None
        self.init_slider()
        self.init_view()
        self.init_metadata()
        self.init_layout()
        self.update_view()

        QtCore.QMetaObject.connectSlotsByName(draw_roi_window_instance)

    def retranslate_ui(self, draw_roi_window_instance):
        _translate = QtCore.QCoreApplication.translate
        draw_roi_window_instance.setWindowTitle(_translate("DrawRoiWindowInstance", "OnkoDICOM - Draw Region Of Interest"))
        self.roi_name_label.setText(_translate("ROINameLabel", "Region of Interest: "))
        self.roi_name_line_edit.setText(_translate("ROINameLineEdit", ""))
        self.image_slice_number_label.setText(_translate("ImageSliceNumberLabel", "Image Slice Number: "))
        self.image_slice_number_transect_button.setText(_translate("ImageSliceNumberTransectButton", "Transect"))
        self.image_slice_number_box_draw_button.setText(_translate("ImageSliceNumberBoxDrawButton", "Set Bounds"))
        self.image_slice_number_draw_button.setText(_translate("ImageSliceNumberDrawButton", "Draw"))
        self.image_slice_number_move_forward_button.setText(_translate("ImageSliceNumberMoveForwardButton", "Forward"))
        self.image_slice_number_move_backward_button.setText(
            _translate("ImageSliceNumberMoveBackwardButton", "Backward"))
        self.draw_roi_window_instance_save_button.setText(_translate("DrawRoiWindowInstanceSaveButton", "Save"))
        self.draw_roi_window_instance_cancel_button.setText(_translate("DrawRoiWindowInstanceCancelButton", "Cancel"))
        self.internal_hole_max_label.setText(_translate("InternalHoleLabel", "Maximum internal hole size (pixels): "))
        self.internal_hole_max_line_edit.setText(_translate("InternalHoleInput", "9"))
        self.isthmus_width_max_label.setText(_translate("IsthmusWidthLabel", "Maximum isthmus width size (pixels): "))
        self.isthmus_width_max_line_edit.setText(_translate("IsthmusWidthInput", "5"))
        self.min_pixel_density_label.setText(_translate("MinPixelDensityLabel", "Minimum density (pixels): "))
        self.min_pixel_density_line_edit.setText(_translate("MinPixelDensityInput", ""))
        self.max_pixel_density_label.setText(_translate("MaxPixelDensityLabel", "Maximum density (pixels): "))
        self.max_pixel_density_line_edit.setText(_translate("MaxPixelDensityInput", ""))
        self.draw_roi_window_viewport_zoom_label.setText(_translate("DrawRoiWindowViewportZoomLabel", "Zoom: "))
        self.draw_roi_window_instance_action_reset_button.setText(
            _translate("DrawRoiWindowInstanceActionClearButton", "Reset"))


    def init_view(self):
        """
        Create a view widget for DICOM image.
        """
        self.view = QtWidgets.QGraphicsView()
        # Add antialiasing and smoothing when zooming in
        self.view.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.SmoothPixmapTransform)
        background_brush = QtGui.QBrush(QtGui.QColor(0, 0, 0), QtCore.Qt.SolidPattern)
        self.view.setBackgroundBrush(background_brush)
        # Set event filter on the DICOM View area
        self.view.viewport().installEventFilter(self.draw_roi_window_instance)

    def init_layout(self):
        """
        Initialize the layout for the DICOM View tab.
        Add the view widget and the slider in the layout.
        Add the whole container 'tab2_view' as a tab in the main page.
        """

        # Initialise a DrawROIWindow
        stylesheet = open("src/res/stylesheet.qss").read()
        window_icon = QIcon()
        window_icon.addPixmap(QPixmap("src/res/images/icon.ico"), QIcon.Normal, QIcon.Off)
        self.draw_roi_window_instance.setObjectName("DrawRoiWindowInstance")
        self.draw_roi_window_instance.setWindowIcon(window_icon)

        # Creating a form box to hold all buttons and input fields
        self.draw_roi_window_input_container_box = QFormLayout()
        self.draw_roi_window_input_container_box.setObjectName("DrawRoiWindowInputContainerBox")
        self.draw_roi_window_input_container_box.setLabelAlignment(Qt.AlignLeft)


        # Create a label for denoting the ROI name
        self.roi_name_label = QLabel()
        self.roi_name_label.setObjectName("ROINameLabel")
        self.roi_name_line_edit = QLineEdit()
        # Create an input box for ROI name
        self.roi_name_line_edit.setObjectName("ROINameLineEdit")
        self.roi_name_line_edit.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.roi_name_line_edit.resize(self.roi_name_line_edit.sizeHint().width(),
                                       self.roi_name_line_edit.sizeHint().height())
        self.roi_name_line_edit.setEnabled(False)
        self.draw_roi_window_input_container_box.addRow(self.roi_name_label, self.roi_name_line_edit)


        # Create a label for denoting the Image Slice Number
        self.image_slice_number_label = QLabel()
        self.image_slice_number_label.setObjectName("ImageSliceNumberLabel")
        # Create a line edit for containing the image slice number
        self.image_slice_number_line_edit = QLineEdit()
        self.image_slice_number_line_edit.setObjectName("ImageSliceNumberLineEdit")
        self.image_slice_number_line_edit.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        self.image_slice_number_line_edit.resize(self.image_slice_number_line_edit.sizeHint().width(),
                                                 self.image_slice_number_line_edit.sizeHint().height())
        self.image_slice_number_line_edit.setEnabled(False)
        self.draw_roi_window_input_container_box.addRow(self.image_slice_number_label, self.image_slice_number_line_edit)


        # Create a horizontal box for containing the zoom function
        self.draw_roi_window_viewport_zoom_box = QHBoxLayout()
        self.draw_roi_window_viewport_zoom_box.setObjectName("DrawRoiWindowViewportZoomBox")
        # Create a label for zooming
        self.draw_roi_window_viewport_zoom_label = QLabel()
        self.draw_roi_window_viewport_zoom_label.setObjectName("DrawRoiWindowViewportZoomLabel")
        # Create an input box for zoom factor
        self.draw_roi_window_viewport_zoom_input = QLineEdit()
        self.draw_roi_window_viewport_zoom_input.setObjectName("DrawRoiWindowViewportZoomInput")
        self.draw_roi_window_viewport_zoom_input.setText("{:.2f}".format(self.zoom * 100) + "%")
        self.draw_roi_window_viewport_zoom_input.setCursorPosition(0)
        self.draw_roi_window_viewport_zoom_input.setEnabled(False)
        self.draw_roi_window_viewport_zoom_input.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.draw_roi_window_viewport_zoom_input.resize(self.draw_roi_window_viewport_zoom_input.sizeHint().width(),
                                                        self.draw_roi_window_viewport_zoom_input.sizeHint().height())
        # Create 2 buttons for zooming in and out
        # Zoom In Button
        self.draw_roi_window_viewport_zoom_in_button = QPushButton()
        self.draw_roi_window_viewport_zoom_in_button.setObjectName("DrawRoiWindowViewportZoomInButton")
        self.draw_roi_window_viewport_zoom_in_button.setSizePolicy(
            QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.draw_roi_window_viewport_zoom_in_button.resize(QSize(24, 24))
        self.draw_roi_window_viewport_zoom_in_button.setProperty("QPushButtonClass", "zoom-button")
        icon_zoom_in = QtGui.QIcon()
        icon_zoom_in.addPixmap(QtGui.QPixmap('src/res/images/btn-icons/zoom_in_icon.png'))
        self.draw_roi_window_viewport_zoom_in_button.setIcon(icon_zoom_in)
        self.draw_roi_window_viewport_zoom_in_button.clicked.connect(self.on_zoom_in_clicked)
        # Zoom Out Button
        self.draw_roi_window_viewport_zoom_out_button = QPushButton()
        self.draw_roi_window_viewport_zoom_out_button.setObjectName("DrawRoiWindowViewportZoomOutButton")
        self.draw_roi_window_viewport_zoom_out_button.setSizePolicy(
            QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.draw_roi_window_viewport_zoom_out_button.resize(QSize(24, 24))
        self.draw_roi_window_viewport_zoom_out_button.setProperty("QPushButtonClass", "zoom-button")
        icon_zoom_out = QtGui.QIcon()
        icon_zoom_out.addPixmap(QtGui.QPixmap('src/res/images/btn-icons/zoom_out_icon.png'))
        self.draw_roi_window_viewport_zoom_out_button.setIcon(icon_zoom_out)
        self.draw_roi_window_viewport_zoom_out_button.clicked.connect(self.on_zoom_out_clicked)
        self.draw_roi_window_viewport_zoom_box.addWidget(self.draw_roi_window_viewport_zoom_label)
        self.draw_roi_window_viewport_zoom_box.addWidget(self.draw_roi_window_viewport_zoom_input)
        self.draw_roi_window_viewport_zoom_box.addWidget(self.draw_roi_window_viewport_zoom_out_button)
        self.draw_roi_window_viewport_zoom_box.addWidget(self.draw_roi_window_viewport_zoom_in_button)
        self.draw_roi_window_input_container_box.addRow(self.draw_roi_window_viewport_zoom_box)


        # Create a horizontal box for forward and backward button
        self.draw_roi_window_backward_forward_box = QHBoxLayout()
        self.draw_roi_window_backward_forward_box.setObjectName("DrawRoiWindowBackwardForwardBox")
        # Create a button to move backward to the previous image
        self.image_slice_number_move_backward_button = QPushButton()
        self.image_slice_number_move_backward_button.setObjectName("ImageSliceNumberMoveBackwardButton")
        self.image_slice_number_move_backward_button.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum))
        self.image_slice_number_move_backward_button.resize(
            self.image_slice_number_move_backward_button.sizeHint().width(),
            self.image_slice_number_move_backward_button.sizeHint().height())
        self.image_slice_number_move_backward_button.clicked.connect(self.on_backward_clicked)
        icon_move_backward = QtGui.QIcon()
        icon_move_backward.addPixmap(QtGui.QPixmap('src/res/images/btn-icons/backward_slide_icon.png'))
        self.image_slice_number_move_backward_button.setIcon(icon_move_backward)
        self.draw_roi_window_backward_forward_box.addWidget(self.image_slice_number_move_backward_button)
        # Create a button to move forward to the next image
        self.image_slice_number_move_forward_button = QPushButton()
        self.image_slice_number_move_forward_button.setObjectName("ImageSliceNumberMoveForwardButton")
        self.image_slice_number_move_forward_button.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum))
        self.image_slice_number_move_forward_button.resize(
            self.image_slice_number_move_forward_button.sizeHint().width(),
            self.image_slice_number_move_forward_button.sizeHint().height())
        self.image_slice_number_move_forward_button.clicked.connect(self.on_forward_clicked)
        icon_move_forward = QtGui.QIcon()
        icon_move_forward.addPixmap(QtGui.QPixmap('src/res/images/btn-icons/forward_slide_icon.png'))
        self.image_slice_number_move_forward_button.setIcon(icon_move_forward)
        self.draw_roi_window_backward_forward_box.addWidget(self.image_slice_number_move_forward_button)
        self.draw_roi_window_input_container_box.addRow(self.draw_roi_window_backward_forward_box)


        # Create a horizontal box for transect and draw button
        self.draw_roi_window_transect_draw_box = QHBoxLayout()
        self.draw_roi_window_transect_draw_box.setObjectName("DrawRoiWindowTransectDrawBox")
        # Create a transect button
        self.image_slice_number_transect_button = QPushButton()
        self.image_slice_number_transect_button.setObjectName("ImageSliceNumberTransectButton")
        self.image_slice_number_transect_button.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum))
        self.image_slice_number_transect_button.resize(
            self.image_slice_number_transect_button.sizeHint().width(),
            self.image_slice_number_transect_button.sizeHint().height())
        self.image_slice_number_transect_button.clicked.connect(self.transect_handler)
        icon_transect = QtGui.QIcon()
        icon_transect.addPixmap(QtGui.QPixmap('src/res/images/btn-icons/transect_icon.png'))
        self.image_slice_number_transect_button.setIcon(icon_transect)
        self.draw_roi_window_transect_draw_box.addWidget(self.image_slice_number_transect_button)
        # Create a bounding box button
        self.image_slice_number_box_draw_button = QPushButton()
        self.image_slice_number_box_draw_button.setObjectName("ImageSliceNumberBoxDrawButton")
        self.image_slice_number_box_draw_button.setSizePolicy(
            QSizePolicy.MinimumExpanding, QSizePolicy.Minimum
        )
        self.image_slice_number_box_draw_button.resize(
            self.image_slice_number_box_draw_button.sizeHint().width(),
            self.image_slice_number_box_draw_button.sizeHint().height()
        )
        self.image_slice_number_box_draw_button.clicked.connect(self.on_box_draw_clicked)
        icon_box_draw = QtGui.QIcon()
        icon_box_draw.addPixmap(QtGui.QPixmap('src/res/images/btn-icons/draw_bound_icon.png'))
        self.image_slice_number_box_draw_button.setIcon(icon_box_draw)
        self.draw_roi_window_transect_draw_box.addWidget(self.image_slice_number_box_draw_button)
        # Create a draw button
        self.image_slice_number_draw_button = QPushButton()
        self.image_slice_number_draw_button.setObjectName("ImageSliceNumberDrawButton")
        self.image_slice_number_draw_button.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum))
        self.image_slice_number_draw_button.resize(
            self.image_slice_number_draw_button.sizeHint().width(),
            self.image_slice_number_draw_button.sizeHint().height())
        self.image_slice_number_draw_button.clicked.connect(self.on_draw_clicked)
        icon_draw = QtGui.QIcon()
        icon_draw.addPixmap(QtGui.QPixmap('src/res/images/btn-icons/draw_icon.png'))
        self.image_slice_number_draw_button.setIcon(icon_draw)
        self.draw_roi_window_transect_draw_box.addWidget(self.image_slice_number_draw_button)
        self.draw_roi_window_input_container_box.addRow(self.draw_roi_window_transect_draw_box)

        # Create a contour preview button and alpha selection input
        self.row_preview_layout = QtWidgets.QHBoxLayout()
        self.button_contour_preview = QtWidgets.QPushButton("Preview contour")
        self.button_contour_preview.clicked.connect(self.on_preview_clicked)
        self.label_alpha_value = QtWidgets.QLabel("Alpha value:")
        self.input_alpha_value = QtWidgets.QLineEdit("0.2")
        self.row_preview_layout.addWidget(self.button_contour_preview)
        self.row_preview_layout.addWidget(self.label_alpha_value)
        self.row_preview_layout.addWidget(self.input_alpha_value)
        self.draw_roi_window_input_container_box.addRow(self.row_preview_layout)
        icon_preview = QtGui.QIcon()
        icon_preview.addPixmap(QtGui.QPixmap('src/res/images/btn-icons/preview_icon.png'))
        self.button_contour_preview.setIcon(icon_preview)

        # Create a label for denoting the max internal hole size
        self.internal_hole_max_label = QLabel()
        self.internal_hole_max_label.setObjectName("InternalHoleLabel")
        # Create input for max internal hole size
        self.internal_hole_max_line_edit = QLineEdit()
        self.internal_hole_max_line_edit.setObjectName("InternalHoleInput")
        self.internal_hole_max_line_edit.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        self.internal_hole_max_line_edit.resize(self.internal_hole_max_line_edit.sizeHint().width(),
                                                self.internal_hole_max_line_edit.sizeHint().height())
        self.draw_roi_window_input_container_box.addRow(self.internal_hole_max_label, self.internal_hole_max_line_edit)


        # Create a label for denoting the isthmus width size
        self.isthmus_width_max_label = QLabel()
        self.isthmus_width_max_label.setObjectName("IsthmusWidthLabel")
        # Create input for max isthmus width size
        self.isthmus_width_max_line_edit = QLineEdit()
        self.isthmus_width_max_line_edit.setObjectName("IsthmusWidthInput")
        self.isthmus_width_max_line_edit.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        self.isthmus_width_max_line_edit.resize(self.isthmus_width_max_line_edit.sizeHint().width(),
                                                self.isthmus_width_max_line_edit.sizeHint().height())
        self.draw_roi_window_input_container_box.addRow(self.isthmus_width_max_label, self.isthmus_width_max_line_edit)


        # Create a label for denoting the minimum pixel density
        self.min_pixel_density_label = QLabel()
        self.min_pixel_density_label.setObjectName("MinPixelDensityLabel")
        # Create input for min pixel size
        self.min_pixel_density_line_edit = QLineEdit()
        self.min_pixel_density_line_edit.setObjectName("MinPixelDensityInput")
        self.min_pixel_density_line_edit.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        self.min_pixel_density_line_edit.resize(self.min_pixel_density_line_edit.sizeHint().width(),
                                                self.min_pixel_density_line_edit.sizeHint().height())
        self.draw_roi_window_input_container_box.addRow(self.min_pixel_density_label, self.min_pixel_density_line_edit)


        # Create a label for denoting the minimum pixel density
        self.max_pixel_density_label = QLabel()
        self.max_pixel_density_label.setObjectName("MaxPixelDensityLabel")
        # Create input for min pixel size
        self.max_pixel_density_line_edit = QLineEdit()
        self.max_pixel_density_line_edit.setObjectName("MaxPixelDensityInput")
        self.max_pixel_density_line_edit.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        self.max_pixel_density_line_edit.resize(self.max_pixel_density_line_edit.sizeHint().width(),
                                                self.max_pixel_density_line_edit.sizeHint().height())
        self.draw_roi_window_input_container_box.addRow(self.max_pixel_density_label, self.max_pixel_density_line_edit)


        # Create a button to clear the draw
        self.draw_roi_window_instance_action_reset_button = QPushButton()
        self.draw_roi_window_instance_action_reset_button.setObjectName("DrawRoiWindowInstanceActionClearButton")
        self.draw_roi_window_instance_action_reset_button.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum))
        self.draw_roi_window_instance_action_reset_button.resize(
            self.draw_roi_window_instance_action_reset_button.sizeHint().width(),
            self.draw_roi_window_instance_action_reset_button.sizeHint().height())
        self.draw_roi_window_instance_action_reset_button.clicked.connect(self.on_reset_clicked)
        self.draw_roi_window_instance_action_reset_button.setProperty("QPushButtonClass", "fail-button")
        icon_clear_roi_draw = QtGui.QIcon()
        icon_clear_roi_draw.addPixmap(QtGui.QPixmap('src/res/images/btn-icons/reset_roi_draw_icon.png'))
        self.draw_roi_window_instance_action_reset_button.setIcon(icon_clear_roi_draw)
        self.draw_roi_window_input_container_box.addRow(self.draw_roi_window_instance_action_reset_button)


        # Create a horizontal box for saving and cancel the drawing
        self.draw_roi_window_cancel_save_box = QHBoxLayout()
        self.draw_roi_window_cancel_save_box.setObjectName("DrawRoiWindowCancelSaveBox")
        # Create an exit button to cancel the drawing
        # Add a button to go back/exit from the application
        self.draw_roi_window_instance_cancel_button = QPushButton()
        self.draw_roi_window_instance_cancel_button.setObjectName("DrawRoiWindowInstanceCancelButton")
        self.draw_roi_window_instance_cancel_button.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum))
        self.draw_roi_window_instance_cancel_button.resize(self.draw_roi_window_instance_cancel_button.sizeHint().width(),
                                                    self.draw_roi_window_instance_cancel_button.sizeHint().height())
        self.draw_roi_window_instance_cancel_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.draw_roi_window_instance_cancel_button.clicked.connect(self.on_cancel_button_clicked)
        self.draw_roi_window_instance_cancel_button.setProperty("QPushButtonClass", "fail-button")
        icon_cancel = QtGui.QIcon()
        icon_cancel.addPixmap(QtGui.QPixmap('src/res/images/btn-icons/cancel_icon.png'))
        self.draw_roi_window_instance_cancel_button.setIcon(icon_cancel)
        self.draw_roi_window_cancel_save_box.addWidget(self.draw_roi_window_instance_cancel_button)
        # Create a save button to save all the changes
        self.draw_roi_window_instance_save_button = QPushButton()
        self.draw_roi_window_instance_save_button.setObjectName("DrawRoiWindowInstanceSaveButton")
        self.draw_roi_window_instance_save_button.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum))
        self.draw_roi_window_instance_save_button.resize(
            self.draw_roi_window_instance_save_button.sizeHint().width(),
            self.draw_roi_window_instance_save_button.sizeHint().height())
        self.draw_roi_window_instance_save_button.setProperty("QPushButtonClass", "success-button")
        icon_save = QtGui.QIcon()
        icon_save.addPixmap(QtGui.QPixmap('src/res/images/btn-icons/save_icon.png'))
        self.draw_roi_window_instance_save_button.setIcon(icon_save)
        self.draw_roi_window_instance_save_button.clicked.connect(self.on_save_clicked)
        self.draw_roi_window_cancel_save_box.addWidget(self.draw_roi_window_instance_save_button)
        self.draw_roi_window_input_container_box.addRow(self.draw_roi_window_cancel_save_box)


        # Creating a horizontal box to hold the ROI view and slider
        self.draw_roi_window_instance_view_box = QHBoxLayout()
        self.draw_roi_window_instance_view_box.setObjectName("DrawRoiWindowInstanceViewBox")
        # Add View and Slider into horizontal box
        self.slider.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.MinimumExpanding)
        self.slider.resize(self.slider.sizeHint().width(), self.slider.sizeHint().height())
        self.draw_roi_window_instance_view_box.addWidget(self.view)
        self.draw_roi_window_instance_view_box.addWidget(self.slider)
        # Create a widget to hold the image slice box
        self.draw_roi_window_instance_view_widget = QWidget()
        self.draw_roi_window_instance_view_widget.setObjectName(
            "DrawRoiWindowInstanceActionWidget")
        self.draw_roi_window_instance_view_widget.setLayout(
            self.draw_roi_window_instance_view_box)


        # Create a horizontal box for containing the input fields and the viewport
        self.draw_roi_window_main_box = QHBoxLayout()
        self.draw_roi_window_main_box.setObjectName("DrawRoiWindowMainBox")
        self.draw_roi_window_main_box.addLayout(self.draw_roi_window_input_container_box, 1)
        self.draw_roi_window_main_box.addWidget(self.draw_roi_window_instance_view_widget, 11)


        # Create a new central widget to hold the vertical box layout
        self.draw_roi_window_instance_central_widget = QWidget()
        self.draw_roi_window_instance_central_widget.setObjectName("DrawRoiWindowInstanceCentralWidget")
        self.draw_roi_window_instance_central_widget.setLayout(self.draw_roi_window_main_box)

        self.retranslate_ui(self.draw_roi_window_instance)
        self.draw_roi_window_instance.setStyleSheet(stylesheet)
        self.draw_roi_window_instance.setCentralWidget(self.draw_roi_window_instance_central_widget)
        QtCore.QMetaObject.connectSlotsByName(self.draw_roi_window_instance)

    def init_slider(self):
        """
        Create a slider for the DICOM Image View.
        """
        pixmaps = self.patient_dict_container.get("pixmaps")
        self.slider = QtWidgets.QSlider(QtCore.Qt.Vertical)
        self.slider.setMinimum(0)
        self.slider.setMaximum(len(pixmaps) - 1)
        self.slider.setValue(int(len(pixmaps) / 2))
        self.slider.setTickPosition(QtWidgets.QSlider.TicksLeft)
        self.slider.setTickInterval(1)
        self.slider.setStyleSheet("QSlider::handle:vertical:hover {background: qlineargradient(x1:0, y1:0, x2:1, "
                                  "y2:1, stop:0 #fff, stop:1 #ddd);border: 1px solid #444;border-radius: 4px;}")
        self.slider.valueChanged.connect(self.value_changed)
        self.slider.setGeometry(QtCore.QRect(0, 0, 50, 1000))
        self.slider.setFocusPolicy(QtCore.Qt.NoFocus)

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

    def on_zoom_in_clicked(self):
        """
        This function is used for zooming in button
        """
        self.zoom *= 1.05
        self.update_view(zoomChange=True)
        self.draw_roi_window_viewport_zoom_input.setText("{:.2f}".format(self.zoom * 100) + "%")
        self.draw_roi_window_viewport_zoom_input.setCursorPosition(0)

    def on_zoom_out_clicked(self):
        """
        This function is used for zooming out button
        """
        self.zoom /= 1.05
        self.update_view(zoomChange=True)
        self.draw_roi_window_viewport_zoom_input.setText("{:.2f}".format(self.zoom * 100) + "%")
        self.draw_roi_window_viewport_zoom_input.setCursorPosition(0)

    def on_cancel_button_clicked(self):
        """
        This function is used for canceling the drawing

        """
        self.close()

    def value_changed(self):
        """
        Function triggered when the value of the slider has changed.
        Update the view.
        """
        self.forward_pressed = False
        self.backward_pressed = False
        self.slider_changed = True
        self.update_view()

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

        if zoomChange:
            self.view.setTransform(QtGui.QTransform().scale(self.zoom, self.zoom))

        if self.upper_limit and self.lower_limit:
            self.min_pixel_density_line_edit.setText(str(self.lower_limit))
            self.max_pixel_density_line_edit.setText(str(self.upper_limit))

        if eventChangedWindow:
            self.image_display(eventChangedWindow=True)
        else:
            self.image_display()

        self.update_metadata()
        self.view.setScene(self.scene)

    def image_display(self, eventChangedWindow=False):
        """
        Update the image to be displayed on the DICOM View.

        :param eventChangedWindow:
         Boolean indicating if the user is altering the window and level values through mouse movement and button press
         events in the DICOM View area.
         False by default.
        """

        slider_id = self.slider.value()
        if (self.forward_pressed):
            slider_id = self.current_slice
        if (self.backward_pressed):
            slider_id = self.current_slice
        if (self.slider_changed):
            slider_id = self.slider.value()

        # PyQt5.QtGui.QPixMap objects
        pixmaps = self.patient_dict_container.get("pixmaps")
        image = pixmaps[slider_id]
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

        # Getting most updated selected slice
        id = self.slider.value()
        if (self.forward_pressed):
            id = self.current_slice
        elif (self.backward_pressed):
            id = self.current_slice
        elif (self.slider_changed):
            id = self.slider.value()

        filename = self.patient_dict_container.filepaths[id]
        dicomtree_slice = DicomTree(filename)
        dict_slice = dicomtree_slice.dict

        # Information to display
        pixmaps = self.patient_dict_container.get("pixmaps")
        current_slice = dict_slice['Instance Number'][0]
        total_slices = len(pixmaps)
        row_img = dict_slice['Rows'][0]
        col_img = dict_slice['Columns'][0]
        patient_pos = dict_slice['Patient Position'][0]
        window = self.patient_dict_container.get("window")
        level = self.patient_dict_container.get("level")
        try:
            slice_pos = dict_slice['Slice Location'][0]
        except:
            imagePosPatient = dict_slice['Image Position (Patient)']
            # logging.error('Image Position (Patient):' + str(imagePosPatient))
            imagePosPatientCoordinates = imagePosPatient[0]
            # logging.error('Image Position (Patient) coordinates :' + str(imagePosPatientCoordinates))
            slice_pos = imagePosPatientCoordinates[2]

        self.text_imageID.setText(_translate("MainWindow", "Image: " + str(current_slice) + " / " + str(total_slices)))
        self.text_imagePos.setText(_translate("MainWindow", "Position: " + str(slice_pos) + " mm"))
        self.text_WL.setText(_translate("MainWindow", "W/L: " + str(window) + "/" + str(level)))
        self.text_imageSize.setText(_translate("MainWindow", "Image Size: " + str(row_img) + "x" + str(col_img) + "px"))
        self.text_zoom.setText(_translate("MainWindow", "Zoom: " + "{:.2f}".format(self.zoom * 100) + "%"))
        self.text_patientPos.setText(_translate("MainWindow", "Patient Position: " + patient_pos))
        self.image_slice_number_line_edit.setText(_translate("ImageSliceNumberLineEdit", str(current_slice)))

    def on_backward_clicked(self):
        self.backward_pressed = True
        self.forward_pressed = False
        self.slider_changed = False

        image_slice_number = self.image_slice_number_line_edit.text()

        # Backward will only execute if current image slice is above 1.
        if int(image_slice_number) > 1:
            self.current_slice = int(image_slice_number)

            # decrements slice by 1
            self.current_slice = self.current_slice - 2

            # Update slider to move to correct position
            self.slider.setValue(self.current_slice)

            self.update_view()

    def on_forward_clicked(self):
        pixmaps = self.patient_dict_container.get("pixmaps")
        total_slices = len(pixmaps)

        self.backward_pressed = False
        self.forward_pressed = True
        self.slider_changed = False

        image_slice_number = self.image_slice_number_line_edit.text()

        # Forward will only execute if current image slice is below the total number of slices.
        if int(image_slice_number) < total_slices:
            # increments slice by 1
            self.current_slice = int(image_slice_number)

            # Update slider to move to correct position
            self.slider.setValue(self.current_slice)

            self.update_view()

    def on_reset_clicked(self):
        self.image_display()
        self.update_view()
        self.isthmus_width_max_line_edit.setText("5")
        self.internal_hole_max_line_edit.setText("9")
        self.min_pixel_density_line_edit.setText("")
        self.max_pixel_density_line_edit.setText("")
        if hasattr(self, 'bounds_box_draw'):
            delattr(self, 'bounds_box_draw')

    def transect_handler(self):
        """
        Function triggered when the Transect button is pressed from the menu.
        """

        pixmaps = self.patient_dict_container.get("pixmaps")
        id = self.slider.value()

        # Getting most updated selected slice
        if (self.forward_pressed):
            id = self.current_slice
        elif (self.backward_pressed):
            id = self.current_slice
        elif (self.slider_changed):
            id = self.slider.value()

        dt = self.patient_dict_container.dataset[id]
        rowS = dt.PixelSpacing[0]
        colS = dt.PixelSpacing[1]
        dt.convert_pixel_data()
        MainPageCallClass().runTransect(
            self.draw_roi_window_instance,
            self.view,
            pixmaps[id],
            dt._pixel_array.transpose(),
            rowS,
            colS,
            isROIDraw=True,
        )

    def on_draw_clicked(self):
        """
        Function triggered when the Draw button is pressed from the menu.
        """
        pixmaps = self.patient_dict_container.get("pixmaps")

        if self.min_pixel_density_line_edit.text() == "" or self.max_pixel_density_line_edit.text() == "":
            QMessageBox.about(self.draw_roi_window_instance, "Not Enough Data",
                              "Not all values are specified or correct.")
        else:
            id = self.slider.value()

            # Getting most updated selected slice
            if (self.forward_pressed):
                id = self.current_slice
            elif (self.backward_pressed):
                id = self.current_slice
            elif (self.slider_changed):
                id = self.slider.value()

            dt = self.patient_dict_container.dataset[id]
            dt.convert_pixel_data()

            # Path to the selected .dcm file
            location = self.patient_dict_container.filepaths[id]
            self.ds = pydicom.dcmread(location)

            min_pixel = self.min_pixel_density_line_edit.text()
            max_pixel = self.max_pixel_density_line_edit.text()

            # If they are number inputs
            if min_pixel.isdecimal() and max_pixel.isdecimal():

                min_pixel = int(min_pixel)
                max_pixel = int(max_pixel)

                if min_pixel >= max_pixel:
                    QMessageBox.about(self.draw_roi_window_instance, "Incorrect Input",
                                      "Please ensure maximum density is atleast higher than minimum density.")

                self.drawingROI = Drawing(
                    pixmaps[id],
                    dt._pixel_array.transpose(),
                    min_pixel,
                    max_pixel,
                    self.patient_dict_container.dataset[id],
                    self.draw_roi_window_instance
                )
                self.view.setScene(self.drawingROI)

            else:
                QMessageBox.about(self.draw_roi_window_instance, "Not Enough Data", "Not all values are specified or correct.")

    def on_box_draw_clicked(self):
        id = self.slider.value()
        dt = self.patient_dict_container.dataset[id]
        dt.convert_pixel_data()
        pixmaps = self.patient_dict_container.get("pixmaps")

        self.bounds_box_draw = DrawBoundingBox(pixmaps[id], dt)
        self.view.setScene(self.bounds_box_draw)

    def on_save_clicked(self):
        # Make sure the user has clicked Draw first
        if self.ds is not None:
            # Because the contour data needs to be a list of points that form a polygon, the list of pixel points need
            # to be converted to a concave hull.
            pixel_hull = self.calculate_concave_hull_of_points()
            if pixel_hull is not None:
                hull = self.convert_hull_to_rcs(pixel_hull)
                single_array = []
                for sublist in hull:
                    for item in sublist:
                        single_array.append(item)
                new_rtss = ROI.create_roi(self.dataset_rtss, self.ROI_name, single_array, self.ds)
                self.signal_roi_drawn.emit((new_rtss, {"draw": self.ROI_name}))
                QMessageBox.about(self.draw_roi_window_instance, "Warning",
                                  "This feature is still in development. The ROI will appear in your structures tab,"
                                                                        " but may demonstrate some technical issues "
                                                                        "when performing tasks.")
                self.close()
            else:
                QMessageBox.about(self.draw_roi_window_instance, "Multipolygon detected",
                                  "Selected points will generate multiple contours, which is not currently supported. "
                                  "If the region you are drawing is not meant to generate multiple contours, please "
                                  "ajust your selected alpha value.")
        else:
            QMessageBox.about(self.draw_roi_window_instance, "Not Enough Data",
                              "Please ensure you have drawn your ROI first.")

    def calculate_concave_hull_of_points(self):
        # Get all the pixels in the drawing window's list of highlighted pixels, excluding the removed pixels.
        target_pixel_coords = [(item[0], item[1]) for item in self.drawingROI.target_pixel_coords]

        # Calculate the concave hull of the points.
        #alpha = 0.95 * alphashape.optimizealpha(points)
        alpha = float(self.input_alpha_value.text())
        hull = alphashape.alphashape(target_pixel_coords, alpha)
        if isinstance(hull, MultiPolygon):
            return None

        hull_xy = hull.exterior.coords.xy

        points = []
        for i in range(len(hull_xy[0])):
            points.append([int(hull_xy[0][i]), int(hull_xy[1][i])])

        return points

    def convert_hull_to_rcs(self, hull_pts):
        slider_id = self.slider.value()
        dataset = self.patient_dict_container.dataset[slider_id]
        pixlut = self.patient_dict_container.get("pixluts")[dataset.SOPInstanceUID]
        z_coord = dataset.SliceLocation
        points = []

        # Convert the pixels to an RCS location and move them to a list of points.
        for i, item in enumerate(hull_pts):
            points.append(ROI.pixel_to_rcs(pixlut, item[0], item[1]))

        contour_data = []
        for p in points:
            coords = (p[0], p[1], z_coord)
            contour_data.append(coords)

        return contour_data

    def on_preview_clicked(self):
        if hasattr(self, 'drawingROI'):
            pass  # display contour on image
        else:
            QMessageBox.about(self.draw_roi_window_instance, "Not Enough Data",
                              "Please ensure you have drawn your ROI first.")

    def set_selected_roi_name(self, roi_name):

        roi_exists = False

        patient_dict_container = PatientDictContainer()
        existing_rois = patient_dict_container.get("rois")
        number_of_rois = len(existing_rois)

        # Check to see if the ROI already exists
        for key, value in existing_rois.items():
            if roi_name in value['name']:
                roi_exists = True

        if roi_exists:
            QMessageBox.about(self.draw_roi_window_instance, "ROI already exists in RTSS",
                              "Would you like to continue?")

        self.ROI_name = roi_name
        self.roi_name_line_edit.setText(self.ROI_name)


#####################################################################################################################
#                                                                                                                   #
#  This Class handles the ROI Pop Up functionalities                                                                    #
#                                                                                                                   #
#####################################################################################################################
class SelectROIPopUp(QDialog):
    signal_roi_name = QtCore.pyqtSignal(str)

    def __init__(self):
        QDialog.__init__(self)

        stylesheet = open("src/res/stylesheet.qss").read()
        self.setStyleSheet(stylesheet)
        self.standard_names = []
        self.init_standard_names()

        self.setWindowTitle("Select A Region of Interest To Draw")
        self.setMinimumSize(350, 180)

        self.icon = QtGui.QIcon()
        self.icon.addPixmap(QtGui.QPixmap("src/res/images/icon.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(self.icon)

        self.explanation_text = QLabel("Search for ROI:")

        self.input_field = QLineEdit()
        self.input_field.textChanged.connect(self.on_text_edited)

        self.button_area = QWidget()
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.on_cancel_clicked)
        self.begin_draw_button = QPushButton("Begin Draw Process")

        self.begin_draw_button.clicked.connect(self.on_begin_clicked)

        self.button_layout = QHBoxLayout()
        self.button_layout.addWidget(self.cancel_button)
        self.button_layout.addWidget(self.begin_draw_button)
        self.button_area.setLayout(self.button_layout)

        self.list_label = QLabel()
        self.list_label.setText("Select a Standard Region of Interest")

        self.list_of_ROIs = QListWidget()
        for standard_name in self.standard_names:
            self.list_of_ROIs.addItem(standard_name)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.explanation_text)
        self.layout.addWidget(self.input_field)
        self.layout.addWidget(self.list_label)
        self.layout.addWidget(self.list_of_ROIs)
        self.layout.addWidget(self.button_area)
        self.setLayout(self.layout)

        self.list_of_ROIs.clicked.connect(self.on_roi_clicked)

    def init_standard_names(self):
        """
        Create two lists containing standard organ and standard volume names as set by the Add-On options.
        """
        with open('src/data/csv/organName.csv', 'r') as f:
            standard_organ_names = []

            csv_input = csv.reader(f)
            header = next(f)  # Ignore the "header" of the column
            for row in csv_input:
                standard_organ_names.append(row[0])

        with open('src/data/csv/volumeName.csv', 'r') as f:
            standard_volume_names = []

            csv_input = csv.reader(f)
            header = next(f)  # Ignore the "header" of the column
            for row in csv_input:
                standard_volume_names.append(row[1])

        self.standard_names = standard_organ_names + standard_volume_names

    def on_text_edited(self, text):
        self.list_of_ROIs.clear()
        text_upper_case = text.upper()
        for item in self.standard_names:
            if item.startswith(text) or item.startswith(text_upper_case):
                self.list_of_ROIs.addItem(item)

    def on_roi_clicked(self):
        self.begin_draw_button.setEnabled(True)
        self.begin_draw_button.setFocus()

    def on_begin_clicked(self):
        # If there is a ROI Selected
        if self.list_of_ROIs.currentItem() != None:
            roi = self.list_of_ROIs.currentItem()
            self.roi_name = str(roi.text())

            # Call function on UIDrawWindow so it has selected ROI
            self.signal_roi_name.emit(self.roi_name)
            self.close()

    def on_cancel_clicked(self):
        self.close()


#####################################################################################################################
#                                                                                                                   #
#  This Class handles the Drawing functionality                                                                    #
#                                                                                                                   #
#####################################################################################################################
class Drawing(QtWidgets.QGraphicsScene):

    # Initialisation function  of the class
    def __init__(self, imagetoPaint, pixmapdata, min_pixel, max_pixel, dataset, draw_roi_window_instance):
        super(Drawing, self).__init__()

        #create the canvas to draw the line on and all its necessary components
        self.draw_roi_window_instance = draw_roi_window_instance
        self.min_pixel = min_pixel
        self.max_pixel = max_pixel
        self.addItem(QGraphicsPixmapItem(imagetoPaint))
        self.img = imagetoPaint
        self.data = pixmapdata
        self.values = []
        self.getValues()
        self.rect = QtCore.QRect(250, 300, 20, 20)
        self.update()
        self._points = {}
        self._circlePoints = []
        self.drag_position = QtCore.QPoint()
        self.cursor = None
        self.isPressed = False
        self.dataset = dataset
        self.pixel_array = None
        # This will contain the new pixel coordinates specifed by the min and max pixel density
        self.target_pixel_coords = []
        self.accordingColorList = []
        self.q_image = None
        self.q_pixmaps = None
        self.label = QtWidgets.QLabel()
        self.draw_tool_radius = 19
        self._display_pixel_color()

    def _display_pixel_color(self):
        """
        Creates the initial list of pixel values within the given minimum and maximum densities, then displays them
        on the view.
        """
        if self.min_pixel <= self.max_pixel:
            data_set = self.dataset
            if hasattr(self.draw_roi_window_instance, 'bounds_box_draw'):
                min_x = int(self.draw_roi_window_instance.bounds_box_draw.box.rect().x())
                min_y = int(self.draw_roi_window_instance.bounds_box_draw.box.rect().y())
                max_x = int(self.draw_roi_window_instance.bounds_box_draw.box.rect().width() + min_x)
                max_y = int(self.draw_roi_window_instance.bounds_box_draw.box.rect().height() + min_y)
            else:
                min_x = 0
                min_y = 0
                max_x = data_set.Rows
                max_y = data_set.Columns

            """
            pixel_array is a 2-Dimensional array containing all pixel coordinates of the q_image. 
            pixel_array[x][y] will return the density of the pixel
            """
            self.pixel_array = data_set._pixel_array
            self.q_image = self.img.toImage()
            for x_coord in range(min_y, max_y):
                for y_coord in range(min_x, max_x):
                    if (self.pixel_array[x_coord][y_coord] >= self.min_pixel) and (
                            self.pixel_array[x_coord][y_coord] <= self.max_pixel):
                        self.target_pixel_coords.append((y_coord, x_coord))

            """
            For the meantime, a new image is created and the pixels specified are coloured. 
            This will need to altered so that it creates a new layer over the existing image instead of replacing it.
            """
            # Convert QPixMap into Qimage
            for x_coord, y_coord in self.target_pixel_coords:
                c = self.q_image.pixel(x_coord, y_coord)
                colors = QColor(c).getRgbF()
                self.accordingColorList.append((x_coord, y_coord, colors))

            for x_coord, y_coord, colors in self.accordingColorList:
                self.q_image.setPixelColor(x_coord, y_coord, QColor(QtGui.QRgba64.fromRgba(90, 250, 175, 200)))

            # Convert Qimage back to QPixMap
            self.q_pixmaps = QtGui.QPixmap.fromImage(self.q_image)
            self.label.setPixmap(self.q_pixmaps)
            self.addWidget(self.label)

    def _find_neighbor_point(self, event):
        """
        Find point around mouse position. This function is for if we want to choose and drag the circle
        :rtype: ((int, int)|None)
        :return: (x, y) if there are any point around mouse else None
        """
        distance_threshold = 3.0
        nearest_point = None
        min_distance = math.sqrt(2 * (100 ** 2))
        for x, y in self._points.items():
            distance = math.hypot(event.xdata - x, event.ydata - y)
            if distance < min_distance:
                min_distance = distance
                nearest_point = (x, y)
        if min_distance < distance_threshold:
            return nearest_point
        return None

    def getValues(self):
        """
        This function gets the corresponding values of all the points in the drawn line from the dataset.
        """
        for i in range(512):
            for j in range(512):
                self.values.append(self.data[i][j])

    def remove_pixels_within_circle(self, clicked_x, clicked_y):
        """
        Removes all highlighted pixels within the selected circle and updates the image.
        """
        # Calculate euclidean distance between each highlighted point and the clicked point. If the distance is less
        # than the radius, remove it from the highlighted pixels.
        for x, y, colors in self.accordingColorList[:]:
            clicked_point = numpy.array((clicked_x, clicked_y))
            point_to_check = numpy.array((x, y))
            distance = numpy.linalg.norm(clicked_point - point_to_check)
            if distance <= self.draw_tool_radius:
                self.q_image.setPixelColor(x, y, QColor.fromRgbF(colors[0], colors[1], colors[2], colors[3]))
                self.target_pixel_coords.remove((x, y))
                self.accordingColorList.remove((x, y, colors))

        self.q_pixmaps = QtGui.QPixmap.fromImage(self.q_image)
        self.label.setPixmap(self.q_pixmaps)
        self.addWidget(self.label)

    def draw_cursor(self, event_x, event_y, new_circle=False):
        """
        Draws a blue circle where the user clicked.
        :param event_x: QGraphicsScene event attribute: event.scenePos().x()
        :param event_y: QGraphicsScene event attribute: event.scenePos().y()
        :param new_circle: True when the circle object is being created rather than updated.
        """
        x = event_x - self.draw_tool_radius
        y = event_y - self.draw_tool_radius
        if new_circle:
            self.cursor = QGraphicsEllipseItem(x, y, self.draw_tool_radius * 2, self.draw_tool_radius * 2)
            self.cursor.setPen(QPen(QColor("blue")))
            self.addItem(self.cursor)
        else:
            self.cursor.setRect(x, y, self.draw_tool_radius * 2, self.draw_tool_radius * 2)

    def wheelEvent(self, event):
        delta = event.delta() / 120
        change = int(delta * 6)

        if delta <= -1 and keyboard.is_pressed("ctrl"):
            self.draw_tool_radius = max(self.draw_tool_radius + change, 7)
        elif delta >= 1 and keyboard.is_pressed("ctrl"):
            self.draw_tool_radius = min(self.draw_tool_radius + change, 25)

        self.draw_cursor(event.scenePos().x(), event.scenePos().y())

    def mousePressEvent(self, event):
        if self.cursor:
            self.removeItem(self.cursor)
        self.isPressed = True
        if (
                2 * QtGui.QVector2D(event.pos() - self.rect.center()).length()
                < self.rect.width()
        ):
            self.drag_position = event.pos() - self.rect.topLeft()
        super().mousePressEvent(event)
        self.draw_cursor(event.scenePos().x(), event.scenePos().y(), new_circle=True)
        self.remove_pixels_within_circle(event.scenePos().x(), event.scenePos().y())
        self.update()

    def mouseMoveEvent(self, event):
        if not self.drag_position.isNull():
            self.rect.moveTopLeft(event.pos() - self.drag_position)
        super().mouseMoveEvent(event)
        if self.cursor and self.isPressed:
            self.draw_cursor(event.scenePos().x(), event.scenePos().y())
            self.remove_pixels_within_circle(event.scenePos().x(), event.scenePos().y())
        self.update()

    def mouseReleaseEvent(self, event):
        self.isPressed = False
        self.drag_position = QtCore.QPoint()
        super().mouseReleaseEvent(event)
        self.update()


class DrawBoundingBox(QtWidgets.QGraphicsScene):
    """
    Object responsible for updating and displaying the bounds of the ROI draw.
    """

    def __init__(self, image_to_paint, pixmap_data):
        super().__init__()
        self.addItem(QGraphicsPixmapItem(image_to_paint))
        self.img = image_to_paint
        self.pixmap_data = pixmap_data
        self.drawing = False
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None
        self.box = None

    def draw_bounding_box(self, new_box=False):
        if new_box:
            self.box = QtWidgets.QGraphicsRectItem(self.start_x, self.start_y, 0, 0)
            pen = QtGui.QPen(QtGui.QColor("red"))
            pen.setStyle(QtCore.Qt.DashDotDotLine)
            pen.setWidth(0)
            self.box.setPen(pen)
            self.addItem(self.box)
        else:
            if self.start_x < self.end_x:
                x = self.start_x
                width = self.end_x - self.start_x
            else:
                x = self.end_x
                width = self.start_x - self.end_x

            if self.start_y < self.end_y:
                y = self.start_y
                height = self.end_y - self.start_y
            else:
                y = self.end_y
                height = self.start_y - self.end_y

            self.box.setRect(x, y, width, height)

    def mousePressEvent(self, event):
        if self.box:
            self.removeItem(self.box)
        self.drawing = True
        self.start_x = event.scenePos().x()
        self.start_y = event.scenePos().y()
        self.draw_bounding_box(new_box=True)

    def mouseMoveEvent(self, event):
        if self.drawing:
            self.end_x = event.scenePos().x()
            self.end_y = event.scenePos().y()
            self.draw_bounding_box()

    def mouseReleaseEvent(self, event):
        if self.drawing:
            self.drawing = False
            self.end_x = event.scenePos().x()
            self.end_y = event.scenePos().y()
            self.draw_bounding_box()
