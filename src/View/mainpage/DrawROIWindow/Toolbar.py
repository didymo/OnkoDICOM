from PySide6.QtWidgets import QToolBar, QColorDialog, QLabel, QSpinBox
from PySide6.QtGui import QAction, QColor, QFontDatabase, QIcon
from PySide6.QtCore import Qt,Signal



class CutsomToolbar(QToolBar):
    """Class to hold the draw ROI features"""
    colour = Signal(QColor)
    opasity_value = Signal(int)
    update_cursor_size = Signal()

    def __init__(self, parent=None, canvas_label = None, left_label = None):
        super().__init__("Toolbar", parent)
        self.parent = parent
        self.setFont(QFontDatabase.systemFont(QFontDatabase.GeneralFont))
        #Sets communication between classes
        self.canvas_label = canvas_label
        self.left_label = left_label
        self.opasity_spinBox = None

        #sets darwing variables
        self.is_drawing = False
        self.rt_value = False
        colourAction = QAction(self)
        colourAction.setIcon(QIcon("res/images/DrawRoi-icons/icons8-color-swatch-48.png"))
        colourAction.setToolTip("Change Colour")
        colourAction.triggered.connect(self.change_colour)
        self.addAction(colourAction)

        #Undo feature / redo feature
        undo_button = QAction(self)
        undo_button.setIcon(QIcon("res/images/DrawRoi-icons/undo-alt.png"))
        undo_button.setToolTip("Undo")
        undo_button.triggered.connect(self.undo_button)
        self.addAction(undo_button)

        redo_button = QAction(self)
        redo_button.setIcon(QIcon("res/images/DrawRoi-icons/redo-alt.png"))
        redo_button.setToolTip("Redo")
        redo_button.triggered.connect(self.redo_button)
        self.addAction(redo_button)

        quick_copy = QAction(self)
        quick_copy.setIcon(QIcon("res/images/DrawRoi-icons/Quick-copy-up.png"))
        quick_copy.setToolTip("Quick Copy Up")
        quick_copy.triggered.connect(lambda checked=False: self.quick_copy(True))
        self.addAction(quick_copy)

        quick_copy_down = QAction(self)
        quick_copy_down.setToolTip("Quick Copy Down")
        quick_copy_down.setIcon(QIcon("res/images/DrawRoi-icons/Quick-copy-down.png"))
        quick_copy_down.triggered.connect(lambda checked=False: self.quick_copy(False))
        self.addAction(quick_copy_down)
        self.addSeparator()
        spin_defs = [
            ("Brush Size",      1,   100,  12,   self.update_pen_size),
            ("Pixel Range Min",  0,  6000,   0,   self.update_pixel_min),
            ("Pixel Range Max",  0,  6000,6000,  self.update_pixel_max),
            ("Erase Dags",       0,262144,  20,  self.update_erase_dags),
            ("Opacity",          1,   255, 126,  self.update_transparency),
        ]

        for text, mn, mx, val, slot in spin_defs:
            self._add_labeled_spinbox(text, mn, mx, val, slot)
        
    def _add_labeled_spinbox(self, label_text, minimum, maximum, default, slot):
        self.addSeparator()
        lbl = QLabel(label_text + " :")
        self.addWidget(lbl)
        sb = QSpinBox()
        sb.setFocusPolicy(Qt.ClickFocus)
        sb.editingFinished.connect(lambda _=None: self.setFocus(Qt.OtherFocusReason))
        sb.setRange(minimum, maximum)
        sb.setValue(default)
        sb.valueChanged.connect(slot)
        self.addWidget(sb)

    def change_colour(self):
        """Allows us to change the colour of the pen"""
        dialog = QColorDialog()
        if on_clicked_ok := dialog.exec():
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
        """
        Copys the next slide up
        Parm : Bool
        """
        self.canvas_label.quick_copy(up_or_down)
    
    def update_pen_size(self, value):
        """
        Changes the width of the drawing
        Parm int : value
        Return : None
        """
        self.canvas_label.pen.setWidth(value)
        self.update_cursor_size.emit()

    def update_transparency(self,value):
        """
        Updates the value of the transparency
        Parm int : value
        Return : None
        """
        colour = self.canvas_label.pen.color()
        colour.setAlpha(value)
        self.canvas_label.pen.setColor(colour)
        self.canvas_label.max_alpha = value
        self.opasity_value.emit(value)


    def update_pixel_min(self, value):
        """
        Updates the lower bounds of the pixel range for ROI
        Parm int : value
        Return : None
        """
        self.canvas_label.min_range = value
        self.canvas_label.lock_pixel()

    def update_pixel_max(self, value):
        """
        Updates the upper bounds of the pixel range for ROI
        Parm int : value
        Return : None
        """
        self.canvas_label.max_range = value
        self.canvas_label.lock_pixel()

    def update_erase_dags(self, value):
        """
        Updates the erase dags connected pixel number 
        par :: int
        """
        self.canvas_label.erase_das_num = value