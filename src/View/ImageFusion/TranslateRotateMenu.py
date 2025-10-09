import itertools
import threading
import numpy as np
import os
import logging
import pydicom
import datetime

from PIL.ImageQt import QPixmap
from PySide6 import QtWidgets, QtCore
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFileDialog, QMessageBox
from src.View.ImageFusion.TransformMatrixDialog import TransformMatrixDialog
from src.Controller.PathHandler import resource_path
from src.Model.DicomUtils import truncate_ds_fields
from src.Model.PatientDictContainer import PatientDictContainer
from pydicom.dataset import FileDataset
from pydicom.uid import generate_uid
from pydicom import dcmread
from pydicom.dataset import Dataset
from pydicom.uid import generate_uid

"""
    For all private tags 0x7777, 0x0020 / 0x7777, 0x0021 / etc
    these are private dicom tags for extra info used as fallback if the normal registration tag for loading the saved transform fails. 
    (saving normal rego first means it can be used by other programs. Private tags can only be read by onko dicom).
    they must use an odd group number i.e 0x7777 and an element number i.e 0x0010, can be saved as any odd number group 
    and must be consistent in the program as it needs to know it to read private tags

    This is saved and set in Translate rotation menu _create_spatial_registration_dicom
    9/10/25 in line 650 & 651
    
    # Save user translation/rotation as private tags for round-trip
        ds.add_new((0x7777, 0x0020), 'LT', ",".join([str(v) for v in translation]))
        ds.add_new((0x7777, 0x0021), 'LT', ",".join([str(v) for v in rotation]))
        
    see links for more details
        https://dicom.nema.org/medical/dicom/current/output/chtml/part05/sect_7.8.html
        https://pydicom.github.io/pydicom/stable/guides/user/private_data_elements.html

"""


def get_color_pair_from_text(text):
    """
        Maps a combo box selection string to corresponding color pair values.

        Args:
            text (str): The string from the color combo box (e.g. "Purple + Green").

        Returns:
            tuple[str, str, bool]: (fixed_color, moving_color, coloring_enabled)
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
        Widget for manual image fusion controls.

        Provides:
          - Color selection for overlay visualization.
          - Translation sliders (LR, PA, IS).
          - Rotation sliders (LR, PA, IS).
          - Mouse interaction modes (translate, rotate, interrogation).
          - Opacity adjustment.
          - Buttons for reset/save/load/show transform matrix.
        """

    def __init__(self, _back_callback=None):
        """
              Initializes the TranslateRotateMenu widget.

              Args:
                  _back_callback (callable, optional): Callback invoked when going 'back'.
              """
        super().__init__()
        self.offset_changed_callback = None
        self.mouse_mode = None

        # Main layout (vertical stacking of all sections)
        layout = QtWidgets.QVBoxLayout()

        # Initialize all UI sections
        self._init_color_pair_section(layout)
        self._init_translate_section(layout)
        self._init_mouse_mode_toolbar(layout)
        self._init_rotate_section(layout)
        self._init_opacity_section(layout)
        self._init_transform_buttons(layout)

        # Add stretch so content stays at top, flexible space at bottom
        layout.addStretch(1)
        self.setLayout(layout)

        # Matrix dialog instance (created on demand)
        self._matrix_dialog = None
        self._get_vtk_engine_callback = None

        # Store current colour/enable state
        self.fixed_color = "Purple"
        self.moving_color = "Green"
        self.coloring_enabled = True

        # Mouse mode callback (set by parent)
        self.mouse_mode_changed_callback = None

    def _init_color_pair_section(self, layout):
        """
                Creates the overlay color pair selection combo box.
                """
        color_pair_options = [
            "No Colors (Grayscale)",
            "Purple + Green",
            "Blue + Yellow",
            "Red + Cyan"
        ]
        color_pair_hbox = QtWidgets.QHBoxLayout()
        color_pair_hbox.addWidget(QtWidgets.QLabel("Overlay Colors:"))

        # Combo box with predefined color pair options
        self.color_pair_combo = QtWidgets.QComboBox()
        self.color_pair_combo.addItems(color_pair_options)
        self.color_pair_combo.setCurrentText("Purple + Green")
        color_pair_hbox.addWidget(self.color_pair_combo)

        # Add section to main layout
        layout.addLayout(color_pair_hbox)

        # Initialize with default colors
        self.fixed_color, self.moving_color, self.coloring_enabled = get_color_pair_from_text("Purple + Green")

        # Connect event when color selection changes
        self.color_pair_combo.currentTextChanged.connect(self._on_color_pair_changed)

    def _init_translate_section(self, layout):
        """
                Creates translation sliders for LR, PA, and IS axes.
                Each slider controls translation in millimeters.
                """
        layout.addSpacing(4)
        layout.addWidget(QtWidgets.QLabel("Translate:"), alignment=Qt.AlignLeft)
        self.translate_sliders = []
        self.translate_labels = []

        # Loop over the three anatomical axes
        for i, axis in enumerate(['LR', 'PA', 'IS']):
            hbox = QtWidgets.QHBoxLayout()
            label = QtWidgets.QLabel(axis)

            # Axis label
            label.setFixedWidth(30)

            # Slider with mm range
            slider = QtWidgets.QSlider(Qt.Horizontal)
            slider.setMinimum(-500)
            slider.setMaximum(500)
            slider.setValue(0)
            slider.setSingleStep(1)  # 1mm per step
            slider.setPageStep(1)
            slider.setTickInterval(0)
            slider.setTracking(True)
            slider.valueChanged.connect(self._make_offset_change_handler(i))

            # Display value label
            value_label = QtWidgets.QLabel("0 mm")
            value_label.setFixedWidth(50)

            # Pack row
            hbox.addWidget(label)
            hbox.addWidget(slider)
            hbox.addWidget(value_label)
            layout.addLayout(hbox)

            # Keep references
            self.translate_sliders.append(slider)
            self.translate_labels.append(value_label)

    def _init_mouse_mode_toolbar(self, layout):
        """
                Creates toolbar for mouse interaction modes (translate, rotate, interrogation).
                Allows toggling between exclusive modes.
                """
        mouse_mode_hbox = QtWidgets.QHBoxLayout()
        mouse_mode_hbox.setSpacing(5)
        mouse_mode_hbox.setContentsMargins(5, 2, 5, 2)

        # Buttons for each mode
        self.mouse_translate_btn = QtWidgets.QPushButton()
        self.mouse_rotate_btn = QtWidgets.QPushButton()
        self.mouse_interrogation_btn = QtWidgets.QPushButton()
        self.mouse_none_btn = QtWidgets.QPushButton()

        # Tooltips
        self.mouse_translate_btn.setToolTip("Enable mouse translation mode")
        self.mouse_rotate_btn.setToolTip("Enable mouse rotation mode")
        self.mouse_interrogation_btn.setToolTip(
            "Enable interrogation window mode (focus overlay in a square around mouse)")

        # Icon sizes
        self.mouse_translate_btn.setIconSize(QtCore.QSize(20, 20))
        self.mouse_rotate_btn.setIconSize(QtCore.QSize(20, 20))
        self.mouse_interrogation_btn.setIconSize(QtCore.QSize(20, 22))

        # Use QIcon's built-in modes for checked/unchecked states
        self.mouse_translate_btn.setCheckable(True)
        self.mouse_rotate_btn.setCheckable(True)
        self.mouse_interrogation_btn.setCheckable(True)

        # Set alternate icons for checked state using addPixmap
        translate_icon = QIcon()
        translate_icon.addPixmap(QPixmap(resource_path("res/images/btn-icons/translate_arrow_icon.png")),
                                 QIcon.Mode.Normal, QIcon.State.Off)
        translate_icon.addPixmap(QPixmap(resource_path("res/images/btn-icons/translate_arrow_icon_black_border.png")),
                                 QIcon.Mode.Normal, QIcon.State.On)
        self.mouse_translate_btn.setIcon(translate_icon)

        rotate_icon = QIcon()
        rotate_icon.addPixmap(QPixmap(resource_path("res/images/btn-icons/rotate_arrow_icon.png")), QIcon.Mode.Normal,
                              QIcon.State.Off)
        rotate_icon.addPixmap(QPixmap(resource_path("res/images/btn-icons/rotate_arrow_icon_black_border.png")),
                              QIcon.Mode.Normal, QIcon.State.On)
        self.mouse_rotate_btn.setIcon(rotate_icon)

        interrogation_icon = QIcon()
        interrogation_icon.addPixmap(QPixmap(resource_path("res/images/btn-icons/interrogation_window_icon.png")),
                                     QIcon.Mode.Normal, QIcon.State.Off)
        interrogation_icon.addPixmap(
            QPixmap(resource_path("res/images/btn-icons/interrogation_window_icon_black_border.png")),
            QIcon.Mode.Normal, QIcon.State.On)
        self.mouse_interrogation_btn.setIcon(interrogation_icon)

        # Center buttons horizontally
        mouse_mode_hbox.addStretch(1)
        mouse_mode_hbox.addWidget(self.mouse_translate_btn)
        mouse_mode_hbox.addWidget(self.mouse_rotate_btn)
        mouse_mode_hbox.addWidget(self.mouse_interrogation_btn)
        mouse_mode_hbox.addStretch(1)

        # Insert below color pair section with spacing
        layout.insertSpacing(1, 8)
        layout.insertLayout(2, mouse_mode_hbox)

        # Make buttons mutually exclusive
        self.mouse_mode_group = QtWidgets.QButtonGroup(self)
        self.mouse_mode_group.setExclusive(True)
        self.mouse_mode_group.addButton(self.mouse_translate_btn)
        self.mouse_mode_group.addButton(self.mouse_rotate_btn)

        self.mouse_mode_group.addButton(self.mouse_interrogation_btn)

        # Track last checked for "toggle off" behavior
        self._last_checked_button = None

        def on_mouse_mode_btn_clicked(btn):
            """
            Handles mouse mode button clicks to toggle between translation, rotation, and interrogation modes.
            Updates the internal mouse mode state and triggers the mouse mode changed callback if set.
            """
            if self._last_checked_button == btn and btn.isChecked():
                # Toggle off if same button clicked twice
                self.mouse_mode_group.setExclusive(False)
                btn.setChecked(False)
                self.mouse_mode_group.setExclusive(True)
                self._last_checked_button = None
                self.mouse_mode = None
            else:
                # Otherwise set mode accordingly
                self._last_checked_button = btn
                if btn == self.mouse_translate_btn:
                    self.mouse_mode = "translate"
                elif btn == self.mouse_rotate_btn:
                    self.mouse_mode = "rotate"

                elif btn == self.mouse_interrogation_btn:
                    self.mouse_mode = "interrogation"
                elif btn == self.mouse_none_btn:
                    self.mouse_mode = None

            # Notify parent if callback set
            if self.mouse_mode_changed_callback:
                self.mouse_mode_changed_callback(self.mouse_mode)

        # Connect signals
        self.mouse_translate_btn.clicked.connect(lambda: on_mouse_mode_btn_clicked(self.mouse_translate_btn))
        self.mouse_rotate_btn.clicked.connect(lambda: on_mouse_mode_btn_clicked(self.mouse_rotate_btn))
        self.mouse_interrogation_btn.clicked.connect(lambda: on_mouse_mode_btn_clicked(self.mouse_interrogation_btn))

    def _init_rotate_section(self, layout):
        """
                Creates rotation sliders for LR, PA, and IS axes.
                Each slider controls rotation in degrees (0.1° per step).
                """
        layout.addSpacing(5)

        # Add the rotation sliders
        layout.addWidget(QtWidgets.QLabel("Rotate:"), alignment=Qt.AlignLeft)
        self.rotate_sliders = []
        self.rotate_labels = []
        self.rotation_changed_callback = None

        # Loop over the three anatomical axes
        for i, axis in enumerate(['LR', 'PA', 'IS']):
            hbox = QtWidgets.QHBoxLayout()

            # Axis label
            label = QtWidgets.QLabel(axis)
            label.setFixedWidth(30)

            # Slider with degrees range
            slider = QtWidgets.QSlider(Qt.Horizontal)
            slider.setMinimum(-1800)  # -180.0 deg (in 0.1 deg steps)
            slider.setMaximum(1800)  # +180.0 deg (in 0.1 deg steps)
            slider.setValue(0)
            slider.setSingleStep(1)  # 0.1 deg per step
            slider.valueChanged.connect(self._make_rotation_change_handler(i))

            # Display value label
            value_label = QtWidgets.QLabel("0°")
            value_label.setFixedWidth(50)

            # Pack row
            hbox.addWidget(label)
            hbox.addWidget(slider)
            hbox.addWidget(value_label)
            layout.addLayout(hbox)

            # Keep references
            self.rotate_sliders.append(slider)
            self.rotate_labels.append(value_label)

    def _init_opacity_section(self, layout):
        """
                Creates an opacity slider (0–100%).
                """
        layout.addSpacing(5)
        layout.addWidget(QtWidgets.QLabel("Opacity:"), alignment=Qt.AlignLeft)

        # Setting the values and adding the widget
        self.opacity_slider = QtWidgets.QSlider(Qt.Horizontal)
        self.opacity_slider.setMinimum(0)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setValue(50)
        layout.addWidget(self.opacity_slider)

    def _init_transform_buttons(self, layout):
        """
                Adds transform-related action buttons:
                  - Reset transform
                  - Save/load state
                  - Show transform matrix
                """
        # Reset button
        reset_btn = QtWidgets.QPushButton("Reset Transform")
        reset_btn.setToolTip("Reset all translation and rotation to zero")
        reset_btn.clicked.connect(self.reset_transform)
        layout.addWidget(reset_btn)

        # Save button
        save_button = QtWidgets.QPushButton("Save Fusion State")
        save_button.clicked.connect(self.save_fusion_state)
        layout.addWidget(save_button)

        # Load button
        load_button = QtWidgets.QPushButton("Load Fusion State")
        load_button.clicked.connect(self.load_fusion_state)
        layout.addWidget(load_button)

        # Show matrix button
        show_matrix_btn = QtWidgets.QPushButton("Show Transform Matrix")
        show_matrix_btn.setToolTip("Show the current 4x4 transformation matrix")
        show_matrix_btn.clicked.connect(self.show_transform_matrix)
        layout.addWidget(show_matrix_btn)

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
            self.mouse_interrogation_btn.setChecked(False)
        elif mode == "rotate":
            self.mouse_translate_btn.setChecked(False)
            self.mouse_interrogation_btn.setChecked(False)
            self.mouse_rotate_btn.setChecked(True)
        elif mode == "interrogation":
            self.mouse_translate_btn.setChecked(False)
            self.mouse_interrogation_btn.setChecked(True)
            self.mouse_rotate_btn.setChecked(False)
        else:
            self.mouse_translate_btn.setChecked(False)
            self.mouse_rotate_btn.setChecked(False)
            self.mouse_interrogation_btn.setChecked(False)
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
                self._matrix_dialog.set_matrix(engine.sitk_matrix)

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
                self._matrix_dialog.set_matrix(engine.sitk_matrix)

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
                self._matrix_dialog.set_matrix(engine.sitk_matrix)

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
            self._matrix_dialog.set_matrix(engine.sitk_matrix)
        self._matrix_dialog.show()
        self._matrix_dialog.raise_()
        self._matrix_dialog.activateWindow()

    def save_fusion_state(self):
        """
                Save the current fusion transform as a DICOM Spatial Registration Object (SRO).
                This function creates a standards-compliant DICOM SRO containing the 4x4 transformation matrix
                for the moving image overlay, referencing the fixed and moving images. The user is prompted
                to select the save location and filename for the DICOM file.
                Returns:
                    None
                """


        vtk_engine = self._get_vtk_engine_callback() if hasattr(self,
                                                                "_get_vtk_engine_callback") and self._get_vtk_engine_callback else None
        if vtk_engine is None:
            QMessageBox.warning(self, "Error", "No VTK engine found.")
            logging.error("No VTK engine found in save_fusion_state")
            return

        # Gather the 4x4 transform matrix
        #matris is used ignore the error
        matrix = None
        if hasattr(vtk_engine, "transform"):
            m = vtk_engine.transform.GetMatrix()
            matrix = np.array([[m.GetElement(i, j) for j in range(4)] for i in range(4)], dtype=np.float32)
        else:
            QMessageBox.warning(self, "Error", "No transform matrix found.")
            logging.error("No transform matrix found")
            return

        # Print translation and rotation being saved
        translation = [vtk_engine._tx, vtk_engine._ty, vtk_engine._tz]
        rotation = [vtk_engine._rx, vtk_engine._ry, vtk_engine._rz]

        ds = self._create_spatial_registration_dicom(matrix, translation, rotation, vtk_engine)

        moving_dir = getattr(vtk_engine, "moving_dir", None)

        initial_path = os.path.join(moving_dir, "transform.dcm") if moving_dir else "transform.dcm"
        filename, _ = QFileDialog.getSaveFileName(self, "Save Spatial Registration (SRO)", initial_path,
                                                  "DICOM Files (*.dcm)")
        if filename:
            truncate_ds_fields(ds)
            ds.save_as(filename)
            QMessageBox.information(self, "Saved", f"Spatial Registration (SRO) saved to {filename}")

    def _create_spatial_registration_dicom(self, matrix, translation, rotation, vtk_engine):
        """
                Create a DICOM Spatial Registration Object (SRO) dataset with the given transform.

                Args:
                    matrix: 4x4 numpy array representing the transformation matrix.
                    translation: List of translation values [tx, ty, tz].
                    rotation: List of rotation values [rx, ry, rz].
                    vtk_engine: The VTKEngine instance (for UIDs).

                Returns:
                    pydicom FileDataset representing the SRO.
                """

        fixed_ds, fixed_series_uid, fixed_image_uid = self._get_fixed_image_info()
        moving_series_uid, moving_image_uid = self._get_moving_image_info(vtk_engine)
        patient_name, patient_id = self._get_patient_info(fixed_ds)

        file_meta = self._create_file_meta()
        ds = FileDataset("transform.dcm", {}, file_meta=file_meta, preamble=b"\0" * 128)
        ds.is_little_endian = True
        ds.is_implicit_VR = True

        self._set_dicom_fields(ds, patient_name, patient_id, file_meta)
        self._add_referenced_series(ds, fixed_series_uid, fixed_image_uid)
        self._add_registration_sequence(ds, matrix, moving_series_uid, moving_image_uid)

        # Save user translation/rotation as private tags for round-trip
        ds.add_new((0x7777, 0x0020), 'LT', ",".join([str(v) for v in translation]))
        ds.add_new((0x7777, 0x0021), 'LT', ",".join([str(v) for v in rotation]))

        return ds

    def _get_fixed_image_info(self):
        """
                Retrieve the fixed image dataset and its SeriesInstanceUID and SOPInstanceUID.

                Returns:
                    tuple: (fixed_ds, fixed_series_uid, fixed_image_uid)
                """
        pdc = PatientDictContainer()
        fixed_ds = pdc.dataset[0] if pdc.dataset and 0 in pdc.dataset else None
        fixed_series_uid = getattr(fixed_ds, "SeriesInstanceUID", "1.2.3.4.5.6.7.8.1")
        fixed_image_uid = getattr(fixed_ds, "SOPInstanceUID", "1.2.3.4.5.6.7.8.1.1")
        return fixed_ds, fixed_series_uid, fixed_image_uid

    def _get_moving_image_info(self, vtk_engine):
        """
                Retrieve the moving image SeriesInstanceUID and SOPInstanceUID from the VTKEngine.

                Args:
                    vtk_engine: The VTKEngine instance.

                Returns:
                    tuple: (moving_series_uid, moving_image_uid)
                """
        moving_series_uid = getattr(vtk_engine, "moving_series_uid", None)
        moving_image_uid = getattr(vtk_engine, "moving_image_uid", None)
        if not moving_series_uid or not moving_image_uid:
            moving_series_uid = "1.2.3.4.5.6.7.8.2"
            moving_image_uid = "1.2.3.4.5.6.7.8.2.1"
        return moving_series_uid, moving_image_uid

    def _get_patient_info(self, fixed_ds):
        """
                Retrieve the patient name and ID for the DICOM SRO.

                Args:
                    fixed_ds: The fixed image dataset.

                Returns:
                    tuple: (patient_name, patient_id)
                """
        

        patient_name = getattr(self, "patient_name", None)
        patient_id = getattr(self, "patient_id", None)
        if not patient_name or not patient_id:
            try:
                pdc = PatientDictContainer()
                filepaths = pdc.filepaths
                if filepaths and isinstance(filepaths, dict):
                    if image_keys := [
                        k for k in filepaths.keys() if str(k).isdigit()
                    ]:
                        first_key = sorted(image_keys, key=lambda x: int(x))[0]
                        first_image_path = filepaths[first_key]
                        ds_fixed = dcmread(first_image_path, stop_before_pixels=True)
                        patient_name = getattr(ds_fixed, "PatientName", None)
                        patient_id = getattr(ds_fixed, "PatientID", None)
                        logging.debug(
                            f"Found patient info in file: {first_image_path} PatientName={patient_name}, PatientID={patient_id}")
            except Exception as e:
                logging.debug(f"Could not get patient info from PatientDictContainer filepaths: {e}")

        if not patient_name or not patient_id:
            try:
                pdc = PatientDictContainer()
                patient_name = pdc.get("patient_name") or "FUSION"
                patient_id = pdc.get("patient_id") or "FUSION"
                logging.debug(
                    f"Fallback patient info from PatientDictContainer: PatientName={patient_name}, PatientID={patient_id}")
            except Exception as e:
                logging.debug(f"Could not get patient info from PatientDictContainer: {e}")
                patient_name = "FUSION"
                patient_id = "FUSION"
                logging.debug(f"Using default patient info: PatientName={patient_name}, PatientID={patient_id}")

        if patient_name and len(str(patient_name)) > 64:
            logging.warning(
                f"PatientName length ({len(str(patient_name))}) exceeds DICOM max of 64. It will be truncated.")
            patient_name = str(patient_name)[:64]
        if patient_id and len(str(patient_id)) > 64:
            logging.warning(f"PatientID length ({len(str(patient_id))}) exceeds DICOM max of 64. It will be truncated.")
            patient_id = str(patient_id)[:64]
        logging.debug(f"Saving transform DICOM with PatientName={patient_name}, PatientID={patient_id}")
        return patient_name, patient_id

    def _create_file_meta(self):
        """
                Create the DICOM file meta information for the SRO.

                Returns:
                    pydicom.Dataset: The file meta dataset.
                """
        
        file_meta = pydicom.Dataset()
        file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.66.1"  # Spatial Registration Storage
        file_meta.MediaStorageSOPInstanceUID = generate_uid()
        file_meta.ImplementationClassUID = generate_uid()
        return file_meta

    def _set_dicom_fields(self, ds, patient_name, patient_id, file_meta):
        """
                Set the required DICOM fields for the SRO dataset.

                Args:
                    ds: The FileDataset to update.
                    patient_name: The patient name.
                    patient_id: The patient ID.
                    file_meta: The file meta dataset.
                """
    
        dt = datetime.datetime.now()
        ds.PatientName = patient_name
        ds.PatientID = patient_id
        ds.StudyInstanceUID = generate_uid()
        ds.SeriesInstanceUID = generate_uid()
        ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
        ds.SOPClassUID = file_meta.MediaStorageSOPClassUID
        ds.Modality = "REG"
        ds.StudyDate = dt.strftime('%Y%m%d')
        ds.StudyTime = dt.strftime('%H%M%S')
        ds.SeriesDescription = "Manual Fusion Spatial Registration"
        ds.SeriesNumber = "1"
        ds.InstanceNumber = "1"

    def _add_referenced_series(self, ds, fixed_series_uid, fixed_image_uid):
        """
                Add the referenced series and image sequence for the fixed image.

                Args:
                    ds: The FileDataset to update.
                    fixed_series_uid: The SeriesInstanceUID of the fixed image.
                    fixed_image_uid: The SOPInstanceUID of the fixed image.
                """
        
        ds.ReferencedSeriesSequence = [Dataset()]
        ds.ReferencedSeriesSequence[0].SeriesInstanceUID = fixed_series_uid
        ds.ReferencedSeriesSequence[0].ReferencedImageSequence = [Dataset()]
        ds.ReferencedSeriesSequence[0].ReferencedImageSequence[0].ReferencedSOPClassUID = "1.2.840.10008.5.1.4.1.1.2"
        ds.ReferencedSeriesSequence[0].ReferencedImageSequence[0].ReferencedSOPInstanceUID = fixed_image_uid

    def _add_registration_sequence(self, ds, matrix, moving_series_uid, moving_image_uid):
        """
                Add the registration sequence for the moving image and transformation.

                Args:
                    ds: The FileDataset to update.
                    matrix: 4x4 numpy array representing the transformation matrix.
                    moving_series_uid: The SeriesInstanceUID of the moving image.
                    moving_image_uid: The SOPInstanceUID of the moving image.
                """


        reg = Dataset()
        reg.MatrixRegistrationSequence = [Dataset()]
        reg.MatrixRegistrationSequence[0].FrameOfReferenceTransformationMatrixType = "RIGID"
        reg.MatrixRegistrationSequence[0].FrameOfReferenceTransformationMatrix = [float(v) for v in matrix.flatten()]
        reg.MatrixRegistrationSequence[0].FrameOfReferenceTransformationComment = "Manual fusion transform"
        reg.MatrixRegistrationSequence[0].FrameOfReferenceUID = generate_uid()
        reg.MatrixRegistrationSequence[0].ReferencedSeriesSequence = [Dataset()]
        reg.MatrixRegistrationSequence[0].ReferencedSeriesSequence[0].SeriesInstanceUID = moving_series_uid
        reg.MatrixRegistrationSequence[0].ReferencedSeriesSequence[0].ReferencedImageSequence = [Dataset()]
        reg.MatrixRegistrationSequence[0].ReferencedSeriesSequence[0].ReferencedImageSequence[
            0].ReferencedSOPClassUID = "1.2.840.10008.5.1.4.1.1.2"
        reg.MatrixRegistrationSequence[0].ReferencedSeriesSequence[0].ReferencedImageSequence[
            0].ReferencedSOPInstanceUID = moving_image_uid
        ds.RegistrationSequence = [reg]
        # Also add the referenced series/image sequence for moving image (for compatibility)
        ds.RegistrationSequence[0].MatrixRegistrationSequence[0].ReferencedSeriesSequence = [Dataset()]
        ds.RegistrationSequence[0].MatrixRegistrationSequence[0].ReferencedSeriesSequence[
            0].SeriesInstanceUID = moving_series_uid
        ds.RegistrationSequence[0].MatrixRegistrationSequence[0].ReferencedSeriesSequence[0].ReferencedImageSequence = [
            Dataset()]
        ds.RegistrationSequence[0].MatrixRegistrationSequence[0].ReferencedSeriesSequence[0].ReferencedImageSequence[
            0].ReferencedSOPClassUID = "1.2.840.10008.5.1.4.1.1.2"
        ds.RegistrationSequence[0].MatrixRegistrationSequence[0].ReferencedSeriesSequence[0].ReferencedImageSequence[
            0].ReferencedSOPInstanceUID = moving_image_uid


    def load_fusion_state(self):
        """
                Load a fusion transform state from a DICOM Spatial Registration Object (SRO).
                This function loads a previously saved 4x4 transformation matrix from a DICOM SRO file
                (created by the Save Fusion State function) and applies it to the current fusion session.
                The user is prompted to select the DICOM file to load.
                Returns:
                    None
                """

        vtk_engine = self._get_vtk_engine_callback() if hasattr(self,
                                                                "_get_vtk_engine_callback") and self._get_vtk_engine_callback else None
        if vtk_engine is None:
            logging.error("No VTK engine found in load_fusion_state")
            return

        moving_dir = getattr(vtk_engine, "moving_dir", None)

        initial_path = moving_dir or ""
        filename, _ = QFileDialog.getOpenFileName(self, "Load Fusion State", initial_path, "DICOM Files (*.dcm)")

        if filename:
            try:
                ds = pydicom.dcmread(filename)
            except Exception as e:
                logging.error(f"Could not read DICOM file:\n{e}")
                return

            # Check for Spatial Registration Object
            if hasattr(ds, "RegistrationSequence"):
                self._extracted_from_load_fusion_state_sro(ds, np, vtk_engine, filename)
            #fallback to private tags if above failed
            elif (0x7777, 0x0020) in ds or (0x7777, 0x0021) in ds:
                self._extracted_from_load_fusion_state_sro(ds, np, vtk_engine, filename)
            else:
                logging.error("No spatial registration found in DICOM file.\nPlease select a transform.dcm file "
                              "created by the Save Fusion State function.")

    def _extracted_from_load_fusion_state_sro(self, ds, np, vtk_engine, filename):
        """
        Apply a loaded fusion transform from a DICOM SRO to the current session.
        Given a DICOM dataset containing a spatial registration, this method extracts the
        4x4 transformation matrix, applies it to the VTK engine, updates the GUI sliders,
        and refreshes the fusion views.
        Args:
            ds: The loaded pydicom Dataset containing the SRO.
            np: The numpy module.
            vtk_engine: The VTKEngine instance to update.
            filename: The filename of the loaded DICOM file.
        Returns:
            None
        """
        # Import main window here to avoid circular imports
        from src.View.mainpage.MainPage import UIMainWindow

        # --- Extract 4x4 transform matrix from SRO ---
        reg_seq = ds.RegistrationSequence[0]
        mat_seq = reg_seq.MatrixRegistrationSequence[0]
        matrix_flat = mat_seq.FrameOfReferenceTransformationMatrix
        matrix = np.array(matrix_flat, dtype=np.float32).reshape((4, 4))

        # For SRO, translation/rotation are not stored separately, so extract from matrix
        # Try to load user translation/rotation if present
        if (0x7777, 0x0020) in ds:
            translation = [float(x) for x in ds[(0x7777, 0x0020)].value.split(",")]
        else:
            translation = [matrix[0, 3], matrix[1, 3], matrix[2, 3]]
        if (0x7777, 0x0021) in ds:
            rotation = [float(x) for x in ds[(0x7777, 0x0021)].value.split(",")]
        else:
            rotation = [0, 0, 0]

        main_window = next(
            (w for w in QtWidgets.QApplication.topLevelWidgets() if isinstance(w, UIMainWindow)),
            None,
        )
        if main_window is not None:
            main_window.apply_matrix_and_transform_to_engine(
                vtk_engine=vtk_engine,
                matrix=matrix,
                translation=translation,
                rotation=rotation,
                menu=self
            )

        

        mw = next(
            (
                widget
                for widget in QtWidgets.QApplication.topLevelWidgets()
                if isinstance(widget, UIMainWindow)
            ),
            None,
        )
        if mw is not None:
            mw.update_views()

        if threading.current_thread() is threading.main_thread():
            QMessageBox.information(self, "Loaded", f"Spatial Registration loaded from {filename}")
        else:
            logging.error(f"[INFO] Spatial Registration loaded from {filename}")