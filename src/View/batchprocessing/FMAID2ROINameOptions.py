from PySide6 import QtCore, QtGui, QtWidgets


class FMAID2ROINameOptions(QtWidgets.QWidget):
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

        # Create widgets
        self.info_label = QtWidgets.QLabel()
        self.label_text = "Converts FMA IDs into their equivalent ROI name."
        self.info_label.setText(self.label_text)
        self.info_label.setAlignment(QtCore.Qt.AlignCenter)
        self.font = QtGui.QFont()
        self.font.setPointSize(14)
        self.info_label.setFont(self.font)
        self.main_layout.addWidget(self.info_label)

        self.setLayout(self.main_layout)
