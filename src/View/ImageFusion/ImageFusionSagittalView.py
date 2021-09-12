from PySide6 import QtWidgets
from src.View.mainpage.DicomView import DicomView, GraphicsScene


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

    def image_display(self):
        """
        Update the image to be displayed on the DICOM View.
        """
        pixmaps = self.patient_dict_container.get("color_"+self.slice_view)
        slider_id = self.slider.value()
        image = pixmaps[slider_id]

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
        for roi in selected_rois:
            selected_rois_name.append(rois[roi]['name'])

        for roi in selected_rois:
            roi_name = rois[roi]['name']
            polygons = self.patient_dict_container.get("dict_polygons_axial")[
                roi_name][curr_slice]
            super().draw_roi_polygons(roi, polygons)
