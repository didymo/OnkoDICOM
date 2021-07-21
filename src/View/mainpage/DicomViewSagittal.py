from PySide6 import QtGui, QtCore

from src.Controller.PathHandler import resource_path
from src.Model.ROI import get_contour_pixel_sagittal, get_roi_contour_pixel
from src.View.mainpage.DicomView import DicomView


class DicomViewSagittal(DicomView):
    def __init__(self, roi_color=None, iso_color=None):
        self.slice_view = 'sagittal'
        super(DicomViewSagittal, self).__init__(roi_color, iso_color)
        self.update_view()

    def roi_display(self):
        maxVal = self.slider.maximum()
        slider_id = self.slider.value()
        # curr_slice = self.patient_dict_container.get("dict_uid")
        aspect = self.patient_dict_container.get("aspect")["sagittal"]
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
                polygons = self.calc_roi_polygon(roi_name, slider_id, dict_rois_contours, aspect)
                new_dict_polygons[roi_name][slider_id] = polygons
                self.patient_dict_container.set("dict_polygons_sagittal", new_dict_polygons)

            elif self.patient_dict_container.get("dict_polygons_sagittal")[roi_name] is None:
                pass
            elif slider_id not in self.patient_dict_container.get("dict_polygons_sagittal")[roi_name].keys():
                new_dict_polygons = self.patient_dict_container.get("dict_polygons_sagittal")
                all_roi_contour = get_roi_contour_pixel(self.patient_dict_container.get("raw_contour"),
                                                        selected_rois_name, self.patient_dict_container.get("pixluts"))
                slice_ids = dict((v, k) for k, v in self.patient_dict_container.get("dict_uid").items())
                dict_rois_contours = self.get_dict_roi_contours(all_roi_contour, slice_ids)
                polygons = self.calc_roi_polygon(roi_name, slider_id, dict_rois_contours, aspect)
                new_dict_polygons[roi_name][slider_id] = polygons
                self.patient_dict_container.set("dict_polygons_sagittal", new_dict_polygons)

            else:
                polygons = self.patient_dict_container.get("dict_polygons_sagittal")[roi_name][slider_id]

            if polygons is not None:
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
                self.scene.addPolygon(polygons, pen, QtGui.QBrush(color))

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
                            new_list[name][contour[i][0]].append([contour[i][1], slice_ids[slice]])
                        else:
                            new_list[name][contour[i][0]] = []
                            new_list[name][contour[i][0]].append([contour[i][1], slice_ids[slice]])
        return new_list

    def calc_roi_polygon(self, curr_roi, curr_slice, dict_rois_contours, aspect):
        """
        Calculate a list of polygons to display for a given ROI and a given slice.
        :param curr_roi:
         the ROI structure
        :param curr_slice:
         the current slice
        :return: List of polygons of type QPolygonF.
        """
        # TODO Implement support for showing "holes" in contours.
        # Possible process for this is:
        # 1. Calculate the areas of each contour on the slice
        # https://stackoverflow.com/questions/24467972/calculate-area-of-polygon-given-x-y-coordinates
        # 2. Compare each contour to the largest contour by area to determine if it is contained entirely within the
        # largest contour.
        # https://stackoverflow.com/questions/4833802/check-if-polygon-is-inside-a-polygon
        # 3. If the polygon is contained, use QPolygonF.subtracted(QPolygonF) to subtract the smaller "hole" polygon
        # from the largest polygon, and then remove the polygon from the list of polygons to be displayed.
        # This process should provide fast and reliable results, however it should be noted that this method may fall
        # apart in a situation where there are multiple "large" polygons, each with their own hole in it. An appropriate
        # solution to that may be to compare every contour against one another and determine which ones have holes
        # encompassed entirely by them, and then subtract each hole from the larger polygon and delete the smaller
        # holes. This second solution would definitely lead to more accurate representation of contours, but could
        # possibly be too slow to be viable.

        list_polygons = []
        if curr_slice in dict_rois_contours[curr_roi]:
            pixel_list = dict_rois_contours[curr_roi][curr_slice]
            list_qpoints = []
            for i in range(len(pixel_list)):
                curr_qpoint = QtCore.QPoint(pixel_list[i][0], pixel_list[i][1]/aspect)
                list_qpoints.append(curr_qpoint)
            curr_polygon = QtGui.QPolygonF(list_qpoints)
            return curr_polygon
        else:
            return None
