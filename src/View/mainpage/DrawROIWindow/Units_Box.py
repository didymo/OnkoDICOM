from PySide6 import QtWidgets
from PySide6.QtWidgets import QGroupBox, QGridLayout, QLabel, QSpinBox, QSlider
from PySide6.QtCore import Qt,Signal

class UnitsBox(QtWidgets.QLabel):
    """The class contains all of the unit boxes"""
    opasity_value = Signal(int)
    def __init__(self, parent = None, pen = None, canvas_label = None,):
        super().__init__(parent)
        self.canvas_label = canvas_label
        self.parent = parent
        self.pen = pen
        self.text_entry_setup()
        print("3")


    def text_entry_setup(self):
        """Sets up the text entry and allows for the pen to change size based off the input"""
        #Adding the layout
        self._grid_group_box = QGroupBox()
        layout = QGridLayout()

        #Creating all of the labels and boxes

        #Brush size
        pen_size  = QLabel("Brush Size :")
        self.pen_size_spinbox = QSpinBox()
        self.pen_size_spinbox.setFocusPolicy(Qt.ClickFocus)
        self.pen_size_spinbox.editingFinished.connect(lambda: self.setFocus(Qt.OtherFocusReason))
        self.pen_size_spinbox.setRange(1,100)
        self.pen_size_spinbox.setValue(12)
        self.pen_size_spinbox.valueChanged.connect(self.update_pen_size)

        #Min Pixel range (lower Bounds)
        pixel_min_range = QLabel("Pixel Range Min :")
        self.pixel_range_min = QSpinBox()
        self.pixel_range_min.setFocusPolicy(Qt.ClickFocus)
        self.pixel_range_min.editingFinished.connect(lambda: self.setFocus(Qt.OtherFocusReason))
        self.pixel_range_min.setRange(0,6000)
        self.pixel_range_min.valueChanged.connect(self.update_pixel_min)
        self.pixel_range_min.setValue(0)

        #Upper bounds of the pixel range
        pixel_max_range = QLabel("Pixel Range Max :")
        self.pixel_range_max = QSpinBox()
        self.pixel_range_max.setFocusPolicy(Qt.ClickFocus)
        self.pixel_range_max.editingFinished.connect(lambda: self.setFocus(Qt.OtherFocusReason))
        self.pixel_range_max.setRange(0,6000)
        self.pixel_range_max.valueChanged.connect(self.update_pixel_max)
        self.pixel_range_max.setValue(6000)

        #Transparency Widget
        transparency = QLabel("Opacity :")
        self.transparency_slider = QSlider(Qt.Horizontal)
        self.transparency_slider.setRange(1,100)
        self.transparency_slider.valueChanged.connect(self.update_transparency)
        self.transparency_slider.setValue(50)
        
        #Ading the them to the layout
        layout.addWidget(pen_size,0,0)
        layout.addWidget(self.pen_size_spinbox, 0,1)
        layout.addWidget(transparency, 1,0)
        layout.addWidget(self.transparency_slider, 1,1)
        layout.addWidget(pixel_min_range, 2,0)
        layout.addWidget(self.pixel_range_min, 2,1)
        layout.addWidget(pixel_max_range, 3,0)
        layout.addWidget(self.pixel_range_max, 3,1)

        #setting the layout and adding
        self._grid_group_box.setLayout(layout)
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(self._grid_group_box)
        self.setLayout(main_layout)

    def update_pen_size(self, value):
        """Changes the width of the drawing"""
        self.canvas_label.pen.setWidth(value)

    def update_transparency(self,value):
        """Updates the value of the transparency"""
        colour = self.canvas_label.pen.color()
        transparency_value = int((255/100) * value)
        colour.setAlpha(transparency_value)
        self.canvas_label.pen.setColor(colour)
        self.canvas_label.max_alpha = transparency_value
        self.opasity_value.emit(transparency_value)



    def update_pixel_min(self, value):
        """Updates the lower bounds of the pixel range for ROI"""
        self.canvas_label.min_range = value
        self.canvas_label.lock_pixel()

    def update_pixel_max(self, value):
        """Updates the upper bounds of the pixel range for ROI"""
        self.canvas_label.max_range = value
        self.canvas_label.lock_pixel()