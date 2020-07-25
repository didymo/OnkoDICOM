class PatientDictContainer:

    def __init__(self, path, dataset, filepaths, **kwargs):
        """
        :param path: The path of the loaded directory.
        :param dataset: Dictionary where keys are slice number/RT modality and values are PyDicom dataset objects.
        :param filepaths: Dictionary where keys are slice number/RT modality and values are filepaths.
        :param kwargs: Any additional values that are required (e.g. rois, raw_dvh, raw_contour, etc)
        """
        self.path = path
        self.dataset = dataset
        self.filepaths = filepaths
        self.additional_data = kwargs

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

    def has(self, dicom_type):
        """
        Example usage: dicom_data.has("rtss")
        :param dicom_type: A string containing a DICOM class name as defined in ImageLoading.allowed_classes
        :return: True if dataset contains provided DICOM type.
        """
        return dicom_type in self.dataset
