import os
import pytest
from pathlib import Path

from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QSpinBox
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
        selected_files = find_DICOM_files(
            desired_path)  # list of DICOM test files
        file_path = os.path.dirname(os.path.commonprefix(
            selected_files))  # file path of DICOM files
        read_data_dict, file_names_dict = ImageLoading.get_datasets(
            selected_files)

        # Create patient dict container object
        patient_dict_container = PatientDictContainer()
        patient_dict_container.clear()
        patient_dict_container.set_initial_values(
            file_path, read_data_dict, file_names_dict)

        # Set additional attributes in patient dict container (otherwise program will crash and test will fail)
        if "rtss" in file_names_dict:
            dataset_rtss = dcmread(file_names_dict['rtss'])
            self.rois = ImageLoading.get_roi_info(dataset_rtss)
            dict_raw_contour_data, dict_numpoints = ImageLoading.get_raw_contour_data(
                dataset_rtss)
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
    qtbot.mouseClick(
        test_object.main_window.structures_tab.button_roi_draw, Qt.LeftButton)
    assert test_object.main_window.splitter.isHidden() is True
    assert test_object.main_window.draw_roi.isHidden() is False

    assert test_object.main_window.draw_roi is not None

    menu_items = [
        test_object.main_window.action_handler.action_save_structure,
        test_object.main_window.action_handler.action_save_as_anonymous,
        test_object.main_window.action_handler.action_one_view,
        test_object.main_window.action_handler.action_four_views,
        test_object.main_window.action_handler.action_show_cut_lines,
        test_object.main_window.action_handler.action_image_fusion
    ]

    for item in menu_items:
        assert item.isEnabled() is False

    # Close the ROI window
    test_object.main_window.draw_roi.close_window()

    # Assertions after closing
    assert test_object.main_window.splitter.isHidden() is False

    # Only check hidden state if the attribute still exists
    if hasattr(test_object.main_window, "draw_roi"):
        assert test_object.main_window.draw_roi.isHidden() is True

    for item in menu_items:
        assert item.isEnabled() is True


def test_change_transparency_slider_value(qtbot, test_object, init_config):
    """Test that the transparency slider affects the alpha of newly drawn pixels."""
    # Trigger the draw window
    qtbot.mouseClick(
        test_object.main_window.structures_tab.button_roi_draw, Qt.LeftButton
    )
    draw_roi_window = test_object.main_window.draw_roi
    assert draw_roi_window is not None

    mid_point = (256, 256)  # Pixel to test

    paint_bucket = True

    # First flood with alpha = 100
    opacity = draw_roi_window._toolbar.findChild(QSpinBox, "Opacity")
    assert opacity is not None
    opacity.setValue(100)
    color = draw_roi_window.pen.color()
    color.setAlpha(100)
    draw_roi_window.pen.setColor(color)

    draw_roi_window.canvas_labal.flood(mid_point, paint_bucket)
    # Update the pixmap so pixel reading is correct
    draw_roi_window.canvas_labal.setPixmap(
        draw_roi_window.canvas_labal.canvas[draw_roi_window.canvas_labal.slice_num])
    before_alpha = draw_roi_window.canvas_labal.pixmap(
    ).toImage().pixelColor(*mid_point).alpha()

    # Second flood with alpha = 50
    opacity.setValue(50)
    color = draw_roi_window.pen.color()
    color.setAlpha(50)
    draw_roi_window.pen.setColor(color)

    draw_roi_window.canvas_labal.flood(mid_point, paint_bucket)
    draw_roi_window.canvas_labal.setPixmap(
        draw_roi_window.canvas_labal.canvas[draw_roi_window.canvas_labal.slice_num])
    after_alpha = draw_roi_window.canvas_labal.pixmap(
    ).toImage().pixelColor(*mid_point).alpha()

    # Assert that the two floods produced different alpha values
    assert before_alpha != after_alpha

    # Clear canvas to ensure no conflicts with other tests
    draw_roi_window.canvas_labal.erase_roi()


def test_manual_drawing(qtbot, test_object, init_config):
    """Test that manual drawing changes the canvas where previously empty."""

    # Trigger draw window
    qtbot.mouseClick(
        test_object.main_window.structures_tab.button_roi_draw, Qt.LeftButton)
    draw_roi_window = test_object.main_window.draw_roi
    assert draw_roi_window is not None

    # Pick a test spot
    test_point = (256, 256)

    # Assert the spot is initially empty
    before_img = draw_roi_window.canvas_labal.pixmap().toImage().copy()
    assert before_img.pixelColor(test_point[0], test_point[1]).alpha() == 0

    # Ensure draw tool is active
    draw_roi_window.canvas_labal.set_tool(2)  # 2 = Tool.DRAW

    # Simulate drawing: press, move, release

    press_event = QMouseEvent(QMouseEvent.MouseButtonPress, QPoint(
        *test_point), Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
    draw_roi_window.canvas_labal.mousePressEvent(press_event)

    move_event = QMouseEvent(QMouseEvent.MouseMove, QPoint(
        test_point[0]+5, test_point[1]+5), Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
    draw_roi_window.canvas_labal.mouseMoveEvent(move_event)

    release_event = QMouseEvent(QMouseEvent.MouseButtonRelease, QPoint(
        test_point[0]+5, test_point[1]+5), Qt.LeftButton, Qt.LeftButton, Qt.NoModifier)
    draw_roi_window.canvas_labal.mouseReleaseEvent(release_event)

    # Assert the spot is now drawn on
    after_img = draw_roi_window.canvas_labal.pixmap().toImage().copy()
    assert after_img.pixelColor(test_point[0], test_point[1]).alpha() > 0

    # Clear canvas to ensure no conflicts with other tests
    draw_roi_window.canvas_labal.erase_roi()


def test_roi_windowing(qtbot, test_object):
    """Tests that the windowing action items update the draw ROI windowing display."""

    # Open the Draw ROI window
    qtbot.mouseClick(
        test_object.main_window.structures_tab.button_roi_draw, Qt.LeftButton
    )
    draw_roi_window = test_object.main_window.draw_roi
    assert draw_roi_window is not None

    # Access CanvasLabel which contains patient_dict_container
    canvas_label = draw_roi_window.canvas_labal
    assert canvas_label is not None

    # Capture existing window/level
    existing_window = canvas_label.patient_dict_container.get("window")
    existing_level = canvas_label.patient_dict_container.get("level")

    # Change windowing type via the real handler
    test_object.main_window.action_handler.windowing_handler(None, "Lung")

    # Get updated values
    new_window = canvas_label.patient_dict_container.get("window")
    new_level = canvas_label.patient_dict_container.get("level")

    # Assert that windowing values have changed
    assert existing_window != new_window, "Window should be updated via handler"
    assert existing_level != new_level, "Level should be updated via handler"
