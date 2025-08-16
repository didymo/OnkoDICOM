from PySide6 import QtWidgets
from PySide6.QtCore import Qt

class TranslateRotateMenu(QtWidgets.QWidget):
    """
    A menu for adjusting translation, rotation, and opacity of the overlay image.
    Displays sliders for 'LR', 'PA', and 'IS' for both translation and rotation,
    and an opacity slider. Designed for a portrait layout.
    """

    def __init__(self, _back_callback=None):
        super().__init__()
        layout = QtWidgets.QVBoxLayout()

        # Translate section
        layout.addSpacing(4)
        layout.addWidget(QtWidgets.QLabel("Translate:"), alignment=Qt.AlignLeft)
        self.translate_sliders = []
        for axis in ['LR', 'PA', 'IS']:
            hbox = QtWidgets.QHBoxLayout()
            label = QtWidgets.QLabel(axis)
            label.setFixedWidth(30)
            slider = QtWidgets.QSlider(Qt.Horizontal)
            slider.setMinimum(-100)
            slider.setMaximum(100)
            slider.setValue(0)
            hbox.addWidget(label)
            hbox.addWidget(slider)
            layout.addLayout(hbox)
            self.translate_sliders.append(slider)

        # Rotate section
        layout.addSpacing(8)
        layout.addWidget(QtWidgets.QLabel("Rotate:"), alignment=Qt.AlignLeft)
        self.rotate_sliders = []
        for axis in ['LR', 'PA', 'IS']:
            hbox = QtWidgets.QHBoxLayout()
            label = QtWidgets.QLabel(axis)
            label.setFixedWidth(30)
            slider = QtWidgets.QSlider(Qt.Horizontal)
            slider.setMinimum(-180)
            slider.setMaximum(180)
            slider.setValue(0)
            hbox.addWidget(label)
            hbox.addWidget(slider)
            layout.addLayout(hbox)
            self.rotate_sliders.append(slider)

        # Opacity section
        layout.addSpacing(8)
        layout.addWidget(QtWidgets.QLabel("Overlay Opacity:"), alignment=Qt.AlignLeft)
        self.opacity_slider = QtWidgets.QSlider(Qt.Horizontal)
        self.opacity_slider.setMinimum(0)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setValue(100)
        layout.addWidget(self.opacity_slider)

        layout.addStretch(1)
        self.setLayout(layout)