from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtWidgets import QGraphicsPixmapItem


class DrawBoundingBox(QtWidgets.QGraphicsScene):
    """
    Object responsible for updating and displaying the bounds of the ROI draw.
    """

    def __init__(self, image_to_paint, pixmap_data):
        super().__init__()
        self.addItem(QGraphicsPixmapItem(image_to_paint))
        self.img = image_to_paint
        self.pixmap_data = pixmap_data
        self.drawing = False
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None
        self.box = None

    def draw_bounding_box(self, new_box=False):
        """
            his method is called to draw the bounding box in draw ROI window.
            :param new_box: check if any box has been drawn before
        """
        if new_box:
            self.box = QtWidgets.QGraphicsRectItem(self.start_x, self.start_y,
                                                   0, 0)
            pen = QtGui.QPen(QtGui.QColor("red"))
            pen.setStyle(QtCore.Qt.DashDotDotLine)
            pen.setWidth(0)
            self.box.setPen(pen)
            self.addItem(self.box)
        else:
            if self.start_x < self.end_x:
                x = self.start_x
                width = self.end_x - self.start_x
            else:
                x = self.end_x
                width = self.start_x - self.end_x

            if self.start_y < self.end_y:
                y = self.start_y
                height = self.end_y - self.start_y
            else:
                y = self.end_y
                height = self.start_y - self.end_y

            self.box.setRect(x, y, width, height)

    def mousePressEvent(self, event):
        """
            This method is called to handle a mouse press event
            :param event: the mouse event
        """
        if self.box:
            self.removeItem(self.box)
        self.drawing = True
        self.start_x = event.scenePos().x()
        self.start_y = event.scenePos().y()
        self.draw_bounding_box(new_box=True)

    def mouseMoveEvent(self, event):
        """
            This method is called to handle a mouse move event
            :param event: the mouse event
        """
        if self.drawing:
            self.end_x = event.scenePos().x()
            self.end_y = event.scenePos().y()
            self.draw_bounding_box()

    def mouseReleaseEvent(self, event):
        """
            This method is called to handle a mouse release event
            :param event: the mouse event
        """
        if self.drawing:
            self.drawing = False
            self.end_x = event.scenePos().x()
            self.end_y = event.scenePos().y()
            self.draw_bounding_box()
