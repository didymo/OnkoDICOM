import os
import pytest
from pathlib import Path

from PySide6.QtCore import Qt
from pydicom import dcmread
from pydicom.errors import InvalidDicomError
from src.Controller.GUIController import MainWindow
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


class TestDrawingMock:
    """Function to set up a Drawing window."""
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

        # main window
        self.main_window = MainWindow()


@pytest.fixture(scope="module")
def test_object():
    """Function to initialise a Drawing window object."""
    test = TestDrawingMock()
    return test


def test_draw_roi_window_displayed(qtbot, test_object):
    """Function to test that the draw_roi_window is displayed
    within the main window when the draw ROI button is clicked"""
    qtbot.mouseClick(test_object.main_window.structures_tab.button_roi_draw, Qt.LeftButton)
    assert test_object.main_window.splitter.isHidden() is True
    assert test_object.main_window.draw_roi.isHidden() is False

    assert test_object.main_window.draw_roi is not None

    menu_items = [test_object.main_window.action_handler.action_save_structure,
                  test_object.main_window.action_handler.action_save_as_anonymous,
                  test_object.main_window.action_handler.action_one_view,
                  test_object.main_window.action_handler.action_four_views,
                  test_object.main_window.action_handler.action_show_cut_lines,
                  test_object.main_window.action_handler.action_image_fusion
                  ]

    for item in menu_items:
        assert item.isEnabled() is False

    qtbot.mouseClick(test_object.main_window.draw_roi.draw_roi_window_instance_cancel_button, Qt.LeftButton)
    assert test_object.main_window.splitter.isHidden() is False
    assert hasattr(test_object.main_window, 'draw_roi') is False

    for item in menu_items:
        assert item.isEnabled() is True


def test_change_transparency_slider_value(qtbot, test_object, init_config):
    """Function to change the value of the transparency slider, and assert that the image has been updated."""
    # Triggering draw window
    qtbot.mouseClick(test_object.main_window.structures_tab.button_roi_draw, Qt.LeftButton)
    assert test_object.main_window.draw_roi is not None
    draw_roi_window = test_object.main_window.draw_roi

    # Assert initial drawing has been created
    draw_roi_window.min_pixel_density_line_edit.setText("900")
    draw_roi_window.max_pixel_density_line_edit.setText("1000")
    draw_roi_window.onFillClicked()
    draw_roi_window.drawingROI.fill_source = [250, 250]
    draw_roi_window.drawingROI._display_pixel_color()
    post_draw_clicked_drawing = draw_roi_window.drawingROI.q_pixmaps
    assert post_draw_clicked_drawing is not None

    # Assert drawn image has been changed after slider adjustment
    draw_roi_window.transparency_slider.setValue(100)
    post_transparency_change_drawing = draw_roi_window.drawingROI.q_pixmaps
    assert post_transparency_change_drawing != post_draw_clicked_drawing

    # Run Drawing reset, prevents post test crash
    draw_roi_window.onResetClicked()


def test_manual_drawing(qtbot, test_object, init_config):
    """Function to create a drawing, press fill, press draw, and assert that the drawing is in draw "mode"."""
    # Triggering draw window
    qtbot.mouseClick(test_object.main_window.structures_tab.button_roi_draw, Qt.LeftButton)
    assert test_object.main_window.draw_roi is not None
    draw_roi_window = test_object.main_window.draw_roi

    # Assert drawing is in draw "mode"
    draw_roi_window.min_pixel_density_line_edit.setText("900")
    draw_roi_window.max_pixel_density_line_edit.setText("1000")
    qtbot.mouseClick(draw_roi_window.image_slice_number_fill_button, Qt.LeftButton)
    qtbot.mouseClick(draw_roi_window.image_slice_number_draw_button, Qt.LeftButton)
    assert draw_roi_window.keep_empty_pixel is True
    assert draw_roi_window.drawingROI.is_drawing is True

    # Run Drawing reset, prevents post test crash
    draw_roi_window.onResetClicked()


def test_roi_windowing(qtbot, test_object):
    """Tests that the windowing action items changes the draw ROI windowing display"""
    qtbot.mouseClick(test_object.main_window.structures_tab.button_roi_draw, Qt.LeftButton)
    assert test_object.main_window.draw_roi is not None
    draw_roi_window = test_object.main_window.draw_roi

    existing_window = draw_roi_window.patient_dict_container.get("window")
    existing_level = draw_roi_window.patient_dict_container.get("level")
    existing_pixmaps = draw_roi_window.patient_dict_container.get("pixmaps_axial")
    existing_view = draw_roi_window.dicom_view.scene

    # changing windowing type directly via handler
    test_object.main_window.action_handler.windowing_handler(None, "Lung")

    new_window = draw_roi_window.patient_dict_container.get("window")
    new_level = draw_roi_window.patient_dict_container.get("level")
    new_pixmaps = draw_roi_window.patient_dict_container.get("pixmaps_axial")
    new_view = draw_roi_window.dicom_view.scene

    # assert that the values have been updated
    assert existing_window != new_window
    assert existing_level != new_level
    assert existing_pixmaps != new_pixmaps
    assert existing_view != new_view

    assert draw_roi_window.dicom_view.label_wl.text() == f"W/L: {str(new_window)}/{str(new_level)}"
