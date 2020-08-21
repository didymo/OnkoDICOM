######################################################################################################
#                                                                                                    #
#   This file handles all the processes done within the ROI Delete and Draw button                   #
#                                                                                                    #
######################################################################################################
import csv
import sys
import webbrowser
from PyQt5.QtWidgets import QFileDialog, QMessageBox
from src.View.Main_Page.DeleteROIWindow import *
from src.Controller.AddOnOptionsController import *
from pydicom import Dataset

######################################################################################################
#                                                                                                    #
#   Create the ROI Delete Options class based on the UI from the file in View/ROI Delete Optio       #
#                                                                                                    #
######################################################################################################

class RoiDeleteOptions(QtWidgets.QMainWindow, Ui_DeleteROIWindow):
        newStructure = QtCore.pyqtSignal(Dataset)  # new PyDicom dataset

        def __init__(self, window, rois, dataset_rtss):
            super(RoiDeleteOptions, self).__init__()

            self.window = window
            self.setupUi(self, rois, dataset_rtss, self.newStructure)

###################################################################################################################
#                                                                                                                 #
# The class that will be called by the main page to access the ROI Options controller                             #
#                                                                                                                 #
###################################################################################################################

class ROIDelOption:

    def __init__(self, window, rois, dataset_rtss):
        super(ROIDelOption, self).__init__()
        self.window = window
        self.rois = rois
        self.dataset_rtss = dataset_rtss

    def show_roi_delete_options(self):
        self.options_window = RoiDeleteOptions(self.window, self.rois, self.dataset_rtss)
        self.options_window.show()