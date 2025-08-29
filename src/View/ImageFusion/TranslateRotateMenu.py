from PySide6 import QtWidgets
from PySide6.QtCore import Qt
from src.View.ImageFusion.TransformMatrixDialog import TransformMatrixDialog


def get_color_pair_from_text(text):
    """
    Utility function to map color pair combo text to (fixed_color, moving_color, coloring_enabled).
    """
    if text == "No Colors (Grayscale)":
        return "Grayscale", "Grayscale", False
    elif text == "Purple + Green":
        return "Purple", "Green", True
    elif text == "Blue + Yellow":
        return "Blue", "Yellow", True
    elif text == "Red + Cyan":
        return "Red", "Cyan", True
    else:
        return "Purple", "Green", True

class TranslateRotateMenu(QtWidgets.QWidget):
    """
    A menu for adjusting translation, rotation, and opacity of the overlay image.
    Displays sliders for 'LR', 'PA', and 'IS' for both translation and rotation,
    and an opacity slider. Designed for a portrait layout.
    Also includes color selection and coloring enable/disable.
    """

    def __init__(self, _back_callback=None):
        super().__init__()
        self.offset_changed_callback = None

        layout = QtWidgets.QVBoxLayout()

        # Colour selection and coloring enable
        color_pair_options = [
            "No Colors (Grayscale)",
            "Purple + Green",
            "Blue + Yellow",
            "Red + Cyan"
        ]
        color_pair_hbox = QtWidgets.QHBoxLayout()
        color_pair_hbox.addWidget(QtWidgets.QLabel("Overlay Colors:"))
        self.color_pair_combo = QtWidgets.QComboBox()
        self.color_pair_combo.addItems(color_pair_options)
        self.color_pair_combo.setCurrentText("Purple + Green")
        color_pair_hbox.addWidget(self.color_pair_combo)
        layout.addLayout(color_pair_hbox)

        # Store current color/enable state
        self.fixed_color, self.moving_color, self.coloring_enabled = get_color_pair_from_text("Purple + Green")

        # Connect signal for color pair selection
        self.color_pair_combo.currentTextChanged.connect(self._on_color_pair_changed)

        # Translate section
        layout.addSpacing(4)
        layout.addWidget(QtWidgets.QLabel("Translate:"), alignment=Qt.AlignLeft)
        self.translate_sliders = []
        self.translate_labels = []
        for i, axis in enumerate(['LR', 'PA', 'IS']):
            hbox = QtWidgets.QHBoxLayout()
            label = QtWidgets.QLabel(axis)
            label.setFixedWidth(30)
            slider = QtWidgets.QSlider(Qt.Horizontal)
            slider.setMinimum(-500)
            slider.setMaximum(500)
            slider.setValue(0)
            slider.setSingleStep(1)
            slider.setPageStep(1)
            slider.setTickInterval(0)
            slider.setTracking(True)
            slider.valueChanged.connect(self._make_offset_change_handler(i))
            value_label = QtWidgets.QLabel("0 mm")
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
        self.rotate_labels = []
        self.rotation_changed_callback = None
        for i, axis in enumerate(['LR', 'PA', 'IS']):
            hbox = QtWidgets.QHBoxLayout()
            label = QtWidgets.QLabel(axis)
            label.setFixedWidth(30)
            slider = QtWidgets.QSlider(Qt.Horizontal)
            slider.setMinimum(-180)
            slider.setMaximum(180)
            slider.setValue(0)
            slider.valueChanged.connect(self._make_rotation_change_handler(i))
            value_label = QtWidgets.QLabel("0°")
            value_label.setFixedWidth(50)
            hbox.addWidget(label)
            hbox.addWidget(slider)
            hbox.addWidget(value_label)
            layout.addLayout(hbox)
            self.rotate_sliders.append(slider)
            self.rotate_labels.append(value_label)

        # Opacity section
        layout.addSpacing(8)
        layout.addWidget(QtWidgets.QLabel("Opacity:"), alignment=Qt.AlignLeft)
        self.opacity_slider = QtWidgets.QSlider(Qt.Horizontal)
        self.opacity_slider.setMinimum(0)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setValue(50)
        layout.addWidget(self.opacity_slider)

        # Reset Transform Button
        reset_btn = QtWidgets.QPushButton("Reset Transform")
        reset_btn.setToolTip("Reset all translation and rotation to zero")
        reset_btn.clicked.connect(self.reset_transform)
        layout.addWidget(reset_btn)

        # Show Transform Matrix Button
        show_matrix_btn = QtWidgets.QPushButton("Show Transform Matrix")
        show_matrix_btn.setToolTip("Show the current 4x4 transformation matrix")
        show_matrix_btn.clicked.connect(self.show_transform_matrix)
        layout.addWidget(show_matrix_btn)

        layout.addStretch(1)
        self.setLayout(layout)

        # Matrix dialog instance (created on demand)
        self._matrix_dialog = None
        self._get_vtk_engine_callback = None

        # Store current colour/enable state
        self.fixed_color = "Purple"
        self.moving_color = "Green"
        self.coloring_enabled = True

    def on_offset_change(self, axis_index, value):
        """
            When a slider value changes, this method collects the current x, y, z offsets and
            calls the registered offset_changed_callback with the new values.

            Args:
                axis_index: The index of the axis that was changed (0 for x, 1 for y, 2 for z).
                value: The new value of the changed slider.
        """
        self.translate_labels[axis_index].setText(f"{value} mm")
        if self.offset_changed_callback:
            x = self.translate_sliders[0].value()
            y = self.translate_sliders[1].value()
            z = self.translate_sliders[2].value()
            self.offset_changed_callback((x, y, z))
        # Update matrix dialog if open
        if self._matrix_dialog and self._get_vtk_engine_callback:
            engine = self._get_vtk_engine_callback()
            if engine is not None and hasattr(engine, "transform"):
                self._matrix_dialog.set_matrix(engine.transform)

    def set_offset_changed_callback(self, callback):
        """
                This method allows external code to register a callback that will be
                invoked with the new (x, y, z) offset when a slider is adjusted.

                Args:
                    callback: A function that takes a tuple or list representing
                    the new (x, y, z) offset.
                """
        self.offset_changed_callback = callback

    def set_rotation_changed_callback(self, callback):
        """
        Allows external code to register a callback for rotation changes.
        Args:
            callback: A function that takes a tuple (rx, ry, rz) in degrees.
        """
        self.rotation_changed_callback = callback

    def set_color_pair_changed_callback(self, callback):
        """
        Allows external code to register a callback for color pair changes.
        Args:
            callback: A function that takes (fixed_color, moving_color, coloring_enabled).
        """
        self.color_pair_changed_callback = callback

    def _make_rotation_change_handler(self, idx):
        return lambda value: self.on_rotation_change(idx, value)

    def on_rotation_change(self, axis_index, value):
        """
        Called when a rotation slider value changes.
        """
        self.rotate_labels[axis_index].setText(f"{value}°")
        if self.rotation_changed_callback:
            rx = self.rotate_sliders[0].value()
            ry = self.rotate_sliders[1].value()
            rz = self.rotate_sliders[2].value()
            self.rotation_changed_callback((rx, ry, rz))
        # Update matrix dialog if open
        if self._matrix_dialog and self._get_vtk_engine_callback:
            engine = self._get_vtk_engine_callback()
            if engine is not None and hasattr(engine, "transform"):
                self._matrix_dialog.set_matrix(engine.transform)

    def set_offsets(self, offsets):
        """
            This method updates the slider positions for the x, y, z axes without
            emitting value changed signals.

            Args:
                offsets: A tuple or list containing the new x, y, z offset values.
        """

        for i in range(3):
            self.translate_sliders[i].blockSignals(True)
            self.translate_sliders[i].setValue(offsets[i])
            self.translate_labels[i].setText(f"{offsets[i]} mm")
            self.translate_sliders[i].blockSignals(False)

    def reset_trans(self):
        """
        This method sets each translation slider to zero and updates the
        corresponding label to "0 mm".
        """
        for slider, label in zip(self.translate_sliders, self.translate_labels):
            slider.blockSignals(True)
            slider.setValue(0)
            label.setText("0 mm")
            slider.blockSignals(False)

    def reset_rot(self):
        """
        This method sets each rotation slider to zero.
        """
        for slider, label in zip(self.rotate_sliders, self.rotate_labels):
            slider.blockSignals(True)
            slider.setValue(0)
            label.setText("0°")
            slider.blockSignals(False)

    def reset_transform(self):
        """
        Resets both translation and rotation sliders to zero and calls callbacks.
        """
        self.reset_trans()
        self.reset_rot()
        # Call callbacks to update the views/engine
        if self.offset_changed_callback:
            x = self.translate_sliders[0].value()
            y = self.translate_sliders[1].value()
            z = self.translate_sliders[2].value()
            self.offset_changed_callback((x, y, z))
        if self.rotation_changed_callback:
            rx = self.rotate_sliders[0].value()
            ry = self.rotate_sliders[1].value()
            rz = self.rotate_sliders[2].value()
            self.rotation_changed_callback((rx, ry, rz))
        # Update matrix dialog if open
        if self._matrix_dialog and self._get_vtk_engine_callback:
            engine = self._get_vtk_engine_callback()
            if engine is not None and hasattr(engine, "transform"):
                self._matrix_dialog.set_matrix(engine.transform)

    def _make_offset_change_handler(self, idx):
        return lambda value: self.on_offset_change(idx, value)

    def _on_color_pair_changed(self, text):
        """
        Handle changes to the color pair combo box.
        Updates the internal color state and emits a signal/callback if set.
        """
        self.fixed_color, self.moving_color, self.coloring_enabled = get_color_pair_from_text(text)

        # If a callback is set, notify external listeners (e.g., the main view/controller)
        if hasattr(self, "color_pair_changed_callback") and callable(self.color_pair_changed_callback):
            self.color_pair_changed_callback(self.fixed_color, self.moving_color, self.coloring_enabled)

    def set_get_vtk_engine_callback(self, callback):
        """
        Set a callback that returns the current VTKEngine instance.
        """
        self._get_vtk_engine_callback = callback

    def show_transform_matrix(self):
        """
        Show the transformation matrix dialog for the current VTKEngine.
        """
        if self._matrix_dialog is None:
            self._matrix_dialog = TransformMatrixDialog(self)
        # Get the VTKEngine instance from the callback
        engine = self._get_vtk_engine_callback() if self._get_vtk_engine_callback else None
        if engine is not None and hasattr(engine, "transform"):
            self._matrix_dialog.set_matrix(engine.transform)
        self._matrix_dialog.show()
        self._matrix_dialog.raise_()
        self._matrix_dialog.activateWindow()
