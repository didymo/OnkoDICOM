import datetime
import pydicom
from copy import deepcopy
from pydicom import Dataset, Sequence
from pydicom.dataset import FileMetaDataset, validate_file_meta
from pydicom.tag import Tag
from pydicom.uid import generate_uid, ImplicitVRLittleEndian


def generate_dicom_sr(file_path, img_ds, data):
    """
    Generates DICOM Structured Report files for the given file path.
    :param file_path: the file name and directory to save the DICOM
                      SR file in.
    :param img_ds: A CT or MR image from the dataset used to pull
                   general information for the DICOM SR.
    :param data: Text data to be written to the DICOM SR file.
    :return: dicom_sr, a dataset for the new DICOM SR file.
    """
    if img_ds is None:
        raise ValueError("No CT data to initialize RT SS")

    # Create file meta
    file_meta = FileMetaDataset()
    file_meta.FileMetaInformationGroupLength = 238
    file_meta.FileMetaInformationVersion = b'\x00\x01'
    file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.88.11'
    file_meta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()
    file_meta.TransferSyntaxUID = ImplicitVRLittleEndian
    validate_file_meta(file_meta)

    # Create dataset
    dicom_sr = pydicom.dataset.FileDataset(file_path, {}, preamble=b"\0" * 128,
                                        file_meta=file_meta)
    dicom_sr.fix_meta_info()

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
        print("Tag ", tag)
        if tag in img_ds:
            print("value of tag in image: ", img_ds[tag])
            dicom_sr[tag] = deepcopy(img_ds[tag])

    dicom_sr.AccessionNumber = ""

    # == SR Document Series Module
    dicom_sr.SeriesDate = dicom_date
    dicom_sr.SeriesTime = dicom_time
    dicom_sr.Modality = "SR"
    dicom_sr.SeriesDescription = "Optional"  #TODO replace with Clinical Data/Pyradiomics
    # Can be empty
    referenced_performed_procedure_step_sequence = Sequence()
    # Ask about these
    #referenced_performed_procedure_step_sequence[0].ReferencedSOPClassUID = ''
    #referenced_performed_procedure_step_sequence[0].ReferencedSOPInstanceUID = ''
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

    # Required if the identity of a CDA Document equivalent to the
    # current SOP Instance is known at the time of creation of this SOP
    # Instance
    # dicom_sr.ReferencedInstanceSequence = Sequence()

    dicom_sr.InstanceNumber = 1

    # Required if VerificationFlag = VERIFIED
    # dicom_sr.VerifyingObserverSequence = Sequence()

    # Required if document includes content from other documents
    # dicom_sr.PredecessorDocumentsSequence = Sequence()

    # Required if document fulfulls one+ requested procedure
    # dicom_sr.ReferencedRequestSequence = Sequence()

    # Empty if unknown
    performed_procedure_code_sequence = Sequence()

    dicom_sr.PerformedProcedureCodeSequence = performed_procedure_code_sequence

    # Required if the creator is aware of Composite Objects acquired in
    # order to satisfy the Requested Procedure(s) for which the SR
    # Document is or if Instances are referenced in the content tree
    # dicom_sr.CurrentRequestedProcedureEvidenceSequence = Sequence()

    # Required if pertinent evidence from other requested procedures
    # needs to be recorded
    # dicom_sr.PertinentOtherEvidenceSequence = Sequence()

    # Do not want to mark as complete in case it isn't!
    dicom_sr.CompletionFlag = "PARTIAL"
    dicom_sr.VerificationFlag = "UNVERIFIED"

    # Required if document stored with different SOP instance UIDs in
    # one or more other studies
    # dicom_sr.IdenticalDocumentsSequence = Sequence()

    # == SR Document Content Module
    referenced_sop_sequence = Sequence([Dataset()])
    # Ask
    referenced_sop_sequence[0].ReferencedSOPClassUID = ''
    referenced_sop_sequence[0].ReferencedSOPInstanceUID = ''

    # Required if the Referenced SOP Instance is a multi-frame image and
    # the reference does not apply to all frames, and Referenced Segment
    # Number (0062,000B) is not present.
    # referenced_sop_sequence[0].ReferencedFrameNumber = ''

    # Required if the Referenced SOP Instance is a Waveform that
    # contains multiple Channels and not all Channels in the Waveform
    # are referenced.
    # referenced_sop_sequence[0].ReferencedWaveformChannels = ''

    # Required if the Referenced SOP Instance is a Segmentation and the
    # reference does not apply to all segments and Referenced Frame
    # Number (0008,1160) is not present.
    # referenced_sop_sequence[0].ReferencedSegmentNumber = ''

    dicom_sr.ReferencedSOPSequence = referenced_sop_sequence
    dicom_sr.ValueType = "TEXT"

    concept_name_code_sequence = Sequence([Dataset()])
    # Ask
    concept_name_code_sequence[0].CodeValue = ''
    concept_name_code_sequence[0].CodingSchemeDesignator = ''
    concept_name_code_sequence[0].CodingSchemeVErsion = ''
    concept_name_code_sequence[0].CodeMeaning = ''

    dicom_sr.ConceptNameCodeSequence = concept_name_code_sequence
    dicom_sr.ContinuityOfContent = "CONTINUOUS"  # Ask
    dicom_sr.TemporalRangeTime = ""  # Ask
    dicom_sr.ReferencedTimeOffsets = ""  # Ask
    dicom_sr.ReferencedDateTime = ""  # Ask

    # Content!
    dicom_sr.TextValue = data

    concept_code_sequence = Sequence([Dataset()])
    concept_code_sequence[0].CodeValue = ''  # Ask
    concept_code_sequence[0].CodingScehemDesignator = ''  # Ask
    concept_code_sequence[0].CodingScehemVersion = ''  # Ask
    concept_code_sequence[0].CodeMeaning = 'Required'  # Ask

    dicom_sr.ConceptCodeSequence = concept_code_sequence
    dicom_sr.MeasuredValueSequence = Sequence()  # Can be empty. Ask
    og_frame_of_reference_UID = deepcopy(img_ds[Tag("FrameOfReferenceUID")].value)
    dicom_sr.ReferencedFrameOfReferenceUID = og_frame_of_reference_UID  # Ask

    # == SOP Common Module
    dicom_sr.SOPClassUID = ''  # Ask
    dicom_sr.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID

    dicom_sr.is_little_endian = True
    dicom_sr.is_implicit_VR = True

    return dicom_sr
