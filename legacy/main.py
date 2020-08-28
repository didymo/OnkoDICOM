import warnings

from PyQt5.QtGui import QFont

warnings.filterwarnings("ignore")
import sys
import platform
from src.Controller.MainPageController import *
from legacy.src.Controller.interPageController import Controller


if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)
    
    # Set the font to Segoe UI, 9, when in windows OS
    if platform.system() == 'Windows':
        f = QFont("Segoe UI", 9)
        app.setFont(f)

    controller = Controller()
    controller.show_welcome()
    sys.exit(app.exec_())
