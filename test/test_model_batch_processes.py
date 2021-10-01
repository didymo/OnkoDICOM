import csv
import os
import pytest
from pathlib import Path
from pydicom import dcmread
from pydicom.errors import InvalidDicomError
from PySide6.QtWidgets import QApplication
from src.Controller.BatchProcessingController import BatchProcessingController
from src.Model import DICOMDirectorySearch
from src.Model import DICOMStructuredReport
from src.Model.batchprocessing.BatchProcessClinicalDataSR2CSV import \
    BatchProcessClinicalDataSR2CSV
from src.Model.batchprocessing.BatchProcessCSV2ClinicalDataSR import \
    BatchProcessCSV2ClinicalDataSR
from src.Model.batchprocessing.BatchProcessISO2ROI import BatchProcessISO2ROI


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


def test_batch_csv2clinicaldatasr(test_object):
    """
    Test asserts an SR is created with dummy clinical data. Test deletes
    SR after running.
    :param test_object: test_object function, for accessing the shared
                        TestObject object.
    """
    # Get patient ID for dummy CSV
    patient_id = None
    for root, dirs, files in os.walk(test_object.batch_dir, topdown=True):
        if patient_id is not None:
            break
        for name in files:
            try:
                ds = dcmread(os.path.join(root, name))
                if hasattr(ds, 'PatientID'):
                    patient_id = ds.PatientID
                    break
            except (InvalidDicomError, FileNotFoundError):
                pass

    assert patient_id is not None

    # Create dummy CSV
    csv_path = test_object.batch_dir.joinpath("dummy_cd.csv")
    data = [['MD5Hash', 'Age', 'Nationality'],
            [patient_id, '20', 'Australian']]

    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(data[0])
        writer.writerow(data[1])
        f.close()

    # Loop through each patient
    for patient in test_object.get_patients():
        # Get current patient files
        cur_patient_files = BatchProcessingController.get_patient_files(
            patient)

        # Create Batch CSV to Clinical Data SR object
        process = \
            BatchProcessCSV2ClinicalDataSR(test_object.DummyProgressWindow,
                                           test_object.DummyProgressWindow,
                                           cur_patient_files,
                                           csv_path)

        # Start the process, assert it finished successfully
        status = process.start()
        assert status

    # Assert SR exists
    sr_path = test_object.batch_dir.joinpath("Clinical-Data-SR.dcm")
    assert os.path.exists(sr_path)

    # Assert data is correct in SR
    text_data = "MD5Hash: " + patient_id + "\n"
    text_data += "Age: 20\nNationality: Australian\n"
    sr_ds = dcmread(sr_path)
    assert sr_ds.SeriesDescription == "CLINICAL-DATA"
    sr_text_data = sr_ds.ContentSequence[0].TextValue
    assert text_data == sr_text_data

    # Delete dummy CSV and SR
    os.remove(csv_path)
    os.remove(sr_path)


def test_batch_clinicaldatasr2csv(test_object):
    """
    Test asserts a CSV is created with dummy clinical data. Test deletes
    CSV after running.
    :param test_object: test_object function, for accessing the shared
                        TestObject object.
    """
    # Get patient ID for dummy SR
    patient_id = None
    for root, dirs, files in os.walk(test_object.batch_dir, topdown=True):
        if patient_id is not None:
            break
        for name in files:
            try:
                ds = dcmread(os.path.join(root, name))
                if hasattr(ds, 'PatientID') \
                        and ds.SOPClassUID == '1.2.840.10008.5.1.4.1.1.2':
                    patient_id = ds.PatientID
                    break
            except (InvalidDicomError, FileNotFoundError):
                pass

    # Assert a patient ID was found
    assert patient_id is not None

    # Create dummy SR
    dcm_path = test_object.batch_dir.joinpath("Clinical-Data-SR.dcm")
    text_data = "MD5Hash: " + patient_id + "\n"
    text_data += "Age: 20\nNationality: Australian\n"
    dicom_sr = DICOMStructuredReport.generate_dicom_sr(dcm_path, ds, text_data,
                                                       "CLINICAL-DATA")
    dicom_sr.save_as(dcm_path)

    # Assert dummy SR was created
    assert os.path.exists(dcm_path)

    # Loop through each patient
    for patient in test_object.get_patients():
        # Get current patient files
        cur_patient_files = BatchProcessingController.get_patient_files(
            patient)

        # Create Batch Clinical Data SR to CSV object
        process = \
            BatchProcessClinicalDataSR2CSV(test_object.DummyProgressWindow,
                                           test_object.DummyProgressWindow,
                                           cur_patient_files,
                                           test_object.batch_dir)

        # Start the process, assert it finished successfully
        status = process.start()
        assert status

    # Assert CSV exists
    csv_path = test_object.batch_dir.joinpath("ClinicalData.csv")
    assert os.path.exists(csv_path)

    # Assert data is correct in CSV
    with open(csv_path, newline="") as stream:
        data = list(csv.reader(stream))
        stream.close()

    assert data[0] == ["MD5Hash", "Age", "Nationality"]
    assert data[1] == [patient_id, "20", "Australian"]

    # Delete dummy CSV and SR
    os.remove(csv_path)
    os.remove(dcm_path)
