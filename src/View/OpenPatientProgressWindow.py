import logging
import os
import platform
from pathlib import Path

from PIL.ImageQt import QPixmap
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QMessageBox
from PySide6 import QtCore, QtGui, QtWidgets
from src.View.ProgressWindow import ProgressWindow
from src.View.ImageLoader import ImageLoader
from src.Controller.PathHandler import resource_path, delete_files
from src.View.StyleSheetReader import StyleSheetReader

logger = logging.getLogger(__name__)


class OpenPatientProgressWindow(ProgressWindow):

    def __init__(self, *args,
                 kwargs=QtCore.Qt.WindowTitleHint |
                        QtCore.Qt.WindowCloseButtonHint):
        super(OpenPatientProgressWindow, self).__init__(*args, kwargs)

    def start_loading(self, selected_files, existing_rtss=None):
        image_loader = ImageLoader(selected_files, existing_rtss, self)
        image_loader.signal_request_calc_dvh.connect(
            self.prompt_calc_dvh)
        # Connect slot for incorrect slice detection
        image_loader.incorrect_slice_orientation.connect(
            self.prompt_warn_incorrect_slice)

        # Start loading the selected files on separate thread
        self.start(image_loader.load)


    def prompt_calc_dvh(self):
        """
        Windows displays buttons in a different order from Linux. A check for
        platform is performed to ensure consistency of button positioning across
        platforms.
        """
        message = "DVHs not present in RTDOSE or do not correspond to ROIs. "
        message += "Would you like to calculate DVHs? (This may take up to "
        message += "several minutes on some systems.)"
        if platform.system() == "Linux":
            choice = QMessageBox.question(self, "Calculate DVHs?", message,
                                          QMessageBox.Yes | QMessageBox.No)

            if choice == QMessageBox.Yes:
                self.signal_advise_calc_dvh.emit(True)
            else:
                self.signal_advise_calc_dvh.emit(False)
        else:
            # Create a message box and add attributes
            mb = QMessageBox()
            mb.setIcon(QMessageBox.Question)
            mb.setWindowTitle("Calculate DVHs?")
            mb.setText(message)
            button_no = QtWidgets.QPushButton("No")
            button_yes = QtWidgets.QPushButton("Yes")

            # We want the buttons 'No' & 'Yes' to be displayed in that
            # exact order. QMessageBox displays buttons in respect to
            # their assigned roles. (0 first, then 1 and so on)
            # 'AcceptRole' is 0 and 'RejectRole' is 1 thus by assigning
            # 'No' to 'AcceptRole' and 'Yes' to 'RejectRole' the buttons
            # are positioned as desired.
            mb.addButton(button_no, QtWidgets.QMessageBox.ButtonRole.AcceptRole)
            mb.addButton(button_yes, QtWidgets.QMessageBox.ButtonRole.RejectRole)

            # Apply stylesheet to the message box and add icon to the window
            mb.setStyleSheet(StyleSheetReader().get_stylesheet())
            mb.setWindowIcon(QtGui.QIcon(resource_path(Path.cwd().joinpath(
                'res', 'images', 'btn-icons', 'onkodicom_icon.png'))))
            mb.exec_()

            if mb.clickedButton() == button_yes:
                self.signal_advise_calc_dvh.emit(True)
            else:
                self.signal_advise_calc_dvh.emit(False)

    @Slot()
    def prompt_warn_incorrect_slice(self, slice_list: list) -> None:
        """
        Prompts user about incorrectly aligned DICOM slices.
        Displays a warning dialog showing non-axially aligned slices and
        offers the user an option to permanently delete the files.
        Handles user's choice by either deleting files or acknowledging the issue.

        Args:
            slice_list: A list of file paths for incorrectly aligned slices.
        """
        # Create string of slices
        slices_str = "\n".join(os.path.basename(slice_path) for slice_path in slice_list)

        # Setup message box
        text = f"The following slices are not Axially aligned and"\
            f" have been omitted from the dataset:\n\n {slices_str}"\
            f"\n\nWould you like to delete the file(s)? \n"\
            f"(Warning, this action is irreversible!)"
        msgbox = self._styled_msgbox("Incorrect Slice Alignment", text)

        # Add buttons in specific order
        button_no = QtWidgets.QPushButton("No")
        button_yes = QtWidgets.QPushButton("Yes")
        msgbox.addButton(button_no, QtWidgets.QMessageBox.ButtonRole.AcceptRole)
        msgbox.addButton(button_yes, QtWidgets.QMessageBox.ButtonRole.RejectRole)

        msgbox.exec_()

        if msgbox.clickedButton() == button_yes:
            # Call to delete files pass slice_list
            slices_not_deleted = delete_files(slice_list)
            self.display_files_deleted_result(slices_not_deleted)

        elif msgbox.clickedButton() == button_no:
            self.signal_acknowledge_incorrect_slice.emit()

    def display_files_deleted_result(self, slices_not_deleted: list) -> None:
        """
        Displays the result of file deletion attempts.
        Shows a message box informing the user about the success or failure
        of deleting incorrectly aligned DICOM slices. Emits a signal to
        acknowledge the slice orientation issue.

        Args:
            slices_not_deleted: A list of file paths that could not be deleted.
        """
        if slices_not_deleted:
            failed_str = "\n".join(os.path.basename(f) for f in slices_not_deleted)
            text = f"The following file(s) were not deleted:\n\n{failed_str}\n\n\
                    Please manually delete them."
        else:
            text = "Files were successfully deleted."

        msgbox = self._styled_msgbox("Files Deleted", text)
        button_ok = QtWidgets.QPushButton("Ok")
        msgbox.addButton(button_ok, QtWidgets.QMessageBox.ButtonRole.AcceptRole)
        msgbox.exec_()

        if msgbox.clickedButton() == button_ok:
            self.signal_acknowledge_incorrect_slice.emit()

    def _styled_msgbox(self, title: str, text: str, icon_path: str = 'res/images/icon.icns') -> QMessageBox:
        """
        Creates a consistently styled QMessageBox with OnkoDICOM branding.
        Generates a QMessageBox with a standardized appearance.

        Args:
            title: The window title for the message box.
            text: The main text content of the message box.
            icon_path: Path to the icon image, defaults to OnkoDICOM icon.

        Returns:
            A configured QMessageBox ready for display.
        """
        msgbox = QMessageBox(self)
        pixmap = (QPixmap(resource_path(icon_path))
                  .scaledToHeight(100, QtCore.Qt.TransformationMode.SmoothTransformation))
        msgbox.setIconPixmap(pixmap)
        msgbox.setWindowTitle(title)
        msgbox.setText(text)
        msgbox.setStyleSheet(StyleSheetReader().get_stylesheet())
        return msgbox