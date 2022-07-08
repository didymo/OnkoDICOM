"""
DICOMStructure outlines the parent structure of a given DICOM File
"""
class DICOMStructure:
    """
    A class representing the structure of the given DICOM files. Used by the
    open patient window to generate the tree structure of the DICOM set.
    Creates a hierarchy of Patient -> can have many Studies -> which can
    have many Series -> which can have many Images.
    """

    def __init__(self):
        """
        patients: A dictionary of Patient objects.
        """
        self.patients = {}

    def add_patient(self, patient):
        """
        Add a Patient object to the dictionary of patients.
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
        :return: List of all filepaths in all images below this item in the
        hierarchy.
        """
        filepaths = []
        for patient_id, patient in self.patients.items():
            filepaths += (patient.get_files())

        return filepaths

    def get_tree_items_list(self):
        """
        :return: A list of QTreeWidgetItems based on the DICOMStructure object.
        """
        return [patient.get_widget_item()
                for patient_id, patient in self.patients.items()]
