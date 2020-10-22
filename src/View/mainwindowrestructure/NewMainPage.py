import pydicom
from PyQt5 import QtCore, QtGui, QtWidgets

from src.Model.CalculateImages import convert_raw_data, get_pixmaps
from src.Model.GetPatientInfo import get_basic_info, DicomTree, dict_instanceUID
from src.Model.Isodose import get_dose_pixluts
from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.ROI import ordered_list_rois
from src.View.mainwindowrestructure.NewDVHTab import NewDVHTab
from src.View.mainwindowrestructure.NewDicomTree import NewDicomTree
from src.View.mainwindowrestructure.NewDicomView import NewDicomView
from src.View.mainwindowrestructure.NewIsodoseTab import NewIsodoseTab
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
        if patient_dict_container.has_modality("rtss"):
            patient_dict_container.set("file_rtss", filepaths['rtss'])
            patient_dict_container.set("dataset_rtss", dataset['rtss'])

            dicom_tree_rtss = DicomTree(filepaths['rtss'])
            patient_dict_container.set("dict_dicom_tree_rtss", dicom_tree_rtss.dict)

            patient_dict_container.set("list_roi_numbers", ordered_list_rois(patient_dict_container.get("rois")))
            patient_dict_container.set("selected_rois", [])

            patient_dict_container.set("dict_uid", dict_instanceUID(dataset))
            patient_dict_container.set("dict_polygons", {})

        # Set RTDOSE attributes
        if patient_dict_container.has_modality("rtdose"):
            dicom_tree_rtdose = DicomTree(filepaths['rtdose'])
            patient_dict_container.set("dict_dicom_tree_rtdose", dicom_tree_rtdose.dict)

            patient_dict_container.set("dose_pixluts", get_dose_pixluts(dataset))

            patient_dict_container.set("selected_doses", [])
            patient_dict_container.set("rxdose", 1) # This will be overwritten if an RTPLAN is present. TODO calculate value w/o RTPLAN

        # Set RTPLAN attributes
        if patient_dict_container.has_modality("rtplan"):
            # the TargetPrescriptionDose is type 3 (optional), so it may not be there
            # However, it is preferable to the sum of the beam doses
            # DoseReferenceStructureType is type 1 (value is mandatory),
            # but it can have a value of ORGAN_AT_RISK rather than TARGET
            # in which case there will *not* be a TargetPrescriptionDose
            # and even if it is TARGET, that's no guarantee that TargetPrescriptionDose
            # will be encoded and have a value
            rxdose = 1
            if ('DoseReferenceSequence' in dataset['rtplan'] and
                    dataset['rtplan'].DoseReferenceSequence[0].DoseReferenceStructureType and
                    dataset['rtplan'].DoseReferenceSequence[0].TargetPrescriptionDose):
                rxdose = dataset['rtplan'].DoseReferenceSequence[0].TargetPrescriptionDose * 100
            # beam doses are to a point, not necessarily to the same point
            # and don't necessarily add up to the prescribed dose to the target
            # which is frequently to a SITE rather than to a POINT
            elif dataset['rtplan'].FractionGroupSequence:
                fraction_group = dataset['rtplan'].FractionGroupSequence[0]
                if ("NumberOfFractionsPlanned" in fraction_group) and \
                        ("ReferencedBeamSequence" in fraction_group):
                    beams = fraction_group.ReferencedBeamSequence
                    number_of_fractions = fraction_group.NumberOfFractionsPlanned
                    for beam in beams:
                        if "BeamDose" in beam:
                            rxdose += beam.BeamDose * number_of_fractions * 100
            patient_dict_container.set("rxdose", rxdose)

            dicom_tree_rtplan = DicomTree(filepaths['rtplan'])
            patient_dict_container.set("dict_dicom_tree_rtplan", dicom_tree_rtplan.dict)


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
        self.left_panel = QtWidgets.QTabWidget()
        self.left_panel.setMinimumWidth(230)
        self.left_panel.setMaximumWidth(500)
        self.left_panel_layout = QtWidgets.QHBoxLayout(self.left_panel)

        # Add structures tab to left panel
        if patient_dict_container.has_modality("rtss"):
            self.structures_tab = NewStructureTab()
            self.structures_tab.request_update_structures.connect(self.update_views)
            self.left_panel.addTab(self.structures_tab, "Structures")

        if patient_dict_container.has_modality("rtdose"):
            self.isodoses_tab = NewIsodoseTab()
            self.isodoses_tab.request_update_isodoses.connect(self.update_views)
            self.left_panel.addTab(self.isodoses_tab, "Isodoses")

        self.left_panel_layout.addWidget(self.left_panel)

        # Hide left panel if no rtss or rtdose
        if not patient_dict_container.has_modality("rtss") and not patient_dict_container.has_modality("rtdose"):
            self.left_panel.hide()

        # Right panel contains the different tabs of DICOM view, DVH, clinical data, DICOM tree
        self.right_panel = QtWidgets.QTabWidget()

        # Add DICOM view to right panel as a tab
        roi_color_dict = self.structures_tab.color_dict if hasattr(self, 'structures_tab') else None
        iso_color_dict = self.isodoses_tab.color_dict if hasattr(self, 'isodoses_tab') else None
        self.dicom_view = NewDicomView(roi_color=roi_color_dict, iso_color=iso_color_dict)
        self.right_panel.addTab(self.dicom_view, "DICOM View")

        # Add DVH tab to right panel as a tab
        if patient_dict_container.has_modality("rtss") and patient_dict_container.has_modality("rtdose"):
            self.dvh_tab = NewDVHTab()
            self.right_panel.addTab(self.dvh_tab, "DVH")

        self.dicom_tree = NewDicomTree()
        self.right_panel.addTab(self.dicom_tree, "DICOM Tree")

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
        if hasattr(self, 'dvh_tab'):
            self.dvh_tab.update_plot()
