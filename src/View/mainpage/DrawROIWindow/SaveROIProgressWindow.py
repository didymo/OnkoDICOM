import pydicom
from PySide6 import QtWidgets, QtCore

from src.Model import ROI
from src.Model.Worker import Worker


class SaveROIProgressWindow(QtWidgets.QDialog):
    """
    This class displays a window that advises the user that
    the RTSTRUCT is being modified, and then creates a new
    thread where the new RTSTRUCT is modified.
    """

    #signal_roi_saved = QtCore.Signal(object)  # Emits the new dataset
    def __init__(self, *args, **kwargs):
        super(SaveROIProgressWindow, self).__init__(*args, **kwargs)
        print("Did somthing as well")
        layout = QtWidgets.QVBoxLayout()
        text = QtWidgets.QLabel("Creating ROI...")
        layout.addWidget(text)
        self.setWindowTitle("Please wait...")
        self.setFixedWidth(150)
        self.setLayout(layout)
        self.threadpool = QtCore.QThreadPool()

    def start_saving(self, dataset_rtss, roi_name, roi_list):
        """
        Creates a thread that generates the new dataset object.
        :param dataset_rtss: dataset of RTSS
        :param roi_name: ROIName
        :param roi_list: list of contours to be saved
        """
        print("Did somthing")
        worker = Worker(ROI.create_roi, dataset_rtss, roi_name, roi_list)
        print("tried 2 help")
        worker.signals.result.connect(self.roi_saved)
        self.threadpool.start(worker)

    def roi_saved(self, result):
        """
        This method is called when the second thread completes generation of
        the new dataset object. :param result: The resulting dataset from
        the ROI.create_roi function.
        """
        #self.signal_roi_saved.emit(result)
        self.close()
