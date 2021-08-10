import os
import pytest

from src.Controller.GUIController import MainWindow
from src.Model.PatientDictContainer import PatientDictContainer
from src.View.ImageLoader import ImageLoading
from src.Model.GetPatientInfo import DicomTree

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


def recursive_search(dict_tree, parent):
    """
    Recursive Function to test all rows match the data from the dictionary
    :param dict_tree: The dictionary to be compared to
    :param parent: Parent node of the DICOM Tree
    """
    count = 0  # Keep track of rows
    for key in dict_tree:
        value = dict_tree[key]  # get value from dict tree
        if isinstance(value, type(dict_tree)):  # if dict_tree object in row
            child = parent.child(count)
            recursive_search(value, child)
        else:
            # Check row matches
            assert parent.child(count, 0).text() == key
            assert parent.child(count, 1).text() == str(value[0])
            assert parent.child(count, 2).text() == str(value[1])
            assert parent.child(count, 3).text() == str(value[2])
            assert parent.child(count, 4).text() == str(value[3])
        count += 1
    return count


class TestDICOMTreeTab:
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
        self.main_window.three_dimension_view.close()

        self.main_window.right_panel.setCurrentIndex(2)
        self.dicom_tree = self.main_window.dicom_tree


@pytest.fixture
def test_obj(qtbot):
    """
    Testing Object
    :return:
    """
    test_tree = TestDICOMTreeTab()
    return test_tree


def test_file_components(test_obj):
    """
    Unit Test for DICOM Tree
    :test_tree: Window to be tested - DICOM Tree window
    :return:
    """

    # Test initial values are correct and initial tree is clear
    file_count = len(test_obj.dicom_tree.special_files) + len(
        test_obj.main_window.dicom_tree.patient_dict_container.get("pixmaps_axial"))
    assert test_obj.dicom_tree.model_tree.rowCount() == 0
    assert test_obj.dicom_tree.selector.currentIndex() == 0
    current_text = test_obj.dicom_tree.selector.currentText()
    assert current_text == "Select a DICOM dataset..."

    # Check tree loaded all files from patient_dict_container
    assert test_obj.dicom_tree.selector.count() - 1 == file_count

    # Loop through each file
    for i in range(1, file_count):

        # Set program to next file
        test_obj.dicom_tree.selector.setCurrentIndex(i)
        test_obj.dicom_tree.item_selected(i)
        current_text = test_obj.dicom_tree.selector.currentText()

        # Make New Tree to compare
        if i > len(test_obj.dicom_tree.special_files):
            index = i - len(test_obj.dicom_tree.special_files) - 1
            name = test_obj.dicom_tree.patient_dict_container.filepaths[index]
            dicom_tree_slice = DicomTree(name)
            dict_tree = dicom_tree_slice.dict
            text = "Image Slice " + str(index + 1)
            assert current_text == text

        elif test_obj.dicom_tree.special_files[i - 1] == "rtss":
            dict_tree = test_obj.dicom_tree.patient_dict_container.get(
                "dict_dicom_tree_rtss")
            assert current_text == "RT Structure Set"

        elif test_obj.dicom_tree.special_files[i - 1] == "rtdose":
            dict_tree = test_obj.dicom_tree.patient_dict_container.get(
                "dict_dicom_tree_rtdose")
            assert current_text == "RT Dose"

        elif test_obj.dicom_tree.special_files[i - 1] == "rtplan":
            dict_tree = test_obj.dicom_tree.patient_dict_container.get(
                "dict_dicom_tree_rtplan")
            assert current_text == "RT Plan"

        else:
            dict_tree = None
            print("Error filename in update_tree function")

        # Loop Through Each Row
        parent = test_obj.dicom_tree.model_tree.invisibleRootItem()
        total_count = test_obj.dicom_tree.model_tree.rowCount()
        assert recursive_search(dict_tree, parent) == total_count
