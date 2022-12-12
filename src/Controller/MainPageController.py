# This file handles all the processes within the Main page window of the
# software
import csv
import logging
import math

import matplotlib.cbook
import matplotlib.pyplot as plt1
from PySide6 import QtWidgets, QtCore, QtGui
from dateutil.relativedelta import relativedelta
from matplotlib.backend_bases import MouseEvent

import src.constants as constant
try:
    from src.Model.Anon import anonymize
    FEATURE_TOGGLE_PSEUDONYMISE = True # need to have declared either way
except ImportError as ePymedphysImportFailed:
    FEATURE_TOGGLE_PSEUDONYMISE = False
    logging.error(ePymedphysImportFailed)
    
from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.Transform import linear_transform
from src.Controller.PathHandler import data_path
from src.View.mainpage import ClinicalDataView

matplotlib.cbook.handle_exceptions = "print"  # default
matplotlib.cbook.handle_exceptions = "raise"
matplotlib.cbook.handle_exceptions = "ignore"

# matplotlib.cobook.handle_exceptions = my_logger
# will be called with exception as argument

# The following code are global functions and data/variables used by both
# Clinical Data form and Display classes

# This variable holds the errors messages of the Clinical data form
message = ""

# reading the csv files containing the available diseases
with open(data_path('ICD10_Topography.csv'), 'r') as f:
    reader = csv.reader(f)
    icd = list(reader)
    icd.pop(0)
with open(data_path('ICD10_Topography_C.csv'), 'r') as f:
    reader = csv.reader(f)
    icdc = list(reader)
    icdc.pop(0)
with open(data_path('ICD10_Morphology.csv'), 'r') as f:
    reader = csv.reader(f)
    hist = list(reader)
    hist.pop(0)

# Creating the arrays containing the above data and formatting them
# appropriately
new_icd = []
new_hist = []
strg = ''

for items in icd:
    for item in items:
        strg = strg + item
    new_icd.append(strg)
    strg = ''

for items in icdc:
    for item in items:
        strg = strg + item
    new_icd.append(strg)
    strg = ''

for items in hist:
    for item in items:
        strg = strg + item
    new_hist.append(strg)
    strg = ''


# This function return the difference of two dates in decimal years
def calculate_years(year1, year2):
    difference_years = relativedelta(year2.toPython(), year1.toPython()).years

    difference_months = relativedelta(
        year2.toPython(), year1.toPython()).months
    difference_in_days = relativedelta(year2.toPython(), year1.toPython()).days
    value = difference_years \
            + (difference_months / 12) \
            + (difference_in_days / 365)
    return "%.2f" % value


# This Class handles the Transect functionality
class Transect(QtWidgets.QGraphicsScene):

    # Initialisation function  of the class
    def __init__(self, main_window, image_to_paint, dataset, row_s, col_s,
                 tab_window, is_roi_draw=False):
        super(Transect, self).__init__()

        # create the canvas to draw the line on and all its necessary
        # components
        self.addItem(QtWidgets.QGraphicsPixmapItem(image_to_paint))
        self.img = image_to_paint
        self.values = []
        self.distances = []
        self.data = dataset
        self.pix_spacing = row_s / col_s
        self._start = QtCore.QPointF()
        self.drawing = True
        self._current_rect_item = None
        self.pos1 = QtCore.QPoint()
        self.pos2 = QtCore.QPoint()
        self.points = []
        self.roi_values = []
        self.roi_list = []
        self.is_ROI_draw = is_roi_draw
        self.tabWindow = tab_window
        self.mainWindow = main_window
        self._figure, self._axes, self._line = None, None, None
        self.leftLine, self.rightLine = None, None
        self._dragging_point = None
        self._points = {}
        self._valueTuples = {}
        self.thresholds = [4, 10]
        self.upper_limit = None
        self.lower_limit = None

    # This function starts the line draw when the mouse is pressed into the
    # 2D view of the scan
    def mousePressEvent(self, event):
        # Clear the current transect first
        plt1.close()
        # If is the first time we can draw as we want a line per button press
        if self.drawing:
            self.pos1 = event.scenePos()
            self._current_rect_item = QtWidgets.QGraphicsLineItem()
            pen = QtGui.QPen(QtGui.QColor("red"))
            self._current_rect_item.setPen(pen)
            self._current_rect_item.setFlag(
                QtWidgets.QGraphicsItem.ItemIsMovable, False)
            self.addItem(self._current_rect_item)
            self._start = event.scenePos()
            r = QtCore.QLineF(self._start, self._start)
            self._current_rect_item.setLine(r)

        # Second time generate mouse position

    # This function tracks the mouse and draws the line from the original
    # press point
    def mouseMoveEvent(self, event):
        if self._current_rect_item is not None and self.drawing:
            r = QtCore.QLineF(self._start, event.scenePos())
            self._current_rect_item.setLine(r)

    # This function terminates the line drawing and initiates the plot
    def mouseReleaseEvent(self, event):
        if self.drawing:
            self.pos2 = event.scenePos()
            # If a user just clicked one position
            if self.pos1.x() == self.pos2.x() \
                    and self.pos1.y() == self.pos2.y():
                self.drawing = False
            else:
                self.draw_dda(round(self.pos1.x()), round(self.pos1.y()),
                              round(self.pos2.x()), round(self.pos2.y()))
                self.drawing = False
                self.plot_result()
                self._current_rect_item = None

    # This function performs the DDA algorithm that locates all the points in
    # the drawn line
    def draw_dda(self, x1, y1, x2, y2):
        x, y = x1, y1
        length = abs(x2 - x1) if abs(x2 - x1) > abs(y2 - y1) else abs(y2 - y1)
        dx = (x2 - x1) / float(length)
        dy = (y2 - y1) / float(length)
        self.points.append((round(x), round(y)))

        for i in range(length):
            x += dx
            y += dy
            self.points.append((round(x), round(y)))

        # get the values of these points from the dataset
        self.get_values()
        # get their distances for the plot
        self.get_distances()

    # This function calculates the distance between two points
    def calculate_distance(self, x1, y1, x2, y2):
        dist = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        return dist

    # This function gets the corresponding values of all the points in the
    # drawn line from the dataset
    def get_values(self):
        for i, j in self.points:
            if i in range(constant.DEFAULT_WINDOW_SIZE) \
                    and j in range(constant.DEFAULT_WINDOW_SIZE):
                x, y = linear_transform(
                    i, j, len(self.data), len(self.data[0]))
                self.values.append(self.data[x][y])

    # Get the distance of each point from the end of the line
    def get_distances(self):
        for i, j in self.points:
            if i in range(constant.DEFAULT_WINDOW_SIZE) \
                    and j in range(constant.DEFAULT_WINDOW_SIZE):
                x, y = linear_transform(i, j,
                                        len(self.data), len(self.data[0]))
                x_2, y_2 = linear_transform(
                    round(self.pos2.x()), round(self.pos2.y()),
                    len(self.data), len(self.data[0]))
                self.distances.append(self.calculate_distance(
                    x, y, x_2, y_2))
        self.distances.reverse()

    # This function handles the closing event of the transect graph
    def on_close(self, event):
        plt1.close()

        # returns the main page back to a non-drawing environment
        if self.is_ROI_draw:
            self.mainWindow.upper_limit = self.upper_limit
            self.mainWindow.lower_limit = self.lower_limit
            self.mainWindow.on_transect_close()
        else:
            self.mainWindow.dicom_single_view.update_view()
            self.mainWindow.dicom_axial_view.update_view()

        event.canvas.figure.axes[0].has_been_closed = True

    def find_limits(self, roi_values):
        self.upper_limit = roi_values[len(roi_values) - 1]
        self.lower_limit = roi_values[0]
        temp = 0
        if self.lower_limit > self.upper_limit:
            temp = self.upper_limit
            self.upper_limit = self.lower_limit
            self.lower_limit = temp

    def return_limits(self):
        return [self.lower_limit, self.upper_limit]

    # This function plots the Transect graph into a pop up window
    def plot_result(self):
        plt1.close('all')
        new_list = [(x * self.pix_spacing) for x in self.distances]
        self.thresholds[0] = new_list[1]
        self.thresholds[1] = new_list[len(new_list) - 1]
        self._points[self.thresholds[0]] = 0
        self._points[self.thresholds[1]] = 0
        self._figure = plt1.figure(num='Transect Graph')
        new_manager = self._figure.canvas.manager
        new_manager.canvas.figure = self._figure
        self._figure.set_canvas(new_manager.canvas)
        self._axes = self._figure.add_subplot(111)
        self._axes.has_been_closed = False
        # new list is axis x, self.values is axis y
        self._axes.step(new_list, self.values, where='mid')
        if self.is_ROI_draw:
            for x in range(len(new_list)):
                self._valueTuples[new_list[x]] = self.values[x]
            self.leftLine = self._axes.axvline(self.thresholds[0], color='r')
            self.rightLine = self._axes.axvline(self.thresholds[1], color='r')
            # Recalculate the distance and CT# to show ROI in histogram
            self.roi_list.clear()
            self.roi_values.clear()
            for x in range(len(new_list)):
                if self.thresholds[0] <= new_list[x] <= self.thresholds[1]:
                    self.roi_list.append(new_list[x])
                    self.roi_values.append(self._valueTuples[new_list[x]])

        plt1.xlabel('Distance mm')
        plt1.ylabel('CT #')
        plt1.grid(True)
        self._figure.canvas.mpl_connect('close_event', self.on_close)
        self._figure.canvas.mpl_connect('button_press_event', self._on_click)
        self._figure.canvas.mpl_connect('button_release_event',
                                        self._on_release)
        self._figure.canvas.mpl_connect('motion_notify_event', self._on_motion)
        self._update_plot()
        plt1.show()

    def _update_plot(self):
        if self.is_ROI_draw:
            if not self._points:
                self._line.set_data([], [])
            else:
                x, y = zip(*sorted(self._points.items()))
                # Add new plot
                if not self._line:
                    self._line, = self._axes.plot(x, y, "b", marker="o",
                                                  markersize=10)
                # Update current plot
                else:
                    self._line.set_data(x, y)
                if len(x) >= 2:
                    self.leftLine.set_xdata(x[0])
                    self.rightLine.set_xdata(x[1])
                    self.thresholds[0] = x[0]
                    self.thresholds[1] = x[1]

                for i in self._axes.bar(self.distances, self.values):
                    i.set_color('white')
                for x in range(len(self.distances)):
                    self._valueTuples[self.distances[x]] = self.values[x]
                # Recalculate the distance and CT# to show ROI in histogram
                self.roi_list.clear()
                self.roi_values.clear()
                for x in range(len(self.distances)):
                    if self.thresholds[0] <= self.distances[x] \
                            <= self.thresholds[1]:
                        self.roi_list.append(self.distances[x])
                        self.roi_values.append(
                            self._valueTuples[self.distances[x]])
                self.find_limits(self.roi_values)
            self._figure.canvas.draw()

    def _add_point(self, x, y=None):
        if self.is_ROI_draw:
            if isinstance(x, MouseEvent):
                x = int(x.xdata)
            self._points[x] = 0
            return x, 0

    def _remove_point(self, x, _):
        if self.is_ROI_draw:
            if x in self._points:
                self._points.pop(x)

    def _find_neighbor_point(self, event):
        u""" Find point around mouse position

        :rtype: ((int, int)|None)
        :return: (x, y) if there are any point around mouse else None
        """
        if self.is_ROI_draw:
            distance_threshold = 50.0
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

    def _on_click(self, event):
        u""" callback method for mouse click event

        :type event: MouseEvent
        """
        if self.is_ROI_draw:
            # left click
            if event.button == 1 and event.inaxes in [self._axes]:
                point = self._find_neighbor_point(event)
                if point:
                    self._dragging_point = point
                self._update_plot()

    def _on_release(self, event):
        u""" callback method for mouse release event

        :type event: MouseEvent
        """
        if self.is_ROI_draw:
            if event.button == 1 \
                    and event.inaxes in [self._axes] \
                    and self._dragging_point:
                self._dragging_point = None
                self._update_plot()

    def _on_motion(self, event):
        u""" callback method for mouse motion event

        :type event: MouseEvent
        """
        if self.is_ROI_draw:
            if not self._dragging_point:
                return
            if event.xdata is None or event.ydata is None:
                return
            self._remove_point(*self._dragging_point)
            self._dragging_point = self._add_point(event)
            self._update_plot()


# This is the main page Controller class that handles all the activity
# in the main page

class MainPageCallClass:

    # Initialisation function of the controller
    def __init__(self):
        self.patient_dict_container = PatientDictContainer()

    # This function runs Anonymization on button click
    def run_anonymization(self, raw_dvh):
        if not FEATURE_TOGGLE_PSEUDONYMISE:
            raise ImportError("Unable to import pymedphys")
        path = self.patient_dict_container.path
        dataset = self.patient_dict_container.dataset
        filepaths = self.patient_dict_container.filepaths
        target_path = anonymize(path, dataset, filepaths, raw_dvh)
        return target_path

    def display_clinical_data(self, tab_window):
        """
        Display the clinical data tab.
        :param tab_window: The Tab Window that this tab is to be added
                           to.
        """
        self.tab_cd = ClinicalDataView.ClinicalDataView()
        tab_window.addTab(self.tab_cd, "Clinical Data")

    # This function runs Transect on button click
    def run_transect(self, main_window, tab_window, imageto_paint, dataset,
                     row_s, col_s, is_roi_draw=False):
        self.tab_ct = Transect(main_window, imageto_paint,
                               dataset, row_s, col_s, tab_window, is_roi_draw)
        tab_window.setScene(self.tab_ct)
