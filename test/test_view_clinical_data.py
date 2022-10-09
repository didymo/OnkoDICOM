import csv
import os
import pytest

from pathlib import Path
from pydicom import dcmread
from pydicom.errors import InvalidDicomError
from PySide6.QtWidgets import QTableWidgetItem
from src.Model.DICOM import DICOMStructuredReport
from src.Model import ImageLoading
from src.Model.PatientDictContainer import PatientDictContainer
from src.View.mainpage.ClinicalDataView import ClinicalDataView


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


class TestClinicalDataView:
    """
    Class to set up variables required for testing the Clinical Data
    view.
    """
    __test__ = False

    def __init__(self):
        # Load test DICOM files
        desired_path = Path.cwd().joinpath('test', 'testdata')

        # list of DICOM test files
        selected_files = find_DICOM_files(desired_path)
        # file path of DICOM files
        self.file_path = os.path.dirname(os.path.commonprefix(selected_files))
        read_data_dict, file_names_dict = \
            ImageLoading.get_datasets(selected_files)

        # Create patient dict container object
        self.patient_dict_container = PatientDictContainer()
        self.patient_dict_container.clear()
        self.patient_dict_container.set_initial_values(self.file_path,
                                                       read_data_dict,
                                                       file_names_dict)

        self.file_path = self.patient_dict_container.path
        self.file_path = Path(self.file_path).joinpath("Clinical-Data-SR.dcm")

        # Test data to write
        self.data = [['123456789', 'Jim', 'Jimson']]


@pytest.fixture(scope="module")
def test_object():
    """
    Function to pass a shared TestClinicalDataView object to each test.
    """
    test = TestClinicalDataView()
    return test


def test_import_clinical_data(test_object):
    """
    Unit Test for importing clinical data from a CSV.
    :param test_object: test_object function, for accessing the shared
                        TestClinicalDataView object.
    """
    # Set patient ID
    patient_id = '123456789'

    # Create temporary CSV
    file_path = Path.cwd().joinpath('test', 'testdata', 'ClinicalData.csv')
    with open(file_path, "w") as csvFile:  # inserting the hash values
        writer = csv.writer(csvFile)
        for row in test_object.data:
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


def test_save_clinical_data(test_object):
    """
    Test for saving clinical data to a DICOM SR file.
    :param test_object: test_object function, for accessing the shared
                        TestClinicalDataView object.
    """
    text = ','.join(test_object.data[0])

    # Get test data files
    ds = test_object.patient_dict_container.dataset[0]
    dicom_sr = DICOMStructuredReport.generate_dicom_sr(test_object.file_path,
                                                       ds, text,
                                                       "CLINICAL-DATA")
    dicom_sr.save_as(test_object.file_path)

    # Assert that the new SR exists
    assert os.path.isfile(test_object.file_path)


def test_import_from_sr(test_object):
    """
    Test for importing clinical data from a DICOM SR file.
    :param test_object: test_object function, for accessing the shared
                        TestClinicalDataView object.
    """
    # Open clinical data file
    clinical_data = dcmread(test_object.file_path)
    assert clinical_data

    # Get text from clinical data dataset
    text = clinical_data.ContentSequence[0].TextValue
    assert text

    # Split text
    data = text.split(",")
    assert data[0] == test_object.data[0][0]
    assert data[1] == test_object.data[0][1]
    assert data[2] == test_object.data[0][2]

    # Delete the created DICOM SR
    os.remove(test_object.file_path)
    assert not os.path.exists(test_object.file_path)


def test_populate_table(test_object):
    """
    Test to create the Clinical Data View and populate the table.
    :param test_object: test_object function, for accessing the shared
                        TestClinicalDataView object.
    """
    # Create Clinical Data View object
    cd_view = ClinicalDataView()

    # Create table headers
    headers = ["ID", "FirstName", "LastName"]

    # Populate table
    for i, value in enumerate(headers):
        attrib = QTableWidgetItem(value)
        data = QTableWidgetItem(test_object.data[0][i])
        cd_view.table_cd.insertRow(i)
        cd_view.table_cd.setItem(i, 0, attrib)
        cd_view.table_cd.setItem(i, 1, data)

    # Assert data exists in table
    for i, value in enumerate(headers):
        assert cd_view.table_cd.item(i, 0).text() == value
        assert cd_view.table_cd.item(i, 1).text() == test_object.data[0][i]
