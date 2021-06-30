from PySide6.QtCore import Qt

from src.Model.DICOMWidgetItem import DICOMWidgetItem


class DICOMStructure:
    """
    A class representing the structure of the given DICOM files.
    Used by the open patient window to generate the tree structure of the DICOM set.
    Creates a hierarchy of Patient -> can have many Studies -> which can have many Series -> which can have many Images.
    """

    def __init__(self):
        """
        patients: A list of Patient objects.
        """
        self.patients = {}

    def add_patient(self, patient):
        """
        Add a Patient object to the list of patients.
        :param patient: A Patient object.
        """
        self.patients[patient.patient_id] = patient

    def has_patient(self, patient_id):
        """
        :param patient_id: PatientID to check.
        :return: True if patients contains patient_id.
        """
        return patient_id in self.patients

    def get_patient(self, patient_id):
        """
        :param patient_id: PatientID to check.
        :return: Patient object if patient found.
        """
        if self.has_patient(patient_id):
            return self.patients[patient_id]
        return None

    def get_files(self):
        """
        :return: List of all filepaths in all images below this item in the hierarchy.
        """
        filepaths = []
        for patient_id, patient in self.patients.items():
            filepaths += (patient.get_files())

        return filepaths

    def get_tree_items_list(self):
        """
        :return: A list of QTreeWidgetItems based on the DICOMStructure object.
        """
        new_items_list = []
        for patient_id, patient in self.patients.items():
            new_items_list.append(patient.get_widget_item())

        return new_items_list


class Patient:

    def __init__(self, patient_id, patient_name):
        """
        studies: A list of Study objects.
        :param patient_id: PatientID in DICOM standard.
        """
        self.patient_id = patient_id
        self.patient_name = patient_name
        self.studies = {}

    def add_study(self, study):
        """
        Adds a Study object to the patient's list of studies.
        :param study: A Study object.
        """
        self.studies[study.study_id] = study

    def has_study(self, study_id):
        """
        :param study_id: StudyInstanceUID to check.
        :return: True if studies contains study_id
        """
        return study_id in self.studies

    def get_study(self, study_id):
        """
        :param study_id: StudyID to check.
        :return: Study object if study found.
        """
        if self.has_study(study_id):
            return self.studies[study_id]
        return None

    def get_files(self):
        """
        :return: List of all filepaths in all images below this item in the hierarchy.
        """
        filepaths = []
        for study_id, study in self.studies.items():
            filepaths += (study.get_files())

        return filepaths

    def output_as_text(self):
        """
        :return: Information about the object as a string
        """
        return "Patient: %s (%s)" % (self.patient_name, self.patient_id)

    def get_widget_item(self):
        """
        :return: DICOMWidgetItem to be used in a QTreeWidget.
        """
        widget_item = DICOMWidgetItem(self.output_as_text(), self)
        widget_item.setFlags(widget_item.flags() | Qt.ItemIsAutoTristate | Qt.ItemIsUserCheckable)

        # Add all children of this object as children of the widget item.
        for study_id, study in self.studies.items():
            widget_item.addChild(study.get_widget_item())

        return widget_item


class Study:

    def __init__(self, study_id):
        """
        series: A list of Series objects.
        :param study_id: StudyInstanceUID in DICOM standard.
        """
        self.study_id = study_id
        self.study_description = None
        self.series = {}

    def add_series(self, series):
        """
        Adds a Series object to the patient's list of series.
        :param series: A Series object.
        """
        self.series[series.series_id] = series

    def has_series(self, series_id):
        """
        :param series_id: A SeriesInstanceUID to check.
        :return: True if series contains series_id.
        """
        return series_id in self.series

    def get_series(self, series_id):
        """
        :param series_id: SeriesID to check.
        :return: Series object if series found.
        """
        if self.has_series(series_id):
            return self.series[series_id]
        return None

    def get_files(self):
        """
        :return: List of all filepaths in all images below this item in the hierarchy.
        """
        filepaths = []
        for series_id, series in self.series.items():
            filepaths += (series.get_files())

        return filepaths

    def output_as_text(self):
        """
        :return: Information about the object as a string
        """
        return "Study: %s (DICOM-RT: %s)" % (self.study_description, "Y" if self.is_dicom_rt() else "N")

    def is_dicom_rt(self):
        """
        :return: True if study can be considered DICOM-RT
        """
        rt_classes = ["1.2.840.10008.5.1.4.1.1.2",          # CT Image
                      "1.2.840.10008.5.1.4.1.1.481.3",      # RT Structure Set
                      "1.2.840.10008.5.1.4.1.1.481.2",      # RT Dose
                      "1.2.840.10008.5.1.4.1.1.481.5"]      # RT Plan

        contained_classes = []
        for series_id, series in self.series.items():
            for image_id, image in series.images.items():
                if image.class_id not in contained_classes:
                    contained_classes.append(image.class_id)

        return sorted(rt_classes) == sorted(contained_classes)

    def get_widget_item(self):
        """
        :return: DICOMWidgetItem to be used in a QTreeWidget.
        """
        widget_item = DICOMWidgetItem(self.output_as_text(), self)
        widget_item.setFlags(widget_item.flags() | Qt.ItemIsAutoTristate | Qt.ItemIsUserCheckable)

        # Add all children of this object as children of the widget item.
        for series_id, series in self.series.items():
            widget_item.addChild(series.get_widget_item())

        return widget_item


class Series:

    def __init__(self, series_id):
        """
        images: A list of Image objects.
        :param series_id: SeriesInstanceUID in DICOM standard.
        """
        self.series_id = series_id
        self.series_description = None
        self.images = {}

    def add_image(self, image):
        """
        Adds an Image object to the patient's list of images.
        :param image:  An Image object.
        """
        self.images[image.image_id] = image

    def has_image(self, image_id):
        """
        :param image_id: A SOPInstanceUID to check.
        :return: True if images contains image_id.
        """
        return image_id in self.images

    def get_image(self, image_id):
        """
        :param image_id: ImageID to check
        :return: Image object if Image found.
        """
        if self.get_image(image_id):
            return self.images[image_id]
        return None

    def get_files(self):
        """
        :return: List of all filepaths in all images below this item in the hierarchy.
        """
        filepaths = []
        for image_id, image in self.images.items():
            filepaths += [image.path]

        return filepaths

    def output_as_text(self):
        """
        :return: Information about the object as a string
        """
        return "Series: %s (%s, %s images)" % (self.series_description, self.get_series_type(), len(self.images))

    def get_series_type(self):
        """
        :return: List of string or single string containing modalities of all images in the series.
        """
        series_types = []
        for image_id, image in self.images.items():
            if image.modality not in series_types:
                series_types.append(image.modality)
        return series_types if len(series_types) > 1 else series_types[0]

    def get_widget_item(self):
        """
        :return: DICOMWidgetItem to be used in a QTreeWidget.
        """
        widget_item = DICOMWidgetItem(self.output_as_text(), self)
        widget_item.setFlags(widget_item.flags() | Qt.ItemIsUserCheckable)
        widget_item.setCheckState(0, Qt.Unchecked)
        return widget_item


class Image:

    def __init__(self, path, image_id, class_id, modality):
        """
        image_id: SOPInstanceUID in DICOM standard.
        :param dicom_file: A PyDicom dataset.
        :param path: Path of the DICOM file.
        """
        self.path = path
        self.image_id = image_id
        self.class_id = class_id
        self.modality = modality

    def output_as_text(self):
        """
        :return: Information about the object as a string
        """
        return "Image: %s | Path: %s" % (self.image_id, self.path)