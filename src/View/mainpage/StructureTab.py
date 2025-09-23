import csv
import pydicom
from pathlib import Path
from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtCore import Qt
import numpy as np
from src.Controller.ROIOptionsController import ROIDelOption, \
    ROIManipulateOption
from src.Model.DICOM.Structure.DICOMSeries import Series
from src.Model import ImageLoading
from src.Model.CalculateDVHs import dvh2rtdose
from src.Model.GetPatientInfo import DicomTree
from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.MovingDictContainer import MovingDictContainer
from src.Model.ROI import ordered_list_rois, get_roi_contour_pixel, \
    calc_roi_polygon, transform_rois_contours, merge_rtss
from src.View.mainpage.StructureWidget import StructureWidget
from src.View.util.SelectRTSSPopUp import SelectRTSSPopUp
from src.Controller.PathHandler import data_path, resource_path


class StructureTab(QtWidgets.QWidget):
    request_update_structures = QtCore.Signal()
    signal_roi_draw = QtCore.Signal()

    def __init__(self, moving=False):
        QtWidgets.QWidget.__init__(self)
        self.patient_dict_container = PatientDictContainer()
        self.moving_dict_container = MovingDictContainer()
        self.rois = self.patient_dict_container.get("rois")
        self.color_dict = self.init_color_roi(self.patient_dict_container)
        self.patient_dict_container.set("roi_color_dict", self.color_dict)
        self.structure_tab_layout = QtWidgets.QVBoxLayout()

        self.roi_delete_handler = ROIDelOption(
            self.fixed_container_structure_modified)
        self.roi_manipulate_handler = ROIManipulateOption(
            self.fixed_container_structure_modified)

        # Create scrolling area widget to contain the content.
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.scroll_area_content = QtWidgets.QWidget(self.scroll_area)
        self.scroll_area.ensureWidgetVisible(self.scroll_area_content)

        # Create layout for checkboxes and colour squares
        self.layout_content = QtWidgets.QVBoxLayout(self.scroll_area_content)
        self.layout_content.setContentsMargins(0, 0, 0, 0)
        self.layout_content.setSpacing(0)
        self.layout_content.setAlignment(
            QtCore.Qt.AlignTop | QtCore.Qt.AlignTop)

        # Create list of standard organ and volume names
        self.standard_organ_names = []
        self.standard_volume_names = []
        self.init_standard_names()

        # Create StructureWidget objects
        self.update_content()

        # Create a modified indicator
        self.modified_indicator_widget = QtWidgets.QWidget()
        self.modified_indicator_widget.setContentsMargins(8, 5, 8, 5)
        modified_indicator_layout = QtWidgets.QHBoxLayout()
        modified_indicator_layout.setAlignment(
            QtCore.Qt.AlignLeft | QtCore.Qt.AlignLeft)

        modified_indicator_icon = QtWidgets.QLabel()
        modified_indicator_icon.setPixmap(QtGui.QPixmap(
            resource_path("res/images/btn-icons/alert_icon.png")))
        modified_indicator_layout.addWidget(modified_indicator_icon)

        modified_indicator_text = QtWidgets.QLabel(
            "Structures have been modified")
        modified_indicator_text.setStyleSheet("color: red")
        modified_indicator_layout.addWidget(modified_indicator_text)

        self.modified_indicator_widget.setLayout(modified_indicator_layout)
        self.modified_indicator_widget.mouseReleaseEvent = self. \
            save_new_rtss_to_fixed_image_set
        self.modified_indicator_widget.setVisible(False)

        # Create ROI manipulation buttons
        self.button_roi_manipulate = QtWidgets.QPushButton()
        self.button_roi_draw = QtWidgets.QPushButton()
        self.button_roi_delete = QtWidgets.QPushButton()
        self.roi_buttons = QtWidgets.QWidget()
        self.init_roi_buttons()

        # Set layout
        self.structure_tab_layout.addWidget(self.scroll_area)
        self.structure_tab_layout.addWidget(self.modified_indicator_widget)
        self.structure_tab_layout.addWidget(self.roi_buttons)
        self.setLayout(self.structure_tab_layout)

    def init_color_roi(self, dict_container):
        """
        Generates a dictionary mapping ROI IDs to their display colors.
        The function gets the ROI contour information from the dictionary container input,
        assigns a color to each ROI (using the specified color if available, or a random color otherwise),
        and returns a dictionary mapping ROI IDs to QColor objects.

        Args:
            dict_container: The container holding DICOM RTSS data (either PatientDict or MovingDict).

        Returns:
            dict: A dictionary mapping ROI IDs to QColor objects.
        """
        roi_color = {}
        rtss = dict_container.get("dict_dicom_tree_rtss")
        roi_contour_info = rtss.get("ROI Contour Sequence")

        # Check if roi contour data dictionary exists
        if isinstance(roi_contour_info, dict) and roi_contour_info:
            for roi_key, roi_dict in roi_contour_info.items():
                # Get roi numbers list if available
                roi_numbers = roi_dict.get("Referenced ROI Number")

                # Check exists and is list
                if isinstance(roi_numbers, list) and roi_numbers:
                    roi_id = roi_numbers[0]
                else:
                    continue  # skip if invalid

                # Get ROI color list if available
                roi_colors = roi_dict.get("ROI Display Color")

                # Check ROI colors is a non-empty list of lists
                if isinstance(roi_colors, list) and roi_colors and all(isinstance(color, list) for color in roi_colors)\
                        and len(roi_colors[0]) == 3 and all(isinstance(color, (int, float)) for color in roi_colors[0]):
                    r, g, b = roi_colors[0]     # Assign colors from roi color list
                else:
                    r, g, b = np.random.default_rng(seed=roi_id).integers(0, 256, 3) # Assign random colors

                roi_color[roi_id] = QtGui.QColor(r, g, b)

        return roi_color

    def init_standard_names(self):
        """
        Create two lists containing standard organ and standard volume names
        as set by the Add-On options.
        """
        with open(data_path('organName.csv'), 'r') as f:
            self.standard_organ_names = []

            csv_input = csv.reader(f)
            header = next(f)  # Ignore the "header" of the column
            for row in csv_input:
                self.standard_organ_names.append(row[0])

        with open(data_path('volumeName.csv'), 'r') as f:
            self.standard_volume_names = []

            csv_input = csv.reader(f)
            header = next(f)  # Ignore the "header" of the column
            for row in csv_input:
                self.standard_volume_names.append(row[1])

    def init_roi_buttons(self):
        icon_roi_delete = QtGui.QIcon()
        icon_roi_delete.addPixmap(
            QtGui.QPixmap(
                resource_path('res/images/btn-icons/delete_icon.png')),
            QtGui.QIcon.Normal,
            QtGui.QIcon.On
        )

        icon_roi_draw = QtGui.QIcon()
        icon_roi_draw.addPixmap(
            QtGui.QPixmap(resource_path('res/images/btn-icons/draw_icon.png')),
            QtGui.QIcon.Normal,
            QtGui.QIcon.On
        )

        icon_roi_manipulate = QtGui.QIcon()
        icon_roi_manipulate.addPixmap(
            QtGui.QPixmap(
                resource_path('res/images/btn-icons/manipulate_icon.png')),
            QtGui.QIcon.Normal,
            QtGui.QIcon.On
        )

        self.button_roi_delete.setIcon(icon_roi_delete)
        self.button_roi_delete.setText("Delete ROI")
        self.button_roi_delete.clicked.connect(self.roi_delete_clicked)

        self.button_roi_draw.setIcon(icon_roi_draw)
        self.button_roi_draw.setText("Draw ROI")
        self.button_roi_draw.clicked.connect(self.roi_draw_clicked)

        self.button_roi_manipulate.setIcon(icon_roi_manipulate)
        self.button_roi_manipulate.setText("Manipulate ROI")
        self.button_roi_manipulate.clicked.connect(self.roi_manipulate_clicked)

        layout_roi_buttons = QtWidgets.QVBoxLayout(self.roi_buttons)
        layout_roi_buttons.setContentsMargins(0, 0, 0, 0)
        layout_roi_buttons.addWidget(self.button_roi_draw)
        layout_roi_buttons.addWidget(self.button_roi_manipulate)
        layout_roi_buttons.addWidget(self.button_roi_delete)

    def update_ui(self, moving=False):
        """
        Update the UI of Structure Tab when a new patient is opened
        """
        self.patient_dict_container = PatientDictContainer()
        self.rois = self.patient_dict_container.get("rois")
        self.color_dict = self.init_color_roi(self.patient_dict_container)
        self.patient_dict_container.set("roi_color_dict", self.color_dict)
        if hasattr(self, "modified_indicator_widget"):
            self.modified_indicator_widget.setParent(None)
        self.update_content()

    def update_content(self):
        """
        Add the contents (color square and checkbox) in the scrolling area
        widget.
        """
        # Clear the children
        for i in reversed(range(self.layout_content.count())):
            self.layout_content.itemAt(i).widget().setParent(None)

        row = 0
        for roi_id, roi_dict in self.rois.items():
            # Creates a widget representing each ROI
            color = self.color_dict[roi_id]
            color.setAlpha(255)
            structure = StructureWidget(roi_id, color, roi_dict['name'], self)
            if roi_id in self.patient_dict_container.get("selected_rois"):
                structure.checkbox.setChecked(Qt.Checked)
            structure.structure_renamed. \
                connect(self.fixed_container_structure_modified)
            self.layout_content.addWidget(structure)
            row += 1

        self.scroll_area.setStyleSheet(
            "QScrollArea {background-color: #ffffff; border-style: none;}")
        self.scroll_area_content.setStyleSheet(
            "QWidget {background-color: #ffffff; border-style: none;}")

        self.scroll_area.setWidget(self.scroll_area_content)

    def roi_delete_clicked(self):
        self.roi_delete_handler.show_roi_delete_options()

    def roi_draw_clicked(self):
        self.signal_roi_draw.emit()

    def roi_manipulate_clicked(self):
        """ Open ROI Manipulate Window """
        self.roi_manipulate_handler.show_roi_manipulate_options(
            self.color_dict)

    def moving_container_structure_modified(self, changes):
        """
        Executes when a structure of moving container is modified.
        Changes is a tuple of (new_dataset,
        description_of_changes)
        description_of_changes follows the format
        {"type_of_change": value_of_change}.
        Examples:
        {"rename": ["TOOTH", "TEETH"]} represents that the TOOTH structure has
            been renamed to TEETH.
        {"delete": ["TEETH", "MAXILLA"]} represents that the TEETH and MAXILLA
            structures have been deleted.
        {"draw": "AORTA"} represents that a new structure AORTA has been drawn.
        Note: Use {"draw": None} after multiple ROIs are generated
        (E.g., from ISO2ROI functionality), and use {"transfer":None} for
         ROI Transfer instead of calling this function
        multiple times. This will trigger auto save.
        """
        new_dataset = changes[0]
        change_description = changes[1]

        # If this is the first change made to the RTSS file, update the
        # dataset with the new one so that OnkoDICOM starts working off this
        # dataset rather than the original RTSS file.
        self.moving_dict_container.set("rtss_modified", True)
        self.moving_dict_container.set("dataset_rtss", new_dataset)

        # Refresh ROIs in main page
        self.moving_dict_container.set(
            "rois", ImageLoading.get_roi_info(new_dataset))
        self.rois = self.moving_dict_container.get("rois")
        contour_data = ImageLoading.get_raw_contour_data(new_dataset)
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

        if "draw" in change_description or "transfer" in change_description:
            dicom_tree_rtss = DicomTree(None)
            dicom_tree_rtss.dataset = new_dataset
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

        if self.moving_dict_container.has_modality("raw_dvh"):
            # Rename structures in DVH list
            if "rename" in change_description:
                new_raw_dvh = self.moving_dict_container.get("raw_dvh")
                for key, dvh in new_raw_dvh.items():
                    if dvh.name == change_description["rename"][0]:
                        dvh.name = change_description["rename"][1]
                        break

                self.moving_dict_container.set("raw_dvh", new_raw_dvh)

            # Remove structures from DVH list - the only visible effect of
            # this section is the exported DVH csv
            if "delete" in change_description:
                list_of_deleted = []
                new_raw_dvh = self.moving_dict_container.get("raw_dvh")
                for key, dvh in new_raw_dvh.items():
                    if dvh.name in change_description["delete"]:
                        list_of_deleted.append(key)
                for key in list_of_deleted:
                    new_raw_dvh.pop(key)
                self.moving_dict_container.set("raw_dvh", new_raw_dvh)

        if "transfer" in change_description \
                and change_description["transfer"] is None:
            self.save_new_rtss_to_moving_image_set()

    def fixed_container_structure_modified(self, changes):
        """
        Executes when a structure of fixed patient container is modified
        Displays indicator that structure has changed.
        Changes is a tuple of (new_dataset,
        description_of_changes)
        description_of_changes follows the format
        {"type_of_change": value_of_change}.
        Examples:
        {"rename": ["TOOTH", "TEETH"]} represents that the TOOTH structure has
            been renamed to TEETH.
        {"delete": ["TEETH", "MAXILLA"]} represents that the TEETH and MAXILLA
            structures have been deleted.
        {"draw": "AORTA"} represents that a new structure AORTA has been drawn.
        Note: Use {"draw": None} after multiple ROIs are generated
        (E.g., from ISO2ROI functionality), and use {"transfer":None} for
         ROI Transfer instead of calling this function
        multiple times. This will trigger auto save.
        """

        new_dataset = changes[0]
        change_description = changes[1]

        # Only show the modified indicator if description_of_changes is
        # not {"draw": None}, as this description means that the RTSS
        # is autosaved, and therefore there is no need to tell the user
        # that the RTSS has been modified
        if not ("draw" in change_description
                and change_description["draw"] is None) and \
                not ("transfer" in change_description):
            self.show_modified_indicator()

        # If this is the first change made to the RTSS file, update the
        # dataset with the new one so that OnkoDICOM starts working off this
        # dataset rather than the original RTSS file.
        self.patient_dict_container.set("rtss_modified", True)
        self.patient_dict_container.set("dataset_rtss", new_dataset)

        # Refresh ROIs in main page
        self.patient_dict_container.set(
            "rois", ImageLoading.get_roi_info(new_dataset))
        self.rois = self.patient_dict_container.get("rois")
        contour_data = ImageLoading.get_raw_contour_data(new_dataset)
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

        if "draw" in change_description or "transfer" in change_description:
            dicom_tree_rtss = DicomTree(None)
            dicom_tree_rtss.dataset = new_dataset
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

        if self.patient_dict_container.has_attribute("raw_dvh"):
            # Rename structures in DVH list
            if "rename" in change_description:
                new_raw_dvh = self.patient_dict_container.get("raw_dvh")
                for key, dvh in new_raw_dvh.items():
                    if dvh.name == change_description["rename"][0]:
                        dvh.name = change_description["rename"][1]
                        break

                self.patient_dict_container.set("raw_dvh", new_raw_dvh)
                dvh2rtdose(new_raw_dvh)

            # Remove structures from DVH list - the only visible effect of
            # this section is the exported DVH csv
            if "delete" in change_description:
                list_of_deleted = []
                new_raw_dvh = self.patient_dict_container.get("raw_dvh")
                for key, dvh in new_raw_dvh.items():
                    if dvh.name in change_description["delete"]:
                        list_of_deleted.append(key)
                for key in list_of_deleted:
                    new_raw_dvh.pop(key)
                self.patient_dict_container.set("raw_dvh", new_raw_dvh)
                dvh2rtdose(new_raw_dvh)

        # Refresh ROIs in DVH tab and DICOM View
        self.request_update_structures.emit()

        # Refresh structure tab
        self.update_content()

        if "draw" in change_description and change_description["draw"] is None:
            self.save_new_rtss_to_fixed_image_set(auto=True)
        elif "transfer" in change_description \
                and change_description["transfer"] is None:
            self.save_new_rtss_to_fixed_image_set(auto=True)

    def show_modified_indicator(self):
        self.modified_indicator_widget.setVisible(True)

    def structure_checked(self, state, roi_id):
        """
        Function triggered when the checkbox of a structure is
        checked / unchecked.
        Update the list of selected structures.
        Update the plot of the DVH and the DICOM view.

        :param state: True if the checkbox is checked, False otherwise.
        :param roi_id: ROI number
        """

        selected_rois = self.patient_dict_container.get("selected_rois")
        if state:
            selected_rois.append(roi_id)
        else:
            selected_rois.remove(roi_id)

        self.patient_dict_container.set("selected_rois", selected_rois)
        self.update_dict_polygons(state, roi_id)

        self.request_update_structures.emit()

    def update_dict_polygons(self, state, roi_id):
        """
        Update the polygon dictionaries (axial, coronal, sagittal) used to
        display the ROIs.
        :param state: True if the ROI is selected, False otherwise
        :param roi_id: ROI number
        """
        rois = self.patient_dict_container.get("rois")
        new_dict_polygons_axial = self.patient_dict_container.get(
            "dict_polygons_axial")
        new_dict_polygons_coronal = self.patient_dict_container.get(
            "dict_polygons_coronal")
        new_dict_polygons_sagittal = self.patient_dict_container.get(
            "dict_polygons_sagittal")
        aspect = self.patient_dict_container.get("pixmap_aspect")
        roi_name = rois[roi_id]['name']

        if state:
            new_dict_polygons_axial[roi_name] = {}
            new_dict_polygons_coronal[roi_name] = {}
            new_dict_polygons_sagittal[roi_name] = {}
            dict_rois_contours_axial = get_roi_contour_pixel(
                self.patient_dict_container.get("raw_contour"),
                [roi_name], self.patient_dict_container.get("pixluts"))
            dict_rois_contours_coronal, dict_rois_contours_sagittal = \
                transform_rois_contours(
                    dict_rois_contours_axial)

            for slice_id in self.patient_dict_container.get(
                    "dict_uid").values():
                polygons = calc_roi_polygon(roi_name, slice_id,
                                            dict_rois_contours_axial)
                new_dict_polygons_axial[roi_name][slice_id] = polygons

            for slice_id in range(0, len(self.patient_dict_container.get(
                    "pixmaps_coronal"))):
                polygons_coronal = calc_roi_polygon(
                    roi_name, slice_id,
                    dict_rois_contours_coronal,
                    aspect["coronal"])
                polygons_sagittal = calc_roi_polygon(
                    roi_name, slice_id,
                    dict_rois_contours_sagittal,
                    1 / aspect["sagittal"])
                new_dict_polygons_coronal[roi_name][
                    slice_id] = polygons_coronal
                new_dict_polygons_sagittal[roi_name][
                    slice_id] = polygons_sagittal

            self.patient_dict_container.set("dict_polygons_axial",
                                            new_dict_polygons_axial)
            self.patient_dict_container.set("dict_polygons_coronal",
                                            new_dict_polygons_coronal)
            self.patient_dict_container.set("dict_polygons_sagittal",
                                            new_dict_polygons_sagittal)
        else:
            new_dict_polygons_axial.pop(roi_name, None)
            new_dict_polygons_coronal.pop(roi_name, None)
            new_dict_polygons_sagittal.pop(roi_name, None)

    def on_rtss_selected(self, selected_rtss):
        """
        Function to run after a rtss is selected from SelectRTSSPopUp
        """
        self.patient_dict_container.get("existing_rtss_files").clear()
        self.patient_dict_container.get("existing_rtss_files").append(
            selected_rtss)
        self.save_new_rtss(auto=True)

    def display_select_rtss_window(self):
        """
        Display a pop up window that contains all RTSSs attached to the
        selected image set.
        """
        self.select_rtss_window = SelectRTSSPopUp(
            self.patient_dict_container.get("existing_rtss_files"),
            parent=self)
        self.select_rtss_window.signal_rtss_selected.connect(
            self.on_rtss_selected)
        self.select_rtss_window.show()

    def save_new_rtss_to_fixed_image_set(self, event=None, auto=False):
        """
        Save the current RTSS stored in fixed patient dictionary to the file
        system. :param event: Not used but will be passed as an argument
        from modified_indicator_widget on mouseReleaseEvent :param auto:
        Used for auto save without user confirmation
        """
        existing_rtss_files = self.patient_dict_container.get(
            "existing_rtss_files")
        if len(existing_rtss_files) == 1:
            if isinstance(existing_rtss_files[0], Series):
                existing_rtss_directory = str(Path(
                    existing_rtss_files[0].get_files()[0]))
            else:
                # This "else" is used by iso2roi gui and structure tab tests to
                # quickly set existing_rtss_directory
                existing_rtss_directory = existing_rtss_files[0]
        elif len(existing_rtss_files) > 1:
            self.display_select_rtss_window()
            # This function will be called again when a RTSS is selected
            return
        else:
            existing_rtss_directory = None

        rtss_directory = str(
            Path(self.patient_dict_container.get("file_rtss")))

        if auto:
            confirm_save = QtWidgets.QMessageBox.Yes
        else:
            confirm_save = \
                QtWidgets.QMessageBox.information(self, "Confirmation",
                                                  "Are you sure you want to "
                                                  "save the modified RTSTRUCT "
                                                  "file? This will overwrite "
                                                  "the existing file. This is "
                                                  "not reversible.",
                                                  QtWidgets.QMessageBox.Yes,
                                                  QtWidgets.QMessageBox.No)

        if confirm_save == QtWidgets.QMessageBox.Yes:
            if existing_rtss_directory is None:
                self.patient_dict_container.get("dataset_rtss").save_as(
                    rtss_directory)
            else:
                new_rtss = self.patient_dict_container.get("dataset_rtss")
                old_rtss = pydicom.dcmread(existing_rtss_directory,
                                           force=True)
                old_roi_names = \
                    set(value["name"] for value in
                        ImageLoading.get_roi_info(old_rtss).values())
                new_roi_names = \
                    set(value["name"] for value in
                        self.patient_dict_container.get("rois").values())
                duplicated_names = old_roi_names.intersection(new_roi_names)

                # stop if there are conflicting roi names and user do not
                # wish to proceed.
                if duplicated_names and not self.display_confirm_merge(
                        duplicated_names):
                    return

                merged_rtss = merge_rtss(old_rtss, new_rtss, duplicated_names)
                merged_rtss.save_as(existing_rtss_directory)

            if not auto:
                QtWidgets.QMessageBox.about(self.parentWidget(),
                                            "File saved",
                                            "The RTSTRUCT file has been saved."
                                            )
            self.patient_dict_container.set("rtss_modified", False)
            # Hide the modified indicator
            self.modified_indicator_widget.setVisible(False)

    def save_new_rtss_to_moving_image_set(self, event=None):
        """
        Save the current RTSS stored in moving patient dictionary to the
        file system. ROIs modification into moving patient dict is auto
        saved :param event: Not used but will be passed as an argument from
        modified_indicator_widget on mouseReleaseEvent
        """
        if self.moving_dict_container.get("existing_file_rtss") is not None:
            existing_rtss_directory = str(Path(self.moving_dict_container.get(
                "existing_file_rtss")))
        else:
            existing_rtss_directory = None
        rtss_directory = str(
            Path(self.moving_dict_container.get("file_rtss")))

        if existing_rtss_directory is None:
            self.moving_dict_container.get("dataset_rtss").save_as(
                rtss_directory)
        else:
            new_rtss = self.moving_dict_container.get("dataset_rtss")
            old_rtss = pydicom.dcmread(existing_rtss_directory, force=True)
            old_roi_names = \
                set(value["name"] for value in
                    ImageLoading.get_roi_info(old_rtss).values())
            new_roi_names = \
                set(value["name"] for value in
                    self.moving_dict_container.get("rois").values())
            duplicated_names = old_roi_names.intersection(new_roi_names)
            merged_rtss = merge_rtss(old_rtss, new_rtss, duplicated_names)
            merged_rtss.save_as(existing_rtss_directory)
        self.moving_dict_container.set("rtss_modified", False)

    def display_confirm_merge(self, duplicated_names):
        confirm_merge = QtWidgets.QMessageBox(parent=self)
        confirm_merge.setIcon(QtWidgets.QMessageBox.Question)
        confirm_merge.setWindowTitle("Merge RTSTRUCTs?")
        confirm_merge.setText("Conflicting ROI names found between new ROIs "
                              "and existing ROIs:\n" + str(duplicated_names) +
                              "\nAre you sure you want to merge the RTSTRUCT "
                              "files? The new ROIs will replace the existing "
                              "ROIs. ")
        button_yes = QtWidgets.QPushButton("Yes, I want to merge")
        button_no = QtWidgets.QPushButton("No, I will change the names")
        """ 
        We want the buttons 'No' & 'Yes' to be displayed in that exact 
        order. QMessageBox displays buttons in respect to their assigned 
        roles. (0 first, then 0 and so on) 'AcceptRole' is 0 and 
        'RejectRole' is 1 thus by counterintuitively assigning 'No' to 
        'AcceptRole' and 'Yes' to 'RejectRole' the buttons are 
        positioned as desired.
        """
        confirm_merge.addButton(button_no, QtWidgets.QMessageBox.AcceptRole)
        confirm_merge.addButton(button_yes, QtWidgets.QMessageBox.RejectRole)
        confirm_merge.exec_()

        if confirm_merge.clickedButton() == button_yes:
            return True
        return False
