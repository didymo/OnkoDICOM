import pytest
import os.path
from pathlib import Path
from PySide6.QtWidgets import QApplication
from src.Controller.BatchProcessingController import BatchProcessingController
from src.Model import DICOMDirectorySearch
from src.Model.batchprocessing.BatchProcessISO2ROI import BatchProcessISO2ROI
from src.Model.batchprocessing.BatchProcessPyrad2PyradSR import \
    BatchProcessPyRad2PyRadSR


class TestObject:

    def __init__(self):
        self.batch_dir = Path.cwd().joinpath('test', 'testdata')
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


def test_batch_pyrad2pyradsr(test_object):
    """
    Test that a DICOM file 'PyRadiomics-SR.dcm' is created from Pyrad2Pyrad-SR.
    :param test_object: test_object function, for accessing the shared
                        TestObject object.
    """
    # Loop through patient datasets
    for patient in test_object.get_patients():
        # Get the files for the patient
        cur_patient_files = BatchProcessingController.get_patient_files(
            patient)

        # Create and setup the batch process
        process = BatchProcessPyRad2PyRadSR(test_object.DummyProgressWindow,
                                            test_object.DummyProgressWindow,
                                            cur_patient_files)

        # Start the process
        process.start()

        # Get dataset directory

        directory = process.patient_dict_container.path

        file_name = 'Pyradiomics-SR.dcm'

        path = Path(directory).joinpath(file_name)

        assert os.path.exists(str(path))
