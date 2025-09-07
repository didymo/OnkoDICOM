import os
import warnings
import sys
import platform

from PySide6 import QtWidgets, QtCore
from PySide6.QtGui import QFont
from src.Model.Configuration import Configuration
from src.Controller.TopLevelController import Controller
from src.View.util.RedirectStdOut import ConsoleOutputStream
warnings.filterwarnings("ignore")

QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

if __name__ == "__main__":

    # On some configurations error traceback is not being displayed
    #     when the program crashes. This is a workaround.
    sys._excepthook = sys.excepthook

    def exception_hook(exctype, value, traceback):
        print(exctype, value, traceback)
        sys._excepthook(exctype, value, traceback)
        sys.exit(1)

    sys.excepthook = exception_hook

    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    app = QtWidgets.QApplication(sys.argv)

    print("PDPI: " + str(app.primaryScreen().physicalDotsPerInch()))

    # Allow redirected stream in AutoSegmentation to still output to console
    sys.stdout = ConsoleOutputStream()

    # Set the font to Segoe UI, 9, when in windows OS
    if platform.system() == 'Windows':
        f = QFont("Segoe UI", 9)
        app.setFont(f)
    elif platform.system() == 'Darwin':
        f = QFont("Helvetica Neue", 13)
        app.setFont(f)

    if len(sys.argv) > 1:
        controller = Controller(default_directory=sys.argv[1])
        controller.show_open_patient()
    else:
        # Get the default DICOM directory from SQLite database
        # stored in a hidden directory in the user home directory
        configuration = Configuration()
        default_dir = configuration.get_default_directory()
        if default_dir is None:
            controller = Controller()
            controller.show_first_time_welcome()
        else:
            controller = Controller(default_directory=default_dir)
            controller.show_welcome()

    sys.exit(app.exec_())
