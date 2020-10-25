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
    """
    This Singleton class represents the model component of OnkoDICOM. It contains all data relating to the DICOM
    datasets loaded by the user into the program. Initially, the object will contain the initial values set below, and
    as different UI components are initialized and the user performs certain actions during runtime, new data will be
    added and old data will be updated. When the user chooses to open and work on a new dataset, this object will be
    completed cleaned in order to ensure that no unused data persists within the program's memory.
    """

    def __init__(self):
        # Initialize base requirements
        self.path = None                # The path of the loaded directory.
        self.dataset = None             # Dictionary of PyDicom dataset objects.
        self.filepaths = None           # Dictionary of filepaths.

        self.additional_data = None     # Any additional values that are required (e.g. rois, raw_dvh, raw_contour, etc)

    def set_base_values(self, path, dataset, filepaths, **kwargs):
        """
        Used to initialize the data on the creation of a new patient.
        :param path: The path of the loaded directory.
        :param dataset: Dictionary where keys are slice number/RT modality and values are PyDicom dataset objects.
        :param filepaths: Dictionary where keys are slice number/RT modality and values are filepaths.
        :param kwargs: Any additional values that are required (e.g. rois, raw_dvh, raw_contour, etc)
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
        Adds a new value to the additional data attribute.
        :param key: The key of the new item.
        :param value: The value of the new item.
        """
        self.additional_data[key] = value

    def get(self, keyword):
        """
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
