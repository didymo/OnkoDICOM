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
            self._extracted_from_load_4(progress_callback)
        except Exception as e:
            if progress_callback is not None:
                progress_callback.emit(("Error loading images", e))
            self.signal_error.emit((False, e))

    # TODO Rename this here and in `load`
    def _extracted_from_load_4(self, progress_callback):
        # Progress: loading fixed image
        if progress_callback is not None:
            progress_callback.emit(("Loading fixed image...", 10))

        # Gather fixed filepaths
        patient_dict_container = PatientDictContainer()
        fixed_filepaths = [
            patient_dict_container.filepaths[i]
            for i in range(len(patient_dict_container.filepaths))
            if i in patient_dict_container.filepaths
        ]

        # Load fixed image as a sorted DICOM series
        fixed_image = self._load_dicom_series(fixed_filepaths)
        if progress_callback is not None:
            progress_callback.emit(("Loading overlay image...", 50))

        # Load moving image as a sorted DICOM series
        moving_image = self._load_dicom_series(self.selected_files)

        if progress_callback is not None:
            progress_callback.emit(("Finished loading images", 100))

        # Emit loaded images
        self.signal_loaded.emit((True, {
            "fixed_image": fixed_image,
            "moving_image": moving_image
        }))

    def _load_dicom_series(self, filepaths):
        """
        Loads a DICOM series robustly for image fusion.

        - Filters out files that are not valid CT DICOM images.
        - Sorts the valid files by their Z position (ImagePositionPatient tag).
        - Reads the sorted series into a 3D SimpleITK image.

        Args:
            filepaths (list): List of file paths to DICOM files.

        Returns:
            SimpleITK.Image: The loaded 3D image volume.
        """
        if not filepaths:
            raise ValueError("No DICOM files provided.")

        # Collect (filepath, z) for valid CT files in a single pass
        valid_files_with_z = []
        for f in filepaths:
            try:
                img = sitk.ReadImage(f)
                if img.HasMetaDataKey("0008|0060"):
                    modality = img.GetMetaData("0008|0060")
                    if modality.upper() == "CT":
                        z = 0.0
                        if img.HasMetaDataKey("0020|0032"):
                            ipp = img.GetMetaData("0020|0032").split("\\")
                            z = float(ipp[2])
                        valid_files_with_z.append((f, z))
            except Exception:
                continue

        if not valid_files_with_z:
            raise ValueError("No valid CT DICOM files found.")

        # Sort by Z position
        valid_files_with_z.sort(key=lambda x: x[1])
        sorted_files = [f for f, _ in valid_files_with_z]

        # Read the sorted series into a 3D image
        reader = sitk.ImageSeriesReader()
        reader.SetFileNames(sorted_files)
        return reader.Execute()