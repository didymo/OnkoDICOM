"""
Derived from RTStruct:
rois
raw_contour
num_points
pixluts

Derived from RTStruct and RTDose:
raw_dvh
dvh_xy
"""

from multipledispatch import dispatch


class DICOMData:

    @dispatch(str, dict, dict)
    def __init__(self, path, dataset, filepaths):
        """
        Main constructor for when the DICOM files loaded are only image files.
        :param path: The path of the loaded directory.
        :param dataset: Dictionary where keys are slice number/RT modality and values are PyDicom dataset objects.
        :param filepaths: Dictionary where keys are slice number/RT modality and values are filepaths.
        """
        self.path = path
        self.dataset = dataset
        self.filepaths = filepaths

    @dispatch(str, dict, dict, dict, dict, dict, dict)
    def __init__(self, path, dataset, filepaths, rois, raw_contour, num_points, pixluts):
        """
        Constructor for when an RT Struct file is provided.
        :param path: The path of the loaded directory.
        :param dataset: Dictionary where keys are slice number/RT modality and values are PyDicom dataset objects.
        :param filepaths: Dictionary where keys are slice number/RT modality and values are filepaths.
        :param rois: Dictionary of Regions of Interest.
        :param raw_contour: Dictionary of contour data for ROIs.
        :param num_points: Dictionary containing number of points in a ROI contour.
        :param pixluts: Dictionary of pixel LUts.
        """
        self.path = path
        self.dataset = dataset
        self.filepaths = filepaths
        self.rois = rois
        self.raw_contour = raw_contour
        self.num_points = num_points
        self.pixluts = pixluts

    @dispatch(str, dict, dict, dict, dict, dict, dict, dict, dict)
    def __init__(self, path, dataset, filepaths, rois, raw_contour, num_points, pixluts, raw_dvh, dvh_xy):
        """
        Constructor for when RT Struct and RT Dose files are provided.
        :param path: The path of the loaded directory.
        :param dataset: Dictionary where keys are slice number/RT modality and values are PyDicom dataset objects.
        :param filepaths: Dictionary where keys are slice number/RT modality and values are filepaths.
        :param rois: Dictionary of Regions of Interest.
        :param raw_contour: Dictionary of contour data for ROIs.
        :param num_points: Dictionary containing number of points in a ROI contour.
        :param pixluts: Dictionary of pixel LUts.
        :param raw_dvh: Dictionary of all DVHs for all ROIs.
        :param dvh_xy: Dictionary of bincenters and counts (x and y of DVH).
        """
        self.path = path
        self.dataset = dataset
        self.filepaths = filepaths
        self.rois = rois
        self.raw_contour = raw_contour
        self.num_points = num_points
        self.pixluts = pixluts
        self.raw_dvh = raw_dvh
        self.dvh_xy = dvh_xy

    def has(self, dicom_type):
        """
        Example usage: dicom_data.has("rtss")
        :param dicom_type: A string containing a DICOM class name as defined in ImageLoading.allowed_classes
        :return: True if dataset contains provided DICOM type.
        """
        return dicom_type in self.dataset
