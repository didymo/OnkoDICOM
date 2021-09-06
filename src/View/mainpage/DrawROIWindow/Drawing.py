import math

import numpy
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtGui import QColor, QPen
from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsEllipseItem

import src.constants as constant
from src.constants import DEFAULT_WINDOW_SIZE


# noinspection PyAttributeOutsideInit

class Drawing(QtWidgets.QGraphicsScene):
    """
        Class responsible for the ROI drawing functionality
        """

    # Initialisation function  of the class
    def __init__(self, imagetoPaint, pixmapdata, min_pixel, max_pixel, dataset,
                 draw_roi_window_instance, slice_changed,
                 current_slice, drawing_tool_radius, keep_empty_pixel,
                 target_pixel_coords=set()):
        super(Drawing, self).__init__()

        # create the canvas to draw the line on and all its necessary
        # components
        self.dataset = dataset
        self.different_sizes = (dataset['Rows'].value != DEFAULT_WINDOW_SIZE)
        self.rows = dataset['Rows'].value
        self.cols = dataset['Columns'].value
        self.draw_roi_window_instance = draw_roi_window_instance
        self.slice_changed = slice_changed
        self.current_slice = current_slice
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
        self.pixel_array = None
        # This will contain the new pixel coordinates specifed by the min
        # and max pixel density
        self.target_pixel_coords = target_pixel_coords
        self.according_color_dict = {}
        self.q_image = None
        self.q_pixmaps = None
        self.label = QtWidgets.QLabel()
        self.draw_tool_radius = drawing_tool_radius
        self.is_current_pixel_coloured = False
        self.keep_empty_pixel = keep_empty_pixel
        self._display_pixel_color()


    def _display_pixel_color(self):
        """
        Creates the initial list of pixel values within the given minimum
        and maximum densities, then displays them on the view.
        """
        if self.min_pixel <= self.max_pixel:
            data_set = self.dataset
            if hasattr(self.draw_roi_window_instance, 'bounds_box_draw'):
                bound_box = \
                    self.draw_roi_window_instance.bounds_box_draw.box.rect()
                self.min_x, self.min_y = linear_transform(
                    bound_box.x(), bound_box.y(),
                    self.rows, self.cols
                )
                self.max_x, self.max_y = linear_transform(
                    bound_box.width(), bound_box.height(),
                    self.rows, self.cols
                )
                self.max_x += self.min_x
                self.max_y += self.min_y
            else:
                self.min_x = 0
                self.min_y = 0
                self.max_x = data_set.Rows
                self.max_y = data_set.Columns

            """pixel_array is a 2-Dimensional array containing all pixel 
            coordinates of the q_image. pixel_array[x][y] will return the 
            density of the pixel """
            self.pixel_array = data_set._pixel_array
            self.q_image = self.img.toImage()
            for y_coord in range(self.min_y, self.max_y):
                for x_coord in range(self.min_x, self.max_x):
                    if (self.pixel_array[y_coord][x_coord] >= self.min_pixel) \
                            and (self.pixel_array[y_coord][
                                     x_coord] <= self.max_pixel):
                        self.target_pixel_coords.add((x_coord, y_coord))

            """For the meantime, a new image is created and the pixels 
            specified are coloured. This will need to altered so that it 
            creates a new layer over the existing image instead of replacing 
            it. """
            # Convert QPixMap into Qimage
            for x_coord, y_coord in self.target_pixel_coords:
                if self.different_sizes:
                    x_colour, y_colour = inv_linear_transform(
                        x_coord, y_coord, self.rows, self.cols)
                    c = self.q_image.pixel(x_colour[0], y_colour[0])
                else:
                    c = self.q_image.pixel(x_coord, y_coord)
                colors = QColor(c).getRgbF()
                self.according_color_dict[(x_coord, y_coord)] = colors
            color = QtGui.QColor()
            color.setRgb(90, 250, 175, 200)
            for x_coord, y_coord in self.according_color_dict:
                if self.different_sizes:
                    x_arr, y_arr = inv_linear_transform(
                        x_coord, y_coord, self.rows, self.cols)
                    for x in x_arr:
                        for y in y_arr:
                            self.q_image.setPixelColor(x, y, color)
                else:
                    self.q_image.setPixelColor(x_coord, y_coord, color)

            self.refresh_image()

    def _find_neighbor_point(self, event):
        """
        Find point around mouse position. This function is for if we want to
        choose and drag the circle :rtype: ((int, int)|None) :param event:
        the mouse event :return: (x, y) if there are any point around mouse
        else None
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
        This function gets the corresponding values of all the points in the
        drawn line from the dataset.
        """
        for i in range(DEFAULT_WINDOW_SIZE):
            for j in range(DEFAULT_WINDOW_SIZE):
                x, y = linear_transform(
                    i, j, self.rows, self.cols)
                self.values.append(self.data[x][y])

    def refresh_image(self):
        """
        Convert QImage containing modified CT slice with highlighted pixels
        into a QPixmap, and then display it onto the view.
        """
        self.q_pixmaps = QtWidgets.QGraphicsPixmapItem(
            QtGui.QPixmap.fromImage(self.q_image))
        self.addItem(self.q_pixmaps)

    def remove_pixels_within_circle(self, clicked_x, clicked_y):
        """
        Removes all highlighted pixels within the selected circle and
        updates the image. :param clicked_x: the current x coordinate :param
        clicked_y: the current y coordinate
        """
        # Calculate euclidean distance between each highlighted point and
        # the clicked point. If the distance is less than the radius,
        # remove it from the highlighted pixels.

        # The roi drawn on current slice is changed after several pixels are
        # modified
        self.slice_changed = True
        clicked_x, clicked_y = linear_transform(
            clicked_x, clicked_y, self.rows, self.cols)
        according_color_dict_key_list = list(self.according_color_dict.keys())

        color_to_draw = QtGui.QColor()
        color_to_draw.setRgb(90, 250, 175, 200)

        for x, y in according_color_dict_key_list:
            colors = self.according_color_dict[(x, y)]
            clicked_point = numpy.array((clicked_x, clicked_y))
            point_to_check = numpy.array((x, y))
            distance = numpy.linalg.norm(clicked_point - point_to_check)
            if distance <= self.draw_tool_radius * (
                    float(self.rows) / DEFAULT_WINDOW_SIZE):
                if self.different_sizes:
                    x_arr, y_arr = inv_linear_transform(
                        x, y, self.rows, self.cols)
                    for x_t in x_arr:
                        for y_t in y_arr:
                            self.q_image.setPixelColor(x_t, y_t,
                                                   QColor.fromRgbF(colors[0],
                                                                   colors[1],
                                                                   colors[2],
                                                                   colors[3]))
                else:
                    self.q_image.setPixelColor(x, y,
                                               QColor.fromRgbF(colors[0],
                                                               colors[1],
                                                               colors[2],
                                                               colors[3]))

                self.target_pixel_coords.remove((x, y))
                self.according_color_dict.pop((x, y))
                # The roi drawn on current slice is changed after several
                # pixels are modified
                self.slice_changed = True

        self.refresh_image()

    def fill_pixels_within_circle(self, clicked_x, clicked_y):
        """
        Add all highlighted pixels within the selected circle and updates
        the image. :param clicked_x: the current x coordinate :param
        clicked_y: the current y coordinate
        """
        # Calculate euclidean distance between each highlighted point and
        # the clicked point. If the distance is less than the radius,
        # add it to the highlighted pixels.

        # Set of points to color
        points_to_color = set()

        # The roi drawn on current slice is changed after several pixels are
        # modified
        self.slice_changed = True
        clicked_x, clicked_y = linear_transform(
            clicked_x, clicked_y, self.rows, self.cols)
        scaled_tool_radius = int(self.draw_tool_radius * (
                    float(self.rows) / DEFAULT_WINDOW_SIZE))

        min_y_bound_square = math.floor(clicked_y) - scaled_tool_radius
        min_x_bound_square = math.floor(clicked_x) - scaled_tool_radius
        max_y_bound_square = math.floor(clicked_y) + scaled_tool_radius
        max_x_bound_square = math.floor(clicked_x) + scaled_tool_radius
        for y_coord in range(
                max(self.min_y, min_y_bound_square),
                min(self.max_y, max_y_bound_square)):
            for x_coord in range(
                    max(self.min_x, min_x_bound_square),
                    min(self.max_x, max_x_bound_square)):
                clicked_point = numpy.array((clicked_x, clicked_y))
                point_to_check = numpy.array((x_coord, y_coord))
                distance = numpy.linalg.norm(clicked_point - point_to_check)

                if (self.keep_empty_pixel or
                    self.min_pixel <= self.pixel_array[y_coord][
                        x_coord] <= self.max_pixel) \
                        and distance <= scaled_tool_radius:
                    if self.different_sizes:
                        x_colour, y_colour = inv_linear_transform(
                            x_coord, y_coord,
                            self.rows, self.cols)
                        c = self.q_image.pixel(x_colour[0], y_colour[0])
                    else:
                        c = self.q_image.pixel(x_coord, y_coord)
                    colors = QColor(c)
                    if (x_coord, y_coord) not in self.according_color_dict:
                        self.according_color_dict[
                            (x_coord, y_coord)] = colors.getRgbF()
                        points_to_color.add((x_coord, y_coord))
                        self.target_pixel_coords.add((x_coord, y_coord))

        # Color to draw
        color_to_draw = QtGui.QColor()
        color_to_draw.setRgb(90, 250, 175, 200)

        for x_coord, y_coord in points_to_color:
            if self.different_sizes:
                x_arr, y_arr = inv_linear_transform(
                    x_coord, y_coord, self.rows, self.cols)
                for x in x_arr:
                    for y in y_arr:
                        self.q_image.setPixelColor(x, y, color_to_draw)
            else:
                self.q_image.setPixelColor(x_coord, y_coord, color_to_draw)
        self.refresh_image()

    def clear_cursor(self, drawing_tool_radius):
        """
        Clean the current cursor
        :param drawing_tool_radius: the current radius of the drawing tool
        """
        self.draw_tool_radius = drawing_tool_radius
        if self.cursor:
            self.removeItem(self.cursor)
            self.cursor = False

    def draw_cursor(self, event_x, event_y, drawing_tool_radius,
                    new_circle=False):
        """
        Draws a blue circle where the user clicked. :param event_x:
        QGraphicsScene event attribute: event.scenePos().x() :param event_y:
        QGraphicsScene event attribute: event.scenePos().y() :param
        drawing_tool_radius: the current radius of the drawing tool :param
        new_circle: True when the circle object is being created rather than
        updated.
        """
        self.draw_tool_radius = drawing_tool_radius
        self.current_cursor_x = event_x - self.draw_tool_radius
        self.current_cursor_y = event_y - self.draw_tool_radius
        if new_circle:
            self.cursor = QGraphicsEllipseItem(self.current_cursor_x,
                                               self.current_cursor_y,
                                               self.draw_tool_radius * 2,
                                               self.draw_tool_radius * 2)
            pen = QPen(QColor("blue"))
            pen.setWidth(0)
            self.cursor.setPen(pen)
            self.cursor.setZValue(1)
            self.addItem(self.cursor)
        elif self.cursor is not None:
            self.cursor.setRect(self.current_cursor_x, self.current_cursor_y,
                                self.draw_tool_radius * 2,
                                self.draw_tool_radius * 2)

    def draw_contour_preview(self, list_of_points):
        """
        Draws a polygon onto the view so the user can preview what their
        contour will look like once exported. :param list_of_points: A list
        of points ordered to form a polygon.
        """
        qpoint_list = []
        for point in list_of_points:
            if self.different_sizes:
                x_arr, y_arr = inv_linear_transform(
                    point[0], point[1], self.rows, self.cols)
                for x in x_arr:
                    for y in y_arr:
                        qpoint = QtCore.QPoint(x, y)
                        qpoint_list.append(qpoint)
            else:
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
        """
            This method is called to handle a mouse press event
            :param event: the mouse event
        """
        if self.cursor:
            self.removeItem(self.cursor)
        self.isPressed = True
        if (
                2 * QtGui.QVector2D(event.pos() - self.rect.center()).length()
                < self.rect.width()
        ):
            self.drag_position = event.pos() - self.rect.topLeft()
        super().mousePressEvent(event)
        x, y = linear_transform(
            math.floor(event.scenePos().x()), math.floor(event.scenePos().y()),
            self.rows, self.cols)
        is_coloured = (x, y) in self.according_color_dict
        self.is_current_pixel_coloured = is_coloured
        self.draw_cursor(event.scenePos().x(), event.scenePos().y(),
                         self.draw_tool_radius, new_circle=True)

        if not self.is_current_pixel_coloured:
            self.fill_pixels_within_circle(event.scenePos().x(),
                                           event.scenePos().y())
        else:
            self.remove_pixels_within_circle(event.scenePos().x(),
                                             event.scenePos().y())
        self.update()

    def mouseMoveEvent(self, event):
        """
            This method is called to handle a mouse move event
            :param event: the mouse event
        """
        if not self.drag_position.isNull():
            self.rect.moveTopLeft(event.pos() - self.drag_position)
        super().mouseMoveEvent(event)
        if self.cursor and self.isPressed:
            self.draw_cursor(event.scenePos().x(), event.scenePos().y(),
                             self.draw_tool_radius)
            if not self.is_current_pixel_coloured:
                self.fill_pixels_within_circle(event.scenePos().x(),
                                               event.scenePos().y())
            else:
                self.remove_pixels_within_circle(event.scenePos().x(),
                                                 event.scenePos().y())
        self.update()

    def mouseReleaseEvent(self, event):
        """
            This method is called to handle a mouse release event
            :param event: the mouse event
        """
        self.isPressed = False
        self.drag_position = QtCore.QPoint()
        super().mouseReleaseEvent(event)
        self.update()


# These functions scale window input to Image Size
def linear_transform(x, y, m1, m2):
    m_x = float(m1) / constant.DEFAULT_WINDOW_SIZE
    m_y = float(m2) / constant.DEFAULT_WINDOW_SIZE
    return int(m_x * x), int(m_y * y)


def inv_linear_transform(x, y, m1, m2):
    m_x = float(constant.DEFAULT_WINDOW_SIZE) / m1
    m_y = float(constant.DEFAULT_WINDOW_SIZE) / m2
    x_min = int(m_x * x)
    x_max = int(m_x * (x + 1))
    y_min = int(m_y * y)
    y_max = int(m_y * (y + 1))
    return numpy.arange(x_min, x_max), numpy.arange(y_min, y_max)
