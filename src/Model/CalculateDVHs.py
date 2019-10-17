import os
import numpy as np
from dicompylercore import dvhcalc, dvh, dicomparser
import pydicom
# import matplotlib.pyplot as plt
# from dicompylercore.dicomparser import DicomParser
import multiprocessing
import pandas as pd

# Retrieve a dictionary of basic info of all ROIs
# Return value: dict
# {"1": {'uid': '1.3.12.2.1107.5.1.4.100020.30000018082923183405900000003', 'name': 'MQ', 'algorithm': 'SEMIAUTOMATIC'}
# "1" is the ROINumber of the roi (ID)
# 'uid' is ReferencedFrameOfReferenceUID
# 'name' is ROIName (Name of the ROI)
# 'algorithm' is ROIGenerationAlgorithm


def get_roi_info(ds_rtss):
    dict_roi = {}
    for sequence in ds_rtss.StructureSetROISequence:
        dict_temp = {}
        dict_temp['uid'] = sequence.ReferencedFrameOfReferenceUID
        dict_temp['name'] = sequence.ROIName
        dict_temp['algorithm'] = sequence.ROIGenerationAlgorithm
        dict_roi[sequence.ROINumber] = dict_temp
    return dict_roi


# Return a dictionary of all the DVHs of all the ROIs of the patient
# Return value: dict
# {"1": dvh}
# "1" is the ID of the ROI
# dvh is a data type defined in dicompyler-core
# For dvh plotting example with matplotlib, see: dvh_plot()
# def calc_dvhs(rtss, dose, dict_roi, dose_limit=None):
#     dict_dvh = {}
#     for roi in dict_roi:
#         # dicompylercore.dvhcalc.get_dvh(structure, dose, roi,
#         #                                   limit=None, calculate_full_volume=True, use_structure_extents=False,
#         #                # # Example of usage
# if __name__ == '__main__':
#     path = '/home/xudong/dicom_sample/'
#     rtss_path = path + 'rtss.dcm'
#     rtdose_path = path + 'rtdose.dcm'
#
#     ds_rtdose = pydicom.dcmread(rtdose_path, force = True)
#     ds_rtss = pydicom.dcmread(rtss_path, force = True)
#
#     rois = get_roi_info(ds_rtss)
#     print(rois)
#
#     # for roi in rois:
#     #     print(rois[roi]['name'])
#
#     dvhs = calc_dvhs(ds_rtss, ds_rtdose, rois)
#     for i in dvhs:
#         print(dvhs[i])                   interpolation_resolution=None, interpolation_segments_between_planes=0,
#         #                                   thickness=None, callback=None)
#         dict_dvh[roi] = dvhcalc.get_dvh(rtss, dose, roi, dose_limit)
#     return dict_dvh


# MultiProcessing Calculation of DVHs

def multi_get_dvhs(rtss, dose, roi, queue, dose_limit=None):
    dvh = {}
    dvh[roi] = dvhcalc.get_dvh(rtss, dose, roi, dose_limit)

    print("This is", roi)
    queue.put(dvh)


def calc_dvhs(rtss, rtdose, dict_roi, dose_limit=None):
    queue = multiprocessing.Queue()
    processes = []
    dict_dvh = {}

    roi_list = []
    for key in dict_roi:
        roi_list.append(key)

    for i in range(len(roi_list)):
        p = multiprocessing.Process(
            target=multi_get_dvhs, args=(rtss, rtdose, roi_list[i], queue))
        processes.append(p)
        p.start()

    for proc in processes:
        dvh = queue.get()
        dict_dvh.update(dvh)

    for proc in processes:
        proc.join()

    return dict_dvh


# Deal with the case where the last value of the DVH is not 0
# Return a dictionary of bincenters (x axis of DVH) and counts (y value of DVH)
# Return value: dict
# {"1": {"bincenters": bincenters ; "counts": counts}}
# "1" is the ID of the ROI
def converge_to_O_dvh(dict_dvh):
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


def dvh2csv(dict_dvh, path, csv_name, patientID):
    tar_path = path + csv_name + '.csv'
    dvh_csv_list = []

    csv_header = []
    csv_header.append('Patient ID')
    csv_header.append('ROI')
    csv_header.append('Volume (mL)')

    max_roi_dose = 0

    for i in dict_dvh:
        dvh_roi_list = []
        dvh = dict_dvh[i]
        name = dvh.name
        volume = dvh.volume
        dvh_roi_list.append(patientID)
        dvh_roi_list.append(name)
        dvh_roi_list.append(volume)
        dose = dvh.relative_volume.counts

        for i in range(0, len(dose), 10):
            dvh_roi_list.append(dose[i])
            if i > max_roi_dose:
                max_roi_dose = i

        dvh_csv_list.append(dvh_roi_list)

    for i in range(0, max_roi_dose + 1, 10):
        csv_header.append(str(i) + 'cGy')

    pddf_csv = pd.DataFrame(dvh_csv_list, columns=csv_header).round(2)
    pddf_csv.fillna(0.0, inplace=True)
    pddf_csv.set_index('Patient ID', inplace=True)

    pddf_csv.to_csv(tar_path)


# # Example of usage
# if __name__ == '__main__':
#     path = '/home/xudong/dicom_sample/'
#     rtss_path = path + 'rtss.dcm'
#     rtdose_path = path + 'rtdose.dcm'
#
#     ds_rtdose = pydicom.dcmread(rtdose_path, force = True)
#     ds_rtss = pydicom.dcmread(rtss_path, force = True)
#
#     rois = get_roi_info(ds_rtss)
#     print(rois)
#
#     # for roi in rois:
#     #     print(rois[roi]['name'])
#
#     dict_dvh = calc_dvhs(ds_rtss, ds_rtdose, rois)
#
#     csv_name = 'hahahahaha'
#     patientID = '007'
#     dvh2csv(dict_dvh, path, csv_name, patientID)
