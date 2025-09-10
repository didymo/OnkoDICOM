from PySide6 import QtWidgets
from typing import Optional
from PySide6.QtWidgets import QGroupBox, QGridLayout, QPushButton, QButtonGroup
from PySide6.QtGui import QPixmap, QImage, QMouseEvent, QPixmap, QPainter, QPen, QColor, QAction, QBrush,QCursor
from PySide6.QtCore import Qt, Slot

class RST_Holder(QtWidgets.QWidget):
    """Widget that holds the rst struct file that is being added to"""
    def __init__(self, parent = None, rtstuct_data = None):
        super().__init__(parent)
        self.parent = parent
        self.rt = rtstuct_data


        self.rt_display = Qlabel()
