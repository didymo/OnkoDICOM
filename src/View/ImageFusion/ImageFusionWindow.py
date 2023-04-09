import threading

from PySide6 import QtGui, QtWidgets
from PySide6.QtCore import QThreadPool, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QWidget, QTreeWidget, QTreeWidgetItem, \
    QMessageBox, QHBoxLayout, QVBoxLayout, \
    QLabel, QLineEdit, QSizePolicy, QPushButton

from src.Model.PatientDictContainer import PatientDictContainer
from src.Model import ImageLoading
from src.Model.DICOM import DICOMDirectorySearch
from src.Model.Worker import Worker
from src.View.ImageFusion.ImageFusionProgressWindow \
    import ImageFusionProgressWindow
from src.View.resources_open_patient_rc import *

from src.Controller.PathHandler import resource_path
import platform


class UIImageFusionWindow(object):
    image_fusion_info_initialized = QtCore.Signal(object)

    def setup_ui(self, open_image_fusion_select_instance):
        """Sets up a UI"""
        if platform.system() == 'Darwin':
            self.stylesheet_path = "res/stylesheet.qss"
        else:
            self.stylesheet_path = "res/stylesheet-win-linux.qss"

        window_icon = QIcon()
        window_icon.addPixmap(QPixmap(resource_path("res/images/icon.ico")),
                              QIcon.Normal, QIcon.Off)
        open_image_fusion_select_instance.setObjectName(
            "OpenPatientWindowInstance")
        open_image_fusion_select_instance.setWindowIcon(window_icon)
        open_image_fusion_select_instance.resize(840, 530)

        # Create a vertical box for containing the other elements and layouts
        self.open_patient_window_instance_vertical_box = QVBoxLayout()
        self.open_patient_window_instance_vertical_box.setObjectName(
            "OpenPatientWindowInstanceVerticalBox")

        # Create a label to prompt the user to enter the path to the
        # directory that contains the DICOM files
        self.open_patient_directory_prompt = QLabel()
        self.open_patient_directory_prompt.setObjectName(
            "OpenPatientDirectoryPrompt")
        self.open_patient_directory_prompt.setAlignment(Qt.AlignLeft)
        self.open_patient_window_instance_vertical_box.addWidget(
            self.open_patient_directory_prompt)

        # Create a horizontal box to hold the input box for the directory 
        # and the choose button
        self.open_patient_directory_input_horizontal_box = QHBoxLayout()
        self.open_patient_directory_input_horizontal_box.setObjectName(
            "OpenPatientDirectoryInputHorizontalBox")
        # Create a textbox to contain the path to the directory that contains 
        # the DICOM files
        self.open_patient_directory_input_box = \
            UIImageFusionWindowDragAndDropEvent(self)

        self.open_patient_directory_input_box.setObjectName(
            "OpenPatientDirectoryInputBox")
        self.open_patient_directory_input_box.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding,
                        QSizePolicy.MinimumExpanding))
        self.open_patient_directory_input_box.returnPressed.connect(
            self.scan_directory_for_patient)
        self.open_patient_directory_input_horizontal_box.addWidget(
            self.open_patient_directory_input_box)

        # Create a choose button to open the file dialog
        self.open_patient_directory_choose_button = QPushButton()
        self.open_patient_directory_choose_button.setObjectName(
            "OpenPatientDirectoryChooseButton")
        self.open_patient_directory_choose_button.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding,
                        QSizePolicy.MinimumExpanding))
        self.open_patient_directory_choose_button.resize(
            self.open_patient_directory_choose_button.sizeHint().width(),
            self.open_patient_directory_input_box.height())
        self.open_patient_directory_choose_button.setCursor(
            QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.open_patient_directory_input_horizontal_box.addWidget(
            self.open_patient_directory_choose_button)
        self.open_patient_directory_choose_button.clicked.connect(
            self.choose_button_clicked)

        # Create a widget to hold the input fields
        self.open_patient_directory_input_widget = QWidget()
        self.open_patient_directory_input_horizontal_box.setStretch(0, 4)
        self.open_patient_directory_input_widget.setLayout(
            self.open_patient_directory_input_horizontal_box)
        self.open_patient_window_instance_vertical_box.addWidget(
            self.open_patient_directory_input_widget)

        # Create a horizontal box to hold the stop button and direction to 
        # the user on where to select the patient
        self.open_patient_appear_prompt_and_stop_horizontal_box = QHBoxLayout()
        self.open_patient_appear_prompt_and_stop_horizontal_box.setObjectName(
            "OpenPatientAppearPromptAndStopHorizontalBox")
        # Create a label to show direction on where the files will appear
        self.open_patient_directory_appear_prompt = QLabel()
        self.open_patient_directory_appear_prompt.setObjectName(
            "OpenPatientDirectoryAppearPrompt")
        self.open_patient_directory_appear_prompt.setAlignment(Qt.AlignLeft)
        self.open_patient_appear_prompt_and_stop_horizontal_box.addWidget(
            self.open_patient_directory_appear_prompt)
        self.open_patient_appear_prompt_and_stop_horizontal_box.addStretch(1)
        # Create a button to stop searching
        self.open_patient_window_stop_button = QPushButton()
        self.open_patient_window_stop_button.setObjectName(
            "OpenPatientWindowStopButton")
        self.open_patient_window_stop_button.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding,
                        QSizePolicy.MinimumExpanding))
        self.open_patient_window_stop_button.resize(
            self.open_patient_window_stop_button.sizeHint().width(),
            self.open_patient_window_stop_button.sizeHint().height())
        self.open_patient_window_stop_button.setCursor(
            QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.open_patient_window_stop_button.clicked.connect(
            self.stop_button_clicked)
        self.open_patient_window_stop_button.setProperty(
            "QPushButtonClass", "fail-button")
        self.open_patient_window_stop_button.setVisible(False)
        self.open_patient_appear_prompt_and_stop_horizontal_box.addWidget(
            self.open_patient_window_stop_button)
        # Create a widget to hold the layout
        self.open_patient_appear_prompt_and_stop_widget = QWidget()
        self.open_patient_appear_prompt_and_stop_widget.setLayout(
            self.open_patient_appear_prompt_and_stop_horizontal_box)
        self.open_patient_window_instance_vertical_box.addWidget(
            self.open_patient_appear_prompt_and_stop_widget)

        # Create a tree view list to list out all patients in the directory 
        # selected above
        self.open_patient_window_patients_tree = QTreeWidget()
        self.open_patient_window_patients_tree.setObjectName(
            "OpenPatientWindowPatientsTree")
        self.open_patient_window_patients_tree.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding,
                        QSizePolicy.MinimumExpanding))
        self.open_patient_window_patients_tree.resize(
            self.open_patient_window_patients_tree.sizeHint().width(),
            self.open_patient_window_patients_tree.sizeHint().height())
        self.open_patient_window_patients_tree.setHeaderHidden(False)
        self.open_patient_window_patients_tree.setHeaderLabels([""])
        self.open_patient_window_patients_tree.itemChanged.connect(
            self.tree_item_clicked)
        self.open_patient_window_instance_vertical_box.addWidget(
            self.open_patient_window_patients_tree)
        self.last_patient = None

        # Create a label to show what would happen if they select the patient
        self.open_patient_directory_result_label = QtWidgets.QLabel()
        self.open_patient_directory_result_label.setObjectName(
            "OpenPatientDirectoryResultLabel")
        self.open_patient_directory_result_label.setAlignment(Qt.AlignLeft)
        self.open_patient_window_instance_vertical_box.addWidget(
            self.open_patient_directory_result_label)

        # Create a horizontal box to hold the Cancel and Open button
        self.open_patient_window_patient_open_actions_horizontal_box = \
            QHBoxLayout()
        self.open_patient_window_patient_open_actions_horizontal_box. \
            setObjectName("OpenPatientWindowPatientOpenActionsHorizontalBox")
        self.open_patient_window_patient_open_actions_horizontal_box. \
            addStretch(1)
        # Add a button to go back/close from the application
        self.open_patient_window_close_button = QPushButton()
        self.open_patient_window_close_button.setObjectName(
            "OpenPatientWindowcloseButton")
        self.open_patient_window_close_button.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding,
                        QSizePolicy.MinimumExpanding))
        self.open_patient_window_close_button.resize(
            self.open_patient_window_stop_button.sizeHint().width(),
            self.open_patient_window_stop_button.sizeHint().height())
        self.open_patient_window_close_button.setCursor(
            QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.open_patient_window_close_button.clicked.connect(
            self.close_button_clicked)
        self.open_patient_window_close_button.setProperty(
            "QPushButtonClass", "fail-button")
        self.open_patient_window_patient_open_actions_horizontal_box. \
            addWidget(self.open_patient_window_close_button)

        # Add a button to confirm opening of the patient
        self.open_patient_window_confirm_button = QPushButton()
        self.open_patient_window_confirm_button.setObjectName(
            "OpenPatientWindowConfirmButton")
        self.open_patient_window_confirm_button.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding,
                        QSizePolicy.MinimumExpanding))
        self.open_patient_window_confirm_button.resize(
            self.open_patient_window_confirm_button.sizeHint().width(),
            self.open_patient_window_confirm_button.sizeHint().height())

        self.open_patient_window_confirm_button.setCursor(
            QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.open_patient_window_confirm_button.setDisabled(True)
        self.open_patient_window_confirm_button.clicked.connect(
            self.confirm_button_clicked)
        self.open_patient_window_confirm_button.setProperty(
            "QPushButtonClass", "success-button")
        self.open_patient_window_patient_open_actions_horizontal_box. \
            addWidget(
            self.open_patient_window_confirm_button)

        # Create a widget to house all of the actions button for open patient
        #  window
        self.open_patient_window_patient_open_actions_widget = QWidget()
        self.open_patient_window_patient_open_actions_widget.setLayout(
            self.open_patient_window_patient_open_actions_horizontal_box)
        self.open_patient_window_instance_vertical_box.addWidget(
            self.open_patient_window_patient_open_actions_widget)

        # Set the vertical box fourth element, the tree view, to stretch 
        # out as far as possible
        self.open_patient_window_instance_vertical_box.setStretch(3, 4)
        self.open_patient_window_instance_central_widget = QWidget()
        self.open_patient_window_instance_central_widget.setObjectName(
            "OpenPatientWindowInstanceCentralWidget")
        self.open_patient_window_instance_central_widget.setLayout(
            self.open_patient_window_instance_vertical_box)

        # Create threadpool for multithreading
        self.threadpool = QThreadPool()
        # print("Multithreading with maximum %d threads" % self.threadpool.
        # maxThreadCount())
        # Create interrupt event for stopping the directory search
        self.interrupt_flag = threading.Event()

        # Bind all texts into the buttons and labels
        self.retranslate_ui(open_image_fusion_select_instance)
        # Set the central widget, ready for display
        open_image_fusion_select_instance.setCentralWidget(
            self.open_patient_window_instance_central_widget)

        # Set the current stylesheet to the instance and connect it back 
        # to the caller through slot
        _stylesheet = open(resource_path(self.stylesheet_path)).read()
        open_image_fusion_select_instance.setStyleSheet(_stylesheet)

        QtCore.QMetaObject.connectSlotsByName(
            open_image_fusion_select_instance)

    def retranslate_ui(self, open_image_fusion_select_instance):
        """Translates UI"""
        _translate = QtCore.QCoreApplication.translate
        open_image_fusion_select_instance.setWindowTitle(
            _translate("OpenPatientWindowInstance",
                       "OnkoDICOM - Select Patient"))
        self.open_patient_directory_prompt.setText(_translate(
            "OpenPatientWindowInstance",
            "Choose an image to merge with:"))
        self.open_patient_directory_input_box.setPlaceholderText(
            _translate("OpenPatientWindowInstance",
                       "Enter DICOM Files Path (For example, "
                       "C:\\path\\to\\your\\DICOM\\Files)"))
        self.open_patient_directory_choose_button.setText(_translate(
            "OpenPatientWindowInstance",
            "Choose"))
        self.open_patient_directory_appear_prompt.setText(_translate(
            "OpenPatientWindowInstance",
            "Please select below the image set you wish to overlay:"))
        self.open_patient_directory_result_label. \
            setText("The selected imageset(s) above will be "
                    "co-registered with the current imageset.")
        self.open_patient_window_stop_button.setText(_translate(
            "OpenPatientWindowInstance", "Stop Search"))
        self.open_patient_window_close_button.setText(_translate(
            "OpenPatientWindowInstance", "Close"))
        self.open_patient_window_confirm_button.setText(_translate(
            "OpenPatientWindowInstance", "Confirm"))

    def update_patient(self):
        self.clear_checked_leaves()
        self.patient_dict_container = PatientDictContainer()
        self.patient = self.patient_dict_container.get("basic_info")
        self.patient_id = self.patient['id']

        dataset = self.patient_dict_container.dataset[0]
        self.patient_current_image_series_uid = \
            dataset.get("SeriesInstanceUID")

    def clear_checked_leaves(self):
        """
        Resets all leaves to their unchecked state
        """
        def recurse(parent_item: QTreeWidgetItem):
            for i in range(parent_item.childCount()):
                child = parent_item.child(i)
                grand_children = child.childCount()
                if grand_children > 0:
                    recurse(child)
                else:
                    if child.checkState(0) == Qt.Checked:
                        child.setCheckState(0, Qt.CheckState.Unchecked)
                        child.setSelected(False)

        recurse(self.open_patient_window_patients_tree.invisibleRootItem())
        self.open_patient_window_patients_tree.collapseAll()

    def close_button_clicked(self):
        """Closes the window."""
        self.close()

    def scan_directory_for_patient(self):
        # Reset tree view header and last patient
        self.open_patient_window_confirm_button.setDisabled(True)
        self.open_patient_window_patients_tree.setHeaderLabels([""])
        self.last_patient = None
        self.filepath = self.open_patient_directory_input_box.text()
        # Proceed if a folder was selected
        if self.filepath != "":
            # Update the QTreeWidget to reflect data being loaded
            # First, clear the widget of any existing data
            self.open_patient_window_patients_tree.clear()

            # Next, update the tree widget
            self.open_patient_window_patients_tree.addTopLevelItem(
                QTreeWidgetItem(["Loading selected directory..."]))

            # The choose button is disabled until the thread finishes executing
            self.open_patient_directory_choose_button.setEnabled(False)

            # Reveals the Stop Search button for the duration of the search
            self.open_patient_window_stop_button.setVisible(True)

            # The interrupt flag is then un-set if a previous search has been
            # stopped.
            self.interrupt_flag.clear()

            # Then, create a new thread that will load the selected folder
            worker = Worker(DICOMDirectorySearch.get_dicom_structure,
                            self.filepath,
                            self.interrupt_flag, progress_callback=True)
            worker.signals.result.connect(self.on_search_complete)
            worker.signals.progress.connect(self.search_progress)

            # Execute the thread
            self.threadpool.start(worker)

    def choose_button_clicked(self):
        """
        Executes when the choose button is clicked.
        Gets filepath from the user and loads all files and subdirectories.
        """
        # Get folder path from pop up dialog box
        self.filepath = QtWidgets.QFileDialog.getExistingDirectory(
            None, 'Select patient folder...', '')
        self.open_patient_directory_input_box.setText(self.filepath)
        self.scan_directory_for_patient()

    def stop_button_clicked(self):
        self.interrupt_flag.set()

    def search_progress(self, progress_update):
        """
        Current progress of the file search.
        """
        self.open_patient_window_patients_tree.clear()
        self.open_patient_window_patients_tree.addTopLevelItem(
            QTreeWidgetItem(["Loading selected directory... "
                             "(%s files searched)" % progress_update]))

    def on_search_complete(self, dicom_structure):
        """
        Executes once the directory search is complete.
        :param dicom_structure: DICOMStructure object constructed by the
        directory search.
        """
        self.open_patient_directory_choose_button.setEnabled(True)
        self.open_patient_window_stop_button.setVisible(False)
        self.open_patient_window_patients_tree.clear()

        # dicom_structure will be None if function was interrupted.
        if dicom_structure is None:
            return

        for patient_item in dicom_structure.get_tree_items_list():
            self.open_patient_window_patients_tree.addTopLevelItem(
                patient_item)
            patient_item.setExpanded(True)  # Display all studies
            # Display all image sets
            for i in range(patient_item.childCount()):
                study = patient_item.child(i)
                study.setExpanded(True)

        if len(dicom_structure.patients) == 0:
            QMessageBox.about(self, "No files found",
                              "Selected directory contains no DICOM files.")

    def tree_item_clicked(self, item, _):
        """
        Executes when a tree item is checked or unchecked.
        If a different patient is checked, uncheck the previous patient.
        Inform user about missing DICOM files.
        """
        # If patient is only selected, but not checked, set it to "focus" to
        # coincide with stylesheet. And if the selected item is an image set,
        # display its child branches.
        if item.checkState(0) == Qt.CheckState.Unchecked:
            self.open_patient_window_patients_tree.setCurrentItem(item)
        else:  # Otherwise don't "focus", then set patient as selected
            self.open_patient_window_patients_tree.setCurrentItem(None)
            item.setSelected(True)

        # Expand or collapse the tree branch if item is an image series
        # Only collapse if the selected image series is expanded but unchecked
        # Otherwise, expand its tree branch to show RT files
        is_expanded = False \
            if (item.isExpanded() is True and
                item.checkState(0) == Qt.CheckState.Unchecked) else True
        self.display_a_tree_branch(item, is_expanded)

        selected_patient = item
        # If the item is not top-level, bubble up to see which top-level item
        # this item belongs to
        if self.open_patient_window_patients_tree.invisibleRootItem(). \
                indexOfChild(item) == -1:
            while self.open_patient_window_patients_tree.invisibleRootItem(). \
                    indexOfChild(selected_patient) == -1:
                selected_patient = selected_patient.parent()

        # Uncheck previous patient if a different patient is selected
        if item.checkState(0) == Qt.CheckState.Checked and self.last_patient \
                != selected_patient:
            if self.last_patient is not None:
                last_patient_checked_items = self.get_checked_nodes(
                    self.last_patient)
                for checked_item in last_patient_checked_items:
                    checked_item.setCheckState(0, Qt.Unchecked)
            self.last_patient = selected_patient

        # Check selected items and display warning messages
        self.check_selected_items(selected_patient)

    def display_a_tree_branch(self, node, is_expanded):
        # TO DO:
        # Could Team 23 please update the defintion of this docstring as
        # well as same function presented in OpenPatientWindow.
        """
        Displays a tree branch
        Parameters:
            node : root node the tree
            is_expanded (boolean): flag for checking if a particular
            node/leaf is expanded.
        """
        node.setExpanded(is_expanded)
        if node.childCount() > 0:
            for i in range(node.childCount()):
                self.display_a_tree_branch(node.child(i), is_expanded)
        else:
            return

    def check_selected_items(self, selected_patient):
        """
        Check and display warning messages based on the existence and quantity
        of image series, RTSTRUCT, RTPLAN, RTDOSE and SR files

        Parameters:
            selected_patient (DICOMStructure): DICOM Object of patient
        """
        # Get the types of all selected leaves & Get the names of all selected
        # studies
        checked_nodes = self.get_checked_nodes(
            self.open_patient_window_patients_tree.invisibleRootItem())
        selected_series_types = [checked_node.dicom_object.get_series_type()
                                 for checked_node in checked_nodes]
        selected_series_id = [checked_node.dicom_object.series_uid
                              for checked_node in checked_nodes]

        # Total number of selected image series
        total_selected_image_series = selected_series_types.count('CT') + \
                                      selected_series_types.count('MR') + \
                                      selected_series_types.count('PT')

        # Check the existence of IMAGE, RTSTRUCT, RTPLAN and RTDOSE files
        proceed = True

        if total_selected_image_series < 1:
            header = "Cannot proceed without an image."
            proceed = False
        elif total_selected_image_series > 1:
            header = "Cannot proceed with more than 1 selected image."
            proceed = False
        elif selected_patient.dicom_object.patient_id.strip() != \
                self.patient_id:
            header = "Cannot proceed with different patient."
            proceed = False
        elif self.patient_current_image_series_uid in selected_series_id:
            header = "Cannot fuse with the same series."
            proceed = False
        elif not self.check_selected_items_referencing(checked_nodes):
            # Check that selected items properly reference each other
            header = "Selected series do not reference each other."
            proceed = False
        elif 'RTSTRUCT' not in selected_series_types and \
            self.check_existing_rtss(checked_nodes):
            header = "The associated RTSTRUCT must be selected."
            proceed = False
        elif 'RTDOSE' in selected_series_types:
            header = "Cannot fuse with a RTDOSE file."
            proceed = False
        else:
            header = ""
        self.open_patient_window_confirm_button.setDisabled(not proceed)

        # Set the tree header
        self.open_patient_window_patients_tree.setHeaderLabel(header)

    def check_selected_items_referencing(self, items):
        """
        Check if selected tree items properly reference each other.
        :param items: List of selected DICOMWidgetItems.
        :return: True if the selected items belong to the same tree branch.
        """
        # Dictionary of series of different file types
        series = {
            "IMAGE": None,
            "RTSTRUCT": None,
            "RTPLAN": None,
            "RTDOSE": None,
            "SR": None
        }

        for item in items:
            series_type = item.dicom_object.get_series_type()
            if series_type in series:
                series[series_type] = item
            else:
                series["IMAGE"] = item

        # Check if the RTSTRUCT, RTPLAN, and RTDOSE are a child item of the
        # image series
        if series["IMAGE"]:
            if series["RTSTRUCT"] and series["RTSTRUCT"].parent() != \
                    series["IMAGE"]:
                return False

            if series["RTPLAN"] and \
                    series["RTPLAN"].parent().parent() != series["IMAGE"]:
                return False

            if series["SR"] and series["SR"].parent() != series["IMAGE"]:
                return False

        return True

    def check_existing_rtss(self, items):
        """
        Check for existing rtss
        :return: bool, whether there is a rtss associated with the selected
        image series
        """
        image_series = ['CT', 'MR', 'PT']
        for item in items:
            if item.dicom_object.get_series_type() in image_series:
                for i in range(item.childCount()):
                    if item.child(i).dicom_object:
                        return True
                return False

    def get_checked_nodes(self, root):
        """
        :param root: QTreeWidgetItem as a root.
        :return: A list of all QTreeWidgetItems in the QTreeWidget that are
        checked under the root.
        """
        checked_items = []

        def recurse(parent_item: QTreeWidgetItem):
            for i in range(parent_item.childCount()):
                child = parent_item.child(i)
                if int(child.flags()) & int(Qt.ItemIsUserCheckable) and \
                        child.checkState(0) == Qt.Checked:
                    checked_items.append(child)
                grand_children = child.childCount()
                if grand_children > 0:
                    recurse(child)

        recurse(root)
        return checked_items

    def confirm_button_clicked(self):
        """
        Begins loading of the selected files.
        """
        selected_files = []
        for item in self.get_checked_nodes(
                self.open_patient_window_patients_tree.invisibleRootItem()):
            selected_files += item.dicom_object.get_files()

        self.progress_window = ImageFusionProgressWindow(self)
        self.progress_window.signal_loaded.connect(self.on_loaded)
        self.progress_window.signal_error.connect(self.on_loading_error)
        self.progress_window.start_loading(selected_files)

    def on_loaded(self, results):
        """
        Executes when the progress bar finishes loaded the selected files.
        """
        if results[0] is True:  # Will be NoneType if loading was interrupted.
            self.image_fusion_info_initialized.emit(results[1])

    def on_loading_error(self, exception):
        """
        Error handling for progress window.
        """
        if type(exception[1]) == ImageLoading.NotRTSetError:
            QMessageBox.about(self.progress_window,
                              "Unable to open selection",
                              "Selected files cannot be opened as they are not"
                              " a DICOM-RT set.")
            self.progress_window.close()
        elif type(exception[1]) == ImageLoading.NotAllowedClassError:
            QMessageBox.about(self.progress_window,
                              "Unable to open selection",
                              "Selected files cannot be opened as they contain"
                              " unsupported DICOM classes.")
            self.progress_window.close()


# This is to allow for dropping a directory into the input text.
class UIImageFusionWindowDragAndDropEvent(QLineEdit):
    parent_window = None

    def __init__(self, ui_image_fusion_window_instance):
        super(UIImageFusionWindowDragAndDropEvent, self).__init__()
        self.parent_window = ui_image_fusion_window_instance
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
            dicom_file_path = str(urls[0].path())[1:]
            # add / for not Windows machines
            if platform.system() != 'Windows':
                dicom_file_path = "/" + dicom_file_path
            # Pastes the directory into the text field
            self.setText(dicom_file_path)
            UIImageFusionWindow.scan_directory_for_patient(self.parent_window)
