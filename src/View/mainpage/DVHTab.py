import os
import platform
import threading

import matplotlib.pylab as plt
import numpy as np
from PyQt5 import QtWidgets, QtCore, QtGui
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from src.Controller.PathHandler import resource_path
from src.Model import ImageLoading
from src.Model.CalculateDVHs import dvh2csv
from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.Worker import Worker


class DVHTab(QtWidgets.QWidget):

    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.patient_dict_container = PatientDictContainer()
        self.dvh_calculated = self.patient_dict_container.has_attribute("raw_dvh")

        self.raw_dvh = None
        self.dvh_x_y = None
        self.plot = None

        self.selected_rois = self.patient_dict_container.get("selected_rois")

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

        button_export = QtWidgets.QPushButton("Export DVH")
        button_export.clicked.connect(self.export_csv)

        self.dvh_tab_layout.setAlignment(QtCore.Qt.Alignment())
        self.dvh_tab_layout.addWidget(widget_plot)
        self.dvh_tab_layout.addWidget(button_export, alignment=QtCore.Qt.AlignRight)

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
                #print(self.dvh_x_y[roi])

                # Counts, obtained from the dvh object, give the y axis values
                # (values between 0 and dvh.volume)
                counts = self.dvh_x_y[roi]['counts']


                # Color of the line is the same as the color shown in the left column of the window
                color = self.patient_dict_container.get("roi_color_dict")[roi]
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
        choice = QtWidgets.QMessageBox.question(self, "Calculate DVHs?", "Would you like to calculate DVHs? This may"
                                                                         " take up to several minutes on some systems.",
                                                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)

        if choice == QtWidgets.QMessageBox.Yes:
            progress_window = CalculateDVHProgressWindow(self, QtCore.Qt.WindowTitleHint | QtCore.Qt.WindowCloseButtonHint)
            progress_window.signal_dvh_calculated.connect(self.dvh_calculation_finished)
            progress_window.exec_()

    def dvh_calculation_finished(self):
        # Clear the screen
        self.clear_layout()
        self.dvh_calculated = True
        self.init_layout_dvh()

    def update_plot(self):
        if self.dvh_calculated:
            # Get new list of selected rois that have DVHs calculated
            self.selected_rois = [roi for roi in self.patient_dict_container.get("selected_rois")
                                  if roi in self.raw_dvh.keys()]

            # Clear the current layout
            self.clear_layout()

            # If the DVH has become outdated, show the user an indicator advising them such.
            if self.patient_dict_container.get("dvh_outdated"):
                self.display_outdated_indicator()

            # Re-draw the plot and add to layout
            self.init_layout_dvh()

    def export_csv(self):
        path = self.patient_dict_container.path
        basic_info = self.patient_dict_container.get("basic_info")
        if not os.path.isdir(path + '/CSV'):
            os.mkdir(path + '/CSV')
        dvh2csv(self.raw_dvh,
                path + "/CSV/",
                'DVH_' + basic_info['id'],
                basic_info['id'])
        save_reply = QtWidgets.QMessageBox.information(self, "Message",
                                                      "The DVH Data was saved successfully in your directory!",
                                                      QtWidgets.QMessageBox.Ok)

    def display_outdated_indicator(self):
        self.modified_indicator_widget = QtWidgets.QWidget()
        self.modified_indicator_widget.setContentsMargins(8, 5, 8, 5)
        #self.modified_indicator_widget.setFixedHeight(35)
        modified_indicator_layout = QtWidgets.QHBoxLayout()
        modified_indicator_layout.setAlignment(QtCore.Qt.AlignLeft)

        modified_indicator_icon = QtWidgets.QLabel()
        modified_indicator_icon.setPixmap(QtGui.QPixmap(resource_path("src/res/images/btn-icons/alert_icon.png")))
        modified_indicator_layout.addWidget(modified_indicator_icon)

        modified_indicator_text = QtWidgets.QLabel("Contours have been modified since DVH calculation. Some DVHs may "
                                                   "now be out of date.")
        modified_indicator_text.setStyleSheet("color: red")
        modified_indicator_layout.addWidget(modified_indicator_text)

        self.modified_indicator_widget.setLayout(modified_indicator_layout)

        self.dvh_tab_layout.addWidget(self.modified_indicator_widget, QtCore.Qt.AlignTop)


class CalculateDVHProgressWindow(QtWidgets.QDialog):

    signal_dvh_calculated = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(CalculateDVHProgressWindow, self).__init__(*args, **kwargs)
        layout = QtWidgets.QVBoxLayout()
        text = QtWidgets.QLabel("Calculating DVHs... (This may take several minutes)")
        layout.addWidget(text)
        self.setWindowTitle("Please wait...")
        self.setLayout(layout)

        self.threadpool = QtCore.QThreadPool()
        self.patient_dict_container = PatientDictContainer()

        dataset_rtss = self.patient_dict_container.dataset["rtss"]
        dataset_rtdose = self.patient_dict_container.dataset["rtdose"]
        rois = self.patient_dict_container.get("rois")

        dict_thickness = ImageLoading.get_thickness_dict(dataset_rtss, self.patient_dict_container.dataset)

        interrupt_flag = threading.Event()
        fork_safe_platforms = ['Linux']
        if platform.system() in fork_safe_platforms:
            worker = Worker(ImageLoading.multi_calc_dvh, dataset_rtss, dataset_rtdose, rois, dict_thickness)
        else:
            worker = Worker(ImageLoading.calc_dvhs, dataset_rtss, dataset_rtdose, rois, dict_thickness, interrupt_flag)

        worker.signals.result.connect(self.dvh_calculated)

        self.threadpool.start(worker)

    def dvh_calculated(self, result):
        dvh_x_y = ImageLoading.converge_to_0_dvh(result)
        self.patient_dict_container.set("raw_dvh", result)
        self.patient_dict_container.set("dvh_x_y", dvh_x_y)
        self.signal_dvh_calculated.emit()
        self.close()
