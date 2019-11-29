from PyQt5 import QtWidgets, QtCore, QtGui
import matplotlib.pylab as plt
import numpy as np
import os
from src.Model.CalculateDVHs import *
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class DVH(object):
    """
    Manage all functionalities related to the DVH tab.
    - Create and update the DVH.
    - Manage Export DVH functionality.
    """

    def __init__(self, mainWindow):
        """
        Initialize the information useful for creating the DVH.
        Create the plot widget to place in the window (plotWidget) and the export DVH button.

        :param mainWindow:
         the window of the main page
        """
        self.window = mainWindow
        self.selected_rois = mainWindow.selected_rois
        self.raw_dvh = mainWindow.raw_dvh
        self.dvh_x_y = mainWindow.dvh_x_y
        self.roi_color = mainWindow.roiColor
        self.plot = self.plot_dvh()
        self.plotWidget = FigureCanvas(self.plot)
        self.button_export = self.export_button()


    def plot_dvh(self):
        """
        :return:
         DVH plot using Matplotlib library.
        """

        # Initialisation of the plots
        fig, ax = plt.subplots()
        fig.subplots_adjust(0.1, 0.15, 1, 1)
        # Maximum value for x axis
        max_xlim = 0

        # Plot for all the ROIs selected in the left column of the window
        for roi in self.selected_rois:
            dvh = self.raw_dvh[int(roi)]

            # Plot only the ROIs whose volume is non equal to 0
            if dvh.volume != 0:
                # Bincenters, obtained from the dvh object, give the x axis values
                # (Doses originally in Gy unit)
                bincenters = self.dvh_x_y[roi]['bincenters']

                # Counts, obtained from the dvh object, give the y axis values
                # (values between 0 and dvh.volume)
                counts = self.dvh_x_y[roi]['counts']

                # Color of the line is the same as the color shown in the left column of the window
                color = self.roi_color[roi]
                color_R = color['R'] / 255
                color_G = color['G'] / 255
                color_B = color['B'] / 255

                plt.plot(100 * bincenters,
                         100 * counts / dvh.volume,
                         label=dvh.name,
                         color=[color_R, color_G, color_B])

                # Update the maximum value for x axis (usually different between ROIs)
                if (100 * bincenters[-1]) > max_xlim:
                    max_xlim = 100 * bincenters[-1]

                plt.xlabel('Dose [%s]' % 'cGy')
                plt.ylabel('Volume [%s]' % '%')
                if dvh.name:
                    plt.legend(loc='lower center', bbox_to_anchor=(0, 1, 5, 5))

        # Set the range values for x and y axis
        ax.set_ylim([0, 105])
        ax.set_xlim([0, max_xlim + 3])

        # Create the grids on the plot
        major_ticks_y = np.arange(0, 105, 20)
        minor_ticks_y = np.arange(0, 105, 5)
        major_ticks_x = np.arange(0, max_xlim + 250, 1000)
        minor_ticks_x = np.arange(0, max_xlim + 250, 250)
        ax.set_xticks(major_ticks_x)
        ax.set_xticks(minor_ticks_x, minor=True)
        ax.set_yticks(major_ticks_y)
        ax.set_yticks(minor_ticks_y, minor=True)
        ax.grid(which='minor', alpha=0.2)
        ax.grid(which='major', alpha=0.5)

        # Add the legend at the bottom left of the graph
        if len(self.selected_rois) != 0:
            ax.legend(loc='upper left', bbox_to_anchor=(-0.1, -0.15), ncol=4)

        plt.subplots_adjust(bottom=0.3)

        return fig


    def init_layout(self, mainWindow):
        """
        Initialize the layout for the DVH tab.
        Add the plot widget and the Export button in the layout.

        :param mainWindow:
         the window of the main page
        """
        self.layout = QtWidgets.QGridLayout(mainWindow.tab2_DVH)
        self.layout.addWidget(self.plotWidget, 1, 0, 1, 1)
        self.layout.addWidget(self.button_export, 1, 1, 1, 1, QtCore.Qt.AlignBottom)


    def update_plot(self, mainWindow):
        """
        Update the DVH plot.

        :param mainWindow:
         the window of the main page
        """
        self.layout.removeWidget(self.plotWidget)
        self.__init__(mainWindow)
        self.layout.addWidget(self.plotWidget, 1, 0, 1, 1)


    def export_button(self):
        """
        Create a button Export DVH.
        """
        button = QtWidgets.QPushButton()
        button.setFocusPolicy(QtCore.Qt.NoFocus)
        button.setFixedSize(QtCore.QSize(100, 39))
        button.setCursor(
            QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        button.setStyleSheet("background-color: rgb(238, 238, 236);\n"
                                            "font: 57 11pt \"Ubuntu\";\n"
                                            "color:rgb(75,0,130);\n"
                                            "font-weight: bold;\n")
        button.setObjectName("button_exportDVH")
        button.clicked.connect(self.export_csv)

        return button



    def export_csv(self):
        """
        Export DVH as a CSV file in the current directory.
        """
        main_window = self.window
        if not os.path.isdir(main_window.path + '/CSV'):
            os.mkdir(main_window.path + '/CSV')
        dvh2csv(main_window.raw_dvh,
                main_window.path + "/CSV/",
                'DVH_'+ main_window.basicInfo['id'],
                main_window.dataset[0].PatientID)
        SaveReply = QtWidgets.QMessageBox.information(main_window, "Message",
                                            "The DVH Data was saved successfully in your directory!",
                                            QtWidgets.QMessageBox.Ok)
        if SaveReply == QtWidgets.QMessageBox.Ok:
            pass