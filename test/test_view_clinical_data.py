import csv
import os

from pydicom import dcmread
from pydicom.errors import InvalidDicomError
from pathlib import Path
from src.Model import DICOMStructuredReport
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


def test_import_clinical_data():
    """
    Unit Test for importing clinical data from a CSV.
    """
    # Set patient ID
    patient_id = '123456789'

    # Create temporary CSV
    file_path = Path.cwd().joinpath('test', 'testdata', 'ClinicalData.csv')
    data = [['123456789', 'Jim', 'Jimson']]
    with open(file_path, "w") as csvFile:  # inserting the hash values
        writer = csv.writer(csvFile)
        for row in data:
            writer.writerow(row)
        csvFile.close()

    # Attempt to import clinical data
    with open(file_path, newline="") as stream:
        data = list(csv.reader(stream))

    patient_in_file = False
    row_num = 0
    for i, row in enumerate(data):
        if row[0] == patient_id:
            patient_in_file = True
            row_num = i
            break

    # Delete the created CSV
    os.remove(file_path)

    # Assert the patient has been found
    assert patient_in_file
    assert row_num == 0



def test_save_clinical_data():
    """
    Test for saving clinical data to a DICOM SR file.
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
    file_path = Path(file_path).joinpath("Clinical-Data-SR.dcm")
    ds = patient_dict_container.dataset[0]
    dicom_sr = DICOMStructuredReport.generate_dicom_sr(file_path, ds, "text")
    dicom_sr.save_as(file_path)

    # Assert that the new SR exists
    assert os.path.isfile(file_path)

    # Delete the created DICOM SR
    os.remove(file_path)
