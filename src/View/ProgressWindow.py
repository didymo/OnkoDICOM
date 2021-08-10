import threading

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import QThreadPool
from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout

from src.Model.Worker import Worker

class ProgressWindow(QDialog):
    signal_loaded = QtCore.Signal(tuple)
    signal_error = QtCore.Signal(Exception)

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

    def start(self, funct):
        """
        Function that executes 'funct' on new thread
        :param funct: function to execute.
        :param progress_callback: signal that receives the current progress of the loading.
        """
        worker = Worker(funct, self.interrupt_flag, progress_callback=True)
        worker.signals.result.connect(self.on_finish)
        worker.signals.error.connect(self.on_error)
        worker.signals.progress.connect(self.update_progress)

        self.threadpool.start(worker)
        self.exec_()

    def on_finish(self, result):
        self.signal_loaded.emit((result, self))

    def update_progress(self, progress_update):
        """
        Function responsible for updating the bar percentage and the label.
        :param progress_update: A tuple containing update text and update percentage
        """
        self.text_field.setText(progress_update[0])
        self.progress_bar.setValue(progress_update[1])

    def on_error(self, err):
        self.signal_error.emit(err)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.interrupt_flag.set()