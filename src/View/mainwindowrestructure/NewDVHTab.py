from PyQt5 import QtWidgets, QtCore
from matplotlib.backends.backend_template import FigureCanvas
import matplotlib.pylab as plt
from pandas import np

from src.Model.PatientDictContainer import PatientDictContainer


class NewDVHTab(QtWidgets.QWidget):

    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.patient_dict_container = PatientDictContainer()
        self.dvh_calculated = self.patient_dict_container.get("raw_dvh")
        print(self.dvh_calculated)

        self.raw_dvh = None
        self.dvh_x_y = None
        self.plot = None

        self.selected_rois = self.patient_dict_container.get("selected_rois")
        self.roi_color = self.patient_dict_container.get("roi_color_dict")

        self.dvh_tab_layout = QtWidgets.QVBoxLayout()

        # Construct the layout based on whether or not the DVH has already been calculated.
        if self.dvh_calculated:
            self.init_layout_dvh()
        else:
            self.init_layout_no_dvh()

        self.setLayout(self.dvh_tab_layout)

    def init_layout_dvh(self):
        self.raw_dvh = self.patient_dict_container.get("raw_dvh")
        self.dvh_x_y = self.patient_dict_container.get("dvh_x_y")

        self.plot = self.plot_dvh()
        widget_plot = FigureCanvas(self.plot)

        self.dvh_tab_layout.addWidget(widget_plot)

    def init_layout_no_dvh(self):
        button_calc_dvh = QtWidgets.QPushButton("Calculate DVH")
        button_calc_dvh.clicked.connect(self.prompt_calc_dvh)

        self.dvh_tab_layout.setAlignment(QtCore.Qt.AlignCenter)
        self.dvh_tab_layout.addWidget(button_calc_dvh)

    def clear_layout(self):
        for i in reversed(range(self.dvh_tab_layout.count())):
            self.dvh_tab_layout.itemAt(i).widget().setParent(None)

    def plot_dvh(self):
        """
        :return: DVH plot using Matplotlib library.
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
                color_R = color.red() / 255
                color_G = color.green() / 255
                color_B = color.blue() / 255

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

    def prompt_calc_dvh(self):
        # TODO this will confirm if DVH is to be calculated, then bring up a progress while the DVH calculates
        # once the DVH is calculated, clear the layout and call init_layout_dvh
        pass

    def update_plot(self):
        # Get new list of selected rois
        self.selected_rois = self.patient_dict_container.get("selected_rois")

        # Clear the current layout
        self.clear_layout()

        # Re-draw the plot and add to layout
        self.init_layout_dvh()
