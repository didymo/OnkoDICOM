from PySide6 import QtCore
from PySide6.QtWidgets import QMessageBox


class UITransferROIWindow:

    def setup_ui(self, transfer_roi_window_instance,
                 patient_A_rois, patient_B_rois, signal_roi_transferred):
        self.patient_A_rois = patient_A_rois
        self.patient_B_rois = patient_B_rois
        self.signal_roi_transferred = signal_roi_transferred
        self.transfer_roi_window_instance = transfer_roi_window_instance
        QtCore.QMetaObject.connectSlotsByName(transfer_roi_window_instance)

    def roi_transfer_saved(self):
        self.signal_roi_transferred.emit(123456)
        QMessageBox.about(self.transfer_roi_window_instance, "Saved",
                          "ROIs are successfully transferred!")
        self.closeWindow()

    def closeWindow(self):
        """
        function to close draw roi window
        """
        self.close()
