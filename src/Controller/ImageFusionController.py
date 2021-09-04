from PySide6 import QtWidgets, QtCore

from src.View.ImageFusionWindow import UIImageFusionWindow

from src.Model.MovingModel import create_moving_model
from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.MovingDictContainer import MovingDictContainer


class ImageFusionWindow(QtWidgets.QMainWindow, UIImageFusionWindow):
    go_next_window = QtCore.Signal(object)

    def __init__(self, default_directory=None):
        QtWidgets.QMainWindow.__init__(self)
        self.setup_ui(self)
        self.image_fusion_info_initialized.connect(self.open_patient)

    def set_up_directory(self, default_directory):
        self.filepath = default_directory
        self.open_patient_directory_input_box.setText(default_directory)
        self.scan_directory_for_patient()

    def open_patient(self, progress_window):
        self.go_next_window.emit(progress_window)


# This Controller is currently being called by the MainPage only
class ImageFusionController:
    progress_window_signal = QtCore.Signal()

    def __init__(self, window, default_directory=None):
        self.filepath = default_directory
        self.window = window
        self.image_fusion_select_window = QtWidgets.QMainWindow()
        self.image_fusion_select_window = ImageFusionWindow()

        self.image_fusion_select_window.go_next_window.connect(
            self.close_select_window)

    def set_path(self, directory):
        self.image_fusion_select_window.set_up_directory(directory)

    def show_image_fusion_select_window(self):
        self.image_fusion_select_window.show()

    def close_select_window(self, progress_window):
        progress_window.update_progress(("Creating Moving Model", 50))
        create_moving_model()
        progress_window.update_progress(("Finished Creating Moving Model", 60))
        progress_window.close()

        self.image_fusion_select_window.close()
        self.progress_window_signal.emit()
