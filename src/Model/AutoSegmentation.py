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
        self.dicom_dir = self.patient_dict_container.path # Get the current loaded dir to DICOM series
        self.temp_dir = tempfile.mkdtemp()

        self.signals = SegmentationWorkerSignals()

        # Connect worker signals to controller slots
        self.signals.progress_updated.connect(self.controller.update_progress_text)
        self.signals.finished.connect(self.controller.on_segmentation_finished)
        self.signals.error.connect(self.controller.on_segmentation_error)

    def _create_copied_temporary_directory(self, dicom_dir):
        if not dicom_dir:
            self.signals.error.emit(f'No dicom directory found. Received dicom_dir={dicom_dir!r}')
            return

        try:
            shutil.copytree(dicom_dir, self.temp_dir, ignore=_ignore_func, dirs_exist_ok=True)
        except Exception as e:
            logger.exception("Failed to copy DICOM files.")
            self.signals.error.emit("Failed to copy DICOM files.")

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

        # Copy contents from selected dir to temp dir (excludes rt*.dcm files)
        self._create_copied_temporary_directory(self.dicom_dir)

        # Connect the terminal stream output to the progress text gui element
        self._connect_terminal_stream_to_gui()

        # Create the output path for Nifti segmentation files
        output_dir = os.path.join(self.dicom_dir, "segmentations")
        os.makedirs(output_dir, exist_ok=True)
        output_rt = os.path.join(self.dicom_dir, "rtss.dcm")

        # Call total segmentator API
        try:
            totalsegmentator(input=self.temp_dir,
                             output=output_dir,
                             task=task,
                             output_type="nifti",  # output to dicom
                             device="cpu",  # Run on cpu
                             fastest=fast
                             )

            output_rt = os.path.join(self.dicom_dir, "rtss.dcm")

        except Exception as e:
            self.signals.error.emit("Failed to run segmentation workflow.")
            logger.exception(e)
            shutil.rmtree(output_dir)

        try:
            nifti_to_rtstruct_conversion(output_dir, self.temp_dir, output_rt)
            self.controller.update_progress_text("Segmentation complete.")

        except Exception as e:
            self.controller.update_progress_text("Segmentation conversion failed.")
            logger.error(f"Segmentation conversion failed.{e}")


# This function is specific to loading the dcm image files for Total Segmnetator API
def _ignore_func(directory, contents):
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
    ignored_items = []
    exclude_patterns = ["rt*.dcm"]

    for pattern in exclude_patterns:
        if pattern.endswith('/'):
            dir_name = pattern.rstrip('/')
            if dir_name in contents and os.path.isdir(os.path.join(directory, dir_name)):
                ignored_items.append(dir_name)
        elif '*' in pattern or '?' in pattern:
            ignored_items.extend(
                item for item in contents if fnmatch.fnmatch(item, pattern)
            )
        elif pattern in contents and os.path.isfile(os.path.join(directory, pattern)):
            ignored_items.append(pattern)
    return ignored_items
