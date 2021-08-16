import math

import numpy
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtGui import QColor, QPen
from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsEllipseItem

import src.constants as constant


# noinspection PyAttributeOutsideInit


#####################################################################################################################
#                                                                                                                   #
#  This Class handles the Drawing functionality                                                                     #
#                                                                                                                   #
#####################################################################################################################
class Drawing(QtWidgets.QGraphicsScene):

    # Initialisation function  of the class
    def __init__(self, imagetoPaint, pixmapdata, min_pixel, max_pixel, dataset, draw_roi_window_instance, target_pixel_coords=set()):
        super(Drawing, self).__init__()

        # create the canvas to draw the line on and all its necessary components
        self.draw_roi_window_instance = draw_roi_window_instance
        self.min_pixel = min_pixel
        self.max_pixel = max_pixel
        self.addItem(QGraphicsPixmapItem(imagetoPaint))
        self.img = imagetoPaint
        self.data = pixmapdata
        self.values = []
        self.getValues()
        self.rect = QtCore.QRect(250, 300, 20, 20)
        self.update()
        self._points = {}
        self._circlePoints = []
        self.drag_position = QtCore.QPoint()
        self.cursor = None
        self.polygon_preview = None
        self.isPressed = False
        self.dataset = dataset
        self.pixel_array = None
        # This will contain the new pixel coordinates specifed by the min and max pixel density
        self.target_pixel_coords = target_pixel_coords
        self.according_color_dict = {}
        self.q_image = None
        self.q_pixmaps = None
        self.label = QtWidgets.QLabel()
        self.draw_tool_radius = 19
        self.is_current_pixel_coloured = False
        self._display_pixel_color()

    def _display_pixel_color(self):
        """
        Creates the initial list of pixel values within the given minimum and maximum densities, then displays them
        on the view.
        """
        if self.min_pixel <= self.max_pixel:
            data_set = self.dataset
            if hasattr(self.draw_roi_window_instance, 'bounds_box_draw'):
                print(self.draw_roi_window_instance.bounds_box_draw)
                self.min_x = int(self.draw_roi_window_instance.bounds_box_draw.box.rect().x())
                self.min_y = int(self.draw_roi_window_instance.bounds_box_draw.box.rect().y())
                self.max_x = int(self.draw_roi_window_instance.bounds_box_draw.box.rect().width() + self.min_x)
                self.max_y = int(self.draw_roi_window_instance.bounds_box_draw.box.rect().height() + self.min_y)
            else:
                self.min_x = 0
                self.min_y = 0
                self.max_x = data_set.Rows
                self.max_y = data_set.Columns

            """
            pixel_array is a 2-Dimensional array containing all pixel coordinates of the q_image. 
            pixel_array[x][y] will return the density of the pixel
            """
            self.pixel_array = data_set._pixel_array
            self.q_image = self.img.toImage()
            for y_coord in range(self.min_y, self.max_y):
                for x_coord in range(self.min_x, self.max_x):

                    if (self.pixel_array[y_coord][x_coord] >= self.min_pixel) and (
                            self.pixel_array[y_coord][x_coord] <= self.max_pixel):
                        self.target_pixel_coords.add((x_coord, y_coord))

            """
            For the meantime, a new image is created and the pixels specified are coloured. 
            This will need to altered so that it creates a new layer over the existing image instead of replacing it.
            """
            # Convert QPixMap into Qimage
            for x_coord, y_coord in self.target_pixel_coords:
                c = self.q_image.pixel(x_coord, y_coord)
                colors = QColor(c).getRgbF()
                self.according_color_dict[(x_coord, y_coord)] = colors
            color = QtGui.QColor()
            color.setRgb(90, 250, 175, 200)
            for x_coord, y_coord in self.according_color_dict:
                self.q_image.setPixelColor(x_coord, y_coord, color)

            self.refresh_image()

    def _find_neighbor_point(self, event):
        """
        Find point around mouse position. This function is for if we want to choose and drag the circle
        :rtype: ((int, int)|None)
        :return: (x, y) if there are any point around mouse else None
        """
        distance_threshold = 3.0
        nearest_point = None
        min_distance = math.sqrt(2 * (100 ** 2))
        for x, y in self._points.items():
            distance = math.hypot(event.xdata - x, event.ydata - y)
            if distance < min_distance:
                min_distance = distance
                nearest_point = (x, y)
        if min_distance < distance_threshold:
            return nearest_point
        return None

    def getValues(self):
        """
        This function gets the corresponding values of all the points in the drawn line from the dataset.
        """
        for i in range(constant.DEFAULT_WINDOW_SIZE):
            for j in range(constant.DEFAULT_WINDOW_SIZE):
                self.values.append(self.data[i][j])

    def refresh_image(self):
        """
        Convert QImage containing modified CT slice with highlighted pixels into a QPixmap, and then display it onto
        the view.
        """
        self.q_pixmaps = QtWidgets.QGraphicsPixmapItem(QtGui.QPixmap.fromImage(self.q_image))
        self.addItem(self.q_pixmaps)

    def remove_pixels_within_circle(self, clicked_x, clicked_y):
        """
        Removes all highlighted pixels within the selected circle and updates the image.
        """
        # Calculate euclidean distance between each highlighted point and the clicked point. If the distance is less
        # than the radius, remove it from the highlighted pixels.

        according_color_dict_key_list = list(self.according_color_dict.keys())

        color_to_draw = QtGui.QColor()
        color_to_draw.setRgb(90, 250, 175, 200)

        for x, y in according_color_dict_key_list:
            colors = self.according_color_dict[(x, y)]
            clicked_point = numpy.array((clicked_x, clicked_y))
            point_to_check = numpy.array((x, y))
            distance = numpy.linalg.norm(clicked_point - point_to_check)
            if distance <= self.draw_tool_radius:
                self.q_image.setPixelColor(x, y, QColor.fromRgbF(colors[0], colors[1], colors[2], colors[3]))
                self.target_pixel_coords.remove((x, y))
                self.according_color_dict.pop((x, y))

        self.refresh_image()

    def fill_pixels_within_circle(self, clicked_x, clicked_y):
        """
        Add all highlighted pixels within the selected circle and updates the image.
        """
        # Calculate euclidean distance between each highlighted point and the clicked point. If the distance is less
        # than the radius, add it to the highlighted pixels.

        # Set of points to color
        points_to_color = set()

        min_y_bound_square = math.floor(clicked_y) - self.draw_tool_radius
        min_x_bound_square = math.floor(clicked_x) - self.draw_tool_radius
        max_y_bound_square = math.floor(clicked_y) + self.draw_tool_radius
        max_x_bound_square = math.floor(clicked_x) + self.draw_tool_radius
        for y_coord in range(max(self.min_y, min_y_bound_square), min(self.max_y, max_y_bound_square)):
            for x_coord in range(max(self.min_x, min_x_bound_square), min(self.max_x, max_x_bound_square)):
                clicked_point = numpy.array((clicked_x, clicked_y))
                point_to_check = numpy.array((x_coord, y_coord))
                distance = numpy.linalg.norm(clicked_point - point_to_check)
                if (self.pixel_array[y_coord][x_coord] >= self.min_pixel) and (
                        self.pixel_array[y_coord][x_coord] <= self.max_pixel) and (distance <= self.draw_tool_radius):
                    c = self.q_image.pixel(x_coord, y_coord)
                    colors = QColor(c)
                    if (x_coord, y_coord) not in self.according_color_dict:
                        self.according_color_dict[(x_coord, y_coord)] = colors.getRgbF()
                        points_to_color.add((x_coord, y_coord))
                        self.target_pixel_coords.add((x_coord, y_coord))

        # Color to draw
        color_to_draw = QtGui.QColor()
        color_to_draw.setRgb(90, 250, 175, 200)

        for x_coord, y_coord in points_to_color:
            self.q_image.setPixelColor(x_coord, y_coord, color_to_draw)
        self.refresh_image()

    def draw_cursor(self, event_x, event_y, new_circle=False):
        """
        Draws a blue circle where the user clicked.
        :param event_x: QGraphicsScene event attribute: event.scenePos().x()
        :param event_y: QGraphicsScene event attribute: event.scenePos().y()
        :param new_circle: True when the circle object is being created rather than updated.
        """
        self.current_cursor_x = event_x - self.draw_tool_radius
        self.current_cursor_y = event_y - self.draw_tool_radius
        if new_circle:
            self.cursor = QGraphicsEllipseItem(self.current_cursor_x, self.current_cursor_y, self.draw_tool_radius * 2,
                                               self.draw_tool_radius * 2)
            pen = QPen(QColor("blue"))
            pen.setWidth(0)
            self.cursor.setPen(pen)
            self.cursor.setZValue(1)
            self.addItem(self.cursor)
        elif self.cursor is not None:
            self.cursor.setRect(self.current_cursor_x, self.current_cursor_y, self.draw_tool_radius * 2,
                                self.draw_tool_radius * 2)

    def draw_contour_preview(self, list_of_points):
        """
        Draws a polygon onto the view so the user can preview what their contour will look like once exported.
        :param list_of_points: A list of points ordered to form a polygon.
        """
        qpoint_list = []
        for point in list_of_points:
            qpoint = QtCore.QPoint(point[0], point[1])
            qpoint_list.append(qpoint)
        if self.polygon_preview is not None:  # Erase the existing preview
            self.removeItem(self.polygon_preview)
        polygon = QtGui.QPolygonF(qpoint_list)
        self.polygon_preview = QtWidgets.QGraphicsPolygonItem(polygon)
        pen = QtGui.QPen(QtGui.QColor("yellow"))
        pen.setStyle(QtCore.Qt.DashDotDotLine)
        self.polygon_preview.setPen(pen)
        self.addItem(self.polygon_preview)

    def mousePressEvent(self, event):
        if self.cursor:
            self.removeItem(self.cursor)
        self.isPressed = True
        if (
                2 * QtGui.QVector2D(event.pos() - self.rect.center()).length()
                < self.rect.width()
        ):
            self.drag_position = event.pos() - self.rect.topLeft()
        super().mousePressEvent(event)
        self.is_current_pixel_coloured = (math.floor(event.scenePos().x()),
                                          math.floor(
                                              event.scenePos().y())) in self.according_color_dict
        self.draw_cursor(event.scenePos().x(), event.scenePos().y(), new_circle=True)

        if self.is_current_pixel_coloured:
            self.fill_pixels_within_circle(event.scenePos().x(), event.scenePos().y())
        else:
            self.remove_pixels_within_circle(event.scenePos().x(), event.scenePos().y())
        self.update()

    def mouseMoveEvent(self, event):
        if not self.drag_position.isNull():
            self.rect.moveTopLeft(event.pos() - self.drag_position)
        super().mouseMoveEvent(event)
        if self.cursor and self.isPressed:
            self.draw_cursor(event.scenePos().x(), event.scenePos().y())
            if self.is_current_pixel_coloured:
                self.fill_pixels_within_circle(event.scenePos().x(), event.scenePos().y())
            else:
                self.remove_pixels_within_circle(event.scenePos().x(), event.scenePos().y())
        self.update()

    def mouseReleaseEvent(self, event):
        self.isPressed = False
        self.drag_position = QtCore.QPoint()
        super().mouseReleaseEvent(event)
        self.update()
