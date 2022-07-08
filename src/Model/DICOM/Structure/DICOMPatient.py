"""
DICOMPatient outlines a patient given within a DICOM file
"""
from src.Model.DICOM.DICOMWidgetItem import DICOMWidgetItem

class Patient:
    """Holds id, name and studies relating to patient"""

    def __init__(self, patient_id, patient_name):
        """
        studies: A dictionary of Study objects.
        :param patient_id: PatientID in DICOM standard.
        """
        self.patient_id = patient_id
        self.patient_name = patient_name
        self.studies = {}

    def add_study(self, study):
        """
        Adds a Study object to the patient's dictionary of studies.
        :param study: A Study object.
        """
        self.studies[study.study_uid] = study

    def has_study(self, study_uid):
        """
        :param study_uid: StudyInstanceUID to check.
        :return: True if studies contains study_uid
        """
        return study_uid in self.studies

    def get_study(self, study_uid):
        """
        :param study_uid: StudyID to check.
        :return: Study object if study found.
        """
        if self.has_study(study_uid):
            return self.studies[study_uid]
        return None

    def get_files(self):
        """
        :return: List of all filepaths in all images below this item in the
        hierarchy.
        """
        filepaths = []
        for study_uid, study in self.studies.items():
            filepaths += (study.get_files())

        return filepaths

    def output_as_text(self):
        """
        :return: Information about the object as a string
        """
        return f"Patient: {self.patient_name} ({self.patient_id})"

    def get_widget_item(self):
        """
        :return: DICOMWidgetItem to be used in a QTreeWidget.
        """
        widget_item = DICOMWidgetItem(self.output_as_text(), self)

        # Add all children of this object as children of the widget item.
        for study_uid, study in self.studies.items():
            widget_item.addChild(study.get_widget_item())
        return widget_item
