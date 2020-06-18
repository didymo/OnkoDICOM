from PyQt5.QtWidgets import QMessageBox, QDesktopWidget, QApplication
from PyQt5 import QtCore, QtGui, QtWidgets
import sys

from Gui_redesign.Controller.new_gui_controller import *


class Controller:

    # Initialisation function that creates an instance of each window
    def __init__(self):
        self.welcome_window = QtWidgets.QMainWindow()

    def show_welcome(self):
        """
        Display welcome page
        """
        self.welcome_window = NewWelcomeGui()
        # After this window the progress bar will be displayed if a path is provided
        self.welcome_window.show()
