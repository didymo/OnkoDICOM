from PyQt5.QtWidgets import QTreeWidgetItem


class DICOMWidgetItem(QTreeWidgetItem):
    def __init__(self, item_string, dicom_object):
        super().__init__([item_string])
        self.dicom_object = dicom_object
