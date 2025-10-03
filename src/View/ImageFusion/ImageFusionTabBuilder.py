import contextlib
from PySide6 import QtWidgets

from src.Model.MovingDictContainer import MovingDictContainer
from src.View.ImageFusion.TranslateRotateMenu import TranslateRotateMenu

class ImageFusionTabBuilder:
    """
        Helper class to build and configure the Image Fusion tab and all related widgets.

        Responsibilities:
            - Clean up existing fusion widgets and tabs from the main window.
            - Create new fusion views and associated UI components.
            - Configure callbacks for translation, rotation, color pairing, mouse interaction, and overlays.

        Attributes:
            main_window: The main application window object that holds panels, tabs, and image fusion views.
            manual (bool): If True, build the manual fusion tab (with Translate/Rotate/Opacity controls).
    """

    def __init__(self, main_window, manual=False):
        self.main_window = main_window
        self.manual = manual

    def build(self):
        """
            Build the Image Fusion tab and configure all related UI and callbacks.
            Steps:
            - Clean up any existing fusion widgets/tabs.
            - Set up the new fusion tab.
        """
        self._cleanup_old_fusion_widgets_and_tabs()
        self._setup_fusion_tab()
        return

    def _cleanup_old_fusion_widgets_and_tabs(self):
        """
            Helper to clean up old fusion widgets, sliders, and remove the fusion tab
            from the right panel if it exists.

            - Deletes attributes on the main window that reference fusion widgets.
            - Ensures proper cleanup by calling deleteLater() on QWidget instances.
            - Removes the fusion tab from the right panel if one is already present.
        """
        for attr in [
            'image_fusion_single_view',
            'image_fusion_view_axial',
            'image_fusion_view_sagittal',
            'image_fusion_view_coronal',
            'image_fusion_view',
            'fusion_options_tab',
            'windowing_slider',
            'image_fusion_roi_transfer_option_view',
            'image_fusion_four_views',
        ]:
            if hasattr(self.main_window, attr):
                widget = getattr(self.main_window, attr)
                if isinstance(widget, QtWidgets.QWidget):
                    with contextlib.suppress(Exception):
                        if widget is not None and widget.parent() is not None:
                            widget.deleteLater()
                delattr(self.main_window, attr)

        # Remove the fusion tab from the right panel if it exists
        if hasattr(self.main_window, "right_panel") and hasattr(self.main_window, "image_fusion_view"):
            for i in range(self.main_window.right_panel.count()):
                if self.main_window.right_panel.widget(i) == self.main_window.image_fusion_view:
                    self.main_window.right_panel.removeTab(i)
                    break

    def _setup_fusion_tab(self):
        """
            Sets up the fusion tab, views, sliders, and all callbacks.
        """
        main = self.main_window

        # Set a flag for Zooming
        main.action_handler.has_image_registration_four = True

        # Ensure ROI panel is updated if RTSS is present but ROIs are missing
        moving_dict_container = MovingDictContainer()
        if moving_dict_container.dataset is not None and moving_dict_container.has_modality("rtss") and len(
                main.structures_tab.rois.items()) == 0:
            main.structures_tab.update_ui(moving=True)

        # --- Define callbacks for fusion options ---
        def update_all_views(offset):
            """
                Propagate translation offset changes to all fusion views.
            """
            for view in [
                main.image_fusion_single_view,
                main.image_fusion_view_axial,
                main.image_fusion_view_sagittal,
                main.image_fusion_view_coronal,
            ]:
                view.update_overlay_offset(
                    offset,
                    orientation=main.last_fusion_slice_orientation,
                    slice_idx=main.last_fusion_slice_idx
                )

        def update_all_rotations(rotation_tuple):
            """
                Propagate rotation changes to all fusion views.
            """
            for view in [
                main.image_fusion_single_view,
                main.image_fusion_view_axial,
                main.image_fusion_view_sagittal,
                main.image_fusion_view_coronal,
            ]:
                view.update_overlay_rotation(
                    rotation_tuple,
                    orientation=main.last_fusion_slice_orientation,
                    slice_idx=main.last_fusion_slice_idx
                )

        def propagate_color_pair_change(fixed_color, moving_color, coloring_enabled):
            """
                Propagate color pair changes (or grayscale mode) to all fusion views.
            """
            for view in [
                main.image_fusion_single_view,
                main.image_fusion_view_axial,
                main.image_fusion_view_sagittal,
                main.image_fusion_view_coronal,
            ]:
                if hasattr(view, "_on_color_pair_changed"):
                    # Map colors back to UI combo text
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

        # --- Fusion Options Tab with Translate/Rotate Menu ---
        main.fusion_options_tab = None

        if not hasattr(main, "images"):
            main.images = {}

        vtk_engine = None
        if isinstance(main.images, dict) and "vtk_engine" in main.images:
            vtk_engine = main.images["vtk_engine"]

        if self.manual:
            # Build manual Translate/Rotate/Opacity/Color menu
            main.fusion_options_tab = TranslateRotateMenu()
            main.fusion_options_tab.set_offset_changed_callback(update_all_views)
            main.fusion_options_tab.set_rotation_changed_callback(update_all_rotations)
            main.fusion_options_tab.set_color_pair_changed_callback(propagate_color_pair_change)
            main.fusion_options_tab.set_get_vtk_engine_callback(lambda: vtk_engine)
            main.left_panel.addTab(main.fusion_options_tab, "Fusion Options")
            main.left_panel.setCurrentWidget(main.fusion_options_tab)

            def propagate_mouse_mode_change(mode):
                """
                    Propagate mouse mode changes (translate/rotate/interrogation) to all views.
                """
                for view in [
                    main.image_fusion_single_view,
                    main.image_fusion_view_axial,
                    main.image_fusion_view_sagittal,
                    main.image_fusion_view_coronal,
                ]:
                    if hasattr(view, "_on_mouse_mode_changed"):
                        view._on_mouse_mode_changed(mode)
                        view.refresh_overlay_now()

            main.fusion_options_tab.set_mouse_mode_changed_callback(propagate_mouse_mode_change)

        # --- Create and configure fusion views ---
        main._init_fusion_views(vtk_engine)

        # Initialize sliders, ROI, slice tracking, and overlays
        main.init_windowing_slider()
        main.init_roi_transfer_option_view()
        main.init_fusion_slice_tracking()
        main.apply_transform_if_present(vtk_engine)
        main.connect_slider_callbacks()
        main.set_slider_ranges()
        main.setup_static_overlays_if_no_vtk(vtk_engine)
        main.rescale_and_update_fusion_views()
        main.setup_fusion_four_views_layout()
        main.finalize_fusion_tab()