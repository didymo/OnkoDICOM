import os
import pytest

from pathlib import Path
from pydicom import dcmread
from pydicom.errors import InvalidDicomError
from src.Model import ImageLoading
from src.Model.CalculateDVHs import dvh2rtdose, rtdose2dvh
from src.Model.PatientDictContainer import PatientDictContainer


def find_DICOM_files(file_path):
    """Function to find DICOM files in a given folder.
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


class TestDvh2RtDose:
    """
    This class is to set up data and variables needed for the DVH2RTDOSE
    functionality.
    """

    __test__ = False

    def __init__(self):
        self.dvh_data = None

        # Load test DICOM files
        desired_path = Path.cwd().joinpath('test', 'testdata')
        selected_files = find_DICOM_files(desired_path)
        file_path = os.path.dirname(os.path.commonprefix(selected_files))
        read_data_dict, file_names_dict = \
            ImageLoading.get_datasets(selected_files)

        # Create patient dict container object
        self.patient_dict_container = PatientDictContainer()
        self.patient_dict_container.clear()
        self.patient_dict_container.set_initial_values(file_path,
                                                       read_data_dict,
                                                       file_names_dict)


@pytest.fixture(scope="module")
def test_object():
    """Function to pass a shared TestIso2Roi object to each test."""
    test = TestDvh2RtDose()
    return test


def test_rtdose_to_dvh(test_object):
    """
    Test converting DVH data contained within an RT Dose into DVH data
    used by OnkoDICOM.
    :param test_object: test_object function, for accessing the shared
                        TestDvh2RtDose object.
    """
    # Get DVH data
    test_object.dvh_data = rtdose2dvh()

    # Assert DVH data exists and is of expected length
    assert test_object.dvh_data


def test_dvh_to_rtdose(test_object):
    """
    Test saving DVH data to an RT Dose file.
    :param test_object: test_object function, for accessing the shared
                        TestDvh2RtDose object.
    """
    # Get RT Dose last modified time
    rt_dose = Path(test_object.patient_dict_container.filepaths['rtdose'])
    last_modified = rt_dose.stat().st_mtime
    dvh_length = len(test_object.patient_dict_container
                     .dataset['rtdose'].DVHSequence)

    # Save DVH data
    test_object.dvh_data.pop("diff")
    dvh2rtdose(test_object.dvh_data)

    # Assert file has been modified, and DVHs are the same length
    assert dvh_length == len(test_object.patient_dict_container
                             .dataset['rtdose'].DVHSequence)
    assert last_modified < rt_dose.stat().st_mtime

