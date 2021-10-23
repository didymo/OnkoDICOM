from PySide6 import QtWidgets, QtCore, QtGui


class GraphicsView(QtWidgets.QGraphicsView):
    """
    A child class of the QGraphicsView that overides mouse events
    """

    def __init__(self, parent):
        super(GraphicsView, self).__init__(parent)

    def mouseMoveEvent(self, event):
        self.parent().mouseMoveEvent(event)

    def keyPressEvent(self, event):
        self.parent().keyPressEvent(event)

