import os
import SimpleITK as sitk
import pydicom

from src.constants import CT_RESCALE_INTERCEPT

from src.Model.CalculateImages import convert_raw_data, get_pixmaps
from src.Model.GetPatientInfo import get_basic_info, DicomTree, \
    dict_instance_uid
from src.Model.Isodose import get_dose_pixluts, calculate_rx_dose_in_cgray

from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.MovingDictContainer import MovingDictContainer

from src.Model.ROI import ordered_list_rois
from src.Controller.PathHandler import resource_path

from src.Model.ImageFusion import create_fused_model, get_fused_window


def create_moving_model():
    """
    This function initializes all the attributes in the 
    MovingDictContainer model required for the operation of the main
    window. This should be called before the 
    main window's components are constructed, but after the initial
    values of the MovingDictContainer instance are set (i.e. dataset 
    and filepaths).
    """
    ##############################
    #  LOAD PATIENT INFORMATION  #
    ##############################
    moving_dict_container = MovingDictContainer()

    dataset = moving_dict_container.dataset
    filepaths = moving_dict_container.filepaths
    moving_dict_container.set("rtss_modified_moving", False)

    # Determine if dataset is CT for aditional rescaling
    is_ct = False
    if dataset[0].Modality == "CT":
        is_ct = True

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

    moving_dict_container.set("window", window)
    moving_dict_container.set("level", level)

    # Check to see if the imageWindowing.csv file exists
    if os.path.exists(resource_path('data/csv/imageWindowing.csv')):
        # If it exists, read data from file into the self.dict_windowing
        # variable
        dict_windowing = {}
        with open(resource_path('data/csv/imageWindowing.csv'), "r") \
                as fileInput:
            next(fileInput)
            dict_windowing["Normal"] = [window, level]
            for row in fileInput:
                # Format: Organ - Scan - Window - Level
                items = [item for item in row.split(',')]
                dict_windowing[items[0]] = [int(items[2]), int(items[3])]
    else:
        # If csv does not exist, initialize dictionary with default
        # values
        dict_windowing = {"Normal": [window, level], "Lung": [1600, -300],
                          "Bone": [1400, 700], "Brain": [160, 950],
                          "Soft Tissue": [400, 800],
                          "Head and Neck": [275, 900]}

    moving_dict_container.set("dict_windowing_moving", dict_windowing)

    if not moving_dict_container.has_attribute("scaled"):
        moving_dict_container.set("scaled", True)
        pixel_values = convert_raw_data(dataset, False, is_ct)
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

    moving_dict_container.set("pixmaps_axial", pixmaps_axial)
    moving_dict_container.set("pixmaps_coronal", pixmaps_coronal)
    moving_dict_container.set("pixmaps_sagittal", pixmaps_sagittal)
    moving_dict_container.set("pixel_values", pixel_values)
    moving_dict_container.set("pixmap_aspect", pixmap_aspect)

    basic_info = get_basic_info(dataset[0])
    moving_dict_container.set("basic_info", basic_info)

    moving_dict_container.set("dict_uid", dict_instance_uid(dataset))

    # Set RTSS attributes
    if moving_dict_container.has_modality("rtss"):
        moving_dict_container.set("file_rtss", filepaths['rtss'])
        moving_dict_container.set("dataset_rtss", dataset['rtss'])

        dicom_tree_rtss = DicomTree(filepaths['rtss'])
        moving_dict_container.set("dict_dicom_tree_rtss", dicom_tree_rtss.dict)

        moving_dict_container.set("list_roi_numbers", ordered_list_rois(
            moving_dict_container.get("rois")))
        moving_dict_container.set("selected_rois", [])

        moving_dict_container.set("dict_polygons", {})

    # Set RTDOSE attributes
    if moving_dict_container.has_modality("rtdose"):
        dicom_tree_rtdose = DicomTree(filepaths['rtdose'])
        moving_dict_container.set(
            "dict_dicom_tree_rtdose", dicom_tree_rtdose.dict)

        moving_dict_container.set("dose_pixluts", get_dose_pixluts(dataset))

        moving_dict_container.set("selected_doses", [])
        # This will be overwritten if an RTPLAN is present.
        moving_dict_container.set("rx_dose_in_cgray", 1)

    # Set RTPLAN attributes
    if moving_dict_container.has_modality("rtplan"):
        rx_dose_in_cgray = calculate_rx_dose_in_cgray(dataset["rtplan"])
        moving_dict_container.set("rx_dose_in_cgray", rx_dose_in_cgray)

        dicom_tree_rtplan = DicomTree(filepaths['rtplan'])
        moving_dict_container.set("dict_dicom_tree_rtplan",
                                  dicom_tree_rtplan.dict)


def read_images_for_fusion(level=0, window=0):
    """
    Performs initial image fusion, this is by converting the old and
    new images for transformations, then creating the fusion object,
    then using the fusion object to generate a comparison color map and
    storing the color map
    :param level: the level (midpoint) of windowing
    :param window: the window (range) of windowing
    """
    patient_dict_container = PatientDictContainer()
    moving_dict_container = MovingDictContainer()
    if level == 0 or window == 0:
        level = patient_dict_container.get("level")
        window = patient_dict_container.get("window")

    amount = len(patient_dict_container.filepaths)
    orig_fusion_list = []

    for i in range(amount):
        try:
            orig_fusion_list.append(patient_dict_container.filepaths[i])
        except KeyError:
            continue

    orig_image = sitk.ReadImage(orig_fusion_list)
    patient_dict_container.set("sitk_original", orig_image)

    amount = len(moving_dict_container.filepaths)
    new_fusion_list = []

    for i in range(amount):
        try:
            new_fusion_list.append(moving_dict_container.filepaths[i])
        except KeyError:
            continue

    new_image = sitk.ReadImage(new_fusion_list)
    moving_dict_container.set("sitk_moving", new_image)

    #create_fused_model(orig_image, new_image)
    #color_axial, color_sagittal, color_coronal = \
    #    get_fused_window(level, window)

    #patient_dict_container.set("color_axial", color_axial)
    #patient_dict_container.set("color_sagittal", color_sagittal)
    #patient_dict_container.set("color_coronal", color_coronal)
