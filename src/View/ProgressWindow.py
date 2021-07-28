import threading
import platform

from pathlib import Path
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout, QMessageBox

from src.Model import ImageLoading
from src.Model.Worker import Worker
from src.View.ImageLoader import ImageLoader
from src.Controller.PathHandler import resource_path


class ProgressWindow(QDialog):
    signal_loaded = QtCore.Signal(tuple)
    signal_error = QtCore.Signal(int)
    signal_advise_calc_dvh = QtCore.Signal(bool)

    def __init__(self, *args, **kwargs):
        super(ProgressWindow, self).__init__(*args, **kwargs)

        # Setting up progress bar
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setGeometry(10, 50, 230, 20)
        self.progress_bar.setMaximum(100)

        self.setWindowTitle("Loading")
        self.setFixedSize(248, 80)

        self.text_field = QLabel("Loading")

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.text_field)
        self.layout.addWidget(self.progress_bar)
        self.setLayout(self.layout)

        self.threadpool = QThreadPool()
        self.interrupt_flag = threading.Event()

    def start_loading(self, selected_files):
        image_loader = ImageLoader(selected_files, self)
        image_loader.signal_request_calc_dvh.connect(self.prompt_calc_dvh)

        worker = Worker(
            image_loader.load, self.interrupt_flag, progress_callback=True)
        worker.signals.result.connect(self.on_finish)
        worker.signals.error.connect(self.on_error)
        worker.signals.progress.connect(self.update_progress)

        self.threadpool.start(worker)

    def on_finish(self, result):
        self.update_progress(("Initializing patient window...", 90))
        self.signal_loaded.emit((result, self))

    def update_progress(self, progress_update):
        """
        Function responsible for updating the bar percentage and the label.
        :param progress_update: A tuple containing update text and update
        percentage
        """
        self.text_field.setText(progress_update[0])
        self.progress_bar.setValue(progress_update[1])

    def prompt_calc_dvh(self):
        """
        Windows displays buttons in a different order from Linux. A check
        for platform is performed to ensure consistency of button
        positioning across platforms.
        """
        if platform.system() == "Linux":
            choice = QMessageBox.question(
                self, "Calculate DVHs?",
                "RTSTRUCT and RTDOSE datasets identified. Would you "
                "like to calculate DVHs? (This may take up to "
                "several minutes on some systems.)",
                QMessageBox.Yes | QMessageBox.No)

            if choice == QMessageBox.Yes:
                self.signal_advise_calc_dvh.emit(True)
            else:
                self.signal_advise_calc_dvh.emit(False)
        else:
            stylesheet_path = ""

            # Select appropriate style sheet
            if platform.system() == 'Darwin':
                stylesheet_path = Path.cwd().joinpath(
                    'res', 'stylesheet.qss')
            else:
                stylesheet_path = Path.cwd().joinpath(
                    'res', 'stylesheet-win-linux.qss')

            # Create a message box and add attributes
            mb = QMessageBox()
            mb.setIcon(QMessageBox.Question)
            mb.setWindowTitle("Calculate DVHs?")
            mb.setText("RTSTRUCT and RTDOSE datasets identified. Would you "
                       "like to calculate DVHs? (This may take up to several "
                       "minutes on some systems.)")
            button_no = QtWidgets.QPushButton("No")
            button_yes = QtWidgets.QPushButton("Yes")

            """We want the buttons 'No' & 'Yes' to be displayed in that 
            exact order. QMessageBox displays buttons in respect to their 
            assigned roles. (0 first, then 0 and so on) 'AcceptRole' is 0 
            and 'RejectRole' is 1 thus by counterintuitively assigning 'No' 
            to 'AcceptRole' and 'Yes' to 'RejectRole' the buttons are 
            positioned as desired. """
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

    def on_error(self, err):
        if type(err[1]) is ImageLoading.NotRTSetError:
            self.signal_error.emit(0)
        elif type(err[1]) is ImageLoading.NotAllowedClassError:
            self.signal_error.emit(1)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.interrupt_flag.set()
