

def truncate_ds_fields(dicom_dataset):
    """Truncates the values of all DICOM elements with VR 'DS' to a maximum of 16 characters.

    This function is called whenever a DICOM dataset is being saved, especially for RTSTRUCT and Spatial Registration (SRO) objects.
    It ensures that all 'DS' fields conform to the DICOM standard's length restrictions, preventing save errors and improving compatibility.

    Args:
        dicom_dataset: A pydicom Dataset whose 'DS' fields will be truncated.
    """
    for element in dicom_dataset.iterall():
        if element.VR == "DS":
            if isinstance(element.value, (list, tuple)):
                # Truncate each element, ensure it's a string representing a float
                truncated_values = []
                for value in element.value:
                    try:
                        float_value = float(value)
                        truncated_str = f"{float_value:.10g}"[:16]
                        truncated_values.append(truncated_str)
                    except Exception:
                        # If value is a stringified list, split and process each element
                        if isinstance(value, str) and "[" in value and "]" in value:
                            cleaned_value = value.strip("[] ")
                            for part in cleaned_value.split(","):
                                part = part.strip()
                                if part:
                                    try:
                                        float_part = float(part)
                                        truncated_part = f"{float_part:.10g}"[:16]
                                        truncated_values.append(truncated_part)
                                    except Exception:
                                        continue
                        else:
                            continue
                element.value = truncated_values
            else:
                # Single value: ensure string, truncate, and must be convertible to float
                single_value = element.value
                try:
                    float_value = float(single_value)
                    truncated_str = f"{float_value:.10g}"[:16]
                    element.value = truncated_str
                except Exception:
                    # If single_value is a stringified list, split and use first valid float
                    if isinstance(single_value, str) and "[" in single_value and "]" in single_value:
                        cleaned_value = single_value.strip("[] ")
                        for part in cleaned_value.split(","):
                            part = part.strip()
                            if part:
                                try:
                                    float_part = float(part)
                                    truncated_part = f"{float_part:.10g}"[:16]
                                    element.value = truncated_part
                                    break
                                except Exception:
                                    continue
                    else:
                        continue