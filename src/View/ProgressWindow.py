from PyQt5 import QtCore
from PyQt5.QtCore import QThreadPool
from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout

from src.Model.Worker import Worker
from src.View.ImageLoader import ImageLoader


class ProgressWindow(QDialog):
    signal_loaded = QtCore.pyqtSignal(tuple)

    def __init__(self, *args, **kwargs):
        super(ProgressWindow, self).__init__(*args, **kwargs)

        self.setWindowTitle("Loading")
        self.resize(150, 60)

        self.text_field = QLabel("Loading")

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.text_field)
        self.setLayout(self.layout)

        self.threadpool = QThreadPool()

    def start_loading(self, selected_files):
        image_loader = ImageLoader(selected_files)

        worker = Worker(image_loader.load)
        worker.signals.result.connect(self.on_finish)
        worker.signals.error.connect(self.print_error)
        image_loader.signal_progress.connect(self.update_text)

        self.threadpool.start(worker)

    def on_finish(self, results):
        self.update_text("Initalizing patient window...")
        self.signal_loaded.emit((results, self))

    def update_text(self, new_text):
        self.text_field.setText(new_text)

    def print_error(self, err):
        # TODO error handling
        print(err)