from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QLayout, QLabel, QSpinBox, \
    QComboBox, QSizePolicy, QDoubleSpinBox, QLineEdit

from src.Model.GetPatientInfo import DicomTree
from src.Model.MovingDictContainer import MovingDictContainer
from src.Model.PatientDictContainer import PatientDictContainer


class ImageFusionOptions(object):
    """
    UI class that can be used by the AddOnOptions Class to allow the user
    customise their input parameters for auto-registration.
    """

    def __init__(self, window_options):
        self.auto_image_fusion_frame = QtWidgets.QFrame()
        self.window = window_options
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

        self.get_patients_info()
        self.create_view()
        self.setupUi()

    def get_patients_info(self):
        """
        Retrieve the patient's study description of the fixed image
        and for the moving image (if it exists).
        """
        patient_dict_container = PatientDictContainer()
        if not patient_dict_container.is_empty():
            filename = patient_dict_container.filepaths[0]
            dicom_tree_slice = DicomTree(filename)
            dict_tree = dicom_tree_slice.dict
            self.fixed_image = dict_tree["Study Description"][0]

        moving_dict_container = MovingDictContainer()
        if not moving_dict_container.is_empty():
            filename = moving_dict_container.filepaths[0]
            dicom_tree_slice = DicomTree(filename)
            dict_tree = dicom_tree_slice.dict
            self.moving_image = dict_tree["Study Description"][0]

    def create_view(self):
        """
        Create a table to hold all the ROI creation by isodose entries.
        """
        self.auto_image_fusion_frame.setVisible(False)

    def setVisible(self, visibility):
        self.auto_image_fusion_frame.setVisible(visibility)

    def setupUi(self):
        # Create a Widget and set layout to a GridLayout
        self.gridLayoutWidget = QWidget()
        self.gridLayout = QtWidgets.QGridLayout(self.gridLayoutWidget)
        self.gridLayout.setSizeConstraint(QLayout.SetDefaultConstraint)
        self.gridLayout.setContentsMargins(10, 10, 10, 10)
        self.gridLayout.setVerticalSpacing(7)

        # Create horizontal spacer in the middle of the grid
        hspacer = QtWidgets.QSpacerItem(QtWidgets.QSizePolicy.Expanding,
                                        QtWidgets.QSizePolicy.Minimum)
        self.gridLayout.addItem(hspacer, 0, 5, 16, 1)

        # Labels
        self.fixed_image_label = QLabel("Fixed Image: ")
        fixed_image_sizePolicy = QSizePolicy(QSizePolicy.Maximum,
                                             QSizePolicy.Preferred)
        fixed_image_sizePolicy.setHorizontalStretch(0)
        fixed_image_sizePolicy.setVerticalStretch(0)
        fixed_image_sizePolicy.setHeightForWidth(
            self.fixed_image_label.sizePolicy().hasHeightForWidth())

        self.fixed_image_label.setAlignment(Qt.AlignRight |
                                            Qt.AlignTrailing |
                                            Qt.AlignVCenter)

        self.fixed_image_placeholder \
            = QLabel("This is a placeholder for fixed image")

        self.fixed_image_placeholder.setText(str(self.fixed_image))
        self.fixed_image_placeholder.setSizePolicy(
            QSizePolicy.Maximum,
            QSizePolicy.Maximum)
        self.fixed_image_placeholder.resize(
            self.fixed_image_placeholder.sizeHint().width(),
            self.fixed_image_placeholder.sizeHint().height())


        self.moving_image_label = QLabel("Moving Image: ")
        moving_image_label_sizePolicy = QSizePolicy(QSizePolicy.Maximum,
                                                    QSizePolicy.Maximum)
        moving_image_label_sizePolicy.setHorizontalStretch(0)
        moving_image_label_sizePolicy.setVerticalStretch(0)
        moving_image_label_sizePolicy.setHeightForWidth(
            self.moving_image_label.sizePolicy().hasHeightForWidth())
        self.moving_image_label.setSizePolicy(moving_image_label_sizePolicy)

        self.moving_image_placeholder = QLabel("This is a placeholder")
        self.moving_image_placeholder.setText(str(self.moving_image))
        self.moving_image_placeholder.setSizePolicy(
            QSizePolicy.Maximum,
            QSizePolicy.Maximum)
        self.moving_image_placeholder.resize(
            self.moving_image_placeholder.sizeHint().width(),
            self.moving_image_placeholder.sizeHint().height())

        self.gridLayout.addWidget(self.fixed_image_label, 0, 0)
        self.gridLayout.addWidget(self.fixed_image_placeholder, 0, 1)
        self.gridLayout.addWidget(self.moving_image_label, 0, 2)
        self.gridLayout.addWidget(self.moving_image_placeholder, 0, 3)

        # Resolution Staging
        self.resolution_staging_label = QLabel("Resolution Staging")
        self.resolution_staging_label.setAlignment(
            Qt.AlignLeft | Qt.AlignTrailing | Qt.AlignVCenter)
        self.gridLayout.addWidget(self.resolution_staging_label, 1, 0)

        self.resolution_staging_spinBox = QSpinBox(self.gridLayoutWidget)
        self.resolution_staging_spinBox.setSizePolicy(QSizePolicy.Minimum,
                                                      QSizePolicy.Fixed)
        self.resolution_staging_spinBox.setValue(8)
        self.gridLayout.addWidget(self.resolution_staging_spinBox, 1, 1)

        # Smooth Sigmas
        self.smooth_sigma_label = QLabel("Smooth Sigma")
        self.smooth_sigma_label.setAlignment(
            Qt.AlignLeft | Qt.AlignTrailing | Qt.AlignVCenter)
        self.gridLayout.addWidget(self.smooth_sigma_label, 1, 2)

        self.smooth_sigmas_spinBox = QLineEdit()
        self.smooth_sigmas_spinBox.setSizePolicy(QSizePolicy.Minimum,
                                                 QSizePolicy.Fixed)
        self.smooth_sigmas_spinBox.setText("[4,2,0]")
        self.gridLayout.addWidget(self.smooth_sigmas_spinBox, 1, 3)

        # Sampling Rate
        self.sampling_rate_label = QLabel("Sampling Rate")
        self.sampling_rate_label.setAlignment(
            Qt.AlignLeft | Qt.AlignTrailing | Qt.AlignVCenter)
        self.gridLayout.addWidget(self.sampling_rate_label, 2, 0)

        self.sampling_rate_spinBox = QDoubleSpinBox(self.gridLayoutWidget)
        self.sampling_rate_spinBox.setValue(0.25)
        self.sampling_rate_spinBox.setMinimum(0)
        self.sampling_rate_spinBox.setMaximum(1)
        self.sampling_rate_spinBox.setSingleStep(0.01)
        self.sampling_rate_spinBox.setSizePolicy(QSizePolicy.Minimum,
                                                 QSizePolicy.Fixed)
        self.gridLayout.addWidget(self.sampling_rate_spinBox, 2, 1)

        # Optimiser
        self.optimiser_label = QLabel("Optimiser")
        self.optimiser_label.setAlignment(
            Qt.AlignLeft | Qt.AlignTrailing | Qt.AlignVCenter)
        self.gridLayout.addWidget(self.optimiser_label, 2, 2)

        self.optimiser_comboBox = QComboBox(self.gridLayoutWidget)
        self.optimiser_comboBox.addItem("lbfgsb")
        self.optimiser_comboBox.addItem("gradient_descent")
        self.optimiser_comboBox.addItem("gradient_descent_line_search")
        self.gridLayout.addWidget(self.optimiser_comboBox, 2, 3)

        # Metric
        self.metric_label = QLabel("Metric")
        self.metric_label.setAlignment(
            QtCore.Qt.AlignLeft | Qt.AlignTrailing | Qt.AlignVCenter)
        self.gridLayout.addWidget(self.metric_label, 3, 0)

        # Default to mean squares
        self.metric_comboBox = QComboBox()
        self.metric_comboBox.addItem("correlation")
        self.metric_comboBox.addItem("mean_squares")
        self.metric_comboBox.addItem("mattes_mi")
        self.metric_comboBox.addItem("joint_hist_mi")
        self.metric_comboBox.setCurrentIndex(1)
        self.gridLayout.addWidget(self.metric_comboBox, 3, 1)

        # Initial Grid Spacing
        self.initial_grid_spacing_label = QLabel("Initial Grid Spacing")
        self.initial_grid_spacing_label.setAlignment(
            Qt.AlignLeft | Qt.AlignTrailing | Qt.AlignVCenter)
        self.gridLayout.addWidget(self.initial_grid_spacing_label, 3, 2)

        self.initial_grid_spacing_spinbox = QSpinBox(self.gridLayoutWidget)
        self.initial_grid_spacing_spinbox.setSizePolicy(QSizePolicy.Minimum,
                                                        QSizePolicy.Fixed)
        self.gridLayout.addWidget(self.initial_grid_spacing_spinbox, 3, 3)

        # Grid Scale Factors
        self.grid_scale_factors_label = QLabel("Grid Scale Factors")
        self.grid_scale_factors_label.setAlignment(
            Qt.AlignLeft | Qt.AlignTrailing | Qt.AlignVCenter)
        self.gridLayout.addWidget(self.grid_scale_factors_label, 4, 0)

        self.grid_scale_spinBox = QSpinBox(self.gridLayoutWidget)
        self.grid_scale_spinBox.setSizePolicy(QSizePolicy.Minimum,
                                              QSizePolicy.Fixed)
        self.gridLayout.addWidget(self.grid_scale_spinBox, 4, 1)

        # Interp Order
        self.interp_order_label = QLabel("Interp Order")
        self.interp_order_label.setAlignment(
            Qt.AlignLeft | Qt.AlignTrailing | Qt.AlignVCenter)
        self.gridLayout.addWidget(self.interp_order_label, 4, 2)

        self.interp_order_spinbox = QSpinBox(self.gridLayoutWidget)
        self.interp_order_spinbox.setValue(2)
        self.interp_order_spinbox.setSizePolicy(QSizePolicy.Minimum,
                                                QSizePolicy.Fixed)
        self.gridLayout.addWidget(self.interp_order_spinbox, 4, 3)

        # Default Numbers
        self.default_numbers_label = QLabel("Default Numbers")
        self.default_numbers_label.setAlignment(
            Qt.AlignLeft | Qt.AlignTrailing | Qt.AlignVCenter)
        self.gridLayout.addWidget(self.default_numbers_label, 5, 0)

        self.default_number_spinBox = QSpinBox(self.gridLayoutWidget)
        self.default_number_spinBox.setRange(-2147483648, 2147483647)
        self.default_number_spinBox.setValue(-1000)
        self.default_number_spinBox.setSizePolicy(QSizePolicy.Minimum,
                                                  QSizePolicy.Fixed)
        self.gridLayout.addWidget(self.default_number_spinBox, 5, 1)

        # Number of Iterations
        self.no_of_iterations_label = QLabel("Number of Iterations")
        self.no_of_iterations_label.setAlignment(
            Qt.AlignLeft | Qt.AlignTrailing | Qt.AlignVCenter)
        self.gridLayout.addWidget(self.no_of_iterations_label, 5, 2)

        self.no_of_iterations_spinBox = QSpinBox(self.gridLayoutWidget)
        self.no_of_iterations_spinBox.setSizePolicy(QSizePolicy.Minimum,
                                                    QSizePolicy.Fixed)
        self.no_of_iterations_spinBox.setRange(0, 100)
        self.no_of_iterations_spinBox.setValue(50)
        self.gridLayout.addWidget(self.no_of_iterations_spinBox, 5, 3)

        # Set layout of frame to the gridlayout widget
        self.auto_image_fusion_frame.setLayout(self.gridLayout)
