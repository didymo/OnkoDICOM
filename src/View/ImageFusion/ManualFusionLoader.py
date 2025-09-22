from PySide6 import QtCore
import logging
import os
from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.VTKEngine import VTKEngine

class ManualFusionLoader(QtCore.QObject):
    signal_loaded = QtCore.Signal(object)
    signal_error = QtCore.Signal(object)

    def __init__(self, selected_files, parent=None, patient_name=None, patient_id=None):
        super().__init__(parent)
        self.selected_files = selected_files
        self.patient_name = patient_name
        self.patient_id = patient_id

    def load(self, interrupt_flag=None, progress_callback=None):
        try:
            self._load_with_vtk(progress_callback)
        except Exception as e:
            if progress_callback is not None:
                progress_callback.emit(("Error loading images", e))
            self.signal_error.emit((False, e))

    def _load_with_vtk(self, progress_callback):
        # Progress: loading fixed image
        if progress_callback is not None:
            progress_callback.emit(("Loading fixed image (VTK)...", 10))

        # Gather fixed filepaths (directory)
        patient_dict_container = PatientDictContainer()
        fixed_dir = patient_dict_container.path
        moving_dir = None
        transform_file = None

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

            # Check if any selected file is a transform DICOM (Spatial Registration)
            from pydicom import dcmread
            from pydicom.errors import InvalidDicomError
            for f in self.selected_files:
                try:
                    ds = dcmread(f, stop_before_pixels=True)
                    modality = getattr(ds, "Modality", "").upper()
                    sop_class = getattr(ds, "SOPClassUID", "")
                    if modality == "REG" or sop_class == "1.2.840.10008.5.1.4.1.1.66.1":
                        transform_file = f
                        break
                except (InvalidDicomError, AttributeError, OSError):
                    continue

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

        # If a transform DICOM was found and is ticked, extract transform data only
        transform_data = None
        if transform_file is not None:
            if progress_callback is not None:
                progress_callback.emit(("Extracting saved transform...", 80))
            import pydicom, numpy as np
            ds = pydicom.dcmread(transform_file)
            if hasattr(ds, "RegistrationSequence") or (0x7777, 0x0010) in ds:
                transform_data = self._extracted_from__load_with_vtk_62(ds, np, transform_file)

        if progress_callback is not None:
            progress_callback.emit(("Finalising", 90))

        # Only emit the VTKEngine for downstream use; overlays will be generated on-the-fly
        self.signal_loaded.emit((True, {
            "vtk_engine": engine,
            "transform_data": transform_data,
        }))

    # TODO Rename this here and in `_load_with_vtk`
    def _extracted_from__load_with_vtk_62(self, ds, np, transform_file):
        reg_seq = ds.RegistrationSequence[0]
        mat_seq = reg_seq.MatrixRegistrationSequence[0]
        matrix_flat = mat_seq.FrameOfReferenceTransformationMatrix
        matrix = np.array(matrix_flat, dtype=np.float32).reshape((4, 4))
        translation = (
            [float(x) for x in ds[(0x7777, 0x0020)].value.split(",")]
            if (0x7777, 0x0020) in ds
            else [matrix[0, 3], matrix[1, 3], matrix[2, 3]]
        )
        if (0x7777, 0x0021) in ds:
            rotation = [float(x) for x in ds[(0x7777, 0x0021)].value.split(",")]
        else:
            rotation = [0, 0, 0]
        return {
            "matrix": matrix,
            "translation": translation,
            "rotation": rotation,
            "transform_file": transform_file,
        }