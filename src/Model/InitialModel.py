import os

import pydicom

from src.Model import ImageLoading
from src.Model.CalculateImages import convert_raw_data, get_pixmaps
from src.Model.GetPatientInfo import get_basic_info, DicomTree, \
    dict_instance_uid
from src.Model.Isodose import get_dose_pixluts, calculate_rx_dose_in_cgray
from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.ROI import ordered_list_rois
from src.Model import ImageLoading
from src.Controller.PathHandler import data_path
from src.constants import CT_RESCALE_INTERCEPT


def create_initial_model():
    """
    This function initializes all the attributes in the PatientDictContainer
    model required for the operation of the main window. This should be
    called before the main window's components are constructed, but after
    the initial values of the PatientDictContainer instance are set (i.e.
    dataset and filepaths).
    """
    ##############################
    #  LOAD PATIENT INFORMATION  #
    ##############################
    patient_dict_container = PatientDictContainer()

    dataset = patient_dict_container.dataset
    filepaths = patient_dict_container.filepaths
    patient_dict_container.set("rtss_modified", False)

    # Determine if dataset is CT for aditional rescaling
    is_ct = False
    if dataset[0].Modality == "CT":
        is_ct = True

    # Determine if dataset is CR for grayscale inverting
    is_cr = False
    if dataset[0].Modality == "CR":
        is_cr = True

    if 'WindowWidth' in dataset[0]:
        if isinstance(dataset[0].WindowWidth, pydicom.valuerep.DSfloat):
            window = int(dataset[0].WindowWidth)
        elif isinstance(dataset[0].WindowWidth, pydicom.multival.MultiValue):
            window = int(dataset[0].WindowWidth[1])
    else:
        window = int(400)

    if 'WindowCenter' in dataset[0]:
        if isinstance(dataset[0].WindowCenter, pydicom.valuerep.DSfloat):
            level = int(dataset[0].WindowCenter) - window/2
        elif isinstance(dataset[0].WindowCenter, pydicom.multival.MultiValue):
            level = int(dataset[0].WindowCenter[1]) - window/2
        if is_ct:
            level += CT_RESCALE_INTERCEPT
    else:
        level = int(800)

    patient_dict_container.set("window", window)
    patient_dict_container.set("level", level)

    # Check to see if the imageWindowing.csv file exists
    if os.path.exists(data_path('imageWindowing.csv')):
        # If it exists, read data from file into the self.dict_windowing
        # variable
        dict_windowing = {}
        with open(data_path('imageWindowing.csv'), "r") \
                as fileInput:
            next(fileInput)
            dict_windowing["Normal"] = [window, level]
            for row in fileInput:
                # Format: Organ - Scan - Window - Level
                items = [item for item in row.split(',')]
                dict_windowing[items[0]] = [int(items[2]), int(items[3])]
    else:
        # If csv does not exist, initialize dictionary with default values
        dict_windowing = {"Normal": [window, level], "Lung": [1600, -300],
                          "Bone": [1400, 700], "Brain": [160, 950],
                          "Soft Tissue": [400, 800],
                          "Head and Neck": [275, 900]}

    patient_dict_container.set("dict_windowing", dict_windowing)

    if not patient_dict_container.has_attribute("scaled"):
        patient_dict_container.set("scaled", True)
        pixel_values = convert_raw_data(dataset, False, is_ct, is_cr)
    else:
        pixel_values = convert_raw_data(dataset, True)

    # Calculate the ratio between x axis and y axis of 3 views
    pixmap_aspect = {}
    pixel_spacing = dataset[0].PixelSpacing
    slice_thickness = dataset[0].SliceThickness
    pixmap_aspect["axial"] = pixel_spacing[1] / pixel_spacing[0]
    pixmap_aspect["sagittal"] = pixel_spacing[1] / slice_thickness
    pixmap_aspect["coronal"] = slice_thickness / pixel_spacing[0]
    pixmaps_axial, pixmaps_coronal, pixmaps_sagittal = \
        get_pixmaps(pixel_values, window, level, pixmap_aspect)

    patient_dict_container.set("pixmaps_axial", pixmaps_axial)
    patient_dict_container.set("pixmaps_coronal", pixmaps_coronal)
    patient_dict_container.set("pixmaps_sagittal", pixmaps_sagittal)
    patient_dict_container.set("pixel_values", pixel_values)
    patient_dict_container.set("pixmap_aspect", pixmap_aspect)

    basic_info = get_basic_info(dataset[0])
    patient_dict_container.set("basic_info", basic_info)

    patient_dict_container.set("dict_uid", dict_instance_uid(dataset))

    # Set RTSS attributes
    patient_dict_container.set("file_rtss", filepaths['rtss'])
    patient_dict_container.set("dataset_rtss", dataset['rtss'])
    dict_raw_contour_data, dict_numpoints = \
        ImageLoading.get_raw_contour_data(dataset['rtss'])
    patient_dict_container.set("raw_contour", dict_raw_contour_data)

    # dict_dicom_tree_rtss will be set in advance if the program
    # generates a new rtss through the execution of
    # ROI.create_initial_rtss_from_ct(...)
    if patient_dict_container.get("dict_dicom_tree_rtss") is None:
        dicom_tree_rtss = DicomTree(filepaths['rtss'])
        patient_dict_container.set("dict_dicom_tree_rtss",
                                   dicom_tree_rtss.dict)

    patient_dict_container.set(
        "list_roi_numbers",
        ordered_list_rois(patient_dict_container.get("rois")))
    patient_dict_container.set("selected_rois", [])

    patient_dict_container.set("dict_polygons_axial", {})
    patient_dict_container.set("dict_polygons_sagittal", {})
    patient_dict_container.set("dict_polygons_coronal", {})

    # Set RTDOSE attributes
    if patient_dict_container.has_modality("rtdose"):
        dicom_tree_rtdose = DicomTree(filepaths['rtdose'])
        patient_dict_container.set("dict_dicom_tree_rtdose",
                                   dicom_tree_rtdose.dict)

        patient_dict_container.set("dose_pixluts", get_dose_pixluts(dataset))

        patient_dict_container.set("selected_doses", [])

        # overwritten if RTPLAN is present.
        patient_dict_container.set("rx_dose_in_cgray", 1)

    # Set RTPLAN attributes
    if patient_dict_container.has_modality("rtplan"):
        # the TargetPrescriptionDose is type 3 (optional), so it may not be
        # there However, it is preferable to the sum of the beam doses
        # DoseReferenceStructureType is type 1 (value is mandatory), but it
        # can have a value of ORGAN_AT_RISK rather than TARGET in which case
        # there will *not* be a TargetPrescriptionDose and even if it is
        # TARGET, that's no guarantee that TargetPrescriptionDose will be
        # encoded and have a value
        rx_dose_in_cgray = calculate_rx_dose_in_cgray(dataset["rtplan"])
        patient_dict_container.set("rx_dose_in_cgray", rx_dose_in_cgray)

        dicom_tree_rtplan = DicomTree(filepaths['rtplan'])
        patient_dict_container.set("dict_dicom_tree_rtplan",
                                   dicom_tree_rtplan.dict)

    # Set SR attributes
    if patient_dict_container.has_modality("sr-cd"):
        dicom_tree_sr_clinical_data = DicomTree(filepaths['sr-cd'])
        patient_dict_container.set("dict_dicom_tree_sr_cd",
                                   dicom_tree_sr_clinical_data.dict)

    if patient_dict_container.has_modality("sr-rad"):
        dicom_tree_sr_pyrad = DicomTree(filepaths['sr-rad'])
        patient_dict_container.set("dict_dicom_tree_sr_pyrad",
                                   dicom_tree_sr_pyrad.dict)


def create_initial_model_batch():
    """
    This function initializes all the attributes in the PatientDictContainer
    required for the operation of batch processing. It is a modified version
    of create_initial_model. This function only sets RTSS values in the
    PatientDictContainer if an RTSS exists. If one does not exist it will only
    be created if needed, whereas the original create_initial_model assumes
    that one is always created. This function also does not set SR attributes
    in the PatientDictContainer, as SRs are only needed for SR2CSV functions,
    which do not require the use of the PatientDictContainer.
    """
    ##############################
    #  LOAD PATIENT INFORMATION  #
    ##############################
    patient_dict_container = PatientDictContainer()

    dataset = patient_dict_container.dataset
    filepaths = patient_dict_container.filepaths
    patient_dict_container.set("rtss_modified", False)

    if 'WindowWidth' in dataset[0]:
        if isinstance(dataset[0].WindowWidth, pydicom.valuerep.DSfloat):
            window = int(dataset[0].WindowWidth)
        elif isinstance(dataset[0].WindowWidth, pydicom.multival.MultiValue):
            window = int(dataset[0].WindowWidth[1])
    else:
        window = int(400)

    if 'WindowCenter' in dataset[0]:
        if isinstance(dataset[0].WindowCenter, pydicom.valuerep.DSfloat):
            level = int(dataset[0].WindowCenter)
        elif isinstance(dataset[0].WindowCenter, pydicom.multival.MultiValue):
            level = int(dataset[0].WindowCenter[1])
    else:
        level = int(800)

    patient_dict_container.set("window", window)
    patient_dict_container.set("level", level)

    # Check to see if the imageWindowing.csv file exists
    if os.path.exists(data_path('imageWindowing.csv')):
        # If it exists, read data from file into the self.dict_windowing
        # variable
        dict_windowing = {}
        with open(data_path('imageWindowing.csv'), "r") \
                as fileInput:
            next(fileInput)
            dict_windowing["Normal"] = [window, level]
            for row in fileInput:
                # Format: Organ - Scan - Window - Level
                items = [item for item in row.split(',')]
                dict_windowing[items[0]] = [int(items[2]), int(items[3])]
    else:
        # If csv does not exist, initialize dictionary with default values
        dict_windowing = {"Normal": [window, level], "Lung": [1600, -300],
                          "Bone": [1400, 700], "Brain": [160, 950],
                          "Soft Tissue": [400, 800],
                          "Head and Neck": [275, 900]}

    patient_dict_container.set("dict_windowing", dict_windowing)

    pixel_values = convert_raw_data(dataset)
    # Calculate the ratio between x axis and y axis of 3 views
    pixmap_aspect = {}
    pixel_spacing = dataset[0].PixelSpacing
    slice_thickness = dataset[0].SliceThickness
    pixmap_aspect["axial"] = pixel_spacing[1] / pixel_spacing[0]
    pixmap_aspect["sagittal"] = pixel_spacing[1] / slice_thickness
    pixmap_aspect["coronal"] = slice_thickness / pixel_spacing[0]
    pixmaps_axial, pixmaps_coronal, pixmaps_sagittal = \
        get_pixmaps(pixel_values, window, level, pixmap_aspect)

    patient_dict_container.set("pixmaps_axial", pixmaps_axial)
    patient_dict_container.set("pixmaps_coronal", pixmaps_coronal)
    patient_dict_container.set("pixmaps_sagittal", pixmaps_sagittal)
    patient_dict_container.set("pixel_values", pixel_values)
    patient_dict_container.set("pixmap_aspect", pixmap_aspect)

    basic_info = get_basic_info(dataset[0])
    patient_dict_container.set("basic_info", basic_info)

    patient_dict_container.set("dict_uid", dict_instance_uid(dataset))

    # Set RTSS attributes
    if patient_dict_container.has_modality("rtss"):
        patient_dict_container.set("file_rtss", filepaths['rtss'])
        patient_dict_container.set("dataset_rtss", dataset['rtss'])
        dict_raw_contour_data, dict_numpoints = \
            ImageLoading.get_raw_contour_data(dataset['rtss'])
        patient_dict_container.set("raw_contour", dict_raw_contour_data)
        dicom_tree_rtss = DicomTree(filepaths['rtss'])
        patient_dict_container.set("dict_dicom_tree_rtss",
                                   dicom_tree_rtss.dict)

        patient_dict_container.set(
            "list_roi_numbers",
            ordered_list_rois(patient_dict_container.get("rois")))
        patient_dict_container.set("selected_rois", [])

        patient_dict_container.set("dict_polygons_axial", {})
        patient_dict_container.set("dict_polygons_sagittal", {})
        patient_dict_container.set("dict_polygons_coronal", {})

    # Set RTDOSE attributes
    if patient_dict_container.has_modality("rtdose"):
        dicom_tree_rtdose = DicomTree(filepaths['rtdose'])
        patient_dict_container.set("dict_dicom_tree_rtdose",
                                   dicom_tree_rtdose.dict)

        patient_dict_container.set("dose_pixluts", get_dose_pixluts(dataset))

        patient_dict_container.set("selected_doses", [])

        # overwritten if RTPLAN is present.
        patient_dict_container.set("rx_dose_in_cgray", 1)

    # Set RTPLAN attributes
    if patient_dict_container.has_modality("rtplan"):
        # the TargetPrescriptionDose is type 3 (optional), so it may not be
        # there However, it is preferable to the sum of the beam doses
        # DoseReferenceStructureType is type 1 (value is mandatory), but it
        # can have a value of ORGAN_AT_RISK rather than TARGET in which case
        # there will *not* be a TargetPrescriptionDose and even if it is
        # TARGET, that's no guarantee that TargetPrescriptionDose will be
        # encoded and have a value
        rx_dose_in_cgray = calculate_rx_dose_in_cgray(dataset["rtplan"])
        patient_dict_container.set("rx_dose_in_cgray", rx_dose_in_cgray)

        dicom_tree_rtplan = DicomTree(filepaths['rtplan'])
        patient_dict_container.set("dict_dicom_tree_rtplan",
                                   dicom_tree_rtplan.dict)
