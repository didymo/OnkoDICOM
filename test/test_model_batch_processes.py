import os
import pytest
from pathlib import Path
from pydicom import dcmread
from pydicom.errors import InvalidDicomError
from PySide6.QtWidgets import QApplication
from src.Controller.BatchProcessingController import BatchProcessingController
from src.Model import DICOMDirectorySearch
from src.Model.batchprocessing.BatchProcessDVH2CSV import BatchProcessDVH2CSV
from src.Model.batchprocessing.BatchProcessISO2ROI import BatchProcessISO2ROI
from src.Model.batchprocessing.BatchProcessPyRad2CSV import \
    BatchProcessPyRadCSV
from src.Model.batchprocessing.BatchProcessROINameCleaning import \
    BatchProcessROINameCleaning


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
    """Function to pass a shared TestIso2Roi object to each test."""
    test = TestObject()
    return test


def test_batch_iso2roi(test_object):
    """
    Test that at least 1 new ROI is created from ISO2ROI.
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


# TODO test suv2roi


def test_batch_dvh2csv(test_object):
    """ Test asserts creation of .csv as result of dvh2csv conversion """

    # Loop through patient datasets
    for patient in test_object.get_patients():
        cur_patient_files = BatchProcessingController.get_patient_files(
            patient)

        # Create and setup the Batch Process
        process = BatchProcessDVH2CSV(test_object.DummyProgressWindow,
                                      test_object.DummyProgressWindow,
                                      cur_patient_files,
                                      str(test_object.batch_dir))

        # Target filename
        filename = 'DVHs_' + test_object.timestamp + '.csv'

        # Set the filename
        process.set_filename(filename)

        # Start the process
        process.start()

        # Assert the resulting .csv file exists
        assert os.path.isfile(Path.joinpath(test_object.batch_dir, 'CSV',
                                            filename))

        # Assert that there is DVH data in the RT Dose
        rtdose = process.patient_dict_container.dataset['rtdose']
        assert len(rtdose.DVHSequence) > 0


@pytest.mark.skip()
def test_batch_pyrad2csv(test_object):
    """ Test asserts creation of .csv as result of pyrad2csv conversion """

    # Loop through patient datasets
    for patient in test_object.get_patients():
        cur_patient_files = BatchProcessingController.get_patient_files(
            patient)

        # Create and setup the Batch Process
        process = BatchProcessPyRadCSV(test_object.DummyProgressWindow,
                                       test_object.DummyProgressWindow,
                                       cur_patient_files,
                                       test_object.batch_dir)

        # Target filename
        filename = 'Pyradiomics_' + test_object.timestamp + '.csv'

        # Set the filename
        process.set_filename(filename)

        # Start the process
        process.start()

        # Assert the resulting .csv file exists
        assert os.path.isfile(Path.joinpath(test_object.batch_dir, 'CSV',
                                            filename))


def test_batch_roi_name_cleaning(test_object):
    """
    Test asserts an ROI changes name and one is deleted.
    """
    # Loop through patient datasets
    for patient in test_object.get_patients():
        cur_patient_files = BatchProcessingController.get_patient_files(
            patient)

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
        roi_options = {rtss_path: [['LUNGS', 1, 'Lungs'],
                                   ['ISO0760', 2]]}
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


# TODO CSV 2 Clinical Data SR

# TODO Clinical Data SR 2 CSV
