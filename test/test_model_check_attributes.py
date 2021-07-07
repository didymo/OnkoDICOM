from main import CheckAttributes

import pytest
import platform
import os


class TestObject:
    """Class contains directory information for test cases, and expected test values"""
    __test__ = False

    def __init__(self):
        # Test data in the testing directory (\\test\\testdata\\DICOM-RT-TEST) contains 1 of each DICOM type
        # null_path would contain no files of any type
        self.test_directory_RTDOSE_Count = 1
        self.test_directory_CT_Count = 1

        # Determine path for the testing files, and a null directory
        if platform.system() == "Windows":
            self.test_directory = "\\testdata\\DICOM-RT-TEST"
            self.null_path = "\\nullpath"
        elif platform.system() == "Linux" or platform.system() == "Darwin":
            test_directory = "/testdata/DICOM-RT-TEST"
            null_path = "/nullpath"

        # Get absolute paths
        self.test_directory = os.path.dirname(os.path.realpath(__file__)) + self.test_directory
        self.null_path = os.path.dirname(os.path.realpath(__file__)) + self.null_path


@pytest.fixture(scope="module")
def test_object():
    """Passes the same instance of TestObject to each test"""
    test = TestObject()
    return test


def test_file_counts_null_directory(test_object):
    """
    Test that no DICOM files of formats 'RT DOSE' or 'CT Image' are present in a directory that doesn't exist.
    Note: a directory that doesn't exist behaves in same way as a directory that contains no DICOM files.

    :param test_object: test_object function, for accessing the shared TestStructureTab object.
    """

    # Create a CheckAttributes object, find all DICOM files in the directory, and find which elements are present
    DICOM_attributes = CheckAttributes(test_object.null_path)
    DICOM_attributes.find_DICOM_files()
    present_elements = DICOM_attributes.check_elements()

    # Assert no elements were found
    assert present_elements is None


def test_file_counts_testing_directory(test_object):
    """
    Test that DICOM files of formats 'RT Dose' and 'CT Image' are present in the test directory and with
    the correct quantities.

    :param test_object: test_object function, for accessing the shared TestStructureTab object.
    """

    # Create a CheckAttributes object, find all DICOM files in the directory, and find which elements are present
    DICOM_attributes = CheckAttributes(test_object.test_directory)
    DICOM_attributes.find_DICOM_files()
    present_elements = DICOM_attributes.check_elements()

    # Assert number of 'RT Dose' files matches expected count
    assert present_elements["RT Dose"] == test_object.test_directory_RTDOSE_Count

    # Assert number of 'CT Image' files matches expected count
    assert present_elements["CT Image"] == test_object.test_directory_CT_Count


