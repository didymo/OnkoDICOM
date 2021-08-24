import platform, threading
from os.path import expanduser
from src.Controller.PathHandler import resource_path
from PySide6.QtGui import QIcon, QPixmap, QFont
from PySide6.QtWidgets import QFileDialog, QCheckBox
from PySide6.QtCore import QThreadPool
from src.Model.Worker import Worker
from src.Model import DICOMDirectorySearch
from PySide6.QtWidgets import QVBoxLayout, QLabel, QLineEdit, QPushButton, QGridLayout

from src.Model.BatchProcessing import BatchProcessingController


class UIBatchProcessingWindow(object):

    # the ui constructor function
    def setup_ui(self, batch_window_instance):
        if platform.system() == 'Darwin':
            self.stylesheet_path = "res/stylesheet.qss"
        else:
            self.stylesheet_path = "res/stylesheet-win-linux.qss"

        self.stylesheet = open(resource_path(self.stylesheet_path)).read()

        window_icon = QIcon()
        window_icon.addPixmap(QPixmap(resource_path("res/images/icon.ico")), QIcon.Normal, QIcon.Off)

        batch_window_instance.setObjectName("BatchWindowInstance")
        batch_window_instance.setWindowIcon(window_icon)
        batch_window_instance.setWindowTitle("Batch Processing")
        batch_window_instance.resize(840, 530)

        self.file_path = "Select file path.. "
        self.processes = []

        self.label_text = "Select directory to perform batch processing:"
        self.label_font = QFont()
        self.label_font.setPixelSize(14)
        self.info_label = QLabel(self.label_text)
        self.info_label.setFont(self.label_font)
        self.directory_input = QLineEdit()
        self.directory_input.setText(self.file_path)
        self.directory_input.textChanged.connect(self.line_edit_changed)
        self.directory_input.returnPressed.connect(self.scan_directory_for_patients)

        self.browse_button = QPushButton("Change")
        self.browse_button.setObjectName("NormalButton")
        self.browse_button.setStyleSheet(self.stylesheet)
        self.directory_input.setStyleSheet(self.stylesheet)

        # Bottom widgets
        self.bottom_text = "Batch Processing will be performed on files in the above directory. "
        self.bottom_text += "Click 'Refresh' to reload the files from the directory."
        self.bottom_label = QLabel(self.bottom_text)
        self.bottom_label.setFont(self.label_font)
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setObjectName("NormalButton")
        self.refresh_button.setStyleSheet(self.stylesheet)
        self.back_button = QPushButton("Back")
        self.back_button.setObjectName("SkipButton")
        self.back_button.setStyleSheet(self.stylesheet)
        self.confirm_button = QPushButton("Confirm")
        self.confirm_button.setObjectName("ConfirmButton")
        self.confirm_button.setEnabled(False)
        self.confirm_button.setStyleSheet(self.stylesheet)

        self.layout = QVBoxLayout()
        self.directory_layout = QGridLayout()
        self.middle_layout = QGridLayout()
        self.bottom_layout = QGridLayout()

        batch_window_instance.setLayout(self.layout)

        # Add widgets to layout
        self.directory_layout.addWidget(self.info_label, 0, 0, 1, 4)
        self.directory_layout.addWidget(self.directory_input, 1, 0, 1, 3)
        self.directory_layout.addWidget(self.browse_button, 1, 3, 1, 1)

        self.patient_label = QLabel("No patients in the selected directory")
        self.patient_label.setFont(self.label_font)
        self.middle_layout.addWidget(self.patient_label, 0, 0, 1, 4)

        self.iso2roi_checkbox = QCheckBox("ISO2ROI")
        #self.suv2roi_checkbox = QCheckBox("SUV2ROI")

        self.middle_layout.addWidget(self.iso2roi_checkbox)
        #self.middle_layout.addWidget(self.suv2roi_checkbox)

        self.bottom_layout.addWidget(self.bottom_label, 0, 0, 2, 4)
        self.bottom_layout.addWidget(self.refresh_button, 2, 0, 1, 1)
        self.bottom_layout.addWidget(self.back_button, 2, 2, 1, 1)
        self.bottom_layout.addWidget(self.confirm_button, 2, 3, 1, 1)

        self.layout.addLayout(self.directory_layout)
        self.layout.addLayout(self.middle_layout)
        self.layout.addLayout(self.bottom_layout)

        # Connect buttons to functions
        self.browse_button.clicked.connect(self.show_file_browser)
        self.confirm_button.clicked.connect(self.confirm_button_clicked)
        self.refresh_button.clicked.connect(self.scan_directory_for_patients)
        self.back_button.clicked.connect(lambda: batch_window_instance.close())

        self.iso2roi_checkbox.stateChanged.connect(lambda state: self.checkbox_changed("iso2roi", state))
        #self.suv2roi_checkbox.stateChanged.connect(lambda state: self.checkbox_changed("suv2roi", state))

        self.dicom_structure = {}
        self.threadpool = QThreadPool()

    def checkbox_changed(self, identifier, state):
        if state == 2:
            self.processes.append(identifier)
        else:
            self.processes.remove(identifier)

    def show_file_browser(self):
        """
        Show the file browser for selecting a folder for the Onko default directory.
        """
        # Open a file dialog and return chosen directory
        folder = QFileDialog.getExistingDirectory(None, 'Choose Directory ..', '')

        # If chosen directory is nothing (user clicked cancel) set to user home
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


    def confirm_button_clicked(self):
        """
        Executes when the confirm button is clicked.
        """
        batch_processing_controller = BatchProcessingController(self.dicom_structure, self.processes)
        batch_processing_controller.start_processing()

    def on_search_complete(self, dicom_structure):
        """
        Executes once the directory search is complete.
        :param dicom_structure: DICOMStructure object constructed by the directory search.
        """
        if dicom_structure is None:  # dicom_structure will be None if function was interrupted.
            return
        self.confirm_button.setEnabled(True)

        self.patient_count = len(dicom_structure.patients)
        self.patient_label.setText("There are {} patient(s) in this directory".format(self.patient_count))
        self.dicom_structure = dicom_structure

    def search_progress(self):
        self.patient_label.setText("Loading files .. ")

    def scan_directory_for_patients(self):
        self.confirm_button.setEnabled(False)
        if self.file_path != "":
            interrupt_flag = threading.Event()

            # Then, create a new thread that will load the selected folder
            worker = Worker(DICOMDirectorySearch.get_dicom_structure, self.file_path,
                            interrupt_flag, progress_callback=True)

            worker.signals.result.connect(self.on_search_complete)
            worker.signals.progress.connect(self.search_progress)

            # Execute the thread
            self.threadpool.start(worker)
        else:
            self.patient_label.setText("No patients in the selected directory")