from PySide6 import QtWidgets

from src.Controller.GUIController import WelcomeWindow, OpenPatientWindow, MainWindow, PyradiProgressBar


class Controller:

    # Initialisation function that creates an instance of each window
    def __init__(self, default_directory=None):
        self.welcome_window = QtWidgets.QMainWindow()
        self.open_patient_window = QtWidgets.QMainWindow()
        self.main_window = QtWidgets.QMainWindow()
        self.pyradi_progressbar = QtWidgets.QWidget()
        self.default_directory = default_directory  # This will contain a filepath of a folder that is dragged onto
        # the executable icon

    def show_welcome(self):
        """
        Display welcome page
        """
        self.welcome_window = WelcomeWindow()
        self.welcome_window.go_next_window.connect(self.show_open_patient)
        self.welcome_window.show()

    def show_open_patient(self):
        """
        Display open patient window
        """
        # Close all other open windows first
        if self.welcome_window.isVisible():
            self.welcome_window.close()

        # open_patient_window has already been initialized if main_window is visible
        if self.main_window.isVisible():
            self.main_window.close()
            self.open_patient_window.open_patient_directory_input_box.setText(self.default_directory)
            self.open_patient_window.scan_directory_for_patient()
        else:
            self.open_patient_window = OpenPatientWindow(self.default_directory)
            self.open_patient_window.go_next_window.connect(self.show_main_window)

        self.open_patient_window.show()

    def show_main_window(self, progress_window):
        """
        Displays the main patient window after completing the loading.
        :param patient_attributes: A tuple of (PatientDictContainer, ProgressWindow)
        :return:
        """
        self.main_window = MainWindow()
        self.main_window.open_patient_window.connect(self.show_open_patient)
        self.main_window.run_pyradiomics.connect(self.show_pyradi_progress)

        # Once the MainWindow has finished loading (which takes some time) close all the other open windows.
        progress_window.update_progress(("Loading complete!", 100))
        progress_window.close()
        self.main_window.show()
        self.open_patient_window.close()

    def show_pyradi_progress(self, path, filepaths, target_path):
        """
        Display pyradiomics progress bar
        """
        self.pyradi_progressbar = PyradiProgressBar(path, filepaths, target_path)
        self.pyradi_progressbar.progress_complete.connect(self.close_pyradi_progress)
        self.pyradi_progressbar.show()

    def close_pyradi_progress(self):
        """
        Close pyradiomics progress bar
        """
        self.pyradi_progressbar.close()
