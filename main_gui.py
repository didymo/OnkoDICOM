import os
import warnings

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QFont

warnings.filterwarnings("ignore")
import sys
import platform
from src.Controller.top_level_controller import Controller

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
    app.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)

    # Set the font to Segoe UI, 9, when in windows OS
    if platform.system() == 'Windows':
        f = QFont("Segoe UI", 9)
        app.setFont(f)

    controller = Controller()
    controller.show_welcome()
    sys.exit(app.exec_())

