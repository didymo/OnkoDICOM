"""
DICOMSeries outlines an instance of the DICOM series that can be found within a study
"""
from PySide6.QtCore import Qt

from src.Model.DICOM.DICOMWidgetItem import DICOMWidgetItem


class Series:
    """Holds a set of images within an individual series within a DICOM study"""

    def __init__(self, series_uid):
        """
        images: A dictionary of Image objects.
        :param series_uid: SeriesInstanceUID in DICOM standard.
        """
        self.series_uid = series_uid
        self.series_description = None
        self.images = {}
        self.frame_of_reference_uid = ""

    def add_image(self, image):
        """
        Adds an Image object to the patient's dictionary of images.
        :param image:  An Image object.
        """
        self.images[image.image_uid] = image

    def add_referenced_objects(self, dicom_file):
        """Adds referenced dicom file objects to Series"""
        if "FrameOfReferenceUID" in dicom_file:
            self.frame_of_reference_uid = dicom_file.FrameOfReferenceUID
        if dicom_file.Modality == "RTSTRUCT":
            self.add_referenced_image_series(dicom_file)
        elif dicom_file.Modality == "RTPLAN":
            self.add_referenced_rtstruct(dicom_file)
        elif dicom_file.Modality == "RTDOSE":
            self.add_referenced_rtstruct(dicom_file)
            self.add_referenced_rtplan(dicom_file)
        elif dicom_file.Modality == "SR":
            self.referenced_frame_of_reference_uid = \
                dicom_file.ReferencedFrameOfReferenceUID

    def add_referenced_image_series(self, dicom_file):
        """adds referenced images to series """
        if "ReferencedFrameOfReferenceSequence" in dicom_file:
            ref_frame = dicom_file.ReferencedFrameOfReferenceSequence
            if "RTReferencedStudySequence" in ref_frame[0]:
                ref_study = ref_frame[0].RTReferencedStudySequence[0]
                if "RTReferencedSeriesSequence" in ref_study:
                    if "SeriesInstanceUID" in \
                            ref_study.RTReferencedSeriesSequence[0]:
                        ref_series = ref_study.RTReferencedSeriesSequence[0]
                        self.ref_image_series_uid = \
                            ref_series.SeriesInstanceUID
        else:
            self.ref_image_series_uid = ''

    def add_referenced_rtstruct(self, dicom_file):
        """adds referenced rtstruct to series"""
        if "ReferencedStructureSetSequence" in dicom_file:
            self.ref_rtstruct_instance_uid = \
                dicom_file.ReferencedStructureSetSequence[
                    0].ReferencedSOPInstanceUID
        else:
            self.ref_rtstruct_instance_uid = ''

    def add_referenced_rtplan(self, dicom_file):
        """adds referenced rtplan to series"""
        if "ReferencedRTPlanSequence" in dicom_file:
            self.ref_rtplan_instance_uid = \
                dicom_file.ReferencedRTPlanSequence[
                    0].ReferencedSOPInstanceUID
        else:
            self.ref_rtplan_instance_uid = ''

    def has_image(self, image_uid):
        """
        :param image_uid: A SOPInstanceUID to check.
        :return: True if images contains image_uid.
        """
        return image_uid in self.images

    def get_image(self, image_uid):
        """
        :param image_uid: ImageID to check
        :return: Image object if Image found.
        """
        if self.get_image(image_uid):
            return self.images[image_uid]
        return None

    def get_files(self):
        """
        :return: List of all filepaths in all images below this item in the
        hierarchy.
        """
        filepaths = []
        for image_uid, image in self.images.items():
            filepaths += [image.path]

        return filepaths

    def output_as_text(self):
        """
        :return: Information about the object as a string
        """
        return f"Series: {self.series_description} " \
               f"({self.get_series_type()}, {len(self.images)} images)"

    def get_series_type(self):
        """
        :return: List of string or single string containing modalities of all
        images in the series.
        """
        series_types = set()
        for image_uid, image in self.images.items():
            series_types.add(image.modality)
        return series_types if len(series_types) > 1 else series_types.pop()

    def get_instance_uid(self):
        """
        :return: List of string or single string containing instance uid of all
        images in the series.
        """
        instance_uid = []
        for image_instance_uid, image in self.images.items():
            instance_uid.append(image_instance_uid)
        return instance_uid if len(instance_uid) > 1 else instance_uid.pop()

    def get_widget_item(self):
        """
        :return: DICOMWidgetItem to be used in a QTreeWidget.
        """
        widget_item = DICOMWidgetItem(self.output_as_text(), self)
        widget_item.setFlags(widget_item.flags() | Qt.ItemIsUserCheckable)
        widget_item.setCheckState(0, Qt.Unchecked)
        return widget_item
