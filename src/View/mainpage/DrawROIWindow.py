import csv
import math
import threading

import numpy
import pydicom
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QPixmap, QColor, QPen
from PySide6.QtWidgets import QMessageBox, QHBoxLayout, QLineEdit, \
    QSizePolicy, QPushButton, QDialog, QListWidget, QGraphicsPixmapItem, \
    QGraphicsEllipseItem, QVBoxLayout, QLabel, QWidget, QFormLayout
import alphashape
from shapely.geometry import MultiPolygon

from src.Controller.MainPageController import MainPageCallClass
from src.Model import ROI
from src.Model.GetPatientInfo import DicomTree
from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.Worker import Worker
from src.View.mainpage.DicomView import DicomView

from src.Controller.PathHandler import resource_path
import platform


# noinspection PyAttributeOutsideInit
class UIDrawROIWindow:

    def setup_ui(self, draw_roi_window_instance,
                 rois, dataset_rtss, signal_roi_drawn):

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
        self.standard_names = []  # Combination of organ and volume
        self.ROI_name = None  # Selected ROI name
        # This will contain the new pixel coordinates specifed
        # by the min and max pixel density
        self.target_pixel_coords = []
        self.target_pixel_coords_single_array = []  # 1D array
        self.draw_roi_window_instance = draw_roi_window_instance
        self.colour = None
        self.ds = None
        self.zoom = 1.0

        self.upper_limit = None
        self.lower_limit = None
        self.dicom_view = DicomView()
        self.dicom_view.slider.valueChanged.connect(self.slider_value_changed)
        self.init_layout()

        QtCore.QMetaObject.connectSlotsByName(draw_roi_window_instance)

    def retranslate_ui(self, draw_roi_window_instance):
        _translate = QtCore.QCoreApplication.translate
        draw_roi_window_instance.setWindowTitle(
            _translate("DrawRoiWindowInstance",
                       "OnkoDICOM - Draw Region Of Interest"))
        self.roi_name_label.setText(
            _translate("ROINameLabel",
                       "Region of Interest: "))
        self.roi_name_line_edit.setText(
            _translate("ROINameLineEdit", ""))
        self.image_slice_number_label.setText(
            _translate("ImageSliceNumberLabel", "Image Slice Number: "))
        self.image_slice_number_line_edit.setText(
            _translate("ImageSliceNumberLineEdit",
                       str(self.dicom_view.current_slice_number)))
        self.image_slice_number_transect_button.setText(
            _translate("ImageSliceNumberTransectButton", "Transect"))
        self.image_slice_number_box_draw_button.setText(
            _translate("ImageSliceNumberBoxDrawButton", "Set Bounds"))
        self.image_slice_number_draw_button.setText(
            _translate("ImageSliceNumberDrawButton", "Draw"))
        self.image_slice_number_move_forward_button.setText(
            _translate("ImageSliceNumberMoveForwardButton", "Forward"))
        self.image_slice_number_move_backward_button.setText(
            _translate("ImageSliceNumberMoveBackwardButton", "Backward"))
        self.draw_roi_window_instance_save_button.setText(
            _translate("DrawRoiWindowInstanceSaveButton", "Save"))
        self.draw_roi_window_instance_cancel_button.setText(
            _translate("DrawRoiWindowInstanceCancelButton", "Cancel"))
        self.internal_hole_max_label.setText(
            _translate("InternalHoleLabel",
                       "Maximum internal hole size (pixels): "))
        self.internal_hole_max_line_edit.setText(
            _translate("InternalHoleInput", "9"))
        self.isthmus_width_max_label.setText(
            _translate("IsthmusWidthLabel",
                       "Maximum isthmus width size (pixels): "))
        self.isthmus_width_max_line_edit.setText(
            _translate("IsthmusWidthInput", "5"))
        self.min_pixel_density_label.setText(
            _translate("MinPixelDensityLabel", "Minimum density (pixels): "))
        self.min_pixel_density_line_edit.setText(
            _translate("MinPixelDensityInput", ""))
        self.max_pixel_density_label.setText(
            _translate("MaxPixelDensityLabel", "Maximum density (pixels): "))
        self.max_pixel_density_line_edit.setText(
            _translate("MaxPixelDensityInput", ""))
        self.draw_roi_window_viewport_zoom_label.setText(
            _translate("DrawRoiWindowViewportZoomLabel", "Zoom: "))
        self.draw_roi_instance_action_reset_button.setText(
            _translate("DrawRoiWindowInstanceActionClearButton", "Reset"))

    def init_layout(self):
        """
        Initialize the layout for the DICOM View tab.
        Add the view widget and the slider in the layout.
        Add the whole container 'tab2_view' as a tab in the main page.
        """

        # Initialise a DrawROIWindow
        if platform.system() == 'Darwin':
            self.stylesheet_path = "res/stylesheet.qss"
        else:
            self.stylesheet_path = "res/stylesheet-win-linux.qss"
        stylesheet = open(resource_path(self.stylesheet_path)).read()
        window_icon = QIcon()
        window_icon.addPixmap(QPixmap(resource_path("res/images/icon.ico")),
                              QIcon.Normal, QIcon.Off)
        self.draw_roi_window_instance.setObjectName("DrawRoiWindowInstance")
        self.draw_roi_window_instance.setWindowIcon(window_icon)

        # Creating a form box to hold all buttons and input fields
        self.draw_roi_window_input_container_box = QFormLayout()
        self.draw_roi_window_input_container_box.setObjectName(
            "DrawRoiWindowInputContainerBox")
        self.draw_roi_window_input_container_box.setLabelAlignment(
            Qt.AlignLeft)

        # Create a label for denoting the ROI name
        self.roi_name_label = QLabel()
        self.roi_name_label.setObjectName("ROINameLabel")
        self.roi_name_line_edit = QLineEdit()
        # Create an input box for ROI name
        self.roi_name_line_edit.setObjectName("ROINameLineEdit")
        self.roi_name_line_edit.setSizePolicy(
            QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.roi_name_line_edit.resize(
            self.roi_name_line_edit.sizeHint().width(),
            self.roi_name_line_edit.sizeHint().height())
        self.roi_name_line_edit.setEnabled(False)
        self.draw_roi_window_input_container_box.addRow(
            self.roi_name_label, self.roi_name_line_edit)

        # Create a label for denoting the Image Slice Number
        self.image_slice_number_label = QLabel()
        self.image_slice_number_label.setObjectName("ImageSliceNumberLabel")
        # Create a line edit for containing the image slice number
        self.image_slice_number_line_edit = QLineEdit()
        self.image_slice_number_line_edit.setObjectName(
            "ImageSliceNumberLineEdit")
        self.image_slice_number_line_edit.setSizePolicy(
            QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        self.image_slice_number_line_edit.resize(
            self.image_slice_number_line_edit.sizeHint().width(),
            self.image_slice_number_line_edit.sizeHint().height())
        self.image_slice_number_line_edit.setEnabled(False)
        self.draw_roi_window_input_container_box.addRow(
            self.image_slice_number_label, self.image_slice_number_line_edit)

        # Create a horizontal box for containing the zoom function
        self.draw_roi_window_viewport_zoom_box = QHBoxLayout()
        self.draw_roi_window_viewport_zoom_box.setObjectName(
            "DrawRoiWindowViewportZoomBox")
        # Create a label for zooming
        self.draw_roi_window_viewport_zoom_label = QLabel()
        self.draw_roi_window_viewport_zoom_label.setObjectName(
            "DrawRoiWindowViewportZoomLabel")
        # Create an input box for zoom factor
        self.draw_roi_window_viewport_zoom_input = QLineEdit()
        self.draw_roi_window_viewport_zoom_input.setObjectName(
            "DrawRoiWindowViewportZoomInput")
        self.draw_roi_window_viewport_zoom_input.setText(
            "{:.2f}".format(self.zoom * 100) + "%")
        self.draw_roi_window_viewport_zoom_input.setCursorPosition(0)
        self.draw_roi_window_viewport_zoom_input.setEnabled(False)
        self.draw_roi_window_viewport_zoom_input.setSizePolicy(
            QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.draw_roi_window_viewport_zoom_input.resize(
            self.draw_roi_window_viewport_zoom_input.sizeHint().width(),
            self.draw_roi_window_viewport_zoom_input.sizeHint().height())
        # Create 2 buttons for zooming in and out
        # Zoom In Button
        self.draw_roi_window_viewport_zoom_in_button = QPushButton()
        self.draw_roi_window_viewport_zoom_in_button.setObjectName(
            "DrawRoiWindowViewportZoomInButton")
        self.draw_roi_window_viewport_zoom_in_button.setSizePolicy(
            QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.draw_roi_window_viewport_zoom_in_button.resize(QSize(24, 24))
        self.draw_roi_window_viewport_zoom_in_button.setProperty(
            "QPushButtonClass", "zoom-button")
        icon_zoom_in = QtGui.QIcon()
        icon_zoom_in.addPixmap(QtGui.QPixmap(resource_path(
            'res/images/btn-icons/zoom_in_icon.png')))
        self.draw_roi_window_viewport_zoom_in_button.setIcon(icon_zoom_in)
        self.draw_roi_window_viewport_zoom_in_button.clicked.connect(
            self.on_zoom_in_clicked)
        # Zoom Out Button
        self.draw_roi_window_viewport_zoom_out_button = QPushButton()
        self.draw_roi_window_viewport_zoom_out_button.setObjectName(
            "DrawRoiWindowViewportZoomOutButton")
        self.draw_roi_window_viewport_zoom_out_button.setSizePolicy(
            QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.draw_roi_window_viewport_zoom_out_button.resize(QSize(24, 24))
        self.draw_roi_window_viewport_zoom_out_button.setProperty(
            "QPushButtonClass", "zoom-button")
        icon_zoom_out = QtGui.QIcon()
        icon_zoom_out.addPixmap(QtGui.QPixmap(
            resource_path('res/images/btn-icons/zoom_out_icon.png')))
        self.draw_roi_window_viewport_zoom_out_button.setIcon(icon_zoom_out)
        self.draw_roi_window_viewport_zoom_out_button.clicked.connect(
            self.on_zoom_out_clicked)
        self.draw_roi_window_viewport_zoom_box.addWidget(
            self.draw_roi_window_viewport_zoom_label)
        self.draw_roi_window_viewport_zoom_box.addWidget(
            self.draw_roi_window_viewport_zoom_input)
        self.draw_roi_window_viewport_zoom_box.addWidget(
            self.draw_roi_window_viewport_zoom_out_button)
        self.draw_roi_window_viewport_zoom_box.addWidget(
            self.draw_roi_window_viewport_zoom_in_button)
        self.draw_roi_window_input_container_box.addRow(
            self.draw_roi_window_viewport_zoom_box)

        # Create a horizontal box for forward and backward button
        self.draw_roi_window_backward_forward_box = QHBoxLayout()
        self.draw_roi_window_backward_forward_box.setObjectName(
            "DrawRoiWindowBackwardForwardBox")
        # Create a button to move backward to the previous image
        self.image_slice_number_move_backward_button = QPushButton()
        self.image_slice_number_move_backward_button.setObjectName(
            "ImageSliceNumberMoveBackwardButton")
        self.image_slice_number_move_backward_button.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum))
        self.image_slice_number_move_backward_button.resize(
            self.image_slice_number_move_backward_button.sizeHint().width(),
            self.image_slice_number_move_backward_button.sizeHint().height())
        self.image_slice_number_move_backward_button.clicked.connect(
            self.on_backward_clicked)
        icon_move_backward = QtGui.QIcon()
        icon_move_backward.addPixmap(QtGui.QPixmap(
            resource_path('res/images/btn-icons/backward_slide_icon.png')))
        self.image_slice_number_move_backward_button.setIcon(
            icon_move_backward)
        self.draw_roi_window_backward_forward_box.addWidget(
            self.image_slice_number_move_backward_button)
        # Create a button to move forward to the next image
        self.image_slice_number_move_forward_button = QPushButton()
        self.image_slice_number_move_forward_button.setObjectName(
            "ImageSliceNumberMoveForwardButton")
        self.image_slice_number_move_forward_button.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum))
        self.image_slice_number_move_forward_button.resize(
            self.image_slice_number_move_forward_button.sizeHint().width(),
            self.image_slice_number_move_forward_button.sizeHint().height())
        self.image_slice_number_move_forward_button.clicked.connect(
            self.on_forward_clicked)
        icon_move_forward = QtGui.QIcon()
        icon_move_forward.addPixmap(QtGui.QPixmap(resource_path(
            'res/images/btn-icons/forward_slide_icon.png')))
        self.image_slice_number_move_forward_button.setIcon(icon_move_forward)
        self.draw_roi_window_backward_forward_box.addWidget(
            self.image_slice_number_move_forward_button)
        self.draw_roi_window_input_container_box.addRow(
            self.draw_roi_window_backward_forward_box)

        # Create a horizontal box for transect and draw button
        self.draw_roi_window_transect_draw_box = QHBoxLayout()
        self.draw_roi_window_transect_draw_box.setObjectName(
            "DrawRoiWindowTransectDrawBox")
        # Create a transect button
        self.image_slice_number_transect_button = QPushButton()
        self.image_slice_number_transect_button.setObjectName(
            "ImageSliceNumberTransectButton")
        self.image_slice_number_transect_button.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum))
        self.image_slice_number_transect_button.resize(
            self.image_slice_number_transect_button.sizeHint().width(),
            self.image_slice_number_transect_button.sizeHint().height())
        self.image_slice_number_transect_button.clicked.connect(
            self.transect_handler)
        icon_transect = QtGui.QIcon()
        icon_transect.addPixmap(QtGui.QPixmap(resource_path(
            'res/images/btn-icons/transect_icon.png')))
        self.image_slice_number_transect_button.setIcon(icon_transect)
        self.draw_roi_window_transect_draw_box.addWidget(
            self.image_slice_number_transect_button)
        # Create a bounding box button
        self.image_slice_number_box_draw_button = QPushButton()
        self.image_slice_number_box_draw_button.setObjectName(
            "ImageSliceNumberBoxDrawButton")
        self.image_slice_number_box_draw_button.setSizePolicy(
            QSizePolicy.MinimumExpanding, QSizePolicy.Minimum
        )
        self.image_slice_number_box_draw_button.resize(
            self.image_slice_number_box_draw_button.sizeHint().width(),
            self.image_slice_number_box_draw_button.sizeHint().height()
        )
        self.image_slice_number_box_draw_button.clicked.connect(
            self.on_box_draw_clicked)
        icon_box_draw = QtGui.QIcon()
        icon_box_draw.addPixmap(QtGui.QPixmap(resource_path(
            'res/images/btn-icons/draw_bound_icon.png')))
        self.image_slice_number_box_draw_button.setIcon(icon_box_draw)
        self.draw_roi_window_transect_draw_box.addWidget(
            self.image_slice_number_box_draw_button)
        # Create a draw button
        self.image_slice_number_draw_button = QPushButton()
        self.image_slice_number_draw_button.setObjectName(
            "ImageSliceNumberDrawButton")
        self.image_slice_number_draw_button.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum))
        self.image_slice_number_draw_button.resize(
            self.image_slice_number_draw_button.sizeHint().width(),
            self.image_slice_number_draw_button.sizeHint().height())
        self.image_slice_number_draw_button.clicked.connect(
            self.on_draw_clicked)
        icon_draw = QtGui.QIcon()
        icon_draw.addPixmap(QtGui.QPixmap(resource_path(
            'res/images/btn-icons/draw_icon.png')))
        self.image_slice_number_draw_button.setIcon(icon_draw)
        self.draw_roi_window_transect_draw_box.addWidget(
            self.image_slice_number_draw_button)
        self.draw_roi_window_input_container_box.addRow(
            self.draw_roi_window_transect_draw_box)

        # Create a contour preview button and alpha selection input
        self.row_preview_layout = QtWidgets.QHBoxLayout()
        self.button_contour_preview = QtWidgets.QPushButton("Preview contour")
        self.button_contour_preview.clicked.connect(self.on_preview_clicked)
        self.label_alpha_value = QtWidgets.QLabel("Alpha value:")
        self.input_alpha_value = QtWidgets.QLineEdit("0.2")
        self.row_preview_layout.addWidget(self.button_contour_preview)
        self.row_preview_layout.addWidget(self.label_alpha_value)
        self.row_preview_layout.addWidget(self.input_alpha_value)
        self.draw_roi_window_input_container_box.addRow(
            self.row_preview_layout)
        icon_preview = QtGui.QIcon()
        icon_preview.addPixmap(QtGui.QPixmap(
            resource_path('res/images/btn-icons/preview_icon.png')))
        self.button_contour_preview.setIcon(icon_preview)

        # Create a label for denoting the max internal hole size
        self.internal_hole_max_label = QLabel()
        self.internal_hole_max_label.setObjectName("InternalHoleLabel")
        # Create input for max internal hole size
        self.internal_hole_max_line_edit = QLineEdit()
        self.internal_hole_max_line_edit.setObjectName("InternalHoleInput")
        self.internal_hole_max_line_edit.setSizePolicy(
            QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        self.internal_hole_max_line_edit.resize(
            self.internal_hole_max_line_edit.sizeHint().width(),
            self.internal_hole_max_line_edit.sizeHint().height())
        self.draw_roi_window_input_container_box.addRow(
            self.internal_hole_max_label, self.internal_hole_max_line_edit)

        # Create a label for denoting the isthmus width size
        self.isthmus_width_max_label = QLabel()
        self.isthmus_width_max_label.setObjectName("IsthmusWidthLabel")
        # Create input for max isthmus width size
        self.isthmus_width_max_line_edit = QLineEdit()
        self.isthmus_width_max_line_edit.setObjectName("IsthmusWidthInput")
        self.isthmus_width_max_line_edit.setSizePolicy(
            QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        self.isthmus_width_max_line_edit.resize(
            self.isthmus_width_max_line_edit.sizeHint().width(),
            self.isthmus_width_max_line_edit.sizeHint().height())
        self.draw_roi_window_input_container_box.addRow(
            self.isthmus_width_max_label, self.isthmus_width_max_line_edit)

        # Create a label for denoting the minimum pixel density
        self.min_pixel_density_label = QLabel()
        self.min_pixel_density_label.setObjectName("MinPixelDensityLabel")
        # Create input for min pixel size
        self.min_pixel_density_line_edit = QLineEdit()
        self.min_pixel_density_line_edit.setObjectName("MinPixelDensityInput")
        self.min_pixel_density_line_edit.setSizePolicy(
            QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        self.min_pixel_density_line_edit.resize(
            self.min_pixel_density_line_edit.sizeHint().width(),
            self.min_pixel_density_line_edit.sizeHint().height())
        self.draw_roi_window_input_container_box.addRow(
            self.min_pixel_density_label, self.min_pixel_density_line_edit)

        # Create a label for denoting the minimum pixel density
        self.max_pixel_density_label = QLabel()
        self.max_pixel_density_label.setObjectName("MaxPixelDensityLabel")
        # Create input for min pixel size
        self.max_pixel_density_line_edit = QLineEdit()
        self.max_pixel_density_line_edit.setObjectName("MaxPixelDensityInput")
        self.max_pixel_density_line_edit.setSizePolicy(
            QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        self.max_pixel_density_line_edit.resize(
            self.max_pixel_density_line_edit.sizeHint().width(),
            self.max_pixel_density_line_edit.sizeHint().height())
        self.draw_roi_window_input_container_box.addRow(
            self.max_pixel_density_label, self.max_pixel_density_line_edit)

        # Create a button to clear the draw
        self.draw_roi_instance_action_reset_button = QPushButton()
        self.draw_roi_instance_action_reset_button.setObjectName(
            "DrawRoiWindowInstanceActionClearButton")
        self.draw_roi_instance_action_reset_button.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum))
        self.draw_roi_instance_action_reset_button.resize(
            self.draw_roi_instance_action_reset_button.sizeHint().width(),
            self.draw_roi_instance_action_reset_button.sizeHint().height())
        self.draw_roi_instance_action_reset_button.clicked.connect(
            self.on_reset_clicked)
        self.draw_roi_instance_action_reset_button.setProperty(
            "QPushButtonClass", "fail-button")
        icon_clear_roi_draw = QtGui.QIcon()
        icon_clear_roi_draw.addPixmap(QtGui.QPixmap(resource_path(
            'res/images/btn-icons/reset_roi_draw_icon.png')))
        self.draw_roi_instance_action_reset_button.setIcon(icon_clear_roi_draw)
        self.draw_roi_window_input_container_box.addRow(
            self.draw_roi_instance_action_reset_button)

        # Create a horizontal box for saving and cancel the drawing
        self.draw_roi_window_cancel_save_box = QHBoxLayout()
        self.draw_roi_window_cancel_save_box.setObjectName(
            "DrawRoiWindowCancelSaveBox")
        # Create an exit button to cancel the drawing
        # Add a button to go back/exit from the application
        self.draw_roi_window_instance_cancel_button = QPushButton()
        self.draw_roi_window_instance_cancel_button.setObjectName(
            "DrawRoiWindowInstanceCancelButton")
        self.draw_roi_window_instance_cancel_button.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum))
        self.draw_roi_window_instance_cancel_button.resize(
            self.draw_roi_window_instance_cancel_button.sizeHint().width(),
            self.draw_roi_window_instance_cancel_button.sizeHint().height())
        self.draw_roi_window_instance_cancel_button.setCursor(
            QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.draw_roi_window_instance_cancel_button.clicked.connect(
            self.on_cancel_button_clicked)
        self.draw_roi_window_instance_cancel_button.setProperty(
            "QPushButtonClass", "fail-button")
        icon_cancel = QtGui.QIcon()
        icon_cancel.addPixmap(QtGui.QPixmap(
            resource_path('res/images/btn-icons/cancel_icon.png')))
        self.draw_roi_window_instance_cancel_button.setIcon(icon_cancel)
        self.draw_roi_window_cancel_save_box.addWidget(
            self.draw_roi_window_instance_cancel_button)
        # Create a save button to save all the changes
        self.draw_roi_window_instance_save_button = QPushButton()
        self.draw_roi_window_instance_save_button.setObjectName(
            "DrawRoiWindowInstanceSaveButton")
        self.draw_roi_window_instance_save_button.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum))
        self.draw_roi_window_instance_save_button.resize(
            self.draw_roi_window_instance_save_button.sizeHint().width(),
            self.draw_roi_window_instance_save_button.sizeHint().height())
        self.draw_roi_window_instance_save_button.setProperty(
            "QPushButtonClass", "success-button")
        icon_save = QtGui.QIcon()
        icon_save.addPixmap(QtGui.QPixmap(resource_path(
            'res/images/btn-icons/save_icon.png')))
        self.draw_roi_window_instance_save_button.setIcon(icon_save)
        self.draw_roi_window_instance_save_button.clicked.connect(
            self.on_save_clicked)
        self.draw_roi_window_cancel_save_box.addWidget(
            self.draw_roi_window_instance_save_button)
        self.draw_roi_window_input_container_box.addRow(
            self.draw_roi_window_cancel_save_box)

        # Creating a horizontal box to hold the ROI view and slider
        self.draw_roi_window_instance_view_box = QHBoxLayout()
        self.draw_roi_window_instance_view_box.setObjectName(
            "DrawRoiWindowInstanceViewBox")
        # Add View and Slider into horizontal box
        self.draw_roi_window_instance_view_box.addWidget(self.dicom_view)
        # Create a widget to hold the image slice box
        self.draw_roi_window_instance_view_widget = QWidget()
        self.draw_roi_window_instance_view_widget.setObjectName(
            "DrawRoiWindowInstanceActionWidget")
        self.draw_roi_window_instance_view_widget.setLayout(
            self.draw_roi_window_instance_view_box)

        # Create a horizontal box for containing the input fields and the
        # viewport
        self.draw_roi_window_main_box = QHBoxLayout()
        self.draw_roi_window_main_box.setObjectName("DrawRoiWindowMainBox")
        self.draw_roi_window_main_box.addLayout(
            self.draw_roi_window_input_container_box, 1)
        self.draw_roi_window_main_box.addWidget(
            self.draw_roi_window_instance_view_widget, 11)

        # Create a new central widget to hold the vertical box layout
        self.draw_roi_window_instance_central_widget = QWidget()
        self.draw_roi_window_instance_central_widget.setObjectName(
            "DrawRoiWindowInstanceCentralWidget")
        self.draw_roi_window_instance_central_widget.setLayout(
            self.draw_roi_window_main_box)

        self.retranslate_ui(self.draw_roi_window_instance)
        self.draw_roi_window_instance.setStyleSheet(stylesheet)
        self.draw_roi_window_instance.setCentralWidget(
            self.draw_roi_window_instance_central_widget)
        QtCore.QMetaObject.connectSlotsByName(self.draw_roi_window_instance)

    def slider_value_changed(self):
        self.image_slice_number_line_edit.setText(str(
            self.dicom_view.current_slice_number))

    def on_zoom_in_clicked(self):
        """
        This function is used for zooming in button
        """
        self.dicom_view.zoom *= 1.05
        self.dicom_view.update_view(zoom_change=True)
        self.draw_roi_window_viewport_zoom_input.setText(
            "{:.2f}".format(self.dicom_view.zoom * 100) + "%")
        self.draw_roi_window_viewport_zoom_input.setCursorPosition(0)

    def on_zoom_out_clicked(self):
        """
        This function is used for zooming out button
        """
        self.dicom_view.zoom /= 1.05
        self.dicom_view.update_view(zoom_change=True)
        self.draw_roi_window_viewport_zoom_input.setText(
            "{:.2f}".format(self.dicom_view.zoom * 100) + "%")
        self.draw_roi_window_viewport_zoom_input.setCursorPosition(0)

    def on_cancel_button_clicked(self):
        """
        This function is used for canceling the drawing
        """
        self.close()

    def on_backward_clicked(self):
        self.backward_pressed = True
        self.forward_pressed = False
        self.slider_changed = False

        image_slice_number = self.dicom_view.current_slice_number

        # Backward will only execute if current image slice is above 1.
        if int(image_slice_number) > 1:
            self.current_slice = int(image_slice_number)

            # decrements slice by 1
            self.current_slice = self.current_slice - 2

            # Update slider to move to correct position
            self.dicom_view.slider.setValue(self.current_slice)
            self.image_slice_number_line_edit.setText(
                str(self.current_slice + 1))
            self.dicom_view.update_view()

    def on_forward_clicked(self):
        pixmaps = self.patient_dict_container.get("pixmaps")
        total_slices = len(pixmaps)

        self.backward_pressed = False
        self.forward_pressed = True
        self.slider_changed = False

        image_slice_number = self.dicom_view.current_slice_number

        # Forward will only execute if current image slice is below the
        # total number of slices.
        if int(image_slice_number) < total_slices:
            # increments slice by 1
            self.current_slice = int(image_slice_number)

            # Update slider to move to correct position
            self.dicom_view.slider.setValue(self.current_slice)
            self.image_slice_number_line_edit.setText(
                str(self.current_slice + 1))
            self.dicom_view.update_view()

    def on_reset_clicked(self):
        self.dicom_view.image_display()
        self.dicom_view.update_view()
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
        id = self.dicom_view.slider.value()

        # Getting most updated selected slice
        if self.forward_pressed:
            id = self.current_slice
        elif self.backward_pressed:
            id = self.current_slice
        elif self.slider_changed:
            id = self.dicom_view.slider.value()

        dt = self.patient_dict_container.dataset[id]
        row_s = dt.PixelSpacing[0]
        col_s = dt.PixelSpacing[1]
        dt.convert_pixel_data()
        MainPageCallClass().run_transect(
            self.draw_roi_window_instance,
            self.dicom_view.view,
            pixmaps[id],
            dt._pixel_array.transpose(),
            row_s,
            col_s,
            is_roi_draw=True,
        )

    def on_transect_close(self):
        if self.upper_limit and self.lower_limit:
            self.min_pixel_density_line_edit.setText(str(self.lower_limit))
            self.max_pixel_density_line_edit.setText(str(self.upper_limit))

        self.dicom_view.update_view()

    def on_draw_clicked(self):
        """
        Function triggered when the Draw button is pressed from the menu.
        """
        pixmaps = self.patient_dict_container.get("pixmaps")

        if self.min_pixel_density_line_edit.text() == "" \
                or self.max_pixel_density_line_edit.text() == "":
            QMessageBox.about(self.draw_roi_window_instance, "Not Enough Data",
                              "Not all values are specified or correct.")
        else:
            id = self.dicom_view.slider.value()

            # Getting most updated selected slice
            if self.forward_pressed:
                id = self.current_slice
            elif self.backward_pressed:
                id = self.current_slice
            elif self.slider_changed:
                id = self.dicom_view.slider.value()

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
                    QMessageBox.about(
                        self.draw_roi_window_instance, "Incorrect Input",
                        "Please ensure maximum density is atleast higher "
                        "than minimum density.")

                self.drawingROI = Drawing(
                    pixmaps[id],
                    dt._pixel_array.transpose(),
                    min_pixel,
                    max_pixel,
                    self.patient_dict_container.dataset[id],
                    self.draw_roi_window_instance
                )
                self.dicom_view.view.setScene(self.drawingROI)

            else:
                QMessageBox.about(self.draw_roi_window_instance,
                                  "Not Enough Data",
                                  "Not all values are specified or correct.")

    def on_box_draw_clicked(self):
        id = self.dicom_view.slider.value()
        dt = self.patient_dict_container.dataset[id]
        dt.convert_pixel_data()
        pixmaps = self.patient_dict_container.get("pixmaps")

        self.bounds_box_draw = DrawBoundingBox(pixmaps[id], dt)
        self.dicom_view.view.setScene(self.bounds_box_draw)

    def on_save_clicked(self):
        # Make sure the user has clicked Draw first
        if self.ds is not None:
            # Because the contour data needs to be a list of points that
            # form a polygon, the list of pixel points need to be converted
            # to a concave hull.
            pixel_hull = self.calculate_concave_hull_of_points()
            if pixel_hull is not None:
                # Convert polygon's pixel points to RCS locations.
                hull = self.convert_hull_to_rcs(pixel_hull)
                # The list of points will need to be converted into a
                # single-dimensional array, as RTSTRUCT contour
                # data is stored in such a way.
                # i.e. [x, y, z, x, y, z, x, y, z, ..., ...]
                single_array = []
                for sublist in hull:
                    for item in sublist:
                        single_array.append(item)

                # Create a popup window that modifies the RTSTRUCT and tells
                # the user that processing is happening.
                progress_window = SaveROIProgressWindow(
                    self,
                    QtCore.Qt.WindowTitleHint)
                progress_window.signal_roi_saved.connect(self.roi_saved)
                progress_window.start_saving(self.dataset_rtss, self.ROI_name,
                                             single_array, self.ds)
                progress_window.show()
            else:
                QMessageBox.about(self.draw_roi_window_instance,
                                  "Multipolygon detected",
                                  "Selected points will generate multiple "
                                  "contours, which is not currently "
                                  "supported. "
                                  "If the region you are drawing is not "
                                  "meant to generate multiple contours, "
                                  "please "
                                  "ajust your selected alpha value.")
        else:
            QMessageBox.about(self.draw_roi_window_instance, "Not Enough Data",
                              "Please ensure you have drawn your ROI first.")

    def roi_saved(self, new_rtss):
        self.signal_roi_drawn.emit((new_rtss, {"draw": self.ROI_name}))
        QMessageBox.about(self.draw_roi_window_instance, "Saved",
                          "New contour successfully created!")
        self.close()

    def calculate_concave_hull_of_points(self):
        """
        Return the alpha shape of the highlighted pixels using the alpha
        entered by the user.
        :return: List of points ordered to form a polygon.
        """
        # Get all the pixels in the drawing window's list of highlighted
        # pixels, excluding the removed pixels.
        target_pixel_coords = [(item[0] + 1, item[1] + 1) for item in
                               self.drawingROI.target_pixel_coords]

        # Calculate the concave hull of the points.
        # alpha = 0.95 * alphashape.optimizealpha(points)
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
        """
        Converts all the pixel coordinates in the given polygon to RCS
        coordinates based off the CT image's matrix.
        :param hull_pts: List of pixel coordinates ordered to form a polygon.
        :return: List of RCS coordinates ordered to form a polygon
        """
        slider_id = self.dicom_view.slider.value()
        dataset = self.patient_dict_container.dataset[slider_id]
        pixlut = self.patient_dict_container.get("pixluts")[
            dataset.SOPInstanceUID]
        z_coord = dataset.SliceLocation
        points = []

        # Convert the pixels to an RCS location and move them to a list
        # of points.
        for i, item in enumerate(hull_pts):
            points.append(ROI.pixel_to_rcs(pixlut, item[0], item[1]))

        contour_data = []
        for p in points:
            coords = (p[0], p[1], z_coord)
            contour_data.append(coords)

        return contour_data

    def on_preview_clicked(self):
        if hasattr(self, 'drawingROI') and len(
                self.drawingROI.target_pixel_coords) > 0:
            list_of_points = self.calculate_concave_hull_of_points()
            if list_of_points is not None:
                self.drawingROI.draw_contour_preview(list_of_points)
            else:
                QMessageBox.about(self.draw_roi_window_instance,
                                  "Multipolygon detected",
                                  "Selected points will generate multiple "
                                  "contours, which is not currently "
                                  "supported. "
                                  "If the region you are drawing is not "
                                  "meant to generate multiple contours, "
                                  "please "
                                  "ajust your selected alpha value.")
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
            QMessageBox.about(self.draw_roi_window_instance,
                              "ROI already exists in RTSS",
                              "Would you like to continue?")

        self.ROI_name = roi_name
        self.roi_name_line_edit.setText(self.ROI_name)


class SaveROIProgressWindow(QtWidgets.QDialog):
    """
    This class displays a window that advises the user that the RTSTRUCT is
    being modified, and then creates a new
    thread where the new RTSTRUCT is modified.
    """

    signal_roi_saved = QtCore.Signal(pydicom.Dataset)  # Emits the new dataset

    def __init__(self, *args, **kwargs):
        super(SaveROIProgressWindow, self).__init__(*args, **kwargs)
        layout = QtWidgets.QVBoxLayout()
        text = QtWidgets.QLabel("Creating ROI...")
        layout.addWidget(text)
        self.setWindowTitle("Please wait...")
        self.setFixedWidth(150)
        self.setLayout(layout)

        self.threadpool = QtCore.QThreadPool()

    def start_saving(self, dataset_rtss, roi_name, single_array, ds):
        """
        Creates a thread that generates the new dataset object.
        :param dataset_rtss: dataset of RTSS
        :param roi_name: ROIName
        :param single_array: Coordinates of pixels for new ROI
        :param ds: Data Set of selected DICOM image file
        """
        worker = Worker(ROI.create_roi, dataset_rtss, roi_name, single_array,
                        ds)
        worker.signals.result.connect(self.roi_saved)
        self.threadpool.start(worker)

    def roi_saved(self, result):
        """
        This method is called when the second thread completes generation of
        the new dataset object.
        :param result: The resulting dataset from the ROI.create_roi function.
        """
        self.signal_roi_saved.emit(result)
        self.close()


# This Class handles the ROI Pop Up functionalities
class SelectROIPopUp(QDialog):
    signal_roi_name = QtCore.Signal(str)

    def __init__(self):
        QDialog.__init__(self)

        if platform.system() == 'Darwin':
            self.stylesheet_path = "res/stylesheet.qss"
        else:
            self.stylesheet_path = "res/stylesheet-win-linux.qss"
        stylesheet = open(resource_path(self.stylesheet_path)).read()
        self.setStyleSheet(stylesheet)
        self.standard_names = []
        self.init_standard_names()

        self.setWindowTitle("Select A Region of Interest To Draw")
        self.setMinimumSize(350, 180)

        self.icon = QtGui.QIcon()
        self.icon.addPixmap(
            QtGui.QPixmap(resource_path("res/images/icon.ico")),
            QtGui.QIcon.Normal, QtGui.QIcon.Off)
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
        Create two lists containing standard organ and standard volume names
        as set by the Add-On options.
        """
        with open(resource_path('data/csv/organName.csv'), 'r') as f:
            standard_organ_names = []

            csv_input = csv.reader(f)
            header = next(f)  # Ignore the "header" of the column
            for row in csv_input:
                standard_organ_names.append(row[0])

        with open(resource_path('data/csv/volumeName.csv'), 'r') as f:
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
        if self.list_of_ROIs.currentItem() is not None:
            roi = self.list_of_ROIs.currentItem()
            self.roi_name = str(roi.text())

            # Call function on UIDrawWindow so it has selected ROI
            self.signal_roi_name.emit(self.roi_name)
            self.close()

    def on_cancel_clicked(self):
        self.close()


# This Class handles the Drawing functionality
class Drawing(QtWidgets.QGraphicsScene):

    # Initialisation function  of the class
    def __init__(self, image_to_paint, pixmapdata, min_pixel, max_pixel,
                 dataset, draw_roi_window_instance):
        super(Drawing, self).__init__()

        # create the canvas to draw the line on and all its necessary
        # components
        self.draw_roi_window_instance = draw_roi_window_instance
        self.min_pixel = min_pixel
        self.max_pixel = max_pixel
        self.addItem(QGraphicsPixmapItem(image_to_paint))
        self.img = image_to_paint
        self.data = pixmapdata
        self.values = []
        self.get_values()
        self.rect = QtCore.QRect(250, 300, 20, 20)
        self.update()
        self._points = {}
        self._circlePoints = []
        self.drag_position = QtCore.QPoint()
        self.cursor = None
        self.polygon_preview = None
        self.isPressed = False
        self.dataset = dataset
        self.pixel_array = None
        # This will contain the new pixel coordinates specifed by the min
        # and max pixel density
        self.target_pixel_coords = []
        self.accordingColorList = []
        self.q_image = None
        self.q_pixmaps = None
        self.label = QtWidgets.QLabel()
        self.draw_tool_radius = 19
        self._display_pixel_color()

    def _display_pixel_color(self):
        """
        Creates the initial list of pixel values within the given minimum and
        maximum densities, then displays them
        on the view.
        """
        if self.min_pixel <= self.max_pixel:
            data_set = self.dataset
            if hasattr(self.draw_roi_window_instance, 'bounds_box_draw'):
                box = self.draw_roi_window_instance.bounds_box_draw.box.rect()
                min_x = int(box.x())
                min_y = int(box.y())
                max_x = int(box.width() + min_x)
                max_y = int(box.height() + min_y)
            else:
                min_x = 0
                min_y = 0
                max_x = data_set.Rows
                max_y = data_set.Columns

            """
            pixel_array is a 2-Dimensional array containing all pixel 
            coordinates of the q_image. 
            pixel_array[x][y] will return the density of the pixel
            """
            self.pixel_array = data_set._pixel_array
            self.q_image = self.img.toImage()
            for x_coord in range(min_y, max_y):
                for y_coord in range(min_x, max_x):
                    if (self.pixel_array[x_coord][
                            y_coord] >= self.min_pixel) and (
                            self.pixel_array[x_coord][
                                y_coord] <= self.max_pixel):
                        self.target_pixel_coords.append((y_coord, x_coord))

            """
            For the meantime, a new image is created and the pixels specified 
            are coloured. 
            This will need to altered so that it creates a new layer over the 
            existing image instead of replacing it.
            """
            # Convert QPixMap into Qimage
            for x_coord, y_coord in self.target_pixel_coords:
                c = self.q_image.pixel(x_coord, y_coord)
                colors = QColor(c).getRgbF()
                self.accordingColorList.append((x_coord, y_coord, colors))

            color = QtGui.QColor()
            color.setRgb(90, 250, 175, 200)
            for x_coord, y_coord, colors in self.accordingColorList:
                self.q_image.setPixelColor(x_coord, y_coord, color)

            self.refresh_image()

    def _find_neighbor_point(self, event):
        """
        Find point around mouse position. This function is for if we want to
        choose and drag the circle
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

    def get_values(self):
        """
        This function gets the corresponding values of all the points in the
        drawn line from the dataset.
        """
        for i in range(512):
            for j in range(512):
                self.values.append(self.data[i][j])

    def refresh_image(self):
        """
        Convert QImage containing modified CT slice with highlighted pixels
        into a QPixmap, and then display it onto
        the view.
        """
        self.q_pixmaps = QtWidgets.QGraphicsPixmapItem(
            QtGui.QPixmap.fromImage(self.q_image))
        self.addItem(self.q_pixmaps)

    def remove_pixels_within_circle(self, clicked_x, clicked_y):
        """
        Removes all highlighted pixels within the selected circle and updates
        the image.
        """
        # Calculate euclidean distance between each highlighted point and
        # the clicked point. If the distance is less than the radius,
        # remove it from the highlighted pixels.
        for x, y, colors in self.accordingColorList[:]:
            clicked_point = numpy.array((clicked_x, clicked_y))
            point_to_check = numpy.array((x, y))
            distance = numpy.linalg.norm(clicked_point - point_to_check)
            if distance <= self.draw_tool_radius:
                self.q_image.setPixelColor(x, y, QColor.fromRgbF(colors[0],
                                                                 colors[1],
                                                                 colors[2],
                                                                 colors[3]))
                self.target_pixel_coords.remove((x, y))
                self.accordingColorList.remove((x, y, colors))

        self.refresh_image()

    def draw_cursor(self, event_x, event_y, new_circle=False):
        """
        Draws a blue circle where the user clicked.
        :param event_x: QGraphicsScene event attribute: event.scenePos().x()
        :param event_y: QGraphicsScene event attribute: event.scenePos().y()
        :param new_circle: True when the circle object is being created rather
        than updated.
        """
        x = event_x - self.draw_tool_radius
        y = event_y - self.draw_tool_radius
        if new_circle:
            self.cursor = QGraphicsEllipseItem(x, y, self.draw_tool_radius * 2,
                                               self.draw_tool_radius * 2)
            pen = QPen(QColor("blue"))
            pen.setWidth(0)
            self.cursor.setPen(pen)
            self.cursor.setZValue(1)
            self.addItem(self.cursor)
        elif self.cursor is not None:
            self.cursor.setRect(x, y, self.draw_tool_radius * 2,
                                self.draw_tool_radius * 2)

    def draw_contour_preview(self, list_of_points):
        """
        Draws a polygon onto the view so the user can preview what their
        contour will look like once exported.
        :param list_of_points: A list of points ordered to form a polygon.
        """
        qpoint_list = []
        for point in list_of_points:
            qpoint = QtCore.QPoint(point[0], point[1])
            qpoint_list.append(qpoint)
        if self.polygon_preview is not None:  # Erase the existing preview
            self.removeItem(self.polygon_preview)
        polygon = QtGui.QPolygonF(qpoint_list)
        self.polygon_preview = QtWidgets.QGraphicsPolygonItem(polygon)
        pen = QtGui.QPen(QtGui.QColor("yellow"))
        pen.setStyle(QtCore.Qt.DashDotDotLine)
        self.polygon_preview.setPen(pen)
        self.addItem(self.polygon_preview)

    def wheelEvent(self, event):
        delta = event.delta() / 120
        change = int(delta * 3)

        if delta <= -1:
            self.draw_tool_radius = max(self.draw_tool_radius + change, 4)
        elif delta >= 1:
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
        self.draw_cursor(event.scenePos().x(), event.scenePos().y(),
                         new_circle=True)
        self.remove_pixels_within_circle(event.scenePos().x(),
                                         event.scenePos().y())
        self.update()

    def mouseMoveEvent(self, event):
        if not self.drag_position.isNull():
            self.rect.moveTopLeft(event.pos() - self.drag_position)
        super().mouseMoveEvent(event)
        if self.cursor and self.isPressed:
            self.draw_cursor(event.scenePos().x(), event.scenePos().y())
            self.remove_pixels_within_circle(event.scenePos().x(),
                                             event.scenePos().y())
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
            self.box = QtWidgets.QGraphicsRectItem(self.start_x, self.start_y,
                                                   0, 0)
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
