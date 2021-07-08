import os
import pytest
import platform
import pytestqt
from PySide6 import QtGui

from src.Controller.GUIController import MainWindow
from src.Model.PatientDictContainer import PatientDictContainer
from src.View.ImageLoader import ImageLoading
from src.Model.GetPatientInfo import DicomTree

from pydicom import dcmread
from pydicom.errors import InvalidDicomError

def get_dicom_files(directory):
    """
    Function to find DICOM files in a given folder.
    :param file_path: File path of folder to search.
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
        if isinstance(value, type(dict_tree)):  # if there's an object in the row
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


@pytest.fixture
def test_tree(qtbot):
    """
    Testing Object
    :qtbot: The bot used for testing
    :return:
    """
    path_text = "/test/testdata/DICOM-RT-TEST"
    if platform.system() == "Windows":
        path_text = "\\testdata\\DICOM-RT-TEST"

    path = os.path.dirname(
        os.path.realpath(__file__)) + path_text
    files = get_dicom_files(path)
    parent_dict = os.path.dirname(os.path.commonprefix(files))
    read_data_dict, file_names_dict = ImageLoading.get_datasets(files)

    patient_dict_container = PatientDictContainer()
    patient_dict_container.clear()
    patient_dict_container.set_initial_values(parent_dict, read_data_dict,
                                              file_names_dict)
    
    i = 0
    if "rtss" in file_names_dict:
        dataset_rtss = dcmread(file_names_dict['rtss'])
        rois = ImageLoading.get_roi_info(dataset_rtss)
        patient_dict_container.set("rois", rois)

    if patient_dict_container.has_modality(
            "rtss") and patient_dict_container.has_modality("rtdose"):
        i = 1

    main_window = MainWindow()
    main_window.right_panel.setCurrentIndex(1+i) # Open to DICOM Tree Tab
    main_window.show()
    qtbot.addWidget(main_window)
    return main_window


def test_file_with_all_components(test_tree, qtbot):
    """
    Unit Test for DICOM Tree
    :test_tree: Window to be tested - DICOM Tree window
    :qtbot: The bot used for testing
    :return:
    """

    # Test headers exist and are initialised with correct names
    assert test_tree.dicom_tree.model_tree.horizontalHeaderItem(0).text() == "Name"
    assert test_tree.dicom_tree.model_tree.horizontalHeaderItem(1).text() == "Value"
    assert test_tree.dicom_tree.model_tree.horizontalHeaderItem(2).text() == "Tag"
    assert test_tree.dicom_tree.model_tree.horizontalHeaderItem(3).text() == "VM"
    assert test_tree.dicom_tree.model_tree.horizontalHeaderItem(4).text() == "VR"

    # Test initial values are correct and initial tree is clear
    file_count = len(test_tree.dicom_tree.special_files) + len(test_tree.dicom_tree.patient_dict_container.get("pixmaps"))
    assert test_tree.dicom_tree.model_tree.rowCount() == 0
    assert test_tree.dicom_tree.selector.currentIndex() == 0
    assert test_tree.dicom_tree.selector.currentText() == "Select a DICOM dataset..."

    # Check tree loaded all files from patient_dict_container
    assert test_tree.dicom_tree.selector.count() - 1 == file_count

    # Loop through each file
    for i in range(1, file_count):

        # Set program to next file -- NOTE: remake using qtbot
        test_tree.dicom_tree.selector.setCurrentIndex(i)
        test_tree.dicom_tree.item_selected(i)

        # Make New Tree to compare
        if i > len(test_tree.dicom_tree.special_files):
            index = i - len(test_tree.dicom_tree.special_files) - 1
            name = test_tree.dicom_tree.patient_dict_container.filepaths[index]
            dicom_tree_slice = DicomTree(name)
            dict_tree = dicom_tree_slice.dict
            text = "Image Slice " + str(index + 1)
            assert test_tree.dicom_tree.selector.currentText() == text

        elif test_tree.dicom_tree.special_files[i - 1] == "rtss":
            dict_tree = test_tree.dicom_tree.patient_dict_container.get(
                "dict_dicom_tree_rtss")
            assert test_tree.dicom_tree.selector.currentText() == "RT Structure Set"

        elif test_tree.dicom_tree.special_files[i - 1] == "rtdose":
            dict_tree = test_tree.dicom_tree.patient_dict_container.get(
                "dict_dicom_tree_rtdose")
            assert test_tree.dicom_tree.selector.currentText() == "RT Dose"

        elif test_tree.dicom_tree.special_files[i - 1] == "rtplan":
            dict_tree = test_tree.dicom_tree.patient_dict_container.get(
                "dict_dicom_tree_rtplan")
            assert test_tree.dicom_tree.selector.currentText() == "RT Plan"

        else:
            dict_tree = None
            print("Error filename in update_tree function")

        total_rows = test_tree.dicom_tree.recurse_build_model(
            dict_tree, test_tree.dicom_tree.model_tree.invisibleRootItem()).rowCount()

        # Check row counts of both trees are equal
        assert test_tree.dicom_tree.model_tree.rowCount() == total_rows

        # Loop Through Each Row
        parent = test_tree.dicom_tree.model_tree.invisibleRootItem()
        recursive_search(dict_tree, parent)
