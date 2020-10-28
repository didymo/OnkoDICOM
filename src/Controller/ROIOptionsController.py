from src.View.mainpage.DeleteROIWindow import *
from src.View.mainpage.DrawROIWindow import *


class RoiDeleteOptions(QtWidgets.QMainWindow, UIDeleteROIWindow):
    """
    Create the ROI Delete Options class based on the UI from the file in View/ROI Delete Option
    """
    deleting_rois_structure_tuple = QtCore.pyqtSignal(tuple)  # new PyDicom dataset

    def __init__(self, rois, dataset_rtss):
        super(RoiDeleteOptions, self).__init__()

        self.setup_ui(self, rois, dataset_rtss, self.deleting_rois_structure_tuple)


class ROIDelOption:
    """
    The class that will be called by the main page to access the ROI Options controller
    """

    def __init__(self, dataset_rtss, structure_modified_function):
        super(ROIDelOption, self).__init__()
        self.dataset_rtss = dataset_rtss
        self.structure_modified_function = structure_modified_function

    def show_roi_delete_options(self):
        patient_dict_container = PatientDictContainer()
        rois = patient_dict_container.get("rois")
        self.options_window = RoiDeleteOptions(rois, self.dataset_rtss)
        self.options_window.deleting_rois_structure_tuple.connect(self.structure_modified_function)
        self.options_window.show()


class RoiDrawOptions(QtWidgets.QMainWindow, UIDrawROIWindow):
    """
    Create the ROI Draw Options class based on the UI from the file in View/ROI Draw Option
    """
    signal_roi_drawn = QtCore.pyqtSignal(tuple)

    def __init__(self, rois, dataset_rtss):
        super(RoiDrawOptions, self).__init__()
        self.setup_ui(self, rois, dataset_rtss, self.signal_roi_drawn)


class ROIDrawOption:
    """
    The class that will be called by the main page to access the ROI Options controller
    """

    def __init__(self, dataset_rtss, structure_modified_function):
        super(ROIDrawOption, self).__init__()
        self.dataset_rtss = dataset_rtss
        self.structure_modified_function = structure_modified_function

    def show_roi_draw_options(self):
        patient_dict_container = PatientDictContainer()
        rois = patient_dict_container.get("rois")
        self.draw_window = RoiDrawOptions(rois, self.dataset_rtss)
        self.draw_window.signal_roi_drawn.connect(self.structure_modified_function)
        self.draw_window.show()
