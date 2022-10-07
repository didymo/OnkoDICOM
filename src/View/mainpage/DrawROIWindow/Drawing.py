import math
import numpy
import logging
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtGui import QColor, QPen
from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsEllipseItem
from PySide6.QtCore import Slot

from src.constants import DEFAULT_WINDOW_SIZE
from src.Model.Transform import linear_transform, get_pixel_coords, \
    get_first_entry, inv_linear_transform


class Drawing(QtWidgets.QGraphicsScene):
    """
        Class responsible for the ROI drawing functionality
        """

    # Initialisation function  of the class
    def __init__(self, imagetoPaint, pixmapdata, min_pixel, max_pixel, dataset,
                 draw_roi_window_instance, slice_changed,
                 current_slice, drawing_tool_radius, keep_empty_pixel, pixel_transparency,
                 target_pixel_coords=set()):
        super(Drawing, self).__init__()

        # create the canvas to draw the line on and all its necessary
        # components
        self.dataset = dataset
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
        self.polygon_preview = []
        self.isPressed = False
        self.pixel_array = None
        self.pen = QtGui.QPen(QtGui.QColor("yellow"))
        self.pen.setStyle(QtCore.Qt.DashDotDotLine)
        # This will contain the new pixel coordinates specified by the min
        # and max pixel density
        self.target_pixel_coords = target_pixel_coords
        self.according_color_dict = {}
        self.q_image = None
        self.q_pixmaps = None
        self.label = QtWidgets.QLabel()
        self.draw_tool_radius = drawing_tool_radius
        self.is_current_pixel_coloured = False
        self.keep_empty_pixel = keep_empty_pixel
        self.pixel_transparency = pixel_transparency
        self.drawn_pixel_color = QtGui.QColor(255, 0, 0, 255)
        self.min_bounds_x = 0
        self.min_bounds_y = 0
        self.max_bounds_x = self.rows
        self.max_bounds_y = self.cols
        self.fill_source = None
        self.is_drawing = False

    def set_bounds(self):
        """
        Sets the custom bounds based on the bounds_box_draw instance
        """
        if hasattr(self.draw_roi_window_instance, 'bounds_box_draw'):
            bound_box = \
                self.draw_roi_window_instance.bounds_box_draw.box.rect()
            self.min_bounds_x, self.min_bounds_y = linear_transform(
                bound_box.x(), bound_box.y(),
                self.rows, self.cols
            )
            self.max_bounds_x, self.max_bounds_y = linear_transform(
                bound_box.width(), bound_box.height(),
                self.rows, self.cols
            )
            self.max_bounds_x += self.min_bounds_x
            self.max_bounds_y += self.min_bounds_y
        else:
            self.min_bounds_x = 0
            self.min_bounds_y = 0
            self.max_bounds_x = self.rows
            self.max_bounds_y = self.cols

    def _display_pixel_color(self):
        """
        Finds the pixel coordinates used to draw the ROI based on the min and max values.
        This process uses a generic BFS that is bound to the min and max bounds,
        as well as the min and max pixel density.
        """
        self.set_bounds()
        self.pixel_array = self.dataset._pixel_array

        self.q_image = self.img.toImage()
        queue = [self.fill_source]

        while len(queue) > 0:
            current = queue.pop(0)

            for x_neighbour in range(-1, 2):
                for y_neighbour in range(-1, 2):
                    element = [current[0] + x_neighbour, current[1] + y_neighbour]

                    if self.check_roi_validity(element):
                        if (element[0], element[1]) not in self.target_pixel_coords:
                            queue.append([element[0], element[1]])
                            self.target_pixel_coords.add((element[0], element[1]))

        """
        For the meantime, a new image is created and the pixels 
        specified are coloured. The _set_colour_of_pixels function
         is then called to colour the newly drawn pixels and blend in
         transparency.
         """
        # Convert QPixMap into Qimage
        for x_coord, y_coord in self.target_pixel_coords:
            temp = set()
            temp.add((x_coord, y_coord))
            points = get_pixel_coords(temp, self.rows, self.cols)
            temp_2 = get_first_entry(points)
            c = self.q_image.pixel(temp_2[0], temp_2[1])
            colors = QColor(c).getRgbF()
            self.according_color_dict[(x_coord, y_coord)] = colors

        points = get_pixel_coords(self.according_color_dict, self.rows, self.cols)
        self._set_color_of_pixels(points)
        self.refresh_image()

    def _set_color_of_pixels(self, points):
        """
        Takes a set of points that need to be coloured, and updates the colour of
        each pixel with the drawn on colour, blended together based on the transparency value.

        :param points:  Set of x and y co-ordinates of pixels to be coloured
        """
        logging.debug("_set_color_of_pixels started")
        img = self.img.toImage()
        for x_coord, y_coord in points:
            old_color = img.pixelColor(x_coord, y_coord)
            # Blend the individual RGB values of the original pixel with the drawn ROI colour values
            new_color = QtGui.QColor(self.drawn_pixel_color.red() * (1 - self.pixel_transparency)
                                     + old_color.red() * self.pixel_transparency,
                                     self.drawn_pixel_color.blue() * (1 - self.pixel_transparency)
                                     + old_color.blue() * self.pixel_transparency,
                                     self.drawn_pixel_color.green() * (1 - self.pixel_transparency)
                                     + old_color.green() * self.pixel_transparency,
                                     255)
            self.q_image.setPixelColor(x_coord, y_coord, new_color)
        logging.debug("_set_color_of_pixels finished")

    def update_pixel_transparency(self):
        """
        Updates the transparency of pixels that have already been drawn, with new
        transparency value set by user and refreshes the image.
        """
        logging.debug("update_pixel_transparency started")
        self._set_color_of_pixels(get_pixel_coords(self.target_pixel_coords, self.rows, self.cols))
        self.refresh_image()
        logging.debug("update_pixel_transparency finished")

    def check_roi_validity(self, coords):
        """
        checks the validity of the ROI coordinates
        returning true or false
        """
        if self.min_bounds_x < coords[0] < self.max_bounds_x:
            if self.min_bounds_y < coords[1] < self.max_bounds_y:
                # note that the x and y are purposely flipped, this was pre-existing
                if self.min_pixel < self.pixel_array[int(coords[1])][int(coords[0])] < self.max_pixel:
                    return True
        return False

    def update_dicom_image(self):
        """
        Updates the dicom image data, recalculating the roi pixel colour and displaying changes
        """
        logging.debug("update_dicom_image started for slice %s", self.current_slice)

        self.q_image = self.img.toImage()

        points = get_pixel_coords(self.according_color_dict, self.rows, self.cols)
        self._set_color_of_pixels(points)

        self.refresh_image()

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
        if self.q_pixmaps:
            self.removeItem(self.q_pixmaps)
        self.q_pixmaps = QtWidgets.QGraphicsPixmapItem(
            QtGui.QPixmap.fromImage(self.q_image))
        self.addItem(self.q_pixmaps)

    def remove_pixels_within_circle(self, clicked_x, clicked_y):
        """
        Removes all highlighted pixels within the selected circle and
        updates the image. :param clicked_x: the current x coordinate :param
        clicked_y: the current y coordinate
        """
        logging.debug("remove_pixels_within_circle started")
        # Calculate euclidean distance between each highlighted point and
        # the clicked point. If the distance is less than the radius,
        # remove it from the highlighted pixels.

        # The roi drawn on current slice is changed after several pixels are
        # modified
        self.slice_changed = True
        clicked_x, clicked_y = linear_transform(
            clicked_x, clicked_y, self.rows, self.cols)
        according_color_dict_key_list = list(self.according_color_dict.keys())

        for x, y in according_color_dict_key_list:
            colors = self.according_color_dict[(x, y)]
            clicked_point = numpy.array((clicked_x, clicked_y))
            point_to_check = numpy.array((x, y))
            distance = numpy.linalg.norm(clicked_point - point_to_check)
            if distance <= self.draw_tool_radius * (
                    float(self.rows) / DEFAULT_WINDOW_SIZE):
                temp = set()
                temp.add((x, y))
                points = get_pixel_coords(temp,
                                          self.rows,
                                          self.cols)
                for x_t, y_t in points:
                    self.q_image.setPixelColor(x_t, y_t,
                                               QColor.fromRgbF(
                                                   colors[0],
                                                   colors[1],
                                                   colors[2],
                                                   colors[3]))
                self.target_pixel_coords.remove((x, y))
                self.according_color_dict.pop((x, y))
                # The roi drawn on current slice is changed after several
                # pixels are modified
                self.slice_changed = True

        self.refresh_image()
        logging.debug("remove_pixels_within_circle finished")

    def fill_pixels_within_circle(self, clicked_x, clicked_y):
        """
        Add all highlighted pixels within the selected circle and updates
        the image. :param clicked_x: the current x coordinate :param
        clicked_y: the current y coordinate
        """
        logging.debug("fill_pixels_within_circle started")
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
        scaled_tool_radius = self.draw_tool_radius * (
                float(self.rows) / DEFAULT_WINDOW_SIZE)

        min_y_bound_square = math.ceil(clicked_y - scaled_tool_radius)
        min_x_bound_square = math.ceil(clicked_x - scaled_tool_radius)
        max_y_bound_square = math.ceil(clicked_y + scaled_tool_radius)
        max_x_bound_square = math.ceil(clicked_x + scaled_tool_radius)
        for y_coord in range(
                max(self.min_bounds_y, min_y_bound_square),
                min(self.max_bounds_y, max_y_bound_square)):
            for x_coord in range(
                    max(self.min_bounds_x, min_x_bound_square),
                    min(self.max_bounds_x, max_x_bound_square)):
                clicked_point = numpy.array((clicked_x, clicked_y))
                point_to_check = numpy.array((x_coord, y_coord))
                distance = numpy.linalg.norm(
                    clicked_point - point_to_check)

                if (self.keep_empty_pixel or
                    self.min_pixel <= self.pixel_array[y_coord][
                        x_coord] <= self.max_pixel) \
                        and distance <= scaled_tool_radius:
                    temp = set()
                    temp.add((x_coord, y_coord))
                    points = get_pixel_coords(temp, self.rows, self.cols)
                    temp_2 = get_first_entry(points)
                    c = self.q_image.pixel(temp_2[0], temp_2[1])
                    colors = QColor(c)
                    if (x_coord, y_coord) not in self.according_color_dict:
                        self.according_color_dict[
                            (x_coord, y_coord)] = colors.getRgbF()
                        points_to_color.add((x_coord, y_coord))
                        self.target_pixel_coords.add((x_coord, y_coord))

        points = get_pixel_coords(points_to_color, self.rows, self.cols)

        self._set_color_of_pixels(points)

        self.refresh_image()
        logging.debug("fill_pixels_within_circle finished")

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

    def draw_contour_preview(self, point_lists):
        """
        Draws a polygon onto the view so the user can preview what their
        contour will look like once exported.
        :param list of point_lists: A list of lists of points ordered to
        form polygons.
        """
        # Extract a list of lists of points
        list_of_qpoint_list = []
        # Scale points for non-standard image
        if self.rows != DEFAULT_WINDOW_SIZE:
            for list_of_points in point_lists:
                qpoint_list = []
                for point in list_of_points:
                    x_arr, y_arr = inv_linear_transform(
                        point[0], point[1], self.rows, self.cols)
                    for x in x_arr:
                        for y in y_arr:
                            qpoint = QtCore.QPoint(x, y)
                            qpoint_list.append(qpoint)
                list_of_qpoint_list.append(qpoint_list)
        else:
            for list_of_points in point_lists:
                qpoint_list = []
                for point in list_of_points:
                    qpoint = QtCore.QPoint(point[0], point[1])
                    qpoint_list.append(qpoint)
                list_of_qpoint_list.append(qpoint_list)

        # Remove previously added polygons
        for polygon in self.polygon_preview:
            self.removeItem(polygon)
        self.polygon_preview.clear()

        # Draw new polygons
        for qpoint_list in list_of_qpoint_list:
            polygon = QtGui.QPolygonF(qpoint_list)
            graphics_polygon_item = QtWidgets.QGraphicsPolygonItem(polygon)
            graphics_polygon_item.setPen(self.pen)
            self.polygon_preview.append(graphics_polygon_item)
            self.addItem(graphics_polygon_item)

    def set_source(self, event):
        """
        Uses the users mouse click position to set the fill source
        """
        self.fill_source = [round(event.scenePos().x()), round(event.scenePos().y())]
        self._display_pixel_color()

    @Slot(bool)
    def set_is_drawing(self, is_drawing):
        """
        Function triggered when either the Draw or Fill button is pressed from the menu.
        Sets the is_drawing bool, allows for filling or drawing from separate button presses
        """
        logging.debug("set_is_drawing started")
        self.is_drawing = is_drawing

    def manual_draw_roi(self, event):
        """
        Draws the ROI based on the users mouse press event and position
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

        if self.is_current_pixel_coloured:
            self.fill_pixels_within_circle(event.scenePos().x(),
                                           event.scenePos().y())
        else:
            self.remove_pixels_within_circle(event.scenePos().x(),
                                             event.scenePos().y())

    def mousePressEvent(self, event):
        """
            This method is called to handle a mouse press event
            :param event: the mouse event
        """
        if not self.is_drawing:
            self.set_source(event)
        else:
            self.manual_draw_roi(event)
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
            if self.is_current_pixel_coloured:
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
