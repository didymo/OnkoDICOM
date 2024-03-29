import platform
from PySide6 import QtCore, QtGui, QtWidgets
from src.Controller.PathHandler import resource_path


class ROIName2FMAIDOptions(QtWidgets.QWidget):
    """
    ROI Name Cleaning options for batch processing.
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

        # Create widgets
        self.info_label = QtWidgets.QLabel()
        self.label_text = "Converts ROI names into their equivalent FMA IDs."
        self.info_label.setText(self.label_text)
        self.info_label.setAlignment(QtCore.Qt.AlignCenter)
        self.font = QtGui.QFont()
        self.font.setPointSize(14)
        self.info_label.setFont(self.font)
        self.main_layout.addWidget(self.info_label)

        self.setLayout(self.main_layout)
