import warnings
warnings.filterwarnings("ignore")
import sys
from src.Controller.mainPageController import *
from src.Controller.interPageController import Controller


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    controller = Controller()
    controller.show_welcome()
    sys.exit(app.exec_())
