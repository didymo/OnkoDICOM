import os

import pytest
from pathlib import Path
from PySide6.QtWidgets import QGridLayout, QGraphicsPolygonItem
from pydicom import dcmread
from pydicom.errors import InvalidDicomError

from src.Controller.GUIController import MainWindow
from src.Model import ImageLoading
from src.Model.PatientDictContainer import PatientDictContainer
from src.View.mainpage.DicomView import DicomView
from src.constants import INITIAL_FOUR_VIEW_ZOOM, INITIAL_ONE_VIEW_ZOOM


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


class TestOneViewAndFourViewsHandling:
    """Class to set up the OnkoDICOM main window for testing the structures tab."""
    __test__ = False

    def __init__(self):
        # Load test DICOM files
        desired_path = Path.cwd().joinpath('test', 'testdata')
        selected_files = find_DICOM_files(desired_path)  # list of DICOM test files
        file_path = os.path.dirname(os.path.commonprefix(selected_files))  # file path of DICOM files
        read_data_dict, file_names_dict = ImageLoading.get_datasets(selected_files)

        # Create patient dict container object
        patient_dict_container = PatientDictContainer()
        patient_dict_container.clear()
        patient_dict_container.set_initial_values(file_path, read_data_dict, file_names_dict)

        # Set additional attributes in patient dict container (otherwise program will crash and test will fail)
        if "rtss" in file_names_dict:
            dataset_rtss = dcmread(file_names_dict['rtss'])
            self.rois = ImageLoading.get_roi_info(dataset_rtss)
            dict_raw_contour_data, dict_numpoints = ImageLoading.get_raw_contour_data(dataset_rtss)
            dict_pixluts = ImageLoading.get_pixluts(read_data_dict)

            patient_dict_container.set("rois", self.rois)
            patient_dict_container.set("raw_contour", dict_raw_contour_data)
            patient_dict_container.set("num_points", dict_numpoints)
            patient_dict_container.set("pixluts", dict_pixluts)

        # Open the main window
        self.main_window = MainWindow()


@pytest.fixture(scope="module")
def test_object():
    """Function to pass a shared TestStructureTab object to each test."""
    test = TestOneViewAndFourViewsHandling()
    return test


def test_one_view_handling(qtbot, test_object, init_config):
    test_object.main_window.show()
    test_object.main_window.action_handler.action_one_view.trigger()
    assert isinstance(test_object.main_window.dicom_single_view, DicomView) is True
    assert test_object.main_window.dicom_view.currentWidget() == test_object.main_window.dicom_single_view


def test_one_view_zoom(qtbot, test_object, init_config):
    test_object.main_window.show()
    test_object.main_window.action_handler.action_one_view.trigger()
    initial_zoom = test_object.main_window.dicom_single_view.zoom
    assert (initial_zoom == INITIAL_ONE_VIEW_ZOOM)
    test_object.main_window.action_handler.action_zoom_in.trigger()
    assert (test_object.main_window.dicom_single_view.zoom == 1.05 * initial_zoom)
    test_object.main_window.action_handler.action_zoom_out.trigger()
    assert (test_object.main_window.dicom_single_view.zoom == initial_zoom)


def test_four_view_handling(qtbot, test_object, init_config):
    test_object.main_window.show()
    test_object.main_window.action_handler.action_four_views.trigger()
    assert isinstance(test_object.main_window.dicom_axial_view, DicomView) is True
    assert isinstance(test_object.main_window.dicom_sagittal_view, DicomView) is True
    assert isinstance(test_object.main_window.dicom_coronal_view, DicomView) is True
    assert isinstance(test_object.main_window.dicom_four_views_layout, QGridLayout) is True
    assert test_object.main_window.dicom_view.currentWidget() == test_object.main_window.dicom_four_views
    assert test_object.main_window.dicom_axial_view.pos().x(), test_object.main_window.dicom_axial_view.pos().y() == (
        0, 0)
    assert test_object.main_window.dicom_sagittal_view.pos().x(), \
        test_object.main_window.dicom_sagittal_view.pos().y() == (0, 1)
    assert test_object.main_window.dicom_coronal_view.pos().x(), \
        test_object.main_window.dicom_coronal_view.pos().y() == (1, 0)


def test_four_view_zoom(qtbot, test_object, init_config):
    test_object.main_window.show()
    test_object.main_window.action_handler.action_four_views.trigger()

    initial_axial_zoom = test_object.main_window.dicom_axial_view.zoom
    initial_coronal_zoom = test_object.main_window.dicom_coronal_view.zoom
    initial_sagittal_zoom = test_object.main_window.dicom_sagittal_view.zoom

    assert (initial_coronal_zoom == INITIAL_FOUR_VIEW_ZOOM)
    assert (initial_sagittal_zoom == INITIAL_FOUR_VIEW_ZOOM)
    assert (initial_axial_zoom == INITIAL_FOUR_VIEW_ZOOM)

    test_object.main_window.action_handler.action_zoom_in.trigger()
    assert (test_object.main_window.dicom_axial_view.zoom == initial_axial_zoom * 1.05)
    assert (test_object.main_window.dicom_coronal_view.zoom == initial_coronal_zoom * 1.05)
    assert (test_object.main_window.dicom_sagittal_view.zoom == initial_sagittal_zoom * 1.05)

    test_object.main_window.action_handler.action_zoom_out.trigger()
    assert (test_object.main_window.dicom_axial_view.zoom == initial_axial_zoom)
    assert (test_object.main_window.dicom_coronal_view.zoom == initial_coronal_zoom)
    assert (test_object.main_window.dicom_sagittal_view.zoom == initial_sagittal_zoom)


def test_one_view_roi(qtbot, test_object, init_config):
    test_object.main_window.show()
    test_object.main_window.action_handler.action_one_view.trigger()

    # The first four ROI can not be displayed on the single DICOM test image. Use the fifth roi to test
    fifth_roi_id = list(test_object.main_window.structures_tab.rois.items())[4][0]
    test_object.main_window.structures_tab.structure_checked(True, fifth_roi_id)

    # Check if ROI is present
    assert isinstance(test_object.main_window.dicom_single_view.scene.items()[0], QGraphicsPolygonItem)

    # Check if ROI color is correct
    assert test_object.main_window.dicom_single_view.scene.items()[0].brush().color() == \
           test_object.main_window.structures_tab.color_dict[fifth_roi_id]
