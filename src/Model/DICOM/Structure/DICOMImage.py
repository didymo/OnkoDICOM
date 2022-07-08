"""
DICOMImage outlines an instance of the DICOM image structure that can be found within a series
"""
class Image:
    """Holds an instance of an image found within a Series"""

    def __init__(self, path, image_uid, class_id, modality):
        """
        image_uid: SOPInstanceUID in DICOM standard.
        :param path: Path of the DICOM file.
        """
        self.path = path
        self.image_uid = image_uid
        self.class_id = class_id
        self.modality = modality

    def output_as_text(self):
        """
        :return: Information about the object as a string
        """
        return f"Image: {self.image_uid} | Path: {self.path}"
