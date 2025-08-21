import contextlib
from PySide6 import QtWidgets, QtGui
from src.View.mainpage.DicomView import DicomView, GraphicsScene
from src.View.ImageFusion.TranslateRotateMenu import TranslateRotateMenu


class BaseFusionView(DicomView):
    def __init__(self, slice_view, roi_color=None, iso_color=None, cut_line_color=None):
        self.slice_view = slice_view
        super().__init__(roi_color, iso_color, cut_line_color)

        self.translation_menu = TranslateRotateMenu()
        self.translation_menu.set_offset_changed_callback(self.update_overlay_offset)
        self.overlay_item = None
        self.overlay_images = None
        self.base_item = None
        self.update_view()

    def image_display(self, overlay_image=None):
        """
                Update the image to be displayed on the DICOM View.
                If overlay_image is provided, use it as the overlay for this view.
                Also ensures overlay_item is created and positioned correctly.
                """
        slider_id = self.slider.value()

        if overlay_image is not None:
            image = overlay_image
        elif self.overlay_images is not None:
            if 0 <= slider_id < len(self.overlay_images):
                image = self.overlay_images[slider_id]
            else:
                return
        else:
            pixmaps = self.patient_dict_container.get(f"color_{self.slice_view}")
            if pixmaps is None:
                return  # Prevent NoneType subscriptable error
            if 0 <= slider_id < len(pixmaps):
                image = pixmaps[slider_id]
            else:
                return

        # Update or create the base image item
        if self.base_item is None:
            self.base_item = QtWidgets.QGraphicsPixmapItem(image)
            self.scene.addItem(self.base_item)
        else:
            self.base_item.setPixmap(image)

            # Update or create the overlay item
        if self.overlay_images is not None and 0 <= slider_id < len(self.overlay_images):
            overlay_pixmap = self.overlay_images[slider_id]
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

    def update_overlay_offset(self, offset):
        """
        Apply translation to the overlay image.
        offset: tuple (x, y)
        """
        self.overlay_offset = offset
        self.refresh_overlay()

    def refresh_overlay(self):
        """
        Repaint the overlay image with the applied offset.
        """
        if self.overlay_images is not None:
            slider_id = self.slider.value()
            if slider_id >= len(self.overlay_images):
                return

            # Only move the overlay_item if it exists
            if hasattr(self, "overlay_item") and self.overlay_item is not None:
                self.overlay_item.setPos(self.overlay_offset[0], self.overlay_offset[1])
                self.scene.update()
                if hasattr(self, "viewport"):
                    self.viewport().update()


