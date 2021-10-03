import csv
import os
import pytest
import os.path
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
from src.Model.batchprocessing.BatchProcessDVH2CSV import BatchProcessDVH2CSV
from src.Model.batchprocessing.BatchProcessISO2ROI import BatchProcessISO2ROI
from src.Model.batchprocessing.BatchProcessPyRad2CSV import \
    BatchProcessPyRad2CSV
from src.Model.batchprocessing.BatchProcessPyrad2PyradSR import \
    BatchProcessPyRad2PyRadSR
from src.Model.batchprocessing.BatchProcessROIName2FMAID import \
    BatchProcessROIName2FMAID
from src.Model.batchprocessing.BatchProcessROINameCleaning import \
    BatchProcessROINameCleaning
from src.Model.batchprocessing.BatchProcessSUV2ROI import BatchProcessSUV2ROI


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
        result = process.start()

        # Get rtss
        if not result:
            return

        rtss = process.patient_dict_container.dataset['rtss']

        # Get ROIS from rtss
        rois = []
        for roi in rtss.StructureSetROISequence:
            rois.append(roi.ROIName)

        # Assert rtss contains new rois
        difference = set(test_object.iso_levels) - set(rois)
        assert len(difference) > 0


@pytest.mark.skip()
def test_batch_suv2roi(test_object):
    """
    Test that at least 1 new ROI is created from SUV2ROI.
    :param test_object: test_object function, for accessing the shared
                        TestObject object.
    """
    # Loop through patient datasets
    for patient in test_object.get_patients():
        # Get the files for the patient
        cur_patient_files = BatchProcessingController.get_patient_files(
            patient)

        # Create and setup the Batch Process
        patient_weight = 70000
        process = BatchProcessSUV2ROI(test_object.DummyProgressWindow,
                                      test_object.DummyProgressWindow,
                                      cur_patient_files, patient_weight)

        # Start the process
        result = process.start()

        if not result:
            return

        # Get rtss
        rtss = process.patient_dict_container.dataset['rtss']

        # Get ROIS from rtss
        rois = []
        for roi in rtss.StructureSetROISequence:
            rois.append(roi.ROIName)

        # Assert rtss contains new rois
        difference = set(test_object.iso_levels) - set(rois)
        assert len(difference) > 0


def test_batch_dvh2csv(test_object):
    """
    Test asserts creation of CSV as result of DVH2CSV conversion.
    :param test_object: test_object function, for accessing the shared
                        TestObject object.
    """
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


def test_batch_pyrad2csv(test_object):
    """
    Test asserts creation of CSV as result of PyRad2CSV conversion.
    :param test_object: test_object function, for accessing the shared
                            TestObject object.
    """
    # Loop through patient datasets
    for patient in test_object.get_patients():
        cur_patient_files = BatchProcessingController.get_patient_files(
            patient)

        # Create and setup the Batch Process
        process = BatchProcessPyRad2CSV(test_object.DummyProgressWindow,
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


def test_batch_pyrad2pyradsr(test_object):
    """
    Test that a DICOM file 'PyRadiomics-SR.dcm' is created from
    Pyrad2Pyrad-SR.
    :param test_object: test_object function, for accessing the shared
                        TestObject object.
    """
    # Loop through patient datasets
    for patient in test_object.get_patients():
        # Get the files for the patient
        cur_patient_files = \
            BatchProcessingController.get_patient_files(patient)

        # Create and setup the batch process
        process = BatchProcessPyRad2PyRadSR(test_object.DummyProgressWindow,
                                            test_object.DummyProgressWindow,
                                            cur_patient_files)

        # Start the process
        process.start()

        # Get dataset directory
        directory = process.patient_dict_container.path

        # Get Pyradiomics SR, assert it exists
        file_name = 'Pyradiomics-SR.dcm'
        path = Path(directory).joinpath(file_name)
        assert os.path.exists(str(path))

        # Delete Pyradiomics SR
        os.remove(path)


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
    sr_path = test_object.batch_dir.joinpath("DICOM-RT-02",
                                             "Clinical-Data-SR.dcm")
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

    # Reload patient (to get newly created SR)
    patients = DICOMDirectorySearch.get_dicom_structure(
        test_object.batch_dir, test_object.DummyProgressWindow,
        test_object.DummyProgressWindow)

    # Loop through each patient
    for patient in patients.patients.values():
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
        assert new_number_rois <= number_rois

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
            assert roi.ROIName != 'Lungs'
