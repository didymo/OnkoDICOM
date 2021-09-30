import os
import pytest
from pathlib import Path
from pydicom import dcmread
from pydicom.errors import InvalidDicomError
from PySide6.QtWidgets import QApplication
from src.Controller.BatchProcessingController import BatchProcessingController
from src.Model import DICOMDirectorySearch
from src.Model.batchprocessing.BatchProcessISO2ROI import BatchProcessISO2ROI
from src.Model.batchprocessing.BatchProcessROIName2FMAID import \
    BatchProcessROIName2FMAID
from src.Model.batchprocessing.BatchProcessROINameCleaning import \
    BatchProcessROINameCleaning


class TestObject:

    def __init__(self):
        self.batch_dir = Path.cwd().joinpath('test', 'batchtestdata')
        self.dicom_structure = DICOMDirectorySearch.get_dicom_structure(
                                                self.batch_dir,
                                                self.DummyProgressWindow,
                                                self.DummyProgressWindow)
        self.iso_levels = self.get_iso_levels()
        self.timestamp = BatchProcessingController.create_timestamp()
        self.application = QApplication()

    def get_patients(self):
        return self.dicom_structure.patients.values()

    @staticmethod
    def get_iso_levels():
        """
        Opens /data/csv/isodoseRoi.csv to find the isodose level names
        return list of isodose level names
        """

        path = Path.cwd().joinpath('data', 'csv', 'batch_isodoseRoi.csv')
        isodose_levels = []

        # Open isodoseRoi.csv
        with open(path, "r") as fileInput:
            index = 0
            for row in fileInput:
                items = row.split(',')
                isodose_levels.append(items[2])
                index += 1

        return isodose_levels

    class DummyProgressWindow:
        @staticmethod
        def emit(message):
            pass

        @staticmethod
        def set():
            return False

        @staticmethod
        def is_set():
            return False


@pytest.fixture(scope="module")
def test_object():
    """
    Function to pass a shared TestObject object to each test.
    """
    test = TestObject()
    return test


def test_batch_iso2roi(test_object):
    """
    Test that at least 1 new ROI is created from ISO2ROI.
    :param test_object: test_object function, for accessing the shared
                        TestObject object.
    """
    # Loop through patient datasets
    for patient in test_object.get_patients():
        # Get the files for the patient
        cur_patient_files = BatchProcessingController.get_patient_files(
            patient)

        # Create and setup the Batch Process
        process = BatchProcessISO2ROI(test_object.DummyProgressWindow,
                                      test_object.DummyProgressWindow,
                                      cur_patient_files)
        # Start the process
        process.start()

        # Get rtss
        rtss = process.patient_dict_container.dataset['rtss']

        # Get ROIS from rtss
        rois = []
        for roi in rtss.StructureSetROISequence:
            rois.append(roi.ROIName)

        # Assert rtss contains new rois
        difference = set(test_object.iso_levels) - set(rois)
        assert len(difference) > 0


def test_batch_roi_name_cleaning(test_object):
    """
    Test asserts an ROI changes name and one is deleted.
    :param test_object: test_object function, for accessing the shared
                        TestObject object.
    """
    # Loop through patient datasets
    for patient in test_object.get_patients():
        # Get RTSS file path, count number of ROIs
        rtss_path = None
        for root, dirs, files in os.walk(test_object.batch_dir, topdown=True):
            for name in files:
                try:
                    ds = dcmread(os.path.join(root, name))
                    if ds.SOPClassUID == '1.2.840.10008.5.1.4.1.1.481.3':
                        rtss_path = os.path.join(root, name)
                        break
                except (InvalidDicomError, FileNotFoundError):
                    pass

        # Assert rtss exists
        assert rtss_path is not None
        assert os.path.exists(rtss_path)

        ds = dcmread(rtss_path)
        number_rois = len(ds.StructureSetROISequence)

        # Create and setup the Batch Process
        process = BatchProcessROINameCleaning(test_object.DummyProgressWindow,
                                              test_object.DummyProgressWindow,
                                              None)

        # Set options (rename LUNGS to Lungs, delete ISO0760)
        roi_options = {'LUNGS': [[1, 'Lungs', rtss_path]],
                       'ISO0760': [[2, 'Adrenal_L', rtss_path]]}
        process.roi_options = roi_options

        # Start the process
        process.start()

        # Assert the number of ROIs decreased by one
        ds = dcmread(rtss_path)
        new_number_rois = len(ds.StructureSetROISequence)
        assert new_number_rois < number_rois

        # Assert ROI name changed
        for roi in ds.StructureSetROISequence:
            if roi.ROIName == 'Lungs':
                assert True
                return

        # Assert false if ROI name was not changed
        assert False


def test_batch_roi_name_to_fma_id(test_object):
    """
    Test asserts an ROI changes name and one is deleted.
    :param test_object: test_object function, for accessing the shared
                        TestObject object.
    """
    # Get RTSS file path, count number of ROIs
    rtss_path = None
    for root, dirs, files in os.walk(test_object.batch_dir, topdown=True):
        for name in files:
            try:
                ds = dcmread(os.path.join(root, name))
                if ds.SOPClassUID == '1.2.840.10008.5.1.4.1.1.481.3':
                    rtss_path = os.path.join(root, name)
                    break
            except (InvalidDicomError, FileNotFoundError):
                pass

    # Assert rtss exists
    assert rtss_path is not None
    assert os.path.exists(rtss_path)

    for patient in test_object.get_patients():
        # Get the files for the patient
        cur_patient_files = BatchProcessingController.get_patient_files(
            patient)

        # Create and setup the Batch Process
        process = BatchProcessROIName2FMAID(test_object.DummyProgressWindow,
                                            test_object.DummyProgressWindow,
                                            cur_patient_files)

        # Start the process
        status = process.start()
        assert status

        # Assert no ROIs called Lungs exists
        ds = dcmread(rtss_path)
        for roi in ds.StructureSetROISequence:
            assert roi.ROIName is not 'Lungs'
