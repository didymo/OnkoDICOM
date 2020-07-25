import glob

from PyQt5.QtCore import Qt

from src.Controller.Add_On_OController import AddOptions
from src.Controller.mainPageController import MainPage
from src.View.InputDialogs import Rxdose_Check
from src.View.Main_Page.PatientBar import *
from src.View.Main_Page.StructureTab import *
from src.View.Main_Page.IsodoseTab import *
from src.View.Main_Page.StructureInformation import *
from src.View.Main_Page.DicomView import *
from src.View.Main_Page.DVH import *
from src.View.Main_Page.DicomTree import *
from src.View.Main_Page.MenuBar import *
from src.View.Main_Page.resources_rc import *


class Ui_MainWindow(object):

    # To initiate progress bar for pyradiomics through anonymization
    pyradi_trigger = QtCore.pyqtSignal(str, dict, str)

    def setupUi(self, MainWindow, patient_dict_container):

        ##############################
        #  LOAD PATIENT INFORMATION  #
        ##############################
        self.dataset = patient_dict_container.dataset
        self.raw_dvh = patient_dict_container.get("raw_dvh")
        self.dvh_x_y = patient_dict_container.get("dvh_x_y")
        
        # Dictionary whose key is the ROI number as specified in the RTSS file
        # and whose value is a dictionary with keys 'uid', 'name' and 'algorithm'
        self.rois = patient_dict_container.get("rois")
        # Contain the ordered list of ROI numbers.
        # Used to manage the case of missing integers in an ordered series of ROI numbers (for example 1 2 4 7)
        self.list_roi_numbers = self.ordered_list_rois()
        
        self.filepaths = patient_dict_container.filepaths
        self.path = patient_dict_container.path
        self.dose_pixluts = get_dose_pixluts(self.dataset)
        self.hashed_path = ''     # Path to hashed patient directory

        self.rxdose = 1
        if self.dataset['rtplan']:
            # the TargetPrescriptionDose is type 3 (optional), so it may not be there
            # However, it is preferable to the sum of the beam doses
            # DoseReferenceStructureType is type 1 (value is mandatory), 
            # but it can have a value of ORGAN_AT_RISK rather than TARGET
            # in which case there will *not* be a TargetPrescriptionDose
            # and even if it is TARGET, that's no guarantee that TargetPrescriptionDose 
            # will be encoded and have a value
            if ('DoseReferenceSequence' in self.dataset['rtplan'] and
                self.dataset['rtplan'].DoseReferenceSequence[0].DoseReferenceStructureType and
                self.dataset['rtplan'].DoseReferenceSequence[0].TargetPrescriptionDose ):
                self.rxdose = self.dataset['rtplan'].DoseReferenceSequence[0].TargetPrescriptionDose * 100
            # beam doses are to a point, not necessarily to the same point
            # and don't necessarily add up to the prescribed dose to the target
            # which is frequently to a SITE rather than to a POINT
            elif self.dataset['rtplan'].FractionGroupSequence:
                fraction_group = self.dataset['rtplan'].FractionGroupSequence[0]
                if ("NumberOfFractionsPlanned" in fraction_group) and \
                        ("ReferencedBeamSequence" in fraction_group):
                    beams = fraction_group.ReferencedBeamSequence
                    number_of_fractions = fraction_group.NumberOfFractionsPlanned
                    for beam in beams:
                        if "BeamDose" in beam:
                            self.rxdose += beam.BeamDose * number_of_fractions * 100
        self.rxdose = round(self.rxdose)

        # Commented out as rx dose dialogue no longer needed.
        #dose_check_dialog = Rxdose_Check(self.rxdose)
        #dose_check_dialog.exec()
        #self.rxdose = dose_check_dialog.get_dose()

        # WindowWidth and WindowCenter values in the DICOM file can be either
        # a list or a float. The following lines of code check what instance
        # the values belong to and sets the window and level values accordingly
        # The values are converted from the type pydicom.valuerep.DSfloat to
        # int for processing later on in the program
        if isinstance(self.dataset[0].WindowWidth, pydicom.valuerep.DSfloat):
            self.window = int(self.dataset[0].WindowWidth)
        elif isinstance(self.dataset[0].WindowWidth, pydicom.multival.MultiValue):
            self.window = int(self.dataset[0].WindowWidth[1])

        if isinstance(self.dataset[0].WindowCenter, pydicom.valuerep.DSfloat):
            self.level = int(self.dataset[0].WindowCenter)
        elif isinstance(self.dataset[0].WindowCenter, pydicom.multival.MultiValue):
            self.level = int(self.dataset[0].WindowCenter[1])

        # Variables to check for the mouse position when altering the window and
        # level values
        self.x1, self.y1 = 256, 256

        # Check to see if the imageWindowing.csv file exists
        if os.path.exists('src/data/csv/imageWindowing.csv'):
            # If it exists, read data from file into the self.dict_windowing variable
            self.dict_windowing = {}
            with open('src/data/csv/imageWindowing.csv', "r") as fileInput:
                next(fileInput)
                self.dict_windowing["Normal"] = [self.window, self.level]
                for row in fileInput:
                    # Format: Organ - Scan - Window - Level
                    items = [item for item in row.split(',')]
                    self.dict_windowing[items[0]] = [
                        int(items[2]), int(items[3])]
        else:
            # If csv does not exist, initialize dictionary with default values
            self.dict_windowing = {"Normal": [self.window, self.level], "Lung": [1600, -300],
                                   "Bone": [1400, 700], "Brain": [160, 950],
                                   "Soft Tissue": [400, 800], "Head and Neck": [275, 900]}

        self.pixel_values = convert_raw_data(self.dataset)
        self.pixmaps = get_pixmaps(self.pixel_values, self.window, self.level)

        self.file_rtss = self.filepaths['rtss']
        self.file_rtdose = self.filepaths['rtdose']
        self.dataset_rtss = pydicom.dcmread(self.file_rtss, force=True)
        self.dataset_rtdose = pydicom.dcmread(self.file_rtdose, force=True)

        self.dict_UID = dict_instanceUID(self.dataset)
        self.selected_rois = []
        self.selected_doses = []

        self.basicInfo = get_basic_info(self.dataset[0])
        self.dict_pixluts = patient_dict_container.get("pixluts")
        self.dict_raw_ContourData = patient_dict_container.get("raw_contour")
        self.dict_NumPoints = patient_dict_container.get("num_points")

        self.dict_polygons = {}

        self.zoom = 1

        # DICOM Tree for RTSS file
        self.dicomTree_rtss = DicomTree(self.file_rtss)
        self.dictDicomTree_rtss = self.dicomTree_rtss.dict

        # DICOM Tree for RT Dose file
        self.dicomTree_rtdose = DicomTree(self.file_rtdose)
        self.dictDicomTree_rtdose = self.dicomTree_rtdose.dict

        # Patient Position
        filename_CT0 = self.filepaths[0]
        dicomTreeSlice_CT0 = DicomTree(filename_CT0)
        dictSlice_CT0 = dicomTreeSlice_CT0.dict
        self.patient_HFS = dictSlice_CT0['Patient Position'][0][:2] == 'HF'

        self.callClass = MainPage(self.path, self.dataset, self.filepaths, self.raw_dvh)
        self.callManager = AddOptions()


        ##########################################
        #  IMPLEMENTATION OF THE MAIN PAGE VIEW  #
        ##########################################

        # Main Window
        MainWindow.setMinimumSize(1080, 700)
        MainWindow.setWindowTitle("OnkoDICOM")
        MainWindow.setWindowIcon(QtGui.QIcon("src/Icon/DONE.png"))


        # Main Container and Layout
        self.main_widget = QtWidgets.QWidget(MainWindow)
        self.main_widget.setFocusPolicy(QtCore.Qt.NoFocus)
        self.main_layout = QtWidgets.QVBoxLayout(self.main_widget)

        # Patient Bar
        self.patient_bar = PatientBar(self)

        # Functionalities Container and Layout
        # (Structure/Isodoses tab, Structure Information tab, DICOM View / DVH / DICOM Tree / Clinical Data tab)
        self.function_widget = QtWidgets.QWidget(MainWindow)
        self.function_widget.setFocusPolicy(QtCore.Qt.NoFocus)
        self.function_layout = QtWidgets.QHBoxLayout(self.function_widget)
        self.function_layout.setContentsMargins(0, 0, 0, 0)

        splitter = QtWidgets.QSplitter(Qt.Horizontal)

        # Left Column
        self.left_widget = QtWidgets.QWidget(self.main_widget)
        self.left_layout = QtWidgets.QVBoxLayout(self.left_widget)
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        self.left_widget.setMinimumWidth(230)
        self.left_widget.setMaximumWidth(500)
        
        # Left Top Column: Structure and Isodoses Tabs
        self.tab1 = QtWidgets.QTabWidget(self.left_widget)
        self.tab1.setFocusPolicy(QtCore.Qt.NoFocus)
        self.tab1.setGeometry(QtCore.QRect(0, 40, 200, 361))

        # Left Column: Structures tab
        self.structures_tab = StructureTab(self)
        # Left Column: Isodoses tab
        self.isodoses_tab = IsodosesTab(self)

        # Structure Information (bottom left of the window)
        self.struct_info = StructureInformation(self)

        self.left_layout.addWidget(self.tab1)
        self.left_layout.addWidget(self.struct_info.widget)


        # Main view
        self.tab2 = QtWidgets.QTabWidget(self.main_widget)
        self.tab2.setGeometry(QtCore.QRect(200, 40, 880, 561))
        self.tab2.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))

        # Main view: DICOM View
        self.dicom_view = DicomView(self)

        # Main view: DVH
        self.dvh = DVH(self)

        # Main view: DICOM Tree
        self.dicom_tree = DicomTreeUI(self)

        # Main view: Clinical Data
        self.tab2_clinical_data = QtWidgets.QWidget()
        self.tab2_clinical_data.setFocusPolicy(QtCore.Qt.NoFocus)
        # check for csv data
        reg = '/CSV/ClinicalData*[.csv]'
        if not glob.glob(self.path + reg):
            self.callClass.display_cd_form(self.tab2, self.path)
        else:
            self.callClass.display_cd_dat(self.tab2, self.path)
        self.tab2.setFocusPolicy(QtCore.Qt.NoFocus)

        splitter.addWidget(self.left_widget)
        splitter.addWidget(self.tab2)
        self.function_layout.addWidget(splitter)

        self.main_layout.addWidget(self.function_widget)

        self.tab1.raise_()
        self.tab2.raise_()
        
        self.create_footer()

        MainWindow.setCentralWidget(self.main_widget)
        self.tab2.setTabText(3, "Clinical Data")
        # self.tab2.setTabText(self.tab2.indexOf(self.tab2_clinical_data), _translate("MainWindow", "Clinical Data"))

        # Menu and Tool bars
        self.menu_bar = MenuBar(self)

        self.tab1.setCurrentIndex(0)
        self.tab2.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)


    def create_footer(self):
        # Bottom Layer
        self.bottom_widget = QtWidgets.QWidget(self.main_widget)
        self.hLayout_bottom = QtWidgets.QHBoxLayout(self.bottom_widget)
        self.hLayout_bottom.setContentsMargins(0, 0, 0, 0)

        # Bottom Layer: "@OnkoDICOM_2019" label
        self.label = QtWidgets.QLabel(self.bottom_widget)
        self.label.setAlignment(QtCore.Qt.AlignRight)
        self.label.setStyleSheet("font: 9pt \"Laksaman\";")
        self.label.setFocusPolicy(QtCore.Qt.NoFocus)
        self.label.setText("@OnkoDICOM 2019")

        self.hLayout_bottom.addWidget(self.label)

        self.main_layout.addWidget(self.bottom_widget)
        self.bottom_widget.raise_()


    def ordered_list_rois(self):
        res = []
        for id, value in self.rois.items():
            res.append(id)
        return sorted(res)


    ####### CLINICAL DATA #######

    def clinicalDataCheck(self):
        reg = '/CSV/ClinicalData*[.csv]'
        if not glob.glob(self.path + reg):
            SaveReply = QtWidgets.QMessageBox.warning(self, "Message",
                                                "You need to complete the Clinical Data form for this patient!",
                                                QtWidgets.QMessageBox.Ok)
            if SaveReply == QtWidgets.QMessageBox.Ok:
                self.tab2.setCurrentIndex(3)
        else:
            SaveReply = QtWidgets.QMessageBox.information(self, "Message",
                                                          "A Clinical Data file exists for this patient! If you wish \n"
                                                          "to update it you can do so in the Clinical Data tab.",
                                                          QtWidgets.QMessageBox.Ok)
            if SaveReply == QtWidgets.QMessageBox.Ok:
                pass
