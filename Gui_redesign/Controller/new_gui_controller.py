from PyQt5.QtWidgets import QMessageBox, QDesktopWidget
from PyQt5 import QtCore, QtGui, QtWidgets
from Gui_redesign.View.welcome_page_liamEdit import UIWelcomeWindow
from Gui_redesign.View.open_patient_liamEdit import UIOpenPatientWindow


class NewWelcomeGui(QtWidgets.QMainWindow, UIWelcomeWindow):

    # Initialisation function to display the UI
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.patient_window = QtWidgets.QMainWindow()

        self.setup_ui(self)
        self.push_button.clicked.connect(self.patient_handler)

    def patient_handler(self):
        """
        Function to handle the Open patient button being clicked
        """
        # Browse directories

        self.patient_opener = NewPatientGui()
        self.patient_opener.show()
        self.close()


class NewPatientGui(QtWidgets.QMainWindow, UIOpenPatientWindow):
    # If patient directory selected, open patient display window
    open_patient_window = QtCore.pyqtSignal(str)

    # Initialisation function to display the UI
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)

        self.setup_ui(self)
