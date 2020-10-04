import pydicom
from PyQt5 import QtCore, QtGui, QtWidgets

from src.Model.CalculateImages import convert_raw_data, get_pixmaps
from src.Model.GetPatientInfo import get_basic_info, DicomTree, dict_instanceUID
from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.ROI import ordered_list_rois
from src.View.mainwindowrestructure.NewDicomView import NewDicomView
from src.View.mainwindowrestructure.NewPatientBar import NewPatientBar
from src.View.mainwindowrestructure.NewStructureTab import NewStructureTab


class UINewMainWindow:
    pyradi_trigger = QtCore.pyqtSignal(str, dict, str)

    def setup_ui(self, main_window_instance):

        ##############################
        #  LOAD PATIENT INFORMATION  #
        ##############################
        patient_dict_container = PatientDictContainer()
        dataset = patient_dict_container.dataset
        filepaths = patient_dict_container.filepaths
        patient_dict_container.set("rtss_modified", False)

        if isinstance(dataset[0].WindowWidth, pydicom.valuerep.DSfloat):
            window = int(dataset[0].WindowWidth)
        elif isinstance(dataset[0].WindowWidth, pydicom.multival.MultiValue):
            window = int(dataset[0].WindowWidth[1])

        if isinstance(dataset[0].WindowCenter, pydicom.valuerep.DSfloat):
            level = int(dataset[0].WindowCenter)
        elif isinstance(dataset[0].WindowCenter, pydicom.multival.MultiValue):
            level = int(dataset[0].WindowCenter[1])

        patient_dict_container.set("window", window)
        patient_dict_container.set("level", level)

        pixel_values = convert_raw_data(dataset)
        pixmaps = get_pixmaps(pixel_values, window, level)
        patient_dict_container.set("pixmaps", pixmaps)

        basic_info = get_basic_info(dataset[0])
        patient_dict_container.set("basic_info", basic_info)

        # Set RTSS attributes
        if patient_dict_container.has("rtss"):
            patient_dict_container.set("file_rtss", filepaths['rtss'])
            patient_dict_container.set("dataset_rtss", dataset['rtss'])

            dicom_tree_rtss = DicomTree(filepaths['rtss'])
            patient_dict_container.set("dict_dicom_tree_rtss", dicom_tree_rtss.dict)

            patient_dict_container.set("list_roi_numbers", ordered_list_rois(patient_dict_container.get("rois")))
            patient_dict_container.set("selected_rois", [])

            patient_dict_container.set("dict_uid", dict_instanceUID(dataset))
            patient_dict_container.set("dict_polygons", {})


        ##########################################
        #  IMPLEMENTATION OF THE MAIN PAGE VIEW  #
        ##########################################
        main_window_instance.setMinimumSize(1080, 700)
        main_window_instance.setWindowTitle("OnkoDICOM")
        main_window_instance.setWindowIcon(QtGui.QIcon("src/Icon/DONE.png"))

        # Import stylesheet
        sheet_file = "src/res/stylesheet.qss"
        with open(sheet_file) as fh:
            main_window_instance.setStyleSheet(fh.read())

        self.central_widget = QtWidgets.QWidget()
        self.central_widget_layout = QtWidgets.QVBoxLayout()

        self.button_open_patient = QtWidgets.QPushButton("Open new patient")
        self.patient_bar = NewPatientBar()

        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)

        # Left panel contains stuctures tab, isodoses tab, and structure information
        self.left_panel = QtWidgets.QWidget()
        self.left_panel.setMinimumWidth(230)
        self.left_panel.setMaximumWidth(500)
        self.left_panel_layout = QtWidgets.QHBoxLayout(self.left_panel)

        self.left_panel_tab = QtWidgets.QTabWidget()

        # Add structures tab to left panel
        if patient_dict_container.has("rtss"):
            self.structures_tab = NewStructureTab()
            self.structures_tab.request_update_structures.connect(self.update_views)
            self.left_panel_tab.addTab(self.structures_tab, "Structures")

        self.left_panel_layout.addWidget(self.left_panel_tab)

        # Right panel contains the different tabs of DICOM view, DVH, clinical data, DICOM tree
        self.right_panel = QtWidgets.QTabWidget()

        # Add DICOM view to right panel as a tab
        roi_color_dict = self.structures_tab.color_dict if hasattr(self, 'structures_tab') else None
        self.dicom_view = NewDicomView(roi_color=roi_color_dict)
        self.right_panel.addTab(self.dicom_view, "DICOM View")

        splitter.addWidget(self.left_panel)
        splitter.addWidget(self.right_panel)

        # Create footer
        self.footer = QtWidgets.QWidget()
        self.create_footer()

        # Set layout
        self.central_widget_layout.addWidget(self.button_open_patient)
        self.central_widget_layout.addWidget(self.patient_bar)
        self.central_widget_layout.addWidget(splitter)
        self.central_widget_layout.addWidget(self.footer)

        self.central_widget.setLayout(self.central_widget_layout)
        main_window_instance.setCentralWidget(self.central_widget)

    def create_footer(self):
        self.footer.setFixedHeight(15)
        layout_footer = QtWidgets.QHBoxLayout(self.footer)
        layout_footer.setContentsMargins(0, 0, 0, 0)

        label_footer = QtWidgets.QLabel("@OnkoDICOM 2019-20")
        label_footer.setAlignment(QtCore.Qt.AlignRight)

        layout_footer.addWidget(label_footer)

    def update_views(self):
        self.dicom_view.update_view()
        # TODO this will also need to update the DVH tab's plot
