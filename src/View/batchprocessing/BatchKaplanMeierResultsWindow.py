import platform
from PySide6 import QtCore, QtGui, QtWidgets
from src.Controller.PathHandler import resource_path


class BatchKaplanMeierResultsWindow(QtWidgets.QDialog):
    """
    This class creates a GUI window for displaying a summary of batch
    processing. It inherits from QDialog.
    """

    def __init__(self):
        QtWidgets.QDialog.__init__(self)
        self.ml_model = None
        self.params = None
        self.scaling = None

        # # Set maximum width, icon, and title
        self.setFixedSize(450, 450)
        self.setWindowTitle("Kaplan Meier Graph")
        window_icon = QtGui.QIcon()
        window_icon.addPixmap(
            QtGui.QPixmap(resource_path("res/images/icon.ico")),
            QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(window_icon)

        # Create widgets
        self.save_graph_button = QtWidgets.QPushButton("Save graph")

        # # Get stylesheet
        if platform.system() == 'Darwin':
            self.stylesheet_path = "res/stylesheet.qss"
        else:
            self.stylesheet_path = "res/stylesheet-win-linux.qss"
        self.stylesheet = open(resource_path(self.stylesheet_path)).read()

        # Set stylesheet
        self.save_graph_button.setStyleSheet(self.stylesheet)

        # Create layout
        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.save_graph_button)

        # Connect buttons to functions
        self.save_graph_button.clicked.connect(
            self.save_graph_clicked)

        # Set layout of window
        self.setLayout(self.layout)

    def set_image(self, image):
        """
        Sets the summary text.
        :param batch_summary: List where first index is a dictionary where key
                              is a patient, and value is a dictionary of
                              process name and status key-value pairs, and
                              second index is a batch ROI name cleaning summary
        """
        self.image = image

    def save_graph_clicked(self):
        """
        Function to handle the ok button being clicked. Closes this
        window.
        :return: True when the window has closed.
        """
        file_path = QtWidgets.QFileDialog. \
            getExistingDirectory(self,
                                 "Open Directory",
                                 "",
                                 QtWidgets.QFileDialog.ShowDirsOnly |
                                 QtWidgets.QFileDialog.DontResolveSymlinks)
        if file_path:
            # save the graph
            pass
