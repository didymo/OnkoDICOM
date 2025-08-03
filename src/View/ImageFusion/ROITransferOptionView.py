from PySide6 import QtWidgets
from PySide6.QtWidgets import QPushButton

from src.Controller.ROIOptionsController import ROITransferOption
from src.View.ImageFusion.TranslateRotateMenu import TranslateRotateMenu

class ROITransferOptionView(QtWidgets.QWidget):
    def __init__(self, fixed_dict_structure_modified_function,
                 moving_dict_structure_modified_function):
        """
        Initialize layout
        :param fixed_dict_structure_modified_function: function to call when
        the fixed image's rtss is modified
        :param moving_dict_structure_modified_function: function to call when
        the moving image's rtss is modified
        """
        QtWidgets.QWidget.__init__(self)

        self.stacked_layout = QtWidgets.QStackedLayout()
        self.init_main_menu(fixed_dict_structure_modified_function, moving_dict_structure_modified_function)
        self.init_translate_rotate_menu()

        self.setLayout(self.stacked_layout)

    def init_main_menu(self, fixed_dict_structure_modified_function, moving_dict_structure_modified_function):
        self.main_menu_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        self.roi_transfer_handler = \
            ROITransferOption(fixed_dict_structure_modified_function,
                              moving_dict_structure_modified_function)

        self.translate_rotate_button = QPushButton("Translate/Rotate")
        self.roi_transfer_option_button = QPushButton("Open ROI Transfer Options")

        for btn in [self.translate_rotate_button, self.roi_transfer_option_button]:
            btn.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
            btn.setMinimumWidth(150)

        self.translate_rotate_button.clicked.connect(self.show_translate_rotate_menu)
        self.roi_transfer_option_button.clicked.connect(self.open_roi_transfer_option)

        layout.addWidget(self.translate_rotate_button)
        layout.addWidget(self.roi_transfer_option_button)
        self.main_menu_widget.setLayout(layout)
        self.stacked_layout.addWidget(self.main_menu_widget)

    def init_translate_rotate_menu(self):
        self.translate_rotate_menu = TranslateRotateMenu(self.show_main_menu)
        self.stacked_layout.addWidget(self.translate_rotate_menu)

    def show_translate_rotate_menu(self):
        self.stacked_layout.setCurrentWidget(self.translate_rotate_menu)

    def show_main_menu(self):
        self.stacked_layout.setCurrentWidget(self.main_menu_widget)

    def open_roi_transfer_option(self):
        self.roi_transfer_handler.show_roi_transfer_options()