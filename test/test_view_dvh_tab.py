import os
import platform
import time

import PySide6
import matplotlib
import pytest
from pathlib import Path
from PySide6 import QtWidgets
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLayout
from matplotlib.backends.backend_template import FigureCanvas
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


class TestDVHTab:
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
            dict_thickness = ImageLoading.get_thickness_dict(dataset_rtss, read_data_dict)

        if 'rtdose' in file_names_dict:
            dataset_rtdose = dcmread(file_names_dict['rtdose'])

        # Open the main window
        self.main_window = MainWindow()
        self.dvh_tab = self.main_window.dvh_tab
        self.new_polygons = {}
        self.raw_dvh = ImageLoading.multi_calc_dvh(dataset_rtss, dataset_rtdose, self.rois, dict_thickness)
        self.dvh_x_y = ImageLoading.converge_to_0_dvh(self.raw_dvh)


@pytest.fixture(scope="module")
def test_object():
    """Function to pass a shared TestStructureTab object to each test."""
    test = TestDVHTab()
    return test


def wait_for_widget(layout, timeout=1000):
    start_time = time.time()
    while time.time() - start_time < timeout/1000:
        if layout and layout.count() > 1:
            return True
        QApplication.processEvents()
        time.sleep(0.1)
    return False


def test_dvh_tab_with_dvh_not_calculated(qtbot, test_object, init_config):
    if test_object.main_window.dvh_tab.patient_dict_container.has_attribute("raw_dvh"):
        test_object.main_window.dvh_tab.patient_dict_container.additional_data.pop("raw_dvh")
    assert test_object.main_window.dvh_tab.patient_dict_container.has_attribute("raw_dvh") is False
    # check that Calculate DVH tab must appear

    test_object.main_window.show()
    layout = test_object.main_window.dvh_tab.dvh_tab_layout.itemAt(1).layout()
    print(f"First pass at Layout: {layout}")
    QTest.qWaitForWindowExposed(test_object.main_window)
    dvh_tab_layout = test_object.main_window.dvh_tab.dvh_tab_layout
    print(f"dvh_tab_layout: {dvh_tab_layout}")
    if dvh_tab_layout and layout is None:
        print(f"Number of items in dvh_tab_layout: {dvh_tab_layout.count()}")
        for i in range(dvh_tab_layout.count()):
            child_item = dvh_tab_layout.itemAt(i)
            print(f"Item {i}: {child_item}")
            if hasattr(child_item, "layout"):
                layout = child_item.layout()
                if layout is not None and layout.count() > 1:
                    break
            elif isinstance(child_item, QLayout):
                layout = child_item
                if layout.count <= 1:
                    print("Fewer than two items in this QLayout instance")
                break

    # assert wait_for_widget(layout), "Widget not found within timeout"
    print(f"Layout: {layout}")
    if layout:
        print(f"Number of items in layout: {layout.count()}")
        for i in range(layout.count()):
            print(f"Item {i}: {layout.itemAt(i)}")

    # button_calc_dvh = \
    #   test_object.main_window.dvh_tab.dvh_tab_layout.itemAt(1).layout()
    button_calc_dvh = layout.itemAt(1).widget()

    assert isinstance(button_calc_dvh, PySide6.QtWidgets.QPushButton) is True


def test_dvh_tab_with_dvh_calculated(qtbot, test_object, init_config):
    test_object.main_window.dvh_tab.patient_dict_container.set("raw_dvh", test_object.raw_dvh)
    test_object.main_window.dvh_tab.patient_dict_container.set("dvh_x_y", test_object.dvh_x_y)
    test_object.main_window.dvh_tab.patient_dict_container.set("dvh_outdated", False)

    assert test_object.main_window.dvh_tab.patient_dict_container.has_attribute("raw_dvh") is True
    # check that Calculate DVH tab must appear

    test_object.main_window = MainWindow()
    layout = test_object.main_window.dvh_tab.dvh_tab_layout
    print(f"Layout: {layout}")
    if layout:
        print(f"Number of items in layout: {layout.count()}")
        for i in range(layout.count()):
            dvh_plot = layout.itemAt(i).widget()
            print(dvh_plot)
            if isinstance(dvh_plot, matplotlib.backends.backend_qtagg.FigureCanvasQTAgg):
                break
    assert isinstance(dvh_plot, matplotlib.backends.backend_qtagg.FigureCanvasQTAgg) is True

    calculated_rois = test_object.main_window.dvh_tab.raw_dvh.keys()

    for roi in test_object.rois:
        # Only check ROIs that have been calculated
        if roi in calculated_rois:
            # Simulate checkbox set to True
            test_object.main_window.structures_tab.structure_checked(True, roi)
            selected_rois = test_object.main_window.dvh_tab.selected_rois
            if roi not in selected_rois:
                assert False

            # then simulate checkbox set to False
            test_object.main_window.structures_tab.structure_checked(False,
                                                                     roi)
            selected_rois = test_object.main_window.dvh_tab.selected_rois
            if roi in selected_rois:
                assert False
