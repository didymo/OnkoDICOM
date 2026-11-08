import os
import copy
import shutil
import tempfile
import logging
from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.Worker import SegmentationWorkerSignals
from totalsegmentator.python_api import totalsegmentator
from src.Model.NiftiToRtstructConverter import nifti_to_rtstruct_conversion
from src.Model.AutoSegmentation.DeviceSelection import select_segmentation_device
from src.View.util.RedirectStdOut import ConsoleOutputStream, redirect_output_to_gui, setup_logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Spline order TotalSegmentator uses to resample the input CT to the model's spacing. Up to 2.14 it
# was fixed at 3 (cubic); 2.15 made it a parameter, still defaulting to 3; 2.16 changed the default
# to 1 (linear) "for faster resampling", and its own help says 3 "may give slightly better
# segmentation accuracy". The parameter needs TotalSegmentator 2.15 or later (pyproject asks for
# ^2.18, the version measured below). We keep 3, the order our
# segmentations were made with before the move to 2.18 (Gitea #16). On the test patient, 2.18 at
# order 3 is voxel-identical to 2.10 for the nine structures checked, while 2.18 at its default 1
# moves the spinal cord by -3.8% (Dice 0.979).
#
# Not settable from here: the rough 6 mm "total" pass that finds the crop region uses a tile step of
# 0.8 in 2.18 where 2.10 used 0.5 (upstream commit fd81a3b, July 2026). It is hard-coded in
# TotalSegmentator's nnunet.py. On the test patient it changed nothing (the comparison above
# includes it).
TOTALSEGMENTATOR_RESAMPLING_ORDER = 3


class AutoSegmentation:
    """Handles the automatic segmentation process.

    This class manages the workflow for running TotalSegmentator, including
    copying DICOM files, setting up the segmentation task, and converting the
    output to DICOM RTSTRUCT format.
    """

    def __init__(self, controller):
        self.controller = controller
        patient_dict_container = PatientDictContainer()
        self.dicom_dir = patient_dict_container.path  # Get the current loaded dir to DICOM series
        self.dicom_temp_dir = None
        self.file_paths = patient_dict_container.filepaths # dict, where keys = slice number/RT modality and values = filepaths

        self.signals = SegmentationWorkerSignals()

        # Connect worker signals to controller slots
        self.signals.progress_updated.connect(self.controller.update_progress_text)
        self.signals.finished.connect(self.controller.on_segmentation_finished)
        self.signals.error.connect(self.controller.on_segmentation_error)

    def _connect_terminal_stream_to_gui(self) -> None:
        """
        Connects the terminal stream to the GUI window to
        update the progress text
        """
        output_stream = ConsoleOutputStream()
        output_stream.new_text.connect(self.controller.update_progress_text)
        redirect_output_to_gui(output_stream)
        setup_logging(output_stream)

    def run_segmentation_workflow(self, task, roi_subset):
        """
        Runs the full segmentation workflow for a given task and speed setting.
        This method manages the process of segmenting DICOM images, converting the
        results to RTSTRUCT, and cleaning up temporary files.

        Args:
            task: The segmentation task to perform.
            roi_subset: The ROI subset to use.

        Returns:
            None
        """
        self.signals.progress_updated.emit("Starting segmentation workflow...")
        self._connect_terminal_stream_to_gui()
        output_dir, output_rt = self._prepare_output_paths()

        try:
            self._copy_temp_dicom_dir()
            self._run_totalsegmentation(task, roi_subset, output_dir)
            self._convert_to_rtstruct(output_dir, output_rt)
            self.signals.finished.emit()
        except Exception as e:
            self.signals.error.emit(str(e))
            logger.exception("Segmentation workflow failed")
        finally:
            self._cleanup_nifti_dir(output_dir)
            self._cleanup_temp_dir()

    def _prepare_output_paths(self) -> tuple[str, str]:
        """
        Prepares and returns the output paths for segmentation and RTSTRUCT files.
        This method creates the output directory for segmentation results if it does
        not exist and determines the path for the RTSTRUCT file.

        Returns:
            tuple: A tuple containing the output directory path and the RTSTRUCT file path.
        """
        out_dir = os.path.join(self.dicom_dir, "segmentations")
        os.makedirs(out_dir, exist_ok=True)
        out_rt = os.path.join(self.dicom_dir, "rtss.dcm")

        return out_dir, out_rt

    def _copy_temp_dicom_dir(self) -> None:
        """
            Copies the file paths from patient dict to a temporary location for processing.
            This method creates a temporary directory and copies the DICOM files paths
            into it, excludes rtdose, rtplan, and rtstruct files.

            Raises:
                ValueError: If the DICOM directory is not set or copying fails.
         """
        if not self.file_paths:
            raise ValueError(f"No dicom files found in {self.file_paths}")
        # Create temporary directory
        self.dicom_temp_dir = tempfile.TemporaryDirectory()

        # Copy each source file to the temporary directory
        for name, src_file_path in self.file_paths.items():

            # Exclude files
            if name in ['rtdose', 'rtss', 'rtplan']:
                continue
            # Create new file path
            dest_file_path = os.path.join(self.dicom_temp_dir.name, os.path.basename(src_file_path))
            try:
                shutil.copyfile(src_file_path, dest_file_path)
            except Exception as e:
                self.signals.error.emit(str(e))


    def _run_totalsegmentation(self, task, roi_subset, output_dir) -> None:
        """
        Runs the TotalSegmentator segmentation task and saves the results.
        This method executes the segmentation process using the specified task,
        on the device chosen by select_segmentation_device (CUDA, then Apple
        MPS, then CPU, unless ONKODICOM_SEGMENTATION_DEVICE overrides it), and
        stores the output in the given directory.

        Args:
            task: The segmentation task to perform.
            roi_subset: The ROI subset to use.
            output_dir: Directory to store the segmentation results.

        Returns:
            None
        """
        device, explicit = select_segmentation_device()
        self.signals.progress_updated.emit(f"Running TotalSegmentator on device: {device}")
        try:
            self._call_totalsegmentator(task, roi_subset, output_dir, device)
        except Exception as err:
            # MPS still lacks some PyTorch operations. When MPS was chosen
            # automatically, fall back to the CPU rather than failing; when the
            # user asked for it explicitly, let the error stand.
            if device != "mps" or explicit:
                raise
            self.signals.progress_updated.emit(f"Segmentation on MPS failed ({err}); retrying on CPU.")
            logger.warning("TotalSegmentator failed on MPS, retrying on CPU", exc_info=True)
            self._call_totalsegmentator(task, roi_subset, output_dir, "cpu")

    def _call_totalsegmentator(self, task, roi_subset, output_dir, device) -> None:
        """
        Calls TotalSegmentator once on the given device.

        Args:
            task: The segmentation task to perform.
            roi_subset: The ROI subset to use.
            output_dir: Directory to store the segmentation results.
            device: "gpu", "gpu:N", "mps" or "cpu".
        """
        totalsegmentator(
            input=self.dicom_temp_dir.name,
            output=output_dir,
            task=task,
            roi_subset=list(set(copy.deepcopy(roi_subset))), # Deep copy to prevent changing to the selection after starting
            output_type="nifti",
            device=device,
            # Set explicitly, not left to TotalSegmentator's default, so an upstream default change
            # cannot silently change our contours. See TOTALSEGMENTATOR_RESAMPLING_ORDER.
            resampling_order=TOTALSEGMENTATOR_RESAMPLING_ORDER,
        )

    def _convert_to_rtstruct(self, nifti_dir, output_rt) -> None:
        """
        Converts NIfTI segmentation results to a DICOM RTSTRUCT file.
        This method calls the conversion utility and updates the progress signal.

        Args:
            nifti_dir: Directory containing the NIfTI segmentation files.
            output_rt: Path to save the generated RTSTRUCT file.

        Returns:
            None
        """
        nifti_to_rtstruct_conversion(nifti_dir, self.dicom_temp_dir.name, output_rt)
        self.signals.progress_updated.emit("Conversion to RTSTRUCT complete.")

    def _cleanup_nifti_dir(self, output_dir) -> None:
        """
        Removes the NIfTI segmentation output directory after processing is complete.
        This method attempts to delete the directory and emits progress updates to the GUI.

        Args:
            output_dir: The directory containing the NIfTI segmentation files to remove.

        Returns:
            None
        """
        try:
            if os.path.exists(output_dir):
                shutil.rmtree(output_dir)
                self.signals.progress_updated.emit("Nifti files removed.")
            else:
                self.signals.progress_updated.emit("Nifti files not found for removal.")
        except Exception as err:
            self.signals.progress_updated.emit(f"Failed to remove Nifti files: {err}")

    def _cleanup_temp_dir(self) -> None:
        """
        Cleans up the temporary DICOM directory if it exists.
        This method ensures that any temporary directory created
        for DICOM files is properly removed after processing.

        Returns:
            None
        """
        if self.dicom_temp_dir:
            self.dicom_temp_dir.cleanup()