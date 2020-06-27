"""
Skeleton for the interface between new boot window and existing patient window.
Intention is to replace, recreate, or reuse most of the functionality served by the ProgressBar.Extended class.
The functions in this file should be enough to generate the arguments required to create a MainWindow class.
read_data_dict, file_names_dict, rois, raw_dvh, dvh_x_y, dict_raw_contour_data, dict_numpoints, dict_pixluts.
The reason why some of these functions will be directly copied is because they currently exist as member functions
of ProgressBar.Extended class and that class is to be deprecated/refactored with the new patient selection window.
"""


def get_datasets(filepaths_list):
    """
    :param filepaths_list: List of all files to be searched.
    :return: Tuple (read_data_dict, file_names_dict)
    """


def image_stack_sort(read_data_dict, file_names_dict):
    """
    :return: Dictionaries sorted by order of displacement.
    """


def get_roi_info(dataset_rtss):
    """
    :param dataset_rtss: RTSTRUCT DICOM dataset object.
    :return: Dictionary of ROI information.
    """


def calc_dvhs(dataset_rtss, dataset_rtdose, rois):
    """
    :param dataset_rtss: RTSTRUCT DICOM dataset object.
    :param dataset_rtdose: RTDOSE DICOM dataset object.
    :param rois: Dictionary of ROI information.
    :return: Dictionary of all the DVHs of all the ROIs of the patient.
    """


def converge_to_0_dvh(raw_dvh):
    """
    :param raw_dvh: Dictionary produced by calc_dvhs(..) function.
    :return: Dictionary of bincenters and counts (x and y of DVH)
    """


def get_raw_contour_data(dataset_rtss):
    """
    :param dataset_rtss: RTSTRUCT DICOM dataset object.
    :return: Tuple (dict_roi, dict_numpoints) raw contour data of the ROIs.
    """


def get_pixluts(read_data_dict):
    """
    :param read_data_dict: Dictionary of all DICOM dataset objects.
    :return: Dictionary of pixluts for the transformation from 3D to 2D.
    """
