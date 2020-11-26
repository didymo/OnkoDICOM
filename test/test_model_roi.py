"""
Created on Thu Dec  5 05:25:04 2019

@author: sjswerdloff
"""

import numpy as np
from pydicom import dataset
from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.ROI import add_to_roi, calculate_matrix, create_roi


def test_calculate_matrix():
    image_ds = dataset.Dataset()
    image_ds.PixelSpacing = [1, 1]
    image_ds.ImageOrientationPatient = [1, 0, 0, 0, 1, 0]
    image_ds.ImagePositionPatient = [0, 0, 0]
    image_ds.Rows = 4
    image_ds.Columns = 4
    array_x, array_y = calculate_matrix(image_ds)
    assert np.all(array_x == np.array([0, 1, 2, 3]))
    assert np.all(array_y == np.array([0, 1, 2, 3]))


def test_add_to_roi():
    rt_ss = dataset.Dataset()

    rt_ss.StructureSetROISequence = []
    rt_ss.StructureSetROISequence.append(dataset.Dataset())
    rt_ss.StructureSetROISequence[0].ReferencedFrameOfReferenceUID = "1.2.3"
    rt_ss.StructureSetROISequence[0].ROINumber = "1"
    rt_ss.StructureSetROISequence[0].ROIName = "NewTestROI"

    rt_ss.ROIContourSequence = []

    rt_ss.RTROIObservationsSequence = []

    roi_name = "NewTestROI"
    roi_coordinates = [0, 0, 0, 0, 1, 0, 1, 0, 0]  # a right triangle
    image_ds = dataset.Dataset()
    image_ds.SOPClassUID = "1.2.840.10008.5.1.4.1.1.2"
    image_ds.SOPInstanceUID = "1.2.3.4.5.6.7.8.9"
    patient_dict_container = PatientDictContainer()
    # container has to be initialised with kwargs content for the get/set to not fail for lack of an
    # "additional_parameters" dict.
    patient_dict_container.set_initial_values(None, None, None, blah="blah", rois={})
    if patient_dict_container.get("rois") is not None:
        print("rois are present in patient dict container")
    updated_rtss = create_roi(rt_ss, roi_name, roi_coordinates, image_ds)
    # clearly the above is an opportunity to factor out to a fixture or similar
    rtss_with_added_roi = add_to_roi(updated_rtss, roi_name, roi_coordinates, image_ds)
    assert (
        rtss_with_added_roi.ROIContourSequence[0]
        .ContourSequence[1]
        .ContourImageSequence[0]
        .ReferencedSOPClassUID
        == image_ds.SOPClassUID
    )


def test_create_roi():
    rt_ss = dataset.Dataset()

    rt_ss.StructureSetROISequence = []
    rt_ss.StructureSetROISequence.append(dataset.Dataset())
    rt_ss.StructureSetROISequence[0].ReferencedFrameOfReferenceUID = "1.2.3"
    rt_ss.StructureSetROISequence[0].ROINumber = "1"

    rt_ss.ROIContourSequence = []

    rt_ss.RTROIObservationsSequence = []

    roi_name = "NewTestROI"
    roi_coordinates = [0, 0, 0, 0, 1, 0, 1, 0, 0]  # a right triangle
    image_ds = dataset.Dataset()
    image_ds.SOPClassUID = "1.2.840.10008.5.1.4.1.1.2"
    image_ds.SOPInstanceUID = "1.2.3.4.5.6.7.8.9"
    patient_dict_container = PatientDictContainer()
    # container has to be initialised with kwargs content for the get/set to not fail for lack of an
    # "additional_parameters" dict.
    patient_dict_container.set_initial_values(None, None, None, blah="blah", rois={})
    if patient_dict_container.get("rois") is not None:
        print("rois are present in patient dict container")
    updated_rtss = create_roi(rt_ss, roi_name, roi_coordinates, image_ds)
    assert (
        updated_rtss.ROIContourSequence[0]
        .ContourSequence[0]
        .ContourImageSequence[0]
        .ReferencedSOPClassUID
        == image_ds.SOPClassUID
    )
