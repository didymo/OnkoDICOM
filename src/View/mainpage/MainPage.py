import logging
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtWidgets import QGridLayout, QWidget, QVBoxLayout, QStackedWidget

from src.Controller.ActionHandler import ActionHandler
from src.Controller.AddOnOptionsController import AddOptions
from src.Controller.MainPageController import MainPageCallClass
from src.Controller.ROIOptionsController import ROIDrawOption
from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.SUV2ROI import SUV2ROI
from src.View.ImageFusion.ROITransferOptionView import ROITransferOptionView
from src.View.StyleSheetReader import StyleSheetReader
from src.View.mainpage.AutoSegmentationTab import AutoSegmentationTab
from src.View.mainpage.DVHTab import DVHTab
from src.View.mainpage.DicomTreeView import DicomTreeView
from src.View.mainpage.DicomAxialView import DicomAxialView
from src.View.mainpage.DicomCoronalView import DicomCoronalView
from src.View.mainpage.DicomSagittalView import DicomSagittalView
from src.View.mainpage.WindowingSlider import WindowingSlider
from src.View.mainpage.IsodoseTab import IsodoseTab
from src.View.mainpage.MenuBar import MenuBar
from src.View.mainpage.DicomView3D import DicomView3D
from src.View.mainpage.Toolbar import Toolbar
from src.View.mainpage.PatientBar import PatientBar
from src.View.mainpage.StructureTab import StructureTab
from src.View.mainpage.DicomStackedWidget import DicomStackedWidget
from src.View.mainpage.MLTab import MLTab
from src.View.PTCTFusion.PETCTView import PetCtView
from src.View.ProgressWindow import ProgressWindow

from src.View.ImageFusion.ImageFusionAxialView import ImageFusionAxialView
from src.View.ImageFusion.ImageFusionSagittalView import \
    ImageFusionSagittalView
from src.View.ImageFusion.ImageFusionCoronalView import ImageFusionCoronalView
from src.Model.MovingDictContainer import MovingDictContainer
from src.View.ImageFusion.TranslateRotateMenu import TranslateRotateMenu


from src.Controller.PathHandler import resource_path
from src.constants import INITIAL_FOUR_VIEW_ZOOM
from src._version import __version__



class UIMainWindow:
    """
    The central class responsible for initializing most of the values stored
    in the PatientDictContainer model and defining the visual layout of the
    main window of OnkoDICOM. No class has access to the attributes
    belonging to this class, except for the class's ActionHandler, which is
    used to trigger actions within the main window. Components of this class
    (i.e. QWidget child classes such as StructureTab, DicomView, DicomTree,
    etc.) should not be able to reference this class, and rather should
    exist independently and only be able to communicate with the
    PatientDictContainer model. If a component needs to communicate with
    another component, that should be accomplished by emitting signals
    within that components, and having the slots for those signals within
    this class (as demonstrated by the update_views() method of this class).
    If a class needs to trigger one of the actions defined in the
    ActionHandler, then the instance of the ActionHandler itself can safely
    be passed into the class.
    """
    pyradi_trigger = QtCore.Signal(str, dict, str)

    # Connect to GUIController
    image_fusion_main_window = QtCore.Signal()

    def setup_ui(self, main_window_instance):
        self.main_window_instance = main_window_instance
        self.call_class = MainPageCallClass()
        self.add_on_options_controller = AddOptions(self)

        ##########################################
        #  IMPLEMENTATION OF THE MAIN PAGE VIEW  #
        ##########################################
        self.stylesheet = StyleSheetReader()

        window_icon = QIcon()
        window_icon.addPixmap(QPixmap(resource_path(
            "res/images/icon.ico")), QIcon.Normal, QIcon.Off)
        self.main_window_instance.setMinimumSize(1080, 700)
        self.main_window_instance.setObjectName("MainOnkoDicomWindowInstance")
        self.main_window_instance.setWindowIcon(window_icon)
        self.main_window_instance.setStyleSheet(self.stylesheet())

        self.setup_central_widget()
        self.setup_actions()

        # Create SUV2ROI object and connect signals
        self.suv2roi = SUV2ROI()
        self.suv2roi_progress_window = \
            ProgressWindow(self.main_window_instance,
                           QtCore.Qt.WindowTitleHint |
                           QtCore.Qt.WindowCloseButtonHint)
        self.suv2roi_progress_window.signal_loaded.connect(
            self.on_loaded_suv2roi)

    def setup_actions(self):
        if hasattr(self, 'toolbar'):
            self.main_window_instance.removeToolBar(self.toolbar)
        self.action_handler = ActionHandler(self)
        self.menubar = MenuBar(self.action_handler)
        self.main_window_instance.setMenuBar(self.menubar)
        self.toolbar = Toolbar(self.action_handler)
        self.main_window_instance.addToolBar(
            QtCore.Qt.TopToolBarArea, self.toolbar)
        self.windowing_slider.set_action_handler(
            self.action_handler)
        self.main_window_instance.setWindowTitle("OnkoDICOM")

    def setup_central_widget(self):
        patient_dict_container = PatientDictContainer()
        self.central_widget = QtWidgets.QWidget()
        self.central_widget_layout = QVBoxLayout()

        self.patient_bar = PatientBar()

        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)

        # Left panel contains stuctures tab, isodoses tab,
        # and structure information
        self.left_panel = QtWidgets.QTabWidget()
        self.left_panel.setMinimumWidth(300)
        self.left_panel.setMaximumWidth(500)

        # Add structures tab to left panel
        if not hasattr(self, 'structures_tab'):
            self.structures_tab = StructureTab()
            self.structures_tab.request_update_structures.connect(
                self.update_views)
            self.structures_tab.signal_roi_draw.connect(self.add_draw_roi_instance)
        else:
            self.structures_tab.update_ui()
        self.left_panel.addTab(self.structures_tab, "Structures")

        if patient_dict_container.has_modality("rtdose"):
            self.isodoses_tab = IsodoseTab()
            self.isodoses_tab.request_update_isodoses.connect(
                self.update_views)
            self.isodoses_tab.request_update_ui.connect(
                self.structures_tab.fixed_container_structure_modified)
            self.left_panel.addTab(self.isodoses_tab, "Isodoses")
        elif hasattr(self, 'isodoses_tab'):
            del self.isodoses_tab

        # Add Auto-Segmentation to the left panel
        if not hasattr(self, 'auto_segmentation_tab'):
            self.auto_segmentation_tab = AutoSegmentationTab(self.stylesheet)
            # Obtain controller from auto segment tab
            self._controller = self.auto_segmentation_tab.get_autoseg_controller()

            # Connect update structures signal to main slot
            self._controller.update_structure_list.connect(self.structures_tab.update_ui)

        self.left_panel.addTab(self.auto_segmentation_tab, "Auto-Seg")

        # Right panel contains the different tabs of DICOM view, DVH,
        # clinical data, DICOM tree
        self.right_panel = QtWidgets.QTabWidget()

        # Create a Dicom View containing single-slice and 3-slice views
        self.dicom_view = DicomStackedWidget(self.format_data)

        roi_color_dict = self.structures_tab.color_dict if hasattr(
            self, 'structures_tab') else None
        iso_color_dict = self.isodoses_tab.color_dict if hasattr(
            self, 'isodoses_tab') else None
        self.dicom_single_view = DicomAxialView(
            roi_color=roi_color_dict, iso_color=iso_color_dict)
        self.dicom_axial_view = DicomAxialView(
            is_four_view=True, roi_color=roi_color_dict, iso_color=iso_color_dict,
            metadata_formatted=True, cut_line_color=QtGui.QColor(255, 0, 0))
        self.dicom_sagittal_view = DicomSagittalView(
            roi_color=roi_color_dict, iso_color=iso_color_dict,
            cut_line_color=QtGui.QColor(0, 255, 0))
        self.dicom_coronal_view = DicomCoronalView(
            roi_color=roi_color_dict, iso_color=iso_color_dict,
            cut_line_color=QtGui.QColor(0, 0, 255))
        self.three_dimension_view = DicomView3D()
        self.windowing_slider = WindowingSlider(self.dicom_single_view)

        # Rescale the size of the scenes inside the 3-slice views
        self.dicom_axial_view.zoom = INITIAL_FOUR_VIEW_ZOOM
        self.dicom_sagittal_view.zoom = INITIAL_FOUR_VIEW_ZOOM
        self.dicom_coronal_view.zoom = INITIAL_FOUR_VIEW_ZOOM
        self.dicom_axial_view.update_view(zoom_change=True)
        self.dicom_sagittal_view.update_view(zoom_change=True)
        self.dicom_coronal_view.update_view(zoom_change=True)

        self.dicom_four_views = QWidget()
        self.dicom_four_views_layout = QGridLayout()

        for i in range(2):
            self.dicom_four_views_layout.setColumnStretch(i, 1)
            self.dicom_four_views_layout.setRowStretch(i, 1)
        self.dicom_four_views_layout.addWidget(self.dicom_axial_view, 0, 0)
        self.dicom_four_views_layout.addWidget(self.dicom_sagittal_view, 0, 1)
        self.dicom_four_views_layout.addWidget(self.dicom_coronal_view, 1, 0)
        self.dicom_four_views_layout.addWidget(self.three_dimension_view, 1, 1)

        self.dicom_four_views.setLayout(self.dicom_four_views_layout)

        self.dicom_four_views_slider = QWidget()
        self.dicom_four_views_slider_layout = QGridLayout()
        self.dicom_four_views_slider_layout.addWidget(self.dicom_four_views, 0, 1)

        self.dicom_four_views_slider.setLayout(self.dicom_four_views_slider_layout)

        self.dicom_single_view_widget = QWidget()
        self.dicom_single_view_layout = QGridLayout()
        self.dicom_single_view_layout.addWidget(self.windowing_slider, 0, 0)
        self.dicom_single_view_layout.addWidget(self.dicom_single_view, 0, 1)
        self.dicom_single_view_widget.setLayout(self.dicom_single_view_layout)

        self.dicom_view.addWidget(self.dicom_four_views_slider)
        self.dicom_view.addWidget(self.dicom_single_view_widget)
        self.dicom_view.setCurrentWidget(self.dicom_single_view_widget)

        # Add DICOM View to right panel as a tab
        self.right_panel.addTab(self.dicom_view, "DICOM View")

        # Add PETVT View to right panel as a tab
        self.pet_ct_tab = PetCtView()
        self.right_panel.addTab(self.pet_ct_tab, "PET/CT View")

        # Add DVH tab to right panel as a tab
        if patient_dict_container.has_modality("rtdose"):
            self.dvh_tab = DVHTab()
            self.right_panel.addTab(self.dvh_tab, "DVH")
        elif hasattr(self, 'dvh_tab'):
            del self.dvh_tab

        # Add DICOM Tree View tab
        self.dicom_tree = DicomTreeView()
        self.right_panel.addTab(self.dicom_tree, "DICOM Tree")

        # Connect SUV2ROI signal to handler function
        self.dicom_single_view.suv2roi_signal.connect(self.perform_suv2roi)

        # Add clinical data tab
        self.call_class.display_clinical_data(self.right_panel)

        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(self.right_panel)

        # Add ML to right panel as a tab
        self.MLTab= MLTab()
        self.right_panel.addTab(self.MLTab, "Use ML Model")

        # Create footer
        self.footer = QtWidgets.QWidget()
        self.create_footer()

        # Create main content page
        self.main_content = QVBoxLayout()
        self.main_content.addWidget(self.splitter)

        # Create draw roi controller
        self.roi_draw_handler = ROIDrawOption(
            self.structures_tab.fixed_container_structure_modified,
            self.remove_draw_roi_instance
        )

        # Set layout
        self.central_widget_layout.addWidget(self.patient_bar)
        self.central_widget_layout.addLayout(self.main_content)
        self.central_widget_layout.addWidget(self.footer)

        self.central_widget.setLayout(self.central_widget_layout)
        self.main_window_instance.setCentralWidget(self.central_widget)

    def create_footer(self):
        self.footer.setFixedHeight(15)
        layout_footer = QtWidgets.QHBoxLayout(self.footer)
        layout_footer.setContentsMargins(0, 0, 0, 0)

        label_footer = QtWidgets.QLabel("@OnkoDICOM2021 v"+ __version__)
        label_footer.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignRight)

        layout_footer.addWidget(label_footer)

    def update_views(self, update_3d_window=False):
        """
        This function is a slot for signals to request the updating of the
        DICOM View and DVH tabs in order to reflect changes made by other
        components of the main window (for example, when a structure in the
        structures tab is selected, this method needs to be called in order
        for the DICOM view window to be updated to show the new region of
        interest.
        :param update_3d_window: a boolean to mark if 3d model
        needs to be updated
        """

        self.dicom_single_view.update_view()
        self.dicom_axial_view.update_view()
        self.dicom_coronal_view.update_view()
        self.dicom_sagittal_view.update_view()

        if update_3d_window:
            self.three_dimension_view.update_view()

        if hasattr(self, 'dvh_tab'):
            self.dvh_tab.update_plot()

        if hasattr(self, 'pet_ct_tab'):
            if self.pet_ct_tab.initialised:
                self.pet_ct_tab.update_view()

        if hasattr(self, 'image_fusion_view'):
            if self.image_fusion_view_axial is not None:
                self.image_fusion_single_view.update_view()
                self.image_fusion_view_axial.update_view()
                self.image_fusion_view_coronal.update_view()
                self.image_fusion_view_sagittal.update_view()

        if hasattr(self, 'draw_roi'):
            if self.draw_roi is not None:
                self.draw_roi.update_draw_roi_pixmaps()

    def toggle_cut_lines(self):
        if self.dicom_axial_view.horizontal_view is None or \
                self.dicom_axial_view.vertical_view is None or \
                self.dicom_coronal_view.horizontal_view is None or \
                self.dicom_coronal_view.vertical_view is None or \
                self.dicom_sagittal_view.horizontal_view is None or \
                self.dicom_sagittal_view.vertical_view is None:
            self.dicom_axial_view.set_views(self.dicom_coronal_view,
                                            self.dicom_sagittal_view)
            self.dicom_coronal_view.set_views(self.dicom_axial_view,
                                              self.dicom_sagittal_view)
            self.dicom_sagittal_view.set_views(self.dicom_axial_view,
                                               self.dicom_coronal_view)
        else:
            self.dicom_axial_view.set_views(None, None)
            self.dicom_coronal_view.set_views(None, None)
            self.dicom_sagittal_view.set_views(None, None)

        if hasattr(self, 'image_fusion_view'):
            if self.image_fusion_view is not None:
                if self.image_fusion_view_axial.horizontal_view is None or \
                        self.image_fusion_view_axial.vertical_view is None or \
                        self.image_fusion_view_coronal.horizontal_view is None \
                        or self.image_fusion_view_coronal.vertical_view is None \
                        or \
                        self.image_fusion_view_sagittal.horizontal_view is None \
                        or \
                        self.image_fusion_view_sagittal.vertical_view is None:
                    self.image_fusion_view_axial.set_views(
                        self.image_fusion_view_coronal,
                        self.image_fusion_view_sagittal)
                    self.image_fusion_view_coronal.set_views(
                        self.image_fusion_view_axial,
                        self.image_fusion_view_sagittal)

                    self.image_fusion_view_sagittal.set_views(
                        self.image_fusion_view_axial,
                        self.image_fusion_view_coronal)
                else:
                    self.image_fusion_view_axial.set_views(None, None)
                    self.image_fusion_view_coronal.set_views(None, None)
                    self.image_fusion_view_sagittal.set_views(None, None)

    def zoom_in(self, is_four_view, image_reg_single, image_reg_four):
        """
        This function calls the zooming in function on the four view's views
        or the single view depending on what view is showing on screen.
        is_four_view: Whether the four view is showing
        """
        if hasattr(self, 'draw_roi') and self.draw_roi:
            self.draw_roi.onZoomInClicked()
        else:
            if is_four_view:
                self.dicom_axial_view.zoom_in()
                self.dicom_coronal_view.zoom_in()
                self.dicom_sagittal_view.zoom_in()
            else:
                self.dicom_single_view.zoom_in()

            if image_reg_single:
                self.image_fusion_single_view.zoom_in()

            if image_reg_four:
                self.image_fusion_view_axial.zoom_in()
                self.image_fusion_view_coronal.zoom_in()
                self.image_fusion_view_sagittal.zoom_in()

            if self.pet_ct_tab.initialised:
                self.pet_ct_tab.zoom_in()

    def zoom_out(self, is_four_view, image_reg_single, image_reg_four):
        """
        This function calls the zooming out function on the four view's
        views or the single view depending on what view is showing on screen.
        is_four_view: Whether the four view is showing
        """
        if hasattr(self, 'draw_roi') and self.draw_roi:
            self.draw_roi.onZoomOutClicked()
        else:
            if is_four_view:
                self.dicom_axial_view.zoom_out()
                self.dicom_coronal_view.zoom_out()
                self.dicom_sagittal_view.zoom_out()
            else:
                self.dicom_single_view.zoom_out()

            if image_reg_single:
                self.image_fusion_single_view.zoom_out()

            if image_reg_four:
                self.image_fusion_view_axial.zoom_out()
                self.image_fusion_view_coronal.zoom_out()
                self.image_fusion_view_sagittal.zoom_out()

            if self.pet_ct_tab.initialised:
                self.pet_ct_tab.zoom_out()

    def format_data(self, size):
        """
        This function is used to update the meta data's font size and margin
        based on the height and width of the viewports.
        size: The size of the DicomStackedWidget
        """
        self.dicom_axial_view.format_metadata(size)

    def create_image_fusion_tab(self, manual=False):
        """
        This function is used to create the tab for image fusion.
        For manual fusion, overlays the base and overlay images without autofusion.
        Adds a "Fusion Options" tab with the Translate/Rotate menu.
        Uses self.fixed_image_sitk and self.moving_image_sitk if available.
        """
        # Set a flag for Zooming
        self.action_handler.has_image_registration_four = True

        # Instance of Moving Model
        moving_dict_container = MovingDictContainer()

        # Only check for modality if dataset is not None
        if moving_dict_container.dataset is not None and moving_dict_container.has_modality("rtss") and len(self.structures_tab.rois.items()) == 0:
            self.structures_tab.update_ui(moving=True)

        # Define a callback that updates all three views for translation
        def update_all_views(offset):
            for view in [
                self.image_fusion_view_axial,
                self.image_fusion_view_sagittal,
                self.image_fusion_view_coronal,
            ]:
                view.update_overlay_offset(
                    offset,
                    orientation=self.last_fusion_slice_orientation,
                    slice_idx=self.last_fusion_slice_idx
                )


        # Define a callback that updates all three views for rotation
        def update_all_rotations(rotation_tuple):
            for view in [
                self.image_fusion_view_axial,
                self.image_fusion_view_sagittal,
                self.image_fusion_view_coronal,
            ]:
                view.update_overlay_rotation(
                    rotation_tuple,
                    orientation=self.last_fusion_slice_orientation,
                    slice_idx=self.last_fusion_slice_idx
                )

        # --- Connect color pair change to all fusion views ---
        def propagate_color_pair_change(fixed_color, moving_color, coloring_enabled):
            for view in [
                self.image_fusion_view_axial,
                self.image_fusion_view_sagittal,
                self.image_fusion_view_coronal,
            ]:
                if hasattr(view, "_on_color_pair_changed"):
                    # Compose the text as in the combo box for compatibility
                    if not coloring_enabled:
                        text = "No Colors (Grayscale)"
                    elif fixed_color == "Purple" and moving_color == "Green":
                        text = "Purple + Green"
                    elif fixed_color == "Blue" and moving_color == "Yellow":
                        text = "Blue + Yellow"
                    elif fixed_color == "Red" and moving_color == "Cyan":
                        text = "Red + Cyan"
                    else:
                        text = "Purple + Green"
                    view._on_color_pair_changed(text)

        # Fusion Options Tab with Translate/Rotate Menu
        self.fusion_options_tab = None

        if manual:
            self.fusion_options_tab = TranslateRotateMenu()
            self.fusion_options_tab.set_offset_changed_callback(update_all_views)
            self.fusion_options_tab.set_rotation_changed_callback(update_all_rotations)
            self.fusion_options_tab.set_color_pair_changed_callback(propagate_color_pair_change)
            self.fusion_options_tab.set_get_vtk_engine_callback(lambda: vtk_engine)
            self.left_panel.addTab(self.fusion_options_tab, "Fusion Options")
            self.left_panel.setCurrentWidget(self.fusion_options_tab)
    

        # VTKEngine integration
        vtk_engine = None
        # Try to get vtk_engine from loader result (set by TopLevelController)
        if hasattr(self, "images") and isinstance(self.images, dict) and "vtk_engine" in self.images:
            vtk_engine = self.images["vtk_engine"]

        # Pass the shared TranslateRotateMenu to all fusion views
        self.image_fusion_single_view = ImageFusionAxialView(
            vtk_engine=vtk_engine, translation_menu=self.fusion_options_tab)
        self.image_fusion_view = QStackedWidget()
        self.image_fusion_view_axial = ImageFusionAxialView(
            metadata_formatted=False,
            cut_line_color=QtGui.QColor(255, 0, 0),
            vtk_engine=vtk_engine,
            translation_menu=self.fusion_options_tab)
        self.image_fusion_view_sagittal = ImageFusionSagittalView(
            cut_line_color=QtGui.QColor(0, 255, 0),
            vtk_engine=vtk_engine,
            translation_menu=self.fusion_options_tab)
        self.image_fusion_view_coronal = ImageFusionCoronalView(
            cut_line_color=QtGui.QColor(0, 0, 255),
            vtk_engine=vtk_engine,
            translation_menu=self.fusion_options_tab)
        self.image_fusion_roi_transfer_option_view = ROITransferOptionView(
            self.structures_tab.fixed_container_structure_modified,
            self.structures_tab.moving_container_structure_modified)

        # Track the last interacted slice orientation and index for rotation axis
        self.last_fusion_slice_orientation = "axial"
        self.last_fusion_slice_idx = 0

        def on_slider_changed(orientation, value):
            self.last_fusion_slice_orientation = orientation
            self.last_fusion_slice_idx = value

        # Connect each fusion view's slider to update the last interacted orientation/index
        self.image_fusion_view_axial.slider.valueChanged.connect(
            lambda v: on_slider_changed("axial", v))
        self.image_fusion_view_coronal.slider.valueChanged.connect(
            lambda v: on_slider_changed("coronal", v))
        self.image_fusion_view_sagittal.slider.valueChanged.connect(
            lambda v: on_slider_changed("sagittal", v))
        
        # Set slider ranges to VTK extents for all fusion views 
        for view in [self.image_fusion_view_axial, self.image_fusion_view_coronal, self.image_fusion_view_sagittal]:
            if hasattr(view, "set_slider_range_from_vtk"):
                view.set_slider_range_from_vtk()

        # If not using VTKEngine, fall back to static overlays
        if vtk_engine is None and hasattr(self, "fixed_image_sitk") and hasattr(self, "moving_image_sitk"):
            import SimpleITK as sitk
            import numpy as np

            # Convert images to numpy arrays for display
            fixed_arr = sitk.GetArrayFromImage(self.fixed_image_sitk)
            moving_arr = sitk.GetArrayFromImage(self.moving_image_sitk)

            def numpy_to_qpixmap(arr):
                from PySide6.QtGui import QImage, QPixmap
                arr = np.clip(arr, 0, 255).astype(np.uint8)
                h, w = arr.shape
                qimg = QImage(arr.data, w, h, w, QImage.Format_Grayscale8)
                return QPixmap.fromImage(qimg)

            # Axial: slices along z
            axial_images = [numpy_to_qpixmap(fixed_arr[i, :, :]) for i in range(fixed_arr.shape[0])]
            # Coronal: slices along y
            coronal_images = [numpy_to_qpixmap(fixed_arr[:, i, :]) for i in range(fixed_arr.shape[1])]
            # Sagittal: slices along x
            sagittal_images = [numpy_to_qpixmap(fixed_arr[:, :, i]) for i in range(fixed_arr.shape[2])]

            # Store overlays for slider use
            self.image_fusion_view_axial.overlay_images = axial_images
            self.image_fusion_view_coronal.overlay_images = coronal_images
            self.image_fusion_view_sagittal.overlay_images = sagittal_images

            # Connect slider to update overlay
            self.image_fusion_view_axial.slider.valueChanged.connect(
                lambda: self.image_fusion_view_axial.image_display())
            self.image_fusion_view_coronal.slider.valueChanged.connect(
                lambda: self.image_fusion_view_coronal.image_display())
            self.image_fusion_view_sagittal.slider.valueChanged.connect(
                lambda: self.image_fusion_view_sagittal.image_display())

            # Initial display
            self.image_fusion_view_axial.image_display()
            self.image_fusion_view_coronal.image_display()
            self.image_fusion_view_sagittal.image_display()

        # Rescale the size of the scenes inside the 3-slice views
        self.image_fusion_view_axial.zoom = INITIAL_FOUR_VIEW_ZOOM
        self.image_fusion_view_sagittal.zoom = INITIAL_FOUR_VIEW_ZOOM
        self.image_fusion_view_coronal.zoom = INITIAL_FOUR_VIEW_ZOOM
        self.image_fusion_view_axial.update_view(zoom_change=True)
        self.image_fusion_view_sagittal.update_view(zoom_change=True)
        self.image_fusion_view_coronal.update_view(zoom_change=True)

        self.image_fusion_four_views = QWidget()
        self.image_fusion_four_views_layout = QGridLayout()
        for i in range(2):
            self.image_fusion_four_views_layout.setColumnStretch(i, 1)
            self.image_fusion_four_views_layout.setRowStretch(i, 1)
        self.image_fusion_four_views_layout.addWidget(
            self.image_fusion_view_axial, 0, 0)
        self.image_fusion_four_views_layout.addWidget(
            self.image_fusion_view_sagittal, 0, 1)
        self.image_fusion_four_views_layout.addWidget(
            self.image_fusion_view_coronal, 1, 0)

        self.image_fusion_four_views_layout.addWidget(
            self.image_fusion_roi_transfer_option_view, 1, 1
        )

        self.image_fusion_four_views.setLayout(
            self.image_fusion_four_views_layout)

        self.image_fusion_view.addWidget(self.image_fusion_four_views)
        self.image_fusion_view.addWidget(self.image_fusion_single_view)
        self.image_fusion_view.setCurrentWidget(self.image_fusion_four_views)

        # Add Image Fusion Tab
        self.right_panel.addTab(self.image_fusion_view, "Image Fusion")
        self.right_panel.setCurrentWidget(self.image_fusion_view)

        # Update the Add On Option GUI
        self.add_on_options_controller.update_ui()

    def perform_suv2roi(self):
        """
        Performs the SUV2ROI process.
        """
        # Get patient weight - needs to run first as GUI cannot run in
        # threads, like the ProgressBar
        patient_dict_container = PatientDictContainer()
        dataset = patient_dict_container.dataset[0]
        self.suv2roi.get_patient_weight(dataset)
        if self.suv2roi.patient_weight is None:
            return

        # Start the SUV2ROI process
        self.suv2roi_progress_window.start(self.suv2roi.start_conversion)

    def on_loaded_suv2roi(self):
        """
        Called when progress bar has finished. Closes the progress
        window and refreshes the main screen.
        """
        if self.suv2roi.suv2roi_status:
            patient_dict_container = PatientDictContainer()
            self.structures_tab.fixed_container_structure_modified((
                patient_dict_container.get('dataset_rtss'), {"draw": None}))
        else:
            # Alert user that SUV2ROI failed and for what reason
            if self.suv2roi.failure_reason == "UNIT":
                failure_reason = \
                    "PET units are not Bq/mL. OnkoDICOM can currently only\n" \
                    "perform SUV2ROI on PET images stored in these units."
            elif self.suv2roi.failure_reason == "DECY":
                failure_reason = \
                    "PET is not decay corrected. OnkoDICOM can currently " \
                    "only\nperform SUV2ROI on PET images that are decay " \
                    "corrected."
            else:
                failure_reason = "The SUV2ROI process has failed."
            button_reply = \
                QtWidgets.QMessageBox(
                    QtWidgets.QMessageBox.Icon.Warning,
                    "SUV2ROI Failed",
                    failure_reason,
                    QtWidgets.QMessageBox.StandardButton.Ok, self)
            button_reply.button(
                QtWidgets.QMessageBox.StandardButton.Ok).setStyleSheet(
                self.stylesheet())
            button_reply.exec_()

        # Close progress window
        self.suv2roi_progress_window.close()

    def add_draw_roi_instance(self):
        """Use ROIDrawOption controller to add the roi instance to the main window"""
        logging.debug("add_draw_roi_instance started")

        self.splitter.setVisible(False)
        self.draw_roi = self.roi_draw_handler.show_roi_draw_window()
        self.main_content.addWidget(self.draw_roi)
        self.draw_roi_toggle_toolbar_items(True)

    def remove_draw_roi_instance(self):
        """removes the draw roi instance from the main window,
        also removing the instance from the ROIDrawOption controller"""
        logging.debug("remove_draw_roi_instance started")

        self.roi_draw_handler.remove_roi_draw_window()
        self.main_content.removeWidget(self.draw_roi)
        delattr(self, 'draw_roi')
        self.draw_roi_toggle_toolbar_items(False)
        self.splitter.setVisible(True)

    def draw_roi_toggle_toolbar_items(self, disabled):
        """Called to disable toolbar options when they do not apply / cannot be used in the current draw roi context"""
        self.action_handler.action_save_structure.setDisabled(disabled)
        self.action_handler.action_save_as_anonymous.setDisabled(disabled)

        self.action_handler.action_one_view.setDisabled(disabled)
        self.action_handler.action_four_views.setDisabled(disabled)
        self.action_handler.action_show_cut_lines.setDisabled(disabled)
        self.action_handler.action_image_fusion.setDisabled(disabled)
