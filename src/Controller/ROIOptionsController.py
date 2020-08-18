######################################################################################################
#                                                                                                    #
#   This file handles all the processes done within the ROI Delete and Draw button                   #
#                                                                                                    #
######################################################################################################
import csv
import sys
import webbrowser
from PyQt5.QtWidgets import QFileDialog
from src.View.Main_Page.DeleteROIWindow import *

######################################################################################################
#                                                                                                    #
#   Create the ROI Delete Options class based on the UI from the file in View/ROI Delete Optio       #
#                                                                                                    #
######################################################################################################

class RoiDeleteOptions(QtWidgets.QMainWindow, Ui_DeleteROIWindow):

        def __init__(self, window):
            super(RoiDeleteOptions, self).__init__()

            self.window = window
            self.setupUi(self)

###################################################################################################################
#                                                                                                                 #
# The class that will be called by the main page to access the ROI Options controller                             #
#                                                                                                                 #
###################################################################################################################

class ROIDelOption:

    def __init__(self, window):
        self.window = window

    def show_roi_delete_options(self):
        self.options_window = RoiDeleteOptions(self.window)
        self.options_window.show()