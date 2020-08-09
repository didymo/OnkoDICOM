import os
import warnings

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtGui import QFont

warnings.filterwarnings("ignore")
import sys
import platform
from src.Controller.TopLevelController import Controller
from src.View.fonts_service import FontService

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

    app_font = QFont()
    app_font.setFamily(FontService.get_instance().font_family())
    app_font.setPixelSize(FontService.get_instance().get_scaled_font_pixel_size(app, 10))
    app.setFont(app_font)

    controller = Controller()
    controller.show_welcome()
    sys.exit(app.exec_())

