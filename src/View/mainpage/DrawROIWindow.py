import copy
import csv
import math

import pydicom
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.Qt import Qt
from PyQt5.QtGui import QIcon, QPixmap, QColor, QPen
from PyQt5.QtWidgets import QMessageBox, QHBoxLayout, QLineEdit, QSizePolicy, QPushButton, QDialog, QListWidget, \
    QGraphicsPixmapItem, QGraphicsEllipseItem, QVBoxLayout, QLabel, QWidget

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
        self.target_pixel_coords_single_array = [] # 1D array of above
        self.draw_roi_window_instance = draw_roi_window_instance
        self.colour = None
        self.ds = None

        self.upper_limit = None
        self.lower_limit = None
        self.init_slider()
        self.init_view()
        self.init_metadata()
        self.update_view()
        self.init_layout()
        self.show_ROI_names()

        QtCore.QMetaObject.connectSlotsByName(draw_roi_window_instance)

    def retranslate_ui(self, draw_roi_window_instance):
        _translate = QtCore.QCoreApplication.translate
        draw_roi_window_instance.setWindowTitle(_translate("DrawRoiWindowInstance", "OnkoDICOM - Draw ROI(s)"))
        self.roi_name_label.setText(_translate("ROINameLabel", "Region of Interest: "))
        self.roi_name_line_edit.setText(_translate("ROINameLineEdit", ""))
        self.image_slice_number_label.setText(_translate("ImageSliceNumberLabel", "Image Slice Number: "))
        self.image_slice_number_transect_button.setText(_translate("ImageSliceNumberTransectButton", "Transect"))
        self.image_slice_number_draw_button.setText(_translate("ImageSliceNumberDrawButton", "Draw"))
        self.image_slice_number_move_forward_button.setText(_translate("ImageSliceNumberMoveForwardButton", "Forward"))
        self.image_slice_number_move_backward_button.setText(
            _translate("ImageSliceNumberMoveBackwardButton", "Backward"))
        self.draw_roi_window_instance_save_button.setText(_translate("DrawRoiWindowInstanceSaveButton", "Save"))
        self.internal_hole_max_label.setText(_translate("InternalHoleLabel", "Maximum internal hole size (pixels): "))
        self.internal_hole_max_line_edit.setText(_translate("InternalHoleInput", "9"))
        self.isthmus_width_max_label.setText(_translate("IsthmusWidthLabel", "Maximum isthmus width size (pixels): "))
        self.isthmus_width_max_line_edit.setText(_translate("IsthmusWidthInput", "5"))
        self.min_pixel_density_label.setText(_translate("MinPixelDensityLabel", "Minimum density (pixels): "))
        self.min_pixel_density_line_edit.setText(_translate("MinPixelDensityInput", ""))
        self.max_pixel_density_label.setText(_translate("MaxPixelDensityLabel", "Maximum density (pixels): "))
        self.max_pixel_density_line_edit.setText(_translate("MaxPixelDensityInput", ""))
        self.draw_roi_window_instance_action_reset_button.setText(
            _translate("DrawRoiWindowInstanceActionClearButton", "Reset"))
        # self.draw_roi_window_instance_action_tool_button.setText(
        #     _translate("DrawRoiWindowInstanceActionToolButton", "Tool"))
        # self.draw_roi_window_instance_action_go_button.setText(
        #     _translate("DrawRoiWindowInstanceActionGoButton", "Go"))




    def init_view(self):
        """
        Create a view widget for DICOM image.
        """
        self.view = QtWidgets.QGraphicsView()
        # Add antialiasing and smoothing when zooming in
        self.view.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.SmoothPixmapTransform)
        background_brush = QtGui.QBrush(QtGui.QColor(0, 0, 0), QtCore.Qt.SolidPattern)
        self.view.setBackgroundBrush(background_brush)
        self.view.setGeometry(QtCore.QRect(0, 0, 877, 517))
        # Set event filter on the DICOM View area
        self.view.viewport().installEventFilter(self.draw_roi_window_instance)

        # Create a line edit for containing the image slice number
        self.image_slice_number_line_edit = QLineEdit()
        self.image_slice_number_line_edit.setObjectName("ImageSliceNumberLineEdit")
        self.image_slice_number_line_edit.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.image_slice_number_line_edit.resize(self.image_slice_number_line_edit.sizeHint().width(),
                                                 self.image_slice_number_line_edit.sizeHint().height())
        self.image_slice_number_line_edit.setEnabled(False)

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

        # Creating a vertical box to hold the details
        self.draw_roi_window_instance_vertical_box = QVBoxLayout()

        self.draw_roi_window_instance_vertical_box.setObjectName("DrawRoiWindowInstanceVerticalBox")

        # Creating a horizontal box to hold the image slice number, move up and down the image slice  and save button
        self.draw_roi_window_instance_image_slice_action_box = QHBoxLayout()
        self.draw_roi_window_instance_image_slice_action_box.setObjectName("DrawRoiWindowInstanceImageSliceActionBox")

        # Create a label for denoting the ROI name
        self.roi_name_label = QLabel()
        self.roi_name_label.setObjectName("ROINameLabel")
        self.roi_name_label.setAlignment(Qt.AlignLeft)
        self.roi_name_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.roi_name_label.resize(
            self.roi_name_label.sizeHint().width(), self.roi_name_label.sizeHint().height())
        self.draw_roi_window_instance_image_slice_action_box.addWidget(self.roi_name_label)

        self.roi_name_line_edit = QLineEdit()
        self.roi_name_line_edit.setObjectName("ROINameLineEdit")
        self.roi_name_line_edit.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.roi_name_line_edit.resize(self.roi_name_line_edit.sizeHint().width(),
                                       self.roi_name_line_edit.sizeHint().height())
        self.roi_name_line_edit.setEnabled(False)
        self.draw_roi_window_instance_image_slice_action_box.addWidget(self.roi_name_line_edit)

        # Create a label for denoting the Image Slice Number
        self.image_slice_number_label = QLabel()
        self.image_slice_number_label.setObjectName("ImageSliceNumberLabel")
        self.image_slice_number_label.setAlignment(Qt.AlignRight)
        self.image_slice_number_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.image_slice_number_label.resize(
            self.image_slice_number_label.sizeHint().width(), self.image_slice_number_label.sizeHint().height())
        self.draw_roi_window_instance_image_slice_action_box.addStretch(1)
        self.draw_roi_window_instance_image_slice_action_box.addWidget(self.image_slice_number_label)

        self.draw_roi_window_instance_image_slice_action_box.addWidget(self.image_slice_number_line_edit)

        # Create a button to move backward to the previous image
        self.image_slice_number_move_backward_button = QPushButton()
        self.image_slice_number_move_backward_button.setObjectName("ImageSliceNumberMoveBackwardButton")
        self.image_slice_number_move_backward_button.setSizePolicy(
            QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum))
        self.image_slice_number_move_backward_button.resize(
            self.image_slice_number_move_backward_button.sizeHint().width(),
            self.image_slice_number_move_backward_button.sizeHint().height())

        self.image_slice_number_move_backward_button.clicked.connect(self.on_backward_clicked)
        self.draw_roi_window_instance_image_slice_action_box.addWidget(self.image_slice_number_move_backward_button)

        # Create a button to move forward to the next image
        self.image_slice_number_move_forward_button = QPushButton()
        self.image_slice_number_move_forward_button.setObjectName("ImageSliceNumberMoveForwardButton")
        self.image_slice_number_move_forward_button.setSizePolicy(
            QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum))
        self.image_slice_number_move_forward_button.resize(
            self.image_slice_number_move_forward_button.sizeHint().width(),
            self.image_slice_number_move_forward_button.sizeHint().height())
        self.image_slice_number_move_forward_button.clicked.connect(self.on_forward_clicked)
        self.draw_roi_window_instance_image_slice_action_box.addWidget(self.image_slice_number_move_forward_button)

        # Create a transect button
        self.image_slice_number_transect_button = QPushButton()
        self.image_slice_number_transect_button.setObjectName("ImageSliceNumberTransectButton")
        self.image_slice_number_transect_button.setSizePolicy(
            QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum))
        self.image_slice_number_transect_button.resize(
            self.image_slice_number_transect_button.sizeHint().width(),
            self.image_slice_number_transect_button.sizeHint().height())
        self.image_slice_number_transect_button.clicked.connect(self.transect_handler)
        self.draw_roi_window_instance_image_slice_action_box.addWidget(self.image_slice_number_transect_button)

        # Create a draw button
        self.image_slice_number_draw_button = QPushButton()
        self.image_slice_number_draw_button.setObjectName("ImageSliceNumberDrawButton")
        self.image_slice_number_draw_button.setSizePolicy(
            QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum))
        self.image_slice_number_transect_button.resize(
            self.image_slice_number_draw_button.sizeHint().width(),
            self.image_slice_number_draw_button.sizeHint().height())
        self.image_slice_number_draw_button.clicked.connect(self.on_draw_clicked)
        self.draw_roi_window_instance_image_slice_action_box.addWidget(self.image_slice_number_draw_button)

        # Create a save button to save all the changes
        self.draw_roi_window_instance_save_button = QPushButton()
        self.draw_roi_window_instance_save_button.setObjectName("DrawRoiWindowInstanceSaveButton")
        self.draw_roi_window_instance_save_button.setSizePolicy(
            QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum))
        self.draw_roi_window_instance_save_button.resize(
            self.draw_roi_window_instance_save_button.sizeHint().width(),
            self.draw_roi_window_instance_save_button.sizeHint().height())
        self.draw_roi_window_instance_save_button.setProperty("QPushButtonClass", "success-button")
        self.draw_roi_window_instance_image_slice_action_box.addStretch(1)
        self.draw_roi_window_instance_save_button.clicked.connect(self.on_save_clicked)
        self.draw_roi_window_instance_image_slice_action_box.addWidget(self.draw_roi_window_instance_save_button)

        # Create a widget to hold the image slice box
        self.draw_roi_window_instance_image_slice_action_widget = QWidget()
        self.draw_roi_window_instance_image_slice_action_widget.setObjectName(
            "DrawRoiWindowInstanceImageSliceActionWidget")
        self.draw_roi_window_instance_image_slice_action_widget.setLayout(
            self.draw_roi_window_instance_image_slice_action_box)
        self.draw_roi_window_instance_vertical_box.addWidget(self.draw_roi_window_instance_image_slice_action_widget)
        self.draw_roi_window_instance_vertical_box.setStretch(0, 1)

        # Create a new Label to hold the pixmap
        # self.image_slice_number_image_view = QLabel()
        # self.image_slice_number_image_view.setPixmap(QPixmap("src/res/images/Capture.png"))
        # self.image_slice_number_image_view.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        # self.image_slice_number_image_view.resize(
        #   self.image_slice_number_image_view.sizeHint().width(), self.image_slice_number_image_view.sizeHint().height())
        # self.draw_roi_window_instance_vertical_box.addWidget(self.image_slice_number_image_view)
        # self.draw_roi_window_instance_vertical_box.setStretch(1, 4)

        # Creating a horizontal box to hold the ROI view and slider
        self.draw_roi_window_instance_view_box = QHBoxLayout()
        self.draw_roi_window_instance_view_box.setObjectName("DrawRoiWindowInstanceActionBox")

        # Add View and Slider into horizontal box
        self.draw_roi_window_instance_view_box.addWidget(self.view)
        self.draw_roi_window_instance_view_box.addWidget(self.slider)

        # # Creating a horizontal box to hold the ROI draw action buttons: clear, tool
        self.draw_roi_window_instance_action_box = QHBoxLayout()
        self.draw_roi_window_instance_action_box.setObjectName("DrawRoiWindowInstanceActionBox")

        # Creating a horizontal box to hold the ROI draw min and max pixel density
        self.draw_roi_window_instance_action_box_2 = QHBoxLayout()
        self.draw_roi_window_instance_action_box_2.setObjectName("DrawRoiWindowInstanceActionBox")

        # Create a label for denoting the internal hole size
        self.internal_hole_max_label = QLabel()
        self.internal_hole_max_label.setObjectName("InternalHoleLabel")
        self.internal_hole_max_label.setAlignment(Qt.AlignLeft)
        self.internal_hole_max_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.internal_hole_max_label.resize(
            self.internal_hole_max_label.sizeHint().width(), self.internal_hole_max_label.sizeHint().height())
        self.draw_roi_window_instance_action_box.addWidget(self.internal_hole_max_label)

        # Create input for max internal hole size
        self.internal_hole_max_line_edit = QLineEdit()
        self.internal_hole_max_line_edit.setObjectName("InternalHoleInput")
        self.internal_hole_max_line_edit.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.internal_hole_max_line_edit.resize(self.internal_hole_max_line_edit.sizeHint().width(),
                                       self.internal_hole_max_line_edit.sizeHint().height())
        self.internal_hole_max_line_edit.setEnabled(True)
        self.draw_roi_window_instance_action_box.addWidget(self.internal_hole_max_line_edit)

        # Create a label for denoting the isthmus width size
        self.isthmus_width_max_label = QLabel()
        self.isthmus_width_max_label.setObjectName("IsthmusWidthLabel")
        self.isthmus_width_max_label.setAlignment(Qt.AlignLeft)
        self.isthmus_width_max_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.isthmus_width_max_label.resize(
            self.isthmus_width_max_label.sizeHint().width(), self.isthmus_width_max_label.sizeHint().height())
        self.draw_roi_window_instance_action_box.addWidget(self.isthmus_width_max_label)

        # Create input for max isthmus width size
        self.isthmus_width_max_line_edit = QLineEdit()
        self.isthmus_width_max_line_edit.setObjectName("IsthmusWidthInput")
        self.isthmus_width_max_line_edit.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.isthmus_width_max_line_edit.resize(self.isthmus_width_max_line_edit.sizeHint().width(),
                                                self.isthmus_width_max_line_edit.sizeHint().height())
        self.isthmus_width_max_line_edit.setEnabled(True)
        self.draw_roi_window_instance_action_box.addWidget(self.isthmus_width_max_line_edit)

        # Create a label for denoting the minimum pixel density
        self.min_pixel_density_label = QLabel()
        self.min_pixel_density_label.setObjectName("MinPixelDensityLabel")
        self.min_pixel_density_label.setAlignment(Qt.AlignLeft)
        self.min_pixel_density_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.min_pixel_density_label.resize(
            self.min_pixel_density_label.sizeHint().width(), self.min_pixel_density_label.sizeHint().height())
        self.draw_roi_window_instance_action_box.addWidget(self.min_pixel_density_label)


        # Create input for min pixel size
        self.min_pixel_density_line_edit = QLineEdit()
        self.min_pixel_density_line_edit.setObjectName("MinPixelDensityInput")
        self.min_pixel_density_line_edit.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.min_pixel_density_line_edit.resize(self.min_pixel_density_line_edit.sizeHint().width(),
                                                self.min_pixel_density_line_edit.sizeHint().height())
        self.min_pixel_density_line_edit.setEnabled(True)
        self.draw_roi_window_instance_action_box.addWidget(self.min_pixel_density_line_edit)

        # Create a label for denoting the minimum pixel density
        self.max_pixel_density_label = QLabel()
        self.max_pixel_density_label.setObjectName("MaxPixelDensityLabel")
        self.max_pixel_density_label.setAlignment(Qt.AlignLeft)
        self.max_pixel_density_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.max_pixel_density_label.resize(
            self.max_pixel_density_label.sizeHint().width(), self.max_pixel_density_label.sizeHint().height())
        self.draw_roi_window_instance_action_box.addWidget(self.max_pixel_density_label)

        # Create input for min pixel size
        self.max_pixel_density_line_edit = QLineEdit()
        self.max_pixel_density_line_edit.setObjectName("MaxPixelDensityInput")
        self.max_pixel_density_line_edit.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.max_pixel_density_line_edit.resize(self.max_pixel_density_line_edit.sizeHint().width(),
                                                self.max_pixel_density_line_edit.sizeHint().height())
        self.max_pixel_density_line_edit.setEnabled(True)
        self.draw_roi_window_instance_action_box.addWidget(self.max_pixel_density_line_edit)

        # Place buttons to the right of the screen
        self.draw_roi_window_instance_action_box.addStretch(1)

        # Create a button to clear the draw
        self.draw_roi_window_instance_action_reset_button = QPushButton()
        self.draw_roi_window_instance_action_reset_button.setObjectName("DrawRoiWindowInstanceActionClearButton")
        self.draw_roi_window_instance_action_reset_button.setSizePolicy(
            QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum))
        self.draw_roi_window_instance_action_reset_button.resize(
            self.draw_roi_window_instance_action_reset_button.sizeHint().width(),
            self.draw_roi_window_instance_action_reset_button.sizeHint().height())
        self.draw_roi_window_instance_action_reset_button.clicked.connect(self.on_reset_clicked)
        self.draw_roi_window_instance_action_box.addWidget(self.draw_roi_window_instance_action_reset_button)

        # # Create a button to tool the draw
        # self.draw_roi_window_instance_action_tool_button = QPushButton()
        # self.draw_roi_window_instance_action_tool_button.setObjectName("DrawRoiWindowInstanceActionToolButton")
        # self.draw_roi_window_instance_action_tool_button.setSizePolicy(
        #     QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum))
        # self.draw_roi_window_instance_action_tool_button.resize(
        #     self.draw_roi_window_instance_action_tool_button.sizeHint().width(),
        #     self.draw_roi_window_instance_action_tool_button.sizeHint().height())
        # self.draw_roi_window_instance_action_tool_button.clicked.connect(self.on_tool_clicked)
        # self.draw_roi_window_instance_action_box.addWidget(self.draw_roi_window_instance_action_tool_button)

        # Create a button for running seed algorithm
        # self.draw_roi_window_instance_action_go_button = QPushButton()
        # self.draw_roi_window_instance_action_go_button.setObjectName("DrawRoiWindowInstanceActionGoButton")
        # self.draw_roi_window_instance_action_go_button.setSizePolicy(
        #     QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum))
        # self.draw_roi_window_instance_action_go_button.resize(
        #     self.draw_roi_window_instance_action_go_button.sizeHint().width(),
        #     self.draw_roi_window_instance_action_go_button.sizeHint().height())
        # self.draw_roi_window_instance_action_go_button.clicked.connect(self.on_go_clicked)
        # self.draw_roi_window_instance_action_box.addWidget(self.draw_roi_window_instance_action_go_button)

        # Create a widget to hold the image slice box
        self.draw_roi_window_instance_view_widget = QWidget()
        self.draw_roi_window_instance_view_widget.setObjectName(
            "DrawRoiWindowInstanceActionWidget")
        self.draw_roi_window_instance_view_widget.setLayout(
            self.draw_roi_window_instance_view_box)
        self.draw_roi_window_instance_vertical_box.addWidget(self.draw_roi_window_instance_view_widget)
        self.draw_roi_window_instance_vertical_box.setStretch(0, 1)

        # Create a widget to hold the image slice box
        self.draw_roi_window_instance_action_widget = QWidget()
        self.draw_roi_window_instance_action_widget.setObjectName(
            "DrawRoiWindowInstanceActionWidget")
        self.draw_roi_window_instance_action_widget.setLayout(
            self.draw_roi_window_instance_action_box)
        self.draw_roi_window_instance_vertical_box.addWidget(self.draw_roi_window_instance_action_widget)
        self.draw_roi_window_instance_vertical_box.setStretch(0, 1)

        # Create a new central widget to hold the vertical box layout
        self.draw_roi_window_instance_central_widget = QWidget()
        self.draw_roi_window_instance_central_widget.setObjectName("DrawRoiWindowInstanceCentralWidget")
        self.draw_roi_window_instance_central_widget.setLayout(self.draw_roi_window_instance_vertical_box)

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

        #PyQt5.QtGui.QPixMap objects
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

        # For formatting
        zoom = 1

        self.text_imageID.setText(_translate("MainWindow", "Image: " + str(current_slice) + " / " + str(total_slices)))
        self.text_imagePos.setText(_translate("MainWindow", "Position: " + str(slice_pos) + " mm"))
        self.text_WL.setText(_translate("MainWindow", "W/L: " + str(window) + "/" + str(level)))
        self.text_imageSize.setText(_translate("MainWindow", "Image Size: " + str(row_img) + "x" + str(col_img) + "px"))
        self.text_zoom.setText(_translate("MainWindow", "Zoom: " + str(zoom) + ":" + str(zoom)))
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
            QMessageBox.about(self.draw_roi_window_instance, "Not Enough Data", "Not all values are specified or correct.")
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
                    self.view,
                    min_pixel,
                    max_pixel,
                    self.patient_dict_container.dataset[id],
                    self.draw_roi_window_instance
                )
                self.view.setScene(self.drawingROI)

            else:
                QMessageBox.about(self.draw_roi_window_instance, "Not Enough Data", "Not all values are specified or correct.")

    def on_save_clicked(self):
        # Make sure the user has clicked Draw first
        if self.ds is not None:
            new_rtss = ROI.create_roi(self.dataset_rtss, self.ROI_name, self.target_pixel_coords_single_array, self.ds)
            self.signal_roi_drawn.emit((new_rtss, {"draw": self.ROI_name}))
            QMessageBox.about(self.draw_roi_window_instance, "Success",
                              "New ROI has been saved to RTSS!")
            self.close()
        else:
            QMessageBox.about(self.draw_roi_window_instance, "Not Enough Data",
                              "Please ensure you have drawn your ROI first.")

        print(new_rtss)


    def init_standard_names(self):
        """
        Create two lists containing standard organ and standard volume names as set by the Add-On options.
        """
        with open('src/data/csv/organName.csv', 'r') as f:
            self.standard_organ_names = []

            csv_input = csv.reader(f)
            header = next(f)  # Ignore the "header" of the column
            for row in csv_input:
                self.standard_organ_names.append(row[0])

        with open('src/data/csv/volumeName.csv', 'r') as f:
            self.standard_volume_names = []

            csv_input = csv.reader(f)
            header = next(f)  # Ignore the "header" of the column
            for row in csv_input:
                self.standard_volume_names.append(row[1])

        self.standard_names = self.standard_organ_names + self.standard_volume_names

    def show_ROI_names(self):
        self.init_standard_names()
        self.select_ROI = SelectROIPopUp(self.standard_names, self.draw_roi_window_instance)
        self.select_ROI.exec_()

    def set_selected_roi_name(self, roi_name):
        self.ROI_name = roi_name
        self.roi_name_line_edit.setText(self.ROI_name)

#####################################################################################################################
#                                                                                                                   #
#  This Class handles the ROI Pop Up functionalities                                                                    #
#                                                                                                                   #
#####################################################################################################################
class SelectROIPopUp(QDialog):
    parent_window = None

    def __init__(self, standard_names, parent_window):
        super(SelectROIPopUp, self).__init__()
        self.parent_window = parent_window
        QDialog.__init__(self)

        stylesheet = open("src/res/stylesheet.qss").read()
        self.setStyleSheet(stylesheet)
        self.standard_names = standard_names

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
            UIDrawROIWindow.set_selected_roi_name(self.parent_window, self.roi_name)
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
    def __init__(self, imagetoPaint, pixmapdata, tabWindow, min_pixel, max_pixel, dataset, draw_roi_window_instance):
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
        self.tabWindow = tabWindow
        self.rect = QtCore.QRect(250,300,20,20)
        self.update()
        self._points = {}
        self._circlePoints = []
        self.drag_position = QtCore.QPoint()
        self.item = None
        self.isPressed = False
        self.dataset = dataset
        self.pixel_array = None
        # This will contain the new pixel coordinates specifed by the min and max pixel density
        self.target_pixel_coords = []
        self.pixel_coords_remove = []
        self.accordingColorList = []
        self.q_image = None
        self.q_image = None
        self.q_pixmaps = None
        self.label = QtWidgets.QLabel()
        self._display_pixel_color()

    def _display_pixel_color(self):
        if self.min_pixel <= self.max_pixel:
            data_set = self.dataset

            """
            pixel_array is a 2-Dimensional array containing all pixel coordinates of the q_image. 
            pixel_array[x][y] will return the density of the pixel
            """
            z_coord = int(data_set.SliceLocation)
            self.pixel_array = data_set._pixel_array
            self.q_image = self.img.toImage()

            for x_coord in range(512):
                for y_coord in range(512):
                    if (self.pixel_array[x_coord][y_coord] >= self.min_pixel) and (
                            self.pixel_array[x_coord][y_coord] <= self.max_pixel):
                                self.target_pixel_coords.append((y_coord, x_coord))

            """
                pixel_array is a 2-Dimensional array containing all pixel coordinates of the q_image. 
                pixel_array[x][y] will return the density of the pixel
            """

            self.draw_roi_window_instance.target_pixel_coords = [ (item[0], item[1], z_coord) for item in self.target_pixel_coords]
            # Make 2D to 1D
            self.draw_roi_window_instance.target_pixel_coords_single_array.clear()
            for sublist in self.draw_roi_window_instance.target_pixel_coords:
                for item in sublist:
                    self.draw_roi_window_instance.target_pixel_coords_single_array.append(item)

            print(self.draw_roi_window_instance.target_pixel_coords_single_array)


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

    # This function is for if we want to choose and drag the circle
    def _find_neighbor_point(self, event):
        u""" Find point around mouse position
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

    # This function gets the corresponding values of all the points in the drawn line from the dataset
    def getValues(self):
        for i in range(512):
            for j in range(512):
                self.values.append(self.data[i][j])

    def calculate_circle_points(self, x , y, r):
        self._circlePoints.clear()
        degree = math.pi/8
        for i in range(300):
            x1 = round(x + 19*math.cos(degree))
            y1 = round(y + 19*math.sin(degree))
            degree = degree + 1/44
            self._circlePoints.append((x1, y1))

    def compare(self):
        for x_coord, y_coord, colors in self.accordingColorList[:]:
            for xc_coord, yc_coord in self._circlePoints[:]:
                if (x_coord == xc_coord and y_coord == yc_coord):
                    self.q_image.setPixelColor(x_coord, y_coord, QColor.fromRgbF(colors[0], colors[1], colors[2], colors[3]))
                    self.pixel_coords_remove.append((x_coord, y_coord))

        self.q_pixmaps = QtGui.QPixmap.fromImage(self.q_image)
        self.label.setPixmap(self.q_pixmaps)
        self.addWidget(self.label)

    def update_data(self):
        if self.min_pixel <= self.max_pixel:
            data_set = self.dataset
            z_coord = int(data_set.SliceLocation)
            """
                pixel_array is a 2-Dimensional array containing all pixel coordinates of the q_image. 
                pixel_array[x][y] will return the density of the pixel
            """
            self.draw_roi_window_instance.target_pixel_coords = [ (item[0], item[1], z_coord) for item in self.target_pixel_coords if item not in self.pixel_coords_remove]

            # Make 2D to 1D
            self.draw_roi_window_instance.target_pixel_coords_single_array.clear()
            for sublist in self.draw_roi_window_instance.target_pixel_coords:
                for item in sublist:
                    self.draw_roi_window_instance.target_pixel_coords_single_array.append(item)

    def wheelEvent(self, event):
        delta = event.delta()

    def mousePressEvent(self, event):
        if self.item:
            self.removeItem(self.item)
        self.isPressed = True
        if (
                2 * QtGui.QVector2D(event.pos() - self.rect.center()).length()
                < self.rect.width()
        ):
            self.drag_position = event.pos() - self.rect.topLeft()
        super().mousePressEvent(event)
        # event.scenePos().x() - 5, event.scenePos().y() - 5
        # event.scenePos().x() - 33, event.scenePos().y() - 33
        x = event.scenePos().x() - 19
        y = event.scenePos().y() - 19
        r = 19
        self.calculate_circle_points(x + 19, y + 19, r)
        #  x = a + r .cos(t), y = b+r.sin(t)
        self.item = QGraphicsEllipseItem(event.scenePos().x() - 19, event.scenePos().y() - 19, 40, 40)
        self.item.setPen(QPen(QColor("blue")))
        self.addItem(self.item)
        self.compare()
        self.update()

    def mouseMoveEvent(self, event):
        if not self.drag_position.isNull():
            self.rect.moveTopLeft(event.pos() - self.drag_position)
        super().mouseMoveEvent(event)
        if self.item and self.isPressed:
            r = 19
            x = event.scenePos().x() - r
            y = event.scenePos().y() - r
            self.calculate_circle_points(x + r, y + r, r)
            self.compare()
            self.item.setRect(event.scenePos().x() - r, event.scenePos().y() - r, 40, 40)
        self.update()

    def mouseReleaseEvent(self, event):
        self.isPressed = False
        self.drag_position = QtCore.QPoint()
        super().mouseReleaseEvent(event)
        self.update_data()
        self.update()
