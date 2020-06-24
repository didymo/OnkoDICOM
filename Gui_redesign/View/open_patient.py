from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QCoreApplication, QThreadPool
from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.Qt import Qt

from Gui_redesign.Model import DICOMDirectorySearch
from Gui_redesign.Model.Worker import Worker


class UIOpenPatientWindow(object):

    def setup_ui(self, main_window):
        main_window.setObjectName("MainWindow")
        main_window.setFixedSize(844, 528)
        main_window.setWindowTitle("OnkoDICOM")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("res/images/icon.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        main_window.setWindowIcon(icon)
        main_window.setAutoFillBackground(False)

        # Create threadpool for multithreading
        self.threadpool = QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

        self.central_widget = QtWidgets.QWidget(main_window)
        self.central_widget.setObjectName("centralwidget")
        self.grid_layout = QtWidgets.QGridLayout(self.central_widget)
        self.grid_layout.setObjectName("gridLayout")

        self.path_label = QtWidgets.QLabel(self.central_widget)
        self.path_label.setObjectName("path_label")
        self.path_label.setText("<html><head/><body><p><span style=\" font-size:10pt;\">Path:</span></p></body></html>")
        self.grid_layout.addWidget(self.path_label, 1, 0, 1, 1)

        self.cancel_button = QtWidgets.QPushButton(self.central_widget)
        self.cancel_button.setObjectName("cancelButton")
        self.cancel_button.setText("Cancel")
        self.cancel_button.clicked.connect(self.cancel_button_clicked) # Signal Closing Application

        self.grid_layout.addWidget(self.cancel_button, 9, 3, 1, 1)
        self.choose_button = QtWidgets.QPushButton(self.central_widget)
        self.choose_button.setObjectName("chooseButton")
        self.choose_button.setText("Choose")
        self.choose_button.clicked.connect(self.choose_button_clicked)

        self.grid_layout.addWidget(self.choose_button, 1, 2, 1, 1)
        self.path_text_browser = QtWidgets.QLineEdit(self.central_widget) #changed to text edit instead of browser
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Ignored)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.path_text_browser.sizePolicy().hasHeightForWidth())
        self.path_text_browser.setSizePolicy(size_policy)
        self.path_text_browser.setObjectName("pathTextBrowser")
        self.grid_layout.addWidget(self.path_text_browser, 1, 1, 1, 1)
        self.choose_label = QtWidgets.QLabel(self.central_widget)
        self.choose_label.setObjectName("choose_label")
        self.choose_label.setText("<html><head/><body><p><span style=\" font-size:10pt;\">Choose the file path of a "
                                  "folder containing DICOM files to create the Patient file "
                                  "directory:</span></p></body></html>")
        self.grid_layout.addWidget(self.choose_label, 0, 1, 1, 3)

        self.patient_file_label = QtWidgets.QLabel(self.central_widget)
        self.patient_file_label.setObjectName("patient_file_label")
        self.patient_file_label.setText("<html><head/><body><p><span style=\" font-size:10pt;\">Patient File "
                                        "directory shown below once file path chosen. Please select the file(s) you "
                                        "want to open:</span></p></body></html>")
        self.grid_layout.addWidget(self.patient_file_label, 6, 1, 1, 3)

        self.confirm_Button = QtWidgets.QPushButton(self.central_widget)
        self.confirm_Button.setObjectName("confirmButton")
        self.confirm_Button.setText("Confirm")
        self.confirm_Button.clicked.connect(self.confirm_button_clicked)
        self.grid_layout.addWidget(self.confirm_Button, 9, 4, 1, 1)

        self.selected_directory_label = QtWidgets.QLabel(self.central_widget)
        self.selected_directory_label.setObjectName("selected_directory_label")
        self.selected_directory_label.setText("<html><head/><body><p><span style=\" font-size:10pt;\">The selected "
                                              "directory(s) above will be opened in the OnkoDICOM "
                                              "program.</span></p></body></html>")
        self.grid_layout.addWidget(self.selected_directory_label, 9, 1, 1, 2)

        self.tree_widget = QtWidgets.QTreeWidget(self.central_widget)
        self.tree_widget.setHeaderHidden(True)
        self.tree_widget.setHeaderLabels([""])
        self.grid_layout.addWidget(self.tree_widget, 7, 1, 1, 1)

        main_window.setCentralWidget(self.central_widget)
        self.status_bar = QtWidgets.QStatusBar(main_window)
        self.status_bar.setObjectName("statusbar")
        self.status_bar.setSizeGripEnabled(False)  # Remove expanding window option
        main_window.setStatusBar(self.status_bar)

        QtCore.QMetaObject.connectSlotsByName(main_window)

    def cancel_button_clicked(self):
        QCoreApplication.exit(0)

    def choose_button_clicked(self):
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

            # Then, create a new thread that will load the selected folder
            worker = Worker(DICOMDirectorySearch.get_dicom_structure, self.filepath)
            worker.signals.result.connect(self.on_dicom_loaded)

            # Execute the thread
            self.threadpool.start(worker)

    def on_dicom_loaded(self, dicom_structure):
        self.choose_button.setEnabled(True)
        self.tree_widget.clear()
        for patient_item in dicom_structure.get_tree_items_list():
            self.tree_widget.addTopLevelItem(patient_item)

    def confirm_button_clicked(self):
        selected_files = []
        for item in self.get_checked_leaves():
            selected_files += item.dicom_object.get_files()
        print(selected_files)  # This needs to be replaced with a link to the existing OnkoDICOM main page

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
