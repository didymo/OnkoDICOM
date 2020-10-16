import csv
from pathlib import Path
from random import randint, seed

from PyQt5 import QtWidgets, QtGui, QtCore
from pandas import np

from src.Model import ImageLoading
from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.ROI import ordered_list_rois
from src.View.mainpage.StructureWidget import StructureWidget


class NewStructureTab(QtWidgets.QWidget):

    request_update_structures = QtCore.pyqtSignal()

    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.patient_dict_container = PatientDictContainer()
        self.rois = self.patient_dict_container.get("rois")
        self.color_dict = self.init_color_roi()
        self.patient_dict_container.set("roi_color_dict", self.color_dict)

        self.structure_tab_layout = QtWidgets.QVBoxLayout()

        # Create scrolling area widget to contain the content.
        self.scroll_area = QtWidgets.QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.scroll_area_content = QtWidgets.QWidget(self.scroll_area)
        self.scroll_area.ensureWidgetVisible(self.scroll_area_content)

        # Create layout for checkboxes and colour squares
        self.layout_content = QtWidgets.QVBoxLayout(self.scroll_area_content)
        self.layout_content.setContentsMargins(0, 0, 0, 0)
        self.layout_content.setSpacing(0)
        self.layout_content.setAlignment(QtCore.Qt.AlignTop)

        # Create list of standard organ and volume names
        self.standard_organ_names = []
        self.standard_volume_names = []
        self.init_standard_names()

        # Create StructureWidget objects
        self.update_content()

        # Create ROI manipulation buttons
        self.button_roi_draw = QtWidgets.QPushButton()
        self.button_roi_delete = QtWidgets.QPushButton()
        self.roi_buttons = QtWidgets.QWidget()
        self.init_roi_buttons()

        # Set layout
        self.structure_tab_layout.addWidget(self.scroll_area)
        self.structure_tab_layout.addWidget(self.roi_buttons)
        self.setLayout(self.structure_tab_layout)

    def init_color_roi(self):
        """
        Create a dictionary containing the colors for each structure.
        :return: Dictionary where the key is the ROI number and the value a QColor object.
        """
        roi_color = dict()

        roi_contour_info = self.patient_dict_container.get("dict_dicom_tree_rtss")['ROI Contour Sequence']

        if len(roi_contour_info) > 0:
            for item, roi_dict in roi_contour_info.items():
                # Note: the keys of roiContourInfo are "item 0", "item 1", etc.
                # As all the ROI structures are identified by the ROI numbers in the whole code,
                # we get the ROI number 'roi_id' by using the member 'list_roi_numbers'
                id = item.split()[1]
                roi_id = self.patient_dict_container.get("list_roi_numbers")[int(id)]

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

    def init_roi_buttons(self):
        icon_roi_delete = QtGui.QIcon()
        icon_roi_delete.addPixmap(
            QtGui.QPixmap(':/images/Icon/ROIdelete.png'),
            QtGui.QIcon.Normal,
            QtGui.QIcon.On
        )

        icon_roi_draw = QtGui.QIcon()
        icon_roi_draw.addPixmap(
            QtGui.QPixmap(':/images/Icon/ROI_Brush.png'),
            QtGui.QIcon.Normal,
            QtGui.QIcon.On
        )

        #self.button_roi_delete.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        self.button_roi_delete.setMinimumHeight(50)
        self.button_roi_delete.setIcon(icon_roi_delete)
        self.button_roi_delete.setText("Delete ROI")
        self.button_roi_delete.clicked.connect(self.roi_delete_clicked)

        #self.button_roi_draw.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        self.button_roi_draw.setMinimumHeight(50)
        self.button_roi_draw.setIcon(icon_roi_draw)
        self.button_roi_draw.setText("Draw ROI")
        self.button_roi_draw.clicked.connect(self.roi_draw_clicked)

        layout_roi_buttons = QtWidgets.QHBoxLayout(self.roi_buttons)
        layout_roi_buttons.setContentsMargins(0, 0, 0, 0)
        layout_roi_buttons.addWidget(self.button_roi_draw)
        layout_roi_buttons.addWidget(self.button_roi_delete)

    def update_content(self):
        """
        Add the contents (color square and checkbox) in the scrolling area widget.
        """
        # Clear the children
        for i in reversed(range(self.layout_content.count())):
            self.layout_content.itemAt(i).widget().setParent(None)

        row = 0
        for roi_id, roi_dict in self.rois.items():
            # Creates a widget representing each ROI
            structure = StructureWidget(roi_id, self.color_dict[roi_id], roi_dict['name'], self)
            structure.structure_renamed.connect(self.structure_modified)
            self.layout_content.addWidget(structure)
            row += 1

        self.scroll_area.setStyleSheet("QScrollArea {background-color: #ffffff; border-style: none;}")
        self.scroll_area_content.setStyleSheet("QWidget {background-color: #ffffff; border-style: none;}")

        self.scroll_area.setWidget(self.scroll_area_content)

    def roi_delete_clicked(self):
        pass

    def roi_draw_clicked(self):
        pass

    def structure_modified(self, changes):
        """
        Executes when a structure is renamed/deleted. Displays indicator that structure has changed.
        changes is a tuple of (new_dataset, description_of_changes)
        description_of_changes follows the format {"type_of_change": value_of_change}.
        Examples: {"rename": ["TOOTH", "TEETH"]} represents that the TOOTH structure has been renamed to TEETH.
        {"delete": ["TEETH", "MAXILLA"]} represents that the TEETH and MAXILLA structures have been deleted.
        """

        new_dataset = changes[0]
        change_description = changes[1]

        # If this is the first time the RTSS has been modified, create a modified indicator giving the user the option
        # to save their new file.
        if not self.patient_dict_container.get("rtss_modified"):
            self.show_modified_indicator()

        # If this is the first change made to the RTSS file, update the dataset with the new one so that OnkoDICOM
        # starts working off this dataset rather than the original RTSS file.
        self.patient_dict_container.set("rtss_modified", True)
        self.patient_dict_container.set("dataset_rtss", new_dataset)

        # Refresh ROIs in main page
        self.patient_dict_container.set("rois", ImageLoading.get_roi_info(new_dataset))
        self.rois = self.patient_dict_container.get("rois")
        contour_data = ImageLoading.get_raw_contour_data(new_dataset)
        self.patient_dict_container.set("raw_contour", contour_data[0])
        self.patient_dict_container.set("num_points", contour_data[1])
        self.patient_dict_container.set("list_roi_numbers", ordered_list_rois(self.patient_dict_container.get("rois")))
        self.patient_dict_container.set("selected_rois", [])

        if self.patient_dict_container.has_modality("raw_dvh"):
            # Rename structures in DVH list
            if "rename" in changes[1]:
                new_raw_dvh = self.patient_dict_container.get("raw_dvh")
                for key, dvh in new_raw_dvh.items():
                    if dvh.name == change_description["rename"][0]:
                        dvh.name = change_description["rename"][1]
                        break

                self.patient_dict_container.set("raw_dvh", new_raw_dvh)

            # Remove structures from DVH list - the only visible effect of this section is the exported DVH csv
            if "delete" in changes[1]:
                list_of_deleted = []
                new_raw_dvh = self.patient_dict_container.get("raw_dvh")
                for key, dvh in new_raw_dvh.items():
                    if dvh.name in change_description["delete"]:
                        list_of_deleted.append(key)
                for key in list_of_deleted:
                    new_raw_dvh.pop(key)
                self.patient_dict_container.set("raw_dvh", new_raw_dvh)

        # Refresh ROIs in DVH tab and DICOM View
        self.request_update_structures.emit()

        # Refresh structure tab
        self.update_content()

    def show_modified_indicator(self):
        modified_indicator_widget = QtWidgets.QWidget()
        modified_indicator_widget.setContentsMargins(8, 5, 8, 5)
        modified_indicator_layout = QtWidgets.QHBoxLayout()
        modified_indicator_layout.setAlignment(QtCore.Qt.AlignLeft)

        modified_indicator_icon = QtWidgets.QLabel()
        modified_indicator_icon.setPixmap(QtGui.QPixmap("src/Icon/alert.png"))
        modified_indicator_layout.addWidget(modified_indicator_icon)

        modified_indicator_text = QtWidgets.QLabel("Structures have been modified")
        modified_indicator_text.setStyleSheet("color: red")
        modified_indicator_layout.addWidget(modified_indicator_text)

        modified_indicator_widget.setLayout(modified_indicator_layout)
        modified_indicator_widget.mouseReleaseEvent = self.save_new_rtss  # When the widget is clicked, save the rtss
        self.structure_tab_layout.addWidget(modified_indicator_widget)

    def structure_checked(self, state, roi_id):
        """
        Function triggered when the checkbox of a structure is checked / unchecked.
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

        self.request_update_structures.emit()

    def save_new_rtss(self, event=None):
        rtss_directory = str(Path(self.patient_dict_container.get("file_rtss")).parent)
        save_filepath = save_filepath = QtWidgets.QFileDialog.getSaveFileName(self.parentWidget(), "Save file",
                                                                              rtss_directory)[0]
        if save_filepath != "":
            self.patient_dict_container.get("dataset_rtss").save_as(save_filepath)
            QtWidgets.QMessageBox.about(self.parentWidget(), "File saved", "The RTSTRUCT file has been saved.")
            self.patient_dict_container.set("rtss_modified", False)
