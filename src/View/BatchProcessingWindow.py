import platform
from os.path import expanduser
from src.Controller.PathHandler import resource_path
from PySide6 import QtCore, QtGui, QtWidgets
from src.Controller.BatchProcessingController import BatchProcessingController
from src.View.batchprocessing.DVH2CSVOptions import DVH2CSVOptions
from src.View.batchprocessing.ISO2ROIOptions import ISO2ROIOptions
from src.View.batchprocessing.SUV2ROIOptions import SUV2ROIOptions


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
        self.tabBar().setTabButton(self.tabBar().count()-1,
                                   QtWidgets.QTabBar.LeftSide, checkbox)

    def isChecked(self, index):
        """
        Returns True if the tab checkbox at index is checked.
        :param index: the index of the tab checkbox.
        :return: True if the checkbox at index is checked, False
                 otherwise.
        """
        return self.tabBar().tabButton(
            index,
            QtWidgets.QTabBar.LeftSide).checkState() != QtCore.Qt.Unchecked

    def setCheckState(self, index, check_state):
        """
        Set the checked state of the checkbox at index.
        :param index: index of the checkbox to change the state of.
        :param check_state: QtCore.CheckState, state to set the checkbox
                            to.
        """
        self.tabBar().tabButton(
            index,
            QtWidgets.QTabBar.LeftSide).setCheckState(check_state)


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
        self.directory_input.setStyleSheet(self.stylesheet)

        # Label to display file search status
        self.search_progress_label = QtWidgets.QLabel("No directory is "
                                                  "currently selected.")
        self.search_progress_label.setFont(label_font)

        # Browse button
        self.browse_button = QtWidgets.QPushButton("Change")
        self.browse_button.setObjectName("NormalButton")
        self.browse_button.setStyleSheet(self.stylesheet)

        # == Tab widgets
        # Tab widget
        self.tab_widget = CheckableTabWidget()
        self.tab_widget.tabBar().setObjectName("batch-tabs")
        self.tab_widget.setStyleSheet(self.stylesheet)

        # Tabs
        self.iso2roi_tab = ISO2ROIOptions()
        self.suv2roi_tab = SUV2ROIOptions()
        self.dvh2csv_tab = DVH2CSVOptions()

        # Add tabs to tab widget
        self.tab_widget.addTab(self.iso2roi_tab, "ISO2ROI")
        self.tab_widget.addTab(self.suv2roi_tab, "SUV2ROI")
        self.tab_widget.addTab(self.dvh2csv_tab, "DVH2CSV")

        # == Bottom widgets
        # Info text
        info_text = "Batch Processing will be performed on datasets in the "
        info_text += "selected directory."
        self.info_label = QtWidgets.QLabel(info_text)
        self.info_label.setFont(label_font)

        # Back button
        self.back_button = QtWidgets.QPushButton("Exit")
        self.back_button.setObjectName("BatchExitButton")
        self.back_button.setMaximumWidth(80)
        self.back_button.setStyleSheet(self.stylesheet)
        self.back_button.setProperty("QPushButtonClass", "fail-button")

        # Begin button
        self.begin_button = QtWidgets.QPushButton("Begin")
        self.begin_button.setObjectName("BeginButton")
        self.begin_button.setMaximumWidth(100)
        self.begin_button.setStyleSheet(self.stylesheet)
        self.begin_button.setProperty("QPushButtonClass", "success-button")
        self.begin_button.setEnabled(False)

        # == Set layout
        # Create layouts
        self.layout = QtWidgets.QVBoxLayout()
        self.directory_layout = QtWidgets.QGridLayout()
        self.middle_layout = QtWidgets.QVBoxLayout()
        self.bottom_layout = QtWidgets.QGridLayout()

        # Add top text
        self.layout.addWidget(self.dir_info_label)

        # Add directory widgets
        self.directory_layout.addWidget(self.directory_input)
        self.directory_layout.addWidget(self.browse_button, 0, 1)
        self.directory_layout.addWidget(self.search_progress_label, 1, 0)
        self.layout.addLayout(self.directory_layout)

        # Add middle widgets (patient count, tabs)
        self.middle_layout.addWidget(self.tab_widget)
        self.layout.addLayout(self.middle_layout)

        # Add bottom widgets (buttons)
        self.bottom_layout.addWidget(self.info_label, 0, 0, 2, 4)
        self.bottom_layout.addWidget(self.back_button, 2, 2, 1, 1)
        self.bottom_layout.addWidget(self.begin_button, 2, 3, 1, 1)
        self.layout.addLayout(self.bottom_layout)

        # Connect buttons to functions
        self.browse_button.clicked.connect(self.show_file_browser)
        self.begin_button.clicked.connect(self.confirm_button_clicked)
        self.back_button.clicked.connect(
            lambda: QtCore.QCoreApplication.exit(0))

        # Set window layout
        batch_window_instance.setLayout(self.layout)

        # Create batch processing controller, enable the processing
        self.batch_processing_controller = BatchProcessingController()

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

    def line_edit_changed(self):
        """
        When the line edit box is changed, update related fields,
        start searching the directory.
        """
        self.file_path = self.directory_input.text()
        self.dvh2csv_tab.set_dvh_output_location(self.file_path, False)

        self.begin_button.setEnabled(False)

        self.batch_processing_controller.set_dicom_structure(None)

        self.batch_processing_controller.load_patient_files(
            self.file_path,
            self.search_progress,
            self.search_completed)

    def search_progress(self, progress_update):
        """
        Changed the progress label
        :param progress_update: current progress of file search
        """
        self.search_progress_label.setText("Loading selected directory... ( "
                                           "%s files searched)" %
                                           progress_update)

    def search_completed(self, dicom_structure):
        """
        Called when patient files are loaded
        :param dicom_structure: DICOMStructure
        """
        if dicom_structure:
            self.batch_processing_controller.set_dicom_structure(
                dicom_structure)
            self.begin_button.setEnabled(True)
            self.search_progress_label.setText("%s patients found." %
                                               len(dicom_structure.patients))

            # Update tables
            self.suv2roi_tab.populate_table(dicom_structure)
        else:
            self.search_progress_label.setText("No patients were found.")
            self.batch_processing_controller.set_dicom_structure(None)

    def confirm_button_clicked(self):
        """
        Executes when the confirm button is clicked.
        """
        processes = ['iso2roi', 'suv2roi', 'dvh2csv']
        selected_processes = []
        suv2roi_weights = self.suv2roi_tab.get_patient_weights()

        # Return if SUV2ROI weights is None. Alert user weights are incorrect.
        if suv2roi_weights is None:
            self.show_invalid_weight_dialog()
            return

        # Get the selected processes
        for i in range(self.tab_widget.count()):
            if self.tab_widget.isChecked(i):
                selected_processes.append(processes[i])

        # Save the changed settings
        self.iso2roi_tab.save_isodoses()

        file_directories = {
            "batch_path": self.file_path,
            "dvh_output_path": self.dvh2csv_tab.get_dvh_output_location()}

        # Setup the batch processing controller
        self.batch_processing_controller.set_file_paths(file_directories)
        self.batch_processing_controller.set_processes(selected_processes)
        self.batch_processing_controller.set_suv2roi_weights(suv2roi_weights)

        # Enable processing
        self.batch_processing_controller.start_processing()

    def show_invalid_weight_dialog(self):
        """
        Shows a dialog informing the user that an entered weight in the
        SUV2ROI tab is invalid (either negative or not a number).
        """
        button_reply = \
            QtWidgets.QMessageBox(QtWidgets.QMessageBox.Icon.Warning,
                                  "Invalid Patient Weight",
                                  "Please enter a valid patient weight.",
                                  QtWidgets.QMessageBox.StandardButton.Ok,
                                  self)
        button_reply.button(
            QtWidgets.QMessageBox.StandardButton.Ok).setStyleSheet(
            self.stylesheet)
        button_reply.exec_()
