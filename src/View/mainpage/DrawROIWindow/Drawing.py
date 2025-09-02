# Drawing.py
import copy
import logging
import numpy
import math

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Signal, Slot
from PySide6.QtGui import QColor, QPen
from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsEllipseItem

from src.constants import DEFAULT_WINDOW_SIZE
from src.Model.Transform import (
    linear_transform, get_pixel_coords, get_first_entry, inv_linear_transform
)


class Drawing(QtWidgets.QGraphicsScene):
    """
    ROI drawing scene
    """

    seed = Signal(list)

    # construction
    def __init__(
        self,
        imagetoPaint, pixmapdata, min_pixel, max_pixel, dataset,
        draw_roi_window_instance, slice_changed,
        current_slice, drawing_tool_radius, keep_empty_pixel, pixel_transparency,
        max_internal_hole_size, target_pixel_coords=set(), **kwargs
    ):
        super().__init__()

        # DICOM / image info
        self.dataset = dataset
        self.rows = dataset['Rows'].value
        self.cols = dataset['Columns'].value

        # external state
        self.draw_roi_window_instance = draw_roi_window_instance
        self.slice_changed = slice_changed
        self.current_slice = current_slice

        # thresholds & UI params
        self.min_pixel = min_pixel
        self.max_pixel = max_pixel
        self.draw_tool_radius = drawing_tool_radius
        self.keep_empty_pixel = keep_empty_pixel
        self.pixel_transparency = pixel_transparency
        self.drawn_pixel_color = QtGui.QColor(255, 0, 0, 255)

        # bounds/limits
        self.min_bounds_x = 0
        self.min_bounds_y = 0
        self.max_bounds_x = self.rows
        self.max_bounds_y = self.cols

        # hole fill
        self.max_internal_hole_size = max_internal_hole_size
        self.is_hole_filling = self.max_internal_hole_size > 0

        # seed wiring (for Fill)
        self.fill_source = kwargs.get('xy') if 'xy' in kwargs else None
        if 'UI' in kwargs and kwargs.get('UI') is not None:
            self.seed.connect(kwargs.get('UI').set_seed)

        # base pixmap & scene item
        # QPixmap (base CT slice as displayed)
        self.img = imagetoPaint
        self.addItem(QGraphicsPixmapItem(self.img))

        # working QImage (we always mutate this, never the base)
        self.q_image = self.img.toImage()

        # pixel array & window copy for value preview
        self.data = pixmapdata
        self.values = []
        self.getValues()

        # {(x,y)-> original RGBA floats}
        self.according_color_dict = {}
        # set[(x,y)] in DICOM pixel grid
        self.target_pixel_coords = set(target_pixel_coords)

        # preview polygons (unchanged)
        self.pen = QtGui.QPen(QtGui.QColor("yellow"))
        self.pen.setStyle(QtCore.Qt.DashDotDotLine)
        self.polygon_preview = []

        # cursor indicator
        self.cursor = None
        self.isPressed = False
        self.drag_position = QtCore.QPoint()
        self.rect = QtCore.QRect(250, 300, 20, 20)    # legacy drag rect

        # runtime buffers
        self.pixel_array = None
        self._circlePoints = []
        self._points = {}

        # mode: draw vs fill
        self.is_drawing = False
        self.is_current_pixel_coloured = False

        # scene mirror item for mutated image
        self.q_pixmaps = None
        self.refresh_image()

        # history stacks (Undo/Redo)
        self._history = []
        self._redo = []
        self._push_history_snapshot()  # initial

    # history helpers
    def _snapshot(self):
        # Lightweight snapshot: copy sets/dicts + a deep copy of q_image
        return (
            copy.deepcopy(self.target_pixel_coords),
            copy.deepcopy(self.according_color_dict),
            QtGui.QImage(self.q_image)  # QImage deep copy ctor
        )

    def _restore(self, snap):
        self.target_pixel_coords, self.according_color_dict, self.q_image = snap
        self.refresh_image()
        self.slice_changed = True

    def _push_history_snapshot(self):
        self._history.append(self._snapshot())
        self._redo.clear()

    @Slot()
    def undo(self):
        if len(self._history) <= 1:
            return
        self._redo.append(self._history.pop())
        self._restore(self._history[-1])

    @Slot()
    def redo(self):
        if not self._redo:
            return
        snap = self._redo.pop()
        self._history.append(snap)
        self._restore(snap)

    # bounds & transforms
    def set_bounds(self):
        if hasattr(self.draw_roi_window_instance, 'bounds_box_draw'):
            bound_box = self.draw_roi_window_instance.bounds_box_draw.box.rect()
            self.min_bounds_x, self.min_bounds_y = linear_transform(
                bound_box.x(), bound_box.y(), self.rows, self.cols
            )
            self.max_bounds_x, self.max_bounds_y = linear_transform(
                bound_box.width(), bound_box.height(), self.rows, self.cols
            )
            self.max_bounds_x += self.min_bounds_x
            self.max_bounds_y += self.min_bounds_y
        else:
            self.min_bounds_x = 0
            self.min_bounds_y = 0
            self.max_bounds_x = self.rows
            self.max_bounds_y = self.cols

    # ROI painting core
    def _display_pixel_color(self):
        """
        Flood fill based on min/max HU and optional hole-filling.
        Updates target_pixel_coords + according_color_dict and repaints.
        """
        self.set_bounds()
        self.pixel_array = self.dataset._pixel_array
        self.q_image = self.img.toImage()

        queue = [self.fill_source]
        outlines = set() if self.is_hole_filling else None

        while queue:
            current = queue.pop(0)
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    elem = [current[0] + dx, current[1] + dy]
                    if self.check_roi_validity(elem):
                        if (elem[0], elem[1]) not in self.target_pixel_coords:
                            queue.append([elem[0], elem[1]])
                            self.target_pixel_coords.add((elem[0], elem[1]))
                    else:
                        if outlines is not None:
                            if (elem[0], elem[1]) not in outlines:
                                outlines.add((elem[0], elem[1]))

        if outlines is not None:
            self.fill_holes(outlines)

        # collect original pixel colors (for later restore on erase)
        for x_coord, y_coord in self.target_pixel_coords:
            tmp = {(x_coord, y_coord)}
            p = get_pixel_coords(tmp, self.rows, self.cols)
            fx, fy = get_first_entry(p)
            col = self.q_image.pixel(fx, fy)
            self.according_color_dict[(x_coord, y_coord)] = QColor(
                col).getRgbF()

        pts = get_pixel_coords(self.according_color_dict, self.rows, self.cols)
        self._set_color_of_pixels(pts)
        self.refresh_image()

        self.slice_changed = True
        self._push_history_snapshot()

        return len(pts) >= 1

    def fill_holes(self, outlines):
        hole_outline_list = []
        while outlines:
            for first in outlines:
                break
            queue = [first]
            hole_outline = set()
            while queue:
                cur = queue.pop(0)
                if (cur[0], cur[1]) in outlines:
                    if (cur[0], cur[1]) not in hole_outline:
                        hole_outline.add((cur[0], cur[1]))
                        outlines.remove((cur[0], cur[1]))
                for dx in (-1, 1):
                    elem = [cur[0] + dx, cur[1]]
                    if (elem[0], elem[1]) in outlines and (elem[0], elem[1]) not in hole_outline:
                        queue.append([elem[0], elem[1]])
                        hole_outline.add((elem[0], elem[1]))
                        outlines.remove((elem[0], elem[1]))
                for dy in (-1, 1):
                    elem = [cur[0], cur[1] + dy]
                    if (elem[0], elem[1]) in outlines and (elem[0], elem[1]) not in hole_outline:
                        queue.append([elem[0], elem[1]])
                        hole_outline.add((elem[0], elem[1]))
                        outlines.remove((elem[0], elem[1]))
            if len(hole_outline) <= self.max_internal_hole_size:
                hole_outline_list.append(hole_outline)

        for outline in hole_outline_list:
            for first in outline:
                break
            if len(outline) == 1:
                if 1 <= self.max_internal_hole_size:
                    self.target_pixel_coords.add((first[0], first[1]))
                continue

            queue = [first]
            volume = 0
            hole_pixels = set()
            while queue:
                cur = queue.pop(0)
                for dx in (-1, 1):
                    elem = [cur[0] + dx, cur[1]]
                    if (elem[0], elem[1]) not in hole_pixels and (elem[0], elem[1]) not in self.target_pixel_coords:
                        queue.append([elem[0], elem[1]])
                        hole_pixels.add((elem[0], elem[1]))
                        volume += 1
                for dy in (-1, 1):
                    elem = [cur[0], cur[1] + dy]
                    if (elem[0], elem[1]) not in hole_pixels and (elem[0], elem[1]) not in self.target_pixel_coords:
                        queue.append([elem[0], elem[1]])
                        hole_pixels.add((elem[0], elem[1]))
                        volume += 1
                if volume > self.max_internal_hole_size:
                    break

            if volume <= self.max_internal_hole_size:
                self.target_pixel_coords.update(hole_pixels)

    def _set_color_of_pixels(self, points):
        """
        Blend ROI color over original image according to pixel_transparency.
        """
        logging.debug("_set_color_of_pixels started")
        base = self.img.toImage()
        for x, y in points:
            old = base.pixelColor(x, y)
            new_color = QtGui.QColor(
                self.drawn_pixel_color.red() * (1 - self.pixel_transparency) +
                old.red() * self.pixel_transparency,
                self.drawn_pixel_color.green() * (1 - self.pixel_transparency) +
                old.green() * self.pixel_transparency,
                self.drawn_pixel_color.blue() * (1 - self.pixel_transparency) +
                old.blue() * self.pixel_transparency,
                255
            )
            self.q_image.setPixelColor(x, y, new_color)
        logging.debug("_set_color_of_pixels finished")

    def update_pixel_transparency(self):
        logging.debug("update_pixel_transparency started")
        pts = get_pixel_coords(self.target_pixel_coords, self.rows, self.cols)
        self._set_color_of_pixels(pts)
        self.refresh_image()
        self.slice_changed = True
        self._push_history_snapshot()
        logging.debug("update_pixel_transparency finished")

    def check_roi_validity(self, coords):
        if self.min_bounds_x < coords[0] < self.max_bounds_x:
            if self.min_bounds_y < coords[1] < self.max_bounds_y:
                # note x/y flipped (historic)
                if self.min_pixel < self.pixel_array[int(coords[1])][int(coords[0])] < self.max_pixel:
                    return True
        return False

    def update_dicom_image(self):
        """
        Called when underlying DICOM windowing changed: repaint ROI over new base.
        """
        logging.debug("update_dicom_image started for slice %s",
                      self.current_slice)
        self.q_image = self.img.toImage()
        pts = get_pixel_coords(self.according_color_dict, self.rows, self.cols)
        self._set_color_of_pixels(pts)
        self.refresh_image()
        self.slice_changed = True
        self._push_history_snapshot()

    def getValues(self):
        for i in range(DEFAULT_WINDOW_SIZE):
            for j in range(DEFAULT_WINDOW_SIZE):
                x, y = linear_transform(i, j, self.rows, self.cols)
                if (0 <= x < self.cols) and (0 <= y < self.rows):
                    self.values.append(self.data[x][y])
                else:
                    logging.warning(
                        "x %s or y %s out of range while drawing, cols=%s rows=%s",
                        x, y, self.cols, self.rows
                    )

    def refresh_image(self):
        if self.q_pixmaps:
            self.removeItem(self.q_pixmaps)
        if self.q_image is None:
            logging.error(
                "q_image was None in refresh_image(); resetting to base img")
            self.q_image = self.img.toImage()
        self.q_pixmaps = QtWidgets.QGraphicsPixmapItem(
            QtGui.QPixmap.fromImage(self.q_image))
        self.addItem(self.q_pixmaps)

    # brush ops (continuous, smooth)
    def _scaled_radius(self):
        return self.draw_tool_radius * (float(self.rows) / DEFAULT_WINDOW_SIZE)

    def remove_pixels_within_circle(self, clicked_x, clicked_y):
        logging.debug("remove_pixels_within_circle started")
        self.slice_changed = True
        cx, cy = linear_transform(clicked_x, clicked_y, self.rows, self.cols)
        to_restore = []
        r = self._scaled_radius()

        # iterate over currently colored points only
        for (x, y), rgba in list(self.according_color_dict.items()):
            if numpy.hypot(cx - x, cy - y) <= r:
                # restore original pixel color
                pts = get_pixel_coords({(x, y)}, self.rows, self.cols)
                for px, py in pts:
                    self.q_image.setPixelColor(px, py, QColor.fromRgbF(*rgba))
                to_restore.append((x, y))

        for key in to_restore:
            self.according_color_dict.pop(key, None)
            self.target_pixel_coords.discard(key)

        self.refresh_image()
        self._push_history_snapshot()
        logging.debug("remove_pixels_within_circle finished")

    def fill_pixels_within_circle(self, clicked_x, clicked_y):
        logging.debug("fill_pixels_within_circle started")
        self.slice_changed = True
        cx, cy = linear_transform(clicked_x, clicked_y, self.rows, self.cols)
        r = self._scaled_radius()

        min_y = max(self.min_bounds_y, math.ceil(cy - r))
        max_y = min(self.max_bounds_y, math.ceil(cy + r))
        min_x = max(self.min_bounds_x, math.ceil(cx - r))
        max_x = min(self.max_bounds_x, math.ceil(cx + r))

        points_to_color = set()
        for y in range(min_y, max_y):
            for x in range(min_x, max_x):
                if numpy.hypot(cx - x, cy - y) <= r:
                    if (self.keep_empty_pixel or (self.min_pixel <= self.dataset._pixel_array[y][x] <= self.max_pixel)):
                        if (x, y) not in self.according_color_dict:
                            pts = get_pixel_coords(
                                {(x, y)}, self.rows, self.cols)
                            fx, fy = get_first_entry(pts)
                            c = self.q_image.pixel(fx, fy)
                            self.according_color_dict[(
                                x, y)] = QColor(c).getRgbF()
                            self.target_pixel_coords.add((x, y))
                            points_to_color.add((x, y))

        if points_to_color:
            pts = get_pixel_coords(points_to_color, self.rows, self.cols)
            self._set_color_of_pixels(pts)
            self.refresh_image()
            self._push_history_snapshot()

        logging.debug("fill_pixels_within_circle finished")

    # cursor ring
    def clear_cursor(self, drawing_tool_radius):
        self.draw_tool_radius = drawing_tool_radius
        if self.cursor:
            self.removeItem(self.cursor)
            self.cursor = None

    def draw_cursor(self, event_x, event_y, drawing_tool_radius, new_circle=False):
        self.draw_tool_radius = drawing_tool_radius
        self.current_cursor_x = event_x - self.draw_tool_radius
        self.current_cursor_y = event_y - self.draw_tool_radius
        if new_circle:
            self.cursor = QGraphicsEllipseItem(
                self.current_cursor_x, self.current_cursor_y,
                self.draw_tool_radius * 2, self.draw_tool_radius * 2
            )
            pen = QPen(QColor("blue"))
            pen.setWidth(0)
            self.cursor.setPen(pen)
            self.cursor.setZValue(1)
            self.addItem(self.cursor)
        elif self.cursor is not None:
            self.cursor.setRect(
                self.current_cursor_x, self.current_cursor_y,
                self.draw_tool_radius * 2, self.draw_tool_radius * 2
            )

    # preview polygon
    def draw_contour_preview(self, point_lists):
        list_of_qpoint_list = []
        if self.rows != DEFAULT_WINDOW_SIZE:
            for lst in point_lists:
                qlist = []
                for (px, py) in lst:
                    x_arr, y_arr = inv_linear_transform(
                        px, py, self.rows, self.cols)
                    for x in x_arr:
                        for y in y_arr:
                            qlist.append(QtCore.QPoint(x, y))
                list_of_qpoint_list.append(qlist)
        else:
            for lst in point_lists:
                qlist = [QtCore.QPoint(p[0], p[1]) for p in lst]
                list_of_qpoint_list.append(qlist)

        for poly in self.polygon_preview:
            self.removeItem(poly)
        self.polygon_preview.clear()

        for ql in list_of_qpoint_list:
            polygon = QtGui.QPolygonF(ql)
            item = QtWidgets.QGraphicsPolygonItem(polygon)
            item.setPen(self.pen)
            self.polygon_preview.append(item)
            self.addItem(item)

    # fill source
    def set_source(self, event):
        self.fill_source = [round(event.scenePos().x()),
                            round(event.scenePos().y())]
        ok = self._display_pixel_color()
        if ok:
            self.seed.emit(self.fill_source)

    # mode switch
    @Slot(bool)
    def set_is_drawing(self, is_drawing):
        logging.debug("set_is_drawing started")
        self.is_drawing = is_drawing

    # --- Qt mouse events ---------------------------------------------------
    def manual_draw_roi(self, event):
        if self.cursor:
            self.removeItem(self.cursor)
        self.isPressed = True

        if 2 * QtGui.QVector2D(event.pos() - self.rect.center()).length() < self.rect.width():
            self.drag_position = event.pos() - self.rect.topLeft()

        super().mousePressEvent(event)

        x, y = linear_transform(
            math.floor(event.scenePos().x()), math.floor(event.scenePos().y()),
            self.rows, self.cols
        )
        self.is_current_pixel_coloured = ((x, y) in self.according_color_dict)

        self.draw_cursor(event.scenePos().x(), event.scenePos(
        ).y(), self.draw_tool_radius, new_circle=True)

        if self.is_current_pixel_coloured:
            self.remove_pixels_within_circle(
                event.scenePos().x(), event.scenePos().y())
        else:
            self.fill_pixels_within_circle(
                event.scenePos().x(), event.scenePos().y())

    def mousePressEvent(self, event):
        if not self.is_drawing:
            self.set_source(event)
        else:
            self.manual_draw_roi(event)
        self.update()

    def mouseMoveEvent(self, event):
        if not self.drag_position.isNull():
            self.rect.moveTopLeft(event.pos() - self.drag_position)
        super().mouseMoveEvent(event)

        if self.cursor and self.isPressed:
            self.draw_cursor(event.scenePos().x(),
                             event.scenePos().y(), self.draw_tool_radius)
            if self.is_current_pixel_coloured:
                self.remove_pixels_within_circle(
                    event.scenePos().x(), event.scenePos().y())
            else:
                self.fill_pixels_within_circle(
                    event.scenePos().x(), event.scenePos().y())
        self.update()

    def mouseReleaseEvent(self, event):
        self.isPressed = False
        self.drag_position = QtCore.QPoint()
        super().mouseReleaseEvent(event)
        self.update()

    def set_pen_width(self, width: int):
        """Update pen radius from toolbar spinbox"""
        self.drawing_tool_radius = width / 2
