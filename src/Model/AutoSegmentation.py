import os
import shutil
import tempfile
import logging
from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.Worker import SegmentationWorkerSignals
import fnmatch
from totalsegmentator.python_api import totalsegmentator
from src.Model.NiftiToRtstructConverter import nifti_to_rtstruct_conversion
from src.View.util.RedirectStdOut import ConsoleOutputStream, redirect_output_to_gui, setup_logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AutoSegmentation:
    """Handles the automatic segmentation process.

    This class manages the workflow for running TotalSegmentator, including
    copying DICOM files, setting up the segmentation task, and converting the
    output to DICOM RTSTRUCT format.
    """

    def __init__(self, controller):
        self.controller = controller
        self.patient_dict_container = PatientDictContainer()
        self.dicom_dir = self.patient_dict_container.path  # Get the current loaded dir to DICOM series
        self.dicom_temp_dir = None

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

    def run_segmentation_workflow(self, task, fast):
        """
        Runs the full segmentation workflow for a given task and speed setting.
        This method manages the process of segmenting DICOM images, converting the
        results to RTSTRUCT, and cleaning up temporary files.

        Args:
            task: The segmentation task to perform.
            fast: Whether to use the fastest segmentation mode.

        Returns:
            None
        """
        self.signals.progress_updated.emit("Starting segmentation workflow...")
        self._connect_terminal_stream_to_gui()
        output_dir, output_rt = self._prepare_output_paths()

        try:
            self._copy_temp_dicom_dir()
            self._run_totalsegmentation(task, fast, output_dir)
            self._convert_to_rtstruct(output_dir, output_rt)
            self._cleanup_nifti_dir(output_dir)
            self.signals.finished.emit()
        except Exception as e:
            self.signals.error.emit(str(e))
            logger.exception("Segmentation workflow failed")
        finally:
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
        Copies the DICOM directory to a temporary location for processing.
        This method creates a temporary directory and copies the DICOM files
        into it, excluding RTSTRUCT files.

        Raises:
            ValueError: If the DICOM directory is not set or copying fails.
        """
        if not self.dicom_dir:
            raise ValueError(f"No dicom directory found: {self.dicom_dir!r}")
        self.dicom_temp_dir = tempfile.TemporaryDirectory()
        try:
            shutil.copytree(
                self.dicom_dir,
                self.dicom_temp_dir.name,
                ignore=shutil.ignore_patterns("rt*.dcm"),
                dirs_exist_ok=True,
            )
        except Exception as e:
            raise ValueError(f"Failed to copy DICOM files: {e}") from e

    def _run_totalsegmentation(self, task, fast, output_dir) -> None:
        """
        Runs the TotalSegmentator segmentation task and saves the results.
        This method executes the segmentation process using the specified task and
        speed, and stores the output in the given directory.

        Args:
            task: The segmentation task to perform.
            fast: Whether to use the fastest segmentation mode.
            output_dir: Directory to store the segmentation results.

        Returns:
            None
        """
        totalsegmentator(
            input=self.dicom_temp_dir.name,
            output=output_dir,
            roi_subset=task,
            output_type="nifti",
            device="cpu",
            fastest=fast,
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
        This method ensures that any temporary directory created for DICOM files is properly removed after processing.

        Returns:
            None
        """
        if self.dicom_temp_dir:
            self.dicom_temp_dir.cleanup()