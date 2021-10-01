import platform
from os.path import expanduser

from PySide6 import QtWidgets
from src.Controller.PathHandler import resource_path


class Pyrad2PyradSROptions(QtWidgets.QWidget):
    """
    PyRad2CSV options for batch processing.
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

        label = QtWidgets.QLabel("The resulting Pyrad-SR files will be "
                                 "located within the individual patient "
                                 "directories.")

        label.setStyleSheet(self.stylesheet)

        self.main_layout.addWidget(label)

        self.setLayout(self.main_layout)
