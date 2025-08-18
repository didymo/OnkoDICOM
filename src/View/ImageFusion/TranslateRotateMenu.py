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
        self.offset_changed_callback = None

        layout = QtWidgets.QVBoxLayout()

        # Translate section
        layout.addSpacing(4)
        layout.addWidget(QtWidgets.QLabel("Translate:"), alignment=Qt.AlignLeft)
        self.translate_sliders = []
        self.translate_labels = []
        for i, axis in enumerate(['x', 'y']):
            hbox = QtWidgets.QHBoxLayout()
            label = QtWidgets.QLabel(axis)
            label.setFixedWidth(30)
            slider = QtWidgets.QSlider(Qt.Horizontal)
            slider.setMinimum(-100)
            slider.setMaximum(100)
            slider.setValue(0)
            slider.valueChanged.connect(self._make_offset_change_handler(i))
            value_label = QtWidgets.QLabel("0 px")
            value_label.setFixedWidth(50)

            hbox.addWidget(label)
            hbox.addWidget(slider)
            hbox.addWidget(value_label)
            layout.addLayout(hbox)
            self.translate_sliders.append(slider)
            self.translate_labels.append(value_label)


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

    def on_offset_change(self, axis_index, value):
        """
            When a slider value changes, this method collects the current x and y offsets and
            calls the registered offset_changed_callback with the new values.

            Args:
                axis_index: The index of the axis that was changed (0 for x, 1 for y).
                value: The new value of the changed slider.
        """
        self.translate_labels[axis_index].setText(f"{value} px")
        if self.offset_changed_callback:
            x = self.translate_sliders[0].value()
            y = self.translate_sliders[1].value()
            self.offset_changed_callback((x, y))

    def set_offset_changed_callback(self, callback):
        """
                This method allows external code to register a callback that will be
                invoked with the new (x, y) offset when a slider is adjusted.

                Args:
                    callback: A function that takes a tuple or list representing
                    the new (x, y) offset.
                """
        self.offset_changed_callback = callback

    def set_offsets(self, offsets):
        """
            This method updates the slider positions for the x and y axes without
            emitting value changed signals.

            Args:
                offsets: A tuple or list containing the new x and y offset values.
        """

        for i in range(2):
            self.translate_sliders[i].blockSignals(True)
            self.translate_sliders[i].setValue(offsets[i])
            self.translate_labels[i].setText(f"{offsets[i]} px")
            self.translate_sliders[i].blockSignals(False)

    def reset_trans(self):
        """
                This method sets each translation slider to zero and updates the
                corresponding label to "0 px".
                """
        for slider, label in zip(self.sliders, self.labels):
            slider.blockSignals(True)
            slider.setValue(0)
            label.setText("0 px")
            slider.blockSignals(False)

    def _make_offset_change_handler(self, idx):
        return lambda value: self.on_offset_change(idx, value)
