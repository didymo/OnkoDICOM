import os
import pytest

from src.Model.SUV2ROI import SUV2ROI
from src.Model.PatientDictContainer import PatientDictContainer
from src.Model import ImageLoading

from pathlib import Path
from pydicom import dcmread
from pydicom.errors import InvalidDicomError


def find_DICOM_files(file_path):
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
        selected_files = find_DICOM_files(desired_path)
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


def test_select_PET_files(test_object):
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
