from PySide6.QtWidgets import QDialog, QGridLayout, QLabel, QSpinBox, QPushButton
from PySide6.QtCore import Signal

class multiPopUp(QDialog):
    """This class facilitates the multi layer contour"""
    contour_number = Signal(int,int)
    max_range_signal = Signal(int)
    min_range_signal = Signal(int)
    
    """This class contains the allows the user to copy there roi to another slice"""
    def __init__(self, num_of_slices = None, current_slice = None, opasity = None, pixel_range_high = None, pixel_range_low = None):
        QDialog.__init__(self)
        self.setWindowTitle("Multi Layer Contour")
        slice_num = num_of_slices
        self.cs = current_slice
        self.opasity = opasity
        layout = QGridLayout()
        self.current_slice_label = QLabel(f"Current Slice : {self.cs}")
        self.upper_bounds_label = QLabel("Upper Bounds : ")
        self.upper_bounds = QSpinBox()
        self.upper_bounds.setRange(1,slice_num)
        self.upper_bounds.setValue(self.cs)
        self.lower_bounds_label = QLabel("Lower Bounds : ")
        self.lower_bounds = QSpinBox()
        self.lower_bounds.setRange(1,slice_num)
        self.lower_bounds.setValue(self.cs)

        opasity_label = QLabel("Opasity")
        self.opasity_spinbox = QSpinBox()
        self.opasity_spinbox.setRange(1,255)
        self.opasity_spinbox.setValue(opasity)

        pixel_min_range = QLabel("Pixel Range Min :")
        self.pixel_range_min = QSpinBox()
        self.pixel_range_min.setRange(0,6000)
        self.pixel_range_min.valueChanged.connect(self.update_pixel_min)
        self.pixel_range_min.setValue(pixel_range_low)

        #Upper bounds of the pixel range
        pixel_max_range = QLabel("Pixel Range Max :")
        self.pixel_range_max = QSpinBox()
        self.pixel_range_max.setRange(0,6000)
        self.pixel_range_max.valueChanged.connect(self.update_pixel_max)
        self.pixel_range_max.setValue(pixel_range_high)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.close)

        confirm_button = QPushButton("Confirm")
        confirm_button.clicked.connect(self.confirm_button)
         
        layout.addWidget(self.current_slice_label, 0,0)
        layout.addWidget(self.upper_bounds_label, 1,0)
        layout.addWidget(self.upper_bounds, 1,1)
        layout.addWidget(self.lower_bounds_label, 2,0)
        layout.addWidget(self.lower_bounds, 2,1)
        layout.addWidget(pixel_min_range,3,0)
        layout.addWidget(self.pixel_range_min,3,1)
        layout.addWidget(pixel_max_range,4,0)
        layout.addWidget(self.pixel_range_max,4,1)
        layout.addWidget(opasity_label, 5,0)
        layout.addWidget(self.opasity_spinbox, 5,1)
        layout.addWidget(cancel_button,6,0)
        layout.addWidget(confirm_button, 6,1)
        self.setLayout(layout)

    def confirm_button(self):
        """Emits the slice numbers that are to be drawn on"""
        self.contour_number.emit(self.upper_bounds.value(),self.lower_bounds.value())
        self.close()
        
    def update_pixel_min(self, value):
        """Updates the lower bounds of the pixel range for ROI
        Parm: int : value
        Output: canvas.change_min_value
        """
        self.min_range_signal.emit(value)

    def update_pixel_max(self, value):
        """Updates the upper bounds of the pixel range for ROI
          Parm: int : value
          Output: canvas.set_max_pixel_value
          """
        self.max_range_signal.emit(value)
