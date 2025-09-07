import pydicom
from pydicom import dcmread
from pydicom.dataset import FileMetaDataset, validate_file_meta
from pydicom.uid import generate_uid, ImplicitVRLittleEndian
from pydicom.tag import Tag
from pathlib import Path
from copy import deepcopy
import datetime

#AttributeError: 'Dataset' object has no attribute 'FrameOfReferenceUID'
#removed 2 lines relating to this error, might need to be looked at if this is required

def create_initial_rtss_from_cr(img_ds: pydicom.dataset.Dataset,
                                filepath: Path,
                                uid_list: list) -> pydicom.dataset.FileDataset:
    """
    Pre-populate an RT Structure Set based on a single CT (or MR) and a
    list of image UIDs The caller should update the Structure Set Label,
    Name, and Description, which are set to "OnkoDICOM" plus the StudyID
    from the CT, and must add Structure Set ROI Sequence, ROI Contour
    Sequence, and RT ROI Observations Sequence
    Parameters
    ----------
    img_ds : pydicom.dataset.Dataset
        A CT or MR image that the RT Structure Set will be "drawn" on
    uid_list : list
        list of UIDs (as strings) of the entire image volume that the
        RT SS references
    filepath: str
        A path where the RTStruct will be saved
    Returns
    -------
    pydicom.dataset.FileDataset
        the half-baked RT SS, ready for Structure Set ROI Sequence,
        ROI Contour Sequence, and RT ROI Observations Sequence
    Raises
    ------
    ValueError
        [description]
    """

    if img_ds is None:
        raise ValueError("No CR data to initialize RT SS")

    now = datetime.datetime.now()
    dicom_date = now.strftime("%Y%m%d")
    dicom_time = now.strftime("%H%M")

    # File Meta module
    file_meta = FileMetaDataset()
    file_meta.FileMetaInformationGroupLength = 238
    file_meta.FileMetaInformationVersion = b'\x00\x01'
    file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.481.3'
    file_meta.MediaStorageSOPInstanceUID = generate_uid()
    file_meta.TransferSyntaxUID = ImplicitVRLittleEndian
    validate_file_meta(file_meta)

    rt_ss = pydicom.dataset.FileDataset(filepath, {}, preamble=b"\0" * 128,
                                        file_meta=file_meta)

    top_level_tags_to_copy: list = [Tag("PatientName"),
                                    Tag("PatientID"),
                                    Tag("PatientBirthDate"),
                                    Tag("PatientSex"),
                                    Tag("StudyDate"),
                                    Tag("StudyTime"),
                                    Tag("AccessionNumber"),
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
                                    Tag("FrameOfReferenceUID"),
                                    Tag("PositionReferenceIndicator"),
                                    Tag("InstitutionName"),
                                    Tag("InstitutionAddress"),
                                    Tag("OperatorsName")
                                    ]

    for tag in top_level_tags_to_copy:
        if tag in img_ds:
            rt_ss[tag] = deepcopy(img_ds[tag])

    if rt_ss.StudyInstanceUID == "":
        raise ValueError(
            "The given dataset is missing a required tag 'StudyInstanceUID'")

    # RT Series Module
    rt_ss.SeriesDate = dicom_date
    rt_ss.SeriesTime = dicom_time
    rt_ss.Modality = "RTSTRUCT"
    rt_ss.OperatorsName = ""
    rt_ss.SeriesInstanceUID = pydicom.uid.generate_uid()
    rt_ss.SeriesNumber = "1"

    # General Equipment Module
    rt_ss.Manufacturer = "OnkoDICOM"
    rt_ss.ManufacturerModelName = "OnkoDICOM"
    # TODO: Pull this off build information in some way
    rt_ss.SoftwareVersions = "2021"

    # Frame of Reference module
    rt_ss.PositionReferenceIndicator = ""

    # Structure Set module
    # Best to modify the Structure Set Label with something more
    # interesting in the application. and populate the Name and
    # Description from the application also.
    rt_ss.StructureSetLabel = "OnkoDICOM rtss"
    rt_ss.StructureSetName = rt_ss.StructureSetLabel
    rt_ss.StructureSetDescription = "OnkoDICOM rtss of " + rt_ss.StudyID
    rt_ss.StructureSetDate = dicom_date
    rt_ss.StructureSetTime = dicom_time

    # Contour Image Sequence
    contour_image_sequence = []
    for uid in uid_list:
        contour_image_sequence_item = pydicom.dataset.Dataset()
        contour_image_sequence_item.ReferencedSOPClassUID = img_ds.SOPClassUID
        contour_image_sequence_item.ReferencedSOPInstanceUID = uid
        contour_image_sequence.append(contour_image_sequence_item)

    # RT Referenced Series Sequence
    rt_referenced_series = pydicom.dataset.Dataset()
    rt_referenced_series.SeriesInstanceUID = img_ds.SeriesInstanceUID
    rt_referenced_series.ContourImageSequence = contour_image_sequence
    rt_referenced_series_sequence = [rt_referenced_series]

    # RT Referenced Study Sequence
    rt_referenced_study = pydicom.dataset.Dataset()
    rt_referenced_study.ReferencedSOPClassUID = "1.2.840.10008.3.1.2.3.1"
    rt_referenced_study.ReferencedSOPInstanceUID = img_ds.StudyInstanceUID
    rt_referenced_study.RTReferencedSeriesSequence = \
        rt_referenced_series_sequence
    rt_referenced_study_sequence = [rt_referenced_study]

    # RT Referenced Frame Of Reference Sequence, Structure Set Module
    referenced_frame_of_reference = pydicom.dataset.Dataset()
    referenced_frame_of_reference.RTReferencedStudySequence = \
        rt_referenced_study_sequence
    rt_ss.ReferencedFrameOfReferenceSequence = [referenced_frame_of_reference]

    # Sequence modules
    rt_ss.StructureSetROISequence = []
    rt_ss.ROIContourSequence = []
    rt_ss.RTROIObservationsSequence = []

    # SOP Common module
    rt_ss.SOPClassUID = rt_ss.file_meta.MediaStorageSOPClassUID
    rt_ss.SOPInstanceUID = rt_ss.file_meta.MediaStorageSOPInstanceUID

    # Add required elements
    rt_ss.InstanceCreationDate = dicom_date
    rt_ss.InstanceCreationTime = dicom_time

    rt_ss.is_little_endian = True
    rt_ss.is_implicit_VR = True
    return rt_ss
