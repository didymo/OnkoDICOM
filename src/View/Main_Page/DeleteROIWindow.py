from PyQt5 import QtCore, QtWidgets
from PyQt5 import QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QTreeWidgetItem, \
    QMessageBox
import os
from src.Model import ROI

class Ui_DeleteROIWindow(QDialog):
    def setupUi(self, DeleteROIWindow, rois, dataset_rtss, newStructure):

        self.listToKeep = []
        self.listToDelete = []
        self.rois = rois
        self.dataset_rtss = dataset_rtss
        self.newStructure = newStructure

        DeleteROIWindow.setObjectName("DeleteROIWindow")
        DeleteROIWindow.setFixedSize(800, 606)
        DeleteROIWindow.setWindowTitle("Delete ROI")
        DeleteROIWindow.setWindowIcon(QtGui.QIcon("src/res/images/icon.ico"))

        self.centralwidget = QtWidgets.QWidget(DeleteROIWindow)
        self.centralwidget.setObjectName("centralwidget")

        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")

        self.frame = QtWidgets.QFrame(self.centralwidget)
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")

        self.listViewKeep = QtWidgets.QTreeWidget(self.frame)
        self.listViewKeep.setGeometry(QtCore.QRect(70, 120, 221, 331))
        self.listViewKeep.setHeaderHidden(True)
        self.listViewKeep.setObjectName("listViewKeep")
        self.listViewKeep.setStyleSheet("border: 2px solid green;")

        self.listViewDelete = QtWidgets.QTreeWidget(self.frame)
        self.listViewDelete.setGeometry(QtCore.QRect(480, 120, 221, 331))
        self.listViewDelete.setHeaderHidden(True)
        self.listViewDelete.setObjectName("listViewDelete")
        self.listViewDelete.setStyleSheet("border: 2px solid red;")


        self.cancelButton = QtWidgets.QPushButton(self.frame)
        self.cancelButton.setGeometry(QtCore.QRect(220, 490, 91, 31))
        self.cancelButton.setObjectName("cancelButton")
        self.cancelButton.setText("Cancel")
        self.cancelButton.clicked.connect(self.on_cancel_button_clicked)

        self.confirmButton = QtWidgets.QPushButton(self.frame)
        self.confirmButton.setGeometry(QtCore.QRect(460, 490, 91, 31))
        self.confirmButton.setObjectName("confirmButton")
        self.confirmButton.setText("Delete")
        self.confirmButton.setEnabled(False)
        self.confirmButton.clicked.connect(self.confirm_button_onClicked)

        self.moveRightButton = QtWidgets.QPushButton(self.frame)
        self.moveRightButton.setGeometry(QtCore.QRect(340, 170, 90, 31))
        self.moveRightButton.setObjectName("moveRightButton")
        self.moveRightButton.setText("Move Right -->")
        self.moveRightButton.clicked.connect(self.move_right_button_onClicked)

        self.moveLeftButton = QtWidgets.QPushButton(self.frame)
        self.moveLeftButton.setGeometry(QtCore.QRect(340, 230, 90, 31))
        self.moveLeftButton.setObjectName("moveLeftButton")
        self.moveLeftButton.setText("Move Left <--")
        self.moveLeftButton.clicked.connect(self.move_left_button_onClicked)

        self.keepLabel = QtWidgets.QLabel(self.frame)
        self.keepLabel.setGeometry(QtCore.QRect(120, 70, 91, 41))
        self.keepLabel.setObjectName("keepLabel")
        self.keepLabel.setText("<html><head/><body><p><span style=\" font-size:14pt; font-weight:600;\">TO KEEP:</span></p></body></html>")

        self.deleteLabel = QtWidgets.QLabel(self.frame)
        self.deleteLabel.setGeometry(QtCore.QRect(530, 70, 121, 41))
        self.deleteLabel.setObjectName("deleteLabel")
        self.deleteLabel.setText("<html><head/><body><p><span style=\" font-size:14pt; font-weight:600;\">TO DELETE:</span></p></body></html>")

        self.headerLabel = QtWidgets.QLabel(self.frame)
        self.headerLabel.setGeometry(QtCore.QRect(200, 30, 381, 16))
        self.headerLabel.setObjectName("headerLabel")
        self.headerLabel.setText("<html><head/><body><p><span style=\" font-size:9pt;\">Move the Regions of Interest to be deleted to the right-hand side.</span></p></body></html>")

        self.gridLayout.addWidget(self.frame, 0, 0, 1, 1)

        DeleteROIWindow.setCentralWidget(self.centralwidget)

        self.display_rois_in_listViewKeep()

        QtCore.QMetaObject.connectSlotsByName(DeleteROIWindow)

    def on_cancel_button_clicked(self):
        self.close()

    def display_rois_in_listViewKeep(self):
        self.listToKeep.clear()
        for roi_id, roi_dict in self.rois.items():
            self.listToKeep.append(roi_dict['name'])

        self.listViewKeep.clear()
        self.listViewKeep.setIndentation(0)
        self.item = QTreeWidgetItem(["item"])
        for index in self.listToKeep:
            item = QTreeWidgetItem([index])
            item.setCheckState(0, Qt.Unchecked)
            self.listViewKeep.addTopLevelItem(item)


    def move_right_button_onClicked(self):
        root_item = self.listViewKeep.invisibleRootItem()
        for index in range(root_item.childCount()):
            item = root_item.child(index)
            if item.checkState(0) == Qt.Checked:
                self.listToDelete.append(item.text(0)) # This will get ROI name
            item.setCheckState(0, Qt.Unchecked)

        self.confirmButton.setEnabled(True)

        ## Move to the right column list
        self.listViewDelete.clear()
        self.listViewDelete.setIndentation(0)
        for roi in self.listToDelete:
            item = QTreeWidgetItem([roi])
            item.setCheckState(0, Qt.Unchecked)
            self.listViewDelete.addTopLevelItem(item)

        ## Delete moved items from the left column list
        self.listToKeep = [x for x in self.listToKeep if x not in self.listToDelete]

        self.listViewKeep.clear()
        for index in self.listToKeep:
            item = QTreeWidgetItem([index])
            item.setCheckState(0, Qt.Unchecked)
            self.listViewKeep.addTopLevelItem(item)


    def move_left_button_onClicked(self):
        root_item = self.listViewDelete.invisibleRootItem()

        for index in range(root_item.childCount()):
            item = root_item.child(index)
            if item.checkState(0) == Qt.Checked:
                self.listToKeep.append(item.text(0)) # This will get ROI name
            item.setCheckState(0, Qt.Unchecked)


        ## Move to the left column list
        self.listViewKeep.clear()
        self.listViewKeep.setIndentation(0)
        for roi in self.listToKeep:
            item = QTreeWidgetItem([roi])
            item.setCheckState(0, Qt.Unchecked)
            self.listViewKeep.addTopLevelItem(item)

        ## Delete moved items from the right column list
        self.listToDelete = [x for x in self.listToDelete if x not in self.listToKeep]

        self.listViewDelete.clear()
        for index in self.listToDelete:
            item = QTreeWidgetItem([index])
            item.setCheckState(0, Qt.Unchecked)
            self.listViewDelete.addTopLevelItem(item)

        if len(self.listToDelete) == 0:
            self.confirmButton.setEnabled(False)

    def confirm_button_onClicked(self):

        confirmation_dialog = QMessageBox.information(self, 'Delete ROIs?',
                                                      'ROIs in the to-delete table will be deleted. '
                                                      'Would you like to continue?',
                                                      QMessageBox.Yes | QMessageBox.No)

        if confirmation_dialog == QMessageBox.Yes:
            for item in self.listToDelete:
                new_dataset = ROI.delete_roi(self.dataset_rtss, item)

            self.newStructure.emit(new_dataset)
            self.close()





