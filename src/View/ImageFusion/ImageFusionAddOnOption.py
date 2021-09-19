from PySide6 import QtWidgets

from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.MovingDictContainer import MovingDictContainer


class ImageFusionOptions(object):
    """
    UI class that can be used by the AddOnOptions Class to allow the user
    customise their input parameters for auto-registration.
    """

    def __init__(self, window_options):
        self.window = window_options
        self.moving_dict_container = MovingDictContainer()
        self.patient_dict_container = PatientDictContainer()
        self.moving_image = None
        self.fixed_image = None
        self.resolution_staging = None
        self.smooth_sigma = None
        self.sampling_rate = None
        self.metric = None
        self.initial_grid_spacing = None
        self.grid_scale_factors = None
        self.interp_order = None
        self.default_number = None
        self.number_of_iterations = None

        self.get_patients_path()
        self.create_view()

    def get_patients_path(self):
        """
        Retrieve the patient's ID
        """
        if (self.patient_dict_container is not None and
                self.moving_dict_container is not None):
            self.fixed_image = self.patient_dict_container.path
            self.moving_image = self.moving_dict_container.path

    def create_view(self):
        """
        Create a table to hold all the ROI creation by isodose entries.
        """
        self.window.test_table = QtWidgets.QTableWidget(self.window.widget)
        self.window.test_table.setStyleSheet(
            "background-color: rgb(255, 255, 255);")
        self.window.test_table.setColumnCount(4)
        self.window.test_table.verticalHeader().hide()
        self.window.test_table.setHorizontalHeaderLabels(
            [" Isodose Level ", " Unit ", " ROI Name ", " Notes "])

        self.window.test_table.setVisible(False)

        # Removing the ability to edit tables with immediate click
        self.window.test_table.setEditTriggers(
            QtWidgets.QTreeView.NoEditTriggers |
            QtWidgets.QTreeView.NoEditTriggers)

