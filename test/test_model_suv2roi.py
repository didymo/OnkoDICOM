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
        desired_path = Path.cwd().joinpath('test', 'testdata', 'DICOM-PT-TEST')

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
        self.suv_data = None

        # Create ISO2ROI object
        self.suv2roi = SUV2ROI()


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

    # Assert that there are both PT CTAC and PT NAC files in the DICOM
    # dataset
    assert test_object.dicom_files
    assert len(test_object.dicom_files["PT CTAC"]) > 0
    assert len(test_object.dicom_files["PT NAC"]) > 0


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

    # Loop through each dataset in PT NAC, append them to datasets
    for ds in test_object.dicom_files["PT NAC"]:
        datasets.append(ds)

    # Loop through each dataset, perform tests
    for ds in datasets:
        # Calculate SUV values
        suv_values = test_object.suv2roi.pet2suv(ds)

        # Assert that there are SUV values, and that there are the same
        # amount of SUV values as there are pixels in the dataset
        assert len(suv_values) == len(ds.pixel_array)

        # Manually SUV values
        # Get data necessary for Bq/ml to SUV calculation
        rescale_slope = ds.RescaleSlope
        rescale_intercept = ds.RescaleIntercept
        pixel_array = ds.pixel_array
        radiopharmaceutical_info = \
            ds.RadiopharmaceuticalInformationSequence[0]
        radionuclide_total_dose = \
            radiopharmaceutical_info['RadionuclideTotalDose'].value
        patient_weight = ds.PatientWeight

        # Convert Bq/ml to SUV
        suv = (pixel_array * rescale_slope + rescale_intercept)
        suv = suv * (1000 * patient_weight) / radionuclide_total_dose

        # Assert that manually-generated SUV values are the same as
        # code-generated SUV values
        assert numpy.array_equal(suv_values, suv)


def test_select_pixel_data(test_object):
    """
    Test for selecting pixel data from PET files.
    :param test_object: test_object function, for accessing the shared
                        TestStructureTab object.
    """
    # Get PT NAC data
    files = test_object.dicom_files["PT NAC"]
    test_object.suv_data = test_object.suv2roi.get_SUV_data(files)

    # Assert that there is SUV data and that it is the same length as
    # the PT CTAC and PT NAC lists inside dicom_files
    assert test_object.suv_data
    assert len(test_object.suv_data) == len(test_object.dicom_files["PT NAC"])

    # Get PT CTAC SUV data
    files = test_object.dicom_files["PT CTAC"]
    test_object.suv_data = test_object.suv2roi.get_SUV_data(files)

    # Assert that there is SUV data and that it is the same length as
    # the PT CTAC and PT NAC lists inside dicom_files
    assert test_object.suv_data
    assert len(test_object.suv_data) == len(test_object.dicom_files["PT CTAC"])


def test_calculate_suv_boundaries(test_object):
    """
    Test for calculating SUV boundaries.
    :param test_object: test_object function, for accessing the shared
                        TestStructureTab object.
    """

    # Get code-generated contours
    contour_data = test_object.suv2roi.calculate_contours(test_object.suv_data)

    # Assert that there is contour data
    assert len(contour_data) > 0

    # Manually calculate contour data
    manual_contour_data = {}

    for i, slice in enumerate(test_object.suv_data):
        manual_contour_data[slice[0]] = []
        for j in range(0, int(slice[1].max()) - 2):
            manual_contour_data[slice[0]].append(
                measure.find_contours(slice[1], j + 3))

    # Assert the manually-generated and code-generated contour data is
    # the same.
    assert len(manual_contour_data) == len(contour_data)
    for key in manual_contour_data:
        assert key in contour_data
        assert len(manual_contour_data[key]) == len(contour_data[key])
