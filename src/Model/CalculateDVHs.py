import datetime
import math
import multiprocessing

import numpy as np
import pandas as pd
import pydicom

from copy import deepcopy
from pathlib import Path
from dicompylercore.dvh import DVH
from dicompylercore import dvhcalc
from pydicom.dataset import Dataset, FileMetaDataset, validate_file_meta
from pydicom.sequence import Sequence
from pydicom.tag import Tag
from pydicom.uid import generate_uid, ImplicitVRLittleEndian
from src.Model.PatientDictContainer import PatientDictContainer
from src import _version

def get_roi_info(ds_rtss):
    """
    Get a dictionary of basic information of all ROIs within the dataset of
    RTSS.

    :param ds_rtss: RTSS Dataset
    :return: dict_roi {ROINumber: {ReferencedFrameOfReferenceUID, ROIName,
    ROIGenerationAlgorithm}}
    """
    # Return dict_roi
    # {"1": {'uid': '1.3.12.2.1107.5.1.4.100020.30000018082923183405900000003',
    # 'name': 'MQ', 'algorithm': 'SEMIAUTOMATIC'}
    # "1" is the ROINumber of the roi (ID)
    # 'uid' is ReferencedFrameOfReferenceUID
    # 'name' is ROIName (Name of the ROI)
    # 'algorithm' is ROIGenerationAlgorithm
    dict_roi = {}
    for sequence in ds_rtss.StructureSetROISequence:
        dict_temp = {}
        dict_temp['uid'] = sequence.ReferencedFrameOfReferenceUID
        dict_temp['name'] = sequence.ROIName
        dict_temp['algorithm'] = sequence.ROIGenerationAlgorithm
        dict_roi[sequence.ROINumber] = dict_temp
    return dict_roi


def multi_get_dvhs(rtss, dose, roi, queue, dose_limit=None):
    """
    Calculation of DVHs of a single roi using MultiProcessing.

    :param rtss: Dataset of RTSS
    :param dose: Dataset of RTDOSE
    :param roi: ROINumber
    :param queue: The queue for multiprocessing tasks
    :param dose_limit:
    """
    dvh = {}
    # Calculate dvh for the roi under dose_limit
    dvh[roi] = dvhcalc.get_dvh(rtss, dose, roi, dose_limit)
    # put the result dvh into the multiprocessing queue
    queue.put(dvh)


def calc_dvhs(rtss, rtdose, dict_roi, dose_limit=None):
    """
    Calculate dvhs of all rois using multiprocesing.

    :param rtss: Dataset of RTSS
    :param rtdose: Dataset of RTDOSE
    :param dict_roi: Dictionary of basic information of all ROIs within the
    patient
    :param dose_limit: Limit of dose
    :return: A dictionary of DVH {ROINumber: DVH}
    """
    # multiprocessing
    queue = multiprocessing.Queue()
    # List of processes
    processes = []

    # dvh dictionary
    dict_dvh = {}

    # List of all the rois within current data
    roi_list = []
    for key in dict_roi:
        roi_list.append(key)

    # Allocate tasks and add them into processes list
    for i in range(len(roi_list)):
        p = multiprocessing.Process(
            target=multi_get_dvhs, args=(rtss, rtdose, roi_list[i], queue))
        processes.append(p)
        p.start()

    # Get the results of dvh from every processes in the queue
    # And update the dictionary of dvhs
    for proc in processes:
        dvh = queue.get()
        dict_dvh.update(dvh)

    # join all the prcesses
    for proc in processes:
        proc.join()

    return dict_dvh


def converge_to_zero_dvh(dict_dvh):
    """
    Deal with the case where the last value of the DVH is not 0.

    :param dict_dvh:
    :return: A dictionary of DVH {ROINumber: DVH}
    """
    # Return a dictionary of bincenters (x axis of DVH) and counts
    # (y value of DVH)
    # {"1": {"bincenters": bincenters ; "counts": counts}}
    # "1" is the ID of the ROI
    res = {}
    zeros = np.zeros(3)

    for roi in dict_dvh:
        res[roi] = {}
        dvh = dict_dvh[roi]

        # The last value of DVH is not equal to 0
        if dvh.counts[-1] != 0:
            tmp_bincenters = []
            for i in range(3):
                tmp_bincenters.append(dvh.bincenters[-1]+i)

            tmp_bincenters = np.array(tmp_bincenters)
            tmp_bincenters = np.concatenate(
                (dvh.bincenters.flatten(), tmp_bincenters))
            bincenters = np.array(tmp_bincenters)
            counts = np.concatenate((dvh.counts.flatten(), np.array(zeros)))

        # The last value of DVH is equal to 0
        else:
            bincenters = dvh.bincenters
            counts = dvh.counts

        res[roi]['bincenters'] = bincenters
        res[roi]['counts'] = counts

    return res


def dvh2pandas(dict_dvh, patient_id):
    """
    Convert dvh data to pandas Dataframe.
    :param dict_dvh: A dictionary of DVH {ROINumber: DVH}
    :param patient_id: Patient Identifier
    :return: pddf, dvh data converted to pandas Dataframe
    """
    csv_header = []
    csv_header.append('Patient ID')
    csv_header.append('ROI')
    csv_header.append('Volume (mL)')

    dvh_csv_list = []

    # DVH.CSV EXPORT
    
    #Row in centiGray cGy
    for i in dict_dvh:
        dvh_roi_list = []
        dvh = dict_dvh[i]
        name = dvh.name
        volume = dvh.volume
        dvh_roi_list.append(patient_id)
        dvh_roi_list.append(name)
        dvh_roi_list.append(volume)
        
        dose = dvh.relative_volume.counts
        
        trough_i = 0
        peak_i = 0
        for percent in np.arange(100, -0.5, -0.5):
            last_volume = -1
            for cgy in range(trough_i, len(dose), 10):
                trough_i = cgy
                if dose[cgy] == percent:
                    last_volume = cgy
                elif dose[cgy] > percent:
                    peak_i = cgy
                elif dose[cgy] < percent:
                    break
            if last_volume == -1 and peak_i != 0:
                if dose[peak_i] != dose[trough_i]:
                    volume_per_drop = -10 * (dose[peak_i] - dose[trough_i])/(peak_i - trough_i)
                    per_drop = dose[peak_i] - percent
                    substract_amount = per_drop/volume_per_drop * 10
                    last_volume = trough_i - substract_amount
                else:
                    last_volume = trough_i
            if last_volume != -1:
                dvh_roi_list.append(str(round(last_volume)))
            else:
                dvh_roi_list.append('')
        dvh_csv_list.append(dvh_roi_list)
            
    #Column in percentage %
    for i in np.arange(100, -0.5, -0.5):
        csv_header.append(str(i) + '%')

    # Convert the list into pandas dataframe, with 2 digit rounding.
    pddf = pd.DataFrame(dvh_csv_list, columns=csv_header).round(2)
    # Fill empty blocks with 0.0
    pddf.fillna(0.0, inplace=True)
    pddf.set_index('Patient ID', inplace=True)

    # Return pandas dataframe
    return pddf


def dvh2csv(dict_dvh, path, csv_name, patient_id):
    """
    Export dvh data to csv file.
    :param dict_dvh: A dictionary of DVH {ROINumber: DVH}
    :param path: Target path of CSV export
    :param csv_name: CSV file name
    :param patient_id: Patient Identifier
    """
    # Full path of the target csv file
    tar_path = path + csv_name + '.csv'

    # Convert dvh data to pandas dataframe
    pddf_csv = dvh2pandas(dict_dvh, patient_id)

    # Convert and export pandas dataframe to CSV file
    pddf_csv.to_csv(tar_path)


def dvh2rtdose(dict_dvh):
    """
    Export dvh data to RT DOSE file.
    :param dict_dvh: A dictionary of DVH {ROINumber: DVH}
    :param patient_id: Patient Identifier
    """
    # Create DVH sequence
    dvh_sequence = Sequence([])

    # Add DVHs to the sequence
    for ds in dict_dvh:
        # Create new DVH dataset
        new_ds = Dataset()

        # Add attributes
        new_ds.add_new(Tag("DVHType"), "CS", dict_dvh[ds].dvh_type.upper())
        new_ds.add_new(Tag("DoseUnits"), "CS", dict_dvh[ds].dose_units.upper())
        new_ds.add_new(Tag("DoseType"), "CS", "PHYSICAL")
        new_ds.add_new(Tag("DVHDoseScaling"), "DS", "1.0")
        new_ds.add_new(Tag("DVHVolumeUnits"), "CS",
                       dict_dvh[ds].volume_units.upper())
        new_ds.add_new(Tag("DVHNumberOfBins"), "IS", len(dict_dvh[ds].bins))

        # Calculate and add DVH data
        dvh_data = []
        for i in range(len(dict_dvh[ds].counts)):
            dvh_data.append(str(dict_dvh[ds].bins[1]))
            dvh_data.append(str(dict_dvh[ds].counts[i]))
        new_ds.add_new(Tag("DVHData"), "DS", dvh_data)

        # Reference ROI sequence dataset/sequence
        referenced_roi_sequence = Dataset()
        referenced_roi_sequence.add_new(Tag("DVHROIContributionType"), "CS",
                                        "INCLUDED")
        referenced_roi_sequence.add_new(Tag("ReferencedROINumber"), "IS", ds)
        new_ds.add_new(Tag("DVHReferencedROISequence"), "SQ",
                       Sequence([referenced_roi_sequence]))

        # Add new DVH dataset to DVH sequences
        dvh_sequence.append(new_ds)

    # Save new RT DOSE
    patient_dict_container = PatientDictContainer()
    patient_dict_container.dataset['rtdose'].DVHSequence = dvh_sequence

    path = patient_dict_container.filepaths['rtdose']
    patient_dict_container.dataset['rtdose'].save_as(path)


def rtdose2dvh():
    """
    Gets DVH data from an RT Dose file.
    """
    # Get RT Dose
    patient_dict_container = PatientDictContainer()
    rtss = patient_dict_container.dataset['rtss']
    rt_dose = patient_dict_container.dataset['rtdose']
    dvh_seq = {"diff": False}

    # Get ROI numbers
    rois = []
    for roi in rtss['StructureSetROISequence']:
        rois.append(roi.ROINumber)
    rois.sort()

    # Try DVH referenced ROI numbers
    dvhs = []
    try:
        for dvh in rt_dose['DVHSequence']:
            dvhs.append(dvh.DVHReferencedROISequence[0].ReferencedROINumber)
        dvhs.sort()
    # RTDOSE has no DVHSequence attribute. Return.
    except KeyError:
        dvh_seq["diff"] = True
        return dvh_seq

    # If there are a different amount of ROIs to DVH sequences
    if rois != dvhs:
        # Size of ROI and DVH sequence is different.
        # alert user, ask to recalculate.
        dvh_seq["diff"] = True

    # Try to get the DVHs for each ROI
    for item in rtss["StructureSetROISequence"]:
        try:
            name = item.ROIName
            dvh = DVH.from_dicom_dvh(rt_dose, item.ROINumber, name=name)
            dvh_seq[item.ROINumber] = dvh
        except AttributeError as e:
            pass

    return dvh_seq


def create_initial_rtdose_from_ct(img_ds: pydicom.dataset.Dataset,
                                filepath: Path,
                                uid_list: list) -> pydicom.dataset.FileDataset:
    """
    Pre-populate an RT Dose  based on the volumetric image datasets.
    
    Parameters
    ----------
    img_ds : pydicom.dataset.Dataset
        A CT or MR image that the RT Dose will be registered to
    uid_list : list
        list of UIDs (as strings) of the entire image volume that the
        RT Dose references
    filepath: str
        A path where the RTDose will be saved
    Returns
    -------
    pydicom.dataset.FileDataset
        the half-baked RT Dose, ready for DVH calculations
    Raises
    ------
    ValueError
        [description]
    """

    if img_ds is None:
        raise ValueError("No CT or MR data to initialize RT Dose")

    now = datetime.datetime.now()
    dicom_date = now.strftime("%Y%m%d")
    dicom_time = now.strftime("%H%M")
    read_data_dict = PatientDictContainer().dataset

    new_image_dict = {key: value for (key, value)
                      in read_data_dict.items()
                      if str(key).isnumeric()}
    
    displacement_dict = dict()

    for i in range(1,len(new_image_dict)-1):
        delta= np.array(list(map(float,new_image_dict[i].ImagePositionPatient))) - np.array(list(map(float,new_image_dict[i-1].ImagePositionPatient)))
        displacement_dict[i] = math.sqrt(delta.dot(delta))

    # File Meta module
    file_meta = FileMetaDataset()
    file_meta.FileMetaInformationGroupLength = 238
    file_meta.FileMetaInformationVersion = b'\x00\x01'
    file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.481.2'
    file_meta.MediaStorageSOPInstanceUID = generate_uid()
    file_meta.TransferSyntaxUID = ImplicitVRLittleEndian
    validate_file_meta(file_meta)

    rt_dose = pydicom.dataset.FileDataset(filepath, {}, preamble=b"\0" * 128,
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
            rt_dose[tag] = deepcopy(img_ds[tag])

    if rt_dose.StudyInstanceUID == "":
        raise ValueError(
            "The given dataset is missing a required tag 'StudyInstanceUID'")

    # RT Series Module
    rt_dose.SeriesDate = dicom_date
    rt_dose.SeriesTime = dicom_time
    rt_dose.Modality = "RTDOSE"
    rt_dose.OperatorsName = ""
    rt_dose.SeriesInstanceUID = pydicom.uid.generate_uid()
    rt_dose.SeriesNumber = "1"

    # General Equipment Module
    rt_dose.Manufacturer = "OnkoDICOM"
    rt_dose.ManufacturerModelName = "OnkoDICOM"
    # Pull this off the top level version for OnkoDICOM
    rt_dose.SoftwareVersions = _version.__version__

    # Frame of Reference module
    rt_dose.FrameOfReferenceUID = img_ds.FrameOfReferenceUID
    rt_dose.PositionReferenceIndicator = ""

    # RT Dose  module

    rt_dose.DoseComment = "OnkoDICOM rtdose of " + rt_dose.StudyID
    rt_dose.ContentDate = dicom_date
    rt_dose.ContentTime = dicom_time
    rt_dose.SamplesPerPixel = 1
    rt_dose.PhotometricInterpretation = "MONOCHROME2"
    rt_dose.BitsAllocated = 16
    rt_dose.BitsStored = rt_dose.BitsAllocated
    rt_dose.HighBit = rt_dose.BitsStored - 1
    rt_dose.DoseUnits = "Gy"
    rt_dose.DoseType = "PHYSICAL"
    rt_dose.DoseSummationType = "PLAN"
    # assuming matching the volumetric image slice spacing
    grid_frame_offset_list = [0.0]
    grid_frame_offset_list.extend(displacement_dict.values())
    rt_dose.GridFrameOffsetVector = grid_frame_offset_list  # need to calculate this based on the volumetric image data stack
    rt_dose.DoseGridScaling = str(1.0/256.0)  # The units are gray, and we have 16 bits.  Use the top 8 bits for up to 256 Gy
    # and leave the bottom 8 bits for fractional representation down to ~ 0.25 cGy.

    # MultiFrame Module
    rt_dose.NumberOfFrames = len(new_image_dict) # use same number as volumetric image slices
    rt_dose.FrameIncrementPointer = 0x3004000C

    # Image Plane Module
    rt_dose.ImagePositionPatient = new_image_dict[0].ImagePositionPatient
    rt_dose.ImageOrientationPatient = img_ds.ImageOrientationPatient
    rt_dose.PixelRepresentation = 0

    # The first pass was to use the same pixel spacing and grid size as the image data
    # But that is a ridiculously fine grid (overly computation intensive and not how things are done in a TPS)
    # finding appropriate pixel spacing and grid size 
    
    pixel_spacing = np.array(list(map(float,img_ds.PixelSpacing)))
    image_pixel_width = pixel_spacing[0] *1.0
    min_grid_spacing = 2.0 # mm
    # max_grid_spacing = 4.0 # mm
    grid_spacing = image_pixel_width
    binary_scaling_factor = 1
    while grid_spacing < min_grid_spacing:
        grid_spacing *= 2
        binary_scaling_factor *=2
    
    # divide the thickness by the grid spacing from above to get cubic voxels.
    # That will work even if the slice spacing isn't even.
    # worst case we have to dose grid going just a bit outside the image volume
    # but... this is an empty/zero filled dose grid anyway.
    image_volume_thickness = sum(grid_frame_offset_list) 
    number_frames_with_grid_spacing = round( (image_volume_thickness / grid_spacing) +0.5)

    
    rt_dose.NumberOfFrames = int(number_frames_with_grid_spacing)
    rt_dose.GridFrameOffsetVector = [ grid_spacing * x for x in range(rt_dose.NumberOfFrames) ]
    rt_dose.PixelSpacing = [grid_spacing, grid_spacing]

    # Image Pixel Module (not including elements already specified above for RT Dose module)
    rt_dose.Rows = int(img_ds.Rows / binary_scaling_factor)
    rt_dose.Columns = int(img_ds.Columns / binary_scaling_factor)


    rt_dose.PixelData = bytes(2 * rt_dose.Rows * rt_dose.Columns * rt_dose.NumberOfFrames)

    # # Contour Image Sequence
    # contour_image_sequence = []
    # for uid in uid_list:
    #     contour_image_sequence_item = pydicom.dataset.Dataset()
    #     contour_image_sequence_item.ReferencedSOPClassUID = img_ds.SOPClassUID
    #     contour_image_sequence_item.ReferencedSOPInstanceUID = uid
    #     contour_image_sequence.append(contour_image_sequence_item)

    # # RT Referenced Series Sequence
    # rt_referenced_series = pydicom.dataset.Dataset()
    # rt_referenced_series.SeriesInstanceUID = img_ds.SeriesInstanceUID
    # rt_referenced_series.ContourImageSequence = contour_image_sequence
    # rt_referenced_series_sequence = [rt_referenced_series]

    # # RT Referenced Study Sequence
    # rt_referenced_study = pydicom.dataset.Dataset()
    # rt_referenced_study.ReferencedSOPClassUID = "1.2.840.10008.3.1.2.3.1"
    # rt_referenced_study.ReferencedSOPInstanceUID = img_ds.StudyInstanceUID
    # rt_referenced_study.RTReferencedSeriesSequence = \
    #     rt_referenced_series_sequence
    # rt_referenced_study_sequence = [rt_referenced_study]

    # # RT Referenced Frame Of Reference Sequence, Structure Set Module
    # referenced_frame_of_reference = pydicom.dataset.Dataset()
    # referenced_frame_of_reference.FrameOfReferenceUID = \
    #     img_ds.FrameOfReferenceUID
    # referenced_frame_of_reference.RTReferencedStudySequence = \
    #     rt_referenced_study_sequence
    # rt_dose.ReferencedFrameOfReferenceSequence = [referenced_frame_of_reference]

    # # Sequence modules
    # rt_dose.StructureSetROISequence = []
    # rt_dose.ROIContourSequence = []
    # rt_dose.RTROIObservationsSequence = []

    # SOP Common module
    rt_dose.SOPClassUID = rt_dose.file_meta.MediaStorageSOPClassUID
    rt_dose.SOPInstanceUID = rt_dose.file_meta.MediaStorageSOPInstanceUID

    # Add required elements
    rt_dose.InstanceCreationDate = dicom_date
    rt_dose.InstanceCreationTime = dicom_time

    rt_dose.is_little_endian = True
    rt_dose.is_implicit_VR = True
    return rt_dose
