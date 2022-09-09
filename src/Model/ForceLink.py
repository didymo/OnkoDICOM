"""
A File only used for clinical edge cases in which the RTDOSE and RTPlan
do not reference the correct RTSTRUCT.
This file will not force a link between IMAGE series and RTSTRUCT

"""

import os
import pydicom
import src.dicom_constants
import logging


def force_link(frame_overwrite, file_path, dicom_array_in):
    """This function takes a frame of reference identifier, a file path and an
    array of dicom ONKO DICOM widget items. This function will return 1 if the
    Link has been forced, and will return -1 if the link cannot be forced for
    any reason."""
    logging.info("Force link initiated")
    dicom = []
    files = []
    series = {
        "RTPLAN": None,
        "RTDOSE": None,
        "SR": None
    }
    # exit the function if the number of files is less than 2
    try:
        if len(dicom_array_in) < 2:
            logging.info("Force link aborted, Not enough dicom files selected")
            return -1
    except TypeError:
        logging.info("Force link aborted, Not enough dicom files selected")
        return -1

    # get a list of dicom files in the desired directory
    try:
        directory = os.listdir(file_path)
    except FileNotFoundError:
        logging.info("Force link aborted, file not found")
        return -1
    except TypeError:
        logging.info("Force link aborted, file input invalid")
        return -1
    for file in directory:
        if file.endswith(".dcm"):
            files.append(os.path.join(file_path, file))
            dicom.append(pydicom.dcmread(os.path.join(file_path, file)))

    # get the 'true' ID of the DICOM series.
    new_id = ""

    for dicom_file in dicom:
        if dicom_file[(0x20, 0x52)].value == frame_overwrite and \
                dicom_file.SOPClassUID == src.dicom_constants.CT_IMAGE:
            new_id = dicom_file.StudyInstanceUID
            break
    logging.debug("Force link forced ID = " + new_id)
    if new_id == "":
        logging.info("Force link forced ID not assigned, process aborted")
        return -1

    image_ids = []
    for series_object in dicom_array_in:
        if series_object.get_series_type() in series:
            image_ids.append(series_object.get_instance_uid())
    index = 0
    for dicom_object in dicom:
        for image_id in image_ids:
            if dicom_object.SOPInstanceUID == image_id:
                temporary_dicom = dicom_object
                temporary_dicom[(0x0020, 0x000D)].value = new_id
                path = files[index]
                temporary_dicom.save_as(path)
                logging.debug("DICOM updated at" + path)
                break
        index = index + 1
    logging.info("Force link completed successfully")
    return 1
