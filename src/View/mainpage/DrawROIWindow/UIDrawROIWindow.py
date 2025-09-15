import logging

import pydicom
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, QSize, QRegularExpression, Slot, Signal, QThread
from PySide6.QtGui import QIcon, QPixmap, QRegularExpressionValidator
from PySide6.QtWidgets import QFormLayout, QLabel, QLineEdit, \
    QSizePolicy, QHBoxLayout, QPushButton, QWidget, \
    QMessageBox, QSlider

from src.Controller.MainPageController import MainPageCallClass
from src.Controller.PathHandler import resource_path, data_path
from src.Model import ROI
from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.ROI import calculate_concave_hull_of_points
from src.View.ProgressWindow import ProgressWindow
from src.View.StyleSheetReader import StyleSheetReader
from src.View.mainpage.DicomAxialView import DicomAxialView
from src.View.mainpage.DrawROIWindow.DrawBoundingBox import DrawBoundingBox
from src.View.mainpage.DrawROIWindow.Drawing import Drawing
from src.View.mainpage.DrawROIWindow.SelectROIPopUp import SelectROIPopUp
from src.View.util.ProgressWindowHelper import connectSaveROIProgress
from src.constants import INITIAL_DRAWING_TOOL_RADIUS


class UIDrawROIWindow:
    is_drawing = Signal(bool)

    def setup_ui(self, draw_roi_window_instance,
                 rois, dataset_rtss, signal_roi_drawn, signal_draw_roi_closed):
        """
        this function is responsible for setting up the UI
        for DrawROIWindow
        param draw_roi_window_instance: the current drawing
        window instance.
        :param rois: the rois to be drawn
        :param dataset_rtss: the rtss to be written to
        :param signal_roi_drawn: the signal to be triggered
        when roi is drawn
        """
        self.patient_dict_container = PatientDictContainer()

        self.rois = rois
        self.dataset_rtss = dataset_rtss
        self.signal_roi_drawn = signal_roi_drawn
        self.signal_draw_roi_closed = signal_draw_roi_closed
        self.drawn_roi_list = {}
        self.standard_organ_names = []
        self.standard_volume_names = []
        self.standard_names = []  # Combination of organ and volume
        self.ROI_name = None  # Selected ROI name
        self.target_pixel_coords = []  # This will contain the new pixel
        # coordinates specified by the min and max
        self.drawingROI = None
        self.slice_changed = False
        self.drawing_tool_radius = INITIAL_DRAWING_TOOL_RADIUS
        self.keep_empty_pixel = True  # This constant will not change
        # pixel density
        self.target_pixel_coords_single_array = []  # 1D array
        self.draw_roi_window_instance = draw_roi_window_instance
        self.colour = None
        self.ds = None
        self.zoom = 1.0
        self.pixel_transparency = 0.50
        self.has_drawing = False

        self.upper_limit = None
        self.lower_limit = None

        # is_four_view is set to True to stop the SUV2ROI button from appearing
        self.dicom_view = DicomAxialView(is_four_view=True)
        self.current_slice = self.dicom_view.slider.value()
        self.dicom_view.slider.valueChanged.connect(self.slider_value_changed)
        self.init_layout()

        QtCore.QMetaObject.connectSlotsByName(draw_roi_window_instance)

    def retranslate_ui(self, draw_roi_window_instance):
        """
            this function retranslate the ui for draw roi window

            :param draw_roi_window_instance: the current drawing
            window instance.
            """
        _translate = QtCore.QCoreApplication.translate
        draw_roi_window_instance.setWindowTitle(
            _translate("DrawRoiWindowInstance",
                       "OnkoDICOM - Draw Region Of Interest"))
        self.roi_name_label.setText(_translate("ROINameLabel",
                                               "Region of Interest: "))
        self.select_roi_type.setText(_translate("SelectRoiTypeButton", "Select ROI"))
        self.image_slice_number_label.setText(
            _translate("ImageSliceNumberLabel", "Slice Number: "))
        self.image_slice_number_line_edit.setText(
            _translate("ImageSliceNumberLineEdit",
                       str(self.dicom_view.current_slice_number)))
        self.image_slice_number_transect_button.setText(
            _translate("ImageSliceNumberTransectButton", "Transect"))
        self.image_slice_number_box_draw_button.setText(
            _translate("ImageSliceNumberBoxDrawButton", "Set Bounds"))
        self.image_slice_number_draw_button.setText(
            _translate("ImageSliceNumberDrawButton", "Draw"))
        self.image_slice_number_clear_button.setText(
            _translate("ImageSliceNumberClearButton", "Clear"))
        self.image_slice_number_fill_button.setText(
            _translate("ImageSliceNumberFillButton", "Fill"))
        self.image_slice_number_move_forward_button.setText(
            _translate("ImageSliceNumberMoveForwardButton", ""))
        self.image_slice_number_move_backward_button.setText(
            _translate("ImageSliceNumberMoveBackwardButton", ""))
        self.draw_roi_window_instance_save_button.setText(
            _translate("DrawRoiWindowInstanceSaveButton", "Save"))
        self.draw_roi_window_instance_cancel_button.setText(
            _translate("DrawRoiWindowInstanceCancelButton", "Cancel"))
        self.internal_hole_max_label.setText(
            _translate("InternalHoleLabel",
                       "Maximum internal hole size (pixels): "))
        self.internal_hole_max_line_edit.setText(
            _translate("InternalHoleInput", "5"))
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
        self.transparency_slider_label.setText(
            _translate("TransparencySliderLabel", "Transparency:"))

        self.draw_roi_window_viewport_zoom_label.setText(
            _translate("DrawRoiWindowViewportZoomLabel", "Zoom: "))
        self.draw_roi_window_cursor_diameter_change_label.setText(
            _translate("DrawRoiWindowCursorDiameterChangeLabel",
                       "Cursor Diameter: "))

        self.draw_roi_window_instance_action_reset_button.setText(
            _translate("DrawRoiWindowInstanceActionClearButton", "Reset"))

    def init_layout(self):
        """
        Initialize the layout for the DICOM View tab.
        Add the view widget and the slider in the layout.
        Add the whole container 'tab2_view' as a tab in the main page.
        """

        # Initialise a DrawROIWindow
        window_icon = QIcon()
        window_icon.addPixmap(QPixmap(resource_path("res/images/icon.ico")),
                              QIcon.Normal, QIcon.Off)
        self.draw_roi_window_instance.setObjectName("DrawRoiWindowInstance")
        self.draw_roi_window_instance.setWindowIcon(window_icon)

        # Creating a form box to hold all buttons and input fields
        self.draw_roi_window_input_container_box = QFormLayout()
        self.draw_roi_window_input_container_box. \
            setObjectName("DrawRoiWindowInputContainerBox")
        self.draw_roi_window_input_container_box. \
            setLabelAlignment(Qt.AlignLeft)

        # Create a label for denoting the ROI name
        self.roi_name_label = QLabel()
        self.roi_name_label.setObjectName("ROINameLabel")

        # Create a select ROI button
        self.select_roi_type = QPushButton()
        self.select_roi_type. \
            setObjectName("SelectRoiTypeButton")
        self.select_roi_type.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum))
        self.select_roi_type.resize(
            self.select_roi_type.sizeHint().width(),
            self.select_roi_type.sizeHint().height())
        self.select_roi_type. \
            setProperty("QPushButtonClass", "draw-roi-button")
        self.select_roi_type.clicked.connect(self.show_roi_type_options)

        self.draw_roi_window_input_container_box. \
            addRow(self.roi_name_label, self.select_roi_type)

        # Create horizontal box to store image slice number and backward,
        # forward buttons
        self.image_slice_number_box = QHBoxLayout()
        self.image_slice_number_box.setObjectName("ImageSliceNumberBox")

        # Create a label for denoting the Image Slice Number
        self.image_slice_number_label = QLabel()
        self.image_slice_number_label.setObjectName("ImageSliceNumberLabel")
        self.image_slice_number_box.addWidget(self.image_slice_number_label)
        # Create a line edit for containing the image slice number
        self.image_slice_number_line_edit = QLineEdit()
        self.image_slice_number_line_edit. \
            setObjectName("ImageSliceNumberLineEdit")
        self.image_slice_number_line_edit. \
            setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.image_slice_number_line_edit.resize(
            self.image_slice_number_line_edit.sizeHint().width(),
            self.image_slice_number_line_edit.sizeHint().height())
        self.image_slice_number_line_edit.setCursorPosition(0)
        self.image_slice_number_line_edit.setEnabled(False)
        self.image_slice_number_box. \
            addWidget(self.image_slice_number_line_edit)
        # Create a button to move backward to the previous image
        self.image_slice_number_move_backward_button = QPushButton()
        self.image_slice_number_move_backward_button. \
            setObjectName("ImageSliceNumberMoveBackwardButton")
        self.image_slice_number_move_backward_button.setSizePolicy(
            QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.image_slice_number_move_backward_button.resize(QSize(24, 24))
        self.image_slice_number_move_backward_button. \
            setProperty("QPushButtonClass", "draw-roi-button")
        self.image_slice_number_move_backward_button.clicked. \
            connect(self.onBackwardClicked)
        icon_move_backward = QtGui.QIcon()
        icon_move_backward.addPixmap(QtGui.QPixmap(
            resource_path('res/images/btn-icons/backward_slide_icon.png')))
        self.image_slice_number_move_backward_button.setIcon(
            icon_move_backward)
        self.image_slice_number_box. \
            addWidget(self.image_slice_number_move_backward_button)
        # Create a button to move forward to the next image
        self.image_slice_number_move_forward_button = QPushButton()
        self.image_slice_number_move_forward_button. \
            setObjectName("ImageSliceNumberMoveForwardButton")
        self.image_slice_number_move_forward_button.setSizePolicy(
            QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.image_slice_number_move_forward_button.resize(QSize(24, 24))
        self.image_slice_number_move_forward_button. \
            setProperty("QPushButtonClass", "draw-roi-button")
        self.image_slice_number_move_forward_button.clicked. \
            connect(self.onForwardClicked)
        icon_move_forward = QtGui.QIcon()
        icon_move_forward.addPixmap(QtGui.QPixmap(
            resource_path('res/images/btn-icons/forward_slide_icon.png')))
        self.image_slice_number_move_forward_button.setIcon(icon_move_forward)
        self.image_slice_number_box. \
            addWidget(self.image_slice_number_move_forward_button)

        self.draw_roi_window_input_container_box. \
            addRow(self.image_slice_number_box)

        # Create a horizontal box for containing the zoom function
        self.draw_roi_window_viewport_zoom_box = QHBoxLayout()
        self.draw_roi_window_viewport_zoom_box.setObjectName(
            "DrawRoiWindowViewportZoomBox")
        # Create a label for zooming
        self.draw_roi_window_viewport_zoom_label = QLabel()
        self.draw_roi_window_viewport_zoom_label. \
            setObjectName("DrawRoiWindowViewportZoomLabel")
        # Create an input box for zoom factor
        self.draw_roi_window_viewport_zoom_input = QLineEdit()
        self.draw_roi_window_viewport_zoom_input. \
            setObjectName("DrawRoiWindowViewportZoomInput")
        self.draw_roi_window_viewport_zoom_input. \
            setText("{:.2f}".format(self.zoom * 100) + "%")
        self.draw_roi_window_viewport_zoom_input.setCursorPosition(0)
        self.draw_roi_window_viewport_zoom_input.setEnabled(False)
        self.draw_roi_window_viewport_zoom_input. \
            setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.draw_roi_window_viewport_zoom_input.resize(
            self.draw_roi_window_viewport_zoom_input.sizeHint().width(),
            self.draw_roi_window_viewport_zoom_input.sizeHint().height())
        # Create a slider for zooming in and out
        self.draw_roi_zoom_slider = QSlider(Qt.Horizontal)
        self.draw_roi_zoom_slider.setMinimum(50)
        self.draw_roi_zoom_slider.setMaximum(2050)
        self.draw_roi_zoom_slider.setSingleStep(10)
        self.draw_roi_zoom_slider.setTickPosition(QSlider.TicksBothSides)
        self.draw_roi_zoom_slider.setTickInterval(100)
        self.draw_roi_zoom_slider.setValue(100)
        self.draw_roi_zoom_slider.setObjectName("ZoomSlider")
        self.draw_roi_zoom_slider.setSizePolicy(
            QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.draw_roi_zoom_slider.setFixedSize(QSize(130, 24))
        self.draw_roi_zoom_slider.valueChanged.connect(self.zoom_slider_value_changed)
        self.draw_roi_window_viewport_zoom_box. \
            addWidget(self.draw_roi_window_viewport_zoom_label)
        self.draw_roi_window_viewport_zoom_box. \
            addWidget(self.draw_roi_window_viewport_zoom_input)
        self.draw_roi_window_viewport_zoom_box. \
            addWidget(self.draw_roi_zoom_slider)
        self.draw_roi_window_input_container_box. \
            addRow(self.draw_roi_window_viewport_zoom_box)

        # Create a horizontal box for containing the cursor diameter changing function
        self.draw_roi_window_cursor_diameter_change_box = QHBoxLayout()
        self.draw_roi_window_cursor_diameter_change_box.setObjectName(
            "DrawRoiWindowCursorDiameterChangeBox")
        # Create a label for cursor diameter change
        self.draw_roi_window_cursor_diameter_change_label = QLabel()
        self.draw_roi_window_cursor_diameter_change_label.setObjectName(
            "DrawRoiWindowCursorDiameterChangeLabel")
        # Create an input box for cursor diameter
        self.draw_roi_window_cursor_diameter_change_input = QLineEdit()
        self.draw_roi_window_cursor_diameter_change_input.setObjectName(
            "DrawRoiWindowCursorDiameterChangeInput")
        self.draw_roi_window_cursor_diameter_change_input.setCursorPosition(0)
        self.draw_roi_window_cursor_diameter_change_input.setEnabled(False)
        self.draw_roi_window_cursor_diameter_change_input.setSizePolicy(
            QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.draw_roi_window_cursor_diameter_change_input.resize(
            self.draw_roi_window_cursor_diameter_change_input.sizeHint().width(),
            self.draw_roi_window_cursor_diameter_change_input.sizeHint().height()
        )

        # Create a slider for increasing and reducing cursor diameter
        self.draw_roi_window_cursor_diameter_slider = QSlider(Qt.Horizontal)
        self.draw_roi_window_cursor_diameter_slider.setMinimum(1)
        self.draw_roi_window_cursor_diameter_slider.setMaximum(50)
        self.draw_roi_window_cursor_diameter_slider.setSingleStep(1)
        self.draw_roi_window_cursor_diameter_slider.setTickPosition(QSlider.TicksBothSides)
        self.draw_roi_window_cursor_diameter_slider.setTickInterval(5)
        self.draw_roi_window_cursor_diameter_slider.setValue(25)
        self.draw_roi_window_cursor_diameter_slider.setObjectName("CursorDiameterSlider")
        self.draw_roi_window_cursor_diameter_slider.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.draw_roi_window_cursor_diameter_slider.setFixedSize(QSize(130, 24))
        self.draw_roi_window_cursor_diameter_slider.valueChanged.connect(self.cursor_diameter_slider_value_changed)
        self.draw_roi_window_cursor_diameter_change_input.setText(
            "{:.0f}".format(self.draw_roi_window_cursor_diameter_slider.value()))
        self.draw_roi_window_cursor_diameter_change_box.addWidget(
            self.draw_roi_window_cursor_diameter_change_label)
        self.draw_roi_window_cursor_diameter_change_box.addWidget(
            self.draw_roi_window_cursor_diameter_change_input)
        self.draw_roi_window_cursor_diameter_change_box.addWidget(
            self.draw_roi_window_cursor_diameter_slider)
        self.draw_roi_window_input_container_box.addRow(
            self.draw_roi_window_cursor_diameter_change_box)
        self.draw_roi_window_cursor_diameter_slider.setEnabled(
            False)

        # Create a horizontal box for containing the transparency changing function
        self.transparency_slider_box = QHBoxLayout()
        self.transparency_slider_box.setObjectName(
            "TransparencySliderBox")
        # Create slider to adjust the transparency of drawn pixels
        self.transparency_slider_label = QLabel()
        self.transparency_slider_label.setObjectName("TransparencySliderLabel")

        self.transparency_slider_input_box = QLineEdit()
        self.transparency_slider_input_box.setObjectName("TransparencySliderInputBox")
        self.transparency_slider_input_box.setText("{:.0f}".format(self.pixel_transparency * 100) + "%")
        self.transparency_slider_input_box.setCursorPosition(0)
        self.transparency_slider_input_box.setEnabled(False)
        self.transparency_slider_input_box.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.transparency_slider_input_box.resize(self.transparency_slider_input_box.sizeHint().width(),
                                                  self.transparency_slider_input_box.sizeHint().height())

        self.transparency_slider = QSlider(Qt.Horizontal)
        self.transparency_slider.setMinimum(0)
        self.transparency_slider.setMaximum(100)
        self.transparency_slider.setSingleStep(1)
        self.transparency_slider.setTickPosition(QSlider.TicksBothSides)
        self.transparency_slider.setTickInterval(10)
        self.transparency_slider.setValue(50)
        self.transparency_slider.setObjectName("TransparencySlider")
        self.transparency_slider.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.transparency_slider.setFixedSize(QSize(130, 24))
        self.transparency_slider.valueChanged.connect(self.transparency_slider_value_changed)
        self.transparency_slider.setEnabled(False)
        self.transparency_slider_box.addWidget(self.transparency_slider_label)
        self.transparency_slider_box.addWidget(self.transparency_slider_input_box)
        self.transparency_slider_box.addWidget(self.transparency_slider)
        self.draw_roi_window_input_container_box.addRow(self.transparency_slider_box)

        # Create a horizontal box for containing the Set Bounds function
        self.set_bounds_box = QHBoxLayout()
        self.set_bounds_box.setObjectName("SetBounds")
        # Create a bounding box button
        self.image_slice_number_box_draw_button = QPushButton()
        self.image_slice_number_box_draw_button. \
            setObjectName("ImageSliceNumberBoxDrawButton")
        self.image_slice_number_box_draw_button. \
            setProperty("QPushButtonClass", "draw-roi-button")
        self.image_slice_number_box_draw_button.setSizePolicy(
            QSizePolicy.MinimumExpanding, QSizePolicy.Minimum
        )
        self.image_slice_number_box_draw_button.resize(
            self.image_slice_number_box_draw_button.sizeHint().width(),
            self.image_slice_number_box_draw_button.sizeHint().height()
        )
        self.image_slice_number_box_draw_button.clicked. \
            connect(self.onBoxDrawClicked)
        icon_box_draw = QtGui.QIcon()
        icon_box_draw.addPixmap(QtGui.QPixmap(
            resource_path('res/images/btn-icons/draw_bound_icon.png')))
        self.image_slice_number_box_draw_button.setIcon(icon_box_draw)
        self.set_bounds_box.addWidget(self.image_slice_number_box_draw_button)
        self.draw_roi_window_input_container_box. \
            addRow(self.set_bounds_box)

        # Create a horizontal box for containing the draw, clear, fill, 3D fill function
        self.draw_button_row_layout = QHBoxLayout()
        self.draw_button_row_layout.setObjectName("DrawButtonRowLayout")
        # Create a draw button
        self.image_slice_number_draw_button = QPushButton()
        self.image_slice_number_draw_button.setObjectName("ImageSliceNumberDrawButton")
        self.image_slice_number_draw_button. \
            setProperty("QPushButtonClass", "draw-roi-button")
        self.image_slice_number_draw_button.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum))
        self.image_slice_number_draw_button.resize(
            self.image_slice_number_draw_button.sizeHint().width(),
            self.image_slice_number_draw_button.sizeHint().height())
        self.image_slice_number_draw_button.clicked.connect(self.onDrawClicked)
        self.image_slice_number_draw_button.setEnabled(False)
        icon_draw = QtGui.QIcon()
        icon_draw.addPixmap(QtGui.QPixmap(
            resource_path('res/images/btn-icons/draw_icon.png')))
        self.image_slice_number_draw_button.setIcon(icon_draw)
        self.draw_button_row_layout.addWidget(self.image_slice_number_draw_button)

        # Create a clear button(clear single slice)
        self.image_slice_number_clear_button = QPushButton()
        self.image_slice_number_clear_button.setObjectName("ImageSliceNumberClearButton")
        self.image_slice_number_clear_button. \
            setProperty("QPushButtonClass", "draw-roi-button")
        self.image_slice_number_clear_button.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum))
        self.image_slice_number_clear_button.resize(
            self.image_slice_number_clear_button.sizeHint().width(),
            self.image_slice_number_clear_button.sizeHint().height())
        self.image_slice_number_clear_button.clicked.connect(self.onClearClicked)
        self.image_slice_number_clear_button.setEnabled(False)
        icon_clear = QtGui.QIcon()
        icon_clear.addPixmap(QtGui.QPixmap(
            resource_path('res/images/btn-icons/clear_icon.png')))
        self.image_slice_number_clear_button.setIcon(icon_clear)
        self.draw_button_row_layout.addWidget(self.image_slice_number_clear_button)

        # Create a fill button
        self.image_slice_number_fill_button = QPushButton()
        self.image_slice_number_fill_button. \
            setObjectName("ImageSliceNumberFillButton")
        self.image_slice_number_fill_button. \
            setProperty("QPushButtonClass", "draw-roi-button")
        self.image_slice_number_fill_button.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum))
        self.image_slice_number_fill_button.resize(
            self.image_slice_number_fill_button.sizeHint().width(),
            self.image_slice_number_fill_button.sizeHint().height())
        self.image_slice_number_fill_button.clicked.connect(lambda: self.onFillClicked(False))
        icon_fill = QtGui.QIcon()
        icon_fill.addPixmap(QtGui.QPixmap(
            resource_path('res/images/btn-icons/fill_icon.png')))
        self.image_slice_number_fill_button.setIcon(icon_fill)
        self.image_slice_number_fill_button.setText("Fill")
        self.draw_button_row_layout. \
            addWidget(self.image_slice_number_fill_button)

        # Create the 3d draw button
        self.image_slice_number_draw_button3D = QPushButton()
        self.image_slice_number_draw_button3D. \
            setObjectName("ImageSliceNumber3dDrawButton")
        self.image_slice_number_draw_button3D. \
            setProperty("QPushButtonClass", "draw-roi-button")
        self.image_slice_number_draw_button3D.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum))
        self.image_slice_number_draw_button3D.resize(
            self.image_slice_number_draw_button3D.sizeHint().width(),
            self.image_slice_number_draw_button3D.sizeHint().height())
        self.image_slice_number_draw_button3D.clicked.connect(lambda: self.onFillClicked(True))
        icon_draw3d = QtGui.QIcon()
        icon_draw3d.addPixmap(QtGui.QPixmap(
            resource_path('res/images/btn-icons/3d_icon.png')))
        self.image_slice_number_draw_button3D.setIcon(icon_draw3d)
        self.image_slice_number_draw_button3D.setText("3D Fill")
        self.draw_button_row_layout. \
            addWidget(self.image_slice_number_draw_button3D)
        self.draw_roi_window_input_container_box. \
            addRow(self.draw_button_row_layout)

        # Create a horizontal box for containing the transect and preview contour function
        self.transect_preview_contour_box = QHBoxLayout()
        self.transect_preview_contour_box.setObjectName("TransectPreviewContourBox")
        # Create a transect button
        self.image_slice_number_transect_button = QPushButton()
        self.image_slice_number_transect_button. \
            setObjectName("ImageSliceNumberTransectButton")
        self.image_slice_number_transect_button. \
            setProperty("QPushButtonClass", "draw-roi-button")
        self.image_slice_number_transect_button.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum))
        self.image_slice_number_transect_button.resize(
            self.image_slice_number_transect_button.sizeHint().width(),
            self.image_slice_number_transect_button.sizeHint().height())
        self.image_slice_number_transect_button.clicked. \
            connect(self.transect_handler)
        icon_transect = QtGui.QIcon()
        icon_transect.addPixmap(QtGui.QPixmap(
            resource_path('res/images/btn-icons/transect_icon.png')))
        self.image_slice_number_transect_button.setIcon(icon_transect)
        self.transect_preview_contour_box. \
            addWidget(self.image_slice_number_transect_button)

        # Create a contour preview button
        self.button_contour_preview = QtWidgets.QPushButton("Preview contour")
        self.button_contour_preview. \
            setProperty("QPushButtonClass", "draw-roi-button")
        self.button_contour_preview.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum))
        self.button_contour_preview.resize(
            self.button_contour_preview.sizeHint().width(),
            self.button_contour_preview.sizeHint().height())
        self.button_contour_preview.clicked.connect(self.onPreviewClicked)
        icon_preview = QtGui.QIcon()
        icon_preview.addPixmap(QtGui.QPixmap(
            resource_path('res/images/btn-icons/preview_icon.png')))
        self.button_contour_preview.setIcon(icon_preview)
        self.transect_preview_contour_box. \
            addWidget(self.button_contour_preview)
        self.draw_roi_window_input_container_box. \
            addRow(self.transect_preview_contour_box)

        # Create input line edit for alpha value
        self.label_alpha_value = QtWidgets.QLabel("Alpha value:")
        self.input_alpha_value = QtWidgets.QDoubleSpinBox()
        self.input_alpha_value.setObjectName("AlphaValueInput")
        self.input_alpha_value. \
            setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        self.input_alpha_value.resize(
            self.input_alpha_value.sizeHint().width(),
            self.input_alpha_value.sizeHint().height())
        self.input_alpha_value.setDecimals(1)
        self.input_alpha_value.setMinimum(0.2)
        self.input_alpha_value.setMaximum(0.9)
        self.input_alpha_value.setSingleStep(0.1)
        # Import the alpha value from config file
        with open(data_path("draw_roi_configuration"), "r") as draw_roi_cfg_file:
            options = draw_roi_cfg_file.read().splitlines()
            if len(options) > 0:
                alpha_value = float(options[0])
            else:
                alpha_value = 0.9
        self.input_alpha_value.setValue(alpha_value)
        self.draw_roi_window_input_container_box. \
            addRow(self.label_alpha_value, self.input_alpha_value)

        # Create a label for denoting the max internal hole size
        self.internal_hole_max_label = QLabel()
        self.internal_hole_max_label.setObjectName("InternalHoleLabel")

        # Create input for max internal hole size
        self.internal_hole_max_line_edit = QLineEdit()
        self.internal_hole_max_line_edit.setObjectName("InternalHoleInput")
        self.internal_hole_max_line_edit. \
            setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        self.internal_hole_max_line_edit.resize(
            self.internal_hole_max_line_edit.sizeHint().width(),
            self.internal_hole_max_line_edit.sizeHint().height())
        self.internal_hole_max_line_edit.setValidator(
            QRegularExpressionValidator(
                QRegularExpression("^[0-9]*$")))
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
        self.isthmus_width_max_line_edit.setValidator(
            QRegularExpressionValidator(
                QRegularExpression("^[0-9]*[.]?[0-9]*$")))
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
        self.min_pixel_density_line_edit.setValidator(
            QRegularExpressionValidator(
                QRegularExpression("^[0-9]*[.]?[0-9]*$")))
        self.draw_roi_window_input_container_box.addRow(
            self.min_pixel_density_label, self.min_pixel_density_line_edit)

        # Create a label for denoting the minimum pixel density
        self.max_pixel_density_label = QLabel()
        self.max_pixel_density_label.setObjectName("MaxPixelDensityLabel")
        # Create input for min pixel size
        self.max_pixel_density_line_edit = QLineEdit()
        self.max_pixel_density_line_edit.setObjectName("MaxPixelDensityInput")
        self.max_pixel_density_line_edit. \
            setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        self.max_pixel_density_line_edit.resize(
            self.max_pixel_density_line_edit.sizeHint().width(),
            self.max_pixel_density_line_edit.sizeHint().height())
        self.max_pixel_density_line_edit.setValidator(
            QRegularExpressionValidator(
                QRegularExpression("^[0-9]*[.]?[0-9]*$")))
        self.draw_roi_window_input_container_box.addRow(
            self.max_pixel_density_label, self.max_pixel_density_line_edit)

        # Create a horizontal box for saving, reset and cancel the drawing
        self.draw_roi_window_cancel_save_box = QHBoxLayout()
        self.draw_roi_window_cancel_save_box. \
            setObjectName("DrawRoiWindowCancelSaveBox")
        # Create an exit button to cancel the drawing
        # Add a button to go back/exit from the application
        self.draw_roi_window_instance_cancel_button = QPushButton()
        self.draw_roi_window_instance_cancel_button. \
            setObjectName("DrawRoiWindowInstanceCancelButton")
        self.draw_roi_window_instance_cancel_button.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum))
        self.draw_roi_window_instance_cancel_button.resize(
            self.draw_roi_window_instance_cancel_button.sizeHint().width(),
            self.draw_roi_window_instance_cancel_button.sizeHint().height())
        self.draw_roi_window_instance_cancel_button. \
            setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.draw_roi_window_instance_cancel_button.clicked. \
            connect(self.onCancelButtonClicked)
        self.draw_roi_window_instance_cancel_button. \
            setProperty("QPushButtonClass", "fail-button")
        icon_cancel = QtGui.QIcon()
        icon_cancel.addPixmap(QtGui.QPixmap(
            resource_path('res/images/btn-icons/cancel_icon.png')))
        self.draw_roi_window_instance_cancel_button.setIcon(icon_cancel)
        self.draw_roi_window_cancel_save_box. \
            addWidget(self.draw_roi_window_instance_cancel_button)

        # Create a button to reset the draw
        self.draw_roi_window_instance_action_reset_button = QPushButton()
        self.draw_roi_window_instance_action_reset_button. \
            setObjectName("DrawRoiWindowInstanceActionClearButton")
        self.draw_roi_window_instance_action_reset_button.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum))
        self.draw_roi_window_instance_action_reset_button. \
            setProperty("QPushButtonClass", "reset-button")
        reset_button = self.draw_roi_window_instance_action_reset_button
        self.draw_roi_window_instance_action_reset_button.resize(
            reset_button.sizeHint().width(), reset_button.sizeHint().height())
        self.draw_roi_window_instance_action_reset_button.clicked. \
            connect(self.onResetClicked)
        icon_clear_roi_draw = QtGui.QIcon()
        icon_clear_roi_draw.addPixmap(QtGui.QPixmap(
            resource_path('res/images/btn-icons/reset_roi_draw_icon.png')))
        self.draw_roi_window_instance_action_reset_button. \
            setIcon(icon_clear_roi_draw)
        self.draw_roi_window_cancel_save_box. \
            addWidget(self.draw_roi_window_instance_action_reset_button)

        # Create a save button to save all the changes
        self.draw_roi_window_instance_save_button = QPushButton()
        self.draw_roi_window_instance_save_button. \
            setObjectName("DrawRoiWindowInstanceSaveButton")
        self.draw_roi_window_instance_save_button.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum))
        self.draw_roi_window_instance_save_button.resize(
            self.draw_roi_window_instance_save_button.sizeHint().width(),
            self.draw_roi_window_instance_save_button.sizeHint().height())
        self.draw_roi_window_instance_save_button. \
            setProperty("QPushButtonClass", "success-button")
        icon_save = QtGui.QIcon()
        icon_save.addPixmap(QtGui.QPixmap(
            resource_path('res/images/btn-icons/save_icon.png')))
        self.draw_roi_window_instance_save_button.setIcon(icon_save)
        self.draw_roi_window_instance_save_button.clicked. \
            connect(self.onSaveClicked)
        self.draw_roi_window_cancel_save_box. \
            addWidget(self.draw_roi_window_instance_save_button)

        self.draw_roi_window_input_container_box. \
            addRow(self.draw_roi_window_cancel_save_box)

        # Creating a horizontal box to hold the ROI view and slider
        self.draw_roi_window_instance_view_box = QHBoxLayout()
        self.draw_roi_window_instance_view_box. \
            setObjectName("DrawRoiWindowInstanceViewBox")
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
        self.draw_roi_window_main_box. \
            addLayout(self.draw_roi_window_input_container_box, 1)
        self.draw_roi_window_main_box. \
            addWidget(self.draw_roi_window_instance_view_widget, 11)

        # Create a new central widget to hold the vertical box layout
        self.draw_roi_window_instance_central_widget = QWidget()
        self.draw_roi_window_instance_central_widget. \
            setObjectName("DrawRoiWindowInstanceCentralWidget")
        self.draw_roi_window_instance_central_widget.setLayout(
            self.draw_roi_window_main_box)

        self.retranslate_ui(self.draw_roi_window_instance)
        self.draw_roi_window_instance.setStyleSheet(StyleSheetReader().get_stylesheet())
        self.draw_roi_window_instance. \
            setCentralWidget(self.draw_roi_window_instance_central_widget)
        QtCore.QMetaObject.connectSlotsByName(self.draw_roi_window_instance)

    def slider_value_changed(self):
        """
        actions to be taken when slider value changes

        """
        image_slice_number = self.current_slice
        # save progress
        self.save_drawing_progress(image_slice_number)
        self.set_current_slice(self.dicom_view.slider.value())

    def set_current_slice(self, slice_number):
        """
            set the current slice
            :param slice_number: the slice number to be set
        """
        self.image_slice_number_line_edit.setText(str(slice_number + 1))
        self.current_slice = slice_number
        self.dicom_view.update_view()

        # check if this slice has any drawings before
        if self.drawn_roi_list.get(self.current_slice) is not None:
            self.drawingROI = self.drawn_roi_list[
                self.current_slice]['drawingROI']
            self.ds = self.drawn_roi_list[self.current_slice]['ds']
            self.dicom_view.view.setScene(self.drawingROI)
            self.enable_cursor_diameter_transparency()
            self.drawingROI.clear_cursor(self.drawing_tool_radius)
            self.has_drawing = True

        else:
            self.disable_cursor_diameter_transparency()
            self.ds = None
            self.has_drawing = False

    def update_draw_roi_pixmaps(self):
        """
        Updates the pixmaps_axial data for the displayed DICOM draw roi panel.
        This will update all slices that do not have a drawn ROI, as well as looping through the drawn objects and
        updating the ROI image
        """
        logging.debug("update_draw_roi_pixmaps started")
        self.save_drawing_progress(self.current_slice)
        self.dicom_view.update_view()

        # for each drawn ROI slice
        for slice_number in self.drawn_roi_list:
            if self.drawn_roi_list.get(slice_number)['drawingROI'] is not None:
                slice_drawing_roi = self.drawn_roi_list[slice_number]['drawingROI']
                slice_drawing_roi.img = self.patient_dict_container.get("pixmaps_axial")[slice_number]
                slice_drawing_roi.update_dicom_image()

        if hasattr(self, 'drawingROI') and self.drawingROI:
            self.dicom_view.view.setScene(self.drawingROI)

    def onZoomInClicked(self):
        """
        This function is used for zooming in button
        """
        self.dicom_view.zoom *= 1.05
        self.dicom_view.update_view(zoom_change=True)
        if hasattr(self, 'drawingROI') and self.drawingROI \
                and self.drawingROI.current_slice == self.current_slice:
            self.dicom_view.view.setScene(self.drawingROI)
        self.draw_roi_window_viewport_zoom_input.setText(
            "{:.2f}".format(self.dicom_view.zoom * 100) + "%")
        self.draw_roi_window_viewport_zoom_input.setCursorPosition(0)
        # update the zoom slider
        self.draw_roi_zoom_slider.setValue(self.dicom_view.zoom * 100)

    def onZoomOutClicked(self):
        """
        This function is used for zooming out button
        """
        self.dicom_view.zoom /= 1.05
        self.dicom_view.update_view(zoom_change=True)
        if hasattr(self, 'drawingROI') and self.drawingROI \
                and self.drawingROI.current_slice == self.current_slice:
            self.dicom_view.view.setScene(self.drawingROI)
        self.draw_roi_window_viewport_zoom_input. \
            setText("{:.2f}".format(self.dicom_view.zoom * 100) + "%")
        self.draw_roi_window_viewport_zoom_input.setCursorPosition(0)
        # update the zoom slider
        self.draw_roi_zoom_slider.setValue(self.dicom_view.zoom * 100)

    def zoom_slider_value_changed(self):
        """
        This function is used for zoom slider value change
        """
        self.dicom_view.zoom = round(self.draw_roi_zoom_slider.value() / 100.0, 2)
        self.dicom_view.update_view(zoom_change=True)
        if hasattr(self, 'drawingROI') and self.drawingROI \
                and self.drawingROI.current_slice == self.current_slice:
            self.dicom_view.view.setScene(self.drawingROI)
        self.draw_roi_window_viewport_zoom_input. \
            setText("{:.2f}".format(self.dicom_view.zoom * 100) + "%")
        self.draw_roi_window_viewport_zoom_input.setCursorPosition(0)

    def transparency_slider_value_changed(self):
        self.pixel_transparency = round(self.transparency_slider.value() / 100.0, 2)
        self.transparency_slider_input_box.setText("{:.0f}".format(self.pixel_transparency * 100) + "%")
        self.transparency_slider_input_box.setCursorPosition(0)
        if hasattr(self, 'drawingROI') and self.drawingROI:
            self.drawingROI.pixel_transparency = self.pixel_transparency
            self.drawingROI.update_pixel_transparency()

    def onCancelButtonClicked(self):
        """
        This function is used for canceling the drawing
        """
        self.closeWindow()

    def onBackwardClicked(self):
        """
        This function is used when backward button is clicked
        """
        image_slice_number = self.current_slice
        # save progress
        if self.save_drawing_progress(image_slice_number):
            # Backward will only execute if current image slice is above 0.
            if int(image_slice_number) > 0:
                # decrements slice by 1 and update slider to move to correct
                # position
                self.dicom_view.slider.setValue(image_slice_number - 1)

    def onForwardClicked(self):
        """
        This function is used when forward button is clicked
        """
        image_slice_number = self.current_slice
        # save progress
        if self.save_drawing_progress(image_slice_number):
            pixmaps = self.patient_dict_container.get("pixmaps_axial")
            total_slices = len(pixmaps)

            # Forward will only execute if current image slice is below the
            # total number of slices.
            if int(image_slice_number) < total_slices:
                # increments slice by 1 and update slider to move to correct
                # position
                self.dicom_view.slider.setValue(image_slice_number + 1)

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
        self.has_drawing = False

    def save_drawing_progress(self, image_slice_number):
        """
        this function saves the drawing progress on current slice
        :param image_slice_number: the slice number to be saved
        """
        if self.slice_changed:
            if hasattr(self, 'drawingROI') and self.drawingROI \
                    and self.ds is not None \
                    and len(self.drawingROI.target_pixel_coords) != 0:
                alpha = self.input_alpha_value.value()
                pixel_hull_list = calculate_concave_hull_of_points(
                    self.drawingROI.target_pixel_coords, alpha)
                coord_list = []
                for pixel_hull in pixel_hull_list:
                    coord_list.append(pixel_hull)
                self.drawn_roi_list[image_slice_number] = {
                    'coords': coord_list,
                    'ds': self.ds,
                    'drawingROI': self.drawingROI
                }
                self.slice_changed = False
                return True
        else:
            return True

        return True

    def on_transect_close(self):
        """
        Function triggered when transect is closed
        """
        if self.upper_limit and self.lower_limit:
            self.min_pixel_density_line_edit.setText(str(self.lower_limit))
            self.max_pixel_density_line_edit.setText(str(self.upper_limit))

        self.dicom_view.update_view()

    def onDrawClicked(self):
        """
        Function triggered when the Draw button is pressed from the menu.
        """
        logging.debug("onDrawClicked started")
        if hasattr(self, 'drawingROI'):
            if self.drawingROI is not None:
                self.is_drawing.connect(self.drawingROI.set_is_drawing)
                self.is_drawing.emit(True)
                self.is_drawing.disconnect(self.drawingROI.set_is_drawing)
        logging.debug("onDrawClicked finished")

    def onFillClicked(self, is_3d):
        """
        Function triggered when the Fill or 3d Fill button is pressed from the menu.
        """
        logging.debug("onFillClicked started")
        if self.has_drawing:
            self.is_drawing.connect(self.drawingROI.set_is_drawing)
            self.is_drawing.emit(False)
            self.is_drawing.disconnect(self.drawingROI.set_is_drawing)
            return None

        if self.min_pixel_density_line_edit.text() == "" \
                or self.max_pixel_density_line_edit.text() == "":
            QMessageBox.about(self.draw_roi_window_instance, "Not Enough Data",
                              "Not all values are specified or correct.")
        else:
            # Getting most updated selected slice

            min_pixel = self.min_pixel_density_line_edit.text()
            max_pixel = self.max_pixel_density_line_edit.text()

            # If they are number inputs
            try:
                float(min_pixel)
                min_is_float = True
            except ValueError:
                min_is_float = False

            try:
                float(max_pixel)
                max_is_float = True
            except ValueError:
                max_is_float = False

            # If they are number inputs
            if min_is_float and max_is_float:

                min_pixel = float(min_pixel)
                max_pixel = float(max_pixel)

                if min_pixel >= max_pixel:
                    QMessageBox.about(self.draw_roi_window_instance,
                                      "Incorrect Input",
                                      "Please ensure maximum density is "
                                      "atleast higher than minimum density.")

                internal_hole_max = self.internal_hole_max_line_edit.text()
                max_internal_hole_size = 0
                if internal_hole_max != "":
                    if int(internal_hole_max) > 0:
                        max_internal_hole_size = int(internal_hole_max)

                pixmaps = self.patient_dict_container.get("pixmaps_axial")
                id = self.current_slice

                if is_3d:
                    if hasattr(self, 'seed'):
                        delattr(self, 'seed')
                    self.create_drawing(min_pixel, max_pixel, pixmaps, id, max_internal_hole_size, True)
                else:
                    self.create_drawing(min_pixel, max_pixel, pixmaps, id, max_internal_hole_size)

            else:
                QMessageBox.about(self.draw_roi_window_instance,
                                  "Not Enough Data",
                                  "Not all values are specified or correct.")

    def create_drawing(self, min_pixel, max_pixel, pixmaps, id, max_internal_hole_size, multiple=False):
        """
        Creates drawing using BFS on a single slice
            If the multiple flag is set, process 3D roi will be indirectly triggered through a signal
        """
        logging.debug("create_drawing started")
        UI = None
        if multiple:
            UI = self

        dt = self.patient_dict_container.dataset[id]
        dt.convert_pixel_data()
        # Path to the selected .dcm file
        location = self.patient_dict_container.filepaths[id]
        self.ds = pydicom.dcmread(location)

        self.drawingROI = Drawing(
            pixmaps[id],
            dt._pixel_array.transpose(),
            min_pixel,
            max_pixel,
            self.patient_dict_container.dataset[id],
            self.draw_roi_window_instance,
            self.slice_changed,
            self.current_slice,
            self.drawing_tool_radius,
            self.keep_empty_pixel,
            self.pixel_transparency,
            max_internal_hole_size,
            set(),
            UI=UI
        )

        self.slice_changed = True
        self.has_drawing = True
        self.dicom_view.view.setScene(self.drawingROI)
        self.enable_cursor_diameter_transparency()

    def process_3D_roi(self, min_pixel, max_pixel, pixmaps, id, max_internal_hole_size, thread=None, interrupt_flag=None,
                       progress_callback=None):
        """
        Processes roi drawing accross multiple slices using a seperate thread, allowing for the user to start drawing on the dicom view
        Creates drawing across multiple slides allowing for the user to start drawing on dicom view.
        """
        logging.debug("process_3D_roi started")

        # If the seed is set then start searching, else assign the drawing function to the left click
        if hasattr(self, 'seed'):
            # Search down from the start position then up from the start position
            total_slices = len(self.patient_dict_container.dataset)
            for x in range(0, 2):

                if x == 0:
                    # search down slice
                    slice_start = id - 1
                    slice_end = 1
                    step = -1
                else:
                    # search up slices
                    slice_start = id
                    slice_end = total_slices - 1
                    step = 1

                # Search the slides in the above ranges (down and up)
                for y_search in range(slice_start, slice_end, step):
                    # checking for interrupt (threading)
                    if interrupt_flag.isSet():
                        logging.debug("interrupting process_3D_roi")
                        break

                    # updating progress
                    progress_callback.emit(
                        ("Processing ROI for multiple slices", int(len(self.drawn_roi_list) / total_slices * 100)))
                    temp_id = y_search

                    # saving previous drawing and updating slice
                    self.save_drawing_progress(self.current_slice)
                    self.current_slice = temp_id

                    if self.drawn_roi_list.get(self.current_slice) is not None:
                        # do not redraw, continue to check the next slice
                        continue

                    dt = self.patient_dict_container.dataset[temp_id]
                    dt.convert_pixel_data()

                    # Path to the selected .dcm file
                    location = self.patient_dict_container.filepaths[temp_id]
                    self.ds = pydicom.dcmread(location)

                    self.drawingROI = Drawing(
                        pixmaps[temp_id],
                        dt._pixel_array.transpose(),
                        min_pixel,
                        max_pixel,
                        self.patient_dict_container.dataset[temp_id],
                        self.draw_roi_window_instance,
                        self.slice_changed,
                        self.current_slice,
                        self.drawing_tool_radius,
                        self.keep_empty_pixel,
                        self.pixel_transparency,
                        max_internal_hole_size,
                        set(),
                        xy=self.seed
                    )
                    self.slice_changed = True
                    self.has_drawing = True
                    self.enable_cursor_diameter_transparency()

                    roi_drawn = self.drawingROI._display_pixel_color()
                    self.drawingROI.moveToThread(thread)
                    if not roi_drawn:
                        break
        logging.debug("process_3D_roi finished")

    @Slot(list)
    def set_seed(self, s):
        """
        Sets the seed in this class, seed retrieved from Drawing.py when user clicks on the view
        This will then trigger to start processing an ROI for each slice based on the source seed
        """

        self.seed = s
        roi_processing_window = ProgressWindow()

        def finished():
            """Inner function called when 3D ROI is finished"""
            roi_processing_window.close()
            self.dicom_view.slider.setValue(self.current_slice)

        def errored(err):
            """Inner function called when 3D ROI has errored"""
            logging.error('process_3D_roi has errored: %s', err)
            roi_processing_window.close()

        roi_processing_window.signal_loaded.connect(finished)
        roi_processing_window.signal_error.connect(errored)

        roi_processing_window.start(self.process_3D_roi, float(self.min_pixel_density_line_edit.text()),
                                    float(self.max_pixel_density_line_edit.text()),
                                    self.patient_dict_container.get("pixmaps_axial"),
                                    self.current_slice, int(self.internal_hole_max_line_edit.text()), QThread.currentThread())

    def onBoxDrawClicked(self):
        """
        Function triggered when bounding box button is pressed
        """
        id = self.current_slice
        dt = self.patient_dict_container.dataset[id]
        dt.convert_pixel_data()
        pixmaps = self.patient_dict_container.get("pixmaps_axial")

        self.bounds_box_draw = DrawBoundingBox(pixmaps[id], dt)
        self.dicom_view.view.setScene(self.bounds_box_draw)
        self.disable_cursor_diameter_transparency()
        self.has_drawing = False

    def onClearClicked(self):
        """
        This function is used when reset button is clicked
        """
        self.dicom_view.image_display()
        self.dicom_view.update_view()
        self.isthmus_width_max_line_edit.setText("5")
        self.internal_hole_max_line_edit.setText("5")
        self.min_pixel_density_line_edit.setText("")
        self.max_pixel_density_line_edit.setText("")
        if hasattr(self, 'bounds_box_draw'):
            delattr(self, 'bounds_box_draw')
        if hasattr(self, 'drawingROI'):
            delattr(self, 'drawingROI')
            self.has_drawing = False
        if hasattr(self, 'seed'):
            delattr(self, 'seed')

        self.ds = None

    def onResetClicked(self):
        """
        This function is used when reset button is clicked
        """
        self.onClearClicked()
        self.drawn_roi_list = {}

    def onSaveClicked(self):
        """
            Function triggered when Save button is clicked
        """
        # Make sure the user has clicked Draw first
        if self.save_drawing_progress(image_slice_number=self.current_slice):
            self.saveROIList()

    def saveROIList(self):
        """
            Function triggered when saving ROI list
        """
        logging.debug("saveROIList started")
        if self.ROI_name is None:
            QMessageBox.about(self.draw_roi_window_instance, "No ROI instance selected",
                              "Please ensure you have selected your ROI instance before saving.")
            return

        roi_list = ROI.convert_hull_list_to_contours_data(
            self.drawn_roi_list, self.patient_dict_container)
        if len(roi_list) == 0:
            QMessageBox.about(self.draw_roi_window_instance, "No ROI Detected",
                              "Please ensure you have drawn your ROI first.")
            return

        # The list of points will need to be converted into a
        # single-dimensional array, as RTSTRUCT contour data is stored in
        # such a way. i.e. [x, y, z, x, y, z, x, y, z, ..., ...] Create a
        # popup window that modifies the RTSTRUCT and tells the user that
        # processing is happening.
        connectSaveROIProgress(
            self, roi_list, self.dataset_rtss, self.ROI_name, self.roi_saved)

    def roi_saved(self, new_rtss):
        """
            Function to call save ROI and display progress
        """
        self.signal_roi_drawn.emit((new_rtss, {"draw": self.ROI_name}))
        QMessageBox.about(self.draw_roi_window_instance, "Saved",
                          "New contour successfully created!")
        self.closeWindow()

    def onPreviewClicked(self):
        """
        function triggered when Preview button is clicked
        """
        if hasattr(self, 'drawingROI') and self.drawingROI and len(
                self.drawingROI.target_pixel_coords) > 0:
            alpha = self.input_alpha_value.value()
            polygon_list = calculate_concave_hull_of_points(
                self.drawingROI.target_pixel_coords, alpha)
            self.drawingROI.draw_contour_preview(polygon_list)
        else:
            QMessageBox.about(self.draw_roi_window_instance, "Not Enough Data",
                              "Please ensure you have drawn your ROI first.")

    def set_selected_roi_name(self, roi_name):
        """
        function to set selected roi name
        :param roi_name: roi name selected
        """
        roi_exists = False

        patient_dict_container = PatientDictContainer()
        existing_rois = patient_dict_container.get("rois")

        # Check to see if the ROI already exists
        for key, value in existing_rois.items():
            if roi_name in value['name']:
                roi_exists = True

        if roi_exists:
            QMessageBox.about(self.draw_roi_window_instance,
                              "ROI already exists in RTSS",
                              "Would you like to continue?")

        self.ROI_name = roi_name
        self.select_roi_type.setText(self.ROI_name)

    def cursor_diameter_slider_value_changed(self):
        """
            function to update slider value change
        """
        self.drawing_tool_radius = self.draw_roi_window_cursor_diameter_slider.value() / 2
        self.draw_roi_window_cursor_diameter_change_input.setText(
            "{:.0f}".format(self.draw_roi_window_cursor_diameter_slider.value()))
        self.draw_roi_window_cursor_diameter_change_input.setCursorPosition(0)
        self.draw_cursor_when_diameter_changed()

    def draw_cursor_when_diameter_changed(self):
        """
        function to update drawing cursor when diameter changed
        """
        if self.drawingROI.cursor:
            self.drawingROI.draw_cursor(
                self.drawingROI.current_cursor_x + self.drawing_tool_radius,
                self.drawingROI.current_cursor_y + self.drawing_tool_radius,
                self.drawing_tool_radius)
        else:
            self.drawingROI.draw_cursor(
                (self.drawingROI.min_bounds_x + self.drawingROI.max_bounds_x) / 2,
                (self.drawingROI.min_bounds_y + self.drawingROI.max_bounds_y) / 2,
                self.drawing_tool_radius,
                True)

    def disable_cursor_diameter_transparency(self):
        """
        function to disable cursor diameter change box, draw button and transparency slider
        """
        self.draw_roi_window_cursor_diameter_slider.setEnabled(
            False)
        self.image_slice_number_draw_button.setEnabled(False)
        self.image_slice_number_clear_button.setEnabled(False)
        self.transparency_slider.setEnabled(False)

    def enable_cursor_diameter_transparency(self):
        """
        function to enable cursor diameter change box, draw button and transparency slider
        """
        self.draw_roi_window_cursor_diameter_slider.setEnabled(
            True)
        self.image_slice_number_draw_button.setEnabled(True)
        self.image_slice_number_clear_button.setEnabled(True)
        self.transparency_slider.setEnabled(True)

    def show_roi_type_options(self):
        """Creates and displays roi type options popup"""
        logging.debug("show_roi_type_options started")
        self.choose_roi_name_window = SelectROIPopUp()
        self.choose_roi_name_window.signal_roi_name.connect(
            self.set_selected_roi_name)
        self.choose_roi_name_window.show()

    def closeWindow(self):
        """
        function to close draw roi window
        """
        # Save the alpha value to the config file
        with open(data_path("draw_roi_configuration"), "w") as stream:
            stream.write(str(self.input_alpha_value.value()))
            stream.write("\n")

        self.drawn_roi_list = {}
        if hasattr(self, 'bounds_box_draw'):
            delattr(self, 'bounds_box_draw')
        if hasattr(self, 'drawingROI'):
            delattr(self, 'drawingROI')
        self.ds = None
        if hasattr(self, 'seed'):
            delattr(self, 'seed')
        self.close()
        self.signal_draw_roi_closed.emit()

