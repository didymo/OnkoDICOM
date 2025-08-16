from PySide6 import QtCore
import SimpleITK as sitk
from src.Model.PatientDictContainer import PatientDictContainer

class ManualFusionLoader(QtCore.QObject):
    signal_loaded = QtCore.Signal(object)
    signal_error = QtCore.Signal(object)

    def __init__(self, selected_files, parent=None):
        super().__init__(parent)
        self.selected_files = selected_files

    def load(self, interrupt_flag=None, progress_callback=None):
        try:
            # Optionally, emit progress if callback is provided
            if progress_callback is not None:
                progress_callback.emit(("Loading fixed image...", 10))
            # Load fixed (base) and moving (overlay) images as SimpleITK
            patient_dict_container = PatientDictContainer()
            fixed_filepaths = []
            for i in range(len(patient_dict_container.filepaths)):
                try:
                    fixed_filepaths.append(patient_dict_container.filepaths[i])
                except KeyError:
                    continue

            moving_filepaths = self.selected_files

            fixed_image = sitk.ReadImage(fixed_filepaths)
            if progress_callback is not None:
                progress_callback.emit(("Loading overlay image...", 50))
            moving_image = sitk.ReadImage(moving_filepaths)

            if progress_callback is not None:
                progress_callback.emit(("Finished loading images", 100))

            self.signal_loaded.emit((True, {
                "fixed_image": fixed_image,
                "moving_image": moving_image
            }))
        except Exception as e:
            self.signal_error.emit((False, e))
