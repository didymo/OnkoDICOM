from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QThreadPool
from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout

from src.Model import ImageLoading
from src.Model.Worker import Worker
from src.View.ImageLoader import ImageLoader


class ProgressWindow(QDialog):
    signal_loaded = QtCore.pyqtSignal(tuple)
    signal_error = QtCore.pyqtSignal(int)

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

    def start_loading(self, selected_files):
        image_loader = ImageLoader(selected_files)

        worker = Worker(image_loader.load)
        worker.signals.result.connect(self.on_finish)
        worker.signals.error.connect(self.on_error)
        worker.signals.progress.connect(self.update_progress)

        self.threadpool.start(worker)

    def on_finish(self, results):
        self.update_progress(("Initalizing patient window...", 90))
        self.signal_loaded.emit((results, self))

    def update_progress(self, progress_update):
        """
        Function responsible for updating the bar percentage and the label.
        :param progress_update: A tuple containing update text and update percentage
        """
        self.text_field.setText(progress_update[0])
        self.progress_bar.setValue(progress_update[1])

    def on_error(self, err):
        if type(err[1]) is ImageLoading.NotRTSetError:
            self.signal_error.emit(0)
        elif type(err[1]) is ImageLoading.NotAllowedClassError:
            self.signal_error.emit(1)