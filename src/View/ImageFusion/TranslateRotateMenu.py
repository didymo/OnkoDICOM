from PySide6 import QtWidgets
from PySide6.QtCore import Qt

class TranslateRotateMenu(QtWidgets.QWidget):
    """
    A menu for adjusting translation and rotation with sliders for each axis.
    Displays sliders for 'LR', 'PA', and 'IS' for both translation and rotation.
    """

    def __init__(self, back_callback):
        super().__init__()
        layout = QtWidgets.QVBoxLayout()

        # Translate section
        translate_label = QtWidgets.QLabel("Translate")
        layout.addWidget(translate_label)
        self.translate_sliders = []
        for axis in ['LR', 'PA', 'IS']:
            hbox = QtWidgets.QHBoxLayout()
            label = QtWidgets.QLabel(axis)
            slider = QtWidgets.QSlider(Qt.Horizontal)
            slider.setMinimum(-100)
            slider.setMaximum(100)
            slider.setValue(0)
            hbox.addWidget(label)
            hbox.addWidget(slider)
            layout.addLayout(hbox)
            self.translate_sliders.append(slider)

        # Rotate section
        rotate_label = QtWidgets.QLabel("Rotate")
        layout.addWidget(rotate_label)
        self.rotate_sliders = []
        for axis in ['LR', 'PA', 'IS']:
            hbox = QtWidgets.QHBoxLayout()
            label = QtWidgets.QLabel(axis)
            slider = QtWidgets.QSlider(Qt.Horizontal)
            slider.setMinimum(-180)
            slider.setMaximum(180)
            slider.setValue(0)
            hbox.addWidget(label)
            hbox.addWidget(slider)
            layout.addLayout(hbox)
            self.rotate_sliders.append(slider)

        # Back button
        self.back_button = QtWidgets.QPushButton("Back")
        self.back_button.clicked.connect(back_callback)
        layout.addWidget(self.back_button)

        self.setLayout(layout)