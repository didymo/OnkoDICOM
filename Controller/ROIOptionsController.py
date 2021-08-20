from src.View.mainpage.DeleteROIWindow import *
from src.View.mainpage.DrawROIWindow import *


class RoiDeleteOptions(QtWidgets.QMainWindow, UIDeleteROIWindow):
    """
    Create the ROI Delete Options class based on the UI from the file in
    View/ROI Delete Option
    """
    deleting_rois_structure_tuple = QtCore.Signal(tuple)  # new PyDicom dataset

    def __init__(self, rois, dataset_rtss):
        super(RoiDeleteOptions, self).__init__()

        self.setup_ui(
            self, rois, dataset_rtss, self.deleting_rois_structure_tuple)


class ROIDelOption:
    """
    The class that will be called by the main page to access the ROI Options
    controller
    """

    def __init__(self, structure_modified_function):
        super(ROIDelOption, self).__init__()
        self.structure_modified_function = structure_modified_function

    def show_roi_delete_options(self):
        patient_dict_container = PatientDictContainer()
        rois = patient_dict_container.get("rois")
        dataset_rtss = patient_dict_container.get("dataset_rtss")
        self.options_window = RoiDeleteOptions(rois, dataset_rtss)
        self.options_window.deleting_rois_structure_tuple.connect(
            self.structure_modified_function)
        self.options_window.show()


class RoiDrawOptions(QtWidgets.QMainWindow, UIDrawROIWindow):
    """
    Create the ROI Draw Options class based on the UI from the file in
    View/ROI Draw Option
    """
    signal_roi_drawn = QtCore.Signal(tuple)

    def __init__(self, rois, dataset_rtss):
        super(RoiDrawOptions, self).__init__()
        self.setup_ui(self, rois, dataset_rtss, self.signal_roi_drawn)


class ROIDrawOption:
    """
    The class that will be called by the main page to access the ROI
    Options controller
    """

    def __init__(self, structure_modified_function):
        super(ROIDrawOption, self).__init__()
        self.structure_modified_function = structure_modified_function

    def show_roi_draw_options(self):
        self.choose_roi_name_window = SelectROIPopUp()
        self.choose_roi_name_window.signal_roi_name.connect(
            self.roi_name_selected)
        self.choose_roi_name_window.show()

    def roi_name_selected(self, roi_name):
        patient_dict_container = PatientDictContainer()
        rois = patient_dict_container.get("rois")
        dataset_rtss = patient_dict_container.get("dataset_rtss")
        self.draw_window = RoiDrawOptions(rois, dataset_rtss)
        self.draw_window.set_selected_roi_name(roi_name)
        self.draw_window.signal_roi_drawn.connect(
            self.structure_modified_function)
        self.draw_window.show()
