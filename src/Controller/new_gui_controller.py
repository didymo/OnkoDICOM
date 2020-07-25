from PyQt5 import QtCore, QtWidgets

from src.Controller import interPageController
from src.View.welcome_page import UIWelcomeWindow
from src.View.open_patient import UIOpenPatientWindow


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

    # Initialisation function to display the UI
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.patient_window = QtWidgets.QMainWindow()

        self.setup_ui(self)
        self.open_patient_window.connect(self.open_patient)

    def open_patient(self, patient_attributes):
        patient_dict_container = patient_attributes[0]
        progress_window = patient_attributes[1]
        self.patient_window = interPageController.MainWindow(patient_dict_container)
        progress_window.update_progress(("Loading complete!", 100))
        progress_window.close()
        self.patient_window.show()
        self.close()
