from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QIcon, QPixmap

import src.View.StyleSheetReader as StyleSheetReader
from src.Controller.PathHandler import resource_path

def setup_window(window: QWidget, title: str) -> None:
    """
    Protected Method for Setting up the window, with Title, StyleSheet, MinimumSize and Icon
    :param window: QtWidgets.QWidget
    :param title: str
    :returns: None
    """
    # Adding Window Attributes
    window.setStyleSheet(StyleSheetReader.get_stylesheet())
    window.setWindowTitle(title)

    # Adding Window Icon
    window_icon: QIcon() = QIcon()
    window_icon.addPixmap(QPixmap(resource_path("res/images/icon.ico")), QIcon.Mode.Normal, QIcon.State.Off)
    window.setWindowIcon(window_icon)