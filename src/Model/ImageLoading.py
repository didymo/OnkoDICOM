"""
Skeleton for the interface between new boot window and existing patient window.
Intention is to replace, recreate, or reuse most of the functionality served by the ProgressBar.Extended class.
The functions in this file should be enough to generate the arguments required to create a MainWindow class.
read_data_dict, file_names_dict, rois, raw_dvh, dvh_x_y, dict_raw_contour_data, dict_numpoints, dict_pixluts.
The reason why some of these functions will be directly copied is because they currently exist as member functions
of ProgressBar.Extended class and that class is to be deprecated/refactored with the new patient selection window.

Format for allowed_classes:

"SOPClassUID" : {
    "name" : string
    "sliceable" : bool,
    "requires" : [SOPClassUID, ..]
}

Intention of this dictionary is that as SOP Classes are made compatible with OnkoDICOM, they should be defined here.
This refactors the ProgressBar.Extended.get_datasets(..) method with the purpose of making it more future-proof than
it's current state. As it stands, every time a new SOP Class is made compatible with OnkoDICOM, a new if/else branch
needs to be added to compensate. With this new function, new SOP Classes should be added to the allowed_classes
dictionary and the get_datasets() function should not need to be added to. (Of course realistically this is not the
case, however this alternative function promotes scalability and durability of the process).
"""
import collections
import os
import re

from multiprocessing import Queue, Process
from dicompylercore import dvhcalc
from pandas import np
from pydicom import dcmread
from pydicom.errors import InvalidDicomError

allowed_classes = {
    # CT Image
    "1.2.840.10008.5.1.4.1.1.2": {
        "name": "ct",
        "sliceable": True
    },
    # RT Structure Set
    "1.2.840.10008.5.1.4.1.1.481.3": {
        "name": "rtss",
        "sliceable": False
    },
    # RT Dose
    "1.2.840.10008.5.1.4.1.1.481.2": {
        "name": "rtdose",
        "sliceable" : False
    },
    # RT Plan
    "1.2.840.10008.5.1.4.1.1.481.5": {
        "name": "rtplan",
        "sliceable" : False
    },
    # MR Image
    "1.2.840.10008.5.1.4.1.1.4" : {
        "name": "mr",
        "sliceable" : True
    },
    # PET Image
    "1.2.840.10008.5.1.4.1.1.128" : {
        "name": "pet",
        "sliceable": True
    }
}


class NotRTSetError(Exception):
    pass


class NotAllowedClassError(Exception):
    pass


def get_datasets(filepath_list):
    """
    :param filepath_list: List of all files to be searched.
    :return: Tuple (read_data_dict, file_names_dict)
    """
    read_data_dict = {}
    file_names_dict = {}

    slice_count = 0
    for file in natural_sort(filepath_list):
        try:
            read_file = dcmread(file)
        except InvalidDicomError:
            pass
        else:
            if read_file.SOPClassUID in allowed_classes:
                allowed_class = allowed_classes[read_file.SOPClassUID]
                if allowed_class["sliceable"]:
                    slice_name = slice_count
                    slice_count += 1
                else:
                    slice_name = allowed_class["name"]

                read_data_dict[slice_name] = read_file
                file_names_dict[slice_name] = file
            else:
                raise NotAllowedClassError

    return read_data_dict, file_names_dict


def is_dataset_dicom_rt(read_data_dict):
    """
    Tests if a read_data_dict produced by get_datasets(..) is a DICOM-RT set.
    :param read_data_dict: Dictionary of DICOM dataset objects.
    :return:  True if read_data_dict can be considered a complete DICOM-RT object.
    """
    class_names = []

    for key, item in read_data_dict.items():
        if allowed_classes[item.SOPClassUID]["name"] not in class_names:
            class_names.append(allowed_classes[item.SOPClassUID]["name"])

    class_names.sort()
    return class_names == ["ct", "rtdose", "rtplan", "rtss"]


def natural_sort(strings):
    """
    Sort filenames.
    :param strings:   List of strings.
    :return: Sorted list of strings.
    """
    def convert(text): return int(text) if text.isdigit() else text.lower()

    def alphanum_key(key): return [convert(c) for c in re.split('([0-9]+)', key)]

    return sorted(strings, key=alphanum_key)


def get_roi_info(dataset_rtss):
    """
    :param dataset_rtss: RTSTRUCT DICOM dataset object.
    :return: Dictionary of ROI information.
    """
    dict_roi = {}
    for sequence in dataset_rtss.StructureSetROISequence:
        dict_temp = {}
        dict_temp['uid'] = sequence.ReferencedFrameOfReferenceUID
        dict_temp['name'] = sequence.ROIName
        dict_temp['algorithm'] = sequence.ROIGenerationAlgorithm
        dict_roi[sequence.ROINumber] = dict_temp

    return dict_roi


def calc_dvhs(dataset_rtss, dataset_rtdose, rois, dose_limit=None):
    """
    :param dataset_rtss: RTSTRUCT DICOM dataset object.
    :param dataset_rtdose: RTDOSE DICOM dataset object.
    :param rois: Dictionary of ROI information.
    :param dose_limit: Limit of dose for DVH calculation.
    :return: Dictionary of all the DVHs of all the ROIs of the patient.
    """
    dict_dvh = {}
    roi_list = []
    for key in rois:
        roi_list.append(key)

    for roi in roi_list:
        dict_dvh[roi] = dvhcalc.get_dvh(dataset_rtss, dataset_rtdose, roi, dose_limit)

    return dict_dvh


def calc_dvh_worker(rtss, dose, roi, queue, dose_limit=None):
    dvh = {}
    dvh[roi] = dvhcalc.get_dvh(rtss, dose, roi, dose_limit)
    queue.put(dvh)


def multi_calc_dvh(dataset_rtss, dataset_rtdose, rois, dose_limit=None):
    """
    Multiprocessing variant of calc_dvh for fork-based platforms.
    """
    queue = Queue()
    processes = []
    dict_dvh = {}

    roi_list = []
    for key in rois:
        roi_list.append(key)

    for i in range(len(roi_list)):
        p = Process(target=calc_dvh_worker, args=(dataset_rtss, dataset_rtdose, roi_list[i], queue, dose_limit,))
        processes.append(p)
        p.start()

    for process in processes:
        dvh = queue.get()
        dict_dvh.update(dvh)

    for process in processes:
        process.join()

    return dict_dvh


def converge_to_0_dvh(raw_dvh):
    """
    :param raw_dvh: Dictionary produced by calc_dvhs(..) function.
    :return: Dictionary of bincenters and counts (x and y of DVH)
    """
    res = {}
    zeros = np.zeros(3)
    for roi in raw_dvh:
        res[roi] = {}
        dvh = raw_dvh[roi]

        # The last value of DVH is not equal to 0
        if dvh.counts[-1] != 0:
            tmp_bincenters = []
            for i in range(3):
                tmp_bincenters.append(dvh.bincenters[-1] + i)

            tmp_bincenters = np.array(tmp_bincenters)
            tmp_bincenters = np.concatenate(
                (dvh.bincenters.flatten(), tmp_bincenters))
            bincenters = np.array(tmp_bincenters)
            counts = np.concatenate(
                (dvh.counts.flatten(), np.array(zeros)))

        # The last value of DVH is equal to 0
        else:
            bincenters = dvh.bincenters
            counts = dvh.counts

        res[roi]['bincenters'] = bincenters
        res[roi]['counts'] = counts

    return res


def get_raw_contour_data(dataset_rtss):
    """
    :param dataset_rtss: RTSTRUCT DICOM dataset object.
    :return: Tuple (dict_roi, dict_numpoints) raw contour data of the ROIs.
    """
    dict_id = {}
    for i, elem in enumerate(dataset_rtss.StructureSetROISequence):
        roi_number = elem.ROINumber
        roi_name = elem.ROIName
        dict_id[roi_number] = roi_name

    dict_roi = {}
    dict_numpoints = {}
    for roi in dataset_rtss.ROIContourSequence:
        if 'ROIDisplayColor' in roi:
            ROIDisplayColor = roi.ROIDisplayColor
            ReferencedROINumber = roi.ReferencedROINumber
            ROIName = dict_id[ReferencedROINumber]
            dict_contour = collections.defaultdict(list)
            roi_points_count = 0
            if 'ContourSequence' in roi:
                for slice in roi.ContourSequence:
                    if 'ContourImageSequence' in slice:
                        for contour_img in slice.ContourImageSequence:
                            ReferencedSOPInstanceUID = contour_img.ReferencedSOPInstanceUID
                        ContourGeometricType = slice.ContourGeometricType
                        NumberOfContourPoints = slice.NumberOfContourPoints
                        roi_points_count += int(NumberOfContourPoints)
                        ContourData = slice.ContourData
                        dict_contour[ReferencedSOPInstanceUID].append(ContourData)
            dict_roi[ROIName] = dict_contour
            dict_numpoints[ROIName] = roi_points_count

    return dict_roi, dict_numpoints


def calculate_matrix(img_ds):
    # Physical distance (in mm) between the center of each image pixel, specified by a numeric pair
    # - adjacent row spacing (delimiter) adjacent column spacing.
    dist_row = img_ds.PixelSpacing[0]
    dist_col = img_ds.PixelSpacing[1]
    # The direction cosines of the first row and the first column with respect to the patient.
    # 6 values inside: [Xx, Xy, Xz, Yx, Yy, Yz]
    orientation = img_ds.ImageOrientationPatient
    # The x, y, and z coordinates of the upper left hand corner
    # (center of the first voxel transmitted) of the image, in mm.
    # 3 values: [Sx, Sy, Sz]
    position = img_ds.ImagePositionPatient

    # Equation C.7.6.2.1-1.
    # https://dicom.innolitics.com/ciods/rt-structure-set/roi-contour/30060039/30060040/30060050
    matrix_M = np.matrix(
        [[orientation[0] * dist_row, orientation[3] * dist_col, 0, position[0]],
         [orientation[1] * dist_row, orientation[4] * dist_col, 0, position[1]],
         [orientation[2] * dist_row, orientation[5] * dist_col, 0, position[2]],
         [0, 0, 0, 1]]
    )
    x = []
    y = []
    for i in range(0, img_ds.Columns):
        i_mat = matrix_M * np.matrix([[i], [0], [0], [1]])
        x.append(float(i_mat[0]))

    for j in range(0, img_ds.Rows):
        j_mat = matrix_M * np.matrix([[0], [j], [0], [1]])
        y.append(float(j_mat[1]))

    return np.array(x), np.array(y)


def get_pixluts(read_data_dict):
    """
    :param read_data_dict: Dictionary of all DICOM dataset objects.
    :return: Dictionary of pixluts for the transformation from 3D to 2D.
    """
    dict_pixluts = {}
    non_img_type = ['rtdose', 'rtplan', 'rtss']
    for ds in read_data_dict:
        if ds not in non_img_type:
            img_ds = read_data_dict[ds]
            pixlut = calculate_matrix(img_ds)
            dict_pixluts[img_ds.SOPInstanceUID] = pixlut

    return dict_pixluts
