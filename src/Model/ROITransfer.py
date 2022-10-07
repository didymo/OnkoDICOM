import SimpleITK as sitk
from pathlib import Path

import pydicom
import numpy as np
import SimpleITK as sitk

import logging
from platipy.dicom.io.rtstruct_to_nifti import fix_missing_data
from skimage.draw import polygon

from src.View.util.ProgressWindowHelper import check_interrupt_flag


def transform_point_set_from_dicom_struct(dicom_image, dicom_struct,
                                          struct_name_sequence,
                                          spacing_override=None,
                                          interrupt_flag=None):
    """Converts a set of points from a DICOM RTSTRUCT into a mask array.
    This function is modified from the function
    platipy.dicom.io.transform_point_set_from_dicom_struct to align with
    the specific usage of OnkoDICOM.

    Args:
        dicom_image (sitk.Image): The reference image
        dicom_struct (pydicom.Dataset): The DICOM RTSTRUCT
        struct_name_sequence: the name of ROIs to be transformed
        spacing_override (list): The spacing to override. Defaults to None
        interrupt_flag: interrupt flag to stop the process
    Returns:
        tuple: Returns a list of masks and a list of structure names

    """
    if spacing_override:
        current_spacing = list(dicom_image.GetSpacing())
        new_spacing = tuple(
            [
                current_spacing[k] if spacing_override[k] == 0 else
                spacing_override[k]
                for k in range(3)
            ]
        )
        dicom_image.SetSpacing(new_spacing)

    struct_point_sequence = dicom_struct.ROIContourSequence
    all_name_sequence = [
        "_".join(i.ROIName.split()) for i in
        dicom_struct.StructureSetROISequence
    ]
    # find corresponding rois in roi contour sequence
    roi_indexes = {}
    for index, roi_name in enumerate(all_name_sequence):
        if roi_name in struct_name_sequence:
            roi_indexes[roi_name] = index

    struct_list = []
    final_struct_name_sequence = []

    for struct_name in roi_indexes.keys():
        if interrupt_flag is not None and \
                not check_interrupt_flag(interrupt_flag):
            return [], []

        struct_index = roi_indexes[struct_name]
        image_blank = np.zeros(dicom_image.GetSize()[::-1], dtype=np.uint8)
        logging.debug(
            "Converting structure {0} with name: {1}".format(struct_index,
                                                             struct_name))

        if not hasattr(struct_point_sequence[struct_index], "ContourSequence"):
            logging.debug(
                "No contour sequence found for this structure, skipping.")
            continue

        if len(struct_point_sequence[struct_index].ContourSequence) == 0:
            logging.debug(
                "Contour sequence empty for this structure, skipping.")
            continue

        if len(struct_point_sequence[struct_index].ContourSequence) == 0:
            logging.debug(
                "Contour sequence empty for this structure, skipping.")
            continue

        for sl in range(
                len(struct_point_sequence[struct_index].ContourSequence)):

            if interrupt_flag is not None and \
                    not check_interrupt_flag(interrupt_flag):
                return [], []

            contour_data = fix_missing_data(
                struct_point_sequence[struct_index].ContourSequence[
                    sl].ContourData
            )

            struct_slice_contour_data = np.array(contour_data, dtype=np.double)
            vertex_arr_physical = struct_slice_contour_data.reshape(
                struct_slice_contour_data.shape[0] // 3, 3
            )

            point_arr = np.array(
                [dicom_image.TransformPhysicalPointToIndex(i) for i in
                 vertex_arr_physical]
            ).T

            [x_vertex_arr_image, y_vertex_arr_image] = point_arr[[0, 1]]
            z_index = point_arr[2][0]
            if np.any(point_arr[2] != z_index):
                logging.debug(
                    "Error: axial slice index varies in contour. Quitting now.")
                logging.debug("Structure:   {0}".format(struct_name))
                logging.debug("Slice index: {0}".format(z_index))
                quit()

            if z_index >= dicom_image.GetSize()[2]:
                logging.debug(
                    "Warning: Slice index greater than image size. Skipping "
                    "slice.")
                logging.debug("Structure:   {0}".format(struct_name))
                logging.debug("Slice index: {0}".format(z_index))
                continue

            slice_arr = np.zeros(image_blank.shape[-2:], dtype=np.uint8)

            filled_indices_x, filled_indices_y = polygon(
                x_vertex_arr_image, y_vertex_arr_image, shape=slice_arr.shape
            )
            slice_arr[filled_indices_y, filled_indices_x] = 1

            image_blank[z_index] += slice_arr

        struct_image = sitk.GetImageFromArray(1 * (image_blank > 0))
        struct_image.CopyInformation(dicom_image)
        struct_list.append(sitk.Cast(struct_image, sitk.sitkUInt8))
        final_struct_name_sequence.append(struct_name)

    return struct_list, final_struct_name_sequence
