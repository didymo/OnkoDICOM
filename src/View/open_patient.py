import threading
import time

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QCoreApplication, QThreadPool
from PyQt5.QtWidgets import QTreeWidgetItem, QMessageBox
from PyQt5.Qt import Qt

from src.Model import DICOMDirectorySearch
from src.Model.Worker import Worker
from src.View.ProgressWindow import ProgressWindow
from src.View.resources_open_patient_rc import *


class UIOpenPatientWindow(object):
    patient_info_initialized = QtCore.pyqtSignal(tuple)

    def setup_ui(self, main_window):
        stylesheet = open("src/res/stylesheet.qss").read()

        main_window.setObjectName("MainWindow")
        main_window.setStyleSheet(stylesheet)
        main_window.setFixedSize(700, 550)
        #main_window.setFixedSize(750, 570) # Window size change
        main_window.setWindowTitle("OnkoDICOM")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("src/res/images/icon.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        main_window.setWindowIcon(icon)
        main_window.setAutoFillBackground(False)

        # Create threadpool for multithreading
        self.threadpool = QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

        # Create interrupt event for stopping the directory search
        self.interrupt_flag = threading.Event()

        self.central_widget = QtWidgets.QWidget(main_window)
        self.central_widget.setObjectName("centralwidget")

        # self.grid_layout = QtWidgets.QGridLayout(self.central_widget)
        # self.grid_layout.setObjectName("gridLayout")

        # Frame
        self.frame = QtWidgets.QFrame(self.central_widget)
        self.frame.setGeometry(QtCore.QRect(40, 10, 611, 101))
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")

        self.path_text_browser = QtWidgets.QLineEdit(self.frame)  # changed to text edit instead of browser
        self.path_text_browser.setPlaceholderText("Your Path:")
        self.path_text_browser.setGeometry(QtCore.QRect(6, 40, 500, 26))
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Ignored)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.path_text_browser.sizePolicy().hasHeightForWidth())
        self.path_text_browser.setSizePolicy(size_policy)
        self.path_text_browser.setObjectName("pathTextBrowser")
        # self.grid_layout.addWidget(self.path_text_browser, 1, 1, 1, 1)

        self.choose_button = QtWidgets.QPushButton(self.frame)
        self.choose_button.setObjectName("chooseButton")
        self.choose_button.setGeometry(QtCore.QRect(521, 40, 90, 26))
        self.choose_button.setText("Choose")
        self.choose_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.choose_button.clicked.connect(self.choose_button_clicked)
        # self.grid_layout.addWidget(self.choose_button, 1, 2, 1, 1)

        self.choose_label = QtWidgets.QLabel(self.frame)
        self.choose_label.setGeometry(QtCore.QRect(6, 10, 571, 16))
        self.choose_label.setObjectName("choose_label")
        self.choose_label.setText("<html><head/><body><p><span style=\" font-size:10pt;\">Choose the file path of a "
                                  "folder containing DICOM files to create the Patient file "
                                  "directory:</span></p></body></html>")
        # self.grid_layout.addWidget(self.choose_label, 0, 1, 1, 3)

        self.patient_file_label = QtWidgets.QLabel(self.frame)
        self.patient_file_label.setGeometry(QtCore.QRect(6, 76, 571, 16))
        self.patient_file_label.setObjectName("patient_file_label")
        self.patient_file_label.setText("<html><head/><body><p><span style=\" font-size:10pt;\">Patient File "
                                        "directory shown below once file path chosen. Please select the file(s) you "
                                        "want to open:</span></p></body></html>")
        # self.grid_layout.addWidget(self.patient_file_label, 6, 1, 1, 3)

        #self.path_label = QtWidgets.QLabel(self.frame)
        #self.path_label.setGeometry(QtCore.QRect(10, 40, 47, 13))
        #self.path_label.setObjectName("path_label")
        #self.path_label.setText("<html><head/><body><p><span style=\" font-size:10pt;\">Path:</span></p></body></html>")
        #self.grid_layout.addWidget(self.path_label, 1, 0, 1, 1)

        # Frame 2
        self.frame_2 = QtWidgets.QFrame(self.central_widget)
        self.frame_2.setGeometry(QtCore.QRect(44, 130, 611, 411))
        self.frame_2.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_2.setObjectName("frame_2")

        self.cancel_button = QtWidgets.QPushButton(self.frame_2)
        self.cancel_button.setObjectName("cancelButton")
        self.cancel_button.setGeometry(QtCore.QRect(414, 365, 90, 26))
        self.cancel_button.setText("Exit")
        self.cancel_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.cancel_button.clicked.connect(self.cancel_button_clicked) # Signal Closing Application
        #self.grid_layout.addWidget(self.cancel_button, 9, 3, 1, 1)

        self.confirm_Button = QtWidgets.QPushButton(self.frame_2)
        self.confirm_Button.setObjectName("confirmButton")
        self.confirm_Button.setText("Confirm")
        self.confirm_Button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.confirm_Button.setGeometry(QtCore.QRect(520, 365, 90, 36))
        self.confirm_Button.clicked.connect(self.confirm_button_clicked)
        #self.grid_layout.addWidget(self.confirm_Button, 9, 4, 1, 1)

        self.stop_button = QtWidgets.QPushButton(self.frame_2)
        self.stop_button.setObjectName("stopButton")
        self.stop_button.setText("Stop Search")
        self.stop_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.stop_button.setGeometry(QtCore.QRect(6, 365, 120, 26))
        self.stop_button.clicked.connect(self.stop_button_clicked)
        self.stop_button.setVisible(False)  # Button doesn't show until a search commences

        self.selected_directory_label = QtWidgets.QLabel(self.frame_2)
        self.selected_directory_label.setObjectName("selected_directory_label")
        self.selected_directory_label.setGeometry(QtCore.QRect(6, 330, 541, 16))
        self.selected_directory_label.setText("<html><head/><body><p><span style=\" font-size:10pt;\">The selected "
                                              "directory(s) above will be opened in the OnkoDICOM "
                                              "program.</span></p></body></html>")
        #self.grid_layout.addWidget(self.selected_directory_label, 9, 1, 1, 2)

        self.tree_widget = QtWidgets.QTreeWidget(self.frame_2)
        self.tree_widget.setGeometry(QtCore.QRect(0, 0, 611, 321))
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.setHeaderLabels([""])
        #self.grid_layout.addWidget(self.tree_widget, 7, 1, 1, 1)

        main_window.setCentralWidget(self.central_widget)
        self.status_bar = QtWidgets.QStatusBar(main_window)
        self.status_bar.setObjectName("statusbar")
        self.status_bar.setSizeGripEnabled(False)  # Remove expanding window option
        main_window.setStatusBar(self.status_bar)

        QtCore.QMetaObject.connectSlotsByName(main_window)

    def cancel_button_clicked(self):
        QCoreApplication.exit(0)

    def choose_button_clicked(self):
        """
        Executes when the choose button is clicked.
        Gets filepath from the user and loads all files and subdirectories.
        """
        # Get folder path from pop up dialog box
        self.filepath = QtWidgets.QFileDialog.getExistingDirectory(None, 'Select patient folder...', '')
        self.path_text_browser.setText(self.filepath)

        # Proceed if a folder was selected
        if self.filepath != "":
            # Update the QTreeWidget to reflect data being loaded
            # First, clear the widget of any existing data
            self.tree_widget.clear()

            # Next, update the tree widget
            self.tree_widget.addTopLevelItem(QTreeWidgetItem(["Loading selected directory..."]))

            # The choose button is disabled until the thread finishes executing
            self.choose_button.setEnabled(False)

            # Reveals the Stop Search button for the duration of the search
            self.stop_button.setVisible(True)

            # The interrupt flag is then un-set if a previous search has been stopped.
            self.interrupt_flag.clear()

            # Then, create a new thread that will load the selected folder
            worker = Worker(DICOMDirectorySearch.get_dicom_structure, self.filepath, self.interrupt_flag)
            worker.signals.result.connect(self.on_search_complete)
            worker.signals.progress.connect(self.search_progress)

            # Execute the thread
            self.threadpool.start(worker)

    def stop_button_clicked(self):
        self.interrupt_flag.set()

    def search_progress(self, progress_update):
        """
        Current progress of the file search.
        """
        self.tree_widget.clear()
        self.tree_widget.addTopLevelItem(QTreeWidgetItem(["Loading selected directory... (%s files searched)"
                                                          % progress_update]))

    def on_search_complete(self, dicom_structure):
        """
        Executes once the directory search is complete.
        :param dicom_structure: DICOMStructure object constructed by the directory search.
        """
        self.choose_button.setEnabled(True)
        self.stop_button.setVisible(False)
        self.tree_widget.clear()

        if dicom_structure is None:  # dicom_structure will be None if function was interrupted.
            return

        for patient_item in dicom_structure.get_tree_items_list():
            self.tree_widget.addTopLevelItem(patient_item)

        if len(dicom_structure.patients) == 0:
            QMessageBox.about(self, "No files found", "Selected directory contains no DICOM files.")

    def confirm_button_clicked(self):
        """
        Begins loading of the selected files.
        """
        selected_files = []
        for item in self.get_checked_leaves():
            selected_files += item.dicom_object.get_files()

        if len(selected_files) > 0:
            self.progress_window = ProgressWindow(self, QtCore.Qt.WindowTitleHint)
            self.progress_window.signal_loaded.connect(self.on_loaded)
            self.progress_window.signal_error.connect(self.on_loading_error)

            self.progress_window.start_loading(selected_files)
            self.progress_window.exec_()
        else:
            QMessageBox.about(self, "Unable to open selection", "No files selected.")

    def on_loaded(self, results):
        """
        Executes when the progress bar finishes loaded the selected files.
        """
        self.patient_info_initialized.emit(results)

    def on_loading_error(self, error_code):
        """
        Error handling for progress window.
        """
        if error_code == 0:
            QMessageBox.about(self.progress_window, "Unable to open selection",
                              "Selected files cannot be opened as they are not a DICOM-RT set.")
            self.progress_window.close()
        elif error_code == 1:
            QMessageBox.about(self.progress_window, "Unable to open selection",
                              "Selected files cannot be opened as they contain unsupported DICOM classes.")
            self.progress_window.close()

    def get_checked_leaves(self):
        """
        :return: A list of all QTreeWidgetItems in the QTreeWidget that are both leaves and checked.
        """
        checked_items = []

        def recurse(parent_item: QTreeWidgetItem):
            for i in range(parent_item.childCount()):
                child = parent_item.child(i)
                grand_children = child.childCount()
                if grand_children > 0:
                    recurse(child)
                else:
                    if child.checkState(0) == Qt.Checked:
                        checked_items.append(child)

        recurse(self.tree_widget.invisibleRootItem())
        return checked_items


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = UIOpenPatientWindow()
    ui.setup_ui(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
