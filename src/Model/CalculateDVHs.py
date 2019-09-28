# import numpy as np
from dicompylercore import dvhcalc, dicomparser
# import pydicom
# import matplotlib.pyplot as plt
# from dicompylercore.dicomparser import DicomParser


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
def calc_dvhs(rtss, dose, dict_roi, dose_limit=None):
    dict_dvh = {}
    for roi in dict_roi:
        # dicompylercore.dvhcalc.get_dvh(structure, dose, roi,
        #                                   limit=None, calculate_full_volume=True, use_structure_extents=False,
        #                                   interpolation_resolution=None, interpolation_segments_between_planes=0,
        #                                   thickness=None, callback=None)
        dict_dvh[roi] = dvhcalc.get_dvh(rtss, dose, roi, dose_limit)
    return dict_dvh


# # For the demo example
# def dvh_plot(dvh):
#     plt.plot(dvh.bincenters, 100*dvh.counts/dvh.volume, label=dvh.name,
#              color=None if not isinstance(dvh.color, np.ndarray) else
#              (dvh.color / 255))
#     plt.xlabel('Dose [%s]' % dvh.dose_units)
#     plt.ylabel('Volume [%s]' % '%')
#     if dvh.name:
#         plt.legend(loc='best')
#     plt.show()
#
#
# # Example of usage
# if __name__ == '__main__':
#     path = '/home/xudong/dicom_sample/'
#     rtss_path = path + 'rtss.dcm'
#     rtdose_path = path + 'rtdose.dcm'
#
#     ds_rtdose = pydicom.dcmread(rtdose_path)
#     ds_rtss = pydicom.dcmread(rtss_path)
#
#     rois = get_roi_info(ds_rtss)
#     print(rois)
#
#     # for roi in rois:
#     #     print(rois[roi]['name'])
#
#     dvhs = calc_dvhs(ds_rtss, ds_rtdose, rois)
#     for i in dvhs:
#         print(dvhs[i])