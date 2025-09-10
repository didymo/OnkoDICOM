import logging

from PySide6.QtCore import QObject, Signal
import sys


class ConsoleOutputStream(QObject):
    """A QObject subclass to redirect console output to a GUI element.

    This class intercepts text written to stdout and emits it as a Qt signal,
    allowing console output to be displayed in a GUI while maintaining original
    console visibility.
    """
    new_text = Signal(str)

    def write(self, text):
        self.new_text.emit(text)
        sys.__stdout__.write(text)  # Also write to original stdout for console visibility
        sys.__stdout__.flush()

    def flush(self):
        sys.__stdout__.flush()

def redirect_output_to_gui(console_stream: ConsoleOutputStream):
    sys.stdout = console_stream
    # sys.stderr = console_stream  # Redirect stderr too

class QtLogHandler(logging.Handler):
    """Custom logging handler to emit logs to Qt GUI via ConsoleOutputStream."""
    def __init__(self, console_stream: ConsoleOutputStream):
        super().__init__()
        self.console_stream = console_stream

    def emit(self, record):
        msg = self.format(record)
        self.console_stream.new_text.emit(msg + "\n")

def setup_logging(console_stream: ConsoleOutputStream):
    """Sets up logging to redirect logs to the GUI.

    Configures a QtLogHandler to emit log records to the provided
    ConsoleOutputStream, allowing log messages to be displayed in the GUI.
    """
    handler = QtLogHandler(console_stream)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)