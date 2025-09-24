from collections import deque
import pydicom
from enum import Enum, auto
from PySide6 import QtWidgets
from PySide6.QtGui import QPixmap, QImage, QPainter, QPen, QColor
from PySide6.QtCore import Qt, Slot, Signal, QObject
import numpy as np
from src.Model.PatientDictContainer import PatientDictContainer
from src.View.mainpage.DrawROIWindow.Transect_Window import TransectWindow
from src.View.mainpage.DrawROIWindow.SaveToRTSS import SaveROI


class Tool(Enum):
    """Holds the switch for the tools"""
    DRAW = auto()
    FILL = auto()
    CIRCLE = auto()
    TRANSECT = auto()
    ZAPPER = auto()

#emitter necessary because QGraphicsPixmapItem cannot emmit signals
class Emitter(QObject):
    rtss_for_saving = Signal(pydicom.Dataset, str)


class CanvasLabel(QtWidgets.QGraphicsPixmapItem):
    """Class for the drawing funnction, creates an invisable layer projected over a dicom image"""

    def __init__(self, pen: QPen, slider, rtss):
        super().__init__()
        self.pen = pen  # the pen object that is used to draw on the canvas, can be changed in other classes
        self.last_point = None  # becomes a x,y point
        self.first_point = None  # becomes a x,y point
        self.t_window = None  # becomes new window to show to transection window
        self.current_tool = Tool.DRAW
        # used to tell if undelying dicom file matches the above layer, this variable lets the pixel lock know if it needs to run
        self.ds_is_active = False
        # this variable represents the current viewable slice
        self.transect_pixmap_copy = None  # Becomes a pixmap
        self.patient_dict_container = PatientDictContainer()
        self.dicom_slider = slider  # change in future
        self.dicom_data = self.patient_dict_container.dataset
        self.dicom_slider.valueChanged.connect(self.change_layout_bool)
        self.dicom_slider.valueChanged.connect(self.update_pixmap_layer)
        self.slice_num = self.dicom_slider.value()  # must change
        self.number_of_slices = self.dicom_slider.maximum()  # number of image slices
        # sets the canvas and the mouse tracking
        # genorates a pixmap to draw on then copys that pixmap into an array an equal size of the dicom images
        self.gen_pix_map = QPixmap(512, 512)
        self.gen_pix_map.fill(Qt.transparent)
        self.canvas = []  # An array that holds all of the slices used in the viewer

        # zoom variables
        self.base_canvas = []
        self.scale_factor = 1.0

        for _ in range(self.number_of_slices+1):
            self.canvas.append(self.gen_pix_map.copy())
            self.base_canvas.append(self.gen_pix_map.copy())
        # sets the current pixmap to the first slice
        self.setPixmap(self.canvas[self.slice_num])
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.LeftButton)

        # default pen width
        self.pen.setWidth(12)

        # variables for different tools
        self.did_draw = False
        self.max_alpha = 255
        self.pixel_lock = 0       # will become a np.bool_ array [H,W]
        self.transect_array = []  # Holds the two values used to determain the transect array
        self.pixel_array = 0  # A numpy array that holds the pixel data of a slice
        # When drawing will hold the points of each stroke, then creates an average and calculate that average
        self.mid_point = []

        # stores the pixmaps after each draw to allow for an undo button
        self.draw_history = [self.canvas[self.slice_num].copy()]
        self.redo_history = []

        # pen setup
        self.pen = QPen()
        self.pen.setWidth(12)
        self.pen.setColor(Qt.blue)
        self.pen.setCapStyle(Qt.RoundCap)
        self.pen.setJoinStyle(Qt.RoundJoin)

        # transect Pen
        self.t_pen = QPen()
        self.t_pen.setWidth(1)
        self.t_pen.setColor(QColor(255, 105, 180))
        self.t_pen.setCapStyle(Qt.FlatCap)
        self.t_pen.setJoinStyle(Qt.MiterJoin)

        self.min_range = 0 #variables for the pixlock
        self.max_range = 6000 #variables for the pixlock

        self.has_been_draw_on = []  # Used to track the slices that have been draw on
        self.rtss = rtss #the rtss stuctures
        self.roi_name = None #holds the roi names
        self.emitter = Emitter() #used to send signals
        self.erase_das_num = 20 #starting erase dags num

    def set_tool(self, tool_num):
        """Sets the tool  by changing the enum value
        Parm tool_num: int
        Returns: None
        """
        self.current_tool = Tool(tool_num)

    def mousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent):
        """Handles the mouse button click event
        when the user clicks the action depends on the current enum value
            parm event : QtWidgets.QGraphicsSceneMouseEvent
            return: None """
        if event.button() == Qt.LeftButton:
            if not self.ds_is_active:
                # activate once using the current slice’s pixel layer
                self.set_pixel_layer(
                    self.dicom_data[self.dicom_slider.value()])
                self.ds_is_active = True

            # keep everything in *item coordinates* (pixmap pixel space)
            self.slice_num = self.dicom_slider.value()
            self.check_if_drawn(self.slice_num)

            self.last_point = event.pos()
            self.first_point = event.pos()

            if self.current_tool in (Tool.FILL,  Tool.ZAPPER):
                self.flood((int(self.first_point.x()), int(
                    self.first_point.y())), paint_bicket=False)
                self.draw_history.append(self.canvas[self.slice_num].copy())
                self.redo_history.clear()
                self.setPixmap(self.canvas[self.slice_num])

            elif self.current_tool == Tool.TRANSECT:
                # keep a clean copy for live preview during move
                self.transect_pixmap_copy = self.canvas[self.slice_num].copy()

            event.accept()
        else:
            event.ignore()

    def mouseMoveEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent):
        """Handles the mouse click & drag event
            when the user clicks the action depends on the current enum value
            parm event : QtWidgets.QGraphicsSceneMouseEvent
            return: None """
        left_drag = bool(event.buttons() & Qt.LeftButton)

        if left_drag and self.current_tool in (Tool.DRAW, Tool.CIRCLE):
            self.check_if_drawn(self.slice_num)

            current_point = event.pos()
            pm = self.canvas[self.slice_num]
            painter = QPainter(pm)
            painter.setRenderHint(QPainter.Antialiasing, True)
            # or SourceOver if you want alpha blending
            painter.setCompositionMode(QPainter.CompositionMode_Source)
            painter.setPen(self.pen)

            if self.last_point is not None:
                painter.drawLine(self.last_point, current_point)
            painter.end()

            self.setPixmap(pm)  # refresh item
            self.last_point = current_point
            self.mid_point.append(event.pos())
            self.did_draw = True
            event.accept()
            return

        if left_drag and self.current_tool == Tool.TRANSECT:
            # draw a *preview* line on a fresh copy each move
            if self.transect_pixmap_copy is None:
                self.transect_pixmap_copy = self.canvas[self.slice_num].copy()

            preview = QPixmap(self.transect_pixmap_copy)
            painter = QPainter(preview)
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setCompositionMode(QPainter.CompositionMode_Source)
            painter.setPen(self.t_pen)
            painter.drawLine(self.first_point, event.pos())
            painter.end()
            self.setPixmap(preview)            # show preview
            self.last_point = event.pos()
            event.accept()
            return
        if left_drag and self.current_tool == Tool.ZAPPER:
            self.flood((int(event.pos().x()), int(
                    event.pos().y())), paint_bicket=False)
            self.setPixmap(self.canvas[self.slice_num])
        event.ignore()

    def mouseReleaseEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent):
        """Handles the mosue releases event, when the user lets go of the mouse
            parm event : QtWidgets.QGraphicsSceneMouseEvent
            return: None "
        """
        drew_something = False

        if self.current_tool == Tool.CIRCLE:
            self.pen_fill_tool(event)
            drew_something = True
            self.mid_point.clear()

        elif self.did_draw:
            drew_something = True
            self.did_draw = False

        if drew_something and self.current_tool != Tool.TRANSECT:
            self._enforce_lock_after_stroke()
            self.draw_history.append(self.canvas[self.slice_num].copy())
            self.redo_history.clear()
            self.setPixmap(self.canvas[self.slice_num])

        if self.current_tool == Tool.TRANSECT and self.first_point and self.last_point:
            self.transect_window((self.first_point, self.last_point))
            # restore base (remove preview)
            self.setPixmap(self.canvas[self.slice_num])
            self.transect_pixmap_copy = None

        self.last_point = None
        event.accept()

    def check_if_drawn(self, current_slice):
        """Checks if the pixmap has been drawn on, if yes then it gets added to the slice
        this function ensure all slices that have been draw on get saved
        parm int : current_slice"""
        if current_slice not in self.has_been_draw_on:
            self.has_been_draw_on.append(current_slice)

    # Chat gpt redition of breseham algorithm
    def _iter_line_pixels(self, x0: int, y0: int, x1: int, y1: int):
        """Bresenham integer line iterator: yields (x, y) for every pixel crossed."""
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        x, y = x0, y0

        if dx >= dy:
            err = dx // 2
            while x != x1:
                yield x, y
                err -= dy
                if err < 0:
                    y += sy
                    err += dx
                x += sx
            yield x1, y1
        else:
            err = dy // 2
            while y != y1:
                yield x, y
                err -= dx
                if err < 0:
                    x += sx
                    err += dy
                y += sy
            yield x1, y1

    def transect_window(self, point_values):
        """Creates the transect window"""
        self.draw_history.append(self.canvas[self.slice_num].copy())
        p1, p2 = point_values
        p1_x = int(p1.x())
        p1_y = int(p1.y())
        p2_x = int(p2.x())
        p2_y = int(p2.y())

        h, w = self.pixel_array.shape[:2]
        transected_values = [
            self.pixel_array[y, x]
            for x, y in self._iter_line_pixels(p1_x, p1_y, p2_x, p2_y)
            if 0 <= x < w and 0 <= y < h
        ]


        self.t_window = TransectWindow(transected_values)
        self.t_window.show()
        self.canvas[self.slice_num] = self.transect_pixmap_copy
        self.setPixmap(self.canvas[self.slice_num])

    def quick_copy(self, up_or_down: bool):
        """Changes the slide 1 up or 1 down and copies the slide
        parm bool : up_or_down"""
        if up_or_down:
            self.canvas[self.slice_num+1] = self.canvas[self.slice_num].copy()
            self.dicom_slider.setValue(self.dicom_slider.value() + 1)
            self.check_if_drawn(self.slice_num)
        elif not up_or_down and self.slice_num > 1:
            self.canvas[self.slice_num-1] = self.canvas[self.slice_num].copy()
            self.dicom_slider.setValue(self.dicom_slider.value() - 1)
            self.check_if_drawn(self.slice_num)
        self.ds_is_active = False

    def erase_roi(self):
        """
        Erases everything on the current slide
        parm:none
        return:none
        """
        self.canvas[self.slice_num].fill(Qt.transparent)
        self.setPixmap(self.canvas[self.slice_num])

    def pen_fill_tool(self, event):
        """
        connects the last two points and fills the insides
        parm QPoint: event
        return: none
        """
        current_point = event.pos()
        painter = QPainter(self.canvas[self.slice_num])
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        painter.setPen(self.pen)
        painter.drawLine(self.first_point, current_point)
        painter.end()
        self.setPixmap(self.canvas[self.slice_num])
        ave = self.calculate_average_pixel()
        self.flood(ave, paint_bicket=True)
        self.setPixmap(self.canvas[self.slice_num])
        # (history is now handled in mouseReleaseEvent after enforcement)

    def calculate_average_pixel(self):
        """
        calculate the midpoint of the circle/drawing to allow the flood tool to work
        parm :none
        return double: average
        """
        i = 1
        x = 0
        y = 0
        while self.mid_point:
            p = self.mid_point[0]
            x += p.x()
            y += p.y()
            self.mid_point.pop(0)
            i += 1
        return (int(x / i), int(y / i)) #average

    # not the things from halo
    def flood(self, mid_p, paint_bicket):
        """
        Simple BFS flood fill on current canvas, has two modes paint bucket which will ignore pixel lock values
        and look for lines with the same colour, "fill" tool function, this will look for pixel values
        parm: 
        QPoint: mid_p
        bool:paint_bucket
        return: None
        """
        # Painter and drawing details
        fill = QPainter(self.canvas[self.slice_num])
        fill.setCompositionMode(QPainter.CompositionMode_Source)
        colour_contrast = self.pen.color()
        #colour_contrast.setAlpha(self.max_alpha)
        fill.setBrush(QColor(colour_contrast))
        fill.setPen(Qt.NoPen)
        image = self.canvas[self.slice_num].toImage()

        # Cordinate Details
        x, y = mid_p
        queue = deque([(x, y)])
        visited = {(x, y)}
        target_color = image.pixelColor(x, y)
        direction = [(-1, -1), (0, -1), (1, -1),
                     (-1,  0),          (1,  0),
                     (-1,  1), (0,  1), (1,  1)]
        if paint_bicket:
            while queue:
                x, y = queue.popleft()
                fill.drawRect(x, y, 1, 1)
                for dx, dy in direction:
                    nx, ny = dx + x, dy + y
                    if 0 <= nx < image.width() and 0 <= ny < image.height():
                        colour = image.pixelColor(nx, ny)
                        if colour == target_color and (nx, ny) not in visited:
                            queue.append((nx, ny))
                            visited.add((nx, ny))
        else:
            if self.pixel_lock[y, x]:
                return
            while queue:
                x, y = queue.popleft()
                fill.drawRect(x, y, 1, 1)
                for dx, dy in direction:
                    nx, ny = dx + x, dy + y
                    if 0 <= nx < image.width() and 0 <= ny < image.height() and (not self.pixel_lock[ny, nx] and (nx, ny) not in visited):
                        queue.append((nx, ny))
                        visited.add((nx, ny))
        fill.end()

    def undo_draw(self):
        """
        Reloads the last saved pixmap
        parm:None
        Return:None
        """
        if len(self.draw_history) > 1:
            self.redo_history.append(self.canvas[self.slice_num].copy())
            self.draw_history.pop()
            self.canvas[self.slice_num] = self.draw_history[-1].copy()
            self.setPixmap(self.canvas[self.slice_num])

    def redo_draw(self):
        """
        Opposite of undo
        parm:None
        Return:None
        """
        if self.redo_history:
            self.draw_history.append(self.redo_history[-1].copy())
            self.canvas[self.slice_num] = self.redo_history.pop()
            self.setPixmap(self.canvas[self.slice_num])

    def set_pixel_layer(self, ds):
        """
        Takes the pixels values and creates a mask array over the dicom values
        Parm: Dicom dataset : ds
        Return: None
        """
        self.pixel_array = ds.pixel_array.astype(np.int16)
        self.lock_pixel()

    def lock_pixel(self):
        """
        Sets the lock range for the pixels
        Parm :None
        Return :None
        """
        lock_mask = ~((self.pixel_array >= self.min_range) &
                      (self.pixel_array <= self.max_range))
        self.pixel_lock = lock_mask

    def erase_dags(self):
        """    
        Algorithm to erase dags
        1. checks the bool array and returns a list of conected points using 
            def connected_components_grid(self, coords, connectivity=8)
        2. Loops through the array returned and if any are under the length of the erase dags num
            the points get coloured in
        Parm : None
        Return : None
         """
        self.set_pixel_layer(
            self.dicom_data[self.dicom_slider.value()])
        self.ds_is_active = True
        erase = QPainter(self.canvas[self.slice_num])
        erase.setCompositionMode(QPainter.CompositionMode_Source)
        colour_contrast = QColor(Qt.white)
        colour_contrast.setAlpha(0)
        erase.setBrush(QColor(colour_contrast))
        erase.setPen(Qt.NoPen)
        inv = ~self.pixel_lock
        cords = np.argwhere(inv)
        coords_xy = np.stack([cords[:, 1], cords[:, 0]],
                             axis=1)  # flips y,x to x,y
        connected_points = self.connected_components_grid(coords_xy)
        for i in connected_points:
            if len(i) < self.erase_das_num:
                for x, y in i:
                    erase.drawRect(x, y, 1, 1)
        erase.end()
        self.setPixmap(self.canvas[self.slice_num])

    # AI Vibe coded part ChatGPT 5 Thinking
    def connected_components_grid(self, coords, connectivity=8):
        """
        Group integer (x, y) coordinates into connected components on a grid.

        Args:
            coords: iterable of (x, y) integer tuples or 2D array-like.
            connectivity: 4 or 8.

        Returns:
            List[List[tuple]]: each inner list is one component of (x, y) tuples.
        """
        if connectivity == 4:
            nbrs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        elif connectivity == 8:
            nbrs = [(dx, dy) for dx in (-1, 0, 1)
                    for dy in (-1, 0, 1) if not (dx == 0 and dy == 0)]
        else:
            raise ValueError("connectivity must be 4 or 8")

        S = set(map(tuple, coords))           # O(1) membership/removal
        components = []

        while S:
            start = S.pop()
            comp = [start]
            q = deque([start])

            while q:
                x, y = q.popleft()
                for dx, dy in nbrs:
                    nb = (x+dx, y+dy)
                    if nb in S:
                        S.remove(nb)
                        q.append(nb)
                        comp.append(nb)

            components.append(comp)
        return components

    #ChatGPT 4.0
    # --------------- NEW: lock enforcement helpers ---------------
    def _draw_mask_bool(self) -> np.ndarray:
        """Alpha>0 where anything has been drawn on the canvas."""
        img = self.canvas[self.slice_num].toImage(
        ).convertToFormat(QImage.Format_ARGB32)
        h, w = img.height(), img.width()

        # memoryview (read-only is fine for reading)
        ptr = img.constBits()

        # View as bytes with row padding respected via bytesPerLine()
        arr = np.frombuffer(ptr, dtype=np.uint8).reshape(h, img.bytesPerLine())

        # Keep only the real pixel bytes (drop padding), then take alpha channel
        row_bytes = arr[:, : w * 4]   # ARGB32 = 4 bytes per pixel
        alpha = row_bytes[:, 3::4]    # every 4th byte starting at index 3
        return alpha > 0

    def _allowed_mask_bool(self) -> np.ndarray:
        """
        True where drawing is allowed by HU lock.
        (pixel_lock==True means locked; invert it)
        """
        if isinstance(self.pixel_lock, np.ndarray):
            return ~self.pixel_lock
        # If lock isn't ready yet, allow everywhere
        return np.ones((self.canvas[self.slice_num].height(), self.canvas[self.slice_num].width()), dtype=bool)

    def _enforce_lock_after_stroke(self):
        """
        Check drawn pixels against the lock, and erase anything outside the lock.
        """
        # Guard: need a HU array to have a meaningful lock
        if not isinstance(self.pixel_array, np.ndarray):
            return

        draw_mask = self._draw_mask_bool()
        allow_mask = self._allowed_mask_bool()

        if draw_mask.shape != allow_mask.shape:
            # Sizes must match; if not, do nothing to avoid errors
            return

        outside = draw_mask & ~allow_mask
        if not outside.any():
            return  # nothing to fix

        # Build an 8-bit alpha image (255 where allowed to keep, 0 where blocked => erased)
        h, w = allow_mask.shape
        mask_img = QImage(w, h, QImage.Format_Alpha8)
        mask_img.fill(0)

        # Writable memoryview
        mptr = mask_img.bits()
        marr = np.frombuffer(mptr, dtype=np.uint8).reshape(
            h, mask_img.bytesPerLine())

        # Fill only the active width (there may be padding on the right)
        marr[:, :w] = np.where(allow_mask, 255, 0).astype(np.uint8)

        # Apply as alpha mask
        p = QPainter(self.canvas[self.slice_num])
        p.setCompositionMode(QPainter.CompositionMode_DestinationIn)
        p.drawImage(0, 0, mask_img)
        p.end()

        self.setPixmap(self.canvas[self.slice_num])
 # end of AI gen

    def save_roi(self):
        """
            Saves the roi to an rtss and closes the window
            Parm : None
            Return : None
            signal pydicom.Dataset, string : results, self.roi_name
        """
        s = SaveROI(self.dicom_data, self.canvas, self.rtss,
                    self.has_been_draw_on, self.roi_name)
        results = s.save_roi()
        self.emitter.rtss_for_saving.emit(results, self.roi_name)

    def start_transect(self):
        """
        Enable transect drawing mode
        Parm : None
        Return : None
        """
        self.transect_active = True
        self.ds_is_active = False  # Temp disable ROI drawing
        if self.transect_line:
            self.scene().removeItem(self.transect_line)
            self.transect_line = None

# This section contain all of the slots and connections that communicate with methods in other files
    def change_layout_bool(self):
        """
        Changes the values of ds_is_active to remind the drawer to reset the pixel lock
        once the scroll loader changes value
        Parm : None
        Return : None
        """
        self.ds_is_active = False

    def update_pixmap_layer(self, v: int):
        """
        When the slider changes value the pixmap gets updated
        Parm int : v
        Return : None
        """
        self.setPixmap(self.canvas[v])
        self.slice_num = v
        self.update()

    @Slot(int)
    def copy_rois_up(self, v):
        """
        Copys the current pixmap onto other pixmaps
        Parm v : int
        Returns : None
        """
        i = self.slice_num+1
        holder = self.canvas[self.slice_num].copy()
        while v > i:
            self.canvas[i] = self.canvas[self.slice_num].copy()
            self.set_pixel_layer(self.dicom_data[i])
            self._enforce_lock_after_stroke()
            self.check_if_drawn(i)
            i += 1
        self.canvas[self.slice_num] = holder
        self.setPixmap(self.canvas[self.slice_num])
        self.ds_is_active = False

    @Slot(int)
    def copy_rois_down(self, v):
        """
        Copys any pixmap onto the rois values selcted
        Parm v : int
        Returns : None
        """
        i = self.slice_num-1
        holder = self.canvas[self.slice_num].copy()
        while v < i:
            self.canvas[i] = self.canvas[self.slice_num].copy()
            self.set_pixel_layer(self.dicom_data[i])
            self._enforce_lock_after_stroke()
            self.check_if_drawn(i)
            i -= 1
        self.canvas[self.slice_num] = holder
        self.setPixmap(self.canvas[self.slice_num])
        self.ds_is_active = False

    @Slot(str)
    def set_roi_name(self, v):
        """
        Sets the roi name that is emmited from the roi select box
        Parm v : String
        """
        self.roi_name = v

    @Slot(int)
    def set_max_pixel_value(self, v):
        """
        Sets the max pixel value for the pixel lock
        Parm v : int
        return : None
        
        """
        self.max_range = v
        self.lock_pixel()

    @Slot(int)
    def set_min_pixel_value(self, v):
        """
        Sets the min pixel value for the pixel lock
        Parm v : int
        return : None
        """
        self.min_range = v
        self.lock_pixel()

    @Slot(int, int)
    def multi_layer_commit(self, upper_bounds, lower_bounds):
        """
        Auto draws on every slide within the slides and pixmap given
        Parms 
        upper_bounds : int
        lower_bounds : int
        Return : None
        """
        i = lower_bounds
        holder = self.canvas[self.slice_num].copy()
        while upper_bounds > i:
            self.canvas[self.slice_num].fill(self.pen.color())
            self.set_pixel_layer(self.dicom_data[i])
            self._enforce_lock_after_stroke()
            self.canvas[i] = self.canvas[self.slice_num].copy()
            self.check_if_drawn(i)
            i += 1
        if upper_bounds > self.slice_num > lower_bounds:
            self.canvas[self.slice_num].fill(self.pen.color())
            self.set_pixel_layer(self.dicom_data[self.slice_num])
            self._enforce_lock_after_stroke()
            self.check_if_drawn(i)
        else:
            self.canvas[self.slice_num] = holder
        self.setPixmap(self.canvas[self.slice_num])
        self.ds_is_active = False
        self.update()
