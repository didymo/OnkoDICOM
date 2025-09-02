from PySide6 import QtWidgets
from PySide6.QtWidgets import QPushButton

from src.Controller.ROIOptionsController import ROITransferOption

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

        self.setLayout(self.stacked_layout)

    def init_main_menu(self, fixed_dict_structure_modified_function, moving_dict_structure_modified_function):
        self.main_menu_widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        self.roi_transfer_handler = \
            ROITransferOption(fixed_dict_structure_modified_function,
                              moving_dict_structure_modified_function)

        self.roi_transfer_option_button = QPushButton("Open ROI Transfer Options")
        self.roi_transfer_option_button.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        self.roi_transfer_option_button.setMinimumWidth(150)
        self.roi_transfer_option_button.clicked.connect(self.open_roi_transfer_option)

        layout.addWidget(self.roi_transfer_option_button)
        self.main_menu_widget.setLayout(layout)
        self.stacked_layout.addWidget(self.main_menu_widget)

    def show_main_menu(self):
        self.stacked_layout.setCurrentWidget(self.main_menu_widget)

    def open_roi_transfer_option(self):
        self.roi_transfer_handler.show_roi_transfer_options()