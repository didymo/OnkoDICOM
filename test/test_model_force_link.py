"""
Test file for forcelink function.

Author: AlexanderPadayachee
"""
import os
import pytest
from src.Model.ForceLink import *


class dicomTestObject:
    __test__ = False

    def __init__(self, series_uid_in, frame_uid_in, type_in):
        self.series_uid = series_uid_in
        self.frame_of_reference_uid = frame_uid_in
        self.type = type_in

    def get_series_type(self):
        return self.type_in

    def get_instance_uid(self):
        return self.series_uid_in

@pytest.fixture(scope="module")
def test_object(series_uid_in, frame_uid_in, type_in):
    test = dicomTestObject(series_uid_in, frame_uid_in, type_in)
    return test


def test_force_link():
    """Testing for a successful case requires a directory with """
    directory = os.path.join("folderName", "fileName")
    id_test = "0.0.0.0.0"
    dicom_objects = []
    dicom_objects.append(dicomTestObject(id_test, id_test, "IMAGE"))
    dicom_objects.append(dicomTestObject(id_test, id_test, "IMAGE"))
    dicom_objects.append(dicomTestObject(id_test, id_test, "RTSTRUCT"))
    dicom_objects.append(dicomTestObject(id_test, id_test, "RTPLAN"))
    dicom_objects.append(dicomTestObject("1.1.1.1", id_test, "RTDOSE"))

    assert isinstance(force_link(id_test, directory, dicom_objects), int)
    assert force_link(id_test, directory, dicom_objects) == -1
    assert force_link(id_test, directory, dicom_objects[0]) == -1
    assert force_link(id_test, 1, dicom_objects) == -1
    assert force_link(id_test, 1, dicom_objects) == -1



