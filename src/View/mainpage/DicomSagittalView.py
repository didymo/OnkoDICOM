from PySide6 import QtGui

from src.Controller.PathHandler import resource_path
from src.Model.ROI import get_roi_contour_pixel, calc_roi_polygon
from src.View.mainpage.DicomView import DicomView


class DicomSagittalView(DicomView):
    def __init__(self, roi_color=None, iso_color=None):
        self.slice_view = 'sagittal'
        super(DicomSagittalView, self).__init__(roi_color, iso_color)
        self.update_view()

    def roi_display(self):
        slider_id = self.slider.value()
        aspect = self.patient_dict_container.get("pixmap_aspect")["sagittal"]
        selected_rois = self.patient_dict_container.get("selected_rois")
        rois = self.patient_dict_container.get("rois")
        selected_rois_name = []
        for roi in selected_rois:
            selected_rois_name.append(rois[roi]['name'])

        for roi in selected_rois:
            roi_name = rois[roi]['name']

            if roi_name not in self.patient_dict_container.get("dict_polygons_sagittal").keys():
                new_dict_polygons = self.patient_dict_container.get("dict_polygons_sagittal")
                new_dict_polygons[roi_name] = {}
                all_roi_contour = get_roi_contour_pixel(self.patient_dict_container.get("raw_contour"),
                                                        selected_rois_name, self.patient_dict_container.get("pixluts"))
                slice_ids = dict((v, k) for k, v in self.patient_dict_container.get("dict_uid").items())
                dict_rois_contours = self.get_dict_roi_contours(all_roi_contour, slice_ids)
                polygons = calc_roi_polygon(roi_name, slider_id, dict_rois_contours, 1 / aspect)
                new_dict_polygons[roi_name][slider_id] = polygons
                self.patient_dict_container.set("dict_polygons_sagittal", new_dict_polygons)

            elif self.patient_dict_container.get("dict_polygons_sagittal")[roi_name] is None:
                continue
            elif slider_id not in self.patient_dict_container.get("dict_polygons_sagittal")[roi_name].keys():
                new_dict_polygons = self.patient_dict_container.get("dict_polygons_sagittal")
                all_roi_contour = get_roi_contour_pixel(self.patient_dict_container.get("raw_contour"),
                                                        selected_rois_name, self.patient_dict_container.get("pixluts"))
                slice_ids = dict((v, k) for k, v in self.patient_dict_container.get("dict_uid").items())
                dict_rois_contours = self.get_dict_roi_contours(all_roi_contour, slice_ids)
                polygons = calc_roi_polygon(roi_name, slider_id, dict_rois_contours, 1 / aspect)
                new_dict_polygons[roi_name][slider_id] = polygons
                self.patient_dict_container.set("dict_polygons_sagittal", new_dict_polygons)
            else:
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

    def get_dict_roi_contours(self, all_roi_contour, slice_ids):
        new_list = {}
        for name in all_roi_contour.keys():
            new_list[name] = {}
            for slice in slice_ids.keys():
                contours = all_roi_contour[name][slice]
                for contour in contours:
                    for i in range(len(contour)):
                        if contour[i][0] in new_list[name]:
                            new_list[name][contour[i][0]][0].append([contour[i][1], slice_ids[slice]])
                        else:
                            new_list[name][contour[i][0]] = [[]]
                            new_list[name][contour[i][0]][0].append([contour[i][1], slice_ids[slice]])
        return new_list
