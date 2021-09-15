import platform
from pathlib import Path
from PySide6.QtWidgets import QMessageBox
from PySide6 import QtCore, QtGui, QtWidgets
from src.View.ProgressWindow import ProgressWindow
from src.View.ImageFusion.MovingImageLoader import MovingImageLoader
from src.Controller.PathHandler import resource_path


class ImageFusionProgressWindow(ProgressWindow):

    def __init__(self, *args,
                 kwargs=QtCore.Qt.WindowTitleHint |
                 QtCore.Qt.WindowCloseButtonHint):
        super(ImageFusionProgressWindow, self).__init__(*args, kwargs)

    def start_loading(self, selected_files, existing_rtss=None):
        image_loader = MovingImageLoader(
            selected_files, existing_rtss, self)
        image_loader.signal_request_calc_dvh.connect(
            self.prompt_calc_dvh)

        # Start loading the selected files on separate thread
        self.start(image_loader.load)

    def prompt_calc_dvh(self):
        """
        Windows displays buttons in a different order from Linux. A check for
        platform is performed to ensure consistency of button positioning 
        across platforms.
        """
        message = "RTSTRUCT and RTDOSE datasets identified. Would you like to "
        message += "calculate DVHs? (This may take up to several minutes on "
        message += "some systems.)"
        if platform.system() == "Linux":
            choice = QMessageBox.question(self, "Calculate DVHs?", message,
                                          QMessageBox.Yes | QMessageBox.No)

            if choice == QMessageBox.Yes:
                self.signal_advise_calc_dvh.emit(True)
            else:
                self.signal_advise_calc_dvh.emit(False)
        else:
            stylesheet_path = ""

            # Select appropriate style sheet
            if platform.system() == 'Darwin':
                stylesheet_path = Path.cwd().joinpath('res', 'stylesheet.qss')
            else:
                stylesheet_path = Path.cwd().joinpath(
                    'res', 'stylesheet-win-linux.qss')

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
            mb.addButton(button_no, QtWidgets.QMessageBox.AcceptRole)
            mb.addButton(button_yes, QtWidgets.QMessageBox.RejectRole)

            # Apply stylesheet to the message box and add icon to the window
            mb.setStyleSheet(open(stylesheet_path).read())
            mb.setWindowIcon(QtGui.QIcon(resource_path(Path.cwd().joinpath(
                'res', 'images', 'btn-icons', 'onkodicom_icon.png'))))
            mb.exec_()

            if mb.clickedButton() == button_yes:
                self.signal_advise_calc_dvh.emit(True)
            else:
                self.signal_advise_calc_dvh.emit(False)
