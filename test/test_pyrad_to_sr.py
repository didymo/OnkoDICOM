from src.Model.DICOM import DICOMStructuredReport

import os

from pydicom import dcmread
from pydicom.errors import InvalidDicomError
from pathlib import Path
from src.Model import ImageLoading
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


def test_save_radiomics_data():
    """
    Test for saving pyradiomics data to a DICOM SR file.
    """
    # Get test data files
    # Load test DICOM files
    desired_path = Path.cwd().joinpath('test', 'testdata')

    # list of DICOM test files
    selected_files = find_DICOM_files(desired_path)
    # file path of DICOM files
    file_path = os.path.dirname(os.path.commonprefix(selected_files))
    read_data_dict, file_names_dict = \
        ImageLoading.get_datasets(selected_files)

    # Create patient dict container object
    patient_dict_container = PatientDictContainer()
    patient_dict_container.clear()
    patient_dict_container.set_initial_values(file_path, read_data_dict,
                                              file_names_dict)

    file_path = patient_dict_container.path
    file_path = Path(file_path).joinpath("PyRadiomics-SR.dcm")
    ds = patient_dict_container.dataset[0]
    dicom_sr = DICOMStructuredReport.generate_dicom_sr(file_path, ds, "text",
                                                       "PYRADIOMICS")
    dicom_sr.save_as(file_path)

    # Assert that the new SR exists
    assert os.path.isfile(file_path)

    # Delete the created DICOM SR
    os.remove(file_path)
