import glob

from PySide6 import QtCore, QtWidgets
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtWidgets import QGridLayout, QWidget, QVBoxLayout, QStackedWidget

from src.Controller.ActionHandler import ActionHandler
from src.Controller.AddOnOptionsController import AddOptions
from src.Controller.MainPageController import MainPageCallClass
from src.Model.PatientDictContainer import PatientDictContainer
from src.View.mainpage.DVHTab import DVHTab
from src.View.mainpage.DicomTreeView import DicomTreeView
from src.View.mainpage.DicomView import DicomView
from src.View.mainpage.IsodoseTab import IsodoseTab
from src.View.mainpage.MenuBar import MenuBar
from src.View.mainpage.Toolbar import Toolbar
from src.View.mainpage.PatientBar import PatientBar
from src.View.mainpage.StructureTab import StructureTab

from src.Controller.PathHandler import resource_path
import platform


class UIMainWindow:
    """
    The central class responsible for initializing most of the values stored in the PatientDictContainer model and
    defining the visual layout of the main window of OnkoDICOM.
    No class has access to the attributes belonging to this class, except for the class's ActionHandler, which is used
    to trigger actions within the main window. Components of this class (i.e. QWidget child classes such as
    StructureTab, DicomView, DicomTree, etc.) should not be able to reference this class, and rather should exist
    independently and only be able to communicate with the PatientDictContainer model. If a component needs to
    communicate with another component, that should be accomplished by emitting signals within that components, and
    having the slots for those signals within this class (as demonstrated by the update_views() method of this class).
    If a class needs to trigger one of the actions defined in the ActionHandler, then the instance of the ActionHandler
    itself can safely be passed into the class.
    """
    pyradi_trigger = QtCore.Signal(str, dict, str)

    def setup_ui(self, main_window_instance):
        self.main_window_instance = main_window_instance
        self.call_class = MainPageCallClass()
        self.add_on_options_controller = AddOptions(self)

        ##########################################
        #  IMPLEMENTATION OF THE MAIN PAGE VIEW  #
        ##########################################
        if platform.system() == 'Darwin':
            self.stylesheet_path = "res/stylesheet.qss"
        else:
            self.stylesheet_path = "res/stylesheet-win-linux.qss"
        stylesheet = open(resource_path(self.stylesheet_path)).read()
        window_icon = QIcon()
        window_icon.addPixmap(QPixmap(resource_path("res/images/icon.ico")), QIcon.Normal, QIcon.Off)
        self.main_window_instance.setMinimumSize(1080, 700)
        self.main_window_instance.setObjectName("MainOnkoDicomWindowInstance")
        self.main_window_instance.setWindowIcon(window_icon)
        self.main_window_instance.setStyleSheet(stylesheet)

        self.setup_central_widget()

        # Create actions and set menu and tool bars
        self.action_handler = ActionHandler(self)
        self.menubar = MenuBar(self.action_handler)
        self.main_window_instance.setMenuBar(self.menubar)
        self.toolbar = Toolbar(self.action_handler)
        self.main_window_instance.addToolBar(QtCore.Qt.TopToolBarArea, self.toolbar)
        self.main_window_instance.setWindowTitle("OnkoDICOM")

    def setup_central_widget(self):
        patient_dict_container = PatientDictContainer()
        self.central_widget = QtWidgets.QWidget()
        self.central_widget_layout = QVBoxLayout()

        self.patient_bar = PatientBar()

        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)

        # Left panel contains stuctures tab, isodoses tab, and structure information
        self.left_panel = QtWidgets.QTabWidget()
        self.left_panel.setMinimumWidth(300)
        self.left_panel.setMaximumWidth(500)

        # Add structures tab to left panel
        if patient_dict_container.has_modality("rtss"):
            self.structures_tab = StructureTab()
            self.structures_tab.request_update_structures.connect(self.update_views)
            self.left_panel.addTab(self.structures_tab, "Structures")

        if patient_dict_container.has_modality("rtdose"):
            self.isodoses_tab = IsodoseTab()
            self.isodoses_tab.request_update_isodoses.connect(self.update_views)
            self.left_panel.addTab(self.isodoses_tab, "Isodoses")

        # Hide left panel if no rtss or rtdose
        if not patient_dict_container.has_modality("rtss") and not patient_dict_container.has_modality("rtdose"):
            self.left_panel.hide()

        # Right panel contains the different tabs of DICOM view, DVH, clinical data, DICOM tree
        self.right_panel = QtWidgets.QTabWidget()

        # Add DICOM View to right panel as a tab
        self.dicom_view = QStackedWidget()

        roi_color_dict = self.structures_tab.color_dict if hasattr(self, 'structures_tab') else None
        iso_color_dict = self.isodoses_tab.color_dict if hasattr(self, 'isodoses_tab') else None
        self.dicom_view_single = DicomView(roi_color=roi_color_dict, iso_color=iso_color_dict)
        self.dicom_view_axial = DicomView(roi_color=roi_color_dict, iso_color=iso_color_dict, axial_view=True)
        self.dicom_view_sagital = DicomView(roi_color=roi_color_dict, iso_color=iso_color_dict, display_metadata=False)
        self.dicom_view_coronal = DicomView(roi_color=roi_color_dict, iso_color=iso_color_dict, display_metadata=False)

        self.dicom_4_views_widget = QWidget()
        self.dicom_4_views_layout = QGridLayout()
        for i in range(2):
            self.dicom_4_views_layout.setColumnStretch(i, 1)
            self.dicom_4_views_layout.setRowStretch(i, 1)
        self.dicom_4_views_layout.addWidget(self.dicom_view_axial, 0, 0)
        self.dicom_4_views_layout.addWidget(self.dicom_view_sagital, 0, 1)
        self.dicom_4_views_layout.addWidget(self.dicom_view_coronal, 1, 0)
        self.dicom_4_views_widget.setLayout(self.dicom_4_views_layout)

        self.dicom_view.addWidget(self.dicom_4_views_widget)
        self.dicom_view.addWidget(self.dicom_view_single)
        self.dicom_view.setCurrentWidget(self.dicom_view_single)
        self.right_panel.addTab(self.dicom_view, "DICOM View")

        # Add DVH tab to right panel as a tab
        if patient_dict_container.has_modality("rtss") and patient_dict_container.has_modality("rtdose"):
            self.dvh_tab = DVHTab()
            self.right_panel.addTab(self.dvh_tab, "DVH")

        self.dicom_tree = DicomTreeView()
        self.right_panel.addTab(self.dicom_tree, "DICOM Tree")

        # Create Clinical Data tab
        # TODO refactor the entire Clinical Data form/display class
        # As they currently stand, they are given the right tab widget, and make direct modifications to the tab.
        # This class should be refactored in the same way as the rest of the main window's components, i.e. the Clinical
        # Data should be a child of QWidget that can exist independently of OnkoDICOM. This class would differ from most
        # other main window components in that rather than interacting with the PatientDictContainer as its model, it
        # would use the patient's ClinicalData csv file as the model (which means that the QWidget would theoretically
        # easily exist outside OnkoDICOM).
        # There are two classes: one for displaying the clinical data, and another for modifying the clinical data.
        # The check below determines whether there already exists a clinical data csv for the patient, and loads either
        # the data display or the data form depending on what exists.
        reg = '/CSV/ClinicalData*[.csv]'
        if not glob.glob(patient_dict_container.path + reg):
            self.call_class.display_cd_form(self.right_panel, patient_dict_container.path)
        else:
            self.call_class.display_cd_dat(self.right_panel, patient_dict_container.path)

        splitter.addWidget(self.left_panel)
        splitter.addWidget(self.right_panel)

        # Create footer
        self.footer = QtWidgets.QWidget()
        self.create_footer()

        # Set layout
        self.central_widget_layout.addWidget(self.patient_bar)
        self.central_widget_layout.addWidget(splitter)
        self.central_widget_layout.addWidget(self.footer)

        self.central_widget.setLayout(self.central_widget_layout)
        self.main_window_instance.setCentralWidget(self.central_widget)

    def create_footer(self):
        self.footer.setFixedHeight(15)
        layout_footer = QtWidgets.QHBoxLayout(self.footer)
        layout_footer.setContentsMargins(0, 0, 0, 0)

        label_footer = QtWidgets.QLabel("@OnkoDICOM 2019-20")
        label_footer.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignRight)

        layout_footer.addWidget(label_footer)

    def update_views(self):
        """
        This function is a slot for signals to request the updating of the DICOM View and DVH tabs in order to reflect
        changes made by other components of the main window (for example, when a structure in the structures tab is
        selected, this method needs to be called in order for the DICOM view window to be updated to show the new
        region of interest.
        """
        self.dicom_view_single.update_view()
        self.dicom_view_axial.update_view()
        if hasattr(self, 'dvh_tab'):
            self.dvh_tab.update_plot()

    def zoom_in(self):
        self.dicom_view.zoom_in()

    def zoom_out(self):
        self.dicom_view.zoom_out()