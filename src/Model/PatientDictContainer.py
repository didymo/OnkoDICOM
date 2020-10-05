"""
Base requirements for OnkoDICOM to run:
    path
    dataset
    filepaths

Keyword arguments for DICOM-RT:
    rois
    raw_dvh
    dvh_x_y
    raw_contour
    num_points
    pixluts
"""
from src.Model.Singleton import Singleton


class PatientDictContainer(metaclass=Singleton):

    def __init__(self):
        # Initialize base requirements
        self.path = None                # The path of the loaded directory.
        self.dataset = None             # Dictionary of PyDicom dataset objects.
        self.filepaths = None           # Dictionary of filepaths.

        self.additional_data = None     # Any additional values that are required (e.g. rois, raw_dvh, raw_contour, etc)

    def set_base_values(self, path, dataset, filepaths, **kwargs):
        """
        Used to initialize the data on the creation of a new patient.
        :param path:
        :param dataset:
        :param filepaths:
        :param kwargs:
        :return:
        """
        self.path = path
        self.dataset = dataset
        self.filepaths = filepaths
        self.additional_data = kwargs

    def clear(self):
        """
        Clears the data in order to prepare for a new patient to be opened.
        """
        self.path = None
        self.dataset = None
        self.filepaths = None
        self.additional_data = None

    def is_empty(self):
        """
        :return: True if class is empty
        """
        if self.path is not None:
            return False
        if self.dataset is not None:
            return False
        if self.filepaths is not None:
            return False
        if self.additional_data is not None:
            return False

        return True

    def set(self, key, value):
        """
        Sets new attribute to the keyword arguments.
        """
        self.additional_data[key] = value

    def get(self, keyword):
        """
        TODO This method may not be necessary
        Gets a keyword argument and returns it.
        Example usages:
        patient_dict_container.get("rois")
        patient_dict_container.get("raw_dvh")
        :param keyword: Keyword argument to look for.
        :return: Value if keyword found, else None.
        """
        return self.additional_data.get(keyword)

    def has_modality(self, dicom_type):
        """
        Example usage: dicom_data.has_modality("rtss")
        :param dicom_type: A string containing a DICOM class name as defined in ImageLoading.allowed_classes
        :return: True if dataset contains provided DICOM type.
        """
        return dicom_type in self.dataset

    def has_attribute(self, attribute_key):
        """
        Example usage: dicom_data.has_attribute("raw_dvh")
        :param attribute_key: Key of the additional data to be checked
        :return: True if additional data contains given attribute key
        """
        return attribute_key in self.additional_data
