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