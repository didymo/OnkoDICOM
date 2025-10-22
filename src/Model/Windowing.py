from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.PTCTDictContainer import PTCTDictContainer
from src.Model.MovingDictContainer import MovingDictContainer
from src.Model.CalculateImages import get_pixmaps
import logging


windowing_slider = None


def windowing_model(text, init):
    """
    Function triggered when a window is selected from the menu.
    :param text: The name of the window selected.
    :param init: list of bool to determine which views are chosen
    """
    patient_dict_container = PatientDictContainer()

    # Use custom window/level for manual fusion overlays (init[3])
    #TODO This is just a patch. Need to figure out why VTK doesnt work with default dicom windowing
    if init[3]:
        custom_presets = {
            "Normal": [400, 40],  # Normal levels (typical soft tissue window)
            "Lung": [1600, -600],  # Lung, covers -1400 to 200 HU
            "Bone": [2000, 300],  # Bone, covers -700 to 1300 HU
            "Brain": [80, 40],  # Brain, covers 0 to 80 HU
            "Soft Tissue": [440, 40],  # Soft tissue, covers -180 to 260 HU (muscle, fat, organs)
            "Head and Neck": [275, 40],  # Covers -147.5 to 227.5 HU
        }
        windowing_limits = custom_presets.get(text, [400, 40])
    else:
        windowing_limits = patient_dict_container.get("dict_windowing")[text]

    window = windowing_limits[0]
    level = windowing_limits[1]

    windowing_model_direct(window, level, init)


def windowing_model_direct(window, level, init, fixed_image_array=None):
    """
    Function triggered when a window is selected from the menu,
    or when the windowing slider bars are adjusted
    :param level: The desired level
    :param window: The desired window
    :param init: list of bool to determine which views are chosen
    """
    patient_dict_container = PatientDictContainer()
    moving_dict_container = MovingDictContainer()
    pt_ct_dict_container = PTCTDictContainer()

    # Update the dictionary of pixmaps with the updated window and level values for DICOM view
    if init[0]:
        pixel_values = patient_dict_container.get("pixel_values")
        pixmap_aspect = patient_dict_container.get("pixmap_aspect")
        pixmaps_axial, pixmaps_coronal, pixmaps_sagittal = \
            get_pixmaps(pixel_values, window, level, pixmap_aspect)

        patient_dict_container.set("pixmaps_axial", pixmaps_axial)
        patient_dict_container.set("pixmaps_coronal", pixmaps_coronal)
        patient_dict_container.set("pixmaps_sagittal", pixmaps_sagittal)
        patient_dict_container.set("window", window)
        patient_dict_container.set("level", level)

        # Update CT view window/level if selected
    if init[2]:
        ct_pixel_values = pt_ct_dict_container.get("ct_pixel_values")
        ct_pixmap_aspect = pt_ct_dict_container.get("ct_pixmap_aspect")
        ct_pixmaps_axial, ct_pixmaps_coronal, ct_pixmaps_sagittal = \
            get_pixmaps(ct_pixel_values, window, level, ct_pixmap_aspect,
                        fusion=True)

        pt_ct_dict_container.set("ct_pixmaps_axial", ct_pixmaps_axial)
        pt_ct_dict_container.set("ct_pixmaps_coronal", ct_pixmaps_coronal)
        pt_ct_dict_container.set("ct_pixmaps_sagittal", ct_pixmaps_sagittal)
        pt_ct_dict_container.set("ct_window", window)
        pt_ct_dict_container.set("ct_level", level)

        # Update PET view window/level if selected
    if init[1]:
        pt_pixel_values = pt_ct_dict_container.get("pt_pixel_values")
        pt_pixmap_aspect = pt_ct_dict_container.get("pt_pixmap_aspect")
        pt_pixmaps_axial, pt_pixmaps_coronal, pt_pixmaps_sagittal = \
            get_pixmaps(pt_pixel_values, window, level, pt_pixmap_aspect,
                        fusion=True, color="Heat")

        pt_ct_dict_container.set("pt_pixmaps_axial", pt_pixmaps_axial)
        pt_ct_dict_container.set("pt_pixmaps_coronal", pt_pixmaps_coronal)
        pt_ct_dict_container.set("pt_pixmaps_sagittal", pt_pixmaps_sagittal)
        pt_ct_dict_container.set("pt_window", window)
        pt_ct_dict_container.set("pt_level", level)

        # Update manual fusion overlays (VTK) if selected
    if init[3]:
        # Only update fusion window/level for manual fusion overlays (VTK)
        patient_dict_container.set("fusion_window", window)
        patient_dict_container.set("fusion_level", level)

        # If fusion views and VTK engines are present, update them
        global windowing_slider
        if (
                'windowing_slider' in globals()
                and windowing_slider is not None
                and hasattr(windowing_slider, "fusion_views")
                and windowing_slider.fusion_views
        ):
            for view in windowing_slider.fusion_views:
                if hasattr(view, "vtk_engine") and view.vtk_engine is not None:

                    view.vtk_engine.set_window_level(float(window), float(level))
                if hasattr(view, "update_color_overlay"):

                    view.update_color_overlay()
            # Also call the fusion window/level callback if present (ensures views update)
            if hasattr(windowing_slider, "fusion_window_level_callback") and callable(
                    windowing_slider.fusion_window_level_callback):
                windowing_slider.fusion_window_level_callback(window, level)
        else:
            logging.error("[windowing_model_direct] Skipping fusion view update: fusion_views is None")


def set_windowing_slider(slider, fusion_views=None):
    """
        Sets the global windowing slider and optionally assigns fusion views for window/level updates.

        This function registers the provided slider as the global windowing slider used for window/level
        adjustments throughout the application. If a list of fusion views is provided, it also assigns
        these views to the slider for coordinated window/level updates in image fusion mode.

        Note: This will overwrite the global windowing_slider. Only one slider (DICOM or fusion) can be active at a time.
        Always call this when switching between DICOM and fusion tabs, or when opening a new patient.

        Args:
            slider: The WindowingSlider instance to set as global.
            fusion_views: Optional list of fusion views to assign to the slider.

        Returns:
            None
        """
    global windowing_slider
    windowing_slider = slider

    windowing_slider.fusion_views = fusion_views if fusion_views is not None else []

