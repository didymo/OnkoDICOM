from PySide6 import QtWidgets

from src.Controller.GUIController import WelcomeWindow, OpenPatientWindow, \
    MainWindow, PyradiProgressBar, FirstTimeWelcomeWindow, ImageFusionWindow, \
    BatchWindow


class Controller:

    # Initialisation function that creates an instance of each window
    def __init__(self, default_directory=None):
        self.first_time_welcome_window = QtWidgets.QMainWindow()
        self.welcome_window = QtWidgets.QMainWindow()
        self.open_patient_window = QtWidgets.QMainWindow()
        self.main_window = QtWidgets.QMainWindow()
        self.batch_window = QtWidgets.QMainWindow()
        self.pyradi_progressbar = QtWidgets.QWidget()
        # This will contain a filepath of a folder that is dragged onto
        self.default_directory = default_directory

        self.image_fusion_window = QtWidgets.QMainWindow()
        # the executable icon

    def show_first_time_welcome(self):
        """
        Display first time welcome page
        """
        self.first_time_welcome_window = FirstTimeWelcomeWindow()
        self.first_time_welcome_window.update_directory.connect(
            self.update_default_directory)
        self.first_time_welcome_window.go_next_window.connect(
            self.show_open_patient)
        self.first_time_welcome_window.show()

    def update_default_directory(self, new_directory):
        self.default_directory = new_directory

    def show_welcome(self):
        """
        Display welcome page
        """
        self.welcome_window = WelcomeWindow()
        self.welcome_window.go_next_window.connect(self.show_open_patient)
        self.welcome_window.go_batch_window.connect(self.show_batch_window)
        self.welcome_window.show()

    def show_open_patient(self):
        """
        Display open patient window
        """
        # Close all other open windows first
        if self.welcome_window.isVisible():
            self.welcome_window.close()
        if self.main_window.isVisible():
            self.main_window.close()
        if self.first_time_welcome_window.isVisible():
            self.first_time_welcome_window.close()

        # only initialize open_patient_window once
        if not isinstance(self.main_window, MainWindow):
            self.open_patient_window = OpenPatientWindow(
                self.default_directory)
            self.open_patient_window.go_next_window.connect(
                self.show_main_window)

        self.open_patient_window.show()

    def show_main_window(self, progress_window):
        """
        Displays the main patient window after completing the loading.
        :param progress_window: An instance of ProgressWindow
        :return:
        """
        # Only initialize main window once
        if not isinstance(self.main_window, MainWindow):
            self.main_window = MainWindow()
            self.main_window.open_patient_window.connect(
                self.show_open_patient)
            self.main_window.run_pyradiomics.connect(self.show_pyradi_progress)

            # This is actually being used in GUIController
            self.main_window.image_fusion_signal.connect(
                self.show_image_fusion_select_window)
        else:
            self.main_window.update_ui()

        if isinstance(self.image_fusion_window, ImageFusionWindow):
            progress_window.update_progress(
                ("Registering Images...\nThis may take a few minutes.", 
                90))
            self.main_window.update_image_fusion_ui()
            

        # Once the MainWindow has finished loading (which takes some
        # time), close all the other open windows.
        progress_window.update_progress(("Loading complete!", 100))
        progress_window.close()
        self.main_window.show()
        self.open_patient_window.close()
        self.image_fusion_window.close()


    def show_batch_window(self):
        # Only initialise the batch processing window once
        if not isinstance(self.batch_window, BatchWindow):
            self.batch_window = BatchWindow()

        # Close the main window and show the batch processing window
        self.batch_window.show()
        self.welcome_window.close()

    def show_pyradi_progress(self, path, filepaths, target_path):
        """
        Display pyradiomics progress bar
        """
        self.pyradi_progressbar = PyradiProgressBar(
            path, filepaths, target_path)
        self.pyradi_progressbar.progress_complete.connect(
            self.close_pyradi_progress)
        self.pyradi_progressbar.show()

    def close_pyradi_progress(self):
        """
        Close pyradiomics progress bar
        """
        self.pyradi_progressbar.close()

    def show_image_fusion_select_window(self):
        # only initialize image fusion window
        if not isinstance(self.image_fusion_window, ImageFusionWindow):
            self.image_fusion_window = ImageFusionWindow(
                self.default_directory)
            self.image_fusion_window.go_next_window.connect(
                self.show_main_window)

        self.image_fusion_window.show()

