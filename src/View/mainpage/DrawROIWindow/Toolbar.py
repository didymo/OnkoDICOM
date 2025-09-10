from PySide6.QtWidgets import QToolBar, QColorDialog
from PySide6.QtGui import QAction, QColor, QFontDatabase
from PySide6.QtCore import Signal



class CutsomToolbar(QToolBar):
    """Class to hold the draw ROI features"""
    colour = Signal(QColor)

    def __init__(self, parent=None, canvas_label = None, left_label = None):
        super().__init__("Toolbar", parent)
        self.parent = parent
        self.setFont(QFontDatabase.systemFont(QFontDatabase.GeneralFont))
        #Sets communication between classes
        self.canvas_label = canvas_label
        self.left_label = left_label

        #sets darwing variables
        self.is_drawing = False
        self.rt_value = False

        colourAction = QAction("Choose Colour",self)
        colourAction.triggered.connect(self.change_colour)
        self.addAction(colourAction)

        #Undo feature / redo feature
        undo_button = QAction("Undo", self)
        undo_button.triggered.connect(self.undo_button)
        self.addAction(undo_button)

        redo_button = QAction("Redo", self)
        redo_button.triggered.connect(self.redo_button)
        self.addAction(redo_button)

        quick_copy = QAction("Quick Copy Up", self)
        quick_copy.triggered.connect(lambda checked=False: self.quick_copy(True))
        self.addAction(quick_copy)

        quick_copy_down = QAction("Quick Copy Down", self)
        quick_copy_down.triggered.connect(lambda checked=False: self.quick_copy(False))
        self.addAction(quick_copy_down)

    def change_colour(self):
        """Allows us to change the colour of the pen"""
        dialog = QColorDialog()
        on_clicked_ok = dialog.exec()
        if on_clicked_ok:
            colour = dialog.currentColor()
            colour.setAlpha(self.canvas_label.max_alpha)
            self.canvas_label.pen.setColor(colour)
            self.left_label.last_colour = dialog.currentColor()
        self.colour.emit(dialog.currentColor())

    def undo_button(self):
        """Calls the undo method"""
        self.canvas_label.undo_draw()

    def redo_button(self):
        """Calls the redo fucntion"""
        self.canvas_label.redo_draw()

    def quick_copy(self, up_or_down:bool):
        """Copys the next slide up"""
        self.canvas_label.quick_copy(up_or_down)