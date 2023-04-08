import platform
import os

from PySide6 import QtGui, QtCore, QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSizePolicy, QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QLineEdit, QMessageBox
from src.Model.Configuration import Configuration, SqlError

from src.Controller.PathHandler import resource_path


class UIFirstTimeWelcomeWindow(object):
    configured = QtCore.Signal(str)

    # the ui constructor function
    def setup_ui(self, first_time_welcome_window_instance):
        self.filepath = ""
        if platform.system() == 'Darwin':
            self.stylesheet_path = "res/stylesheet.qss"
        else:
            self.stylesheet_path = "res/stylesheet-win-linux.qss"

        window_icon = QtGui.QIcon()
        window_icon.addPixmap(QtGui.QPixmap(resource_path("res/images/icon.ico")), QtGui.QIcon.Normal, QtGui.QIcon.Off)  # adding icon
        first_time_welcome_window_instance.setObjectName("FirstTimeWelcomeWindowInstance")
        first_time_welcome_window_instance.setWindowIcon(window_icon)
        first_time_welcome_window_instance.setFixedSize(840, 530)

        # Create a vertical layout to manage layout in a vertical manner
        self.window_vertical_layout_box = QVBoxLayout()
        self.window_vertical_layout_box.setObjectName("FirstTimeWelcomeWindowInstanceVerticalLayoutBox")

        # Create a horizontal box to hold the Onko logo & welcome message
        self.first_time_welcome_logo_message_horizontal_box = QHBoxLayout()
        self.first_time_welcome_logo_message_horizontal_box.setObjectName("FirstTimeWelcomeLogoMessageBox")

        # Set up the Logo Holder
        self.logo_holder = QtWidgets.QHBoxLayout()
        self.first_time_welcome_logo = QtWidgets.QLabel()
        self.first_time_welcome_logo.setPixmap(QtGui.QPixmap(resource_path("res/images/image.png")))
        self.first_time_welcome_logo.setScaledContents(True)
        self.first_time_welcome_logo.setObjectName("FirstTimeWelcomeWindowLogo")
        self.first_time_welcome_logo.setFixedSize(240, 130)
        self.logo_holder.addWidget(self.first_time_welcome_logo)
        self.first_time_welcome_logo_message_horizontal_box.addLayout(self.logo_holder)

        # Create a vertical box to hold the welcome message
        self.first_time_welcome_message_vertical_box = QVBoxLayout()
        self.first_time_welcome_message_vertical_box.setObjectName("FirstTimeWelcomeWindowWelcomeMessage")

        # Set up the Label
        self.first_time_welcome_message_label = QtWidgets.QLabel()
        self.first_time_welcome_message_label.setObjectName("FirstTimeWelcomeWindowLabel")
        self.first_time_welcome_message_label.setAlignment(Qt.AlignLeft)
        self.first_time_welcome_message_vertical_box.addWidget(self.first_time_welcome_message_label)

        # Set up the Slogan
        self.first_time_welcome_message_slogan = QtWidgets.QLabel()
        self.first_time_welcome_message_slogan.setObjectName("FirstTimeWelcomeWindowSlogan")
        self.first_time_welcome_message_slogan.setAlignment(Qt.AlignLeft)
        self.first_time_welcome_message_slogan.setWordWrap(True)
        self.first_time_welcome_message_vertical_box.addWidget(self.first_time_welcome_message_slogan)

        self.first_time_welcome_message_slogan_widget = QWidget()
        self.first_time_welcome_message_slogan_widget.setLayout(self.first_time_welcome_message_vertical_box)
        self.first_time_welcome_logo_message_horizontal_box.addWidget(self.first_time_welcome_message_slogan_widget)

        self.first_time_welcome_logo_message_widget = QWidget()
        self.first_time_welcome_logo_message_widget.setLayout(self.first_time_welcome_logo_message_horizontal_box)
        self.window_vertical_layout_box.addWidget(self.first_time_welcome_logo_message_widget)

        # Create a label to prompt the user to enter the path to the default directory
        self.first_time_welcome_default_dir_prompt = QtWidgets.QLabel()
        self.first_time_welcome_default_dir_prompt.setObjectName("FirstTimeWelcomeWindowPrompt")
        self.first_time_welcome_default_dir_prompt.setAlignment(Qt.AlignLeft)
        self.window_vertical_layout_box.addWidget(self.first_time_welcome_default_dir_prompt);

        # Create a horizontal box to hold the input box for the directory and the choose button
        self.first_time_welcome_input_horizontal_box = QHBoxLayout()
        self.first_time_welcome_input_horizontal_box.setObjectName("FirstTimeWelcomeWindowInputHorizontalBox")

        # Create a textbox to contain the path to the default directory
        self.first_time_welcome_input_box = UIFirstTimeUserDragAndDropEvent(self)

        self.first_time_welcome_input_box.setObjectName("FirstTimeWelcomeWindowInputBox")
        self.first_time_welcome_input_box.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding))
        self.first_time_welcome_input_horizontal_box.addWidget(self.first_time_welcome_input_box)

        # Create a choose button to open the file dialog
        self.first_time_welcome_choose_button = QPushButton()
        self.first_time_welcome_choose_button.setObjectName("FirstTimeWelcomeWindowChooseButton")
        self.first_time_welcome_choose_button.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding))
        self.first_time_welcome_choose_button.resize(self.first_time_welcome_choose_button.sizeHint().width(),
                                                         self.first_time_welcome_input_box.height())
        self.first_time_welcome_choose_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.first_time_welcome_input_horizontal_box.addWidget(self.first_time_welcome_choose_button)
        self.first_time_welcome_choose_button.clicked.connect(self.choose_button_clicked)

        # Create a widget to hold the input field
        self.first_time_welcome_input_widget = QWidget()
        self.first_time_welcome_input_horizontal_box.setStretch(0, 4)
        self.first_time_welcome_input_widget.setLayout(self.first_time_welcome_input_horizontal_box)
        self.window_vertical_layout_box.addWidget(self.first_time_welcome_input_widget)
        self.window_vertical_layout_box.addStretch(1)


        # Create widgets for the clinical data CSV file path
        self.clinical_data_csv_dir_label = QtWidgets.QLabel()
        self.clinical_data_csv_dir_label.setObjectName("ClinicalDataCSVPrompt")
        self.clinical_data_csv_dir_label.setAlignment(Qt.AlignLeft)
        self.window_vertical_layout_box.addWidget(
            self.clinical_data_csv_dir_label)

        # Create a horizontal box to hold the input box for the
        # directory and the choose button
        self.clinical_data_csv_horizontal_box = QHBoxLayout()
        self.clinical_data_csv_horizontal_box.setObjectName(
            "ClinicalDataCSVHorizontalBox")

        # Create a textbox to contain the path to the default directory
        self.clinical_data_csv_input_box = \
            UIFirstTimeUserDragAndDropEvent(self)

        self.clinical_data_csv_input_box.setObjectName(
            "ClinicalDataCSVInputBox")
        self.clinical_data_csv_input_box.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding,
                        QSizePolicy.MinimumExpanding))
        self.clinical_data_csv_horizontal_box.addWidget(
            self.clinical_data_csv_input_box)

        # Create a choose button to open the file dialog
        self.clinical_data_csv_choose_button = QPushButton()
        self.clinical_data_csv_choose_button.setObjectName(
            "ClinicalDataCSVChooseButton")
        self.clinical_data_csv_choose_button.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding,
                        QSizePolicy.MinimumExpanding))
        self.clinical_data_csv_choose_button.resize(
            self.clinical_data_csv_choose_button.sizeHint().width(),
            self.clinical_data_csv_input_box.height())
        self.clinical_data_csv_choose_button.setCursor(
            QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.clinical_data_csv_horizontal_box.addWidget(
            self.clinical_data_csv_choose_button)
        self.clinical_data_csv_choose_button.clicked.connect(
            self.change_clinical_data_csv_button_clicked)

        # Create a widget to hold the input field
        self.clinical_data_input_widget = QWidget()
        self.clinical_data_csv_horizontal_box.setStretch(0, 4)
        self.clinical_data_input_widget.setLayout(
            self.clinical_data_csv_horizontal_box)
        self.window_vertical_layout_box.addWidget(
            self.clinical_data_input_widget)
        self.window_vertical_layout_box.addStretch(1)

        # Create a horizontal box to hold the Skip and Confirm button
        self.first_time_window_configure_actions_horizontal_box = QHBoxLayout()
        self.first_time_window_configure_actions_horizontal_box.setObjectName(
            "FirstTimeWelcomeWindowConfigureActionsHorizontalBox"
        )
        self.first_time_window_configure_actions_horizontal_box.addStretch(1)

        # Add a button to skip the configuration setting
        self.skip_button = QPushButton()
        self.skip_button.setObjectName("SkipButton")
        self.skip_button.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding))
        self.skip_button.resize(self.skip_button.sizeHint().width(),
                                self.skip_button.sizeHint().height())
        self.skip_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.skip_button.setProperty("QPushButtonClass", "fail-button")
        self.first_time_window_configure_actions_horizontal_box.addWidget(self.skip_button)

        # Add a button to save the default directory
        self.save_dir_button = QPushButton()
        self.save_dir_button.setObjectName("SaveDirButton")
        self.save_dir_button.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding))
        self.save_dir_button.resize(self.save_dir_button.sizeHint().width(),
                                    self.save_dir_button.sizeHint().height())
        self.save_dir_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.save_dir_button.clicked.connect(self.save_options)
        self.save_dir_button.setProperty("QPushButtonClass", "success-button")
        self.first_time_window_configure_actions_horizontal_box.addWidget(self.save_dir_button)

        # Create a widget to house all of the actions button for first-time window
        self.first_time_window_configure_actions_widget = QWidget()
        self.first_time_window_configure_actions_widget.setLayout(
            self.first_time_window_configure_actions_horizontal_box)
        self.window_vertical_layout_box.addWidget(self.first_time_window_configure_actions_widget)

        self.first_time_window_instance_central_widget = QWidget()
        self.first_time_window_instance_central_widget.setLayout(self.window_vertical_layout_box)
        first_time_welcome_window_instance.setCentralWidget(self.first_time_window_instance_central_widget)

        # Set the current stylesheet to the instance and connect it back to the caller through slot
        _stylesheet = open(resource_path(self.stylesheet_path)).read()
        first_time_welcome_window_instance.setStyleSheet(_stylesheet)
        self.retranslate_ui(first_time_welcome_window_instance)
        QtCore.QMetaObject.connectSlotsByName(first_time_welcome_window_instance)

    # this function inserts all the text in the first time page
    def retranslate_ui(self, first_time_welcome_window_instance):
        _translate = QtCore.QCoreApplication.translate
        first_time_welcome_window_instance.setWindowTitle(
            _translate("FirstTimeWelcomeWindowInstance", "OnkoDICOM - First-time User Setting"))
        self.first_time_welcome_message_label.setText(_translate("FirstTimeWelcomeWindowInstance", "Welcome to OnkoDICOM!"))
        self.first_time_welcome_message_slogan.setText(_translate("FirstTimeWelcomeWindowInstance",
                                                      "OnkoDICOM - the solution for producing data for analysis from your oncology plans and scans."))
        self.first_time_welcome_default_dir_prompt.setText(_translate("FirstTimeWelcomeWindowInstance","Choose the path of the default directory containing all DICOM files:"))
        self.first_time_welcome_input_box.setPlaceholderText(_translate("FirstTimeWelcomeWindowInstance",
                                                                            "Enter DICOM Files Path (For example, C:\\path\\to\\your\\DICOM\\Files)"))
        self.first_time_welcome_choose_button.setText(_translate("FirstTimeWelcomeWindowInstance", "Choose"))

        # Clinical data CSV widgets
        self.clinical_data_csv_dir_label.setText(
            _translate("FirstTimeWelcomeWindowInstance",
                       "Choose the CSV file containing patient clinical data:")
        )
        self.clinical_data_csv_input_box.setPlaceholderText(
            _translate("FirstTimeWelcomeWindowInstance",
                       "Enter CSV File Path (for example, C:\\CSV\\file.csv)"))
        self.clinical_data_csv_choose_button.setText(
            _translate("FirstTimeWelcomeWindowInstance", "Choose"))

        self.save_dir_button.setText(_translate("FirstTimeWelcomeWindowInstance", "Confirm"))
        self.skip_button.setText(_translate("FirstTimeWelcomeWindowInstance", "Skip"))

    def save_options(self):
        """
        Saves options selected in the first time welcome window.
        """
        self.filepath = self.first_time_welcome_input_box.text()
        self.csv_path = self.clinical_data_csv_input_box.text()
        if self.filepath == "" and self.csv_path == "":
            QMessageBox.about(self, "Unable to proceed",
                              "No directories selected.")
        elif not os.path.exists(self.filepath) or not \
                os.path.exists(self.csv_path):
            QMessageBox.about(self, "Unable to proceed",
                              "Directories do not exist")
        else:
            config = Configuration()
            try:
                config.update_default_directory(self.filepath)

                # Update CSV path if it exists
                if self.csv_path != "" and os.path.exists(self.csv_path):
                    config.update_clinical_data_csv_dir(self.csv_path)
            except SqlError:
                config.set_up_config_db()
                QMessageBox.critical(self, "Config file error",
                                     "Failed to access configuration file.\nPlease try again.")
            else:
                self.configured.emit(self.filepath)

    def choose_button_clicked(self):
        """
        Executes when the choose button is clicked.
        Gets filepath from the user and loads all files and subdirectories.
        """
        # Get folder path from pop up dialog box
        self.filepath = QtWidgets.QFileDialog.getExistingDirectory(None, 'Select default directory...', '')
        self.first_time_welcome_input_box.setText(self.filepath)

    def change_clinical_data_csv_button_clicked(self):
        """
        Executes when the choose button is clicked.
        Gets filepath from the user.
        """
        # Get folder path from pop up dialog box
        self.csv_path = QtWidgets.QFileDialog.getOpenFileName(
            None, "Open Clinical Data File", "", "CSV data files (*.csv)"
        )[0]
        if len(self.csv_path) > 0:
            self.clinical_data_csv_input_box.setText(self.csv_path)


# This is to allow for dropping a directory into the input text.
class UIFirstTimeUserDragAndDropEvent(QLineEdit):
    parent_window = None

    def __init__(self, ui_first_time_welcome_instance):
        super(UIFirstTimeUserDragAndDropEvent, self).__init__()
        self.parent_window = ui_first_time_welcome_instance
        self.setDragEnabled(True)

    def dragEnterEvent(self, event):
        data = event.mimeData()
        urls = data.urls()
        if urls and urls[0].scheme() == 'file':
            event.acceptProposedAction()

    def dropEvent(self, event):
        data = event.mimeData()
        urls = data.urls()
        if urls and urls[0].scheme() == 'file':
            # Removes the doubled intro slash
            default_directory_path = str(urls[0].path())[1:]
            # add / for not Windows machines
            if platform.system() != 'Windows':
                default_directory_path = "/" + default_directory_path
            # Pastes the directory into the text field
            self.setText(default_directory_path)