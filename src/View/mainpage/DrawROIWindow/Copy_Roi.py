from PySide6.QtWidgets import QWidget, QGridLayout, QLabel, QSpinBox, QPushButton
from PySide6.QtCore import Signal


class CopyROI(QWidget):
    copy_number_high = Signal(int)
    copy_number_low = Signal(int)
    """This class contains the allows the user to copy there roi to another slice"""
    def __init__(self, num_of_slices:int, current_slice:int):
        super().__init__()
        self.setWindowTitle("Copy ROI")
        self.resize(300,300)
        slice_num = num_of_slices
        self.cs = current_slice
        layout = QGridLayout()
        self.current_slice_label = QLabel("Current Slice :", current_slice)
        self.upper_bounds_label = QLabel("upeper Bounds : ")
        self.upper_bounds = QSpinBox()
        self.upper_bounds.setRange(1,slice_num)
        self.upper_bounds.setValue(self.cs)

        self.lower_bounds_label = QLabel("Lower Bounds : ")
        self.lower_bounds = QSpinBox()
        self.lower_bounds.setRange(1,current_slice)
        self.lower_bounds.setValue(self.cs)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.close)

        confirm_button = QPushButton("Confirm")
        confirm_button.clicked.connect(self.confirm_button)
         
        layout.addWidget(self.current_slice_label, 0,0)
        layout.addWidget(self.upper_bounds_label, 1,0)
        layout.addWidget(self.upper_bounds, 1,1)
        layout.addWidget(self.lower_bounds_label, 2,0)
        layout.addWidget(self.lower_bounds, 2,1)
        layout.addWidget(cancel_button,3,0)
        layout.addWidget(confirm_button, 3,1)
        self.setLayout(layout)

    def confirm_button(self):
        """If the numbers have changed the ROIs will be coppyed onto the slides"""
        if self.upper_bounds.value() != self.cs:
            self.copy_number_high.emit(self.upper_bounds.value())
        if self.lower_bounds.value() != self.cs:
            self.copy_number_low.emit(self.lower_bounds.value())
        self.close()





        