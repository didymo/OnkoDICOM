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


class PTCTDictContainer(metaclass=Singleton):
    def __init__(self):

        # Initialize path
        self.path = None

        # Segregate PT and CT
        self.pt_dataset = None
        self.pt_filepath = None

        self.ct_dataset = None
        self.ct_filepath = None

        # Any additional values that are required (e.g. rois, raw_dvh,
        # raw_contour, etc)
        self.additional_data = None

    def set_initial_values(self, path, **kwargs):
        """
        Used to initialize the data on the creation of a new patient.
        :param path: The path of the loaded directory.
        :param kwargs: Any additional values that are required
            (e.g. rois, raw_dvh, raw_contour, etc)
        """
        self.path = path
        self.additional_data = kwargs

        self.pt_dataset = None
        self.pt_filepath = None
        self.ct_dataset = None
        self.ct_filepath = None

    def set_sorted_files(self, pt_dataset, pt_file, ct_dataset, ct_file):
        """
        Used to store the ct and pt datasets
        :param pt_dataset: the dataset that stores pt data
        :param pt_file: the file sets used for pt_dataset
        :param ct_dataset: the dataset that stores ct data
        :param ct_file: the file sets used for ct_dataset
        """
        self.pt_dataset = pt_dataset
        self.pt_filepath = pt_file
        self.ct_dataset = ct_dataset
        self.ct_filepath = ct_file

    def clear(self):
        """
        Clears the data in order to prepare for a new patient to be
        opened.
        """
        self.path = None
        self.additional_data = None

        self.ct_dataset = None
        self.ct_filepath = None
        self.pt_dataset = None
        self.pt_filepath = None

    def is_empty(self):
        """
        :return: True if class is empty
        """
        if self.path is not None \
                or self.additional_data is not None\
                or self.ct_dataset is not None\
                or self.ct_filepath is not None\
                or self.pt_dataset is not None\
                or self.pt_filepath is not None:
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

    def has_attribute(self, attribute_key):
        """
        Example usage: dicom_data.has_attribute("raw_dvh")
        :param attribute_key: Key of the additional data to be checked
        :return: True if additional data contains given attribute key
        """
        return attribute_key in self.additional_data
