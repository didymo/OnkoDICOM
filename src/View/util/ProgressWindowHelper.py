from PySide6 import QtCore

from src.View.mainpage.DrawROIWindow.SaveROIProgressWindow import \
    SaveROIProgressWindow


def connectSaveROIProgress(window, roi_list, rtss, new_roi_name,
                           roi_saved_signal):
    """
    A popup window that modifies the RTSTRUCT and tells the user
    that processing is happening.
    """
    progress_window = SaveROIProgressWindow(window, QtCore.Qt.WindowTitleHint)
    progress_window.signal_roi_saved.connect(roi_saved_signal)
    progress_window.start_saving(rtss, new_roi_name, roi_list)
    progress_window.show()


def check_interrupt_flag(interrupt_flag):
    if interrupt_flag.is_set():
        # TODO: convert print to logging
        print("Stopped ROITransfer")
        return False
    return True
