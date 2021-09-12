from PySide6 import QtWidgets, QtGui
from src.View.mainpage.DicomView import DicomView


class ImageFusionSagittalView(DicomView):
    def __init__(self,
                 roi_color=None,
                 iso_color=None,
                 metadata_formatted=False,
                 cut_line_color=None):
        """
        metadata_formatted: whether the metadata needs to be formatted 
        (only metadata in the four view need to be formatted)
        """
        self.slice_view = 'sagittal'
        super(ImageFusionSagittalView, self).__init__(roi_color,
                                                      iso_color,
                                                      cut_line_color)

        self.update_view()

    def image_display(self, color=False):
        """
        Update the image to be displayed on the DICOM View.
        """
        pixmaps = self.patient_dict_container.get("color_"+self.slice_view)
        slider_id = self.slider.value()
        image = pixmaps[slider_id]

        label = QtWidgets.QGraphicsPixmapItem(image)
        self.scene = QtWidgets.QGraphicsScene()
        self.scene.addItem(label)

    def value_changed(self):
        self.update_view(cut_line_color=True)

    def update_view(self, zoom_change=False, cut_line_color=False):
        """
        Update the view of the DICOM Image.
        :param zoom_change: Boolean indicating whether the user wants 
        to change the zoom. False by default.
        """
        if(cut_line_color):
            self.image_display(color=cut_line_color)
        else:
            self.image_display()

        if zoom_change:
            self.view.setTransform(
                QtGui.QTransform().scale(self.zoom, self.zoom))

        self.view.setScene(self.scene)

    def roi_display(self):
        """
        Display ROI structures on the DICOM Image.
        """
        slider_id = self.slider.value()
        curr_slice = self.patient_dict_container.get("dict_uid")[slider_id]

        selected_rois = self.patient_dict_container.get("selected_rois")
        rois = self.patient_dict_container.get("rois")
        selected_rois_name = []
        for roi in selected_rois:
            selected_rois_name.append(rois[roi]['name'])

        for roi in selected_rois:
            roi_name = rois[roi]['name']
            polygons = self.patient_dict_container.get("dict_polygons_axial")[
                roi_name][curr_slice]
            super().draw_roi_polygons(roi, polygons)
