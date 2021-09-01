import platform

from src.Controller.PathHandler import resource_path

from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.MovingDictContainer import MovingDictContainer

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtWidgets import QPushButton, QLabel, QSizePolicy


class ManualFusionWindow(object):
    """
    Class to hold the view of the manual fusion
    """
    def __init__(self):
        self.stylesheet_path = None
        self.patient_dict_container = None
        self.moving_dict_container = None

        self.manual_window = None
        self.close_button = None
        self.rotate_left_button = None
        self.rotate_right_button = None
        self.instruction_label = None
        self.image_primary = None
        self.image_secondary = None

        self.manual_fusion_layout = None
        self.button_box = None

    def setup_ui(self, manual_fusion_instance):

        # Basic Initialisation
        if platform.system() == 'Darwin':
            self.stylesheet_path = "res/stylesheet.qss"
        else:
            self.stylesheet_path = "res/stylesheet-win-linux.qss"
        stylesheet = open(resource_path(self.stylesheet_path)).read()
        manual_fusion_instance.setObjectName("ManualFusionInstance")
        manual_fusion_instance.setMinimumSize(800, 800)
        window_icon = QIcon()
        window_icon.addPixmap(QPixmap(resource_path("res/images/icon.ico")),
                              QIcon.Normal, QIcon.Off)
        self.manual_fusion_instance.setWindowIcon(window_icon)
        self.manual_fusion_instance.setStyleSheet(stylesheet)

        self.patient_dict_container = PatientDictContainer()
        self.moving_dict_container = MovingDictContainer()

        # Initialise Image Window
        self.manual_window = QtWidgets.QGraphicsView()
        self.image_primary = QtWidgets.QGraphicsScene()
        self.image_secondary = QtWidgets.QGraphicsScene()

        # Initialise Button Box and Controls
        self.button_box = QtWidgets.QHBoxLayout()
        self.close_button = QPushButton()
        self.instruction_label = QLabel()
        self.rotate_left_button = QPushButton()
        self.rotate_right_button = QPushButton()

        # Initialise main layout holder
        self.manual_fusion_layout = QtWidgets.QVBoxLayout()

        # Close Button
        self.close_button.setObjectName("ManualFusionCloseButton")
        self.close_button.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding,
                        QSizePolicy.MinimumExpanding))
        self.close_button.resize(self.close_button.sizeHint().width(),
                                 self.close_button.sizeHint().height())
        self.close_button.setCursor(
            QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.close_button.clicked.connect(self.close)  # Move to controller
        self.close_button.setProperty(
            "QPushButtonClass", "fail-button")

        # Instruction Label
        self.instruction_label.setObjectName("ManualFusionInstructionLabel")
        self.instruction_label.setAlignment(Qt.AlignCenter)

        # Left Rotate
        self.rotate_left_button.setObjectName("ManualFusionRotateLeftButton")
        self.rotate_left_button.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding,
                        QSizePolicy.MinimumExpanding))
        self.rotate_left_button.resize(
            self.rotate_left_button.sizeHint().width(),
            self.rotate_left_button.sizeHint().height())
        self.rotate_left_button.setCursor(
            QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.rotate_left_button.clicked.connect(self.rotate_left)
        self.rotate_left_button.setProperty(
            "QPushButtonClass", "zoom-button")

        # Right Rotate
        self.rotate_right_button.setObjectName("ManualFusionRotateRightButton")
        self.rotate_right_button.setSizePolicy(
            QSizePolicy(QSizePolicy.MinimumExpanding,
                        QSizePolicy.MinimumExpanding))
        self.rotate_right_button.resize(
            self.rotate_right_button.sizeHint().width(),
            self.rotate_right_button.sizeHint().height())
        self.rotate_right_button.setCursor(
            QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.rotate_right_button.clicked.connect(self.rotate_right)
        self.rotate_right_button.setProperty(
            "QPushButtonClass", "zoom-button")

        # TODO: Window

        # Add all items to layout
        self.button_box.addWidget(self.close_button)
        self.button_box.addWidget(self.instruction_label)
        self.button_box.addWidget(self.rotate_left_button)
        self.button_box.addWidget(self.rotate_right_button)

        self.manual_fusion_layout.addWidget(self.manual_window)
        self.manual_fusion_layout.addWidget(self.button_box)

        self.setLayout(self.manual_fusion_layout)

    def retranslate_ui(self, manual_fusion_instance):
        _translate = QtCore.QCoreApplication.translate
        self.manual_fusion_instance.setWindowTitle(
            _translate("ManualFusionInstance",
                       "Manual Image Fusion Controller"))
        self.close_button.setText(
            _translate("ManualFusionCloseButton", "Close"))
        self.instruction_label.setText(
            _translate("ManualFusionInstructionLabel",
                       "Enter info here..."))
        self.rotate_left_button.setText(
            _translate("ManualFusionRotateLeftButton", 'L'))
        self.rotate_right_button.setText(
            _translate("ManualFusionRotateRightButton", 'R'))

    def rotate_left(self):
        # Todo: Rotate Left
        print("Stub")

    def rotate_right(self):
        # Todo: Rotate right
        print("Stub")
