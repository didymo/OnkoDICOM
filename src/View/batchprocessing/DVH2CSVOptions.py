import platform

from PySide6 import QtCore, QtGui, QtWidgets
from src.Controller.PathHandler import resource_path


class DVH2CSVOptions(QtWidgets.QWidget):
    """
    DVH2CSV options for batch processing.
    """

    def __init__(self):
        """
        Initialise the class
        """
        QtWidgets.QWidget.__init__(self)

        # Create the main layout
        self.main_layout = QtWidgets.QVBoxLayout()

        # Get the stylesheet
        # Get the stylesheet
        if platform.system() == 'Darwin':
            self.stylesheet_path = "res/stylesheet.qss"
        else:
            self.stylesheet_path = "res/stylesheet-win-linux.qss"
        self.stylesheet = open(resource_path(self.stylesheet_path)).read()

        label = QtWidgets.QLabel("Nothing to see here, move along.")
        self.main_layout.addWidget(label)
        self.setLayout(self.main_layout)
