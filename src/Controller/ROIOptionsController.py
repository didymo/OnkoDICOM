import logging
from PySide6.QtGui import QKeySequence, QShortcut
from src.View.ImageFusion.UITransferROIWindow import UITransferROIWindow
from src.View.mainpage.DeleteROIWindow import *
from src.View.mainpage.DrawROIWindow.DrawROIInitialiser import RoiInitialiser
from src.View.mainpage.ManipulateROIWindow import *


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

    def update_ui(self, rois, dataset_rtss):
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
        if not hasattr(self, "options_window"):
            self.options_window = RoiDeleteOptions(rois, dataset_rtss)
            self.options_window.deleting_rois_structure_tuple.connect(
                self.structure_modified_function)
        else:
            self.options_window.update_ui(rois, dataset_rtss)
        self.options_window.show()


class RoiDrawOptions(QtWidgets.QMainWindow, RoiInitialiser):
    """
    Create the ROI Draw Options class based on the UI from the file in
    View/ROI Draw Option
    """
    signal_roi_drawn = QtCore.Signal(tuple)
    signal_draw_roi_closed = QtCore.Signal()
    

    def __init__(self, rois, dataset_rtss):
        super(RoiDrawOptions, self).__init__()
        QShortcut(QKeySequence(Qt.Key_Up),   self, activated=lambda: self.scroller.setValue(min(self.scroller.value()+1, self.scroller.maximum())))
        QShortcut(QKeySequence(Qt.Key_Down), self, activated=lambda: self.scroller.setValue(max(self.scroller.value()-1, self.scroller.minimum())))
        

        self._central = QtWidgets.QWidget(self)
        self.setCentralWidget(self._central)
        self.set_up(rois, dataset_rtss, self.signal_roi_drawn,
                    self.signal_draw_roi_closed)

    def update_ui(self, rois, dataset_rtss):
        self.set_up(rois, dataset_rtss, self.signal_roi_drawn,
                    self.signal_draw_roi_closed)
        
    def eventFilter(self, obj, event):
        print(event.type())
        if obj is self.view.viewport() and event.type() == QtCore.QEvent.Resize:
            self._hud.setGeometry(self.view.viewport().rect())
            return False  # don't consume; just reacting
        #12 is the  number acosiated with the arrow press event
        #will trigger when the arrow key is pressed
        if event.type() == 12:
            self._hud.setGeometry(self.view.viewport().rect())
            return False
         #scroll wheel changes the image
        if event.type() == QtCore.QEvent.Type.Wheel:
            self._hud.setGeometry(self.view.viewport().rect())
            dy = event.pixelDelta().y() or event.angleDelta().y()
            if dy > 0:
                #scroll up
                self.scroller.setValue(self.scroller.value()+1)
            elif dy < 0:
                #scroll down
                self.scroller.setValue(self.scroller.value()-1)
            return True
        return super().eventFilter(obj, event)


class ROIDrawOption:
    """
    The class that will be called by the main page to access the ROI
    Options controller
    """

    def __init__(self, structure_modified_function, remove_draw_roi_instance):
        super(ROIDrawOption, self).__init__()
        self.structure_modified_function = structure_modified_function
        self.remove_roi_draw_instance = remove_draw_roi_instance

    def show_roi_draw_window(self):
        """
        Gets data needed for the draw ROI window, creates it and displays the popup window
        """
        logging.debug("show_roi_draw_window started")
        patient_dict_container = PatientDictContainer()
        rois = patient_dict_container.get("rois")
        dataset_rtss = patient_dict_container.get("dataset_rtss")

        if not hasattr(self, "draw_window"):
            self.draw_window = RoiDrawOptions(rois, dataset_rtss)
            self.draw_window.signal_roi_drawn.connect(
                self.structure_modified_function)
            self.draw_window.signal_draw_roi_closed.connect(
                self.remove_roi_draw_instance)
        else:
            self.draw_window.update_ui(rois, dataset_rtss)

        return self.draw_window


    def remove_roi_draw_window(self):
        if hasattr(self, "draw_window"):
            delattr(self, 'draw_window')


class RoiManipulateOptions(QtWidgets.QMainWindow, UIManipulateROIWindow):
    """
    Create the ROI Manipulate Options class based on the UI from the file in
    View/ROI Delete Option
    """
    signal_roi_manipulated = QtCore.Signal(tuple)

    def __init__(self, rois, dataset_rtss, roi_color):
        """
        :param rois: dictionary of ROI info
        :param dataset_rtss: RTSS pydicom dataset
        :param roi_color: dictionary of QColor for each ROI
        """
        super(RoiManipulateOptions, self).__init__()
        self.roi_color = roi_color
        self.setup_ui(self, rois, dataset_rtss, roi_color,
                      self.signal_roi_manipulated)

    def update_ui(self, rois, dataset_rtss, roi_color):
        """
        :param rois: dictionary of ROI info
        :param dataset_rtss: RTSS pydicom dataset
        :param roi_color: dictionary of QColor for each ROI
        """
        self.roi_color = roi_color
        self.setup_ui(self, rois, dataset_rtss, self.roi_color,
                      self.signal_roi_manipulated)


class ROIManipulateOption:
    """
    The class that will be called by the main page to access the ROI
    Options controller
    """

    def __init__(self, structure_modified_function):
        """
        :param structure_modified_function: Function to modify list of ROIs on
        Structure Tab
        """
        super(ROIManipulateOption, self).__init__()
        self.structure_modified_function = structure_modified_function

    def show_roi_manipulate_options(self, roi_color):
        """
        Display ROI manipulate window
        """
        patient_dict_container = PatientDictContainer()
        rois = patient_dict_container.get("rois")
        dataset_rtss = patient_dict_container.get("dataset_rtss")
        if not hasattr(self, "manipulate_window"):
            self.manipulate_window = RoiManipulateOptions(rois, dataset_rtss,
                                                          roi_color)
            self.manipulate_window.signal_roi_manipulated.connect(
                self.structure_modified_function)
        else:
            self.manipulate_window.update_ui(rois, dataset_rtss, roi_color)
        self.manipulate_window.show()


class ROITransferOptionUI(QtWidgets.QMainWindow, UITransferROIWindow):
    """
    Create the ROI Manipulate Options class based on the UI from the file in
    UITransferROIWindow
    """
    signal_roi_transferred_to_fixed_container = QtCore.Signal(tuple)
    signal_roi_transferred_to_moving_container = QtCore.Signal(tuple)

    def __init__(self):
        super(ROITransferOptionUI, self).__init__()
        self.setup_ui(self, self.signal_roi_transferred_to_fixed_container,
                      self.signal_roi_transferred_to_moving_container)


class ROITransferOption:
    """
        The class that will be called by ImageFusion to access the ROI
        Transfer controller
        """

    def __init__(self, fixed_dict_structure_modified_function,
                 moving_dict_structure_modified_function):
        """

        :param fixed_dict_structure_modified_function: function to call when
        the fixed image's rtss is modified
        :param moving_dict_structure_modified_function: function to call when
        the moving image's rtss is modified

        """
        super(ROITransferOption, self).__init__()
        self.fixed_dict_structure_modified_function = \
            fixed_dict_structure_modified_function
        self.moving_dict_structure_modified_function = \
            moving_dict_structure_modified_function

    def show_roi_transfer_options(self):
        """

        function to display ROI Transfer window when
        ROI Transfer button is clicked.

        """
        self.roi_transfer_option_pop_up_window = ROITransferOptionUI()
        self.roi_transfer_option_pop_up_window. \
            signal_roi_transferred_to_moving_container \
            .connect(self.moving_dict_structure_modified_function)
        self.roi_transfer_option_pop_up_window. \
            signal_roi_transferred_to_fixed_container \
            .connect(self.fixed_dict_structure_modified_function)
        self.roi_transfer_option_pop_up_window.show()
