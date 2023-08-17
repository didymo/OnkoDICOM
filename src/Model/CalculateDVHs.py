import multiprocessing

from dicompylercore.dvh import DVH
import numpy as np
import pandas as pd
from dicompylercore import dvhcalc
from pydicom.dataset import Dataset
from pydicom.sequence import Sequence
from pydicom.tag import Tag
from src.Model.PatientDictContainer import PatientDictContainer


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

        current_cGy_list = ''
        current_percentage_range = 100
        for j in range(0, len(dose), 10):
            if dose[j] < current_percentage_range + 0.5 and dose[j] >= current_percentage_range:
                cGy = '[' + str(j) + 'cGy: ' + str(dose[j].round(2)) + ']'
                current_cGy_list += cGy
            else:
                dvh_roi_list.append(current_cGy_list)
                current_percentage_range -= 0.5  
                current_cGy_list = ''                  

        dvh_csv_list.append(dvh_roi_list)
    
    #Column in percentage %
    for i in np.arange(100, -0.5, -0.5):
        csv_header.append(str(i) + '%')

    # Convert the list into pandas dataframe, with 2 digit rounding.
    pddf = pd.DataFrame(dvh_csv_list).round(2)
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
