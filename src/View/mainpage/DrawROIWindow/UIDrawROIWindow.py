import platform

import pydicom
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QFormLayout, QLabel, QLineEdit, QSizePolicy, QHBoxLayout, QPushButton, QWidget, \
    QMessageBox
from alphashape import alphashape
from shapely.geometry import MultiPolygon

from src.Controller.MainPageController import MainPageCallClass
from src.Controller.PathHandler import resource_path
from src.Model import ROI
from src.Model.PatientDictContainer import PatientDictContainer
from src.View.mainpage.DicomAxialView import DicomAxialView
from src.View.mainpage.DrawROIWindow.Drawing import Drawing
from src.View.mainpage.DrawROIWindow.SaveROIProgressWindow import SaveROIProgressWindow
from src.View.mainpage.DrawROIWindow.DrawBoundingBox import DrawBoundingBox


class UIDrawROIWindow:

    def setup_ui(self, draw_roi_window_instance, rois, dataset_rtss, signal_roi_drawn):
        self.patient_dict_container = PatientDictContainer()

        self.rois = rois
        self.dataset_rtss = dataset_rtss
        self.signal_roi_drawn = signal_roi_drawn
        self.drawn_roi_list = {}
        self.standard_organ_names = []
        self.standard_volume_names = []
        self.standard_names = []  # Combination of organ and volume
        self.ROI_name = None  # Selected ROI name
        self.target_pixel_coords = []  # This will contain the new pixel coordinates specified by the min and max
        self.drawingROI = None
        self.slice_changed = False
        # pixel density
        self.target_pixel_coords_single_array = []  # 1D array
        self.draw_roi_window_instance = draw_roi_window_instance
        self.colour = None
        self.ds = None
        self.zoom = 1.0

        self.upper_limit = None
        self.lower_limit = None

        self.dicom_view = DicomAxialView()
        self.current_slice = self.dicom_view.slider.value()
        self.dicom_view.slider.valueChanged.connect(self.slider_value_changed)
        self.init_layout()

        QtCore.QMetaObject.connectSlotsByName(draw_roi_window_instance)

    def retranslate_ui(self, draw_roi_window_instance):
        _translate = QtCore.QCoreApplication.translate
        draw_roi_window_instance.setWindowTitle(
            _translate("DrawRoiWindowInstance", "OnkoDICOM - Draw Region Of Interest"))
        self.roi_name_label.setText(_translate("ROINameLabel", "Region of Interest: "))
        self.roi_name_line_edit.setText(_translate("ROINameLineEdit", ""))
        self.image_slice_number_label.setText(_translate("ImageSliceNumberLabel", "Image Slice Number: "))
        self.image_slice_number_line_edit.setText(
            _translate("ImageSliceNumberLineEdit", str(self.dicom_view.current_slice_number)))
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
        self.draw_roi_window_cursor_radius_change_label.setText(
            _translate("DrawRoiWindowCursorRadiusChangeLabel", "Cursor Radius: "))

        self.draw_roi_window_instance_action_reset_button.setText(
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
        window_icon.addPixmap(QPixmap(resource_path("res/images/icon.ico")), QIcon.Normal, QIcon.Off)
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
        self.draw_roi_window_input_container_box.addRow(self.image_slice_number_label,
                                                        self.image_slice_number_line_edit)

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
        icon_zoom_in.addPixmap(QtGui.QPixmap(resource_path('res/images/btn-icons/zoom_in_icon.png')))
        self.draw_roi_window_viewport_zoom_in_button.setIcon(icon_zoom_in)
        self.draw_roi_window_viewport_zoom_in_button.clicked.connect(self.onZoomInClicked)
        # Zoom Out Button
        self.draw_roi_window_viewport_zoom_out_button = QPushButton()
        self.draw_roi_window_viewport_zoom_out_button.setObjectName("DrawRoiWindowViewportZoomOutButton")
        self.draw_roi_window_viewport_zoom_out_button.setSizePolicy(
            QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.draw_roi_window_viewport_zoom_out_button.resize(QSize(24, 24))
        self.draw_roi_window_viewport_zoom_out_button.setProperty("QPushButtonClass", "zoom-button")
        icon_zoom_out = QtGui.QIcon()
        icon_zoom_out.addPixmap(QtGui.QPixmap(resource_path('res/images/btn-icons/zoom_out_icon.png')))
        self.draw_roi_window_viewport_zoom_out_button.setIcon(icon_zoom_out)
        self.draw_roi_window_viewport_zoom_out_button.clicked.connect(self.onZoomOutClicked)
        self.draw_roi_window_viewport_zoom_box.addWidget(self.draw_roi_window_viewport_zoom_label)
        self.draw_roi_window_viewport_zoom_box.addWidget(self.draw_roi_window_viewport_zoom_input)
        self.draw_roi_window_viewport_zoom_box.addWidget(self.draw_roi_window_viewport_zoom_out_button)
        self.draw_roi_window_viewport_zoom_box.addWidget(self.draw_roi_window_viewport_zoom_in_button)
        self.draw_roi_window_input_container_box.addRow(self.draw_roi_window_viewport_zoom_box)

        self.init_cursor_radius_change_box()

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
        self.image_slice_number_move_backward_button.clicked.connect(self.onBackwardClicked)
        icon_move_backward = QtGui.QIcon()
        icon_move_backward.addPixmap(QtGui.QPixmap(resource_path('res/images/btn-icons/backward_slide_icon.png')))
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
        self.image_slice_number_move_forward_button.clicked.connect(self.onForwardClicked)
        icon_move_forward = QtGui.QIcon()
        icon_move_forward.addPixmap(QtGui.QPixmap(resource_path('res/images/btn-icons/forward_slide_icon.png')))
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
        icon_transect.addPixmap(QtGui.QPixmap(resource_path('res/images/btn-icons/transect_icon.png')))
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
        self.image_slice_number_box_draw_button.clicked.connect(self.onBoxDrawClicked)
        icon_box_draw = QtGui.QIcon()
        icon_box_draw.addPixmap(QtGui.QPixmap(resource_path('res/images/btn-icons/draw_bound_icon.png')))
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
        self.image_slice_number_draw_button.clicked.connect(self.onDrawClicked)
        icon_draw = QtGui.QIcon()
        icon_draw.addPixmap(QtGui.QPixmap(resource_path('res/images/btn-icons/draw_icon.png')))
        self.image_slice_number_draw_button.setIcon(icon_draw)
        self.draw_roi_window_transect_draw_box.addWidget(self.image_slice_number_draw_button)
        self.draw_roi_window_input_container_box.addRow(self.draw_roi_window_transect_draw_box)

        # Create a contour preview button
        self.row_preview_layout = QtWidgets.QHBoxLayout()
        self.button_contour_preview = QtWidgets.QPushButton("Preview contour")
        self.button_contour_preview.clicked.connect(self.onPreviewClicked)
        self.row_preview_layout.addWidget(self.button_contour_preview)
        self.draw_roi_window_input_container_box.addRow(self.row_preview_layout)
        icon_preview = QtGui.QIcon()
        icon_preview.addPixmap(QtGui.QPixmap(resource_path('res/images/btn-icons/preview_icon.png')))
        self.button_contour_preview.setIcon(icon_preview)

        # Create input line edit for alpha value
        self.label_alpha_value = QtWidgets.QLabel("Alpha value:")
        self.input_alpha_value = QtWidgets.QLineEdit("0.2")
        self.input_alpha_value.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        self.input_alpha_value.resize(self.input_alpha_value.sizeHint().width(),
                                      self.input_alpha_value.sizeHint().height())
        self.draw_roi_window_input_container_box.addRow(self.label_alpha_value, self.input_alpha_value)

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
        self.draw_roi_window_instance_action_reset_button.clicked.connect(self.onResetClicked)
        self.draw_roi_window_instance_action_reset_button.setProperty("QPushButtonClass", "fail-button")
        icon_clear_roi_draw = QtGui.QIcon()
        icon_clear_roi_draw.addPixmap(QtGui.QPixmap(resource_path('res/images/btn-icons/reset_roi_draw_icon.png')))
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
        self.draw_roi_window_instance_cancel_button.resize(
            self.draw_roi_window_instance_cancel_button.sizeHint().width(),
            self.draw_roi_window_instance_cancel_button.sizeHint().height())
        self.draw_roi_window_instance_cancel_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.draw_roi_window_instance_cancel_button.clicked.connect(self.onCancelButtonClicked)
        self.draw_roi_window_instance_cancel_button.setProperty("QPushButtonClass", "fail-button")
        icon_cancel = QtGui.QIcon()
        icon_cancel.addPixmap(QtGui.QPixmap(resource_path('res/images/btn-icons/cancel_icon.png')))
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
        icon_save.addPixmap(QtGui.QPixmap(resource_path('res/images/btn-icons/save_icon.png')))
        self.draw_roi_window_instance_save_button.setIcon(icon_save)
        self.draw_roi_window_instance_save_button.clicked.connect(self.onSaveClicked)
        self.draw_roi_window_cancel_save_box.addWidget(self.draw_roi_window_instance_save_button)

        self.draw_roi_window_input_container_box.addRow(self.draw_roi_window_cancel_save_box)

        # Creating a horizontal box to hold the ROI view and slider
        self.draw_roi_window_instance_view_box = QHBoxLayout()
        self.draw_roi_window_instance_view_box.setObjectName("DrawRoiWindowInstanceViewBox")
        # Add View and Slider into horizontal box
        self.draw_roi_window_instance_view_box.addWidget(self.dicom_view)
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

    def slider_value_changed(self):
        self.set_current_slice(self.dicom_view.slider.value())

    def set_current_slice(self, slice_number):
        self.image_slice_number_line_edit.setText(str(slice_number + 1))
        self.current_slice = slice_number
        self.dicom_view.update_view()

        # check if this slice has any drawings before
        if self.drawn_roi_list.get(self.current_slice) is not None:
            self.drawingROI = self.drawn_roi_list[self.current_slice]['drawingROI']
            self.ds = self.drawn_roi_list[self.current_slice]['ds']
            self.dicom_view.view.setScene(self.drawingROI)
        else:
            self.ds = None

    def onZoomInClicked(self):
        """
        This function is used for zooming in button
        """
        self.dicom_view.zoom *= 1.05
        self.dicom_view.update_view(zoom_change=True)
        if self.drawingROI:
            self.dicom_view.view.setScene(self.drawingROI)
        self.draw_roi_window_viewport_zoom_input.setText("{:.2f}".format(self.dicom_view.zoom * 100) + "%")
        self.draw_roi_window_viewport_zoom_input.setCursorPosition(0)

    def onZoomOutClicked(self):
        """
        This function is used for zooming out button
        """
        self.dicom_view.zoom /= 1.05
        self.dicom_view.update_view(zoom_change=True)
        if self.drawingROI:
            self.dicom_view.view.setScene(self.drawingROI)
        self.draw_roi_window_viewport_zoom_input.setText("{:.2f}".format(self.dicom_view.zoom * 100) + "%")
        self.draw_roi_window_viewport_zoom_input.setCursorPosition(0)

    def onCancelButtonClicked(self):
        """
        This function is used for canceling the drawing
        """
        self.closeWindow()

    def onBackwardClicked(self):
        image_slice_number = self.current_slice
        # save progress
        if self.save_drawing_progress(image_slice_number):
            # Backward will only execute if current image slice is above 0.
            if int(image_slice_number) > 0:
                # decrements slice by 1 and update slider to move to correct position
                self.dicom_view.slider.setValue(image_slice_number - 1)

    def onForwardClicked(self):
        image_slice_number = self.current_slice
        # save progress
        if self.save_drawing_progress(image_slice_number):
            pixmaps = self.patient_dict_container.get("pixmaps_axial")
            total_slices = len(pixmaps)

            # Forward will only execute if current image slice is below the total number of slices.
            if int(image_slice_number) < total_slices:
                # increments slice by 1 and update slider to move to correct position
                self.dicom_view.slider.setValue(image_slice_number + 1)

    def onResetClicked(self):
        self.dicom_view.image_display()
        self.dicom_view.update_view()
        self.isthmus_width_max_line_edit.setText("5")
        self.internal_hole_max_line_edit.setText("9")
        self.min_pixel_density_line_edit.setText("")
        self.max_pixel_density_line_edit.setText("")
        if hasattr(self, 'bounds_box_draw'):
            delattr(self, 'bounds_box_draw')
        if hasattr(self, 'drawingROI'):
            delattr(self, 'drawingROI')
        self.ds = None

    def transect_handler(self):
        """
        Function triggered when the Transect button is pressed from the menu.
        """

        pixmaps = self.patient_dict_container.get("pixmaps_axial")
        id = self.current_slice
        dt = self.patient_dict_container.dataset[id]
        rowS = dt.PixelSpacing[0]
        colS = dt.PixelSpacing[1]
        dt.convert_pixel_data()
        MainPageCallClass().run_transect(
            self.draw_roi_window_instance,
            self.dicom_view.view,
            pixmaps[id],
            dt._pixel_array.transpose(),
            rowS,
            colS,
            is_roi_draw=True,
        )

    def save_drawing_progress(self, image_slice_number):
        #  Save drawing progress only when roi on current slice has changed
        if self.slice_changed:
            if hasattr(self, 'drawingROI') and self.drawingROI and self.ds is not None:
                pixel_hull = self.calculate_concave_hull_of_points(self.drawingROI.target_pixel_coords)
                if pixel_hull is not None:
                    self.drawn_roi_list[image_slice_number] = {
                        'coords': pixel_hull,
                        'ds': self.ds,
                        'drawingROI': self.drawingROI
                    }
                    self.slice_changed = False
                    return True
                else:
                    self.display_multipolygon_warning(image_slice_number)
                    return False
        else:
            return True
        return True

    def on_transect_close(self):
        if self.upper_limit and self.lower_limit:
            self.min_pixel_density_line_edit.setText(str(self.lower_limit))
            self.max_pixel_density_line_edit.setText(str(self.upper_limit))

        self.dicom_view.update_view()

    def onDrawClicked(self):
        """
        Function triggered when the Draw button is pressed from the menu.
        """
        pixmaps = self.patient_dict_container.get("pixmaps_axial")

        if self.min_pixel_density_line_edit.text() == "" or self.max_pixel_density_line_edit.text() == "":
            QMessageBox.about(self.draw_roi_window_instance, "Not Enough Data",
                              "Not all values are specified or correct.")
        else:
            # Getting most updated selected slice
            id = self.current_slice

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
                    self.draw_roi_window_instance,
                    self.slice_changed,
                    self.current_slice,
                    set()

                )
                self.slice_changed = True
                self.dicom_view.view.setScene(self.drawingROI)
                self.enable_cursor_radius_change_box()
            else:
                QMessageBox.about(self.draw_roi_window_instance, "Not Enough Data",
                                  "Not all values are specified or correct.")

    def onBoxDrawClicked(self):
        id = self.current_slice
        dt = self.patient_dict_container.dataset[id]
        dt.convert_pixel_data()
        pixmaps = self.patient_dict_container.get("pixmaps_axial")

        self.bounds_box_draw = DrawBoundingBox(pixmaps[id], dt)
        self.dicom_view.view.setScene(self.bounds_box_draw)

    def onSaveClicked(self):
        # Make sure the user has clicked Draw first
        if self.save_drawing_progress(image_slice_number=self.current_slice):
            self.saveROIList()

    def saveROIList(self):
        roi_list = []
        if self.drawn_roi_list == {}:
            QMessageBox.about(self.draw_roi_window_instance, "No ROI Detected",
                              "Please ensure you have drawn your ROI first.")
            return
        for slice_id, slice_info in self.drawn_roi_list.items():
            pixel_hull = slice_info['coords']
            if pixel_hull is not None:
                hull = self.convert_hull_to_rcs(pixel_hull,
                                                slice_id)  # Convert the polygon's pixel points to RCS locations.

                single_array = []
                for sublist in hull:
                    for item in sublist:
                        single_array.append(item)
                roi_list.append({
                    'ds': slice_info['ds'],
                    'coords': single_array
                })
            else:
                self.display_multipolygon_warning(slice_id)
                return

        # The list of points will need to be converted into a single-dimensional array, as RTSTRUCT contour
        # data is stored in such a way. i.e. [x, y, z, x, y, z, x, y, z, ..., ...]
        # Create a popup window that modifies the RTSTRUCT and tells the user that processing is happening.
        progress_window = SaveROIProgressWindow(self, QtCore.Qt.WindowTitleHint)
        progress_window.signal_roi_saved.connect(self.roi_saved)
        progress_window.start_saving(self.dataset_rtss, self.ROI_name, roi_list)
        progress_window.show()

    def roi_saved(self, new_rtss):
        self.signal_roi_drawn.emit((new_rtss, {"draw": self.ROI_name}))
        QMessageBox.about(self.draw_roi_window_instance, "Saved", "New contour successfully created!")
        self.closeWindow()

    def calculate_concave_hull_of_points(self, pixel_coords):
        """
        Return the alpha shape of the highlighted pixels using the alpha entered by the user.
        :return: List of points ordered to form a polygon.
        """
        # Get all the pixels in the drawing window's list of highlighted pixels, excluding the removed pixels.
        target_pixel_coords = [(item[0] + 1, item[1] + 1) for item in pixel_coords]
        # Calculate the concave hull of the points.
        # alpha = 0.95 * alphashape.optimizealpha(points)
        alpha = float(self.input_alpha_value.text())
        hull = alphashape(target_pixel_coords, alpha)
        if isinstance(hull, MultiPolygon):
            return None

        hull_xy = hull.exterior.coords.xy

        points = []
        for i in range(len(hull_xy[0])):
            points.append([int(hull_xy[0][i]), int(hull_xy[1][i])])
        return points

    def convert_hull_to_rcs(self, hull_pts, slider_id):
        """
        Converts all the pixel coordinates in the given polygon to RCS coordinates based off the CT image's matrix.
        :param hull_pts: List of pixel coordinates ordered to form a polygon.
        :return: List of RCS coordinates ordered to form a polygon

        Parameters
        ----------
        slider_id: id of the slide to convert to rcs (z coordinate)
        """
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

    def onPreviewClicked(self):
        if hasattr(self, 'drawingROI') and len(self.drawingROI.target_pixel_coords) > 0:
            list_of_points = self.calculate_concave_hull_of_points(self.drawingROI.target_pixel_coords)
            if list_of_points is not None:
                self.drawingROI.draw_contour_preview(list_of_points)
            else:
                self.display_multipolygon_warning(self.current_slice)
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

    def on_radius_reduce_clicked(self):
        self.drawingROI.draw_tool_radius = max(self.drawingROI.draw_tool_radius - 1, 4)
        self.draw_roi_window_cursor_radius_change_input.setText(str(self.drawingROI.draw_tool_radius))
        self.draw_roi_window_cursor_radius_change_input.setCursorPosition(0)
        self.draw_cursor_when_radius_changed()

    def on_radius_increase_clicked(self):
        self.drawingROI.draw_tool_radius = min(self.drawingROI.draw_tool_radius + 1, 25)
        self.draw_roi_window_cursor_radius_change_input.setText(str(self.drawingROI.draw_tool_radius))
        self.draw_cursor_when_radius_changed()

    def draw_cursor_when_radius_changed(self):
        if self.drawingROI.cursor:
            self.drawingROI.draw_cursor(self.drawingROI.current_cursor_x + self.drawingROI.draw_tool_radius,
                                        self.drawingROI.current_cursor_y + self.drawingROI.draw_tool_radius)
        else:
            self.drawingROI.draw_cursor((self.drawingROI.min_x + self.drawingROI.max_x) / 2,
                                        (self.drawingROI.min_y + self.drawingROI.max_y) / 2, True)

    def init_cursor_radius_change_box(self):
        # Create a horizontal box for containing the cursor radius changing function
        self.draw_roi_window_cursor_radius_change_box = QHBoxLayout()
        self.draw_roi_window_cursor_radius_change_box.setObjectName("DrawRoiWindowCursorRadiusChangeBox")
        # Create a label for cursor radius change
        self.draw_roi_window_cursor_radius_change_label = QLabel()
        self.draw_roi_window_cursor_radius_change_label.setObjectName("DrawRoiWindowCursorRadiusChangeLabel")
        # Create an input box for cursor radius
        self.draw_roi_window_cursor_radius_change_input = QLineEdit()
        self.draw_roi_window_cursor_radius_change_input.setObjectName("DrawRoiWindowCursorRadiusChangeInput")
        self.draw_roi_window_cursor_radius_change_input.setText(str(19))
        self.draw_roi_window_cursor_radius_change_input.setCursorPosition(0)
        self.draw_roi_window_cursor_radius_change_input.setEnabled(False)
        self.draw_roi_window_cursor_radius_change_input.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.draw_roi_window_cursor_radius_change_input.resize(
            self.draw_roi_window_cursor_radius_change_input.sizeHint().width(),
            self.draw_roi_window_cursor_radius_change_input.sizeHint().height())
        # Create 2 buttons for increasing and reducing cursor radius
        # Increase Button
        self.draw_roi_window_cursor_radius_change_increase_button = QPushButton()
        self.draw_roi_window_cursor_radius_change_increase_button.setObjectName(
            "DrawRoiWindowCursorRadiusIncreaseButton")
        self.draw_roi_window_cursor_radius_change_increase_button.setSizePolicy(
            QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.draw_roi_window_cursor_radius_change_increase_button.resize(QSize(24, 24))
        self.draw_roi_window_cursor_radius_change_increase_button.setProperty("QPushButtonClass", "zoom-button")
        icon_zoom_in = QtGui.QIcon()
        icon_zoom_in.addPixmap(QtGui.QPixmap(resource_path('res/images/btn-icons/zoom_in_icon.png')))
        self.draw_roi_window_cursor_radius_change_increase_button.setIcon(icon_zoom_in)
        self.draw_roi_window_cursor_radius_change_increase_button.clicked.connect(self.on_radius_increase_clicked)
        # Reduce Button
        self.draw_roi_window_cursor_radius_change_reduce_button = QPushButton()
        self.draw_roi_window_cursor_radius_change_reduce_button.setObjectName("DrawRoiWindowCursorRadiusReduceButton")
        self.draw_roi_window_cursor_radius_change_reduce_button.setSizePolicy(
            QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.draw_roi_window_cursor_radius_change_reduce_button.resize(QSize(24, 24))
        self.draw_roi_window_cursor_radius_change_reduce_button.setProperty("QPushButtonClass", "zoom-button")
        icon_zoom_out = QtGui.QIcon()
        icon_zoom_out.addPixmap(QtGui.QPixmap(resource_path('res/images/btn-icons/zoom_out_icon.png')))
        self.draw_roi_window_cursor_radius_change_reduce_button.setIcon(icon_zoom_out)
        self.draw_roi_window_cursor_radius_change_reduce_button.clicked.connect(self.on_radius_reduce_clicked)
        self.draw_roi_window_cursor_radius_change_box.addWidget(self.draw_roi_window_cursor_radius_change_label)
        self.draw_roi_window_cursor_radius_change_box.addWidget(self.draw_roi_window_cursor_radius_change_input)
        self.draw_roi_window_cursor_radius_change_box.addWidget(self.draw_roi_window_cursor_radius_change_reduce_button)
        self.draw_roi_window_cursor_radius_change_box.addWidget(
            self.draw_roi_window_cursor_radius_change_increase_button)
        self.draw_roi_window_input_container_box.addRow(self.draw_roi_window_cursor_radius_change_box)
        self.draw_roi_window_cursor_radius_change_increase_button.setEnabled(False)
        self.draw_roi_window_cursor_radius_change_reduce_button.setEnabled(False)

    def enable_cursor_radius_change_box(self):
        self.draw_roi_window_cursor_radius_change_input.setText(str(19))
        self.draw_roi_window_cursor_radius_change_reduce_button.setEnabled(True)
        self.draw_roi_window_cursor_radius_change_increase_button.setEnabled(True)

    def display_multipolygon_warning(self, slice_id):
        QMessageBox.about(self.draw_roi_window_instance, "Multipolygon detected",
                          "Selected points in slice " + str(slice_id + 1) + " will generate multiple contours, "
                                                                            "which is not currently supported. "
                                                                            "If the region you are drawing is not meant to generate multiple contours, please "
                                                                            "adjust your selected alpha value.")

    def closeWindow(self):
        self.drawn_roi_list = {}
        if hasattr(self, 'bounds_box_draw'):
            delattr(self, 'bounds_box_draw')
        if hasattr(self, 'drawingROI'):
            delattr(self, 'drawingROI')
        self.ds = None
        self.close()
