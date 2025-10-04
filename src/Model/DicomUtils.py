

def truncate_ds_fields(ds):
    """
    Truncates all DICOM DS (Decimal String) fields in the dataset to a maximum of 16 characters.

    This function ensures that all DS fields, whether single values or lists, are properly formatted
    as strings representing floats and do not exceed the DICOM standard length. It also handles
    stringified lists and attempts to convert and truncate each value accordingly.

    Args:
        ds: The pydicom Dataset whose DS fields will be truncated.

    Returns:
        None. The dataset is modified in place.
    """

    #TODO if u want to log errors here make sure to sanitise the data
    def _truncate_float_str(val):
        """Convert value to float and return as string, max 16 chars."""
        return f"{float(val):.10g}"[:16]

    def _extract_floats_from_str_list(val):
        """Extract floats from a stringified list and return as list of strings."""
        v_clean = val.strip("[] ")
        result = []
        for part in v_clean.split(","):
            part = part.strip()
            if part:
                try:
                    result.append(_truncate_float_str(part))
                except (ValueError, TypeError):
                    continue
        return result

    for elem in ds.iterall():
        if elem.VR != "DS":
            continue
        value = elem.value
        if isinstance(value, (list, tuple)):
            new_vals = []
            for v in value:
                try:
                    new_vals.append(_truncate_float_str(v))
                except (ValueError, TypeError):
                    if isinstance(v, str) and "[" in v and "]" in v:
                        new_vals.extend(_extract_floats_from_str_list(v))
            elem.value = new_vals
        else:
            try:
                elem.value = _truncate_float_str(value)
            except (ValueError, TypeError):
                if isinstance(value, str) and "[" in value and "]" in value:
                    floats = _extract_floats_from_str_list(value)
                    if floats:
                        elem.value = floats[0]
                        
def update_color_overlay_for_fusion(view_instance):
    """
    Utility function to update the color overlay for a fusion view.
    This function refreshes the displayed fusion colors when the window/level changes,
    and is shared by both BaseFusionView and ImageFusionAxialView to avoid code duplication.

    Args:
        view_instance: The fusion view instance (must have .vtk_engine, .overlay_images, .slice_view, .image_display(), .update_view()).

    Returns:
        None
    """
    from src.Model.PatientDictContainer import PatientDictContainer

    if getattr(view_instance, "vtk_engine", None) is not None:
        _extracted_from_update_color_overlay_for_fusion_16(
            view_instance, PatientDictContainer
        )
    else:
        # Only update overlays if not using VTK/manual fusion
        pd = PatientDictContainer()
        view_instance.overlay_images = pd.get(f"color_{view_instance.slice_view}")

    view_instance.image_display()
    # Force a full view update to redraw ROI/cut lines
    view_instance.update_view()


# TODO Rename this here and in `update_color_overlay_for_fusion`
def _extracted_from_update_color_overlay_for_fusion_16(view_instance, PatientDictContainer):
    view_instance.overlay_images = None  # Always clear overlays for VTK/manual fusion
    pd = PatientDictContainer()
    window = pd.get("fusion_window")
    level = pd.get("fusion_level")
    if window is None:
        window = getattr(view_instance.vtk_engine, "window", 400)
    if level is None:
        level = getattr(view_instance.vtk_engine, "level", 40)
    view_instance.vtk_engine.set_window_level(float(window), float(level))