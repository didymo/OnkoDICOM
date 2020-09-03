from PyQt5 import QtCore, QtWidgets
from PyQt5 import QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QTreeWidgetItem, \
    QMessageBox, QAbstractItemView
import os
from src.Model import ROI

class Ui_DeleteROIWindow(QDialog):
    def setupUi(self, DeleteROIWindow, rois, dataset_rtss, structure_delete):

        self.list_to_keep = []
        self.list_to_delete = []
        self.rois = rois
        self.dataset_rtss = dataset_rtss
        self.structure_delete = structure_delete

        DeleteROIWindow.setFixedSize(800, 606)
        DeleteROIWindow.setWindowTitle("Delete ROI")
        DeleteROIWindow.setWindowIcon(QtGui.QIcon("src/res/images/icon.ico"))

        self.central_widget = QtWidgets.QWidget(DeleteROIWindow)

        self.grid_layout = QtWidgets.QGridLayout(self.central_widget)

        self.frame = QtWidgets.QFrame(self.central_widget)
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)

        self.to_keep_tree = QtWidgets.QTreeWidget(self.frame)
        self.to_keep_tree.setGeometry(QtCore.QRect(70, 120, 221, 331))
        self.to_keep_tree.setHeaderHidden(True)
        self.to_keep_tree.setStyleSheet("border: 2px solid green;")

        self.to_delete_tree = QtWidgets.QTreeWidget(self.frame)
        self.to_delete_tree.setGeometry(QtCore.QRect(480, 120, 221, 331))
        self.to_delete_tree.setHeaderHidden(True)
        self.to_delete_tree.setStyleSheet("border: 2px solid red;")

        self.cancel_button = QtWidgets.QPushButton(self.frame)
        self.cancel_button.setGeometry(QtCore.QRect(220, 490, 91, 31))
        self.cancel_button.setText("Cancel")
        self.cancel_button.clicked.connect(self.on_cancel_button_clicked)

        self.confirm_button = QtWidgets.QPushButton(self.frame)
        self.confirm_button.setGeometry(QtCore.QRect(460, 490, 91, 31))
        self.confirm_button.setText("Delete")
        self.confirm_button.setEnabled(False)
        self.confirm_button.clicked.connect(self.confirm_button_onClicked)

        self.move_right_button = QtWidgets.QPushButton(self.frame)
        self.move_right_button.setGeometry(QtCore.QRect(340, 170, 90, 31))
        self.move_right_button.setText("Move Right -->")
        self.move_right_button.clicked.connect(self.move_right_button_onClicked)

        self.move_left_button = QtWidgets.QPushButton(self.frame)
        self.move_left_button.setGeometry(QtCore.QRect(340, 230, 90, 31))
        self.move_left_button.setText("Move Left <--")
        self.move_left_button.clicked.connect(self.move_left_button_onClicked)

        self.to_keep_label = QtWidgets.QLabel(self.frame)
        self.to_keep_label.setGeometry(QtCore.QRect(120, 70, 91, 41))
        self.to_keep_label.setText("<html><head/><body><p><span style=\" font-size:14pt; font-weight:600;\">TO KEEP:</span></p></body></html>")

        self.to_delete_label = QtWidgets.QLabel(self.frame)
        self.to_delete_label.setGeometry(QtCore.QRect(530, 70, 121, 41))
        self.to_delete_label.setText("<html><head/><body><p><span style=\" font-size:14pt; font-weight:600;\">TO DELETE:</span></p></body></html>")

        self.instruction_label = QtWidgets.QLabel(self.frame)
        self.instruction_label.setGeometry(QtCore.QRect(200, 30, 381, 16))
        self.instruction_label.setText("<html><head/><body><p><span style=\" font-size:9pt;\">Move the Regions of Interest to be deleted to the right-hand side.</span></p></body></html>")

        self.grid_layout.addWidget(self.frame, 0, 0, 1, 1)

        DeleteROIWindow.setCentralWidget(self.central_widget)

        self.display_rois_in_listViewKeep()

        self.to_keep_tree.setSelectionMode(QAbstractItemView.MultiSelection)
        self.to_delete_tree.setSelectionMode(QAbstractItemView.MultiSelection)

        QtCore.QMetaObject.connectSlotsByName(DeleteROIWindow)

    def on_cancel_button_clicked(self):
        self.close()

    def display_rois_in_listViewKeep(self):
        self.list_to_keep.clear()
        for roi_id, roi_dict in self.rois.items():
            self.list_to_keep.append(roi_dict['name'])

        self.to_keep_tree.clear()
        self.to_keep_tree.setIndentation(0)

        self.item = QTreeWidgetItem(["item"])
        for index in self.list_to_keep:
            item = QTreeWidgetItem([index])
            self.to_keep_tree.addTopLevelItem(item)


    def move_right_button_onClicked(self):
        root_item = self.to_keep_tree.invisibleRootItem()
        for index in range(root_item.childCount()):
            item = root_item.child(index)
            if item in self.to_keep_tree.selectedItems():
                # This will get ROI name
                self.list_to_delete.append(item.text(0))

        # Move to the right column list
        self.to_delete_tree.clear()
        self.to_delete_tree.setIndentation(0)
        for roi in self.list_to_delete:
            item = QTreeWidgetItem([roi])
            self.to_delete_tree.addTopLevelItem(item)
            self.confirm_button.setEnabled(True)

        # Delete moved items from the left column list
        self.list_to_keep = [x for x in self.list_to_keep if x not in self.list_to_delete]

        self.to_keep_tree.clear()
        for index in self.list_to_keep:
            item = QTreeWidgetItem([index])
            self.to_keep_tree.addTopLevelItem(item)

    def move_left_button_onClicked(self):
        root_item = self.to_delete_tree.invisibleRootItem()

        for index in range(root_item.childCount()):
            item = root_item.child(index)
            if item in self.to_delete_tree.selectedItems():
                # This will get ROI name
                self.list_to_keep.append(item.text(0))

        # Move to the left column list
        self.to_keep_tree.clear()
        self.to_keep_tree.setIndentation(0)
        for roi in self.list_to_keep:
            item = QTreeWidgetItem([roi])
            self.to_keep_tree.addTopLevelItem(item)

        # Delete moved items from the right column list
        self.list_to_delete = [x for x in self.list_to_delete if x not in self.list_to_keep]

        self.to_delete_tree.clear()
        for index in self.list_to_delete:
            item = QTreeWidgetItem([index])
            self.to_delete_tree.addTopLevelItem(item)

        if len(self.list_to_delete) == 0:
            self.confirm_button.setEnabled(False)

    def confirm_button_onClicked(self):

        confirmation_dialog = QMessageBox.information(self, 'Delete ROIs?',
                                                      'ROIs in the to-delete table will be deleted. '
                                                      'Would you like to continue?',
                                                      QMessageBox.Yes | QMessageBox.No)

        if confirmation_dialog == QMessageBox.Yes:
            for item in self.list_to_delete:
                new_dataset = ROI.delete_roi(self.dataset_rtss, item)

            self.structure_delete.emit((new_dataset, {"delete": self.list_to_delete}))
            self.close()





