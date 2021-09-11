import platform

from PySide6 import QtWidgets, QtCore
from PySide6.QtGui import Qt, QIcon, QPixmap
from PySide6.QtWidgets import QGridLayout, QWidget, QLabel, QPushButton, QCheckBox, QHBoxLayout, QWidgetItem, \
    QListWidget, QListWidgetItem, QMessageBox

from src.Controller.PathHandler import resource_path


class UITransferROIWindow:

    def setup_ui(self, transfer_roi_window_instance,
                 patient_A_rois, patient_B_rois, signal_roi_transferred):
        self.patient_A_initial_rois = patient_A_rois
        self.patient_B_initial_rois = patient_B_rois
        self.signal_roi_transferred = signal_roi_transferred
        self.transfer_roi_window_instance = transfer_roi_window_instance
        self.patient_A_rois_to_B = {}
        self.patient_B_rois_to_A = {}
        self.add_suffix = True
        self.init_layout()

    def retranslate_ui(self, transfer_roi_window_instance):
        _translate = QtCore.QCoreApplication.translate
        transfer_roi_window_instance.setWindowTitle(
            _translate("TransferRoiWindowInstance",
                       "OnkoDICOM - Transfer Region of Interest"))
        self.add_suffix_checkbox.setText(
            _translate("AddSuffixCheckBox", "Add Suffix"))
        self.patient_A_label.setText(
            _translate("PatientAROILabel", "Patient A ROIs"))
        self.patient_B_label.setText(
            _translate("PatientBROILabel", "Patient B ROIs"))
        self.transfer_all_rois_to_patient_B_button.setText(
            _translate("ROITransferToBButton", "")
        )
        self.transfer_all_rois_to_patient_A_button.setText(
            _translate("ROITransferToAButton", "")
        )
        self.save_button.setText(
            _translate("SaveButton", "Save")
        )
        self.reset_button.setText(
            _translate("ResetButton", "Reset")
        )

    def init_layout(self):
        if platform.system() == 'Darwin':
            self.stylesheet_path = "res/stylesheet.qss"
        else:
            self.stylesheet_path = "res/stylesheet-win-linux.qss"
        stylesheet = open(resource_path(self.stylesheet_path)).read()
        window_icon = QIcon()
        window_icon.addPixmap(QPixmap(resource_path("res/images/icon.ico")),
                              QIcon.Normal, QIcon.Off)
        self.transfer_roi_window_instance.setObjectName("TransferRoiWindowInstance")
        self.transfer_roi_window_instance.setWindowIcon(window_icon)

        # Creating a grid layout to hold all elements
        self.transfer_roi_window_grid_layout = QGridLayout()
        self.transfer_roi_window_grid_layout.setColumnStretch(0, 1)
        self.transfer_roi_window_grid_layout.setColumnStretch(1, 1)
        self.transfer_roi_window_grid_layout.setColumnStretch(2, 1)

        self.init_patient_labels()
        self.init_transfer_arrow_buttons()
        self.init_patient_A_initial_roi_list()
        self.init_patient_B_rois_to_A_layout()
        self.init_patient_A_rois_to_B_layout()
        self.init_patient_B_initial_roi_list()
        self.init_add_suffix_checkbox()
        self.init_save_and_reset_button_layout()

        # Create a new central widget to hold the grid layout
        self.transfer_roi_window_instance_central_widget = QWidget()
        self.transfer_roi_window_instance_central_widget.setLayout(
            self.transfer_roi_window_grid_layout)
        self.retranslate_ui(self.transfer_roi_window_instance)
        self.transfer_roi_window_instance.setStyleSheet(stylesheet)
        self.transfer_roi_window_instance.setCentralWidget(self.transfer_roi_window_instance_central_widget)
        QtCore.QMetaObject.connectSlotsByName(self.transfer_roi_window_instance)


    def init_transfer_arrow_buttons(self):
        self.transfer_all_rois_to_patient_B_button = QPushButton()
        self.transfer_all_rois_to_patient_B_button.setObjectName("ROITransferToBButton")
        # TODO: Add icon to button
        self.transfer_all_rois_to_patient_B_button.setMaximumWidth(100)
        self.transfer_all_rois_to_patient_B_button.clicked.connect(self.transfer_all_rois_to_patient_B_button_clicked)
        self.transfer_roi_window_grid_layout.addWidget(self.transfer_all_rois_to_patient_B_button, 1, 1)

        self.transfer_all_rois_to_patient_A_button = QPushButton()
        self.transfer_all_rois_to_patient_A_button.setObjectName("ROITransferToAButton")
        # TODO: Add icon to button
        self.transfer_all_rois_to_patient_A_button.setText("<<")
        self.transfer_all_rois_to_patient_A_button.setMaximumWidth(100)
        self.transfer_all_rois_to_patient_A_button.clicked.connect(self.transfer_all_rois_to_patient_A_button_clicked)
        self.transfer_roi_window_grid_layout.addWidget(self.transfer_all_rois_to_patient_A_button, 2, 1)

    def transfer_all_rois_to_patient_B_button_clicked(self):
        self.patient_A_rois_to_B.clear()
        self.patient_A_rois_to_B_list_widget.clear()

        for i in range(0, len(self.patient_A_initial_rois)):
            self.patient_A_initial_roi_double_clicked(self.patient_A_initial_rois_list_widget.item(i))

    def transfer_all_rois_to_patient_A_button_clicked(self):
        self.patient_B_rois_to_A.clear()
        self.patient_B_rois_to_A_list_widget.clear()

        for i in range(0, len(self.patient_B_initial_rois)):
            self.patient_B_initial_roi_double_clicked(self.patient_B_initial_rois_list_widget.item(i))

    def init_add_suffix_checkbox(self):
        self.add_suffix_checkbox = QCheckBox()
        self.add_suffix_checkbox.setObjectName("AddSuffixCheckBox")
        self.add_suffix_checkbox.setChecked(self.add_suffix)
        self.add_suffix_checkbox.clicked.connect(self.add_suffix_checkbox_clicked)
        self.transfer_roi_window_grid_layout.addWidget(self.add_suffix_checkbox, 3, 0)

    def init_patient_labels(self):
        self.patient_A_label = QLabel()
        self.patient_A_label.setObjectName("PatientAROILabel")
        self.patient_A_label.setMinimumHeight(50)
        self.patient_A_label.setAlignment(Qt.AlignCenter)
        self.patient_A_label.setStyleSheet(
            "QLabel { background-color : green; color : white; font-size: 15pt; font-weight: bold;}")

        self.patient_B_label = QLabel()
        self.patient_B_label.setObjectName("PatientBROILabel")
        self.patient_B_label.setMinimumHeight(50)
        self.patient_B_label.setAlignment(Qt.AlignCenter)
        self.patient_B_label.setStyleSheet(
            "QLabel { background-color : red; color : white; font-size: 15pt; font-weight: bold;}")

        self.transfer_roi_window_grid_layout.addWidget(self.patient_A_label, 0, 0)
        self.transfer_roi_window_grid_layout.addWidget(self.patient_B_label, 0, 2)

    def init_save_and_reset_button_layout(self):
        self.reset_and_save_buttons_layout = QHBoxLayout()
        self.reset_button = QPushButton()
        self.reset_button.setObjectName("ResetButton")
        self.reset_button.clicked.connect(self.reset_clicked)
        self.save_button = QPushButton()
        self.save_button.setObjectName("SaveButton")
        self.save_button.clicked.connect(self.save_clicked)

        self.reset_and_save_buttons_layout.setAlignment(Qt.AlignRight)
        self.reset_and_save_buttons_layout.addWidget(self.reset_button)
        self.reset_and_save_buttons_layout.addWidget(self.save_button)

        # Create a widget to hold Reset and Save buttons
        self.reset_and_save_button_central_widget = QWidget()
        self.reset_and_save_button_central_widget.setLayout(self.reset_and_save_buttons_layout)

        self.transfer_roi_window_grid_layout.addWidget(self.reset_and_save_button_central_widget, 3, 2)

    def add_suffix_checkbox_clicked(self):
        self.add_suffix = self.add_suffix_checkbox.isChecked()

    def init_patient_B_rois_to_A_layout(self):
        # Create scrolling area widget to contain the content.
        self.patient_B_rois_to_A_list_widget = QListWidget(self)
        self.transfer_roi_window_grid_layout.addWidget(self.patient_B_rois_to_A_list_widget, 2, 0)

    def init_patient_A_rois_to_B_layout(self):
        self.patient_A_rois_to_B_list_widget = QListWidget(self)
        self.transfer_roi_window_grid_layout.addWidget(self.patient_A_rois_to_B_list_widget, 1, 2)

    def init_patient_A_initial_roi_list(self):
        self.patient_A_initial_rois_list_widget = QListWidget(self)
        self.patient_A_initial_rois_list_widget.itemDoubleClicked.connect(
            self.patient_A_initial_roi_double_clicked)
        for idx in self.patient_A_initial_rois:
            roi_label = QListWidgetItem(self.patient_A_initial_rois[idx]['name'])
            roi_label.setForeground(Qt.darkGreen)
            roi_label.setData(Qt.UserRole, self.patient_A_initial_rois[idx])
            self.patient_A_initial_rois_list_widget.addItem(roi_label)
        self.transfer_roi_window_grid_layout.addWidget(self.patient_A_initial_rois_list_widget, 1, 0)

    def init_patient_B_initial_roi_list(self):
        self.patient_B_initial_rois_list_widget = QListWidget(self)
        self.patient_B_initial_rois_list_widget.itemDoubleClicked.connect(
            self.patient_B_initial_roi_double_clicked)
        for idx in self.patient_B_initial_rois:
            roi_label = QListWidgetItem(self.patient_B_initial_rois[idx]['name'])
            roi_label.setForeground(Qt.red)
            roi_label.setData(Qt.UserRole, self.patient_B_initial_rois[idx])

            self.patient_B_initial_rois_list_widget.addItem(roi_label)
        self.transfer_roi_window_grid_layout.addWidget(self.patient_B_initial_rois_list_widget, 2, 2)

    def patient_A_initial_roi_double_clicked(self, item):
        roi_to_add = item.data(Qt.UserRole)
        transferred_roi_name = roi_to_add['name']

        # If the clicked roi is already transferred, return
        if transferred_roi_name in self.patient_A_rois_to_B.keys():
            QMessageBox.about(self, "Transfer Failed",
                              "Chosen ROI has already been transferred!")
            return
        # Create a set to store all current roi names in target patient
        # including both initial rois name and added roi names so far
        patient_B_initial_roi_name_list = set()

        for item in self.patient_A_rois_to_B.values():
            patient_B_initial_roi_name_list.add(item)
        for idx in self.patient_B_initial_rois:
            patient_B_initial_roi_name_list.add(self.patient_B_initial_rois[idx]['name'])

        # Check if clicked roi name has duplicate in patient B's initial roi names list
        if transferred_roi_name in patient_B_initial_roi_name_list:
            if self.add_suffix:
                changed_name = transferred_roi_name
                i = 1
                while changed_name in patient_B_initial_roi_name_list:
                    changed_name = transferred_roi_name + "_" + chr(i + 64)
                    i = i + 1
                transferred_roi_name = changed_name
            else:
                QMessageBox.about(self, "Transfer Failed",
                                  "Duplicated ROI name. Please consider adding suffix.")
                return

        # Add clicked roi to transferred list
        self.patient_A_rois_to_B[roi_to_add['name']] = transferred_roi_name
        roi_label = QListWidgetItem(transferred_roi_name)
        roi_label.setForeground(Qt.red)
        self.patient_A_rois_to_B_list_widget.addItem(roi_label)

    def patient_B_initial_roi_double_clicked(self, item):
        roi_to_add = item.data(Qt.UserRole)
        transferred_roi_name = roi_to_add['name']

        # If the clicked roi is already transferred, return
        if transferred_roi_name in self.patient_B_rois_to_A.keys():
            QMessageBox.about(self, "Transfer Failed",
                              "Chosen ROI has already been transferred!")
            return

        # Create a set to store all current roi names in target patient
        # including both initial rois name and added roi names so far
        patient_A_current_roi_name_list = set()

        for item in self.patient_B_rois_to_A.values():
            patient_A_current_roi_name_list.add(item)

        for idx in self.patient_A_initial_rois:
            patient_A_current_roi_name_list.add(self.patient_A_initial_rois[idx]['name'])

        # Check if clicked roi name has duplicate in target patient's roi names list
        if transferred_roi_name in patient_A_current_roi_name_list:
            # if add suffix is ticked, iteratively try adding suffix
            # from _A to _Z, stop when no duplicate found
            if self.add_suffix:
                changed_name = transferred_roi_name
                i = 1
                while changed_name in patient_A_current_roi_name_list:
                    changed_name = transferred_roi_name + "_" + chr(i + 64)
                    i = i + 1
                transferred_roi_name = changed_name
            else:
                QMessageBox.about(self, "Transfer Failed",
                                  "Duplicated ROI name. Please consider adding suffix.")
                return

        # Add clicked roi to transferred list
        self.patient_B_rois_to_A[roi_to_add['name']] = transferred_roi_name
        roi_label = QListWidgetItem(transferred_roi_name)
        roi_label.setForeground(Qt.red)
        self.patient_B_rois_to_A_list_widget.addItem(roi_label)

    def reset_clicked(self):
        self.patient_A_rois_to_B.clear()
        self.patient_B_rois_to_A.clear()
        self.patient_A_rois_to_B_list_widget.clear()
        self.patient_B_rois_to_A_list_widget.clear()

    def save_clicked(self):
        print("UITransferROIWindow.py line 281 method save_clicked")
        print((self.patient_A_rois_to_B, self.patient_B_rois_to_A))
        QMessageBox.about(self.transfer_roi_window_instance, "Saved",
                          "ROIs are successfully transferred!")
        self.closeWindow()

    def closeWindow(self):
        """
        function to close transfer roi window
        """
        self.close()
