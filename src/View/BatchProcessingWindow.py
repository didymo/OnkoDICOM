import platform, threading
from os.path import expanduser
from src.Controller.PathHandler import resource_path
from PySide6 import QtCore, QtGui, QtWidgets
from src.Model import DICOMDirectorySearch
from src.Model.BatchProcessing import BatchProcessingController
from src.Model.Worker import Worker
from src.View.batchprocessing.ISO2ROIOptions import ISO2ROIOptions


class CheckableTabWidget(QtWidgets.QTabWidget):
    """
    Creates a clickable tab widget.
    """
    checked_list = []

    def addTab(self, widget, title):
        """
        Add a tab to the tab bar.
        :param widget: the widget to add to the tab bar.
        :param title: string to display on the tab bar.
        """
        QtWidgets.QTabWidget.addTab(self, widget, title)
        checkbox = QtWidgets.QCheckBox()
        self.checked_list.append(checkbox)
        self.tabBar().setTabButton(self.tabBar().count()-1, QtWidgets.QTabBar.LeftSide, checkbox)

    def isChecked(self, index):
        """
        Returns True if the tab checkbox at index is checked.
        :param index: the index of the tab checkbox.
        :return: True if the checkbox at index is checked, False
                 otherwise.
        """
        return self.tabBar().tabButton(index, QtWidgets.QTabBar.LeftSide).checkState() != QtCore.Qt.Unchecked

    def setCheckState(self, index, check_state):
        """
        Set the checked state of the checkbox at index.
        :param index: index of the checkbox to change the state of.
        :param check_state: QtCore.CheckState, state to set the checkbox
                            to.
        """
        self.tabBar().tabButton(index, QtWidgets.QTabBar.LeftSide).setCheckState(check_state)


class UIBatchProcessingWindow(object):
    """
    This class contains the user interface for the batch processing
    window.
    """
    def setup_ui(self, batch_window_instance):
        """
        Sets up the UI for the batch processing window.
        """
        # Get the appropriate stylesheet
        if platform.system() == 'Darwin':
            self.stylesheet_path = "res/stylesheet.qss"
        else:
            self.stylesheet_path = "res/stylesheet-win-linux.qss"
        self.stylesheet = open(resource_path(self.stylesheet_path)).read()

        # Create class variables
        self.file_path = "Select file path..."

        # Label font
        label_font = QtGui.QFont()
        label_font.setPixelSize(14)

        # Set the window icon
        window_icon = QtGui.QIcon()
        window_icon.addPixmap(
            QtGui.QPixmap(resource_path("res/images/icon.ico")),
            QtGui.QIcon.Normal, QtGui.QIcon.Off)

        # Set window properties
        batch_window_instance.setObjectName("BatchWindowInstance")
        batch_window_instance.setWindowIcon(window_icon)
        batch_window_instance.setWindowTitle("Batch Processing")
        batch_window_instance.resize(840, 530)

        # == Directory widgets
        # Directory label
        dir_label_text = "Select directory to perform batch processing on:"
        self.dir_info_label = QtWidgets.QLabel(dir_label_text)
        self.dir_info_label.setFont(label_font)

        # Directory line edit
        self.directory_input = QtWidgets.QLineEdit()
        self.directory_input.setText(self.file_path)
        self.directory_input.textChanged.connect(self.line_edit_changed)
        self.directory_input.returnPressed.connect(
            self.scan_directory_for_patients)
        self.directory_input.setStyleSheet(self.stylesheet)

        # Browse button
        self.browse_button = QtWidgets.QPushButton("Change")
        self.browse_button.setObjectName("NormalButton")
        self.browse_button.setStyleSheet(self.stylesheet)

        # == Tab widgets
        # Tab widget
        self.tab_widget = CheckableTabWidget()
        self.tab_widget.setStyleSheet(self.stylesheet)

        # Tabs
        self.iso2roi_tab = ISO2ROIOptions()
        self.suv2roi_tab = QtWidgets.QLabel("Coming soon")

        # Add tabs to tab widget
        self.tab_widget.addTab(self.iso2roi_tab, "ISO2ROI")
        self.tab_widget.addTab(self.suv2roi_tab, "SUV2ROI")

        # == Bottom widgets
        # Info text
        info_text = "Batch Processing will be performed on datasets in the "
        info_text += "selected directory. Click 'Refresh' to reload datasets "
        info_text += "in the directory."
        self.info_label = QtWidgets.QLabel(info_text)
        self.info_label.setFont(label_font)

        # Refresh button
        self.refresh_button = QtWidgets.QPushButton("Refresh")
        self.refresh_button.setObjectName("NormalButton")
        self.refresh_button.setStyleSheet(self.stylesheet)

        # Back button
        self.back_button = QtWidgets.QPushButton("Exit")
        self.back_button.setObjectName("BatchExitButton")
        self.back_button.setStyleSheet(self.stylesheet)
        self.back_button.setProperty("QPushButtonClass", "fail-button")

        # Confirm button
        self.confirm_button = QtWidgets.QPushButton("Confirm")
        self.confirm_button.setObjectName("ConfirmButton")
        self.confirm_button.setEnabled(False)
        self.confirm_button.setStyleSheet(self.stylesheet)
        self.confirm_button.setProperty("QPushButtonClass", "success-button")

        # == Set layout
        # Create layouts
        self.layout = QtWidgets.QVBoxLayout()
        self.directory_layout = QtWidgets.QHBoxLayout()
        self.middle_layout = QtWidgets.QVBoxLayout()
        self.bottom_layout = QtWidgets.QGridLayout()

        # Add top text
        self.layout.addWidget(self.dir_info_label)

        # Add directory widgets
        self.directory_layout.addWidget(self.directory_input)
        self.directory_layout.addWidget(self.browse_button)
        self.layout.addLayout(self.directory_layout)

        # Add middle widgets (patient count, tabs)
        self.patient_label = \
            QtWidgets.QLabel("No patients in the selected directory")
        self.patient_label.setFont(label_font)
        self.middle_layout.addWidget(self.patient_label)
        self.middle_layout.addWidget(self.tab_widget)
        self.layout.addLayout(self.middle_layout)

        # Add bottom widgets (buttons)
        self.bottom_layout.addWidget(self.info_label, 0, 0, 2, 4)
        self.bottom_layout.addWidget(self.refresh_button, 2, 0, 1, 1)
        self.bottom_layout.addWidget(self.back_button, 2, 2, 1, 1)
        self.bottom_layout.addWidget(self.confirm_button, 2, 3, 1, 1)
        self.layout.addLayout(self.bottom_layout)

        # Connect buttons to functions
        self.browse_button.clicked.connect(self.show_file_browser)
        self.confirm_button.clicked.connect(self.confirm_button_clicked)
        self.refresh_button.clicked.connect(self.scan_directory_for_patients)
        self.back_button.clicked.connect(lambda: batch_window_instance.close())

        # Set window layout
        batch_window_instance.setLayout(self.layout)

        # Variables to store the DICOM structure and the thread
        self.dicom_structure = {}
        self.threadpool = QtCore.QThreadPool()

    def show_file_browser(self):
        """
        Show the file browser for selecting a folder for the Onko
        default directory.
        """
        # Open a file dialog and return chosen directory
        folder = \
            QtWidgets.QFileDialog.getExistingDirectory(None,
                                                       'Choose Directory ..',
                                                       '')

        # If chosen directory is nothing (user clicked cancel) set to
        # user home
        if folder == "":
            folder = expanduser("~")

        # Update file path
        self.file_path = folder

        # Update directory text
        self.directory_input.setText(self.file_path)
        self.scan_directory_for_patients()

    def line_edit_changed(self):
        """
        When the line edit box is changed, update related fields.
        """
        self.confirm_button.setEnabled(False)
        self.file_path = self.directory_input.text()

    def search_progress(self):
        self.patient_label.setText("Loading files .. ")

    def scan_directory_for_patients(self):
        """
        Scans the selected directory for DICOM patients.
        """
        self.confirm_button.setEnabled(False)
        if self.file_path != "":
            interrupt_flag = threading.Event()

            # Then, create a new thread that will load the selected folder
            worker = Worker(DICOMDirectorySearch.get_dicom_structure,
                            self.file_path,
                            interrupt_flag, progress_callback=True)

            worker.signals.result.connect(self.on_search_complete)
            worker.signals.progress.connect(self.search_progress)

            # Execute the thread
            self.threadpool.start(worker)
        else:
            self.patient_label.setText("No patients in the selected directory")

    def on_search_complete(self, dicom_structure):
        """
        Executes once the directory search is complete.
        :param dicom_structure: DICOMStructure object constructed by the
                                directory search.
        """
        # dicom_structure will be None if function was interrupted
        if dicom_structure is None:
            return
        self.confirm_button.setEnabled(True)

        self.patient_count = len(dicom_structure.patients)
        text = "There are {} patient(s) in this directory".format(
            self.patient_count)
        self.patient_label.setText(text)
        self.dicom_structure = dicom_structure

    def confirm_button_clicked(self):
        """
        Executes when the confirm button is clicked.
        """
        processes = ['iso2roi', 'suv2roi']
        selected_processes = []

        # Get the selected processes
        for i in range(self.tab_widget.count()):
            if self.tab_widget.isChecked(i):
                selected_processes.append(processes[i])

        # Save the changed settings
        self.iso2roi_tab.save_isodoses()

        batch_processing_controller =\
            BatchProcessingController(self.dicom_structure, selected_processes)
        batch_processing_controller.start_processing()
