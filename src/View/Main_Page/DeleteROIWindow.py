from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5 import QtGui
from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QVBoxLayout, QWidget, QHBoxLayout, QPushButton
import os
from src.Model import ROI
from src.View.Main_Page import StructureTab

class Ui_DeleteROIWindow(QDialog):
    def setupUi(self, DeleteROIWindow):

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

        self.listViewKeep = QtWidgets.QTreeView(self.frame)
        self.listViewKeep.setGeometry(QtCore.QRect(70, 120, 221, 331))
        self.listViewKeep.setObjectName("listViewKeep")
        self.listViewKeep.setStyleSheet("border: 2px solid green;")

        self.listViewDelete = QtWidgets.QTreeView(self.frame)
        self.listViewDelete.setGeometry(QtCore.QRect(480, 120, 221, 331))
        self.listViewDelete.setObjectName("listViewDelete")
        self.listViewDelete.setStyleSheet("border: 2px solid red;")


        self.cancelButton = QtWidgets.QPushButton(self.frame)
        self.cancelButton.setGeometry(QtCore.QRect(220, 490, 91, 31))
        self.cancelButton.setObjectName("cancelButton")
        self.cancelButton.setText("Cancel")

        self.confirmButton = QtWidgets.QPushButton(self.frame)
        self.confirmButton.setGeometry(QtCore.QRect(460, 490, 91, 31))
        self.confirmButton.setObjectName("confirmButton")
        self.confirmButton.setText("Confirm")

        self.moveRightButton = QtWidgets.QPushButton(self.frame)
        self.moveRightButton.setGeometry(QtCore.QRect(340, 170, 90, 31))
        self.moveRightButton.setObjectName("moveRightButton")
        self.moveRightButton.setText("Move Right -->")

        self.moveLeftButton = QtWidgets.QPushButton(self.frame)
        self.moveLeftButton.setGeometry(QtCore.QRect(340, 230, 90, 31))
        self.moveLeftButton.setObjectName("moveLeftButton")
        self.moveLeftButton.setText("Move Left <--")

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

        QtCore.QMetaObject.connectSlotsByName(DeleteROIWindow)


