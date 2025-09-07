"""
File to generate the DICOM structured report files for the given file path
"""

import datetime
from copy import deepcopy
import pydicom
from pydicom import Dataset, Sequence
from pydicom.dataset import FileMetaDataset, validate_file_meta
from pydicom.tag import Tag
from pydicom.uid import ImplicitVRLittleEndian
from src import dicom_constants

def generate_dicom_sr(file_path, img_ds, data, series_description):
    """
    Generates DICOM Structured Report files for the given file path.
    :param file_path: the file name and directory to save the DICOM
                      SR file in.
    :param img_ds: A CT or MR image from the dataset used to pull
                   general information for the DICOM SR.
    :param data: Text data to be written to the DICOM SR file.
    :param series_description: Description of text data written to SR.
    :return: dicom_sr, a dataset for the new DICOM SR file.
    """
    if img_ds is None:
        raise ValueError("No CT data to initialize RT SS")

    # Create file meta
    file_meta = FileMetaDataset()
    file_meta.FileMetaInformationGroupLength = 238
    file_meta.FileMetaInformationVersion = b'\x00\x01'
    file_meta.MediaStorageSOPClassUID = dicom_constants.COMPREHENSIVE_SR
    file_meta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()
    file_meta.TransferSyntaxUID = ImplicitVRLittleEndian
    validate_file_meta(file_meta)

    # Create dataset
    dicom_sr = pydicom.dataset.FileDataset(file_path, {}, preamble=b"\0" * 128,
                                        file_meta=file_meta)

    # Get current date and time
    now = datetime.datetime.now()
    dicom_date = now.strftime("%Y%m%d")
    dicom_time = now.strftime("%H%M")

    # List of tags to copy from CT/MR image
    top_level_tags_to_copy: list = [Tag("PatientName"),
                                    Tag("PatientID"),
                                    Tag("PatientBirthDate"),
                                    Tag("PatientSex"),
                                    Tag("StudyDate"),
                                    Tag("StudyTime"),
                                    Tag("ReferringPhysicianName"),
                                    Tag("StudyDescription"),
                                    Tag("StudyInstanceUID"),
                                    Tag("StudyID"),
                                    Tag("RequestingService"),
                                    Tag("PatientAge"),
                                    Tag("PatientSize"),
                                    Tag("PatientWeight"),
                                    Tag("MedicalAlerts"),
                                    Tag("Allergies"),
                                    Tag("PregnancyStatus"),
                                    Tag("InstitutionName"),
                                    Tag("InstitutionAddress")
                                    ]

    # Copy tags from CT/MR image
    for tag in top_level_tags_to_copy:
        if tag in img_ds:
            dicom_sr[tag] = deepcopy(img_ds[tag])

    dicom_sr.AccessionNumber = ""

    # == SR Document Series Module
    dicom_sr.SeriesDate = dicom_date
    dicom_sr.SeriesTime = dicom_time
    dicom_sr.Modality = "SR"
    dicom_sr.SeriesDescription = series_description
    # Can be empty
    referenced_performed_procedure_step_sequence = Sequence()
    dicom_sr.ReferencedPerformedProcedureStepSequence = \
        referenced_performed_procedure_step_sequence
    dicom_sr.SeriesInstanceUID = pydicom.uid.generate_uid()
    dicom_sr.SeriesNumber = 1

    # == General Equipment Module
    dicom_sr.Manufacturer = "OnkoDICOM"
    dicom_sr.ManufacturersModelName = "OnkoDICOM"
    # TODO: Pull this off build information in some way
    dicom_sr.SoftwareVersions = "2021"

    # == SR Document General Module
    dicom_sr.ContentDate = dicom_date
    dicom_sr.ContentTime = dicom_time

    dicom_sr.InstanceNumber = 1

    # Empty if unknown
    performed_procedure_code_sequence = Sequence()

    dicom_sr.PerformedProcedureCodeSequence = performed_procedure_code_sequence

    # Do not want to mark as complete in case it isn't!
    dicom_sr.CompletionFlag = "PARTIAL"
    dicom_sr.VerificationFlag = "UNVERIFIED"

    # == SR Document Content Module
    referenced_sop_sequence = Sequence([Dataset()])
    referenced_sop_sequence[0].ReferencedSOPClassUID = ''
    referenced_sop_sequence[0].ReferencedSOPInstanceUID = ''

    dicom_sr.ReferencedSOPSequence = referenced_sop_sequence
    dicom_sr.ValueType = "CONTAINER"

    dicom_sr.ContinuityOfContent = "CONTINUOUS"
    dicom_sr.TemporalRangeTime = ""
    dicom_sr.ReferencedTimeOffsets = ""
    dicom_sr.ReferencedDateTime = ""

    dicom_sr.MeasuredValueSequence = Sequence()
    dicom_sr.ReferencedFrameOfReferenceUID = deepcopy(img_ds[Tag("FrameOfReferenceUID")].value)

    # == Content Sequence
    content_sequence = Sequence([Dataset()])
    content_sequence[0].RelationshipType = 'CONTAINS'
    content_sequence[0].ValueType = 'TEXT'

    concept_name_code_sequence = Sequence([Dataset()])
    concept_name_code_sequence[0].CodeValue = ''
    concept_name_code_sequence[0].CodingSchemeDesignator = ''
    concept_name_code_sequence[0].CodeMeaning = ''
    content_sequence[0].ConceptNameCodeSequence = concept_name_code_sequence

    content_sequence[0].TextValue = data

    dicom_sr.ContentSequence = content_sequence

    # == SOP Common Module
    dicom_sr.SOPClassUID = dicom_constants.COMPREHENSIVE_SR
    dicom_sr.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID

    dicom_sr.is_little_endian = True
    dicom_sr.is_implicit_VR = True

    return dicom_sr
