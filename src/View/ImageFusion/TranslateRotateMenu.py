import itertools
from PySide6 import QtWidgets, QtCore
from PySide6.QtWidgets import QFileDialog, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from src.View.ImageFusion.TransformMatrixDialog import TransformMatrixDialog
from src.Controller.PathHandler import resource_path


def get_color_pair_from_text(text):
    """
    Utility function to map color pair combo text to (fixed_color, moving_color, coloring_enabled).
    """
    match text:
        case "No Colors (Grayscale)":
            return "Grayscale", "Grayscale", False
        case "Purple + Green":
            return "Purple", "Green", True
        case "Blue + Yellow":
            return "Blue", "Yellow", True
        case "Red + Cyan":
            return "Red", "Cyan", True
        case _:
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
            slider.setSingleStep(1)  # 1mm per step
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

        # Mouse Mode Toolbar (Translate/Rotate)
        mouse_mode_hbox = QtWidgets.QHBoxLayout()
        mouse_mode_hbox.setSpacing(20)
        mouse_mode_hbox.setContentsMargins(0, 0, 0, 0)

        self.mouse_translate_btn = QtWidgets.QPushButton()
        self.mouse_rotate_btn = QtWidgets.QPushButton()
        self.mouse_translate_btn.setCheckable(True)
        self.mouse_rotate_btn.setCheckable(True)
        self.mouse_translate_btn.setToolTip("Enable mouse translation mode")
        self.mouse_rotate_btn.setToolTip("Enable mouse rotation mode")

        # Set icons for buttons
        translate_icon = QIcon(resource_path("res/images/btn-icons/translate_arrow_icon.png"))
        rotate_icon = QIcon(resource_path("res/images/btn-icons/rotate_arrow_icon.png"))
        self.mouse_translate_btn.setIcon(translate_icon)
        self.mouse_rotate_btn.setIcon(rotate_icon)
        self.mouse_translate_btn.setIconSize(QtCore.QSize(24, 24))
        self.mouse_rotate_btn.setIconSize(QtCore.QSize(24, 24))

        # Add stretch, buttons, stretch
        mouse_mode_hbox.addStretch(1)
        mouse_mode_hbox.addWidget(self.mouse_translate_btn)
        mouse_mode_hbox.addWidget(self.mouse_rotate_btn)
        mouse_mode_hbox.addStretch(1)

        # Insert the button row
        layout.insertLayout(1, mouse_mode_hbox)

        # Button group to ensure only one is checked at a time
        self.mouse_mode_group = QtWidgets.QButtonGroup(self)
        self.mouse_mode_group.setExclusive(True)
        self.mouse_mode_group.addButton(self.mouse_translate_btn)
        self.mouse_mode_group.addButton(self.mouse_rotate_btn)

        # Track last clicked button for "toggle off" 
        self._last_checked_button = None

        def on_mouse_mode_btn_clicked(btn):
            if self._last_checked_button == btn and btn.isChecked():
                # uncheck button if active
                self.mouse_mode_group.setExclusive(False)
                btn.setChecked(False)
                self.mouse_mode_group.setExclusive(True)
                self._last_checked_button = None
                self.mouse_mode = None
            else:
                # activate the clicked button
                self._last_checked_button = btn
                if btn == self.mouse_translate_btn:
                    self.mouse_mode = "translate"
                elif btn == self.mouse_rotate_btn:
                    self.mouse_mode = "rotate"

            # Call callback if set
            if self.mouse_mode_changed_callback:
                self.mouse_mode_changed_callback(self.mouse_mode)


        self.mouse_translate_btn.clicked.connect(lambda: on_mouse_mode_btn_clicked(self.mouse_translate_btn))
        self.mouse_rotate_btn.clicked.connect(lambda: on_mouse_mode_btn_clicked(self.mouse_rotate_btn))

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
            slider.setMinimum(-1800)  # -180.0 deg (in 0.1 deg steps)
            slider.setMaximum(1800)   # +180.0 deg (in 0.1 deg steps)
            slider.setValue(0)
            slider.setSingleStep(1)   # 0.1 deg per step
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

        # Add Save/Load buttons
        save_button = QtWidgets.QPushButton("Save Fusion State")
        load_button = QtWidgets.QPushButton("Load Fusion State")
        save_button.clicked.connect(self.save_fusion_state)
        load_button.clicked.connect(self.load_fusion_state)
        # Add to layout (assume self.layout() is a QVBoxLayout)
        layout.addWidget(save_button)
        layout.addWidget(load_button)

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

        # Mouse mode callback (to be set by parent)
        self.mouse_mode_changed_callback = None

    def set_mouse_mode_changed_callback(self, callback):
        """
        Allows external code to register a callback for mouse mode changes.
        Args:
            callback: A function that takes a string: "translate", "rotate", or None.
        """
        self.mouse_mode_changed_callback = callback

    def get_mouse_mode(self):
        """
        Returns the current mouse mode: "translate", "rotate", or None.
        """
        return self.mouse_mode

    def set_mouse_mode(self, mode):
        """
        Set the mouse mode programmatically.
        """
        if mode == "translate":
            self.mouse_translate_btn.setChecked(True)
            self.mouse_rotate_btn.setChecked(False)
        elif mode == "rotate":
            self.mouse_translate_btn.setChecked(False)
            self.mouse_rotate_btn.setChecked(True)
        else:
            self.mouse_translate_btn.setChecked(False)
            self.mouse_rotate_btn.setChecked(False)
        self.mouse_mode = mode
        if self.mouse_mode_changed_callback:
            self.mouse_mode_changed_callback(mode)

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
                self._matrix_dialog.set_matrix(engine.user_transform)

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
        # Show value in degrees (float, 1 decimal)
        self.rotate_labels[axis_index].setText(f"{value/10.0:.1f}°")
        if self.rotation_changed_callback:
            rx = self.rotate_sliders[0].value() / 10.0
            ry = self.rotate_sliders[1].value() / 10.0
            rz = self.rotate_sliders[2].value() / 10.0
            self.rotation_changed_callback((rx, ry, rz))
        # Update matrix dialog if open
        if self._matrix_dialog and self._get_vtk_engine_callback:
            engine = self._get_vtk_engine_callback()
            if engine is not None and hasattr(engine, "transform"):
                self._matrix_dialog.set_matrix(engine.user_transform)

    def set_offsets(self, offsets):
        """
            This method updates the slider positions for the x, y, z axes without
            emitting value changed signals.

            Args:
                offsets: A tuple or list containing the new x, y, z offset values.
        """

        for i in range(3):
            self.translate_sliders[i].blockSignals(True)
            self.translate_sliders[i].setValue(int(round(offsets[i])))
            self.translate_labels[i].setText(f"{int(round(offsets[i]))} mm")
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
                self._matrix_dialog.set_matrix(engine.user_transform)

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

    def save_fusion_state(self):
        import pydicom
        from pydicom.dataset import Dataset, FileDataset
        import datetime
        import numpy as np
        import os
        
        vtk_engine = self._get_vtk_engine_callback() if hasattr(self,
                                                                "_get_vtk_engine_callback") and self._get_vtk_engine_callback else None
        if vtk_engine is None:
            QMessageBox.warning(self, "Error", "No VTK engine found.")
            return

        # Gather the 4x4 transform matrix
        matrix = None
        if hasattr(vtk_engine, "transform"):
            m = vtk_engine.transform.GetMatrix()
            matrix = np.array([[m.GetElement(i, j) for j in range(4)] for i in range(4)], dtype=np.float32)
        else:
            QMessageBox.warning(self, "Error", "No transform matrix found.")
            return

        # Create a minimal DICOM dataset
        file_meta = pydicom.Dataset()
        file_meta.MediaStorageSOPClassUID = pydicom.uid.generate_uid()
        file_meta.MediaStorageSOPInstanceUID = pydicom.uid.generate_uid()
        file_meta.ImplementationClassUID = pydicom.uid.generate_uid()

        ds = FileDataset("transform.dcm", {}, file_meta=file_meta, preamble=b"\0" * 128)
        ds.is_little_endian = True
        ds.is_implicit_VR = True

        # Set required DICOM fields
        dt = datetime.datetime.now()
        ds.PatientName = "FUSION"
        ds.PatientID = "FUSION"
        ds.StudyInstanceUID = pydicom.uid.generate_uid()
        ds.SeriesInstanceUID = pydicom.uid.generate_uid()
        ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
        ds.SOPClassUID = file_meta.MediaStorageSOPClassUID
        ds.Modality = "OT"
        ds.StudyDate = dt.strftime('%Y%m%d')
        ds.StudyTime = dt.strftime('%H%M%S')

        # Store the matrix as a private tag (use (0x7777,0x0010) as example)
        # Flatten the matrix to a string for storage
        matrix_str = ",".join([f"{v:.8f}" for v in matrix.flatten()])
        ds.add_new((0x7777, 0x0010), 'LT', matrix_str)
        ds.add_new((0x7777, 0x0011), 'LO', "VTK Fusion Transform Matrix")

        # Save to transform.dcm in the current working directory
        filename, _ = QFileDialog.getSaveFileName(self, "Save Transform Matrix", "transform.dcm", "DICOM Files (*.dcm)")
        if filename:
            ds.save_as(filename)
            QMessageBox.information(self, "Saved", f"Transform matrix saved to {filename}")


    def load_fusion_state(self):
        import pydicom
        import numpy as np

        vtk_engine = self._get_vtk_engine_callback() if hasattr(self,
                                                                "_get_vtk_engine_callback") and self._get_vtk_engine_callback else None
        if vtk_engine is None:
            QMessageBox.warning(self, "Error", "No VTK engine found.")
            return

        filename, _ = QFileDialog.getOpenFileName(self, "Load Fusion State", "", "DICOM Files (*.dcm)")

        if filename:
            try:
                ds = pydicom.dcmread(filename)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not read DICOM file:\n{e}")
                return

            if (0x7777, 0x0010) in ds:
                self._extracted_from_load_fusion_state_15(ds, np, vtk_engine, filename)
            else:
                QMessageBox.warning(self, "Error",
                                    "No transform matrix found in DICOM file.\nPlease select a transform.dcm file created by the Save Fusion State function.")

    # TODO Rename this here and in `load_fusion_state`
    def _extracted_from_load_fusion_state_15(self, ds, np, vtk_engine, filename):
        import vtk
        matrix_str = ds[(0x7777, 0x0010)].value
        matrix_flat = [float(x) for x in matrix_str.split(",")]
        matrix = np.array(matrix_flat, dtype=np.float32).reshape((4, 4))
        m = vtk.vtkMatrix4x4()
        for i, j in itertools.product(range(4), range(4)):
            m.SetElement(i, j, matrix[i, j])
        if hasattr(vtk_engine, "transform"):
            vtk_engine.transform.SetMatrix(m)
            vtk_engine.reslice3d.SetResliceAxes(m)
            vtk_engine.reslice3d.Modified()

        translation = [m.GetElement(0, 3), m.GetElement(1, 3), m.GetElement(2, 3)]
        rotation = [0, 0, 0]

        self.set_offsets(translation)
        for i in range(3):
            self.rotate_sliders[i].blockSignals(True)
            self.rotate_sliders[i].setValue(int(round(rotation[i] * 10)))
            self.rotate_labels[i].setText(f"{rotation[i]:.1f}°")
            self.rotate_sliders[i].blockSignals(False)
        if self.offset_changed_callback:
            self.offset_changed_callback(translation)
        if self.rotation_changed_callback:
            self.rotation_changed_callback(tuple(rotation))

        # Optionally, force a refresh of all fusion views
        from src.View.mainpage.MainPage import UIMainWindow
        mw = None
        for widget in QtWidgets.QApplication.topLevelWidgets():
            if isinstance(widget, UIMainWindow):
                mw = widget
                break
        if mw is not None:
            mw.update_views()

        QMessageBox.information(self, "Loaded", f"Transform matrix loaded from {filename}")
