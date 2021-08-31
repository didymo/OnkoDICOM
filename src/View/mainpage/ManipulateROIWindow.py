import pydicom
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap, QFont
from PySide6.QtWidgets import QMessageBox, QVBoxLayout, QHBoxLayout, QComboBox, QLineEdit, QSizePolicy, QPushButton, \
    QLabel, QWidget, QFormLayout

from src.Model import ROI, ImageLoading
from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.Worker import Worker
from src.View.mainpage.DicomAxialView import DicomAxialView

from src.Controller.PathHandler import resource_path
import platform


class UIManipulateROIWindow:

    def setup_ui(self, manipulate_roi_window_instance, rois, dataset_rtss,
                 roi_color, signal_roi_manipulated):

        self.patient_dict_container = PatientDictContainer()
        self.rois = rois
        self.dataset_rtss = dataset_rtss
        self.signal_roi_manipulated = signal_roi_manipulated
        self.roi_color = roi_color

        self.roi_names = [] # Names of selected ROIs
        self.all_roi_names = [] # Names of all existing ROIs
        for roi_id, roi_dict in self.rois.items():
            self.all_roi_names.append(roi_dict['name'])

        self.single_roi_operation_names = ["Expand", "Contract",
                                           "Inner Rind (annulus)",
                                           "Outer Rind (annulus)"]
        self.multiple_roi_operation_names = ["Union", "Intersection",
                                             "Difference"]
        self.operation_names = self.multiple_roi_operation_names + \
                               self.single_roi_operation_names

        self.new_ROI_contours = None
        self.manipulate_roi_window_instance = manipulate_roi_window_instance

        self.dicom_view = DicomAxialView(metadata_formatted=True)
        self.dicom_preview = DicomAxialView(metadata_formatted=True)
        self.dicom_view.slider.valueChanged.connect(
            self.dicom_view_slider_value_changed)
        self.dicom_preview.slider.valueChanged.connect(
            self.dicom_preview_slider_value_changed)
        self.init_layout()

        QtCore.QMetaObject.connectSlotsByName(manipulate_roi_window_instance)

    def retranslate_ui(self, manipulate_roi_window_instance):
        _translate = QtCore.QCoreApplication.translate
        manipulate_roi_window_instance.setWindowTitle(_translate("ManipulateRoiWindowInstance", "OnkoDICOM - Draw Region Of Interest"))
        self.first_roi_name_label.setText(_translate("FirstROINameLabel", "ROI 1: "))
        self.first_roi_name_dropdown_list.setPlaceholderText("ROI 1")
        self.first_roi_name_dropdown_list.addItems(self.all_roi_names)
        self.operation_name_label.setText(_translate("OperationNameLabel", "Operation"))
        self.operation_name_dropdown_list.setPlaceholderText("Operation")
        self.operation_name_dropdown_list.addItems(self.operation_names)
        self.second_roi_name_label.setText(_translate("SecondROINameLabel", "ROI 2: "))
        self.second_roi_name_dropdown_list.setPlaceholderText("ROI 2")
        self.second_roi_name_dropdown_list.addItems(self.all_roi_names)
        self.manipulate_roi_window_instance_draw_button.setText(_translate("ManipulateRoiWindowInstanceDrawButton", "Draw"))
        self.manipulate_roi_window_instance_save_button.setText(_translate("ManipulateRoiWindowInstanceSaveButton", "Save"))
        self.manipulate_roi_window_instance_cancel_button.setText(_translate("ManipulateRoiWindowInstanceCancelButton", "Cancel"))
        self.margin_label.setText(_translate("MarginLabel", "Margin (pixels): "))
        self.new_roi_name_label.setText(_translate("NewROINameLabel", "New ROI Name"))
        self.ROI_view_box_label.setText("ROI")
        self.preview_box_label.setText("Preview")

    def init_layout(self):
        """
        Initialize the layout for the DICOM View tab.
        Add the view widget and the slider in the layout.
        Add the whole container 'tab2_view' as a tab in the main page.
        """

        # Initialise a ManipulateROIWindow
        if platform.system() == 'Darwin':
            self.stylesheet_path = "res/stylesheet.qss"
        else:
            self.stylesheet_path = "res/stylesheet-win-linux.qss"
        stylesheet = open(resource_path(self.stylesheet_path)).read()
        window_icon = QIcon()
        window_icon.addPixmap(QPixmap(resource_path("res/images/icon.ico")), QIcon.Normal, QIcon.Off)
        self.manipulate_roi_window_instance.setObjectName("ManipulateRoiWindowInstance")
        self.manipulate_roi_window_instance.setWindowIcon(window_icon)

        # Creating a form box to hold all buttons and input fields
        self.manipulate_roi_window_input_container_box = QFormLayout()
        self.manipulate_roi_window_input_container_box.setObjectName("ManipulateRoiWindowInputContainerBox")
        self.manipulate_roi_window_input_container_box.setLabelAlignment(Qt.AlignLeft)

        # Create a label for denoting the first ROI name
        self.first_roi_name_label = QLabel()
        self.first_roi_name_label.setObjectName("FirstROINameLabel")
        self.first_roi_name_dropdown_list = QComboBox()
        # Create an dropdown list for ROI name
        self.first_roi_name_dropdown_list.setObjectName("FirstROINameDropdownList")
        self.first_roi_name_dropdown_list.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.first_roi_name_dropdown_list.resize(self.first_roi_name_dropdown_list.sizeHint().width(),
                                                 self.first_roi_name_dropdown_list.sizeHint().height())
        self.first_roi_name_dropdown_list.activated.connect(self.update_selected_rois)
        self.manipulate_roi_window_input_container_box.addRow(self.first_roi_name_label,
                                                              self.first_roi_name_dropdown_list)

        # Create a label for denoting the operation
        self.operation_name_label = QLabel()
        self.operation_name_label.setObjectName("OperationNameLabel")
        self.operation_name_dropdown_list = QComboBox()
        # Create an dropdown list for operation name
        self.operation_name_dropdown_list.setObjectName("OperationNameDropdownList")
        self.operation_name_dropdown_list.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.operation_name_dropdown_list.resize(self.operation_name_dropdown_list.sizeHint().width(),
                                                 self.operation_name_dropdown_list.sizeHint().height())
        self.operation_name_dropdown_list.activated.connect(self.operation_changed)
        self.manipulate_roi_window_input_container_box.addRow(self.operation_name_label, self.operation_name_dropdown_list)

        # Create a label for denoting the second ROI name
        self.second_roi_name_label = QLabel()
        self.second_roi_name_label.setObjectName("SecondROINameLabel")
        self.second_roi_name_label.setVisible(False)
        self.second_roi_name_dropdown_list = QComboBox()
        # Create an dropdown list for ROI name
        self.second_roi_name_dropdown_list.setObjectName("SecondROINameDropdownList")
        self.second_roi_name_dropdown_list.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.second_roi_name_dropdown_list.resize(self.second_roi_name_dropdown_list.sizeHint().width(),
                                                  self.second_roi_name_dropdown_list.sizeHint().height())
        self.second_roi_name_dropdown_list.setVisible(False)
        self.second_roi_name_dropdown_list.activated.connect(self.update_selected_rois)
        self.manipulate_roi_window_input_container_box.addRow(self.second_roi_name_label,
                                                              self.second_roi_name_dropdown_list)

        # Create a label for denoting the margin
        self.margin_label = QLabel()
        self.margin_label.setObjectName("MarginLabel")
        self.margin_label.setVisible(False)
        # Create input for the new ROI name
        self.margin_line_edit = QLineEdit()
        self.margin_line_edit.setObjectName("MarginInput")
        self.margin_line_edit.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        self.margin_line_edit.resize(self.margin_line_edit.sizeHint().width(),
                                     self.margin_line_edit.sizeHint().height())
        self.margin_line_edit.setVisible(False)
        self.manipulate_roi_window_input_container_box.addRow(self.margin_label, self.margin_line_edit)

        # Create a label for denoting the new ROI name
        self.new_roi_name_label = QLabel()
        self.new_roi_name_label.setObjectName("NewROINameLabel")
        # Create input for the new ROI name
        self.new_roi_name_line_edit = QLineEdit()
        self.new_roi_name_line_edit.setObjectName("NewROINameInput")
        self.new_roi_name_line_edit.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        self.new_roi_name_line_edit.resize(self.new_roi_name_line_edit.sizeHint().width(),
                                                self.new_roi_name_line_edit.sizeHint().height())
        self.manipulate_roi_window_input_container_box.addRow(self.new_roi_name_label, self.new_roi_name_line_edit)

        # Create a spacer between inputs and buttons
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        spacer.setFocusPolicy(Qt.NoFocus)
        self.manipulate_roi_window_input_container_box.addRow(spacer)

        # Create a draw button
        self.manipulate_roi_window_instance_draw_button = QPushButton()
        self.manipulate_roi_window_instance_draw_button.setObjectName("ManipulateRoiWindowInstanceDrawButton")
        self.manipulate_roi_window_instance_draw_button.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum))
        self.manipulate_roi_window_instance_draw_button.resize(
            self.manipulate_roi_window_instance_draw_button.sizeHint().width(),
            self.manipulate_roi_window_instance_draw_button.sizeHint().height())
        self.manipulate_roi_window_instance_draw_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.manipulate_roi_window_instance_draw_button.clicked.connect(self.onDrawButtonClicked)
        self.manipulate_roi_window_input_container_box.addRow(self.manipulate_roi_window_instance_draw_button)

        # Create a horizontal box for saving and cancel the drawing
        self.manipulate_roi_window_cancel_save_box = QHBoxLayout()
        self.manipulate_roi_window_cancel_save_box.setObjectName("ManipulateRoiWindowCancelSaveBox")
        # Create an exit button to cancel the drawing
        # Add a button to go back/exit from the application
        self.manipulate_roi_window_instance_cancel_button = QPushButton()
        self.manipulate_roi_window_instance_cancel_button.setObjectName("ManipulateRoiWindowInstanceCancelButton")
        self.manipulate_roi_window_instance_cancel_button.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum))
        self.manipulate_roi_window_instance_cancel_button.resize(
            self.manipulate_roi_window_instance_cancel_button.sizeHint().width(),
            self.manipulate_roi_window_instance_cancel_button.sizeHint().height())
        self.manipulate_roi_window_instance_cancel_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.manipulate_roi_window_instance_cancel_button.clicked.connect(self.onCancelButtonClicked)
        self.manipulate_roi_window_instance_cancel_button.setProperty("QPushButtonClass", "fail-button")
        icon_cancel = QtGui.QIcon()
        icon_cancel.addPixmap(QtGui.QPixmap(resource_path('res/images/btn-icons/cancel_icon.png')))
        self.manipulate_roi_window_instance_cancel_button.setIcon(icon_cancel)
        self.manipulate_roi_window_cancel_save_box.addWidget(self.manipulate_roi_window_instance_cancel_button)
        # Create a save button to save all the changes
        self.manipulate_roi_window_instance_save_button = QPushButton()
        self.manipulate_roi_window_instance_save_button.setObjectName("ManipulateRoiWindowInstanceSaveButton")
        self.manipulate_roi_window_instance_save_button.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum))
        self.manipulate_roi_window_instance_save_button.resize(
            self.manipulate_roi_window_instance_save_button.sizeHint().width(),
            self.manipulate_roi_window_instance_save_button.sizeHint().height())
        self.manipulate_roi_window_instance_save_button.setProperty("QPushButtonClass", "success-button")
        icon_save = QtGui.QIcon()
        icon_save.addPixmap(QtGui.QPixmap(resource_path('res/images/btn-icons/save_icon.png')))
        self.manipulate_roi_window_instance_save_button.setIcon(icon_save)
        self.manipulate_roi_window_instance_save_button.clicked.connect(self.onSaveClicked)
        self.manipulate_roi_window_cancel_save_box.addWidget(self.manipulate_roi_window_instance_save_button)
        self.manipulate_roi_window_input_container_box.addRow(self.manipulate_roi_window_cancel_save_box)

        # Creating a horizontal box to hold the ROI view and the preview
        self.manipulate_roi_window_instance_view_box = QHBoxLayout()
        self.manipulate_roi_window_instance_view_box.setObjectName("ManipulateRoiWindowInstanceViewBoxes")
        # Font for the ROI view and preview's labels
        font = QFont()
        font.setBold(True)
        font.setPixelSize(20)
        # Creating the ROI view
        self.ROI_view_box_layout = QVBoxLayout()
        self.ROI_view_box_label = QLabel()
        self.ROI_view_box_label.setFont(font)
        self.ROI_view_box_label.setAlignment(Qt.AlignHCenter)
        self.ROI_view_box_layout.addWidget(self.ROI_view_box_label)
        self.ROI_view_box_layout.addWidget(self.dicom_view)
        self.ROI_view_box_widget = QWidget()
        self.ROI_view_box_widget.setLayout(self.ROI_view_box_layout)
        # Creating the preview
        self.preview_box_layout = QVBoxLayout()
        self.preview_box_label = QLabel()
        self.preview_box_label.setFont(font)
        self.preview_box_label.setAlignment(Qt.AlignHCenter)
        self.preview_box_layout.addWidget(self.preview_box_label)
        self.preview_box_layout.addWidget(self.dicom_preview)
        self.preview_box_widget = QWidget()
        self.preview_box_widget.setLayout(self.preview_box_layout)

        # Add View and Slider into horizontal box
        self.manipulate_roi_window_instance_view_box.addWidget(self.ROI_view_box_widget)
        self.manipulate_roi_window_instance_view_box.addWidget(self.preview_box_widget)
        # Create a widget to hold the image slice box
        self.manipulate_roi_window_instance_view_widget = QWidget()
        self.manipulate_roi_window_instance_view_widget.setObjectName(
            "ManipulateRoiWindowInstanceActionWidget")
        self.manipulate_roi_window_instance_view_widget.setLayout(
            self.manipulate_roi_window_instance_view_box)

        # Create a horizontal box for containing the input fields and the viewports
        self.manipulate_roi_window_main_box = QHBoxLayout()
        self.manipulate_roi_window_main_box.setObjectName("ManipulateRoiWindowMainBox")
        self.manipulate_roi_window_main_box.addLayout(self.manipulate_roi_window_input_container_box, 1)
        self.manipulate_roi_window_main_box.addWidget(self.manipulate_roi_window_instance_view_widget, 11)

        # Create a new central widget to hold the horizontal box layout
        self.manipulate_roi_window_instance_central_widget = QWidget()
        self.manipulate_roi_window_instance_central_widget.setObjectName("ManipulateRoiWindowInstanceCentralWidget")
        self.manipulate_roi_window_instance_central_widget.setLayout(self.manipulate_roi_window_main_box)

        self.retranslate_ui(self.manipulate_roi_window_instance)
        self.manipulate_roi_window_instance.setStyleSheet(stylesheet)
        self.manipulate_roi_window_instance.setCentralWidget(self.manipulate_roi_window_instance_central_widget)
        QtCore.QMetaObject.connectSlotsByName(self.manipulate_roi_window_instance)

    def dicom_view_slider_value_changed(self):
        self.display_selected_roi()

    def dicom_preview_slider_value_changed(self):
        self.draw_roi()

    def onCancelButtonClicked(self):
        """
        This function is used for canceling the drawing
        """
        self.close()

    def onDrawButtonClicked(self):
        """
        Function triggered when the Draw button is pressed from the menu.
        """
        # Check inputs
        selected_operation = self.operation_name_dropdown_list.currentText()
        roi_1 = self.first_roi_name_dropdown_list.currentText()
        roi_2 = self.second_roi_name_dropdown_list.currentText()
        new_roi_name = self.new_roi_name_line_edit.text()

        # Check the selected inputs and execute the operations
        if roi_1 != "" and new_roi_name != "" and \
                self.margin_line_edit.text() != "" and \
                selected_operation in self.single_roi_operation_names:
            # Single ROI operations
            QMessageBox.about(self.manipulate_roi_window_instance,
                              "Operation under implementing",
                              "Single ROI operations have not been supported "
                              "yet.\nPlease select another operation!")
            return
        elif roi_1 != "" and roi_2 != "" and new_roi_name != "" and \
                selected_operation in self.multiple_roi_operation_names:
            # Multiple ROI operations
            dict_rois_contours = ROI.get_roi_contour_pixel(
                self.patient_dict_container.get("raw_contour"),
                [roi_1, roi_2],
                self.patient_dict_container.get("pixluts"))
            roi_1_geometry = ROI.roi_to_geometry(dict_rois_contours[roi_1])
            roi_2_geometry = ROI.roi_to_geometry(dict_rois_contours[roi_2])
            uid_list = ImageLoading.get_image_uid_list(
                self.patient_dict_container.dataset)

            # Execute the selected operation
            new_geometry = ROI.manipulate_rois(roi_1_geometry, roi_2_geometry,
                                               uid_list,
                                               selected_operation.upper())
            self.new_ROI_contours = ROI.geometry_to_roi(new_geometry)

            self.draw_roi()
            return

        QMessageBox.about(self.manipulate_roi_window_instance,
                          "Not Enough Data",
                          "Not all values are specified or correct.")

    def onSaveClicked(self):
        """ Save the new ROI """
        # Get the name of the new ROI
        new_roi_name = self.new_roi_name_line_edit.text()

        if self.new_ROI_contours is None:
            QMessageBox.about(self.manipulate_roi_window_instance,
                              "Empty ROI", "No new ROI has been drawn")
            return

        # Get the required info to create the new ROI
        slider_id = self.dicom_preview.slider.value()
        dataset = self.patient_dict_container.dataset[slider_id]
        location = self.patient_dict_container.filepaths[slider_id]
        ds = pydicom.dcmread(location)
        pixlut = self.patient_dict_container.get("pixluts")
        pixlut = pixlut[dataset.SOPInstanceUID]
        z_coord = dataset.SliceLocation

        # Get the new contour sequence
        if dataset.SOPInstanceUID not in self.new_ROI_contours:
            # TODO: delete after merged with ROI create multiple
            QMessageBox.about(self.manipulate_roi_window_instance,
                              "Empty slice",
                              "The current slice doesn't contain new ROI"
                              "\nPlease move to other slices")
            return
        contour_sequence = self.new_ROI_contours[dataset.SOPInstanceUID]

        # Transform the contour sequence to a 1D array
        # Convert the pixel points to RCS points, then append z coordinate
        single_array = []
        for contour_data in contour_sequence:
            for point in contour_data:
                rcs_pixels = ROI.pixel_to_rcs(pixlut,
                                              round(point[0]),
                                              round(point[1]))
                single_array.append(rcs_pixels[0])
                single_array.append(rcs_pixels[1])
                single_array.append(z_coord)

        # Create a popup window that modifies the RTSTRUCT and tells the user
        # that processing is happening.
        progress_window = SaveROIProgressWindow(self,
                                                QtCore.Qt.WindowTitleHint)
        progress_window.signal_roi_saved.connect(self.roi_saved)
        progress_window.start_saving(self.dataset_rtss, new_roi_name,
                                     single_array, ds)
        progress_window.show()

    def draw_roi(self):
        """ Draw the new ROI """
        # Get the new ROI's name
        new_roi_name = self.new_roi_name_line_edit.text()

        # Check if the new ROI contour is None
        if self.new_ROI_contours is None:
            return

        # Get the info required to draw the new ROI
        slider_id = self.dicom_preview.slider.value()
        curr_slice = self.patient_dict_container.get("dict_uid")[slider_id]

        # Calculate the new ROI's polygon
        dict_ROI_contours = {}
        dict_ROI_contours[new_roi_name] = self.new_ROI_contours
        polygons = ROI.calc_roi_polygon(new_roi_name, curr_slice,
                                        dict_ROI_contours)

        # Set the new ROI color
        color = QtGui.QColor()
        color.setRgb(90, 250, 175, 200)
        pen_color = QtGui.QColor(color.red(), color.green(), color.blue())
        pen = QtGui.QPen(pen_color)
        pen.setStyle(QtCore.Qt.PenStyle(1))
        pen.setWidthF(2.0)

        # Draw the new ROI
        self.dicom_preview.update_view()
        for i in range(len(polygons)):
            self.dicom_preview.scene.addPolygon(polygons[i], pen,
                                                QtGui.QBrush(color))

    def update_selected_rois(self):
        """ Get the names of selected ROIs """
        self.roi_names = []
        if self.first_roi_name_dropdown_list.currentText() != "":
            self.roi_names.append(self.first_roi_name_dropdown_list.currentText())
        if self.second_roi_name_dropdown_list.currentText() != "":
            self.roi_names.append(self.second_roi_name_dropdown_list.currentText())

        self.dict_rois_contours_axial = ROI.get_roi_contour_pixel(
            self.patient_dict_container.get("raw_contour"),
            self.roi_names,
            self.patient_dict_container.get("pixluts"))

        self.display_selected_roi()

    def display_selected_roi(self):
        """ Display selected ROIs """
        # Get the info required to display the selected ROIs
        slider_id = self.dicom_view.slider.value()
        curr_slice = self.patient_dict_container.get("dict_uid")[slider_id]
        self.rois = self.patient_dict_container.get("rois")

        # Display the selected ROIs
        self.dicom_view.update_view()
        for roi_id, roi_dict in self.rois.items():
            roi_name = roi_dict['name']
            if roi_name in self.roi_names:
                polygons = ROI.calc_roi_polygon(roi_name, curr_slice,
                                                self.dict_rois_contours_axial)
                self.dicom_view.draw_roi_polygons(roi_id, polygons, self.roi_color)

    def operation_changed(self):
        selected_operation = self.operation_name_dropdown_list.currentText()
        if selected_operation in self.single_roi_operation_names:
            self.second_roi_name_label.setVisible(False)
            self.second_roi_name_dropdown_list.setVisible(False)
            self.margin_label.setVisible(True)
            self.margin_line_edit.setVisible(True)
        else:
            self.second_roi_name_label.setVisible(True)
            self.second_roi_name_dropdown_list.setVisible(True)
            self.margin_label.setVisible(False)
            self.margin_line_edit.setVisible(False)

    def roi_saved(self, new_rtss):
        new_roi_name = self.new_roi_name_line_edit.text()
        self.signal_roi_manipulated.emit((new_rtss, {"draw": new_roi_name}))
        QMessageBox.about(self.manipulate_roi_window_instance, "Saved",
                          "New contour successfully created!")
        self.close()

class SaveROIProgressWindow(QtWidgets.QDialog):
    """
    This class displays a window that advises the user that the RTSTRUCT is
    being modified, and then creates a new thread where the new RTSTRUCT is
    modified.
    """

    signal_roi_saved = QtCore.Signal(pydicom.Dataset)   # Emits the new dataset

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
        worker = Worker(
            ROI.create_roi, dataset_rtss, roi_name, single_array, ds)

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
