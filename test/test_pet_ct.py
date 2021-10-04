import pytest
import os
import numpy as np

from PySide6.QtWidgets import QPushButton
from PySide6.QtGui import QColor

from src.constants import DEFAULT_WINDOW_SIZE
from src.Model.PTCTDictContainer import PTCTDictContainer
from src.Model.CalculateImages import convert_pt_to_heatmap

from src.Controller.GUIController import MainWindow
from src.Model.PatientDictContainer import PatientDictContainer
from src.View.ImageLoader import ImageLoading

from pydicom import dcmread
from pydicom.errors import InvalidDicomError
from pathlib import Path


def get_dicom_files(directory):
    """
    Function to find DICOM files in a given folder.
    :param directory: File path of folder to search.
    :return: List of file paths of DICOM files in given folder.
    """
    dicom_files = []

    # Walk through directory
    for root, dirs, files in os.walk(directory, topdown=True):
        for name in files:
            # Attempt to open file as a DICOM file
            try:
                dcmread(os.path.join(root, name))
            except (InvalidDicomError, FileNotFoundError):
                pass
            else:
                dicom_files.append(os.path.join(root, name))
    return dicom_files


class TestPETCT:
    """
    Class to set up the OnkoDICOM main window for testing the structures tab.
    """
    __test__ = False

    def __init__(self):
        # Load test DICOM files and set path variable
        path = Path.cwd().joinpath('test', 'testdata')
        files = get_dicom_files(path)  # list of DICOM test files
        file_path = os.path.dirname(os.path.commonprefix(files))
        read_data_dict, file_names_dict = ImageLoading.get_datasets(files)

        # Create patient dict container object
        patient_dict_container = PatientDictContainer()
        patient_dict_container.clear()
        patient_dict_container.set_initial_values(
            file_path, read_data_dict, file_names_dict)

        # Set additional attributes in patient dict container
        # This prevents crashes
        if "rtss" in file_names_dict:
            dataset_rtss = dcmread(file_names_dict['rtss'])
            self.rois = ImageLoading.get_roi_info(dataset_rtss)
            patient_dict_container.set("rois", self.rois)

        # Open the main window
        self.main_window = MainWindow()
        self.main_window.right_panel.setCurrentWidget(
            self.main_window.pet_ct_tab)
        self.pet_ct = self.main_window.pet_ct_tab


@pytest.fixture
def test_obj(qtbot):
    """
    Testing Object
    :return:
    """
    pet_ct = TestPETCT()
    return pet_ct


def test_initial_view(test_obj):
    """
    Tests the initial values are set properly
    """
    assert not test_obj.pet_ct.initialised
    assert isinstance(test_obj.pet_ct.load_pet_ct_button, QPushButton)
    test_pc_dict_container = PTCTDictContainer()
    assert test_pc_dict_container.is_empty()


def test_color_image():
    """
    Tests the heat map function maps correctly
    """
    # Generate two images that mirror each other
    color_1 = convert_pt_to_heatmap(grey_image(False))
    color_2 = convert_pt_to_heatmap(grey_image(True))

    # Check values map to their mirrored values
    for i in range(DEFAULT_WINDOW_SIZE):
        for j in range(DEFAULT_WINDOW_SIZE):
            assert color_1.pixel(i, j) \
                   == color_2.pixel(
                       DEFAULT_WINDOW_SIZE-i-1, DEFAULT_WINDOW_SIZE-j-1)

    # Test end values are black and white
    for k in range(DEFAULT_WINDOW_SIZE):
        assert QColor(color_1.pixel(0, k)).getRgb() \
               == QColor(color_2.pixel(DEFAULT_WINDOW_SIZE-1, k)).getRgb() \
               == (0, 0, 0, 255)
        assert QColor(color_1.pixel(DEFAULT_WINDOW_SIZE-1, k)).getRgb() \
               == QColor(color_2.pixel(0, k)).getRgb() \
               == (255, 255, 255, 255)


def grey_image(flipped):
    """
    generates one greyscale image with dimensions
    DEFAULT_WINDOW_SIZE x DEFAULT_WINDOW_SIZE
    """
    if flipped:
        tmp = np.linspace(255, 0, DEFAULT_WINDOW_SIZE)
    else:
        tmp = np.linspace(0, 255, DEFAULT_WINDOW_SIZE)
    tmp_2 = np.stack(DEFAULT_WINDOW_SIZE * (tmp,))
    return tmp_2
