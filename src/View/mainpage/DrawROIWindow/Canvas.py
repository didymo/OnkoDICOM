"""This document contains the bulk of the programing for the Draw ROI
set_tool - changes the enum value to refelct the selected tool
mousePressEvent - handles the mouse press event. 
                    1st checks if the ds is active, meaning if the image showing matches the dicom data
                    2nd sets last point and first point, variables used in the drawing to conect strokes 
                        and variables used in transect to get the first and last point
                    3rd if the fill tool is active runs the fill tool code
                    4th if the transect tool code runs the transect tool code
"""
from collections import deque
from enum import Enum, auto
from scipy import ndimage as ndi
from PySide6 import QtWidgets
from PySide6.QtGui import QPixmap, QImage, QMouseEvent, QPainter, QPen, QColor
from PySide6.QtCore import Qt, Slot
import numpy as np
from src.Model.PatientDictContainer import PatientDictContainer
from src.View.mainpage.DrawROIWindow.Transect_Window import TransectWindow
from src.View.mainpage.DrawROIWindow.Copy_Roi import CopyROI


class Tool(Enum):
    """Holds the switch for the tools"""
    DRAW     = auto()
    FILL     = auto()
    CIRCLE   = auto()
    TRANSECT = auto()

class CanvasLabel(QtWidgets.QLabel):
    """Class for the drawing funnction, creates an invisable layer projected over a dicom image"""
    def __init__(self, pen: QPen, dicom_slice_viewer):
        super().__init__()
        self.pen = pen #the pen object that is used to draw on the canvas, can be changed in other classes
        self.last_point = None #becomes a x,y point
        self.first_point = None #becomes a x,y point
        self.t_window = None #becomes new window to show to transection window
        self.copy_roi_window = None # becomes the new window for copy roit
        self.current_tool = Tool.DRAW
        self.ds_is_active = False  #used to tell if undelying dicom file matches the above layer, this variable lets the pixel lock know if it needs to run
        self.slice_num = 0 #this variable represents the current viewable slice
        self.transect_pixmap_copy = None #Becomes a pixmap
        self.patient_dict_container = PatientDictContainer()
        self.dicom_slices = dicom_slice_viewer
        self.dicom_data = self.patient_dict_container.dataset
        self.dicom_slices.slider.valueChanged.connect(self.change_layout_bool)
        self.dicom_slices.slider.valueChanged.connect(self.update_pixmap_layer)

        self.number_of_slices = self.dicom_slices.slider.maximum() #number of image slices
        # sets the canvas and the mouse tracking
        #genorates a pixmap to draw on then copys that pixmap into an array an equal size of the dicom images
        self.gen_pix_map = QPixmap(512, 512)
        self.gen_pix_map.fill(Qt.transparent)
        self.canvas = [] #An array that holds all of the slices used in the viewer
        for _ in range(self.number_of_slices):
            self.canvas.append(self.gen_pix_map.copy())
        self.setPixmap(self.canvas[self.slice_num]) #sets the current pixmap to the first slice
        self.setMouseTracking(True)

        # default pen width
        self.pen.setWidth(12)

        # variables for different tools
        self.did_draw = False
        self.max_alpha = 255
        self.pixel_lock = 0       # will become a np.bool_ array [H,W]
        self.transect_array = []  #Holds the two values used to determain the transect array
        self.pixel_array = 0     #A numpy array that holds the pixel data of a slice
        self.mid_point = []   #When drawing will hold the points of each stroke, then creates an average and caculates that average

        # stores the pixmaps after each draw to allow for an undo button
        self.draw_history = [self.canvas.copy()]
        self.redo_history = []

        # pen setup
        self.pen = QPen()
        self.pen.setWidth(12)
        self.pen.setColor(Qt.blue)
        self.pen.setCapStyle(Qt.RoundCap)
        self.pen.setJoinStyle(Qt.RoundJoin)

        # transect Pen
        self.t_pen = QPen()
        self.t_pen.setWidth(2)
        self.t_pen.setColor(QColor(255, 105, 180))
        self.t_pen.setCapStyle(Qt.FlatCap)
        self.t_pen.setJoinStyle(Qt.MiterJoin)

        self.min_range = 0
        self.max_range = 6000

    def set_tool(self, tool_num):
        """Sets the tool"""
        self.current_tool = Tool(tool_num)

    def mousePressEvent(self, event: QMouseEvent):
        """Controls the mouse movements"""
        if not self.ds_is_active:
            self.set_pixel_layer(self.dicom_data[self.dicom_slices.slider.value()])
            self.ds_is_active = True
        self.last_point = event.position().toPoint()
        self.first_point = event.position().toPoint()
        if self.current_tool is Tool.FILL:
            self.pixel_fill((self.first_point.x(), self.first_point.y()))
            self.draw_history.append(self.canvas[self.slice_num].copy())  # CHANGED: record after enforcement
            self.redo_history.clear()
            self.setPixmap(self.canvas[self.slice_num])
        if self.current_tool is Tool.TRANSECT:
            self.transect_pixmap_copy = self.canvas[self.slice_num].copy()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() and (self.current_tool is Tool.DRAW or self.current_tool is Tool.CIRCLE):
            painter = QPainter(self.canvas[self.slice_num])
            current_point = event.position().toPoint()
            self.mid_point.append(current_point)
            painter.setCompositionMode(QPainter.CompositionMode_Source)
            painter.setPen(self.pen)
            if self.last_point:
                painter.drawLine(self.last_point, current_point)
            painter.end()

            self.setPixmap(self.canvas[self.slice_num])
            self.last_point = current_point
            self.did_draw = True
        if event.buttons() and self.current_tool is Tool.TRANSECT:
            painter = QPainter(self.canvas[self.slice_num])
            current_point = event.position().toPoint()
            painter.setCompositionMode(QPainter.CompositionMode_Source)
            painter.setPen(self.t_pen)
            painter.drawLine(self.first_point, current_point)
            self.setPixmap(self.canvas[self.slice_num])
            self.last_point = current_point
            if self.last_point:
                self.canvas[self.slice_num].fill(Qt.transparent)

    def mouseReleaseEvent(self, event: QMouseEvent):
        drew_something = False

        if self.current_tool is Tool.CIRCLE:
            # close the stroke then fill interior
            self.pen_fill_tool(event)
            drew_something = True
            self.mid_point.clear()

        elif self.did_draw:
            drew_something = True
            self.did_draw = False

        # If a stroke/fill occurred and it's not the TRANSECT overlay, enforce lock
        if drew_something and self.current_tool is not Tool.TRANSECT:
            self._enforce_lock_after_stroke()

            # Save history AFTER enforcement so undo/redo has the corrected image
            self.draw_history.append(self.canvas[self.slice_num].copy())  # CHANGED
            self.redo_history.clear()



        # Transect handling (kept as-is, not subject to lock)
        if self.current_tool is Tool.TRANSECT:
            point_values = (self.first_point,self.last_point)
            self.transect_window(point_values)
        self.last_point = None


    #Chat gpt redition of breseham algorithm
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
        transected_values = []

        for x, y in self._iter_line_pixels(p1_x, p1_y, p2_x, p2_y):
            if 0 <= x < w and 0 <= y < h:
                transected_values.append(self.pixel_array[y, x])


        self.t_window = TransectWindow(transected_values)
        self.t_window.show()
        self.canvas[self.slice_num] = self.transect_pixmap_copy
        self.setPixmap(self.canvas[self.slice_num])

    def copy_roi(self):
        """Allows the ablity to copy ROIs onto different areas"""
        self.copy_roi_window = CopyROI(self.number_of_slices, self.slice_num)
        self.copy_roi_window.copy_number_high.connect(self.copy_rois_up)
        self.copy_roi_window.copy_number_low.connect(self.copy_rois_down)
        self.copy_roi_window.show()

    def quick_copy(self, up_or_down:bool):
        """Changes the slide 1 up or 1 down and copies the slide"""
        if up_or_down:
            self.canvas[self.slice_num+1] = self.canvas[self.slice_num].copy()
            self.dicom_slices.slider.setValue(self.dicom_slices.slider.value() +1)
        elif not up_or_down & self.slice_num > 1:
            self.canvas[self.slice_num-1] = self.canvas[self.slice_num].copy()
            self.dicom_slices.slider.setValue(self.dicom_slices.slider.value() -1)
        self.ds_is_active = False
    def erase_roi(self):
        """Erases everything on the current slide"""
        self.canvas[self.slice_num].fill(Qt.transparent)
        self.setPixmap(self.canvas[self.slice_num])

    def pen_fill_tool(self, event):
        """connects the last two points and fills the insides"""
        current_point = event.position().toPoint()
        painter = QPainter(self.canvas[self.slice_num])
        painter.setCompositionMode(QPainter.CompositionMode_Source)
        painter.setPen(self.pen)
        painter.drawLine(self.first_point, current_point)
        painter.end()
        self.setPixmap(self.canvas[self.slice_num])
        ave = self.caculate_average_pixle()
        self.flood(ave)
        self.setPixmap(self.canvas[self.slice_num])
        # (history is now handled in mouseReleaseEvent after enforcement)

    def caculate_average_pixle(self):
        """Caculates the midpoint of the circle/drawing to allow the flood tool to work"""
        i = 1
        x = 0
        y = 0
        while self.mid_point:
            p = self.mid_point[0]
            x += p.x()
            y += p.y()
            self.mid_point.pop(0)
            i += 1
        average = (int(x / i), int(y / i))
        return average

    # not the things from halo
    def flood(self, mid_p):
        """Simple BFS flood fill on current canvas"""
        #Painter and drawing details
        fill = QPainter(self.canvas[self.slice_num])
        fill.setCompositionMode(QPainter.CompositionMode_Source)
        colour_contrast = self.pen.color()
        colour_contrast.setAlpha(self.max_alpha)
        fill.setBrush(QColor(colour_contrast))
        fill.setPen(Qt.NoPen)
        image = self.canvas[self.slice_num].toImage()
        
        #Cordinate Details
        x,y = mid_p
        queue = deque([(x, y)])
        visited = {(x, y)}
        target_color = image.pixelColor(x, y)
        direction = [(0,-1), (1,-1), (-1,0), (1,0), (-1,1), (0,1), (1,1)]

        while queue:
            x,y = queue.popleft()
            fill.drawRect(x, y, 1, 1)
            for dx, dy in direction:
                nx, ny = dx + x, dy + y
                if 0 <= nx < image.width() and 0 <= ny < image.height():
                    colour = image.pixelColor(nx, ny)
                    if colour == target_color and (nx, ny) not in visited:
                        queue.append((nx, ny))
                        visited.add((nx, ny))
        fill.end()

    def pixel_fill(self, mid_p):
        """Fill tool that respects pixel_lock at expansion time"""
        fill = QPainter(self.canvas[self.slice_num])
        fill.setCompositionMode(QPainter.CompositionMode_Source)
        colour_contrast = self.pen.color()
        colour_contrast.setAlpha(self.max_alpha)
        fill.setBrush(QColor(colour_contrast))
        fill.setPen(Qt.NoPen)
        image = self.canvas[self.slice_num].toImage()
        
        #Cordinate Details
        x, y = mid_p
        queue = deque([(x, y)])
        visited = {(x, y)}
        direction = [(0,-1), (1,-1), (-1,0), (1,0), (-1,1), (0,1), (1,1)]

        while queue:
            x, y = queue.popleft()
            fill.drawRect(x, y, 1, 1)
            for dx, dy in direction:
                nx, ny = dx + x, dy + y
                if 0 <= nx < image.width() and 0 <= ny < image.height() and (not self.pixel_lock[ny,nx] and (nx, ny) not in visited):
                    queue.append((nx, ny))
                    visited.add((nx, ny))

        fill.end()
    def undo_draw(self):
        """Reloads the last saved pixmap"""
        if len(self.draw_history) > 1:
            self.redo_history.append(self.canvas[self.slice_num].copy())
            self.draw_history.pop()
            self.canvas[self.slice_num] = self.draw_history[-1].copy()
            self.setPixmap(self.canvas[self.slice_num])

    def redo_draw(self):
        """Opposite of undo"""
        if self.redo_history:
            self.draw_history.append(self.redo_history[-1].copy())
            self.canvas[self.slice_num] = self.redo_history.pop()
            self.setPixmap(self.canvas[self.slice_num])

    def set_pixel_layer(self, ds):
        """Locks the pixels out of range based on max and min values"""
        self.pixel_array = ds.pixel_array.astype(np.int16)
        self.lock_pixel()

    def lock_pixel(self):
        """Creates the lock values for the drawing images"""
        # pixel_lock == True means "locked" (outside allowed HU)
        lock_mask = ~((self.pixel_array >= self.min_range) & (self.pixel_array <= self.max_range))
        self.pixel_lock = lock_mask

    def erase_dags(self):
        """Algorithm to erase dags
        scan the pixmap, note every pixel that shares the target colour
        add thoses into a np array 
        run an algorithm to check for clusters of pixels 
        delete the clusters """
        erase = QPainter(self.canvas[self.slice_num])
        erase.setCompositionMode(QPainter.CompositionMode_Source)
        colour_contrast = QColor(Qt.white)
        colour_contrast.setAlpha(0)
        erase.setBrush(QColor(colour_contrast))
        erase.setPen(Qt.NoPen)

        self._enforce_lock_after_stroke()

    #AI Vibe coded part
    # --------------- NEW: lock enforcement helpers ---------------


    def _draw_mask_bool(self) -> np.ndarray:
        """Alpha>0 where anything has been drawn on the canvas."""
        img = self.canvas[self.slice_num].toImage().convertToFormat(QImage.Format_ARGB32)
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
        marr = np.frombuffer(mptr, dtype=np.uint8).reshape(h, mask_img.bytesPerLine())

        # Fill only the active width (there may be padding on the right)
        marr[:, :w] = np.where(allow_mask, 255, 0).astype(np.uint8)

        # Apply as alpha mask
        p = QPainter(self.canvas[self.slice_num])
        p.setCompositionMode(QPainter.CompositionMode_DestinationIn)
        p.drawImage(0, 0, mask_img)
        p.end()

        self.setPixmap(self.canvas[self.slice_num])
#end of AI Gen

#This section contain all of the slots that communicate with methods in other files
    def change_layout_bool(self):
        """Changes the values of ds_is_active to remind the drawer to reset the pixmap
        once the scroll loader changes value"""
        self.ds_is_active = False

    def update_pixmap_layer(self, v:int):
        """When the slider changes value the pixmap gets updated"""
        self.setPixmap(self.canvas[v])
        self.slice_num = v
        self.update()

    @Slot(int)
    def copy_rois_up(self,v):
        """Copys any pixmap onto the rois values selcted"""
        i = self.slice_num
        while v > i:
            self.canvas[i] = self.canvas[self.slice_num]
            i +=1

    @Slot(int)
    def copy_rois_down(self,v):
        """Copys any pixmap onto the rois values selcted"""
        i = self.slice_num
        while v < i:
            self.canvas[i] = self.canvas[self.slice_num]
            i -=1