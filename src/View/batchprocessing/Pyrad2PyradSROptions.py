from PySide6 import QtWidgets
from src.View.StyleSheetReader import StyleSheetReader


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

        label = QtWidgets.QLabel("The resulting Pyrad-SR files will be "
                                 "located within the individual patient "
                                 "directories.")

        label.setStyleSheet(StyleSheetReader().get_stylesheet())

        self.main_layout.addWidget(label)

        self.setLayout(self.main_layout)
