import src.View.resources_rc
import glob
from random import randint, seed
from src.Controller.Add_On_OController import AddOptions
from src.Controller.mainPageController import MainPage
from src.View.InputDialogs import Rxdose_Check
from src.View.PatientBar import *
from src.View.DicomView import *
from src.View.DVH import *
from src.View.DicomTree import *
from src.View.StructureInformation import *


class Ui_MainWindow(object):

    # To initiate progress bar for pyradiomics through anonymization
    pyradi_trigger = QtCore.pyqtSignal(str, dict, str)

    def setupUi(self, MainWindow, path, dataset, filepaths, rois, raw_dvh, dvhxy, raw_contour, num_points, pixluts):

        ##############################
        #  LOAD PATIENT INFORMATION  #
        ##############################
        self.dataset = dataset
        self.raw_dvh = raw_dvh
        self.dvh_x_y = dvhxy
        self.rois = rois
        self.filepaths = filepaths
        self.path = path
        # dataset = self.dataset
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
        dose_check_dialog = Rxdose_Check(self.rxdose)
        dose_check_dialog.exec()
        self.rxdose = dose_check_dialog.get_dose()

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

        # self.rois = get_roi_info(self.dataset_rtss)
        self.listRoisID = self.orderedListRoiID()
        self.np_listRoisID = np.array(self.listRoisID)
        self.dict_UID = dict_instanceUID(self.dataset)
        self.selected_rois = []
        self.selected_doses = []

        # self.raw_dvh = calc_dvhs(self.dataset_rtss, self.dataset_rtdose, self.rois)
        # self.dvh_x_y = converge_to_O_dvh(self.raw_dvh)
        self.basicInfo = get_basic_info(self.dataset[0])
        self.pixmapWindowing = None

        self.dict_pixluts = pixluts
        self.dict_raw_ContourData = raw_contour
        self.dict_NumPoints = num_points

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

        self.roiColor = self.initRoiColor()  # Color squares initialization for each ROI
        self.callClass = MainPage(self.path, self.dataset, self.filepaths, self.raw_dvh)
        self.callManager = AddOptions()


        ##########################################
        #  IMPLEMENTATION OF THE MAIN PAGE VIEW  #
        ##########################################

        # Main Window
        MainWindow.setObjectName("MainWindow")
        MainWindow.setMinimumSize(1080, 700)
        MainWindow.setWindowIcon(QtGui.QIcon("src/Icon/DONE.jpg"))
        # Central Layer
        self.mainWidget = QtWidgets.QWidget(MainWindow)
        self.mainWidget.setObjectName("mainWidget")
        self.mainWidget.setFocusPolicy(QtCore.Qt.NoFocus)
        self.main_layout = QtWidgets.QVBoxLayout(self.mainWidget)
        
        self.patient_bar = PatientBar(self)

        #######################################
        #######################################


        self.mainView_widget = QtWidgets.QWidget(MainWindow)
        self.mainView_widget.setObjectName("mainView_widget")
        self.mainView_widget.setFocusPolicy(QtCore.Qt.NoFocus)
        self.hLayout_mainView = QtWidgets.QHBoxLayout(self.mainView_widget)
        self.hLayout_mainView.setContentsMargins(0, 0, 0, 0)

        # Left Column
        self.left_widget = QtWidgets.QWidget(self.mainWidget)
        self.vLayout_left = QtWidgets.QVBoxLayout(self.left_widget)
        self.vLayout_left.setContentsMargins(0, 0, 0, 0)
        self.left_widget.setMaximumWidth(230)

        #######################################
        
        # Left Top Column: Structure and Isodoses Tabs
        self.tab1 = QtWidgets.QTabWidget(self.left_widget)
        self.tab1.setFocusPolicy(QtCore.Qt.NoFocus)
        self.tab1.setGeometry(QtCore.QRect(0, 40, 200, 361))
        self.tab1.setObjectName("tab1")
        # Left Column: Structures tab
        self.initStructCol()
        self.updateStructCol()
        self.tab1.addTab(self.tab1_structures, "")
        # Left Column: Isodoses tab
        self.initIsodColumn()
        self.tab1.addTab(self.tab1_isodoses, "")

        #######################################

        # Create the UI of Structure Information (bottom left of the window)
        self.struct_info = StructureInformation(self)

        self.vLayout_left.addWidget(self.tab1)
        self.vLayout_left.addWidget(self.struct_info.widget)

        ############################################
        ############################################

        # Main view
        self.tab2 = QtWidgets.QTabWidget(self.mainWidget)
        self.tab2.setGeometry(QtCore.QRect(200, 40, 880, 561))
        self.tab2.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        self.tab2.setObjectName("tab2")

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


        self.hLayout_mainView.addWidget(self.left_widget)
        self.hLayout_mainView.addWidget(self.tab2)

        self.main_layout.addWidget(self.mainView_widget)

        self.tab1.raise_()
        self.tab2.raise_()

        # Bottom Layer
        self.bottom_widget = QtWidgets.QWidget(self.mainWidget)
        self.hLayout_bottom = QtWidgets.QHBoxLayout(self.bottom_widget)
        self.hLayout_bottom.setContentsMargins(0, 0, 0, 0)

        # Bottom Layer: "@OnkoDICOM_2019" label
        self.label = QtWidgets.QLabel(self.bottom_widget)
        self.label.setAlignment(QtCore.Qt.AlignRight)
        self.label.setStyleSheet("font: 9pt \"Laksaman\";")
        self.label.setObjectName("label")
        self.label.setFocusPolicy(QtCore.Qt.NoFocus)
        self.hLayout_bottom.addWidget(self.label)

        self.main_layout.addWidget(self.bottom_widget)
        self.bottom_widget.raise_()

        MainWindow.setCentralWidget(self.mainWidget)

        #######################################
        #######################################

        # Menu Bar
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 901, 35))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.menubar.setFocusPolicy(QtCore.Qt.NoFocus)

        # Menu Bar: File, Edit, Tools, Help
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        # self.menuEdit = QtWidgets.QMenu(self.menubar)
        # self.menuEdit.setObjectName("menuEdit")
        self.menuTools = QtWidgets.QMenu(self.menubar)
        self.menuTools.setObjectName("menuTools")
        self.menuHelp = QtWidgets.QMenu(self.menubar)
        self.menuHelp.setObjectName("menuHelp")

        # All icons used for menu bar and toolbar
        iconOpen = QtGui.QIcon()
        iconOpen.addPixmap(QtGui.QPixmap(":/images/Icon/open_patient.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        iconAnonymize_and_Save = QtGui.QIcon()
        iconAnonymize_and_Save.addPixmap(QtGui.QPixmap(":/images/Icon/anonlock.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        iconZoom_In = QtGui.QIcon()
        iconZoom_In.addPixmap(QtGui.QPixmap(":/images/Icon/plus.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        iconZoom_Out = QtGui.QIcon()
        iconZoom_Out.addPixmap(QtGui.QPixmap(":/images/Icon/minus.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        iconWindowing = QtGui.QIcon()
        iconWindowing.addPixmap(QtGui.QPixmap(":/images/Icon/windowing.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        iconTransect = QtGui.QIcon()
        iconTransect.addPixmap(QtGui.QPixmap(":/images/Icon/transect.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        #Icons for creating ROIS
        # iconBrush = QtGui.QIcon()
        # iconBrush.addPixmap(QtGui.QPixmap(":/images/Icon/ROI_Brush.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        # iconIsodose = QtGui.QIcon()
        # iconIsodose.addPixmap(QtGui.QPixmap(":/images/Icon/ROI_Isodose.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        iconadd_on_options = QtGui.QIcon()
        iconadd_on_options.addPixmap(QtGui.QPixmap(":/images/Icon/management.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)
        iconExport = QtGui.QIcon()
        iconExport.addPixmap(QtGui.QPixmap(":/images/Icon/export.png"), QtGui.QIcon.Normal, QtGui.QIcon.On)

        # Set Menu Bar (Tools tab)
        self.menuWindowing = QtWidgets.QMenu(self.menuTools)
        self.menuWindowing.setObjectName("menuWindowing")
        self.menuWindowing.setIcon(iconWindowing)
        # self.menuROI_Creation = QtWidgets.QMenu(self.menuTools)
        # self.menuROI_Creation.setObjectName("menuROI_Creation")
        self.menuExport = QtWidgets.QMenu(self.menuTools)
        self.menuExport.setIcon(iconExport)
        self.menuExport.setObjectName("menuExport")

        # Set Tool Bar
        self.toolBar = QtWidgets.QToolBar(MainWindow)
        self.toolBar.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.toolBar.setMovable(False)
        self.toolBar.setObjectName("toolBar")
        MainWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)

        # Open Patient Action
        self.actionOpen = QtWidgets.QAction(MainWindow)
        self.actionOpen.setIcon(iconOpen)
        self.actionOpen.setIconVisibleInMenu(True)
        self.actionOpen.setObjectName("actionOpen")

        # # Import Action
        # self.actionImport = QtWidgets.QAction(MainWindow)
        # self.actionImport.setObjectName("actionImport")
        #
        # # Save Action
        # self.actionSave = QtWidgets.QAction(MainWindow)
        # self.actionSave.setObjectName("actionSave")

        # Save as Anonymous Action
        self.actionSave_as_Anonymous = QtWidgets.QAction(MainWindow)
        self.actionSave_as_Anonymous.setObjectName("actionSave_as_Anonymous")
        self.actionSave_as_Anonymous.triggered.connect(self.HandleAnonymization)

        # Exit Action
        self.actionExit = QtWidgets.QAction(MainWindow)
        self.actionExit.setObjectName("actionExit")

        #All the Edit actions
        # # Undo Action
        # self.actionUndo = QtWidgets.QAction(MainWindow)
        # self.actionUndo.setObjectName("actionUndo")
        #
        # # Redo Action
        # self.actionRedo = QtWidgets.QAction(MainWindow)
        # self.actionRedo.setObjectName("actionRedo")
        #
        # # Rename ROI Action
        # self.actionRename_ROI = QtWidgets.QAction(MainWindow)
        # self.actionRename_ROI.setObjectName("actionRename_ROI")
        #
        # # Delete ROI Action
        # self.actionDelete_ROI = QtWidgets.QAction(MainWindow)
        # self.actionDelete_ROI.setObjectName("actionDelete_ROI")

        # Zoom In Action
        self.actionZoom_In = QtWidgets.QAction(MainWindow)
        self.actionZoom_In.setIcon(iconZoom_In)
        self.actionZoom_In.setIconVisibleInMenu(True)
        self.actionZoom_In.setObjectName("actionZoom_In")
        self.actionZoom_In.triggered.connect(self.dicom_view.zoomIn)

        # Zoom Out Action
        self.actionZoom_Out = QtWidgets.QAction(MainWindow)

        self.actionZoom_Out.setIcon(iconZoom_Out)
        self.actionZoom_Out.setIconVisibleInMenu(True)
        self.actionZoom_Out.setObjectName("actionZoom_Out")
        self.actionZoom_Out.triggered.connect(self.dicom_view.zoomOut)

        # Windowing Action
        self.actionWindowing = QtWidgets.QAction(MainWindow)
        self.actionWindowing.setIcon(iconWindowing)
        self.actionWindowing.setIconVisibleInMenu(True)
        self.actionWindowing.setObjectName("actionWindowing")
        self.initWindowingMenu(MainWindow)

        # Transect Action
        self.actionTransect = QtWidgets.QAction(MainWindow)
        self.actionTransect.setIcon(iconTransect)
        self.actionTransect.setIconVisibleInMenu(True)
        self.actionTransect.triggered.connect(self.transectHandler)

        # # ROI by brush Action
        # self.actionBrush = QtWidgets.QAction(MainWindow)
        # self.actionBrush.setIcon(iconBrush)
        # self.actionBrush.setIconVisibleInMenu(True)
        # self.actionBrush.setObjectName("actionBrush")
        #
        # # ROI by Isodose Action
        # self.actionIsodose = QtWidgets.QAction(MainWindow)
        # self.actionIsodose.setIcon(iconIsodose)
        # self.actionIsodose.setIconVisibleInMenu(True)
        # self.actionIsodose.setObjectName("actionIsodose")

        # Add-On Options Action
        self.actionadd_on_options = QtWidgets.QAction(MainWindow)
        self.actionadd_on_options.setIcon(iconadd_on_options)
        self.actionadd_on_options.setIconVisibleInMenu(True)
        self.actionadd_on_options.setObjectName("actionadd_on_options")
        self.actionadd_on_options.triggered.connect(self.AddOnOptionsHandler)

        # Anonymize and Save Action
        self.actionAnonymize_and_Save = QtWidgets.QAction(MainWindow)
        self.actionAnonymize_and_Save.setIcon(iconAnonymize_and_Save)
        self.actionAnonymize_and_Save.setIconVisibleInMenu(True)
        self.actionAnonymize_and_Save.setObjectName("actionAnonymize_and_Save")
        self.actionAnonymize_and_Save.triggered.connect(
            self.HandleAnonymization)

        # Export DVH Spreadsheet Action
        self.actionDVH_Spreadsheet = QtWidgets.QAction(MainWindow)
        self.actionDVH_Spreadsheet.setObjectName("actionDVH_Spreadsheet")
        self.actionDVH_Spreadsheet.triggered.connect(self.dvh.export_csv)

        # Export Clinical Data Action
        self.actionClinical_Data = QtWidgets.QAction(MainWindow)
        self.actionClinical_Data.setObjectName("actionClinical_Data")
        self.actionClinical_Data.triggered.connect(self.clinicalDataCheck)

        # Export Pyradiomics Action
        self.actionPyradiomics = QtWidgets.QAction(MainWindow)
        self.actionPyradiomics.setObjectName("actionPyradiomics")

        # Build menu bar
        self.menuFile.addAction(self.actionOpen)
        # self.menuFile.addAction(self.actionImport)
        self.menuFile.addSeparator()
        # self.menuFile.addAction(self.actionSave)
        self.menuFile.addAction(self.actionSave_as_Anonymous)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)
        # self.menuEdit.addAction(self.actionUndo)
        # self.menuEdit.addAction(self.actionRedo)
        # self.menuEdit.addSeparator()
        # self.menuEdit.addAction(self.actionRename_ROI)
        # self.menuEdit.addAction(self.actionDelete_ROI)
        # self.menuROI_Creation.addAction(self.actionBrush)
        # self.menuROI_Creation.addAction(self.actionIsodose)
        self.menuExport.addAction(self.actionDVH_Spreadsheet)
        self.menuExport.addAction(self.actionClinical_Data)
        self.menuExport.addAction(self.actionPyradiomics)

        self.menubar.addAction(self.menuFile.menuAction())
        #self.menubar.addAction(self.menuEdit.menuAction())
        self.menubar.addAction(self.menuTools.menuAction())
        self.menubar.addAction(self.menuHelp.menuAction())

        # Windowing drop-down list on toolbar
        self.windowingButton = QtWidgets.QToolButton()
        self.windowingButton.setMenu(self.menuWindowing)
        self.windowingButton.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.windowingButton.setIcon(iconWindowing)
        self.windowingButton.setFocusPolicy(QtCore.Qt.NoFocus)

        # Export Button drop-down list on toolbar
        self.exportButton = QtWidgets.QToolButton()
        self.exportButton.setMenu(self.menuExport)
        self.exportButton.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.exportButton.setIcon(iconExport)
        self.exportButton.setFocusPolicy(QtCore.Qt.NoFocus)

        # Build toolbar
        self.menuTools.addAction(self.actionZoom_In)
        self.menuTools.addAction(self.actionZoom_Out)
        self.menuTools.addAction(self.menuWindowing.menuAction())
        self.menuTools.addAction(self.actionTransect)
        # self.menuTools.addAction(self.menuROI_Creation.menuAction())
        self.menuTools.addAction(self.actionadd_on_options)
        self.menuTools.addSeparator()
        self.menuTools.addAction(self.menuExport.menuAction())
        self.menuTools.addAction(self.actionAnonymize_and_Save)
        self.menuTools.setFocusPolicy(QtCore.Qt.NoFocus)

        # To create a space in the toolbar
        self.toolbar_spacer = QtWidgets.QWidget()
        self.toolbar_spacer.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.toolbar_spacer.setFocusPolicy(QtCore.Qt.NoFocus)

        self.toolBar.addAction(self.actionOpen)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionZoom_In)
        self.toolBar.addAction(self.actionZoom_Out)
        self.toolBar.addSeparator()
        self.toolBar.addWidget(self.windowingButton)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionTransect)
        self.toolBar.addSeparator()
        # self.toolBar.addAction(self.actionBrush)
        # self.toolBar.addAction(self.actionIsodose)
        # self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionadd_on_options)
        self.toolBar.addWidget(self.toolbar_spacer)
        self.toolBar.addWidget(self.exportButton)
        self.toolBar.addAction(self.actionAnonymize_and_Save)

        self.retranslateUi(MainWindow)
        self.tab1.setCurrentIndex(0)
        self.tab2.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)


    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate

        # Window title
        MainWindow.setWindowTitle(_translate("MainWindow", "OnkoDICOM"))

        # Set tab labels
        self.tab1.setTabText(self.tab1.indexOf(self.tab1_structures), _translate("MainWindow", "Structures"))
        self.tab1.setTabText(self.tab1.indexOf(self.tab1_isodoses), _translate("MainWindow", "Isodoses"))
        self.tab2.setTabText(self.tab2.indexOf(self.tab2_view), _translate("MainWindow", "DICOM View"))
        self.tab2.setTabText(self.tab2.indexOf(self.tab2_DVH), _translate("MainWindow", "DVH"))
        self.tab2.setTabText(self.tab2.indexOf(self.tab2_DICOM_tree), _translate("MainWindow", "DICOM Tree"))
        self.tab2.setTabText(3, "Clinical Data")

        # self.tab2.setTabText(self.tab2.indexOf(self.tab2_clinical_data), _translate("MainWindow", "Clinical Data"))

        # Set "export DVH" button label
        self.dvh.button_export.setText(_translate("MainWindow", "Export DVH"))

        # Set bottom layer label
        self.label.setText(_translate("MainWindow", "@OnkoDICOM 2019"))

        # Set menu labels
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        # self.menuEdit.setTitle(_translate("MainWindow", "Edit"))
        self.menuTools.setTitle(_translate("MainWindow", "Tools"))
        self.menuWindowing.setTitle(_translate("MainWindow", "Windowing"))
        # self.menuROI_Creation.setTitle(_translate("MainWindow", "ROI Creation"))
        self.menuExport.setTitle(_translate("MainWindow", "Export"))
        self.menuHelp.setTitle(_translate("MainWindow", "Help"))
        self.toolBar.setWindowTitle(_translate("MainWindow", "toolBar"))

        # Set action labels (menu and tool bars)
        self.actionOpen.setText(_translate("MainWindow", "Open Patient..."))
        # self.actionImport.setText(_translate("MainWindow", "Import..."))
        # self.actionSave.setText(_translate("MainWindow", "Save"))
        self.actionSave_as_Anonymous.setText(_translate("MainWindow", "Save as Anonymous..."))
        self.actionExit.setText(_translate("MainWindow", "Exit"))
        # self.actionUndo.setText(_translate("MainWindow", "Undo"))
        # self.actionRedo.setText(_translate("MainWindow", "Redo"))
        # self.actionRename_ROI.setText(_translate("MainWindow", "Rename ROI..."))
        # self.actionDelete_ROI.setText(_translate("MainWindow", "Delete ROI..."))
        self.actionZoom_In.setText(_translate("MainWindow", "Zoom In"))
        self.actionZoom_Out.setText(_translate("MainWindow", "Zoom Out"))
        self.actionWindowing.setText(_translate("MainWindow", "Windowing"))
        self.actionTransect.setText(_translate("MainWindow", "Transect"))
        # self.actionBrush.setText(_translate("MainWindow", "ROI by Brush"))
        # self.actionIsodose.setText(_translate("MainWindow", "ROI by Isodose"))
        self.actionadd_on_options.setText(_translate("MainWindow", "Add-On Options..."))
        self.actionAnonymize_and_Save.setText(_translate("MainWindow", "Anonymize and Save"))
        self.actionDVH_Spreadsheet.setText(_translate("MainWindow", "DVH"))
        self.actionClinical_Data.setText(_translate("MainWindow", "Clinical Data"))
        self.actionPyradiomics.setText(_translate("MainWindow", "Pyradiomics"))
        MainWindow.setWindowIcon(QtGui.QIcon("src/Icon/DONE.png"))
        MainWindow.update()

    def orderedListRoiID(self):
        res = []
        for id, value in self.rois.items():
            res.append(id)
        return sorted(res)



    #################################################
    #  STRUCTURES AND ISODOSES TAB FUNCTIONALITIES  #
    #################################################

    # Initialization of colors for ROIs

    def initRoiColor(self):
        roiColor = dict()

        # ROI Display color from RTSS file
        roiContourInfo = self.dictDicomTree_rtss['ROI Contour Sequence']
        if len(roiContourInfo)>0:
            for item, roi_dict in roiContourInfo.items():
                id = item.split()[1]
                roi_id = self.listRoisID[int(id)]
                RGB_dict = dict()
                if 'ROI Display Color' in roiContourInfo[item]:
                    RGB_list = roiContourInfo[item]['ROI Display Color'][0]
                    RGB_dict['R'] = RGB_list[0]
                    RGB_dict['G'] = RGB_list[1]
                    RGB_dict['B'] = RGB_list[2]
                else:
                    seed(1)
                    RGB_dict['R'] = randint(0,255)
                    RGB_dict['G'] = randint(0,255)
                    RGB_dict['B'] = randint(0,255)
                with open('src/data/line&fill_configuration', 'r') as stream:
                    elements = stream.readlines()
                    if len(elements) > 0:
                        roi_line = int(elements[0].replace('\n', ''))
                        roi_opacity = int(elements[1].replace('\n', ''))
                        iso_line = int(elements[2].replace('\n', ''))
                        iso_opacity = int(elements[3].replace('\n', ''))
                    else:
                        roi_line = 1
                        roi_opacity = 10
                        iso_line = 2
                        iso_opacity = 5
                    stream.close()
                roi_opacity = int((roi_opacity / 100) * 255)
                RGB_dict['QColor'] = QtGui.QColor(
                    RGB_dict['R'], RGB_dict['G'], RGB_dict['B'])
                RGB_dict['QColor_ROIdisplay'] = QtGui.QColor(
                    RGB_dict['R'], RGB_dict['G'], RGB_dict['B'], roi_opacity)
                roiColor[roi_id] = RGB_dict
        return roiColor

    # Initialization of the list of structures (left column of the main page)

    def initStructCol(self):
        # Scroll Area
        self.tab1_structures = QtWidgets.QWidget()
        self.tab1_structures.setObjectName("tab1_structures")
        self.tab1_structures.setFocusPolicy(QtCore.Qt.NoFocus)

        self.scrollAreaStruct = QtWidgets.QScrollArea(self.tab1_structures)
        self.hLayout_structures = QtWidgets.QHBoxLayout(self.tab1_structures)
        self.hLayout_structures.setContentsMargins(0, 0, 0, 0)

        self.scrollAreaStruct.setWidgetResizable(True)
        self.scrollAreaStruct.setFocusPolicy(QtCore.Qt.NoFocus)
        # Scroll Area Content
        self.scrollAreaStructContents = QtWidgets.QWidget(self.scrollAreaStruct)
        self.scrollAreaStruct.ensureWidgetVisible(self.scrollAreaStructContents)
        self.scrollAreaStructContents.setFocusPolicy(QtCore.Qt.NoFocus)
        # Grid Layout containing the color squares and the checkboxes
        self.gridL_StructColumn = QtWidgets.QGridLayout(self.scrollAreaStructContents)
        self.gridL_StructColumn.setContentsMargins(5, 5, 5, 5)
        self.gridL_StructColumn.setVerticalSpacing(0)
        self.gridL_StructColumn.setHorizontalSpacing(10)
        self.gridL_StructColumn.setObjectName("gridL_StructColumn")

        self.hLayout_structures.addWidget(self.scrollAreaStruct)

    # Add the contents in the list of structures (left column of the main page)
    def updateStructCol(self):
        index = 0
        for key, value in self.rois.items():

            # Color Square
            colorSquareLabel = QtWidgets.QLabel()
            colorSquarePix = QtGui.QPixmap(15, 15)
            colorSquarePix.fill(self.roiColor[key]['QColor'])
            colorSquareLabel.setPixmap(colorSquarePix)
            self.gridL_StructColumn.addWidget(colorSquareLabel, index, 0, 1, 1)
            # QCheckbox
            text = value['name']
            checkBoxStruct = QtWidgets.QCheckBox()
            checkBoxStruct.setFocusPolicy(QtCore.Qt.NoFocus)
            checkBoxStruct.clicked.connect(
                lambda state, text=key: self.checkedStruct(state, text))
            checkBoxStruct.setStyleSheet("font: 10pt \"Laksaman\";")
            checkBoxStruct.setText(text)
            checkBoxStruct.setObjectName(text)
            self.gridL_StructColumn.addWidget(checkBoxStruct, index, 1, 1, 1)
            index += 1
        self.scrollAreaStruct.setStyleSheet(
            "QScrollArea {background-color: #ffffff; border-style: none;}")
        self.scrollAreaStructContents.setStyleSheet(
            "QWidget {background-color: #ffffff; border-style: none;}")

        vspacer = QtWidgets.QSpacerItem(
            QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridL_StructColumn.addItem(vspacer, index + 1, 0, 1, -1)

        hspacer = QtWidgets.QSpacerItem(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.gridL_StructColumn.addItem(hspacer, 0, 2, -1, 1)

        self.scrollAreaStruct.setWidget(self.scrollAreaStructContents)

    # Function triggered when the state of checkbox of a structure has changed
    #   Update the list of selected structures and DVH view

    def checkedStruct(self, state, key):
        # Checkbox of the structure checked
        if state:
            # Add the structure in the list of selected ROIS
            self.selected_rois.append(key)
            # Select the corresponding item in Structure Info selector
            #select the real index from the np array since the keys differ
            index = np.where(self.np_listRoisID == key)
            index = index[0][0] + 1
            self.struct_info.combobox.setCurrentIndex(index)
            self.struct_info.item_selected(index)

        # Checkbox of the structure unchecked
        else:
            # Remove the structure from the list of selected ROIS
            self.selected_rois.remove(key)

        # Update the DVH view
        self.dvh.update_plot(self)

        self.dicom_view.update_view()

    # Initialize the list of isodoses (left column of the main page)

    def initIsodColumn(self):
        self.tab1_isodoses = QtWidgets.QWidget()
        self.tab1_isodoses.setFocusPolicy(QtCore.Qt.NoFocus)
        self.tab1_isodoses.setGeometry(QtCore.QRect(0, 0, 198, 320))
        self.gridL_IsodCol = QtWidgets.QGridLayout(self.tab1_isodoses)
        self.gridL_IsodCol.setContentsMargins(5, 1, 0, 0)
        self.gridL_IsodCol.setVerticalSpacing(1)
        self.gridL_IsodCol.setHorizontalSpacing(10)
        self.gridL_IsodCol.setObjectName("gridL_IsodCol")
        # Color squares
        self.color1_isod = self.colorSquareDraw(131, 0, 0)
        self.color2_isod = self.colorSquareDraw(185, 0, 0)
        self.color3_isod = self.colorSquareDraw(255, 46, 0)
        self.color4_isod = self.colorSquareDraw(255, 161, 0)
        self.color5_isod = self.colorSquareDraw(253, 255, 0)
        self.color6_isod = self.colorSquareDraw(0, 255, 0)
        self.color7_isod = self.colorSquareDraw(0, 143, 0)
        self.color8_isod = self.colorSquareDraw(0, 255, 255)
        self.color9_isod = self.colorSquareDraw(33, 0, 255)
        self.color10_isod = self.colorSquareDraw(11, 0, 134)
        self.gridL_IsodCol.addWidget(self.color1_isod, 0, 0, 1, 1)
        self.gridL_IsodCol.addWidget(self.color2_isod, 1, 0, 1, 1)
        self.gridL_IsodCol.addWidget(self.color3_isod, 2, 0, 1, 1)
        self.gridL_IsodCol.addWidget(self.color4_isod, 3, 0, 1, 1)
        self.gridL_IsodCol.addWidget(self.color5_isod, 4, 0, 1, 1)
        self.gridL_IsodCol.addWidget(self.color6_isod, 5, 0, 1, 1)
        self.gridL_IsodCol.addWidget(self.color7_isod, 6, 0, 1, 1)
        self.gridL_IsodCol.addWidget(self.color8_isod, 7, 0, 1, 1)
        self.gridL_IsodCol.addWidget(self.color9_isod, 8, 0, 1, 1)
        self.gridL_IsodCol.addWidget(self.color10_isod, 9, 0, 1, 1)
        # Checkboxes
        val_isod1 = int(1.07 * self.rxdose)
        val_isod2 = int(1.05 * self.rxdose)
        val_isod3 = int(1.00 * self.rxdose)
        val_isod4 = int(0.95 * self.rxdose)
        val_isod5 = int(0.90 * self.rxdose)
        val_isod6 = int(0.80 * self.rxdose)
        val_isod7 = int(0.70 * self.rxdose)
        val_isod8 = int(0.60 * self.rxdose)
        val_isod9 = int(0.30 * self.rxdose)
        val_isod10 = int(0.10 * self.rxdose)
        self.box1_isod = QtWidgets.QCheckBox(
            "107 % / " + str(val_isod1) + " cGy [Max]")
        self.box2_isod = QtWidgets.QCheckBox(
            "105 % / " + str(val_isod2) + " cGy")
        self.box3_isod = QtWidgets.QCheckBox(
            "100 % / " + str(val_isod3) + " cGy")
        self.box4_isod = QtWidgets.QCheckBox(
            "95 % / " + str(val_isod4) + " cGy")
        self.box5_isod = QtWidgets.QCheckBox(
            "90 % / " + str(val_isod5) + " cGy")
        self.box6_isod = QtWidgets.QCheckBox(
            "80 % / " + str(val_isod6) + " cGy")
        self.box7_isod = QtWidgets.QCheckBox(
            "70 % / " + str(val_isod7) + " cGy")
        self.box8_isod = QtWidgets.QCheckBox(
            "60 % / " + str(val_isod8) + " cGy")
        self.box9_isod = QtWidgets.QCheckBox(
            "30 % / " + str(val_isod9) + " cGy")
        self.box10_isod = QtWidgets.QCheckBox(
            "10 % / " + str(val_isod10) + " cGy")
        self.box1_isod.setFocusPolicy(QtCore.Qt.NoFocus)
        self.box2_isod.setFocusPolicy(QtCore.Qt.NoFocus)
        self.box3_isod.setFocusPolicy(QtCore.Qt.NoFocus)
        self.box4_isod.setFocusPolicy(QtCore.Qt.NoFocus)
        self.box5_isod.setFocusPolicy(QtCore.Qt.NoFocus)
        self.box6_isod.setFocusPolicy(QtCore.Qt.NoFocus)
        self.box7_isod.setFocusPolicy(QtCore.Qt.NoFocus)
        self.box8_isod.setFocusPolicy(QtCore.Qt.NoFocus)
        self.box9_isod.setFocusPolicy(QtCore.Qt.NoFocus)
        self.box10_isod.setFocusPolicy(QtCore.Qt.NoFocus)
        with open('src/data/line&fill_configuration', 'r') as stream:
            elements = stream.readlines()
            if len(elements) > 0:
                roi_line = int(elements[0].replace('\n', ''))
                roi_opacity = int(elements[1].replace('\n', ''))
                iso_line = int(elements[2].replace('\n', ''))
                iso_opacity = int(elements[3].replace('\n', ''))
            else:
                roi_line = 1
                roi_opacity = 10
                iso_line = 2
                iso_opacity = 5
            stream.close()
        iso_opacity = int((iso_opacity / 100) * 255)
        self.box1_isod.clicked.connect(lambda state, text=[107, QtGui.QColor(131, 0, 0, iso_opacity)]:
                                       self.checked_dose(state, text))
        self.box2_isod.clicked.connect(lambda state, text=[105, QtGui.QColor(185, 0, 0, iso_opacity)]:
                                       self.checked_dose(state, text))
        self.box3_isod.clicked.connect(lambda state, text=[100, QtGui.QColor(255, 46, 0, iso_opacity)]:
                                       self.checked_dose(state, text))
        self.box4_isod.clicked.connect(lambda state, text=[95, QtGui.QColor(255, 161, 0, iso_opacity)]:
                                       self.checked_dose(state, text))
        self.box5_isod.clicked.connect(lambda state, text=[90, QtGui.QColor(253, 255, 0, iso_opacity)]:
                                       self.checked_dose(state, text))
        self.box6_isod.clicked.connect(lambda state, text=[80, QtGui.QColor(0, 255, 0, iso_opacity)]:
                                       self.checked_dose(state, text))
        self.box7_isod.clicked.connect(lambda state, text=[70, QtGui.QColor(0, 143, 0, iso_opacity)]:
                                       self.checked_dose(state, text))
        self.box8_isod.clicked.connect(lambda state, text=[60, QtGui.QColor(0, 255, 255, iso_opacity)]:
                                       self.checked_dose(state, text))
        self.box9_isod.clicked.connect(lambda state, text=[30, QtGui.QColor(33, 0, 255, iso_opacity)]:
                                       self.checked_dose(state, text))
        self.box10_isod.clicked.connect(lambda state, text=[10, QtGui.QColor(11, 0, 134, iso_opacity)]:
                                        self.checked_dose(state, text))

        self.box1_isod.setStyleSheet("font: 10pt \"Laksaman\";")
        self.box2_isod.setStyleSheet("font: 10pt \"Laksaman\";")
        self.box3_isod.setStyleSheet("font: 10pt \"Laksaman\";")
        self.box4_isod.setStyleSheet("font: 10pt \"Laksaman\";")
        self.box5_isod.setStyleSheet("font: 10pt \"Laksaman\";")
        self.box6_isod.setStyleSheet("font: 10pt \"Laksaman\";")
        self.box7_isod.setStyleSheet("font: 10pt \"Laksaman\";")
        self.box8_isod.setStyleSheet("font: 10pt \"Laksaman\";")
        self.box9_isod.setStyleSheet("font: 10pt \"Laksaman\";")
        self.box10_isod.setStyleSheet("font: 10pt \"Laksaman\";")
        self.gridL_IsodCol.addWidget(self.box1_isod, 0, 1, 1, 1)
        self.gridL_IsodCol.addWidget(self.box2_isod, 1, 1, 1, 1)
        self.gridL_IsodCol.addWidget(self.box3_isod, 2, 1, 1, 1)
        self.gridL_IsodCol.addWidget(self.box4_isod, 3, 1, 1, 1)
        self.gridL_IsodCol.addWidget(self.box5_isod, 4, 1, 1, 1)
        self.gridL_IsodCol.addWidget(self.box6_isod, 5, 1, 1, 1)
        self.gridL_IsodCol.addWidget(self.box7_isod, 6, 1, 1, 1)
        self.gridL_IsodCol.addWidget(self.box8_isod, 7, 1, 1, 1)
        self.gridL_IsodCol.addWidget(self.box9_isod, 8, 1, 1, 1)
        self.gridL_IsodCol.addWidget(self.box10_isod, 9, 1, 1, 1)

        vspacer = QtWidgets.QSpacerItem(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.gridL_IsodCol.addItem(vspacer, 10, 0, 2, -1)

    # Function triggered when a dose level selected
    # Updates the list of selected isodoses and dicom view
    def checked_dose(self, state, key):
        if state:
            # Add the dose to the list of selected doses
            self.selected_doses.append(key)
        else:
            # Remove dose from list of previously selected doses
            self.selected_doses.remove(key)
        # Update the dicom view
        self.dicom_view.update_view()

    # Draw color squares
    def colorSquareDraw(self, a, b, c):
        colorSquareLabel = QtWidgets.QLabel()
        colorSquarePix = QtGui.QPixmap(15, 15)
        colorSquarePix.fill(QtGui.QColor(a, b, c))
        colorSquareLabel.setPixmap(colorSquarePix)
        return colorSquareLabel
    

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
                                                "A Clinical Data file exists for this patient! If you wish \nto update it you can do so in the Clinical Data tab.",
                                                QtWidgets.QMessageBox.Ok)
            if SaveReply == QtWidgets.QMessageBox.Ok:
                pass



    #############################
    #  TOOLBAR FUNCTI0NALITIES  #
    #############################

    def initWindowingMenu(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate

        # Get the right order for windowing names
        names_ordered = sorted(self.dict_windowing.keys())
        if 'Normal' in self.dict_windowing.keys():
            old_index = names_ordered.index('Normal')
            names_ordered.insert(0, names_ordered.pop(old_index))

        # Create actions for each windowing items
        for name in names_ordered:
            text = str(name)
            actionWindowingItem = QtWidgets.QAction(MainWindow)
            actionWindowingItem.triggered.connect(
                lambda state, text=name: self.setWindowingLimits(state, text))
            self.menuWindowing.addAction(actionWindowingItem)
            actionWindowingItem.setText(_translate("MainWindow", text))

    def HandleAnonymization(self):
        SaveReply = QtWidgets.QMessageBox.information(self, "Confirmation",
                                            "Are you sure you want to perform anonymization?",
                                            QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        if SaveReply == QtWidgets.QMessageBox.Yes:
            self.hashed_path = self.callClass.runAnonymization(self)
            self.pyradi_trigger.emit(self.path, self.filepaths, self.hashed_path) 
        if SaveReply == QtWidgets.QMessageBox.No:
            pass

    def setWindowingLimits(self, state, text):
        # Get the values for window and level from the dict
        windowing_limits = self.dict_windowing[text]

        # Set window and level to the new values
        self.window = windowing_limits[0]
        self.level = windowing_limits[1]

        # Create a deep copy of the pixel values as they are a list of list
        img_data = deepcopy(self.pixel_values)

        # Get id of current slice
        id = self.dicom_view.slider.value()
        np_pixels = img_data[id]

        # Update current slice with the new window and level values
        self.pixmapWindowing = scaled_pixmap(
            np_pixels, self.window, self.level)
        self.dicom_view.update_view(windowingChange=True)

        # Update all the pixmaps with the updated window and level values
        self.pixmaps = get_pixmaps(img_data, self.window, self.level)

    def transectHandler(self):

        id = self.dicom_view.slider.value()
        dt = self.dataset[id]
        rowS = dt.PixelSpacing[0]
        colS = dt.PixelSpacing[1]
        dt.convert_pixel_data()
        self.callClass.runTransect(
            self, self.dicom_view.view, self.pixmaps[id], dt._pixel_array.transpose(), rowS, colS)

    def AddOnOptionsHandler(self):
        options = self.callManager.show_add_on_options()

