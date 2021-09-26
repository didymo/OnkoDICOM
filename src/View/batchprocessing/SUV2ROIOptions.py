import platform
from PySide6 import QtGui, QtWidgets
from src.Controller.PathHandler import resource_path


class SUV2ROIOptions(QtWidgets.QWidget):
    """
    SUV2ROI options for batch processing. A simple description of the
    current requirements for SUV2ROI in OnkoDICOM.
    """

    def __init__(self):
        """
        Initialise the class
        """
        QtWidgets.QWidget.__init__(self)

        # Create the main layout
        self.main_layout = QtWidgets.QVBoxLayout()

        # Get the stylesheet
        if platform.system() == 'Darwin':
            self.stylesheet_path = "res/stylesheet.qss"
        else:
            self.stylesheet_path = "res/stylesheet-win-linux.qss"
        self.stylesheet = open(resource_path(self.stylesheet_path)).read()

        # Create QLabel to display information, and text and font
        self.info_label = QtWidgets.QLabel()
        self.text_font = QtGui.QFont()
        text_info = "SUV2ROI can currently only be performed on PET images " \
                    "that are stored in units of Bq/mL and that are decay " \
                    "corrected. For best results, please ensure only one set " \
                    "of compliant PET images is present in each dataset that " \
                    "you wish to perform SUV2ROI on. For more information " \
                    "on SUV2ROI functionality, see the User Manual."
        self.text_font.setPointSize(12)
        self.info_label.setText(text_info)
        self.info_label.setFont(self.text_font)
        self.info_label.setWordWrap(True)

        self.main_layout.addWidget(self.info_label)
        self.setLayout(self.main_layout)
