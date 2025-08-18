from PySide6 import QtWidgets
from src.View.mainpage.DicomView import DicomView, GraphicsScene
from src.View.ImageFusion.TranslateRotateMenu import TranslateRotateMenu


class BaseFusionView(DicomView):
    def __init__(self, slice_view, roi_color=None, iso_color=None, cut_line_color=None):
        self.slice_view = slice_view

        self.translation_menu = TranslateRotateMenu()
        self.translation_menu.set_offset_changed_callback(self.update_overlay_offset)
        super().__init__(roi_color, iso_color, cut_line_color)
        self.update_view()

    def image_display(self, overlay_image=None):
        """
            Update the image to be displayed on the DICOM View.
            If overlay_image is provided, use it as the overlay for this view.
            """

        slider_id = self.slider.value()

        if overlay_image is not None:
            image = overlay_image
        elif hasattr(self, "overlay_images"):
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

        label = QtWidgets.QGraphicsPixmapItem(image)
        self.scene = GraphicsScene(label, self.horizontal_view, self.vertical_view)

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
        if hasattr(self, "overlay_images"):
            slider_id = self.slider.value()
            if slider_id >= len(self.overlay_images):
                return
            image = self.overlay_images[slider_id]

            if hasattr(self, "overlay_item"):
                # just update position
                self.overlay_item.setPos(self.overlay_offset[0], self.overlay_offset[1])
            else:
                # first-time creation
                self.overlay_item = QtWidgets.QGraphicsPixmapItem(image)
                self.overlay_item.setPos(self.overlay_offset[0], self.overlay_offset[1])
                self.scene.addItem(self.overlay_item)