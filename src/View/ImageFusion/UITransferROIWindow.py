import platform
import traceback
from pathlib import Path
from random import randint, seed

import pydicom
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtGui import Qt, QIcon, QPixmap
from PySide6.QtWidgets import QGridLayout, QWidget, QLabel, QPushButton, \
    QCheckBox, QHBoxLayout, QWidgetItem, \
    QListWidget, QListWidgetItem, QMessageBox
from platipy.imaging.label.utils import binary_decode_image, \
    vectorised_transform_index_to_physical_point
from platipy.imaging.registration.utils import apply_linear_transform
from rt_utils import RTStructBuilder
from rt_utils.image_helper import find_mask_contours

from src.Controller.PathHandler import resource_path
from src.Model import ROI, ImageLoading
from src.Model.GetPatientInfo import DicomTree
from src.Model.MovingDictContainer import MovingDictContainer
from src.Model.PatientDictContainer import PatientDictContainer
import SimpleITK as sitk
import numpy as np

from src.Model.ROI import get_roi_contour_pixel, merge_rtss, ordered_list_rois
from src.Model.ROITransfer import transform_point_set_from_dicom_struct
from src.View.util.SaveROIs import connectSaveROIProgress


class UITransferROIWindow:

    def setup_ui(self, transfer_roi_window_instance):
        self.patient_dict_container = PatientDictContainer()
        self.moving_dict_container = MovingDictContainer()
        self.fixed_image_initial_rois = self.patient_dict_container.get("rois")
        self.moving_image_initial_rois = self.moving_dict_container.get("rois")
        self.transfer_roi_window_instance = transfer_roi_window_instance
        self.fixed_to_moving_rois = {}
        self.moving_to_fixed_rois = {}
        self.add_suffix = True
        self.init_layout()

    def retranslate_ui(self, transfer_roi_window_instance):
        _translate = QtCore.QCoreApplication.translate
        transfer_roi_window_instance.setWindowTitle(
            _translate("TransferRoiWindowInstance",
                       "OnkoDICOM - Transfer Region of Interest"))
        self.add_suffix_checkbox.setText(
            _translate("AddSuffixCheckBox", "Add Suffix"))
        self.patient_A_label.setText(
            _translate("PatientAROILabel", "First Image Set ROIs"))
        self.patient_B_label.setText(
            _translate("PatientBROILabel", "Second Image Set ROIs"))
        self.transfer_all_rois_to_patient_B_button.setText(
            _translate("ROITransferToBButton", "")
        )
        self.transfer_all_rois_to_patient_A_button.setText(
            _translate("ROITransferToAButton", "")
        )
        self.save_button.setText(
            _translate("SaveButton", "Save")
        )
        self.reset_button.setText(
            _translate("ResetButton", "Reset")
        )

    def init_layout(self):
        if platform.system() == 'Darwin':
            self.stylesheet_path = "res/stylesheet.qss"
        else:
            self.stylesheet_path = "res/stylesheet-win-linux.qss"
        stylesheet = open(resource_path(self.stylesheet_path)).read()
        window_icon = QIcon()
        window_icon.addPixmap(QPixmap(resource_path("res/images/icon.ico")),
                              QIcon.Normal, QIcon.Off)
        self.transfer_roi_window_instance.setObjectName(
            "TransferRoiWindowInstance")
        self.transfer_roi_window_instance.setWindowIcon(window_icon)

        # Creating a grid layout to hold all elements
        self.transfer_roi_window_grid_layout = QGridLayout()
        self.transfer_roi_window_grid_layout.setColumnStretch(0, 1)
        self.transfer_roi_window_grid_layout.setColumnStretch(1, 1)
        self.transfer_roi_window_grid_layout.setColumnStretch(2, 1)

        self.init_patient_labels()
        self.init_transfer_arrow_buttons()
        self.init_patient_A_initial_roi_list()
        self.init_patient_B_rois_to_A_layout()
        self.init_patient_A_rois_to_B_layout()
        self.init_patient_B_initial_roi_list()
        self.init_add_suffix_checkbox()
        self.init_save_and_reset_button_layout()

        # Create a new central widget to hold the grid layout
        self.transfer_roi_window_instance_central_widget = QWidget()
        self.transfer_roi_window_instance_central_widget.setLayout(
            self.transfer_roi_window_grid_layout)
        self.retranslate_ui(self.transfer_roi_window_instance)
        self.transfer_roi_window_instance.setStyleSheet(stylesheet)
        self.transfer_roi_window_instance.setCentralWidget(
            self.transfer_roi_window_instance_central_widget)
        QtCore.QMetaObject.connectSlotsByName(
            self.transfer_roi_window_instance)

    def init_transfer_arrow_buttons(self):
        self.transfer_all_rois_to_patient_B_button = QPushButton()
        self.transfer_all_rois_to_patient_B_button.setObjectName(
            "ROITransferToBButton")
        # TODO: Add icon to button
        self.transfer_all_rois_to_patient_B_button.setMaximumWidth(100)
        self.transfer_all_rois_to_patient_B_button.clicked.connect(
            self.transfer_all_rois_to_patient_B_button_clicked)
        self.transfer_roi_window_grid_layout.addWidget(
            self.transfer_all_rois_to_patient_B_button, 1, 1)

        self.transfer_all_rois_to_patient_A_button = QPushButton()
        self.transfer_all_rois_to_patient_A_button.setObjectName(
            "ROITransferToAButton")
        # TODO: Add icon to button
        self.transfer_all_rois_to_patient_A_button.setText("<<")
        self.transfer_all_rois_to_patient_A_button.setMaximumWidth(100)
        self.transfer_all_rois_to_patient_A_button.clicked.connect(
            self.transfer_all_rois_to_patient_A_button_clicked)
        self.transfer_roi_window_grid_layout.addWidget(
            self.transfer_all_rois_to_patient_A_button, 2, 1)

    def transfer_all_rois_to_patient_B_button_clicked(self):
        self.fixed_to_moving_rois.clear()
        self.patient_A_rois_to_B_list_widget.clear()

        for i in range(0, len(self.fixed_image_initial_rois)):
            self.patient_A_initial_roi_double_clicked(
                self.patient_A_initial_rois_list_widget.item(i))

    def transfer_all_rois_to_patient_A_button_clicked(self):
        self.moving_to_fixed_rois.clear()
        self.patient_B_rois_to_A_list_widget.clear()

        for i in range(0, len(self.moving_image_initial_rois)):
            self.patient_B_initial_roi_double_clicked(
                self.patient_B_initial_rois_list_widget.item(i))

    def init_add_suffix_checkbox(self):
        self.add_suffix_checkbox = QCheckBox()
        self.add_suffix_checkbox.setObjectName("AddSuffixCheckBox")
        self.add_suffix_checkbox.setChecked(self.add_suffix)
        self.add_suffix_checkbox.clicked.connect(
            self.add_suffix_checkbox_clicked)
        self.transfer_roi_window_grid_layout.addWidget(
            self.add_suffix_checkbox, 3, 0)

    def init_patient_labels(self):
        self.patient_A_label = QLabel()
        self.patient_A_label.setObjectName("PatientAROILabel")
        self.patient_A_label.setMinimumHeight(50)
        self.patient_A_label.setAlignment(Qt.AlignCenter)
        self.patient_A_label.setStyleSheet(
            "QLabel { background-color : green; color : white; font-size: 15pt; font-weight: bold;}")

        self.patient_B_label = QLabel()
        self.patient_B_label.setObjectName("PatientBROILabel")
        self.patient_B_label.setMinimumHeight(50)
        self.patient_B_label.setAlignment(Qt.AlignCenter)
        self.patient_B_label.setStyleSheet(
            "QLabel { background-color : red; color : white; font-size: 15pt; font-weight: bold;}")

        self.transfer_roi_window_grid_layout.addWidget(self.patient_A_label, 0,
                                                       0)
        self.transfer_roi_window_grid_layout.addWidget(self.patient_B_label, 0,
                                                       2)

    def init_save_and_reset_button_layout(self):
        self.reset_and_save_buttons_layout = QHBoxLayout()
        self.reset_button = QPushButton()
        self.reset_button.setObjectName("ResetButton")
        self.reset_button.clicked.connect(self.reset_clicked)
        self.save_button = QPushButton()
        self.save_button.setObjectName("SaveButton")
        self.save_button.setDisabled(True)
        self.save_button.clicked.connect(self.save_clicked)

        self.reset_and_save_buttons_layout.setAlignment(Qt.AlignRight)
        self.reset_and_save_buttons_layout.addWidget(self.reset_button)
        self.reset_and_save_buttons_layout.addWidget(self.save_button)

        # Create a widget to hold Reset and Save buttons
        self.reset_and_save_button_central_widget = QWidget()
        self.reset_and_save_button_central_widget.setLayout(
            self.reset_and_save_buttons_layout)

        self.transfer_roi_window_grid_layout.addWidget(
            self.reset_and_save_button_central_widget, 3, 2)

    def add_suffix_checkbox_clicked(self):
        self.add_suffix = self.add_suffix_checkbox.isChecked()

    def init_patient_B_rois_to_A_layout(self):
        # Create scrolling area widget to contain the content.
        self.patient_B_rois_to_A_list_widget = QListWidget(self)
        self.transfer_roi_window_grid_layout.addWidget(self.patient_B_rois_to_A_list_widget, 2, 0)
        self.patient_B_rois_to_A_list_widget.itemDoubleClicked.connect(
            self.patient_B_to_A_rois_double_clicked)

    def init_patient_A_rois_to_B_layout(self):
        self.patient_A_rois_to_B_list_widget = QListWidget(self)
        self.transfer_roi_window_grid_layout.addWidget(self.patient_A_rois_to_B_list_widget, 1, 2)
        self.patient_A_rois_to_B_list_widget.itemDoubleClicked.connect(
            self.patient_A_to_B_rois_double_clicked)

    def init_patient_A_initial_roi_list(self):
        self.patient_A_initial_rois_list_widget = QListWidget(self)
        self.patient_A_initial_rois_list_widget.itemDoubleClicked.connect(
            self.patient_A_initial_roi_double_clicked)
        for idx in self.fixed_image_initial_rois:
            roi_label = QListWidgetItem(
                self.fixed_image_initial_rois[idx]['name'])
            roi_label.setForeground(Qt.darkGreen)
            roi_label.setData(Qt.UserRole, self.fixed_image_initial_rois[idx])
            self.patient_A_initial_rois_list_widget.addItem(roi_label)
        self.transfer_roi_window_grid_layout.addWidget(
            self.patient_A_initial_rois_list_widget, 1, 0)

    def init_patient_B_initial_roi_list(self):
        self.patient_B_initial_rois_list_widget = QListWidget(self)
        self.patient_B_initial_rois_list_widget.itemDoubleClicked.connect(
            self.patient_B_initial_roi_double_clicked)
        for idx in self.moving_image_initial_rois:
            roi_label = QListWidgetItem(
                self.moving_image_initial_rois[idx]['name'])
            roi_label.setForeground(Qt.red)
            roi_label.setData(Qt.UserRole, self.moving_image_initial_rois[idx])

            self.patient_B_initial_rois_list_widget.addItem(roi_label)
        self.transfer_roi_window_grid_layout.addWidget(
            self.patient_B_initial_rois_list_widget, 2, 2)

    def patient_A_to_B_rois_double_clicked(self, item):
        roi_to_remove = item.data(Qt.UserRole)
        to_delete_value = roi_to_remove['name']
        self.fixed_to_moving_rois.pop(to_delete_value)
        self.patient_A_rois_to_B_list_widget.clear()
        for key, value in self.fixed_to_moving_rois.items():
            roi_label = QListWidgetItem(value)
            roi_label.setForeground(Qt.red)
            roi_label.setData(Qt.UserRole, {'name': key})
            self.patient_A_rois_to_B_list_widget.addItem(roi_label)
        if self.transfer_list_is_empty():
            self.save_button.setDisabled(True)

    def patient_B_to_A_rois_double_clicked(self, item):
        roi_to_remove = item.data(Qt.UserRole)
        to_delete_value = roi_to_remove['name']
        self.moving_to_fixed_rois.pop(to_delete_value)
        self.patient_B_rois_to_A_list_widget.clear()
        for key, value in self.moving_to_fixed_rois.items():
            roi_label = QListWidgetItem(value)
            roi_label.setForeground(Qt.red)
            roi_label.setData(Qt.UserRole, {'name': key})
            self.patient_B_rois_to_A_list_widget.addItem(roi_label)
        if self.transfer_list_is_empty():
            self.save_button.setDisabled(True)

    def patient_A_initial_roi_double_clicked(self, item):
        roi_to_add = item.data(Qt.UserRole)
        transferred_roi_name = roi_to_add['name']

        # If the clicked roi is already transferred, return
        if transferred_roi_name in self.fixed_to_moving_rois.keys():
            QMessageBox.about(self, "Transfer Failed",
                              "Chosen ROI has already been transferred!")
            return
        # Create a set to store all current roi names in target patient
        # including both initial rois name and added roi names so far
        patient_B_initial_roi_name_list = set()

        for item in self.fixed_to_moving_rois.values():
            patient_B_initial_roi_name_list.add(item)
        for idx in self.moving_image_initial_rois:
            patient_B_initial_roi_name_list.add(
                self.moving_image_initial_rois[idx]['name'])

        # Check if clicked roi name has duplicate in patient B's initial roi names list
        if transferred_roi_name in patient_B_initial_roi_name_list:
            if self.add_suffix:
                changed_name = transferred_roi_name
                i = 1
                while changed_name in patient_B_initial_roi_name_list:
                    changed_name = transferred_roi_name + "_" + chr(i + 64)
                    i = i + 1
                transferred_roi_name = changed_name
            else:
                QMessageBox.about(self, "Transfer Failed",
                                  "Duplicated ROI name. Please consider adding suffix.")
                return

        # Add clicked roi to transferred list
        self.fixed_to_moving_rois[roi_to_add['name']] = transferred_roi_name
        roi_label = QListWidgetItem(transferred_roi_name)
        roi_label.setForeground(Qt.red)
        roi_label.setData(Qt.UserRole, roi_to_add)
        self.patient_A_rois_to_B_list_widget.addItem(roi_label)
        self.save_button.setDisabled(False)

    def patient_B_initial_roi_double_clicked(self, item):
        roi_to_add = item.data(Qt.UserRole)
        transferred_roi_name = roi_to_add['name']

        # If the clicked roi is already transferred, return
        if transferred_roi_name in self.moving_to_fixed_rois.keys():
            QMessageBox.about(self, "Transfer Failed",
                              "Chosen ROI has already been transferred!")
            return

        # Create a set to store all current roi names in target patient
        # including both initial rois name and added roi names so far
        patient_A_current_roi_name_list = set()

        for item in self.moving_to_fixed_rois.values():
            patient_A_current_roi_name_list.add(item)

        for idx in self.fixed_image_initial_rois:
            patient_A_current_roi_name_list.add(
                self.fixed_image_initial_rois[idx]['name'])

        # Check if clicked roi name has duplicate in target patient's roi names list
        if transferred_roi_name in patient_A_current_roi_name_list:
            # if add suffix is ticked, iteratively try adding suffix
            # from _A to _Z, stop when no duplicate found
            if self.add_suffix:
                changed_name = transferred_roi_name
                i = 1
                while changed_name in patient_A_current_roi_name_list:
                    changed_name = transferred_roi_name + "_" + chr(i + 64)
                    i = i + 1
                transferred_roi_name = changed_name
            else:
                QMessageBox.about(self, "Transfer Failed",
                                  "Duplicated ROI name. Please consider adding suffix.")
                return

        # Add clicked roi to transferred list
        self.moving_to_fixed_rois[roi_to_add['name']] = transferred_roi_name
        roi_label = QListWidgetItem(transferred_roi_name)
        roi_label.setForeground(Qt.red)
        roi_label.setData(Qt.UserRole, roi_to_add)
        self.patient_B_rois_to_A_list_widget.addItem(roi_label)
        self.save_button.setDisabled(False)

    def reset_clicked(self):
        self.fixed_to_moving_rois.clear()
        self.moving_to_fixed_rois.clear()
        self.patient_A_rois_to_B_list_widget.clear()
        self.patient_B_rois_to_A_list_widget.clear()
        self.save_button.setDisabled(True)

    def transfer_list_is_empty(self):
        return len(self.fixed_to_moving_rois) == 0 and len(self.moving_to_fixed_rois) == 0

    def save_clicked(self):
        try:
            rtss = self.patient_dict_container.get("dataset_rtss")

            # get sitk for fixed and moving images
            dicom_image = self.read_dicom_image_to_sitk(
                self.patient_dict_container.filepaths)
            # get array of roi indexes from sitk images
            rois_images_fixed = transform_point_set_from_dicom_struct(dicom_image,
                                                                      rtss,
                                                                      self.fixed_to_moving_rois.keys(),
                                                                      spacing_override=None)
            moving_rtss = self.moving_dict_container.get("dataset_rtss")
            moving_dicom_image = self.read_dicom_image_to_sitk(
                self.moving_dict_container.filepaths)
            # get array of roi indexes from sitk images
            if moving_rtss:
                rois_images_moving = transform_point_set_from_dicom_struct(
                    moving_dicom_image,
                    moving_rtss,
                    self.moving_to_fixed_rois.keys(),
                    spacing_override=None)
            else:
                rois_images_moving = ([], [])
            tfm = self.moving_dict_container.get("tfm")
            # TODO: HANDLE CASE WHEN ONE OF TWO DICTS ARE EMPTY
            # transform roi from b to a first
            self.transfer_rois(self.moving_to_fixed_rois, tfm, dicom_image,
                               rois_images_moving, self.patient_dict_container)

            # transform roi from a to b
            self.transfer_rois(self.fixed_to_moving_rois, tfm.GetInverse(),
                               moving_dicom_image,
                               rois_images_fixed, self.moving_dict_container)

            if len(self.fixed_to_moving_rois) > 0:
                # TODO: merge update-moving-dict-structure with
                # update patient_dict_structure
                self.update_moving_dict_structure()
                self.save_roi_to_rtss(self.moving_dict_container)
            if len(self.moving_to_fixed_rois) > 0:
                self.update_patient_dict_structure()
                self.save_roi_to_rtss(self.patient_dict_container)
        except Exception as e:
            traceback.print_exc()
        QMessageBox.about(self.transfer_roi_window_instance, "Saved",
                          "ROIs are successfully transferred!")
        self.closeWindow()

    def update_patient_dict_structure(self):
        # TODO: merge update-moving-dict-structure with
        # update patient_dict_structure
        self.patient_dict_container.set("rtss_modified", True)
        self.patient_dict_container.set(
            "rois", ImageLoading.get_roi_info(self.patient_dict_container.get("dataset_rtss")))
        self.rois = self.patient_dict_container.get("rois")
        contour_data = ImageLoading.get_raw_contour_data(self.patient_dict_container.get("dataset_rtss"))
        self.patient_dict_container.set("raw_contour", contour_data[0])
        self.patient_dict_container.set("num_points", contour_data[1])
        pixluts = ImageLoading.get_pixluts(self.patient_dict_container.dataset)
        self.patient_dict_container.set("pixluts", pixluts)
        self.patient_dict_container.set("list_roi_numbers", ordered_list_rois(
            self.patient_dict_container.get("rois")))
        self.patient_dict_container.set("selected_rois", [])
        self.patient_dict_container.set("dict_polygons_axial", {})
        self.patient_dict_container.set("dict_polygons_sagittal", {})
        self.patient_dict_container.set("dict_polygons_coronal", {})
        dicom_tree_rtss = DicomTree(None)
        dicom_tree_rtss.dataset = self.patient_dict_container.get("dataset_rtss")
        dicom_tree_rtss.dict = dicom_tree_rtss.dataset_to_dict(
            dicom_tree_rtss.dataset)
        self.patient_dict_container.set(
            "dict_dicom_tree_rtss", dicom_tree_rtss.dict)
        self.color_dict = self.init_color_roi(self.patient_dict_container)
        self.patient_dict_container.set("roi_color_dict", self.color_dict)
        if self.patient_dict_container.has_attribute("raw_dvh"):
            # DVH will be outdated once changes to it are made, and
            # recalculation will be required.
            self.patient_dict_container.set("dvh_outdated", True)

    def update_moving_dict_structure(self):
        # TODO: merge update-moving-dict-structure with
        # update patient_dict_structure
        self.moving_dict_container.set("rtss_modified", True)
        self.moving_dict_container.set(
            "rois", ImageLoading.get_roi_info(self.moving_dict_container.get("dataset_rtss")))
        self.rois = self.moving_dict_container.get("rois")
        contour_data = ImageLoading.get_raw_contour_data(self.moving_dict_container.get("dataset_rtss"))
        self.moving_dict_container.set("raw_contour", contour_data[0])
        self.moving_dict_container.set("num_points", contour_data[1])
        pixluts = ImageLoading.get_pixluts(self.moving_dict_container.dataset)
        self.moving_dict_container.set("pixluts", pixluts)
        self.moving_dict_container.set("list_roi_numbers", ordered_list_rois(
            self.moving_dict_container.get("rois")))
        self.moving_dict_container.set("selected_rois", [])
        self.moving_dict_container.set("dict_polygons_axial", {})
        self.moving_dict_container.set("dict_polygons_sagittal", {})
        self.moving_dict_container.set("dict_polygons_coronal", {})
        dicom_tree_rtss = DicomTree(None)
        dicom_tree_rtss.dataset = self.moving_dict_container.get("dataset_rtss")
        dicom_tree_rtss.dict = dicom_tree_rtss.dataset_to_dict(
            dicom_tree_rtss.dataset)
        self.moving_dict_container.set(
            "dict_dicom_tree_rtss", dicom_tree_rtss.dict)
        self.color_dict = self.init_color_roi(self.moving_dict_container)
        self.moving_dict_container.set("roi_color_dict", self.color_dict)
        if self.moving_dict_container.has_attribute("raw_dvh"):
            # DVH will be outdated once changes to it are made, and
            # recalculation will be required.
            self.moving_dict_container.set("dvh_outdated", True)

    def init_color_roi(self, patient_dict_container):
        """
        Create a dictionary containing the colors for each structure.
        :return: Dictionary where the key is the ROI number and the value a
        QColor object.
        """
        roi_color = dict()
        roi_contour_info = patient_dict_container.get(
            "dict_dicom_tree_rtss")['ROI Contour Sequence']

        if len(roi_contour_info) > 0:
            for item, roi_dict in roi_contour_info.items():
                id = item.split()[1]
                roi_id = patient_dict_container.get(
                    "list_roi_numbers")[int(id)]
                if 'ROI Display Color' in roi_contour_info[item]:
                    RGB_list = roi_contour_info[item]['ROI Display Color'][0]
                    red = RGB_list[0]
                    green = RGB_list[1]
                    blue = RGB_list[2]
                else:
                    seed(1)
                    red = randint(0, 255)
                    green = randint(0, 255)
                    blue = randint(0, 255)

                roi_color[roi_id] = QtGui.QColor(red, green, blue)

        return roi_color

    def transfer_rois(self, transfer_dict, tfm, reference_image,
                      original_roi_list, patient_dict_container):
        for roi_name, new_roi_name in transfer_dict.items():
            for index, name in enumerate(original_roi_list[1]):
                if name == roi_name:
                    sitk_image = original_roi_list[0][index]
                    new_contour = apply_linear_transform(
                        input_image=sitk_image, transform=tfm,
                        reference_image=reference_image, is_structure=True)
                    contour = sitk.GetArrayViewFromImage(new_contour)
                    contours = np.transpose(contour.nonzero())
                    self.save_roi(contours, new_roi_name,
                                  patient_dict_container)

    def save_roi(self, contours, roi_name, patient_dict_container):
        pixels_coords_dict = {}
        for contour in contours:
            curr_slice_id = contour[0]
            if curr_slice_id not in pixels_coords_dict:
                pixels_coords_dict[curr_slice_id] = [
                    tuple([contour[2], contour[1]])]
            else:
                pixels_coords_dict[curr_slice_id].append(
                    tuple([contour[2], contour[1]]))

        rois_to_save = {}
        # TODO: optimise this bc it's redundant
        for key in pixels_coords_dict.keys():
            coords = pixels_coords_dict[key]
            polygon_list = ROI.calculate_concave_hull_of_points(coords)
            if len(polygon_list) > 0:
                rois_to_save[key] = {
                    'ds': patient_dict_container.dataset[key],
                    'coords': polygon_list
                }
        roi_list = ROI.convert_hull_list_to_contours_data(
            rois_to_save, patient_dict_container)

        if len(roi_list) > 0:
            print("Saving ", roi_name)
            if isinstance(patient_dict_container, MovingDictContainer):
                new_rtss = ROI.create_roi(patient_dict_container.get("dataset_rtss"),
                                          roi_name, roi_list, "ORGAN", "MOVING")
                self.moving_dict_container.set("dataset_rtss", new_rtss)
            else:
                new_rtss = ROI.create_roi(patient_dict_container.get("dataset_rtss"),
                                          roi_name, roi_list)
                self.patient_dict_container.set("dataset_rtss", new_rtss)

    def save_roi_to_rtss(self, patient_dict_container):
        """
        Save the current RTSS stored in patient dictionary to the file system.
        :patient_dict_container: either patient or moving patient container
        :param auto: Used for auto save without user confirmation
        """
        if patient_dict_container.get("existing_file_rtss") is not None:
            existing_rtss_directory = str(Path(patient_dict_container.get(
                "existing_file_rtss")))
        else:
            existing_rtss_directory = None
        rtss_directory = str(
            Path(patient_dict_container.get("file_rtss")))

        if existing_rtss_directory is None:
            patient_dict_container.get("dataset_rtss").save_as(
                rtss_directory)
        else:
            new_rtss = patient_dict_container.get("dataset_rtss")
            old_rtss = pydicom.dcmread(existing_rtss_directory, force=True)
            old_roi_names = \
                set(value["name"] for value in
                    ImageLoading.get_roi_info(old_rtss).values())
            new_roi_names = \
                set(value["name"] for value in
                    patient_dict_container.get("rois").values())
            duplicated_names = old_roi_names.intersection(new_roi_names)
            merged_rtss = merge_rtss(old_rtss, new_rtss, duplicated_names)
            merged_rtss.save_as(existing_rtss_directory)

    def closeWindow(self):
        """
        function to close transfer roi window
        """
        self.close()

    def read_dicom_image_to_sitk(self, filepaths):
        amount = len(filepaths)
        orig_fusion_list = []

        for i in range(amount):
            try:
                orig_fusion_list.append(filepaths[i])
            except KeyError:
                continue

        return sitk.ReadImage(orig_fusion_list)
