from PySide6.QtWidgets import QTreeWidgetItem


class DICOMWidgetItem(QTreeWidgetItem):
    """
    A child of QTreeWidgetItem that contains a DICOMStructure object
    (i.e. Patient, Study, or Series object)
    """
    def __init__(self, item_string, dicom_object):
        super().__init__([item_string])
        self.dicom_object = dicom_object
