import os

import pytest
from pathlib import Path

from src.Controller.GUIController import MainWindow
from src.Model.PatientDictContainer import PatientDictContainer
from src.Model import ImageLoading

from pydicom import dcmread
from pydicom.errors import InvalidDicomError


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


class TestManipulateROI:
    """Class to set up the OnkoDICOM main window for testing the Manipulate ROI
    window."""
    __test__ = False

    def __init__(self):
        # Load test DICOM files
        desired_path = Path.cwd().joinpath('test', 'testdata')
        # list of DICOM test files
        selected_files = find_DICOM_files(desired_path)
        # file path of DICOM files
        file_path = os.path.dirname(os.path.commonprefix(selected_files))
        read_data_dict, file_names_dict = ImageLoading.get_datasets(
            selected_files)

        # Create patient dict container object
        patient_dict_container = PatientDictContainer()
        patient_dict_container.clear()
        patient_dict_container.set_initial_values(file_path, read_data_dict,
                                                  file_names_dict)

        # Set additional attributes in patient dict container (otherwise
        # program will crash and test will fail)
        if "rtss" in file_names_dict:
            self.dataset_rtss = dcmread(file_names_dict['rtss'])
            self.rois = ImageLoading.get_roi_info(self.dataset_rtss)
            dict_raw_contour_data, dict_numpoints = \
                ImageLoading.get_raw_contour_data(self.dataset_rtss)
            dict_pixluts = ImageLoading.get_pixluts(read_data_dict)

            patient_dict_container.set("rois", self.rois)
            patient_dict_container.set("raw_contour", dict_raw_contour_data)
            patient_dict_container.set("num_points", dict_numpoints)
            patient_dict_container.set("pixluts", dict_pixluts)

        # Open the main window
        self.main_window = MainWindow()
        self.main_window.show()

        # Open the manipulate ROI window
        self.structures_tab = self.main_window.structures_tab
        color_dict = self.structures_tab.color_dict
        self.roi_manipulate_handler = self.structures_tab.\
            roi_manipulate_handler.show_roi_manipulate_options(color_dict)
        self.manipulate_window = self.structures_tab.\
            roi_manipulate_handler.manipulate_window

@pytest.fixture(scope="module")
def test_object():
    """Function to pass a shared TestManipulateROI object to each test."""
    test = TestManipulateROI()
    return test


def test_input_form(test_object):
    """
    Test input form in the left panel. This function selects an operation and
    check if the form's inputs is displayed correctly based on type of the
    selected operation.
    :param test_object: test_object function, for accessing the shared
    TestManipulateROI object.
    """
    # Select a single roi operation
    test_object.manipulate_window.operation_name_dropdown_list.\
        setCurrentText("Expand")
    test_object.manipulate_window.operation_changed()

    # Check input form when selecting a single roi operation
    assert not test_object.manipulate_window.second_roi_name_label.isVisible()
    assert not test_object.manipulate_window.second_roi_name_dropdown_list.\
        isVisible()
    assert test_object.manipulate_window.margin_label.isVisible()
    assert test_object.manipulate_window.margin_line_edit.isVisible()

    # Select a multiple roi operation
    test_object.manipulate_window.operation_name_dropdown_list. \
        setCurrentText("Union")
    test_object.manipulate_window.operation_changed()

    # Check input form when selecting a single roi operation
    assert test_object.manipulate_window.second_roi_name_label.isVisible()
    assert test_object.manipulate_window.second_roi_name_dropdown_list.\
        isVisible()
    assert not test_object.manipulate_window.margin_label.isVisible()
    assert not test_object.manipulate_window.margin_line_edit.isVisible()


def test_warning_message_displaying(test_object):
    """
    Test warning message. This function tests the displaying of the warning
    message when the draw/save button is clicked when not all inputs are set.
    :param test_object: test_object function, for accessing the shared
    TestManipulateROI object.
    """
    # The draw button is clicked when not all values are set
    test_object.manipulate_window.onDrawButtonClicked()
    assert test_object.manipulate_window.warning_message.isVisible()

    # The warning message must disappear when an input is set
    test_object.manipulate_window.operation_name_dropdown_list. \
        setCurrentText("Union")
    test_object.manipulate_window.operation_changed()
    assert not test_object.manipulate_window.warning_message.isVisible()

    # The save button is clicked when not all values are set
    test_object.manipulate_window.onSaveClicked()
    assert test_object.manipulate_window.warning_message.isVisible()

