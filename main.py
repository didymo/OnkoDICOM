import os
import warnings

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QFont

warnings.filterwarnings("ignore")
import sys
import platform
from src.Controller.TopLevelController import Controller
import importlib

QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)

if __name__ == "__main__":

    # On some configurations error traceback is not being displayed when the program crashes. This is a workaround.
    sys._excepthook = sys.excepthook
    def exception_hook(exctype, value, traceback):
        print(exctype, value, traceback)
        sys._excepthook(exctype, value, traceback)
        sys.exit(1)

    sys.excepthook = exception_hook

    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    app = QtWidgets.QApplication(sys.argv)

    print("PDPI: " + str(app.primaryScreen().physicalDotsPerInch()))

    # Set the font to Segoe UI, 9, when in windows OS
    if platform.system() == 'Windows':
        f = QFont("Segoe UI", 9)
        app.setFont(f)

    if len(sys.argv) > 1:
        controller = Controller(default_directory=sys.argv[1])
        controller.show_open_patient()
    else:
        controller = Controller()
        controller.show_welcome()

    sys.exit(app.exec_())
