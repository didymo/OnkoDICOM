import logging
import sys
import traceback

from PySide6.QtCore import QObject, Signal, QRunnable, Slot

class SegmentationWorkerSignals(QObject):
    progress_updated = Signal(str)
    finished = Signal()
    error = Signal(str)

class WorkerSignals(QObject):
    finished = Signal()
    error = Signal(tuple)
    result = Signal(object)
    progress = Signal(object)


class Worker(QRunnable):
    """
    Multi-threading worker class that is executed by a QThreadPool. The
    purpose of this class is to provide a simple way of executing any
    function on a separate thread, which proves especially useful in a GUI
    project when a long calculation needs to run in a separate thread to the
    GUI thread.

    Example usage:
    calcpi_worker = Worker(calculate_pi, 500)   # Calculates pi to 500 decimal
    places
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

        # When the constructor for this class is called with a keyword
        # argument 'progress_callback' set to True, this will allow the
        # worker's progress signal to be connected to. However, this means
        # that the function being called into the new thread will require a
        # progress_callback parameter (which will, within the function being
        # called, be a reference to the worker's progress signal). Within
        # the called function, the progress_callback parameter can be
        # emitted to. Below is an example of how to utilize this aspect of
        # the Worker class.

        # Creating a worker and connecting to it's callback:
        #   worker = Worker(slow_calc_fn,
        #   list_of_inputs, progress_callback=True)
        #   worker.signals.progress.connect(self.update_progress_bar)

        # Defining the function to use and emitting signals to the callback
        #   def slow_calc_fn(list_of_inputs, progress_callback):
        #       progress = do_part_of_calc(...)
        #       progress_callback.emit(progress)

        if 'progress_callback' in self.kwargs \
                and self.kwargs['progress_callback']:
            self.kwargs['progress_callback'] = self.signals.progress
        elif 'progress_callback' in self.kwargs \
                and not self.kwargs['progress_callback']:
            del self.kwargs['progress_callback']

    @Slot()
    def run(self):
        """
        Executed on threadpool.start(..)
        """
        try:
            # Execute the function
            result = self.fn(*self.args, **self.kwargs)
        except:
            # Emit signal error when exception occurs
            logging.exception(traceback.format_exc())       # Log the traceback
            # exc_type: the type of the exception being handled
            # (a subclass of BaseException)
            # value: the exception instance (an instance of the exception type)
            exc_type, value = sys.exc_info()[:2]
            self.signals.error.emit((exc_type, value, traceback.format_exc()))
        else:
            # When the function has finished executing emit the result
            self.signals.result.emit(result)
        finally:
            # Additionally emit a signal indicating the that the function
            # has completed execution
            self.signals.finished.emit()
