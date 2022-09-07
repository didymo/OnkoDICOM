import os
import pytest
from pathlib import Path
from pydicom import dcmread
from pydicom.errors import InvalidDicomError
from src.Controller.GUIController import MainWindow
from src.Controller.ROIOptionsController import RoiDrawOptions
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

        rois = patient_dict_container.get("rois")
        dataset_rtss = patient_dict_container.get("dataset_rtss")

        self.draw_window = RoiDrawOptions(rois, dataset_rtss)


@pytest.fixture(scope="module")
def test_object():
    """Function to initialise a Drawing window object."""
    test = TestDrawingMock()
    return test


def test_change_transparency_slider_value(qtbot, test_object, init_config):
    """Function to change the value of the transparency slider, and assert that the image has been updated."""
    # Assert Drawing window exists
    test_object.draw_window.show()
    assert test_object.draw_window.windowTitle() == "OnkoDICOM - Draw Region Of Interest"

    # Assert initial drawing has been created
    test_object.draw_window.min_pixel_density_line_edit.setText("900")
    test_object.draw_window.max_pixel_density_line_edit.setText("1000")
    test_object.draw_window.onDrawClicked()
    post_draw_clicked_drawing = test_object.draw_window.drawingROI.q_pixmaps
    assert post_draw_clicked_drawing is not None

    # Assert drawn image has been changed after slider adjustment
    test_object.draw_window.transparency_slider.setValue(100)
    post_transparency_change_drawing = test_object.draw_window.drawingROI.q_pixmaps
    assert post_transparency_change_drawing != post_draw_clicked_drawing

    # Run Drawing reset, prevents post test crash
    test_object.draw_window.onResetClicked()
