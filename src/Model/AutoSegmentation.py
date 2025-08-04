import os
import shutil
import tempfile
import logging

from src.Model.PatientDictContainer import PatientDictContainer
import fnmatch

from PySide6.QtWidgets import QMessageBox

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

    def __init__(self, task: str, fast: bool, controller):
        self.task = task
        self.fast = fast
        self.controller = controller
        self.patient_dict_container = PatientDictContainer()
        self.dicom_dir = self.patient_dict_container.path
        self.temp_dir = tempfile.mkdtemp()


    def _create_copied_temporary_directory(self):
        """
        Creates a copy of the current working directory and moves it to
        a temp directory with the purpose of excluding files
        listed in the ignore_files function
        """
        if not self.dicom_dir:
            self.controller.update_progress_text("No DICOM directory found.")
            return

        try:
            shutil.copytree(self.dicom_dir, self.temp_dir, ignore=_ignore_func, dirs_exist_ok=True)
        except Exception as e:
            self.controller.update_progress_text("Failed to copy DICOM files.")

    def _connect_terminal_stream_to_gui(self):
        """
        Connects the terminal stream to the GUI window to
        update the progress text
        """
        output_stream = ConsoleOutputStream()
        output_stream.new_text.connect(self.controller.update_progress_text)
        redirect_output_to_gui(output_stream)
        setup_logging(output_stream)

    def run_segmentation_workflow(self):
        """
        Executes the segmentation workflow.

        This method handles the entire segmentation process, from selecting the DICOM
        directory to running the segmentation task and converting the output to DICOM RTSTRUCT.
        """
        # Clear previous progress text
        self.controller.update_progress_text("Starting segmentation workflow...")

        # Copy contents from selected dir to temp dir (excludes rt*.dcm files)
        self._create_copied_temporary_directory()

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
                             task=self.task,
                             output_type="nifti",  # output to dicom
                             device="cpu",  # Run on cpu
                             fastest=self.fast
                             )
        except Exception as e:
            self.controller.update_progress_text(f"Failed to segment DICOM files.{e}")
            logger.error(f"Failed to segment DICOM files.{e}")

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
