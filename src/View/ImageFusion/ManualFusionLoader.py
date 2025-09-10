from PySide6 import QtCore
import logging
import os
from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.MovingDictContainer import MovingDictContainer
from src.View.ImageFusion.MovingImageLoader import MovingImageLoader

from src.Model.VTKEngine import VTKEngine

from src.View.ImageLoader import ImageLoader

class ManualFusionLoader(ImageLoader):
    signal_loaded = QtCore.Signal(object)
    signal_error = QtCore.Signal(object)

    def __init__(self, selected_files, existing_rtss=None, parent_window=None):
        super().__init__(selected_files, existing_rtss, parent_window)

    def load(self, interrupt_flag=None, progress_callback=None):
        try:
            self._load_with_vtk(progress_callback, interrupt_flag)
        except Exception as e:
            if progress_callback is not None:
                progress_callback.emit(("Error loading images", e))
            self.signal_error.emit((False, e))

    def _load_with_vtk(self, progress_callback, interrupt_flag=None):
        # Progress: loading fixed image
        if progress_callback is not None:
            progress_callback.emit(("Loading fixed image (VTK)...", 10))

        # Gather fixed filepaths (directory)
        patient_dict_container = PatientDictContainer()
        fixed_dir = patient_dict_container.path
        moving_dir = None
        if self.selected_files:
            # Validate all selected files are from the same directory
            dirs = {os.path.dirname(f) for f in self.selected_files}
            if len(dirs) > 1:
                # Emit error message if invalid
                error_msg = (
                    f"Selected files span multiple directories: {dirs}. "
                    "Manual fusion requires all files to be from the same directory."
                )
                if progress_callback is not None:
                    progress_callback.emit(("Error loading images", error_msg))
                self.signal_error.emit((False, error_msg))
                return
            moving_dir = dirs.pop()

        # Use VTKEngine to load images
        engine = VTKEngine()
        fixed_loaded = engine.load_fixed(fixed_dir)
        if not fixed_loaded:
            raise RuntimeError("Failed to load fixed image with VTK.")

        if progress_callback is not None:
            progress_callback.emit(("Loading overlay image (VTK)...", 50))

        moving_loaded = engine.load_moving(moving_dir)
        
        if not moving_loaded:
            raise RuntimeError("Failed to load moving image with VTK.")

        moving_image_loader = MovingImageLoader(self.selected_files, None, self)
        moving_model_populated = moving_image_loader.load_manual_mode(interrupt_flag, progress_callback)

        if not moving_model_populated:
            raise RuntimeError("Failed to populate Moving Model Container")

        if progress_callback is not None:
            progress_callback.emit(("Finalising", 90))

        # Only emit the VTKEngine for downstream use; overlays will be generated on-the-fly
        self.signal_loaded.emit((True, {
            "vtk_engine": engine,
        }))