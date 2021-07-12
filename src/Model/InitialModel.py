import os

import pydicom

from src.Model.CalculateImages import convert_raw_data, get_pixmaps
from src.Model.GetPatientInfo import get_basic_info, DicomTree, dict_instanceUID
from src.Model.Isodose import get_dose_pixluts, calculate_rx_dose_in_cgray
from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.ROI import ordered_list_rois
from src.Controller.PathHandler import resource_path


def create_initial_model():
    """
    This function initializes all the attributes in the PatientDictContainer model required for the operation of the
    main window. This should be called before the main window's components are constructed, but after the initial
    values of the PatientDictContainer instance are set (i.e. dataset and filepaths).
    """
    ##############################
    #  LOAD PATIENT INFORMATION  #
    ##############################
    patient_dict_container = PatientDictContainer()

    dataset = patient_dict_container.dataset
    filepaths = patient_dict_container.filepaths
    patient_dict_container.set("rtss_modified", False)

    if ('WindowWidth' in dataset[0]):
        if isinstance(dataset[0].WindowWidth, pydicom.valuerep.DSfloat):
            window = int(dataset[0].WindowWidth)
        elif isinstance(dataset[0].WindowWidth, pydicom.multival.MultiValue):
            window = int(dataset[0].WindowWidth[1])
    else:
        window = int(400)

    if ('WindowCenter' in dataset[0]):
        if isinstance(dataset[0].WindowCenter, pydicom.valuerep.DSfloat):
            level = int(dataset[0].WindowCenter)
        elif isinstance(dataset[0].WindowCenter, pydicom.multival.MultiValue):
            level = int(dataset[0].WindowCenter[1])
    else:
        level = int(800)

    patient_dict_container.set("window", window)
    patient_dict_container.set("level", level)

    # Check to see if the imageWindowing.csv file exists
    if os.path.exists(resource_path('data/csv/imageWindowing.csv')):
        # If it exists, read data from file into the self.dict_windowing variable
        dict_windowing = {}
        with open(resource_path('data/csv/imageWindowing.csv'), "r") as fileInput:
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
                          "Soft Tissue": [400, 800], "Head and Neck": [275, 900]}

    patient_dict_container.set("dict_windowing", dict_windowing)

    pixel_values = convert_raw_data(dataset)
    # Calculate the ratio between x axis and y axis of 3 views
    aspect = {}
    pixel_spacing = dataset[0].PixelSpacing
    slice_thickness = dataset[0].SliceThickness
    aspect["axial"] = pixel_spacing[1] / pixel_spacing[0]
    aspect["sagittal"] = pixel_spacing[1] / slice_thickness
    aspect["coronal"] = slice_thickness / pixel_spacing[0]
    pixmaps_axial, pixmaps_coronal, pixmaps_sagittal = get_pixmaps(pixel_values, window, level, aspect)

    patient_dict_container.set("pixmaps_axial", pixmaps_axial)
    patient_dict_container.set("pixmaps_coronal", pixmaps_coronal)
    patient_dict_container.set("pixmaps_sagittal", pixmaps_sagittal)
    patient_dict_container.set("pixmaps", pixmaps_coronal)
    patient_dict_container.set("pixel_values", pixel_values)
    patient_dict_container.set("aspect", aspect)

    basic_info = get_basic_info(dataset[0])
    patient_dict_container.set("basic_info", basic_info)

    patient_dict_container.set("dict_uid", dict_instanceUID(dataset))

    # Set RTSS attributes
    if patient_dict_container.has_modality("rtss"):
        patient_dict_container.set("file_rtss", filepaths['rtss'])
        patient_dict_container.set("dataset_rtss", dataset['rtss'])

        dicom_tree_rtss = DicomTree(filepaths['rtss'])
        patient_dict_container.set("dict_dicom_tree_rtss", dicom_tree_rtss.dict)

        patient_dict_container.set("list_roi_numbers", ordered_list_rois(patient_dict_container.get("rois")))
        patient_dict_container.set("selected_rois", [])

        patient_dict_container.set("dict_polygons", {})

    # Set RTDOSE attributes
    if patient_dict_container.has_modality("rtdose"):
        dicom_tree_rtdose = DicomTree(filepaths['rtdose'])
        patient_dict_container.set("dict_dicom_tree_rtdose", dicom_tree_rtdose.dict)

        patient_dict_container.set("dose_pixluts", get_dose_pixluts(dataset))

        patient_dict_container.set("selected_doses", [])
        patient_dict_container.set("rx_dose_in_cgray", 1)  # This will be overwritten if an RTPLAN is present.

    # Set RTPLAN attributes
    if patient_dict_container.has_modality("rtplan"):
        # the TargetPrescriptionDose is type 3 (optional), so it may not be there
        # However, it is preferable to the sum of the beam doses
        # DoseReferenceStructureType is type 1 (value is mandatory),
        # but it can have a value of ORGAN_AT_RISK rather than TARGET
        # in which case there will *not* be a TargetPrescriptionDose
        # and even if it is TARGET, that's no guarantee that TargetPrescriptionDose
        # will be encoded and have a value
        rx_dose_in_cgray = calculate_rx_dose_in_cgray(dataset["rtplan"])
        patient_dict_container.set("rx_dose_in_cgray", rx_dose_in_cgray)

        dicom_tree_rtplan = DicomTree(filepaths['rtplan'])
        patient_dict_container.set("dict_dicom_tree_rtplan", dicom_tree_rtplan.dict)
