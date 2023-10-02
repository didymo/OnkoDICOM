"""Shows the image from the controller
Has a slider to slide through the images"""

from PySide6.QtWidgets import QWidget, QLabel, QApplication, QGridLayout
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QHorizontalBarSeries, QBarSet
from PySide6.QtGui import QPixmap
from PySide6 import QtCore


class ImageWindow(QWidget):
    """Class for the image popup"""

    def __init__(self, width = 100, height = 600):
        """Sets up the GUI"""

        super().__init__()
        self.setWindowTitle("Image Display")

        self.range_select_width = width
        self.range_select_height = height
        #number of positions the sliders can occupy
        self.slider_density = int(self.range_select_height/3)

        self.mouse_held = False
        self.selected_bar = "top"

        # Create widgets
        self.image = QLabel()
        self.title = QLabel("(range-low) - (range-high)")
        self.ranges_view = QChartView()
        self.ranges = QChart()
        self.ranges_view.setChart(self.ranges)
        self.ranges.setPlotArea(
            QtCore.QRectF(0, 0, self.range_select_width, self.range_select_height))
        self.layout = QGridLayout()
        self.layout.addWidget(self.title, 0, 0, QtCore.Qt.AlignCenter)
        self.layout.addWidget(self.image, 1, 0, QtCore.Qt.AlignCenter)
        self.layout.addWidget(self.ranges_view, 1, 1)
        self.setLayout(self.layout)
        self.show()

        self.ranges_view.resize(self.range_select_width, self.range_select_height)
        self.ranges_view.setMouseTracking(True)
        self.ranges_view.viewport().installEventFilter(self)

        #Create sliders
        self.sliders = QHorizontalBarSeries()
        self.density = QLineSeries()
        self.sliders.setLabelsVisible(False)
        self.slider_bars=[]
        for i in range(0,self.slider_density):
            self.slider_bars.append(QBarSet(""))
            self.slider_bars[-1].append(1)
            self.slider_bars[-1].setColor("white")
            self.sliders.append(self.slider_bars[-1])
        self.ranges.addSeries(self.sliders)
        self.ranges.zoom(2)#at default zoom bars dont fill the chart

        #index of slider positions
        self.top = self.slider_density-1
        self.bottom = 0
        self.slider_bars[self.top].setColor("red")
        self.slider_bars[self.bottom].setColor("red")

    def eventFilter(self, obj, event):
        """Interactions with the slider"""

        #Mouse down in chart
        if obj is self.ranges_view.viewport() and event.type() == 2:
            self.mouse_held=True
            #get closest bar
            index = self.height_to_index(event.pos().y())
            if abs(index-self.top) < abs(index-self.bottom):
                self.selected_bar = "top"
            else:
                self.selected_bar = "bottom"
        #Mouse released
        elif self.mouse_held and event.type() == 3:
            self.mouse_held=False
            #move selected bar to closest valid position
            index = int(self.height_to_index(event.pos().y()))
            if self.selected_bar=="top" and index > self.bottom:
                self.slider_bars[self.top].setColor("white")
                self.top = index
                self.slider_bars[index].setColor("red")
            elif index < self.top:
                self.slider_bars[self.bottom].setColor("white")
                self.bottom = index
                self.slider_bars[index].setColor("red")
        return super().eventFilter(obj, event)

    def height_to_index(self, pos):
        """Converts graph coordinates to a slider index"""

        index = self.slider_density-1-int(pos/(self.range_select_height/(self.slider_density)))
        if index < 0:
            return 0
        if index >= self.slider_density:
            return self.slider_density-1
        return index

    def update(self, img, title):
        """Updates the image window"""

        self.image.setPixmap(img)
        self.title.setText(title)

    def set_density_histogram(self, densities):
        """Takes a list of any size for the histogram
        index 0 is for the lowest density"""

        self.density.setColor("grey")
        for i in range(0,len(densities)):
            self.density.append(2-densities[i],i)
        self.ranges.addSeries(self.density)


#test code
app = QApplication([])
im=QPixmap()
im.load("image.png")
a=ImageWindow()
a.update(im,"density range 0.83 - 0.92")
import random
d=[0.5]
for n in range(0,599):
    d.append((d[-1]+random.random())*random.random())
a.set_density_histogram(d)
