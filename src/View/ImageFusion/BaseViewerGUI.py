import contextlib
from PySide6 import QtWidgets, QtGui
from src.View.mainpage.DicomView import DicomView, GraphicsScene
from src.View.ImageFusion.TranslateRotateMenu import TranslateRotateMenu
from src.Model.VTKEngine import VTKEngine
from PySide6 import QtCore

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
        super().__init__(roi_color, iso_color, cut_line_color)

        # Add color pair selection UI ---
        color_pair_options = [
            "No Colors (Grayscale)",
            "Purple + Green",
            "Yellow + Blue",
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
        if self.vtk_engine is not None:
            extent = self.vtk_engine.fixed_extent()
            if extent:
                if self.slice_view == "axial":
                    self.slider.setMinimum(extent[4])
                    self.slider.setMaximum(extent[5])
                    self.slider.setValue((extent[4] + extent[5]) // 2)
                elif self.slice_view == "coronal":
                    self.slider.setMinimum(extent[2])
                    self.slider.setMaximum(extent[3])
                    self.slider.setValue((extent[2] + extent[3]) // 2)
                elif self.slice_view == "sagittal":
                    self.slider.setMinimum(extent[0])
                    self.slider.setMaximum(extent[1])
                    self.slider.setValue((extent[0] + extent[1]) // 2)

    def image_display(self, overlay_image=None):
        """
        Update the image to be displayed on the DICOM View.
        If overlay_image is provided, use it as the overlay for this view.
        If self.vtk_engine is set, use it to get both the base and overlay images for manual fusion.
        """
        slider_id = self.slider.value()

        # If using VTKEngine, get both base and overlay from VTK
        if self.vtk_engine is not None:
            orientation = self.slice_view
            # Use selected color and coloring state
            qimg = self.vtk_engine.get_slice_qimage(
                orientation, slider_id,
                fixed_color=self.fixed_color,
                moving_color=self.moving_color,
                coloring_enabled=self.coloring_enabled
            )
            if qimg.isNull():
                # Log error and show user feedback
                print(f"[ERROR] Null QImage returned from VTKEngine for orientation '{orientation}', slice {slider_id}")
                QtWidgets.QMessageBox.warning(
                    self, "Image Load Error",
                    f"Failed to load image for orientation '{orientation}', slice {slider_id}.\n"
                    "Please check your DICOM data or transformation settings."
                )
                return
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
            return

        # --- Default (non-VTK) logic below ---
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

    def refresh_overlay(self):
        """
        Debounced repaint of the overlay image with the applied offset or transform.
        """
        self._refresh_timer.start(self.DEBOUNCE_MS) 

    def refresh_overlay_now(self):
        """
        Actually repaint the overlay image (called by debounce timer).
        Also sets VTK interpolation to nearest neighbor for speed.
        """
        if self.vtk_engine is not None:
            self.vtk_engine.set_interpolation_linear(False)
        self.image_display()
        self.scene.update()
        if hasattr(self, "viewport"):
            self.viewport().update()

    def _on_color_pair_changed(self, text):
        if text == "No Colors (Grayscale)":
            self.coloring_enabled = False
            self.fixed_color = "Grayscale"
            self.moving_color = "Grayscale"
        elif text == "Purple + Green":
            self.coloring_enabled = True
            self.fixed_color = "Purple"
            self.moving_color = "Green"
        elif text == "Yellow + Blue":
            self.coloring_enabled = True
            self.fixed_color = "Yellow"
            self.moving_color = "Blue"
        elif text == "Red + Cyan":
            self.coloring_enabled = True
            self.fixed_color = "Red"
            self.moving_color = "Cyan"
        else:
            self.coloring_enabled = True
            self.fixed_color = "Purple"
            self.moving_color = "Green"
        self.refresh_overlay()

    def update_overlay_opacity(self, value):
        """
        Update overlay opacity in VTKEngine (manual fusion).
        """
        if self.vtk_engine is not None:
            self.vtk_engine.set_opacity(value / 100.0)
        self.refresh_overlay()

    def update_overlay_offset(self, offset):
        """
        Apply translation to the overlay image (3D GUI offset).
        Also update VTKEngine translation for manual fusion.
        """
        # Accepts (x, y, z)
        self.overlay_offset = offset
        if self.vtk_engine is not None:
            x, y, z = offset
            self.vtk_engine.set_translation(x, y, z)
        self.refresh_overlay()

    def update_overlay_rotation(self, rotation_tuple):
        """
        Update overlay rotation in VTKEngine (manual fusion).
        """
        if self.vtk_engine is not None:
            rx, ry, rz = rotation_tuple
            # Determine which orientation and slice to use for rotation center
            orientation = self.slice_view
            slice_idx = self.slider.value()
            self.vtk_engine.set_rotation_deg(rx, ry, rz, orientation=orientation, slice_idx=slice_idx)
        self.refresh_overlay()


