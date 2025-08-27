import os
import shutil
import tempfile
import logging

from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.Worker import SegmentationWorkerSignals
import fnmatch

# TODO: Move this to own module?
# from ignore_files_in_dir import ignore_func

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

    def _create_copied_temporary_directory(self, dicom_dir):
        self.dicom_temp_dir = tempfile.TemporaryDirectory()

        if not dicom_dir:
            error_message = f'No dicom directory found. Received dicom_dir={dicom_dir!r}'
            raise ValueError(error_message)

        try:
            shutil.copytree(dicom_dir, self.dicom_temp_dir.name, ignore=_exclude_files_from_copy, dirs_exist_ok=True)
        except Exception as e:
            copy_error_message = f"Failed to copy DICOM files: {e}"
            raise ValueError(copy_error_message) from e

    def _connect_terminal_stream_to_gui(self):
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
        Executes the segmentation workflow.

        This method handles the entire segmentation process, from selecting the DICOM
        directory to running the segmentation task and converting the output to DICOM RTSTRUCT.
        """
        # Update text GUI for visual user feedback
        self.signals.progress_updated.emit("Starting segmentation workflow...")

        # Connect the terminal stream output to the progress text gui element
        self._connect_terminal_stream_to_gui()

        # Create the output path for Nifti segmentation files
        output_dir = os.path.join(self.dicom_dir, "segmentations")
        os.makedirs(output_dir, exist_ok=True)
        output_rt = os.path.join(self.dicom_dir, "rtss.dcm")

        try:
            # Copy contents from selected dir to temp dir (excludes rt*.dcm files)
            self._create_copied_temporary_directory(self.dicom_dir)

            # Call total segmentator API
            totalsegmentator(input=self.dicom_temp_dir.name,
                             output=output_dir,
                             task=task,
                             output_type="nifti",
                             device="cpu",
                             fastest=fast
                             )

            nifti_to_rtstruct_conversion(output_dir, self.dicom_temp_dir.name, output_rt)
            self.signals.progress_updated.emit("Conversion to RTSTRUCT complete.")
            try:
                if os.path.exists(output_dir):
                    shutil.rmtree(output_dir)
                    self.signals.progress_updated.emit("Nifti files removed.")
                else:
                    self.signals.progress_updated.emit("Nifti files not found for removal.")
            except Exception as remove_err:
                self.signals.progress_updated.emit(f"Failed to remove Nifti files: {remove_err}")
            self.signals.finished.emit()

        except Exception as e:
            self.signals.error.emit(str(e))  # Emit the error message
            logger.exception(f"Segmentation workflow failed: {e}") # Log the full exception

        finally:
            if self.dicom_temp_dir is not None:
                self.dicom_temp_dir.cleanup()


# This function is specific to loading the dcm image files for Total Segmnetator API
def _exclude_files_from_copy(directory, contents):
    """Filters files and directories to be excluded when copying.

    This function is used with `shutil.copytree` to ignore specific files
    or directories during the copy operation.  It currently excludes files
    matching the pattern "rt*.dcm".

    Args:
        directory: The directory being scanned.
        contents: A list of files and directories within the directory.

    Returns:
        A list of files and directories to be ignored.
    """
    exclude_patterns = ["rt*.dcm"]

    filtered_files = []
    filtered_files.extend(
        file
        for file in contents
        if any(
            fnmatch.fnmatch(file.lower(), pattern)
            for pattern in exclude_patterns
        )
    )
    return filtered_files
