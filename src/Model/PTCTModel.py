import os
import SimpleITK as sitk
import pydicom

from src.constants import CT_RESCALE_INTERCEPT

from src.Model.CalculateImages import convert_raw_data, get_pixmaps
from src.Model.GetPatientInfo import get_basic_info, DicomTree, \
    dict_instance_uid
from src.Model.Isodose import get_dose_pixluts, calculate_rx_dose_in_cgray

from src.Model.PTCTDictContainer import PTCTDictContainer

from src.Model.ROI import ordered_list_rois
from src.Controller.PathHandler import resource_path


def create_pt_ct_model():
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
    pt_ct_dict_container = PTCTDictContainer()

    pt_dataset = pt_ct_dict_container.pt_dataset
    ct_dataset = pt_ct_dict_container.ct_dataset

    # Set up PT images
    if 'WindowWidth' in pt_dataset[0]:
        if isinstance(pt_dataset[0].WindowWidth, pydicom.valuerep.DSfloat):
            window = int(pt_dataset[0].WindowWidth)
        elif isinstance(pt_dataset[0].WindowWidth,
                        pydicom.multival.MultiValue):
            window = int(pt_dataset[0].WindowWidth[1])
    else:
        window = int(400)

    if 'WindowCenter' in pt_dataset[0]:
        if isinstance(pt_dataset[0].WindowCenter, pydicom.valuerep.DSfloat):
            level = int(pt_dataset[0].WindowCenter) - window/2
        elif isinstance(pt_dataset[0].WindowCenter,
                        pydicom.multival.MultiValue):
            level = int(pt_dataset[0].WindowCenter[1]) - window/2
    else:
        level = int(800)

    pt_ct_dict_container.set("pt_window", window)
    pt_ct_dict_container.set("pt_level", level)

    if not pt_ct_dict_container.has_attribute("pt_scaled"):
        pt_ct_dict_container.set("pt_scaled", True)
        pt_pixel_values = convert_raw_data(pt_dataset, False, False)
    else:
        pt_pixel_values = convert_raw_data(pt_dataset, True)

    # Calculate the ratio between x axis and y axis of 3 views
    pt_pixmap_aspect = {}
    pt_pixel_spacing = pt_dataset[0].PixelSpacing
    pt_slice_thickness = pt_dataset[0].SliceThickness
    pt_pixmap_aspect["axial"] = pt_pixel_spacing[1] / pt_pixel_spacing[0]
    pt_pixmap_aspect["sagittal"] = pt_pixel_spacing[1] / pt_slice_thickness
    pt_pixmap_aspect["coronal"] = pt_slice_thickness / pt_pixel_spacing[0]
    
    # Pass in "heat" into the get_pixmaps function to produce
    # a heatmap for the given images.
    pt_pixmaps_axial, pt_pixmaps_coronal, pt_pixmaps_sagittal = \
        get_pixmaps(pt_pixel_values, window, level, pt_pixmap_aspect,
                    fusion=True, color="Heat")

    pt_ct_dict_container.set("pt_pixmaps_axial", pt_pixmaps_axial)
    pt_ct_dict_container.set("pt_pixmaps_coronal", pt_pixmaps_coronal)
    pt_ct_dict_container.set("pt_pixmaps_sagittal", pt_pixmaps_sagittal)
    pt_ct_dict_container.set("pt_pixel_values", pt_pixel_values)
    pt_ct_dict_container.set("pt_pixmap_aspect", pt_pixmap_aspect)

    basic_info = get_basic_info(pt_dataset[0])
    pt_ct_dict_container.set("pt_basic_info", basic_info)
    pt_ct_dict_container.set("pt_dict_uid", dict_instance_uid(pt_dataset))

    # Set up CT images
    if 'WindowWidth' in ct_dataset[0]:
        if isinstance(ct_dataset[0].WindowWidth, pydicom.valuerep.DSfloat):
            window = int(ct_dataset[0].WindowWidth)
        elif isinstance(ct_dataset[0].WindowWidth,
                        pydicom.multival.MultiValue):
            window = int(ct_dataset[0].WindowWidth[1])
    else:
        window = int(400)

    if 'WindowCenter' in ct_dataset[0]:
        if isinstance(ct_dataset[0].WindowCenter, pydicom.valuerep.DSfloat):
            level = int(ct_dataset[0].WindowCenter) - window / 2
        elif isinstance(ct_dataset[0].WindowCenter,
                        pydicom.multival.MultiValue):
            level = int(ct_dataset[0].WindowCenter[1]) - window / 2
        level += CT_RESCALE_INTERCEPT
    else:
        level = int(800)

    pt_ct_dict_container.set("ct_window", window)
    pt_ct_dict_container.set("ct_level", level)

    if not pt_ct_dict_container.has_attribute("ct_scaled"):
        pt_ct_dict_container.set("ct_scaled", True)
        ct_pixel_values = convert_raw_data(ct_dataset, False, True)
    else:
        ct_pixel_values = convert_raw_data(ct_dataset, True)

    # Calculate the ratio between x axis and y axis of 3 views
    ct_pixmap_aspect = {}
    ct_pixel_spacing = ct_dataset[0].PixelSpacing
    ct_slice_thickness = ct_dataset[0].SliceThickness
    ct_pixmap_aspect["axial"] = ct_pixel_spacing[1] / ct_pixel_spacing[0]
    ct_pixmap_aspect["sagittal"] = ct_pixel_spacing[1] / ct_slice_thickness
    ct_pixmap_aspect["coronal"] = ct_slice_thickness / ct_pixel_spacing[0]
    ct_pixmaps_axial, ct_pixmaps_coronal, ct_pixmaps_sagittal = \
        get_pixmaps(ct_pixel_values, window, level, ct_pixmap_aspect,
                    fusion=True)

    pt_ct_dict_container.set("ct_pixmaps_axial", ct_pixmaps_axial)
    pt_ct_dict_container.set("ct_pixmaps_coronal", ct_pixmaps_coronal)
    pt_ct_dict_container.set("ct_pixmaps_sagittal", ct_pixmaps_sagittal)
    pt_ct_dict_container.set("ct_pixel_values", ct_pixel_values)
    pt_ct_dict_container.set("ct_pixmap_aspect", ct_pixmap_aspect)

    basic_info = get_basic_info(ct_dataset[0])
    pt_ct_dict_container.set("ct_basic_info", basic_info)
    pt_ct_dict_container.set("ct_dict_uid", dict_instance_uid(ct_dataset))
