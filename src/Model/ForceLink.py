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
    logging.debug("Force link initiated")
    dicom = []
    files = []
    series = {
        "RTSTRUCT": None,
        "RTPLAN": None,
        "RTDOSE": None,
        "SR": None
    }
    StructSOP = ""
    PlanSOP = ""
    DoseSOP = ""
    ImageUID = ""

    # exit the function if the number of files is less than 2
    try:
        if len(dicom_array_in) < 2:
            logging.debug("Force link aborted, Not enough dicom files selected")
            return -1
    except TypeError:
        logging.debug("Force link aborted, Not enough dicom files selected")
        return -1

    # get a list of dicom files in the desired directory
    try:
        directory = os.listdir(file_path)
    except FileNotFoundError:
        logging.debug("Force link aborted, file not found")
        return -1
    except TypeError:
        logging.debug("Force link aborted, file input invalid")
        return -1
    except NotADirectoryError:
        logging.debug("Force link aborted, file input invalid")
        return -1
    for file in directory:
        if file.endswith(".dcm"):
            files.append(os.path.join(file_path, file))
            dicom.append(pydicom.dcmread(os.path.join(file_path, file)))

    # get the 'true' ID of the DICOM series.
    new_id = ""
    new_study_id = ""
    for dicom_file in dicom:
        if (
            (dicom_file.FrameOfReferenceUID == frame_overwrite)
            and
            (dicom_file.SOPClassUID == src.dicom_constants.CT_IMAGE
            or
            dicom_file.SOPClassUID == src.dicom_constants.MR_IMAGE)
            ):

            new_id = dicom_file.FrameOfReferenceUID
            new_study_id = dicom_file.StudyInstanceUID
            break
    logging.debug("Force link forced study instance ID = " + new_id)
    if new_id == "" or new_study_id == "":
        logging.debug("Force link forced ID not assigned, process aborted")
        return -1
    image_ids = []
    for series_object in dicom_array_in:
        if series_object.get_series_type() in series:
            if series_object.get_series_type() == "RTSTRUCT":
                StructSOP = series_object.get_instance_uid()
            elif series_object.get_series_type() == "RTPLAN":
                PlanSOP = series_object.get_instance_uid()
            elif series_object.get_series_type() == "RTDOSE":
                DoseSOP = series_object.get_instance_uid()

            image_ids.append(series_object.get_instance_uid())
        elif series_object.get_series_type() == "IMAGE":
            ImageUID = series_object.series_uid()
    index = 0

    for dicom_object in dicom:
        for image_id in image_ids:
            if dicom_object.SOPInstanceUID == image_id:
                temporary_dicom = dicom_object
                try:
                    temporary_dicom[(0X0020, 0X0052)].value = new_id
                except KeyError:
                    element = pydicom.DataElement((0x0020, 0x0052), "UI", new_id)
                    temporary_dicom.add(element)

                try:
                    temporary_dicom[(0X0020, 0X00D)].value = new_study_id
                except KeyError:
                    element = pydicom.DataElement((0X0020, 0X00D), "UI", new_study_id)
                    temporary_dicom.add(element)

                try:
                    temporary_dicom[(0x300C, 0x0060)][0][(0x0008, 0x1155)].value = StructSOP
                    logging.debug("Force link, reference to RTSTRUCT overwritten")
                except KeyError:
                    if temporary_dicom.SOPClassUID != "1.2.840.10008.5.1.4.1.1.481.3":
                        element1 = pydicom.DataElement((0x0008, 0x1155), "UI" , StructSOP)
                        data = pydicom.Dataset()
                        data.add(element1)
                        data = [data]
                        element2 = pydicom.DataElement((0x300C, 0x0060), "SQ", data)
                        temporary_dicom.add(element2)


                try:
                    temporary_dicom[(0x300C, 0x0002)][0][(0x0008, 0x1155)].value = PlanSOP
                    logging.debug("Force link, reference to RTPLAN overwritten")
                except KeyError:
                    if temporary_dicom.SOPClassUID != "1.2.840.10008.5.1.4.1.1.481.5":
                        element1 = pydicom.DataElement((0x0008, 0x1155), "UI", StructSOP)
                        data = pydicom.Dataset()
                        data.add(element1)
                        data = [data]
                        element2 = pydicom.DataElement((0x300C, 0x0002), "SQ", data)
                        temporary_dicom.add(element2)

                try:
                    temporary_dicom[(0x300C, 0x0080)][0][(0x0008, 0x1155)].value = DoseSOP
                    logging.debug("Force link, reference to RTDOSE overwritten")
                except KeyError:
                    pass


                path = files[index]
                temporary_dicom.save_as(path)
                logging.debug("DICOM updated at" + path)
                break
        index = index + 1
    logging.debug("Force link completed successfully")
    return 1
