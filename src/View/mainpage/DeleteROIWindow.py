import pydicom
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QTreeWidget, \
    QTreeWidgetItem, QMessageBox, QAbstractItemView, QSizePolicy
from src.Controller.PathHandler import resource_path
from src.Model import ROI
import platform

from src.Model.Worker import Worker


class UIDeleteROIWindow():
    def setup_ui(self, delete_roi_window_instance, regions_of_interest, dataset_rtss, deleting_rois_structure_tuple):
        # Initialise the 2 lists for containing the ROI(s) that we are going to keep and delete respectively
        self.regions_of_interest_to_keep = []
        self.regions_of_interest_to_delete = []
        # This is for holding the original list of ROI(s)
        self.regions_of_interest_list = regions_of_interest
        # This is for holding the DICOM dataset of that specific patient
        self.dataset_rtss = dataset_rtss
        # Assigning new tuple for holding the deleting ROI(s)
        self.deleting_rois_structure_tuple = deleting_rois_structure_tuple

        # Initialise a DeleteROIWindow
        if platform.system() == 'Darwin':
            self.stylesheet_path = "res/stylesheet.qss"
        else:
            self.stylesheet_path = "res/stylesheet-win-linux.qss"
        stylesheet = open(resource_path(self.stylesheet_path)).read()
        window_icon = QIcon()
        window_icon.addPixmap(QPixmap(resource_path("res/images/icon.ico")), QIcon.Normal, QIcon.Off)
        delete_roi_window_instance.setObjectName("DeleteRoiWindowInstance")
        delete_roi_window_instance.setWindowIcon(window_icon)
        delete_roi_window_instance.resize(800, 606)

        # Create a vertical box to hold all widgets
        self.delete_roi_window_instance_vertical_box = QVBoxLayout()
        self.delete_roi_window_instance_vertical_box.setObjectName("DeleteRoiWindowInstanceVerticalBox")

        # Create a label for holding the window's title
        self.delete_roi_window_title = QLabel()
        self.delete_roi_window_title.setObjectName("DeleteRoiWindowTitle")
        self.delete_roi_window_title.setProperty("QLabelClass", "window-title")
        self.delete_roi_window_title.setAlignment(Qt.AlignLeft)
        self.delete_roi_window_instance_vertical_box.addWidget(self.delete_roi_window_title)

        # Create a label for holding the instruction of how to delete the ROIs
        self.delete_roi_window_instruction = QLabel()
        self.delete_roi_window_instruction.setObjectName("DeleteRoiWindowInstruction")
        self.delete_roi_window_instruction.setAlignment(Qt.AlignCenter)
        self.delete_roi_window_instance_vertical_box.addWidget(self.delete_roi_window_instruction)


        # Create a horizontal box for holding the 2 lists and the move left, move right buttons
        self.delete_roi_window_keep_and_delete_box = QHBoxLayout()
        self.delete_roi_window_keep_and_delete_box.setObjectName("DeleteRoiWindowKeepAndDeleteBox")
        # ================================= KEEP BOX =================================
        # Create a vertical box for holding the label and the tree view for holding the ROIs that we are keeping
        self.delete_roi_window_keep_vertical_box = QVBoxLayout()
        self.delete_roi_window_keep_vertical_box.setObjectName("DeleteRoiWindowKeepVerticalBox")
        # Create a label for the tree view with the list of ROIs to keep
        self.delete_roi_window_keep_tree_view_label = QLabel()
        self.delete_roi_window_keep_tree_view_label.setObjectName("DeleteRoiWindowKeepTreeViewLabel")
        self.delete_roi_window_keep_tree_view_label.setProperty("QLabelClass", ["tree-view-label", "tree-view-label-keep-delete"])
        self.delete_roi_window_keep_tree_view_label.setAlignment(Qt.AlignCenter)
        self.delete_roi_window_keep_tree_view_label.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding))
        self.delete_roi_window_keep_tree_view_label.resize(self.delete_roi_window_keep_tree_view_label.sizeHint().width(),
                                                      self.delete_roi_window_keep_tree_view_label.sizeHint().height())
        self.delete_roi_window_keep_vertical_box.addWidget(self.delete_roi_window_keep_tree_view_label)
        # Create a tree view for containing the list of ROIs to keep
        self.delete_roi_window_keep_tree_view = QTreeWidget()
        self.delete_roi_window_keep_tree_view.setObjectName("DeleteRoiWindowKeepTreeView")
        self.delete_roi_window_keep_tree_view.setHeaderHidden(True)
        self.delete_roi_window_keep_tree_view.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding))
        self.delete_roi_window_keep_tree_view.resize(
            self.delete_roi_window_keep_tree_view.sizeHint().width(),
            self.delete_roi_window_keep_tree_view.sizeHint().height())
        self.delete_roi_window_keep_vertical_box.addWidget(self.delete_roi_window_keep_tree_view)
        self.delete_roi_window_keep_vertical_box.setStretch(1, 4)
        # Create a widget to hold the keep vertical box
        self.delete_roi_window_keep_widget = QWidget()
        self.delete_roi_window_keep_widget.setObjectName("DeleteRoiWindowKeepWidget")
        self.delete_roi_window_keep_widget.setLayout(self.delete_roi_window_keep_vertical_box)
        self.delete_roi_window_keep_and_delete_box.addStretch(1)
        self.delete_roi_window_keep_and_delete_box.addWidget(self.delete_roi_window_keep_widget)
        # ================================= KEEP BOX =================================


        # ================================= MOVE LEFT/RIGHT BOX =================================
        # Create a vertical box for holding the 2 buttons for moving left and right
        self.delete_roi_window_move_left_right_vertical_box = QVBoxLayout()
        self.delete_roi_window_move_left_right_vertical_box.setObjectName("DeleteRoiWindowMoveLeftRightVerticalBox")
        # Create Move Right Button / Delete Button
        self.move_right_button = QPushButton()
        self.move_right_button.setObjectName("MoveRightButton")
        self.move_right_button.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding))
        self.move_right_button.resize(self.move_right_button.sizeHint().width(),
                                                    self.move_right_button.sizeHint().height())
        self.move_right_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.move_right_button.clicked.connect(self.move_right_button_onClicked)
        self.move_right_button.setProperty("QPushButtonClass", "fail-button")
        self.delete_roi_window_move_left_right_vertical_box.addStretch(1)
        self.delete_roi_window_move_left_right_vertical_box.addWidget(self.move_right_button)
        # Create Move Left Button / Keep Button
        self.move_left_button = QPushButton()
        self.move_left_button.setObjectName("MoveLeftButton")
        self.move_left_button.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding))
        self.move_left_button.resize(self.move_left_button.sizeHint().width(),
                                      self.move_left_button.sizeHint().height())
        self.move_left_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.move_left_button.clicked.connect(self.move_left_button_onClicked)
        self.move_left_button.setProperty("QPushButtonClass", "success-button")
        self.delete_roi_window_move_left_right_vertical_box.addWidget(self.move_left_button)
        self.delete_roi_window_move_left_right_vertical_box.addStretch(1)
        # Create a widget for holding the 2 buttons
        self.delete_roi_window_move_left_right_widget = QWidget()
        self.delete_roi_window_move_left_right_widget.setObjectName("DeleteRoiWindowMoveLeftRightWidget")
        self.delete_roi_window_move_left_right_widget.setLayout(self.delete_roi_window_move_left_right_vertical_box)
        self.delete_roi_window_keep_and_delete_box.addWidget(self.delete_roi_window_move_left_right_widget)
        # ================================= MOVE LEFT/RIGHT BOX =================================


        # ================================= DELETE BOX =================================
        # Create a vertical box for holding the label and the tree view for holding the ROIs that we are deleting
        self.delete_roi_window_delete_vertical_box = QVBoxLayout()
        self.delete_roi_window_delete_vertical_box.setObjectName("DeleteRoiWindowDeleteVerticalBox")
        # Create a label for the tree view with the list of ROIs to delete
        self.delete_roi_window_delete_tree_view_label = QLabel()
        self.delete_roi_window_delete_tree_view_label.setObjectName("DeleteRoiWindowDeleteTreeViewLabel")
        self.delete_roi_window_delete_tree_view_label.setProperty("QLabelClass",
                                                                ["tree-view-label", "tree-view-label-keep-delete"])
        self.delete_roi_window_delete_tree_view_label.setAlignment(Qt.AlignCenter)
        self.delete_roi_window_delete_tree_view_label.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding))
        self.delete_roi_window_delete_tree_view_label.resize(
            self.delete_roi_window_delete_tree_view_label.sizeHint().width(),
            self.delete_roi_window_delete_tree_view_label.sizeHint().height())
        self.delete_roi_window_delete_vertical_box.addWidget(self.delete_roi_window_delete_tree_view_label)
        # Create a tree view for containing the list of ROIs to delete
        self.delete_roi_window_delete_tree_view = QTreeWidget()
        self.delete_roi_window_delete_tree_view.setObjectName("DeleteRoiWindowDeleteTreeView")
        self.delete_roi_window_delete_tree_view.setHeaderHidden(True)
        self.delete_roi_window_delete_tree_view.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding))
        self.delete_roi_window_delete_tree_view.resize(
            self.delete_roi_window_delete_tree_view.sizeHint().width(),
            self.delete_roi_window_delete_tree_view.sizeHint().height())
        self.delete_roi_window_delete_vertical_box.addWidget(self.delete_roi_window_delete_tree_view)
        self.delete_roi_window_delete_vertical_box.setStretch(1, 4)
        # Create a widget to hold the delete vertical box
        self.delete_roi_window_delete_widget = QWidget()
        self.delete_roi_window_delete_widget.setObjectName("DeleteRoiWindowDeleteWidget")
        self.delete_roi_window_delete_widget.setLayout(self.delete_roi_window_delete_vertical_box)
        self.delete_roi_window_keep_and_delete_box.addWidget(self.delete_roi_window_delete_widget)
        self.delete_roi_window_keep_and_delete_box.addStretch(1)
        self.delete_roi_window_keep_and_delete_box.setStretch(1, 4)
        self.delete_roi_window_keep_and_delete_box.setStretch(3, 4)
        # ================================= DELETE BOX =================================
        # Create a widget to hold the keep and delete box
        self.delete_roi_window_keep_and_delete_widget = QWidget()
        self.delete_roi_window_keep_and_delete_widget.setObjectName("DeleteRoiWindowKeepAndDeleteWidget")
        self.delete_roi_window_keep_and_delete_widget.setLayout(self.delete_roi_window_keep_and_delete_box)
        self.delete_roi_window_instance_vertical_box.addWidget(self.delete_roi_window_keep_and_delete_widget)


        # Create a horizontal box to hold 2 action buttons for this window
        self.delete_roi_window_action_buttons_box = QHBoxLayout()
        self.delete_roi_window_action_buttons_box.setObjectName("DeleteRoiWindowActionButtonsBox")
        # Create the cancel button
        self.delete_roi_window_cancel_button = QPushButton()
        self.delete_roi_window_cancel_button.setObjectName("DeleteRoiWindowCancelButton")
        self.delete_roi_window_cancel_button.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding))
        self.delete_roi_window_cancel_button.resize(self.delete_roi_window_cancel_button.sizeHint().width(),
                                     self.delete_roi_window_cancel_button.sizeHint().height())
        self.delete_roi_window_cancel_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.delete_roi_window_cancel_button.clicked.connect(self.on_cancel_button_clicked)
        self.delete_roi_window_cancel_button.setProperty("QPushButtonClass", "fail-button")
        self.delete_roi_window_action_buttons_box.addStretch(1)
        self.delete_roi_window_action_buttons_box.addWidget(self.delete_roi_window_cancel_button)
        # Create the confirm button
        self.delete_roi_window_confirm_button = QPushButton()
        self.delete_roi_window_confirm_button.setObjectName("DeleteRoiWindowConfirmButton")
        self.delete_roi_window_confirm_button.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding))
        self.delete_roi_window_confirm_button.resize(self.delete_roi_window_confirm_button.sizeHint().width(),
                                                    self.delete_roi_window_confirm_button.sizeHint().height())
        self.delete_roi_window_confirm_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.delete_roi_window_confirm_button.clicked.connect(self.confirm_button_onClicked)
        self.delete_roi_window_confirm_button.setEnabled(False)
        self.delete_roi_window_confirm_button.setProperty("QPushButtonClass", "success-button")
        self.delete_roi_window_action_buttons_box.addWidget(self.delete_roi_window_confirm_button)
        # Create a widget to hold the action buttons
        self.delete_roi_window_action_buttons_widget = QWidget()
        self.delete_roi_window_action_buttons_widget.setObjectName("DeleteRoiWindowActionButtonsWidget")
        self.delete_roi_window_action_buttons_widget.setLayout(self.delete_roi_window_action_buttons_box)
        self.delete_roi_window_instance_vertical_box.addWidget(self.delete_roi_window_action_buttons_widget)

        # Set text for all attributes
        self.retranslate_ui(delete_roi_window_instance)
        # Create a central widget to hold the vertical layout box
        self.delete_roi_window_instance_central_widget = QWidget()
        self.delete_roi_window_instance_central_widget.setObjectName("DeleteRoiWindowInstanceCentralWidget")
        self.delete_roi_window_instance_central_widget.setLayout(self.delete_roi_window_instance_vertical_box)
        self.delete_roi_window_instance_vertical_box.setStretch(2, 4)
        # Set the central widget for the main window and style the window
        delete_roi_window_instance.setCentralWidget(self.delete_roi_window_instance_central_widget)
        delete_roi_window_instance.setStyleSheet(stylesheet)

        # Load the ROIs in
        self.display_rois_in_listViewKeep()
        # Set the selection mode to multi so that we can select multiple ROIs to delete
        self.delete_roi_window_keep_tree_view.setSelectionMode(QAbstractItemView.MultiSelection)
        self.delete_roi_window_delete_tree_view.setSelectionMode(QAbstractItemView.MultiSelection)

        QtCore.QMetaObject.connectSlotsByName(delete_roi_window_instance)

    def retranslate_ui(self, delete_roi_window_instance):
        _translate = QtCore.QCoreApplication.translate
        delete_roi_window_instance.setWindowTitle(_translate("DeleteRoiWindowInstance", "OnkoDICOM - Delete ROI(s)"))
        self.delete_roi_window_title.setText(_translate("DeleteRoiWindowTitle", "Delete ROI(s)"))
        self.delete_roi_window_instruction.setText(_translate("DeleteRoiWindowInstruction", "Move the Regions of Interest to be deleted to the right-hand side or vice versa"))
        self.delete_roi_window_keep_tree_view_label.setText(_translate("DeleteRoiWindowKeepTreeViewLabel", "To Keep"))
        self.delete_roi_window_delete_tree_view_label.setText(_translate("DeleteRoiWindowDeleteTreeViewLabel", "To Delete"))
        self.move_right_button.setText(_translate("MoveRightButton", "Move Right ->>>"))
        self.move_left_button.setText(_translate("MoveLeftButton", "<<<- Move Left"))
        self.delete_roi_window_cancel_button.setText(_translate("DeleteRoiWindowCancelButton", "Cancel"))
        self.delete_roi_window_confirm_button.setText(_translate("DeleteRoiWindowConfirmButton", "Confirm"))

    def on_cancel_button_clicked(self):
        self.close()

    def display_rois_in_listViewKeep(self):
        self.regions_of_interest_to_keep.clear()
        for roi_id, roi_dict in self.regions_of_interest_list.items():
            self.regions_of_interest_to_keep.append(roi_dict['name'])

        self.delete_roi_window_keep_tree_view.clear()
        self.delete_roi_window_keep_tree_view.setIndentation(0)

        self.item = QTreeWidgetItem(["item"])
        for index in self.regions_of_interest_to_keep:
            item = QTreeWidgetItem([index])
            self.delete_roi_window_keep_tree_view.addTopLevelItem(item)


    def move_right_button_onClicked(self):
        root_item = self.delete_roi_window_keep_tree_view.invisibleRootItem()
        for index in range(root_item.childCount()):
            item = root_item.child(index)
            if item in self.delete_roi_window_keep_tree_view.selectedItems():
                # This will get ROI name
                self.regions_of_interest_to_delete.append(item.text(0))

        # Move to the right column list
        self.delete_roi_window_delete_tree_view.clear()
        self.delete_roi_window_delete_tree_view.setIndentation(0)
        for roi in self.regions_of_interest_to_delete:
            item = QTreeWidgetItem([roi])
            self.delete_roi_window_delete_tree_view.addTopLevelItem(item)
            self.delete_roi_window_confirm_button.setEnabled(True)

        # Delete moved items from the left column list
        self.regions_of_interest_to_keep = [x for x in self.regions_of_interest_to_keep if x not in self.regions_of_interest_to_delete]

        self.delete_roi_window_keep_tree_view.clear()
        for index in self.regions_of_interest_to_keep:
            item = QTreeWidgetItem([index])
            self.delete_roi_window_keep_tree_view.addTopLevelItem(item)

    def move_left_button_onClicked(self):
        root_item = self.delete_roi_window_delete_tree_view.invisibleRootItem()

        for index in range(root_item.childCount()):
            item = root_item.child(index)
            if item in self.delete_roi_window_delete_tree_view.selectedItems():
                # This will get ROI name
                self.regions_of_interest_to_keep.append(item.text(0))

        # Move to the left column list
        self.delete_roi_window_keep_tree_view.clear()
        self.delete_roi_window_keep_tree_view.setIndentation(0)
        for roi in self.regions_of_interest_to_keep:
            item = QTreeWidgetItem([roi])
            self.delete_roi_window_keep_tree_view.addTopLevelItem(item)

        # Delete moved items from the right column list
        self.regions_of_interest_to_delete = [x for x in self.regions_of_interest_to_delete if x not in self.regions_of_interest_to_keep]

        self.delete_roi_window_delete_tree_view.clear()
        for index in self.regions_of_interest_to_delete:
            item = QTreeWidgetItem([index])
            self.delete_roi_window_delete_tree_view.addTopLevelItem(item)

        if len(self.regions_of_interest_to_delete) == 0:
            self.delete_roi_window_confirm_button.setEnabled(False)

    def confirm_button_onClicked(self):
        confirmation_dialog = QMessageBox.information(self, 'Delete ROI(s)?',
                                                      'Region(s) of Interest in the To Delete table will be deleted. '
                                                      'Would you like to continue?',
                                                      QMessageBox.Yes | QMessageBox.No)
        if confirmation_dialog == QMessageBox.Yes:
            progress_window = DeleteROIProgressWindow(self, QtCore.Qt.WindowTitleHint)
            progress_window.signal_roi_deleted.connect(self.on_rois_deleted)
            progress_window.start_deleting(self.dataset_rtss, self.regions_of_interest_to_delete)
            progress_window.show()

    def on_rois_deleted(self, new_rtss):
        self.deleting_rois_structure_tuple.emit((new_rtss, {"delete": self.regions_of_interest_to_delete}))
        QMessageBox.about(self, "Saved", "Regions of interest successfully deleted!")
        self.close()


class DeleteROIProgressWindow(QtWidgets.QDialog):
    """
    This class displays a window that advises the user that the RTSTRUCT is being modified, and then creates a new
    thread where the new RTSTRUCT is modified.
    """

    signal_roi_deleted = QtCore.Signal(pydicom.Dataset)   # Emits the new dataset

    def __init__(self, *args, **kwargs):
        super(DeleteROIProgressWindow, self).__init__(*args, **kwargs)
        layout = QtWidgets.QVBoxLayout()
        text = QtWidgets.QLabel("Deleting ROIs...")
        layout.addWidget(text)
        self.setWindowTitle("Please wait...")
        self.setFixedWidth(150)
        self.setLayout(layout)

        self.threadpool = QtCore.QThreadPool()

    def start_deleting(self, dataset_rtss, rois_to_delete):
        """
        Creates a thread that generates the new dataset object.
        :param dataset_rtss: Dataset of RTSS
        :param rois_to_delete: List of ROI names to be deleted
        """
        worker = Worker(ROI.delete_list_of_rois, dataset_rtss, rois_to_delete)
        worker.signals.result.connect(self.roi_deleted)
        self.threadpool.start(worker)

    def roi_deleted(self, result):
        """
        This method is called when the second thread completes generation of the new dataset object.
        :param result: The resulting dataset from the ROI.delete_roi function.
        """
        self.signal_roi_deleted.emit(result)
        self.close()
