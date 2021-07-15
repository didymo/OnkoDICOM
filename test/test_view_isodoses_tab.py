import os
import pytest
from pathlib import Path

from src.Controller.GUIController import MainWindow
from src.Model.PatientDictContainer import PatientDictContainer
from src.View.mainpage.IsodoseTab import isodose_percentages
from src.Model import ImageLoading

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


class TestIsodosesTab:
    """
    Class to set up the OnkoDICOM main window for testing the
    structures tab.
    """
    __test__ = False

    def __init__(self):
        # Load test DICOM files
        desired_path = str(Path.cwd().joinpath('test', 'testdata', \
                                               'DICOM-RT-TEST'))

        # List of DICOM test files
        selected_files = find_DICOM_files(desired_path)
        # File path of DICOM files
        file_path = os.path.dirname(os.path.commonprefix(selected_files))
        read_data_dict, file_names_dict = \
            ImageLoading.get_datasets(selected_files)

        # Create patient dict container object
        self.patient_dict_container = PatientDictContainer()
        self.patient_dict_container.clear()
        self.patient_dict_container.set_initial_values\
            (file_path, read_data_dict, file_names_dict)

        # Set additional attributes in patient dict container
        # (otherwise program will crash and test will fail)
        if "rtss" in file_names_dict:
            dataset_rtss = dcmread(file_names_dict['rtss'])
            self.rois = ImageLoading.get_roi_info(dataset_rtss)
            dict_raw_contour_data, dict_numpoints = \
                ImageLoading.get_raw_contour_data(dataset_rtss)
            dict_pixluts = ImageLoading.get_pixluts(read_data_dict)

            self.patient_dict_container.set("rois", self.rois)
            self.patient_dict_container.set("raw_contour", \
                                            dict_raw_contour_data)
            self.patient_dict_container.set("num_points", \
                                            dict_numpoints)
            self.patient_dict_container.set("pixluts", dict_pixluts)

        # Open the main window
        self.main_window = MainWindow()


@pytest.fixture(scope="module")
def test_object():
    """
    Function to pass a shared TestStructureTab object to each test.
    """
    test = TestIsodosesTab()
    return test


def test_isodoses_tab_check_checkboxes(test_object):
    # For each available isolevel, simulate corresponding checkbox
    # set to true
    for isolevel in isodose_percentages:
        test_object.main_window.isodoses_tab.checked_dose(True, isolevel)
        # Assert the isodose is being drawn
        doses = test_object.patient_dict_container.get('selected_doses')
        assert isolevel in doses


def test_isodoses_tab_uncheck_checkboxes(test_object):
    # For each available isolevel, simulate corresponding
    # checkbox set to false
    for isolevel in isodose_percentages:
        test_object.main_window.isodoses_tab.checked_dose(False, isolevel)
        # Assert the isodose is not being drawn
        doses = test_object.patient_dict_container.get('selected_doses')
        assert isolevel not in doses


