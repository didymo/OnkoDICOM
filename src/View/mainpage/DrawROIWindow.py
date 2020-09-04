from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import QCoreApplication, QThreadPool
from PyQt5.QtWidgets import QWidget, QTreeWidget, QTreeWidgetItem, QMessageBox, QHBoxLayout, QVBoxLayout, \
    QLabel, QLineEdit, QSizePolicy, QPushButton
from PyQt5.Qt import Qt
import os
from src.Model import ROI
from src.View.mainpage.DicomView import *

class UIDrawROIWindow():
    def setup_ui(self, draw_roi_window_instance):
        # Initialise a DrawROIWindow
        stylesheet = open("src/res/stylesheet.qss").read()
        window_icon = QIcon()
        window_icon.addPixmap(QPixmap("src/res/images/icon.ico"), QIcon.Normal, QIcon.Off)
        draw_roi_window_instance.setObjectName("DrawRoiWindowInstance")
        draw_roi_window_instance.setWindowIcon(window_icon)


        # Creating a vertical box to hold the details
        self.draw_roi_window_instance_vertical_box = QVBoxLayout()
        self.draw_roi_window_instance_vertical_box.setObjectName("DrawRoiWindowInstanceVerticalBox")

        # Creating a horizontal box to hold the image slice number, move up and down the image slice  and save button
        self.draw_roi_window_instance_image_slice_action_box = QHBoxLayout()
        self.draw_roi_window_instance_image_slice_action_box.setObjectName("DrawRoiWindowInstanceImageSliceActionBox")
        # Create a label for denoting the Image Slice Number
        self.image_slice_number_label = QLabel()
        self.image_slice_number_label.setObjectName("ImageSliceNumberLabel")
        self.image_slice_number_label.setAlignment(Qt.AlignRight)
        self.image_slice_number_label.setSizePolicy(QSizePolicy.Minimum,QSizePolicy.Minimum)
        self.image_slice_number_label.resize(
            self.image_slice_number_label.sizeHint().width(), self.image_slice_number_label.sizeHint().height())
        self.draw_roi_window_instance_image_slice_action_box.addStretch(1)
        self.draw_roi_window_instance_image_slice_action_box.addWidget(self.image_slice_number_label)
        # Create a line edit for containing the image slice number
        self.image_slice_number_line_edit = QLineEdit()
        self.image_slice_number_line_edit.setObjectName("ImageSliceNumberLineEdit")
        self.image_slice_number_line_edit.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.image_slice_number_line_edit.resize(self.image_slice_number_line_edit.sizeHint().width(), self.image_slice_number_line_edit.sizeHint().height())
        self.image_slice_number_line_edit.setEnabled(False)
        self.draw_roi_window_instance_image_slice_action_box.addWidget(self.image_slice_number_line_edit)
        # Create a button to move backward to the previous image
        self.image_slice_number_move_backward_button = QPushButton()
        self.image_slice_number_move_backward_button.setObjectName("ImageSliceNumberMoveBackwardButton")
        self.image_slice_number_move_backward_button.setSizePolicy(
            QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum))
        self.image_slice_number_move_backward_button.resize(
            self.image_slice_number_move_backward_button.sizeHint().width(),
            self.image_slice_number_move_backward_button.sizeHint().height())
        self.draw_roi_window_instance_image_slice_action_box.addWidget(self.image_slice_number_move_backward_button)
        # Create a button to move forward to the next image
        self.image_slice_number_move_forward_button = QPushButton()
        self.image_slice_number_move_forward_button.setObjectName("ImageSliceNumberMoveForwardButton")
        self.image_slice_number_move_forward_button.setSizePolicy(
            QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum))
        self.image_slice_number_move_forward_button.resize(
            self.image_slice_number_move_forward_button.sizeHint().width(),
            self.image_slice_number_move_forward_button.sizeHint().height())
        self.draw_roi_window_instance_image_slice_action_box.addWidget(self.image_slice_number_move_forward_button)
        # Create a save button to save all the changes
        self.draw_roi_window_instance_save_button = QPushButton()
        self.draw_roi_window_instance_save_button.setObjectName("DrawRoiWindowInstanceSaveButton")
        self.draw_roi_window_instance_save_button.setSizePolicy(
            QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum))
        self.draw_roi_window_instance_save_button.resize(
            self.draw_roi_window_instance_save_button.sizeHint().width(),
            self.draw_roi_window_instance_save_button.sizeHint().height())
        self.draw_roi_window_instance_save_button.setProperty("QPushButtonClass", "success-button")
        self.draw_roi_window_instance_image_slice_action_box.addStretch(1)
        self.draw_roi_window_instance_image_slice_action_box.addWidget(self.draw_roi_window_instance_save_button)
        # Create a widget to hold the image slice box
        self.draw_roi_window_instance_image_slice_action_widget = QWidget()
        self.draw_roi_window_instance_image_slice_action_widget.setObjectName("DrawRoiWindowInstanceImageSliceActionWidget")
        self.draw_roi_window_instance_image_slice_action_widget.setLayout(self.draw_roi_window_instance_image_slice_action_box)
        self.draw_roi_window_instance_vertical_box.addWidget(self.draw_roi_window_instance_image_slice_action_widget)
        self.draw_roi_window_instance_vertical_box.setStretch(0, 1)


        # Create a new Label to hold the pixmap
        self.image_slice_number_image_view = QLabel()
        self.image_slice_number_image_view.setPixmap(QPixmap("src/res/images/Capture.png"))
        self.image_slice_number_image_view.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
        self.image_slice_number_image_view.resize(
            self.image_slice_number_image_view.sizeHint().width(), self.image_slice_number_image_view.sizeHint().height())
        self.draw_roi_window_instance_vertical_box.addWidget(self.image_slice_number_image_view)
        self.draw_roi_window_instance_vertical_box.setStretch(1, 4)

        # Creating a horizontal box to hold the ROI draw action buttons: undo, redo, clear, tool
        self.draw_roi_window_instance_action_box = QHBoxLayout()
        self.draw_roi_window_instance_action_box.setObjectName("DrawRoiWindowInstanceActionBox")
        # Create a button to undo the draw
        self.draw_roi_window_instance_action_undo_button = QPushButton()
        self.draw_roi_window_instance_action_undo_button.setObjectName("DrawRoiWindowInstanceActionUndoButton")
        self.draw_roi_window_instance_action_undo_button.setSizePolicy(
            QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum))
        self.draw_roi_window_instance_action_undo_button.resize(
            self.draw_roi_window_instance_action_undo_button.sizeHint().width(),
            self.draw_roi_window_instance_action_undo_button.sizeHint().height())
        self.draw_roi_window_instance_action_box.addStretch(1)
        self.draw_roi_window_instance_action_box.addWidget(self.draw_roi_window_instance_action_undo_button)
        # Create a button to redo the draw
        self.draw_roi_window_instance_action_redo_button = QPushButton()
        self.draw_roi_window_instance_action_redo_button.setObjectName("DrawRoiWindowInstanceActionRedoButton")
        self.draw_roi_window_instance_action_redo_button.setSizePolicy(
            QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum))
        self.draw_roi_window_instance_action_redo_button.resize(
            self.draw_roi_window_instance_action_redo_button.sizeHint().width(),
            self.draw_roi_window_instance_action_redo_button.sizeHint().height())
        self.draw_roi_window_instance_action_box.addWidget(self.draw_roi_window_instance_action_redo_button)
        # Create a button to clear the draw
        self.draw_roi_window_instance_action_clear_button = QPushButton()
        self.draw_roi_window_instance_action_clear_button.setObjectName("DrawRoiWindowInstanceActionClearButton")
        self.draw_roi_window_instance_action_clear_button.setSizePolicy(
            QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum))
        self.draw_roi_window_instance_action_clear_button.resize(
            self.draw_roi_window_instance_action_clear_button.sizeHint().width(),
            self.draw_roi_window_instance_action_clear_button.sizeHint().height())
        self.draw_roi_window_instance_action_box.addWidget(self.draw_roi_window_instance_action_clear_button)
        # Create a button to tool the draw
        self.draw_roi_window_instance_action_tool_button = QPushButton()
        self.draw_roi_window_instance_action_tool_button.setObjectName("DrawRoiWindowInstanceActionToolButton")
        self.draw_roi_window_instance_action_tool_button.setSizePolicy(
            QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum))
        self.draw_roi_window_instance_action_tool_button.resize(
            self.draw_roi_window_instance_action_tool_button.sizeHint().width(),
            self.draw_roi_window_instance_action_tool_button.sizeHint().height())
        self.draw_roi_window_instance_action_box.addWidget(self.draw_roi_window_instance_action_tool_button)
        # Create a widget to hold the image slice box
        self.draw_roi_window_instance_action_widget = QWidget()
        self.draw_roi_window_instance_action_widget.setObjectName(
            "DrawRoiWindowInstanceActionWidget")
        self.draw_roi_window_instance_action_widget.setLayout(
            self.draw_roi_window_instance_action_box)
        self.draw_roi_window_instance_vertical_box.addWidget(self.draw_roi_window_instance_action_widget)
        self.draw_roi_window_instance_vertical_box.setStretch(0, 1)


        # Create a new central widget to hold the vertical box layout
        self.draw_roi_window_instance_central_widget = QWidget()
        self.draw_roi_window_instance_central_widget.setObjectName("DrawRoiWindowInstanceCentralWidget")
        self.draw_roi_window_instance_central_widget.setLayout(self.draw_roi_window_instance_vertical_box)

        self.retranslate_ui(draw_roi_window_instance)
        draw_roi_window_instance.setStyleSheet(stylesheet)
        draw_roi_window_instance.setCentralWidget(self.draw_roi_window_instance_central_widget)
        draw_roi_window_instance.setFixedSize(self.image_slice_number_image_view.size())
        QtCore.QMetaObject.connectSlotsByName(draw_roi_window_instance)



    def retranslate_ui(self, draw_roi_window_instance):
        _translate = QtCore.QCoreApplication.translate
        draw_roi_window_instance.setWindowTitle(_translate("DrawRoiWindowInstance", "OnkoDICOM - Draw ROI(s)"))
        self.image_slice_number_label.setText(_translate("ImageSliceNumberLabel", "Image Slice Number: "))
        self.image_slice_number_line_edit.setText(_translate("ImageSliceNumberLineEdit", "1"))
        self.image_slice_number_move_forward_button.setText(_translate("ImageSliceNumberMoveForwardButton", "Forward"))
        self.image_slice_number_move_backward_button.setText(_translate("ImageSliceNumberMoveBackwardButton", "Backward"))
        self.draw_roi_window_instance_save_button.setText(_translate("DrawRoiWindowInstanceSaveButton", "Save"))
        self.draw_roi_window_instance_action_undo_button.setText(_translate("DrawRoiWindowInstanceActionUndoButton", "Undo"))
        self.draw_roi_window_instance_action_redo_button.setText(_translate("DrawRoiWindowInstanceActionRedoButton", "Redo"))
        self.draw_roi_window_instance_action_clear_button.setText(_translate("DrawRoiWindowInstanceActionClearButton", "Clear"))
        self.draw_roi_window_instance_action_tool_button.setText(_translate("DrawRoiWindowInstanceActionToolButton", "Tool"))