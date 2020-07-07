from PyQt5.Qt import Qt

from src.Model.DICOMWidgetItem import DICOMWidgetItem


class DICOMStructure:

    def __init__(self):
        """
        patients: A list of Patient objects.
        """
        self.patients = []

    def add_patient(self, patient):
        """
        Add a Patient object to the list of patients.
        :param patient: A Patient object.
        """
        self.patients.append(patient)

    def has_patient(self, patient_id):
        """
        :param patient_id: PatientID to check.
        :return: True if patients contains patient_id.
        """
        for patient in self.patients:
            if patient_id == patient.patient_id:
                return True
        return False

    def get_patient(self, patient_id):
        for patient in self.patients:
            if patient_id == patient.patient_id:
                return patient
        return None

    def get_files(self):
        filepaths = []
        for patient in self.patients:
            filepaths += (patient.get_files())

        return filepaths

    def output_as_text(self):
        output = "DICOM structure:"
        for patient in self.patients:
            output += patient.output_as_text()

        return output

    def get_tree_items_list(self):
        """
        :return: A list of QTreeWidgetItems based on the DICOMStructure object.
        """
        new_items_list = []
        for patient in self.patients:
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
        self.studies = []

    def add_study(self, study):
        """
        Adds a Study object to the patient's list of studies.
        :param study: A Study object.
        """
        self.studies.append(study)

    def has_study(self, study_id):
        """
        :param study_id: StudyInstanceUID to check.
        :return: True if studies contains study_id
        """
        for study in self.studies:
            if study_id == study.study_id:
                return True
        return False

    def get_study(self, study_id):
        for study in self.studies:
            if study_id == study.study_id:
                return study
        return None

    def get_files(self):
        filepaths = []
        for study in self.studies:
            filepaths += (study.get_files())

        return filepaths

    def output_as_text(self):
        output = "\nPatient: %s" % self.patient_id
        for study in self.studies:
            output += study.output_as_text()

        return output

    def get_widget_item(self):
        widget_item = DICOMWidgetItem("Patient: %s (%s)" % (self.patient_name, self.patient_id), self)
        widget_item.setFlags(widget_item.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
        for study in self.studies:
            widget_item.addChild(study.get_widget_item())

        return widget_item


class Study:

    def __init__(self, study_id):
        """
        series: A list of Series objects.
        :param study_id: StudyInstanceUID in DICOM standard.
        """
        self.study_id = study_id
        self.series = []

    def add_series(self, series):
        """
        Adds a Series object to the patient's list of series.
        :param series: A Series object.
        """
        self.series.append(series)

    def has_series(self, series_id):
        """
        :param series_id: A SeriesInstanceUID to check.
        :return: True if series contains series_id.
        """
        for series in self.series:
            if series_id == series.series_id:
                return True
        return False

    def get_series(self, series_id):
        for series in self.series:
            if series_id == series.series_id:
                return series
        return None

    def get_files(self):
        filepaths = []
        for series in self.series:
            filepaths += (series.get_files())

        return filepaths

    def output_as_text(self):
        output = "\n\tStudy: %s" % self.study_id
        for series in self.series:
            output += series.output_as_text()

        return output

    def is_dicom_rt(self):
        """
        :return: True if study can be considered DICOM-RT
        """
        rt_classes = ["1.2.840.10008.5.1.4.1.1.2",          # CT Image
                      "1.2.840.10008.5.1.4.1.1.481.3",      # RT Structure Set
                      "1.2.840.10008.5.1.4.1.1.481.2",      # RT Dose
                      "1.2.840.10008.5.1.4.1.1.481.5"]      # RT Plan

        contained_classes = []
        for series in self.series:
            for image in series.images:
                image_class = image.dicom_file.SOPClassUID
                if image_class not in contained_classes:
                    contained_classes.append(image_class)

        return sorted(rt_classes) == sorted(contained_classes)

    def get_widget_item(self):
        widget_item = DICOMWidgetItem("Study: (DICOM-RT: %s)" % ("Y" if self.is_dicom_rt() else "N"), self)
        widget_item.setFlags(widget_item.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
        for series in self.series:
            widget_item.addChild(series.get_widget_item())

        return widget_item


class Series:

    def __init__(self, series_id):
        """
        images: A list of Image objects.
        :param series_id: SeriesInstanceUID in DICOM standard.
        """
        self.series_id = series_id
        self.images = []

    def add_image(self, image):
        """
        Adds an Image object to the patient's list of images.
        :param image:  An Image object.
        """
        self.images.append(image)

    def has_image(self, image_id):
        """
        :param image_id: A SOPInstanceUID to check.
        :return: True if images contains image_id.
        """
        for image in self.images:
            if image_id == image.image_id:
                return True
        return False

    def get_image(self, image_id):
        for image in self.images:
            if image_id == image.series_id:
                return image
        return None

    def get_files(self):
        filepaths = []
        for image in self.images:
            filepaths += [image.path]

        return filepaths

    def output_as_text(self):
        output = "\n\t\tSeries: %s" % self.series_id
        for image in self.images:
            output += image.output_as_text()

        return output

    def get_series_type(self):
        series_types = []
        for image in self.images:
            modality = image.dicom_file.Modality
            if modality not in series_types:
                series_types.append(modality)
        return series_types if len(series_types) > 1 else series_types[0]

    def get_widget_item(self):
        widget_item = DICOMWidgetItem("Series: %s (%s images)" % (self.get_series_type(), len(self.images)), self)
        widget_item.setFlags(widget_item.flags() | Qt.ItemIsUserCheckable)
        widget_item.setCheckState(0, Qt.Unchecked)
        return widget_item


class Image:

    def __init__(self, dicom_file, path):
        """
        image_id: SOPInstanceUID in DICOM standard.
        :param dicom_file: A PyDicom dataset.
        :param path: Path of the DICOM file.
        """
        self.dicom_file = dicom_file
        self.path = path
        self.image_id = dicom_file.SOPInstanceUID

    def output_as_text(self):
        return "\n\t\t\tImage: %s | Path: %s" % (self.image_id, self.path)
