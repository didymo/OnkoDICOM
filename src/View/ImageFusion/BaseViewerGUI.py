import contextlib
import logging
from PySide6 import QtWidgets, QtGui
from src.View.mainpage.DicomView import DicomView, GraphicsScene
from src.View.ImageFusion.TranslateRotateMenu import TranslateRotateMenu
from src.Model.VTKEngine import VTKEngine
from PySide6 import QtCore
from src.View.ImageFusion.TranslateRotateMenu import get_color_pair_from_text


class BaseFusionView(DicomView):
    DEBOUNCE_MS = 5

    def __init__(self, slice_view, roi_color=None, iso_color=None, cut_line_color=None, vtk_engine=None, translation_menu=None):
        # Always initialize these attributes first
        self.base_item = None
        self.overlay_item = None
        self.overlay_images = None
        self.overlay_offset = (0, 0)

        self.slice_view = slice_view
        self.vtk_engine = vtk_engine  # VTKEngine instance for manual fusion, or None

        # interpolation mode config: 'linear' or 'nearest'
        self.overlay_interpolation_mode = "linear"

        super().__init__(roi_color, iso_color, cut_line_color)

        color_pair_options = [
            "No Colors (Grayscale)",
            "Purple + Green",
            "Blue + Yellow",
            "Red + Cyan"
        ]
        self.color_pair_combo = QtWidgets.QComboBox()
        self.color_pair_combo.addItems(color_pair_options)
        self.color_pair_combo.setCurrentText("Purple + Green")
        # Store current color/enable state
        self.fixed_color = "Purple"
        self.moving_color = "Green"
        self.coloring_enabled = True
        # Connect signal
        self.color_pair_combo.currentTextChanged.connect(self._on_color_pair_changed)

        # Use the shared TranslateRotateMenu if provided, else create a new one
        self.translation_menu = translation_menu or TranslateRotateMenu()
        self.translation_menu.opacity_slider.valueChanged.connect(self.update_overlay_opacity)

        # Mouse mode state
        self.mouse_mode = None

        self._refresh_timer = QtCore.QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.timeout.connect(self.refresh_overlay_now)

    def wheelEvent(self, event: QtGui.QWheelEvent):
        """
            Handle mouse wheel events to scroll through slices.
            This uses angleDelta().y() which gives consistent step values across platforms.
            """

        # Get keyboard modifiers (Ctrl, Alt, Shift, etc.)
        modifiers = event.modifiers()
        ctrl = modifiers & QtCore.Qt.ControlModifier
        alt = modifiers & QtCore.Qt.AltModifier

        # If Ctrl + Alt are pressed AND we're in interrogation mode → custom zoom
        if ctrl and alt and self.mouse_mode == "interrogation":
            # Get scroll delta (angleDelta is preferred because it's device-independent)
            delta_pt = event.angleDelta()
            delta = delta_pt.y() if delta_pt.y() != 0 else delta_pt.x()

            # Fallback: some devices report pixelDelta instead of angleDelta
            if delta == 0:
                delta_pt = event.pixelDelta()
                delta = delta_pt.y() if delta_pt.y() != 0 else delta_pt.x()

            # If we got a valid delta, adjust the interrogation window size
            if delta != 0:
                self._handle_interrogation_window_size_change(delta)
            return

        # If not Ctrl+Alt interrogation, just do the normal behavior
        super().wheelEvent(event)

    def set_slider_range_from_vtk(self):
        """
        Set the slider min/max to match the VTK extent for this orientation.
        Should be called after VTKEngine is loaded.
        """
        if self.vtk_engine is None:
            return
        extent = self.vtk_engine.fixed_extent()
        if not extent:
            return

        def set_slider(min_val, max_val):
            self.slider.setMinimum(min_val)
            self.slider.setMaximum(max_val)
            self.slider.setValue((min_val + max_val) // 2)

        sv = self.slice_view
        if sv == "axial":
            set_slider(extent[4], extent[5])
            return
        if sv == "coronal":
            set_slider(extent[2], extent[3])
            return
        if sv == "sagittal":
            set_slider(extent[0], extent[1])
            return

    def image_display(self, overlay_image=None, mask_rect=None):
        """
                Update the image to be displayed on the DICOM View.
                If overlay_image is provided, use it as the overlay for this view.
                If self.vtk_engine is set, use it to get both the base and overlay images for manual fusion.
                """
        slider_id = self.slider.value()

        # If using VTKEngine (Manual Fusion), get both base and overlay from VTK
        if self.vtk_engine is not None:
            self._display_vtk_image(slider_id, mask_rect=mask_rect)
            return

        # Legacy (non-vtk) logic below
        # Base image (fixed)
        pixmaps = self.patient_dict_container.get(f"color_{self.slice_view}")
        if pixmaps is None or not (0 <= slider_id < len(pixmaps)):
            return
        image = pixmaps[slider_id]

        # Update or create the base image item
        if self.base_item is None:
            self.base_item = QtWidgets.QGraphicsPixmapItem(image)
            self.scene.addItem(self.base_item)
        else:
            self.base_item.setPixmap(image)

        # Overlay image (moving)
        overlay_pixmap = None
        if self.overlay_images is not None and 0 <= slider_id < len(self.overlay_images):
            overlay_pixmap = self.overlay_images[slider_id]

        # Update or create the overlay item
        if overlay_pixmap is not None:
            if self.overlay_item is None:
                self.overlay_item = QtWidgets.QGraphicsPixmapItem(overlay_pixmap)
                self.overlay_item.setZValue(1)  # Ensure overlay is below cut lines
                offset = getattr(self, "overlay_offset", (0, 0))
                self.overlay_item.setPos(offset[0], offset[1])
                self.scene.addItem(self.overlay_item)
            else:
                self.overlay_item.setPixmap(overlay_pixmap)
                offset = getattr(self, "overlay_offset", (0, 0))
                self.overlay_item.setPos(offset[0], offset[1])
        else:
            self.overlay_item = None

            # --- Mouse mode: connect scene mouse events ---
            if hasattr(self.scene, "set_mouse_mode_handler"):
                self.scene.set_mouse_mode_handler(
                    self._handle_mouse_mode_event,
                    self._handle_interrogation_window_size_change
                )
        
    def _display_vtk_image(self, slider_id, mask_rect = None):
        orientation = self.slice_view
        # Use selected color and coloring state
        qimg = self.vtk_engine.get_slice_qimage(
            orientation, slider_id,
            fixed_color=self.fixed_color,
            moving_color=self.moving_color,
            coloring_enabled=self.coloring_enabled,
            mask_rect=mask_rect
        )
        if qimg.isNull():
            logging.error(f"Null QImage returned from VTKEngine for orientation '{orientation}', slice {slider_id}")
            # Create a placeholder image (gray with "No Image" text)
            qimg = QtGui.QImage(256, 256, QtGui.QImage.Format_RGB32)
            qimg.fill(QtGui.QColor('gray'))
            painter = QtGui.QPainter(qimg)
            painter.setPen(QtGui.QColor('red'))
            font = QtGui.QFont('Arial', 20)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(qimg.rect(), QtCore.Qt.AlignCenter, "No Image")
            painter.end()
        pixmap = QtGui.QPixmap.fromImage(qimg)
        # Display as the base image (no overlay needed, since VTKEngine blends)
        if self.base_item is None:
            self.base_item = QtWidgets.QGraphicsPixmapItem(pixmap)
            self.scene.addItem(self.base_item)
        else:
            self.base_item.setPixmap(pixmap)
        # Remove overlay item if present
        if self.overlay_item is not None:
            self.scene.removeItem(self.overlay_item)
            self.overlay_item = None

        # --- Mouse mode: connect scene mouse events ---
        if hasattr(self.scene, "set_mouse_mode_handler"):
            self.scene.set_mouse_mode_handler(self._handle_mouse_mode_event)

    def roi_display(self):
        """
        Display ROI structures on the DICOM Image.
        """
        slider_id = self.slider.value()
        curr_slice = self.patient_dict_container.get("dict_uid")[slider_id]

        selected_rois = self.patient_dict_container.get("selected_rois")
        rois = self.patient_dict_container.get("rois")
        selected_rois_name = []
        selected_rois_name.extend(rois[roi]['name'] for roi in selected_rois)
        for roi in selected_rois:
            roi_name = rois[roi]['name']
            polygons = self.patient_dict_container.get("dict_polygons_axial")[
                roi_name][curr_slice]
            super().draw_roi_polygons(roi, polygons)

    def set_overlay_interpolation_mode(self, mode: str):
        """
        Set interpolation mode for overlay ('linear' or 'nearest').
        """
        if mode in ("linear", "nearest"):
            self.overlay_interpolation_mode = mode
        else:
            raise ValueError("Interpolation mode must be 'linear' or 'nearest'.")

    def refresh_overlay(self):
        """
        Debounced repaint of the overlay image with the applied offset or transform.
        Uses nearest neighbor interpolation for speed during rapid slider movement.
        """
        self.set_overlay_interpolation_mode("nearest")
        self._refresh_timer.start(self.DEBOUNCE_MS) 

    def refresh_overlay_now(self):
        """
                Actually repaint the overlay image (called by debounce timer).
                Uses the current interpolation mode.
                """
        if self.vtk_engine is None:
            return
        self.vtk_engine.set_interpolation_linear(
            self.overlay_interpolation_mode == "linear"
        )
        if self.get_mouse_mode() == "interrogation":
            mask_rect = None
            window_size = getattr(self, "_interrogation_window_size", 80)
            if hasattr(self, "_interrogation_mouse_pos") and self._interrogation_mouse_pos is not None:
                # Use scene coordinates for mask
                mask_rect = (*self._interrogation_mouse_pos, window_size)
            else:
                # Hide overlay everywhere if no mouse pos
                mask_rect = (-1000, -1000, 1)
            self.image_display(mask_rect=mask_rect)
        else:
            self.image_display()
        self.scene.update()
        if hasattr(self, "viewport"):
            self.viewport().update()

    def display_final_overlay(self):
        """
        Display overlay with linear interpolation for best image quality.
        Call this after slider movement is finished.
        """
        self.set_overlay_interpolation_mode("linear")
        if self.vtk_engine is not None:
            self.vtk_engine.set_interpolation_linear(True)
        self.image_display()
        self.scene.update()
        if hasattr(self, "viewport"):
            self.viewport().update()

    def _on_color_pair_changed(self, text):
        self.fixed_color, self.moving_color, self.coloring_enabled = get_color_pair_from_text(text)
        self.refresh_overlay()

    def update_overlay_opacity(self, value):
        """
        Update overlay opacity in VTKEngine (manual fusion).
        """
        if self.vtk_engine is not None:
            self.vtk_engine.set_opacity(value / 100.0)
        self.refresh_overlay()

    def update_overlay_offset(self, offset, orientation=None, slice_idx=None):
        """
        Apply translation to the overlay image (3D GUI offset).
        Also update VTKEngine translation for manual fusion.
        Additionally, propagate the update to all linked fusion views if in multi-view mode.
        Also update the transform matrix dialog if open.
        """
        self.overlay_offset = offset
        if self.vtk_engine is not None:
            x, y, z = offset
            # Pass slice context if available
            if orientation is not None and slice_idx is not None:
                self.vtk_engine.set_translation(x, y, z)
                # reuse the existing apply_transform signature with orientation/slice
                self.vtk_engine._apply_transform(orientation, slice_idx)
            else:
                self.vtk_engine.set_translation(x, y, z)
        self.refresh_overlay()

        # --- Propagate to all linked fusion views if in multi-view mode ---
        # Only propagate if this view has a translation_menu and it is shared
        if hasattr(self, "translation_menu") and hasattr(self.translation_menu, "offset_changed_callback"):
            # Avoid infinite recursion: only propagate if this is the callback source
            if getattr(self, "_is_propagating_offset", False):
                return
            self._is_propagating_offset = True
            try:
                # Call the callback to update all views (if set)
                if callable(self.translation_menu.offset_changed_callback):
                    self.translation_menu.offset_changed_callback(offset)
            finally:
                self._is_propagating_offset = False

        # --- Update matrix dialog if open ---
        if hasattr(self.translation_menu, "_matrix_dialog") and self.translation_menu._matrix_dialog is not None:
            engine = None
            if hasattr(self.translation_menu, "_get_vtk_engine_callback") and self.translation_menu._get_vtk_engine_callback:
                engine = self.translation_menu._get_vtk_engine_callback()
            if engine is not None and hasattr(engine, "transform"):
                self.translation_menu._matrix_dialog.set_matrix(engine.transform)

    def _on_mouse_mode_changed(self, mode):
        self.mouse_mode = mode
        if mode == "interrogation":
            # Set interrogation window to center of the image in image pixel coordinates
            center_x = center_y = None
            if self.vtk_engine is not None:
                slider_id = self.slider.value()
                qimg = self.vtk_engine.get_slice_qimage(
                    self.slice_view, slider_id,
                    fixed_color=self.fixed_color,
                    moving_color=self.moving_color,
                    coloring_enabled=self.coloring_enabled
                )
                center_x = int(qimg.width() / 2)
                center_y = int(qimg.height() / 2)
            elif self.base_item is not None:
                pixmap = self.base_item.pixmap()
                center_x = int(pixmap.width() / 2)
                center_y = int(pixmap.height() / 2)
            elif hasattr(self, "scene") and self.scene is not None:
                rect = self.scene.sceneRect()
                center_x = int(rect.width() / 2)
                center_y = int(rect.height() / 2)

                # Only update interrogation position if valid
            if center_x is not None and center_y is not None:
                self._interrogation_mouse_pos = (center_x, center_y)
                # else: keep last known position instead of clearing

                self.refresh_overlay()

        else:
            # Leaving interrogation mode → explicitly clear
            self._interrogation_mouse_pos = None
            self.refresh_overlay()

    def get_mouse_mode(self):
        """
        Always get the current mouse mode from the translation_menu, not from self.mouse_mode.
        """
        if hasattr(self, "translation_menu") and hasattr(self.translation_menu, "get_mouse_mode"):
            return self.translation_menu.get_mouse_mode()
        return getattr(self, "mouse_mode", None)

    def _handle_mouse_mode_event(self, scene_pos, scene_size, event_type="move"):
        """
               Called by GraphicsScene when a mouse event occurs and mouse mode is active.
               scene_pos: QPointF of event
               scene_size: QSizeF of scene
               """
        mode = self.get_mouse_mode()
        if mode is None:
            # No mouse mode active: let cut lines logic handle the event
            return

        if mode == "interrogation":
            # Clamp mouse position so it cannot go outside the scene
            scene_rect = self.scene.sceneRect()
            clamped_x = min(max(scene_pos.x(), scene_rect.left()), scene_rect.right())
            clamped_y = min(max(scene_pos.y(), scene_rect.top()), scene_rect.bottom())

            # Store clamped position
            self._interrogation_mouse_pos = (int(clamped_x), int(clamped_y))
            self.refresh_overlay()
            return

        if mode == "translate":
            x = scene_pos.x()
            y = scene_pos.y()
            w = scene_size.width()
            h = scene_size.height()
            self._handle_translate_click(x, y, w, h)
        elif mode == "rotate":
            x = scene_pos.x()
            y = scene_pos.y()
            w = scene_size.width()
            h = scene_size.height()
            self._handle_rotate_click(x, y, w, h)

    def _handle_translate_click(self, x, y, w, h):
        def axial_trans(x, y, w, h):
            if abs(x - w / 2) > abs(y - h / 2):
                return 1.0 if x < w / 2 else -1.0, 0.0, 0.0
            else:
                return 0.0, 1.0 if y < h / 2 else -1.0, 0.0

        def sagittal_trans(x, y, w, h):
            if abs(x - w / 2) > abs(y - h / 2):
                return 0.0, 1.0 if x < w / 2 else -1.0, 0.0
            else:
                return 0.0, 0.0, 1.0 if y < h / 2 else -1.0

        def coronal_trans(x, y, w, h):
            if abs(x - w / 2) > abs(y - h / 2):
                return 1.0 if x < w / 2 else -1.0, 0.0, 0.0
            else:
                return 0.0, 0.0, 1.0 if y < h / 2 else -1.0

        translate_lookup = {
            "axial": axial_trans,
            "sagittal": sagittal_trans,
            "coronal": coronal_trans,
        }
        dx, dy, dz = translate_lookup.get(self.slice_view, lambda *_: (0.0, 0.0, 0.0))(x, y, w, h)
        curr = [self.vtk_engine._tx, self.vtk_engine._ty, self.vtk_engine._tz] if self.vtk_engine else [0.0, 0.0, 0.0]
        new_offset = (curr[0] + dx, curr[1] + dy, curr[2] + dz)
        self.translation_menu.set_offsets(new_offset)
        self.update_overlay_offset(new_offset, orientation=self.slice_view, slice_idx=self.slider.value())

    def _handle_rotate_click(self, x, y, w, h):
        def axial_rot(x, y, w, h):
            if abs(x - w / 2) > abs(y - h / 2):
                return (0.0, 0.0, 0.5 if x < w / 2 else -0.5)
            else:
                return (-0.5 if y < h / 2 else 0.5, 0.0, 0.0)

        def sagittal_rot(x, y, w, h):
            if abs(x - w / 2) > abs(y - h / 2):
                return (0.5 if x < w / 2 else -0.5, 0.0, 0.0)
            else:
                return (0.0, -0.5 if y < h / 2 else 0.5, 0.0)

        def coronal_rot(x, y, w, h):
            if abs(x - w / 2) > abs(y - h / 2):
                return (0.0, -0.5 if x < w / 2 else 0.5, 0.0)
            else:
                return (-0.5 if y < h / 2 else 0.5, 0.0, 0.0)

        rotate_lookup = {
            "axial": axial_rot,
            "sagittal": sagittal_rot,
            "coronal": coronal_rot,
        }
        rx, ry, rz = rotate_lookup.get(self.slice_view, lambda *_: (0.0, 0.0, 0.0))(x, y, w, h)
        curr = [self.vtk_engine._rx, self.vtk_engine._ry, self.vtk_engine._rz] if self.vtk_engine else [0.0, 0.0, 0.0]
        new_rot = (curr[0] + rx, curr[1] + ry, curr[2] + rz)
        self.translation_menu.rotate_sliders[0].setValue(int(round(new_rot[0] * 10)))
        self.translation_menu.rotate_sliders[1].setValue(int(round(new_rot[1] * 10)))
        self.translation_menu.rotate_sliders[2].setValue(int(round(new_rot[2] * 10)))
        self.update_overlay_rotation(new_rot, orientation=self.slice_view, slice_idx=self.slider.value())


    def update_overlay_rotation(self, rotation_tuple, orientation=None, slice_idx=None):
        """
        Update overlay rotation in VTKEngine (manual fusion).
        Additionally, propagate the update to all linked fusion views if in multi-view mode.
        Also update the transform matrix dialog if open.
        """
        if self.vtk_engine is not None:
            rx, ry, rz = rotation_tuple
            if orientation is None:
                orientation = self.slice_view
            if slice_idx is None:
                slice_idx = self.slider.value()
            self.vtk_engine.set_rotation_deg(rx, ry, rz, orientation=orientation, slice_idx=slice_idx)
        self.refresh_overlay()

        # --- Propagate to all linked fusion views if in multi-view mode ---
        if hasattr(self, "translation_menu") and hasattr(self.translation_menu, "rotation_changed_callback"):
            if getattr(self, "_is_propagating_rotation", False):
                return
            self._is_propagating_rotation = True
            try:
                if callable(self.translation_menu.rotation_changed_callback):
                    self.translation_menu.rotation_changed_callback(rotation_tuple)
            finally:
                self._is_propagating_rotation = False

        # --- Update matrix dialog if open ---
        if hasattr(self.translation_menu, "_matrix_dialog") and self.translation_menu._matrix_dialog is not None:
            engine = None
            if hasattr(self.translation_menu, "_get_vtk_engine_callback") and self.translation_menu._get_vtk_engine_callback:
                engine = self.translation_menu._get_vtk_engine_callback()
            if engine is not None and hasattr(engine, "transform"):
                self.translation_menu._matrix_dialog.set_matrix(engine.transform)

    def update_view(self, zoom_change=False):
        """
        Update the view of the DICOM Image.
        :param zoom_change: Boolean indicating whether the user wants
        to change the zoom. False by default.
        """
        super().update_view(zoom_change)
        # After zoom or view update, reapply interrogation mask if needed
        if self.get_mouse_mode() == "interrogation":
            self.refresh_overlay_now()

    def zoom_in(self):
        super().zoom_in()
        if self.get_mouse_mode() == "interrogation":
            self.refresh_overlay_now()

    def zoom_out(self):
        super().zoom_out()
        if self.get_mouse_mode() == "interrogation":
            self.refresh_overlay_now()

    def _handle_interrogation_window_size_change(self, delta):
        """
            Adjust the interrogation window size based on scroll delta.
            Positive delta = shrink window (zoom in).
            Negative delta = enlarge window (zoom out).
            """

        # Safety: make sure we're still in interrogation mode
        if self.get_mouse_mode() != "interrogation":
            return

        # Pixel shrink and grow amount
        step = 8

        # Initialize default interrogation window size if not set yet
        if not hasattr(self, "_interrogation_window_size"):
            self._interrogation_window_size = 80

        # Update interrogation window size based on scroll direction
        if delta > 0:
            # Scroll forward
            new_size = max(10, self._interrogation_window_size - step)
        else:
            # Scroll backward
            new_size = self._interrogation_window_size + step

        # Save updated size
        self._interrogation_window_size = new_size

        # If mouse position is available, refresh the overlay at that location
        if hasattr(self, "_interrogation_mouse_pos") and self._interrogation_mouse_pos is not None:
            self.refresh_overlay_now()

