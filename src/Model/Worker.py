import sys
import traceback

from PyQt5.QtCore import QObject, pyqtSignal, QRunnable, pyqtSlot


class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(object)


class Worker(QRunnable):
    """
    Multi-threading worker class that is executed by a QThreadPool.
    Example usage:
    calcpi_worker = Worker(calculate_pi, 500)   # Calculates pi to 500 decimal places
    calcpi_worker.signals.result.connect(display_result)
    threadpool.start(calcpi_worker)
    """

    def __init__(self, fn, *args, **kwargs):
        """
        :param fn: The function to be executed by a worker.
        :param args: The function's parameters.
        :param kwargs: Any kwargs used by the function.
        """
        super(Worker, self).__init__()

        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        if 'progress_callback' in self.kwargs and self.kwargs['progress_callback'] is True:
            self.kwargs['progress_callback'] = self.signals.progress

    @pyqtSlot()
    def run(self):
        """
        Executed on threadpool.start(..)
        """
        try:
            # Execute the function
            result = self.fn(*self.args, **self.kwargs)
        except:
            # Emit signal error when exception occurs
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            # When the function has finished executing emit the result
            self.signals.result.emit(result)
        finally:
            # Additionally emit a signal indicating the that the function has completed execution
            self.signals.finished.emit()
