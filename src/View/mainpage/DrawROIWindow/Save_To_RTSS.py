from PySide6 import QtCore
from src.View.mainpage.DrawROIWindow.ConvertToDicom import ConvertPixmapToDicom
from src.Model import ROI
import pydicom
import time
from src.View.util.ProgressWindowHelper import connectSaveROIProgress
from src.Model.Worker import Worker

class SaveROI(QtCore.QObject):
    """Save the roi drawing into the rtss file
    Parm : dicom data = patient_dict_container.dataset
    Parm : canvas = array of pixmaps
    Parm : patient_dict_container
    """
    signal_roi_saved = QtCore.Signal(pydicom.Dataset)
    def __init__(self,dicom_data = None, canvas = None, rtss = None, has_been_draw_on = None, roi_name = None):
        self.dicom_data = dicom_data
        self.canvas = canvas
        self.has_been_draw_on = has_been_draw_on
        self.roi_name = roi_name
        self.rtss = rtss
        self.threadpool = QtCore.QThreadPool()
        self.save_roi()

    def save_roi(self):
        """Saves the roi to the thing"""
        pending_roi_list = []
        for i in self.has_been_draw_on:  # iterate all slices you drew on
            converter = ConvertPixmapToDicom(self.dicom_data[i], self.canvas[i])
            slice_roi_list = converter.start(include_holes=True, simplify_tol_px=1.0)
            pending_roi_list.extend(slice_roi_list)

        worker = Worker(ROI.create_roi, self.rtss, self.roi_name, pending_roi_list)
        worker.signals.result.connect(self.roi_saved)
        self.threadpool.start(worker)

    def roi_saved(self, result):
        self.signal_roi_saved.emit(result,self.roi_name)