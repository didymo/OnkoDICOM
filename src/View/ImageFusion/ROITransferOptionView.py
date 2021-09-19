from PySide6 import QtWidgets
from PySide6.QtWidgets import QPushButton

from src.Controller.ROIOptionsController import ROITransferOption


class ROITransferOptionView(QtWidgets.QWidget):
    def __init__(self, fixed_dict_structure_modified_function, moving_dict_structure_modified_function):
        """
        Initialize layout
        """
        QtWidgets.QWidget.__init__(self)

        # Create the layout
        self.roi_transfer_option_layout = QtWidgets.QHBoxLayout()

        self.roi_transfer_handler = ROITransferOption(fixed_dict_structure_modified_function,
                                                      moving_dict_structure_modified_function)

        # Create roi transfer option button
        self.roi_transfer_option_button = QPushButton()
        self.roi_transfer_option_button.setText("Open ROI Transfer Options")
        self.roi_transfer_option_button.clicked.connect(self.open_roi_transfer_option)

        # Set layout
        self.roi_transfer_option_layout.addWidget(self.roi_transfer_option_button)
        self.setLayout(self.roi_transfer_option_layout)

    def open_roi_transfer_option(self):
        self.roi_transfer_handler.show_roi_transfer_options()
