import logging

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
    for elem in ds.iterall():
        if elem.VR == "DS":
            if isinstance(elem.value, (list, tuple)):
                # Truncate each element, ensure it's a string representing a float
                new_vals = []
                for v in elem.value:
                    try:
                        f = float(v)
                        s = f"{f:.10g}"[:16]
                        new_vals.append(s)
                    except (ValueError, TypeError) as e:
                        logging.error(f"Error converting DS list element '{v}' to float: {e}")
                        # If v is a stringified list, split and process each element
                        if isinstance(v, str) and "[" in v and "]" in v:
                            v_clean = v.strip("[] ")
                            for part in v_clean.split(","):
                                if part := part.strip():
                                    try:
                                        f2 = float(part)
                                        s2 = f"{f2:.10g}"[:16]
                                        new_vals.append(s2)
                                    except (ValueError, TypeError) as e2:
                                        logging.error(f"Error converting DS sub-element '{part}' to float: {e2}")
                                        continue
                elem.value = new_vals
            else:
                # Single value: ensure string, truncate, and must be convertible to float
                v = elem.value
                try:
                    f = float(v)
                    s = f"{f:.10g}"[:16]
                    elem.value = s
                except (ValueError, TypeError) as e:
                    logging.error(f"Error converting DS value '{v}' to float: {e}")
                    # If v is a stringified list, split and use first valid float
                    if isinstance(v, str) and "[" in v and "]" in v:
                        v_clean = v.strip("[] ")
                        for part in v_clean.split(","):
                            part = part.strip()
                            if part:
                                try:
                                    f2 = float(part)
                                    s2 = f"{f2:.10g}"[:16]
                                    elem.value = s2
                                    break
                                except (ValueError, TypeError) as e2:
                                    logging.error(f"Error converting DS sub-element '{part}' to float: {e2}")
                                    continue