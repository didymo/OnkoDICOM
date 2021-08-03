import os
import platform
import pytest

from src.Controller.GUIController import MainWindow
from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.ROI import get_contour_pixel
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


class TestStructureTab:
    """Class to set up the OnkoDICOM main window for testing the structures tab."""
    __test__ = False

    def __init__(self):
        # Load test DICOM files
        if platform.system() == "Windows":
            desired_path = "\\testdata\\DICOM-RT-TEST"
        elif platform.system() == "Linux" or platform.system() == "Darwin":
            desired_path = "/testdata/DICOM-RT-TEST"

        desired_path = os.path.dirname(os.path.realpath(__file__)) + desired_path

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
        self.main_window.show()

        self.dicom_view = self.main_window.dicom_single_view
        self.new_polygons = {}
        slider_id = self.dicom_view.slider.value()
        self.curr_slice = self.dicom_view.patient_dict_container.get("dict_uid")[slider_id]


@pytest.fixture(scope="module")
def test_object():
    """Function to pass a shared TestStructureTab object to each test."""
    test = TestStructureTab()
    return test


def test_structure_tab_check_checkboxes(test_object):
    """Test checking checkboxes in the structure tab. This function calculates what polygons should be drawn
    and asserts that these are the same as the polygons that are drawn.

    :param test_object: test_object function, for accessing the shared TestStructureTab object.
    """
    for roi in test_object.rois:
        # Simulate checkbox set to True
        test_object.main_window.structures_tab.structure_checked(True, roi)

        # Calculate what the dict_polygons dictionary should be
        name = test_object.rois[roi]["name"]
        test_object.new_polygons[name] = {}
        dict_rois_contours = get_contour_pixel(test_object.dicom_view.patient_dict_container.get("raw_contour"),
                                               [name],
                                               test_object.dicom_view.patient_dict_container.get("pixluts"),
                                               test_object.curr_slice)
        polygons = test_object.dicom_view.calc_roi_polygon(name, test_object.curr_slice, dict_rois_contours)
        test_object.new_polygons[name][test_object.curr_slice] = polygons

        # Get the actual dict_polygons dictionary
        view_polygons = test_object.main_window.dicom_single_view.patient_dict_container.get("dict_polygons")

        # Get the currently selected ROIs
        selected_rois = test_object.main_window.dicom_single_view.patient_dict_container.get("selected_rois")
        selected_roi_names = []
        for selected_roi in selected_rois:
            selected_roi_names.append(test_object.rois[selected_roi]["name"])

        # Assert that the actual and expected dict_polygons dictionaries are equal in length
        assert len(test_object.new_polygons) == len(view_polygons)

        # Assert that the length of the selected ROIs and the length of the calculated dictionary are the same
        assert len(test_object.new_polygons) == len(selected_rois)

        # Assert that the checked ROI is in the selected_roi_names list
        assert name in selected_roi_names

        # Assert that the actual and expected dict_polygons dictionaries are equal in value
        for key in test_object.new_polygons:
            for uid in test_object.new_polygons[key]:
                for polygon in range(0, len(test_object.new_polygons[key][uid])):
                    for point in range(0, len(test_object.new_polygons[key][uid][polygon])):
                        assert test_object.new_polygons[key][uid][polygon][point] == view_polygons[key][uid][polygon][point]


def test_structure_tab_uncheck_checkboxes(test_object):
    """Test unchecking checkboxes in the structure tab. This function asserts that the unchecked ROI is not
    flagged to be drawn into the DICOM view.

    :param test_object:
    """
    # Turn ROIs off, check change occurs in image view
    for roi in test_object.rois:
        # Simulate checkbox set to False
        test_object.main_window.structures_tab.structure_checked(False, roi)

        # Remove the element from the calculated dictionary
        name = test_object.rois[roi]["name"]
        del test_object.new_polygons[name]

        # Get the actual selected ROIs
        selected_rois = test_object.main_window.dicom_single_view.patient_dict_container.get("selected_rois")
        selected_roi_names = []
        for selected_roi in selected_rois:
            selected_roi_names.append(test_object.rois[selected_roi]["name"])

        # Assert that the length of the selected ROIs and the length of the calculated dictionary are the same
        assert len(test_object.new_polygons) == len(selected_rois)

        # Assert that the unchecked ROI is not in the selected_roi_names list
        assert name not in selected_roi_names
