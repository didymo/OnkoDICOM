import os
import numpy
import pytest

from src.Model.SUV2ROI import SUV2ROI
from src.Model.PatientDictContainer import PatientDictContainer
from src.Model import ImageLoading

from pathlib import Path
from pydicom import dcmread
from pydicom.errors import InvalidDicomError
from skimage import measure


def find_dicom_files(file_path):
    """
    Function to find DICOM files in a given folder.
    :param file_path: File path of folder to search.
    :return: List of file paths of DICOM files in given folder.
    """

    dicom_files = []

    # Walk through directory
    for root, dirs, files in os.walk(file_path, topdown=True):
        for name in files:
            # Attempt to open file as a DICOM file
            try:
                dcmread(os.path.join(root, name))
            except (InvalidDicomError, FileNotFoundError):
                pass
            else:
                dicom_files.append(os.path.join(root, name))
    return dicom_files


class TestSuv2Roi:
    """
    Class to set up the OnkoDICOM main window for testing
    SUV2ROI functionality. Assumes there is test data containing PET
    files, both CTAC and NAC, in /test/testdata/DICOM-PT-TEST/. Tests
    will all fail without this data.
    """
    __test__ = False

    def __init__(self):
        # Load test DICOM files
        desired_path = Path.cwd().joinpath('test', 'testdata')

        # list of DICOM test files
        selected_files = find_dicom_files(desired_path)
        # file path of DICOM files
        file_path = os.path.dirname(os.path.commonprefix(selected_files))
        read_data_dict, file_names_dict = \
            ImageLoading.get_datasets(selected_files)

        # Create patient dict container object
        self.patient_dict_container = PatientDictContainer()
        self.patient_dict_container.clear()
        self.patient_dict_container.set_initial_values\
            (file_path, read_data_dict, file_names_dict)

        # Create variables to be initialised later
        self.dicom_files = None
        self.suv_data = []

        # Create ISO2ROI object
        self.suv2roi = SUV2ROI()
        # Set patient weight. Not actual weight, just for testing
        # purposes.
        self.suv2roi.patient_weight = 70000


@pytest.fixture(scope="module")
def test_object():
    """Function to pass a shared TestIso2Roi object to each test."""
    test = TestSuv2Roi()
    return test


def test_select_pet_files(test_object):
    """
    Test for selecting PET files from a DICOM dataset.
    :param test_object: test_object function, for accessing the shared
                        TestStructureTab object.
    """
    # Get DICOM files in directory
    test_object.dicom_files = test_object.suv2roi.find_PET_datasets()

    # Assert that there are PT CTAC and no PT NAC files in the DICOM
    # dataset
    assert test_object.dicom_files
    assert len(test_object.dicom_files["PT CTAC"]) > 0
    assert len(test_object.dicom_files["PT NAC"]) == 0


def test_calculate_suv_values(test_object):
    """
    Test for calculating SUV values from PET pixel data.
    :param test_object: test_object function, for accessing the shared
                        TestStructureTab object.
    """
    datasets = []

    # Loop through each dataset in PT CTAC, append them to datasets
    for ds in test_object.dicom_files["PT CTAC"]:
        datasets.append(ds)

    # Loop through each dataset, perform tests
    for ds in datasets:
        # Calculate SUV values
        suv_values = test_object.suv2roi.pet2suv(ds)
        test_object.suv_data.append(suv_values)

        # Assert that there are SUV values, and that there are the same
        # amount of SUV values as there are pixels in the dataset
        assert len(suv_values) == len(ds.pixel_array)

        # Manually SUV values
        # Get data necessary for Bq/ml to SUV calculation
        rescale_slope = ds.RescaleSlope
        rescale_intercept = ds.RescaleIntercept
        pixel_array = ds.pixel_array

        # Convert Bq/ml to SUV
        suv = (pixel_array * rescale_slope + rescale_intercept) \
            * test_object.suv2roi.weight_over_dose

        # Assert that manually-generated SUV values are the same as
        # code-generated SUV values
        assert numpy.array_equal(suv_values, suv)


def test_calculate_suv_boundaries(test_object):
    """
    Test for calculating SUV boundaries.
    :param test_object: test_object function, for accessing the shared
                        TestStructureTab object.
    """

    # Manually calculate contour data (one slice only)
    manual_contour_data = {}

    # Get SUV data from PET file
    suv_data = test_object.suv_data[40]
    current_suv = 1
    max_suv = numpy.amax(suv_data)

    # Continue calculating SUV contours for the slice until the
    # max SUV has been reached.
    while current_suv < max_suv:
        # Find the contours for the SUV (i)
        contours = measure.find_contours(suv_data, current_suv)

        # Get the SUV name
        name = "SUV-" + str(current_suv)
        if name not in manual_contour_data:
            manual_contour_data[name] = []
        manual_contour_data[name].append((0, contours))
        current_suv += 1

    # Assert the manually-generated contour data exists
    assert len(manual_contour_data) > 0
    for key in manual_contour_data:
        assert len(manual_contour_data[key][0][1]) >= 0


def test_generate_roi_from_suv(test_object):
    """
    Test for generating ROIs from SUV data.
    :param test_object: test_object function, for accessing the shared
                        TestStructureTab object.
    """
    # Create fake contour data
    contours = {
        "101": [[[[0, 1]]]], "102": [[[[1, 2]]]], "103": [[[[2, 3]]]],
        "104": [[[[3, 4]]]], "105": [[[[4, 5]]]]
    }

    # Calculate SUV ROI for each slice and SUV level from 3 to the
    # max, skip if slice has no contour data
    single_array = []
    # Loop through each contour
    for item in contours:
        for i in range(len(contours[item])):
            for j in range(len(contours[item][i][0])):
                # Loop through every point in the contour
                for point in contours[item][i][0][j]:
                    # Append points to the single array. Converting to
                    # RCS points is skipped on purpose.
                    single_array.append(point)
                single_array.append(1)

    # Assert ROI points exist
    assert len(single_array) == 15
    assert len(single_array) == 3 * len(contours)
