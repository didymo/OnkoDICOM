import platform
from PySide6 import QtWidgets
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

        self.setLayout(self.main_layout)