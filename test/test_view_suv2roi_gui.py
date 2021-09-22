import os
import pytest

from pathlib import Path
from pydicom import dcmread
from pydicom.errors import InvalidDicomError
from src.Controller.GUIController import MainWindow
from src.Model.PatientDictContainer import PatientDictContainer
from src.Model import ImageLoading
from src.View.ImageLoader import ImageLoader


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


class DummyProgressWindow:
    """
    A class for running threads/progress windows without actually
    creating a progress window.
    """
    @staticmethod
    def emit(message):
        pass

    @staticmethod
    def set():
        return False

    @staticmethod
    def is_set():
        return False


class TestSuv2RoiGui:
    """
    Class that initializes an OnkoDICOM window for testing SUV2ROI GUI.
    This uses files from the pet-testdata directory.
    """

    __test__ = False

    def __init__(self):
        # Load test DICOM files
        desired_path = Path.cwd().joinpath('test', 'pet-testdata')

        # List of DICOM test files
        selected_files = find_DICOM_files(desired_path)

        # File path of DICOM files
        file_path = os.path.dirname(os.path.commonprefix(selected_files))
        read_data_dict, file_names_dict = \
            ImageLoading.get_datasets(selected_files)

        # Create patient dict container object
        self.patient_dict_container = PatientDictContainer()
        self.patient_dict_container.clear()
        self.patient_dict_container.set_initial_values \
            (file_path, read_data_dict, file_names_dict)

        # Set additional attributes in patient dict container
        # (otherwise program will crash and test will fail)
        self.patient_dict_container.set("existing_rtss_files",
                                        [])
        if "rtss" in file_names_dict:
            dataset_rtss = dcmread(file_names_dict['rtss'])
            self.rois = ImageLoading.get_roi_info(dataset_rtss)
            dict_raw_contour_data, dict_numpoints = \
                ImageLoading.get_raw_contour_data(dataset_rtss)
            dict_pixluts = ImageLoading.get_pixluts(read_data_dict)

            self.patient_dict_container.set("rois", self.rois)
            self.patient_dict_container.set("raw_contour",
                                            dict_raw_contour_data)
            self.patient_dict_container.set("num_points", dict_numpoints)
            self.patient_dict_container.set("pixluts", dict_pixluts)
        else:
            img_loader = ImageLoader(selected_files, None, None)
            img_loader.load_temp_rtss(file_path, DummyProgressWindow,
                                      DummyProgressWindow)

        # Open the main window
        self.main_window = MainWindow()

        # Get the initial structure and ROI count
        self.initial_structure_count = \
            self.main_window.structures_tab.layout_content.count()
        self.initial_roi_count = len(self.main_window.structures_tab.rois)


@pytest.fixture(scope="module")
def test_object():
    """
    Function to pass a shared TestIso2RoiGui object
    to each test.
    """
    return TestSuv2RoiGui()


@pytest.mark.skip()
def test_structures_convert_suv_to_roi_button_pressed(test_object):
    """
    Test will simulate the 'Convert SUVs to ROIs' button being
    pressed, assert structure count is greater than or equal to what it
    originally was.
    :param test_object: test_object function, for accessing the shared
                        TestSuv2RoiGui object.
    """
    # Set patient weight
    test_object.main_window.suv2roi.patient_weight = 70000

    # Simulate 'Convert SUVs to ROIs' button being pressed
    test_object.main_window.suv2roi_progress_window.start(
        test_object.main_window.suv2roi.start_conversion)

    # Get the new length of structures in Structures Tab
    current_structure_count = \
        test_object.main_window.structures_tab.layout_content.count()

    # Assert the length has not changed
    assert current_structure_count >= test_object.initial_structure_count


@pytest.mark.skip()
def test_rois_convert_suv_to_roi_button_pressed(test_object):
    """
    Test will simulate the 'Convert SUVs to ROIs' button being
    pressed, assert ROI count is greater than or equal to what it
    originally was.
    :param test_object: test_object function, for accessing the shared
                        TestSuv2RoiGui object.
    """
    # Set patient weight
    test_object.main_window.suv2roi.patient_weight = 70000

    # Simulate 'Convert SUVs to ROIs' button being pressed
    test_object.main_window.suv2roi_progress_window.start(
        test_object.main_window.suv2roi.start_conversion)

    # Get the new length of ROI's in Structures Tab
    current_roi_count = len(test_object.main_window.structures_tab.rois)

    # Assert the length has not changed
    assert current_roi_count >= test_object.initial_roi_count
