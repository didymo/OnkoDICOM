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

        #sets darwing variables
        self.is_drawing = False
        self.rt_value = False

        colourAction = QAction(self)
        colourAction.setIcon(QIcon("res/images/DrawRoi-icons/icons8-color-swatch-48.png"))
        colourAction.triggered.connect(self.change_colour)
        self.addAction(colourAction)

        #Undo feature / redo feature
        undo_button = QAction(self)
        undo_button.setIcon(QIcon("res/images/DrawRoi-icons/undo-alt.png"))
        undo_button.triggered.connect(self.undo_button)
        self.addAction(undo_button)

        redo_button = QAction(self)
        redo_button.setIcon(QIcon("res/images/DrawRoi-icons/redo-alt.png"))
        redo_button.triggered.connect(self.redo_button)
        self.addAction(redo_button)

        quick_copy = QAction("Quick Copy Up", self)
        quick_copy.triggered.connect(lambda checked=False: self.quick_copy(True))
        self.addAction(quick_copy)

        quick_copy_down = QAction("Quick Copy Down", self)
        quick_copy_down.triggered.connect(lambda checked=False: self.quick_copy(False))
        self.addAction(quick_copy_down)

        self.addSeparator()
        pen_size_label  = QLabel("Brush Size :")
        self.addWidget(pen_size_label)
        pen_size_spinbox = QSpinBox()
        pen_size_spinbox.setFocusPolicy(Qt.ClickFocus)
        pen_size_spinbox.editingFinished.connect(lambda: self.setFocus(Qt.OtherFocusReason))
        pen_size_spinbox.setRange(1,100)
        pen_size_spinbox.setValue(12)
        pen_size_spinbox.valueChanged.connect(self.update_pen_size)
        self.addWidget(pen_size_spinbox)
        self.addSeparator()

        #Min Pixel range (lower Bounds)
        pixel_min_range_label = QLabel("Pixel Range Min :")
        self.addWidget(pixel_min_range_label)
        pixel_range_min = QSpinBox()
        pixel_range_min.setFocusPolicy(Qt.ClickFocus)
        pixel_range_min.editingFinished.connect(lambda: self.setFocus(Qt.OtherFocusReason))
        pixel_range_min.setRange(0,6000)
        pixel_range_min.valueChanged.connect(self.update_pixel_min)
        pixel_range_min.setValue(0)
        self.addWidget(pixel_range_min)
        self.addSeparator()

        #Upper bounds of the pixel range
        pixel_range_max_lanbel = QLabel("Pixel Range Max :")
        self.addWidget(pixel_range_max_lanbel)
        pixel_range_max = QSpinBox()
        pixel_range_max.setFocusPolicy(Qt.ClickFocus)
        pixel_range_max.editingFinished.connect(lambda: self.setFocus(Qt.OtherFocusReason))
        pixel_range_max.setRange(0,6000)
        pixel_range_max.valueChanged.connect(self.update_pixel_max)
        pixel_range_max.setValue(6000)
        self.addWidget(pixel_range_max)
        self.addSeparator()

        erase_dags_num_label = QLabel("Erase Dags :")
        self.addWidget(erase_dags_num_label)
        erase_dags_num = QSpinBox()
        erase_dags_num.setFocusPolicy(Qt.ClickFocus)
        erase_dags_num.editingFinished.connect(lambda: self.setFocus(Qt.OtherFocusReason))
        erase_dags_num.setRange(0,262144)
        erase_dags_num.valueChanged.connect(self.update_erase_dags)
        erase_dags_num.setValue(20)
        self.addWidget(erase_dags_num)
        self.addSeparator()
        
        #Transparency Widget
        transparency_slider_label = QLabel("Opacity :")
        self.addWidget(transparency_slider_label)
        transparency_slider = QSpinBox()
        transparency_slider.setFocusPolicy(Qt.ClickFocus)
        transparency_slider.editingFinished.connect(lambda: self.setFocus(Qt.OtherFocusReason))
        transparency_slider.setRange(1,255)
        transparency_slider.valueChanged.connect(self.update_transparency)
        transparency_slider.setValue(126)
        self.addWidget(transparency_slider)

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