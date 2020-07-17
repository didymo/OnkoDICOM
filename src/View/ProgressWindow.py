from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QThreadPool
from PyQt5.QtWidgets import QDialog, QLabel, QVBoxLayout

from src.Model import ImageLoading
from src.Model.Worker import Worker
from src.View.ImageLoader import ImageLoader

# Used to update progress bar
percent_counter = 0

class ProgressWindow(QDialog):
    signal_loaded = QtCore.pyqtSignal(tuple)
    signal_error = QtCore.pyqtSignal(int)

    def __init__(self, *args, **kwargs):
        super(ProgressWindow, self).__init__(*args, **kwargs)

        # Setting up progress bar
        self.progress_bar = QtWidgets.QProgressBar(self)
        self.progress_bar.setGeometry(10, 50, 230, 20)
        self.progress_bar.setMaximum(100)

        self.setWindowTitle("Loading")
        self.resize(248, 80)

        self.text_field = QLabel("Loading")

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.text_field)
        self.setLayout(self.layout)

        self.threadpool = QThreadPool()

    def start_loading(self, selected_files):
        image_loader = ImageLoader(selected_files)

        worker = Worker(image_loader.load)
        worker.signals.result.connect(self.on_finish)
        worker.signals.error.connect(self.on_error)
        image_loader.signal_progress.connect(self.update_text)

        self.threadpool.start(worker)

    def on_finish(self, results):
        self.update_text("Initalizing patient window...")
        self.signal_loaded.emit((results, self))

    def update_text(self, new_text):
        """
                Function responsible for updating the bar percentage and the label
        """
        self.text_field.setText(new_text)

        global percent_counter
        # Increments every time the text is updated.
        percent_counter = percent_counter + 1

        if percent_counter == 1:
            self.progress_bar.setValue(10)
        elif percent_counter == 2:
            self.progress_bar.setValue(30)
        elif percent_counter == 3:
            self.progress_bar.setValue(60)
        elif percent_counter == 4:
            self.progress_bar.setValue(75)
        elif percent_counter == 5:
            self.progress_bar.setValue(85)
        else:
            self.progress_bar.setValue(95)

    def on_error(self, err):
        if type(err[1]) is ImageLoading.NotRTSetError:
            self.signal_error.emit(0)
