from PySide6 import QtGui

from src.Controller.PathHandler import resource_path
from src.View.mainpage.DicomView import DicomView


class DicomSagittalView(DicomView):
    def __init__(self, roi_color=None, iso_color=None):
        self.slice_view = 'sagittal'
        super(DicomSagittalView, self).__init__(roi_color, iso_color)
        self.update_view()

    def roi_display(self):
        slider_id = self.slider.value()
        selected_rois = self.patient_dict_container.get("selected_rois")
        rois = self.patient_dict_container.get("rois")
        selected_rois_name = []
        for roi in selected_rois:
            selected_rois_name.append(rois[roi]['name'])

        for roi in selected_rois:
            roi_name = rois[roi]['name']
            polygons = self.patient_dict_container.get("dict_polygons_sagittal")[roi_name][slider_id]

            color = self.patient_dict_container.get("roi_color_dict")[roi]
            with open(resource_path('data/line&fill_configuration'), 'r') as stream:
                elements = stream.readlines()
                if len(elements) > 0:
                    roi_line = int(elements[0].replace('\n', ''))
                    roi_opacity = int(elements[1].replace('\n', ''))
                    line_width = float(elements[4].replace('\n', ''))
                else:
                    roi_line = 1
                    roi_opacity = 10
                    line_width = 2.0
                stream.close()
            roi_opacity = int((roi_opacity / 100) * 255)

            color.setAlpha(roi_opacity)
            pen = self.get_qpen(color, roi_line, line_width)
            for i in range(len(polygons)):
                self.scene.addPolygon(polygons[i], pen, QtGui.QBrush(color))

    def isodose_display(self):
        print(self.slice_view)
