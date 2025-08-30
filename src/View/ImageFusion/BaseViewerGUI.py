import contextlib
import logging
from PySide6 import QtWidgets, QtGui
from src.View.mainpage.DicomView import DicomView, GraphicsScene
from src.View.ImageFusion.TranslateRotateMenu import TranslateRotateMenu
from src.Model.VTKEngine import VTKEngine
from PySide6 import QtCore
from src.View.ImageFusion.TranslateRotateMenu import get_color_pair_from_text


class BaseFusionView(DicomView):
    DEBOUNCE_MS = 5  # adjust debounce time as needed

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

        self._refresh_timer = QtCore.QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.timeout.connect(self.refresh_overlay_now)

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

    def image_display(self, overlay_image=None):
        """
        Update the image to be displayed on the DICOM View.
        If overlay_image is provided, use it as the overlay for this view.
        If self.vtk_engine is set, use it to get both the base and overlay images for manual fusion.
        """
        slider_id = self.slider.value()

        # If using VTKEngine, get both base and overlay from VTK
        if self.vtk_engine is not None:
            self._display_vtk_image(slider_id)
            return
        
    def _display_vtk_image(self, slider_id):
        orientation = self.slice_view
        # Use selected color and coloring state
        qimg = self.vtk_engine.get_slice_qimage(
            orientation, slider_id,
            fixed_color=self.fixed_color,
            moving_color=self.moving_color,
            coloring_enabled=self.coloring_enabled
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
        if self.vtk_engine is not None:
            self.vtk_engine.set_interpolation_linear(
                self.overlay_interpolation_mode == "linear"
            )
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


    def update_overlay_rotation(self, rotation_tuple, orientation=None, slice_idx=None):
        """
        Update overlay rotation in VTKEngine (manual fusion).
        """
        if self.vtk_engine is not None:
            rx, ry, rz = rotation_tuple
            if orientation is None:
                orientation = self.slice_view
            if slice_idx is None:
                slice_idx = self.slider.value()
            self.vtk_engine.set_rotation_deg(rx, ry, rz, orientation=orientation, slice_idx=slice_idx)
        self.refresh_overlay()


