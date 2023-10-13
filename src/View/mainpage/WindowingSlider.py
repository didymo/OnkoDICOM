from src.Model.PatientDictContainer import PatientDictContainer
from PySide6.QtWidgets import QWidget, QLabel, QApplication, QGridLayout, QSizePolicy
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QHorizontalBarSeries, QBarSet
from PySide6.QtGui import QPixmap, QPainter
from PySide6 import QtCore
from math import ceil

from src.Model.Windowing import windowing_model_direct, set_windowing_slider

import random


def gen_random_histogram():
    """
    Temporary function to populate histogram
    """
    d = [0.5]
    for n in range(0, 599):
        d.append((d[-1] + random.random()) * random.random())
    return d


class WindowingSlider(QWidget):
    """
    A custom Widget that contains a histogram of
    pixel values in the current image, and two
    sliders that allowing setting of the windowing
    function.
    """

    # Max distance from slider clicks are accepted
    MAX_CLICK_DIST = 5
    # Minimum rendering height for bottom bar
    MIN_BOTTOM_INDEX = 4
    # Window/Level consts
    MAX_PIXEL_VALUE = 4096
    LEVEL_OFFSET = 1000

    SINGLETON = None

    def __init__(self, width=50):
        """
        Initialise the slider
        :param width: the fixed width of the widget
        """

        super().__init__()
        self.action_handler = None
        if WindowingSlider.SINGLETON is None:
            WindowingSlider.SINGLETON = self
            set_windowing_slider(self)

        # Manage size of whole widget
        self.fixed_width = width
        self.size_policy = QSizePolicy()
        self.size_policy.setHorizontalPolicy(QSizePolicy.Policy.Fixed)
        self.size_policy.setVerticalPolicy(QSizePolicy.Policy.Preferred)
        self.setSizePolicy(self.size_policy)
        self.setFixedWidth(self.fixed_width)

        # Histogram
        self.histogram_view = HistogramChart(self)
        self.histogram_view.windowing_slider = self
        self.histogram = QChart()
        self.histogram_view.setChart(self.histogram)
        self.histogram.setPlotArea(
            QtCore.QRectF(0, 0, self.fixed_width, self.height()))

        self.histogram_view.resize(self.fixed_width, self.height())
        self.histogram_view.setMouseTracking(True)
        self.histogram_view.viewport().installEventFilter(self)

        self.density = QLineSeries()
        self.slider_density = int(self.height() / 3)

        # Create sliders
        self.sliders = QHorizontalBarSeries()
        self.density = QLineSeries()
        self.sliders.setLabelsVisible(False)
        self.slider_bars = []
        for i in range(0, self.slider_density):
            self.slider_bars.append(QBarSet(""))
            self.slider_bars[-1].append(1)
            self.slider_bars[-1].setColor("white")
            self.sliders.append(self.slider_bars[-1])
        self.histogram.addSeries(self.sliders)
        self.histogram.zoom(2)  # at default zoom bars don't fill the chart

        # Layout
        self.layout = QGridLayout()
        self.layout.addWidget(self.histogram_view, 0, 0)
        self.setLayout(self.layout)

        # index of slider positions
        self.top = self.slider_density - 1
        self.bottom = 0

        # Get the values for window and level from the dict
        patient_dict_container = PatientDictContainer()
        print(patient_dict_container.get("dict_windowing"))  # testing
        windowing_limits = patient_dict_container.get("dict_windowing")['Normal']

        # Set window and level to the new values
        window = windowing_limits[0]
        level = windowing_limits[1]
        self.set_bars_from_window(window, level)

        # Middle drag
        self.mouse_held = False
        self.selected_bar = "top"
        self.middle_drag_bounds = {
            "top_origin": 0,
            "bottom_origin": 0
        }

        # Test
        self.set_density_histogram(gen_random_histogram())

    def set_action_handler(self, action_handler):
        """
        Sets the action handler.
        The action handler can call update_views()
        :param action_handler: the action handler
        """
        self.action_handler = action_handler

    def resizeEvent(self, event):
        self.histogram.setPlotArea(
            QtCore.QRectF(0, 0, self.fixed_width, event.size().height()))

    def height_to_index(self, pos):
        """
        Converts graph coordinates to a slider index
        :param pos: a local coordinate on the graph
        """
        index = self.slider_density-1-int(pos/(self.height()/self.slider_density))
        if index < 0:
            return 0
        if index >= self.slider_density:
            return self.slider_density-1
        return index

    def window_to_index(self, val):
        """
        Converts a window value to a slider index
        :param val: a value
        """
        normalized_val = val / WindowingSlider.MAX_PIXEL_VALUE
        index = ceil(self.slider_density * (1 - normalized_val)) - 1
        return index

    def index_to_window(self, index):
        """
        Converts a slider index to a window value
        :param index: a value
        """

        percent = index / self.slider_density
        val = round((1 - percent) * WindowingSlider.MAX_PIXEL_VALUE)
        return val

    def set_bars_from_window(self, window, level):
        """
        Triggered when the user selects a windowing preset.
        Adjusts the values into the 0-2000 range, then updates the bars.
        :param window: the window value of the preset
        :param level: the level value of the preset
        """
        level = level + WindowingSlider.LEVEL_OFFSET
        self.update_bar(
            self.window_to_index(level - window * 0.5), top_bar=True)
        self.update_bar(
            self.window_to_index(level + window * 0.5), top_bar=False)

    def set_density_histogram(self, densities):
        """
        Takes a list of any size and forms the histogram.
        Index 0 is for the lowest density.
        :param densities: a list of values from 0-1
        """

        self.density.setColor("grey")
        for i in range(0, len(densities)):
            self.density.append(2-densities[i], i)
        self.histogram.addSeries(self.density)

    def update_bar(self, index, top_bar=True):
        """
        Moves the chosen bar to the provided index.
        :param index: the index to move to
        :param top_bar: whether to move the top or bottom bar
        """

        # Clamp index to range
        index = max(index, 0)
        index = min(index, self.slider_density-1)

        if top_bar:
            self.slider_bars[self.top].setColor("white")
            self.top = index
            self.slider_bars[index].setColor("red")
        else:
            # Ensure the bottom bar is actually rendered
            # Functionally the bar will still be correct
            self.slider_bars[
                max(self.bottom, WindowingSlider.MIN_BOTTOM_INDEX)
                ].setColor("white")
            self.bottom = index
            self.slider_bars[
                max(index, WindowingSlider.MIN_BOTTOM_INDEX)
                ].setColor("red")

    def set_bars(self, top_index, bottom_index):
        """
        Call to set the state of the two sliders.
        :param top_index: index of the top bar
        :param bottom_index: index of the bottom bar
        """

        self.update_bar(top_index, top_bar=True)
        self.update_bar(bottom_index, top_bar=False)

    def mouse_press(self, event):
        """
        Called on the HistogramChart's mousePressEvent
        :param event: PySide mouse press event
        """

        # get the closest bar
        index = self.height_to_index(event.position().y())

        dist_to_top = abs(index - self.top)
        dist_to_bottom = abs(index - self.bottom)
        min_dist = min(dist_to_top, dist_to_bottom)

        if min_dist > WindowingSlider.MAX_CLICK_DIST:
            # Check for middle drag
            if index - self.top > 0 or index - self.bottom > 0:
                self.selected_bar = "middle"
                self.mouse_held = True
                self.middle_drag_bounds['top_origin'] = self.top
                self.middle_drag_bounds['bottom_origin'] = self.bottom
            return

        self.mouse_held = True
        if dist_to_top < dist_to_bottom:
            self.selected_bar = "top"
        else:
            self.selected_bar = "bottom"

    def mouse_move(self, event):
        """
        Called on the HistogramChart's mouseMoveEvent
        :param event: PySide mouse move event
        """

        if not self.mouse_held:
            return

        self.update_bar_position(event)

    def mouse_release(self, event):
        """
        Called on the HistogramChart's mouseReleaseEvent
        :param event: PySide mouse release event
        """

        if not self.mouse_held:
            return

        self.mouse_held = False
        self.update_bar_position(event)

        send = [
            True,
            False,
            False,
            False]

        top_bar = self.index_to_window(self.top)
        bottom_bar = self.index_to_window(self.bottom)

        level = (top_bar + bottom_bar) * 0.5
        window = 2 * (bottom_bar - level)
        level = level - 1000

        windowing_model_direct(level, window, send)
        if self.action_handler is not None:
            self.action_handler.update_views()

    def update_bar_position(self, event):
        if self.selected_bar == "middle":
            self.update_bar_middle_drag(event)
            return

        # move selected bar to the closest valid position
        index = int(self.height_to_index(event.position().y()))
        if self.selected_bar == "top":
            if index <= self.bottom:
                index = self.bottom + 1
            self.update_bar(index, top_bar=True)
        else:
            if index >= self.top:
                index = self.top - 1
            self.update_bar(index, top_bar=False)

    def update_bar_middle_drag(self, event):
        """"""
        pass


class HistogramChart(QChartView):
    """
    A custom QChartView class to override mouse events
    when clicking on the histogram.
    Calls the respective functions in the parent
    WindowingSlider class.
    """

    def __int__(self, parent):
        self.windowing_slider = parent

    def mousePressEvent(self, event):
        self.windowing_slider.mouse_press(event)

    def mouseMoveEvent(self, event):
        self.windowing_slider.mouse_move(event)

    def mouseReleaseEvent(self, event):
        self.windowing_slider.mouse_release(event)
