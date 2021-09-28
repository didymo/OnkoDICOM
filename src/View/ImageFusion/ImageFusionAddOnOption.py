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

        self.reg_method = None
        self.metric = None
        self.optimiser = None
        self.shrink_factors = None
        self.smooth_sigma = None
        self.sampling_rate = None
        self.final_interp = None
        self.number_of_iterations = None
        self.default_number = None

        self.dict = {}

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

    def set_value(self, key, value):
        self.dict[key] = value

    def create_view(self):
        """
        Create a table to hold all the ROI creation by isodose entries.
        """
        self.auto_image_fusion_frame.setVisible(False)

    def setVisible(self, visibility):
        self.auto_image_fusion_frame.setVisible(visibility)

    def setupUi(self):

        # Create a vertical Widget to hold Vertical Layout
        self.vertical_layout_widget = QWidget()
        self.vertical_layout = QtWidgets.QVBoxLayout()

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

        # Default Numbers
        self.default_numbers_label = QLabel("Default Numbers")
        self.default_numbers_label.setAlignment(
            Qt.AlignLeft | Qt.AlignTrailing | Qt.AlignVCenter)
        self.gridLayout.addWidget(self.default_numbers_label, 1, 0)

        self.default_number_spinBox = QSpinBox(self.gridLayoutWidget)
        self.default_number_spinBox.setRange(-2147483648, 2147483647)
        # self.default_number_spinBox.setValue(-1000)
        self.default_number_spinBox.setSizePolicy(QSizePolicy.Minimum,
                                                  QSizePolicy.Fixed)
        self.default_number_spinBox.setToolTip(
            "Default voxel value. Defaults to -1000.")
        self.gridLayout.addWidget(self.default_number_spinBox, 1, 1)

        # Final Interp
        self.interp_order_label = QLabel("Final Interp")
        self.interp_order_label.setAlignment(
            Qt.AlignLeft | Qt.AlignTrailing | Qt.AlignVCenter)
        self.gridLayout.addWidget(self.interp_order_label, 2, 0)

        self.interp_order_spinbox = QSpinBox(self.gridLayoutWidget)
        # self.interp_order_spinbox.setValue(2)
        self.interp_order_spinbox.setSizePolicy(QSizePolicy.Minimum,
                                                QSizePolicy.Fixed)
        self.interp_order_spinbox.setToolTip("The final interpolation order. "
                                             "Defaults to 2 (linear).")
        self.gridLayout.addWidget(self.interp_order_spinbox, 2, 1)

        # Metric
        self.metric_label = QLabel("Metric")
        self.metric_label.setAlignment(
            QtCore.Qt.AlignLeft | Qt.AlignTrailing | Qt.AlignVCenter)
        self.gridLayout.addWidget(self.metric_label, 3, 0)

        self.metric_comboBox = QComboBox()
        self.metric_comboBox.addItem("correlation")
        self.metric_comboBox.addItem("mean_squares")
        self.metric_comboBox.addItem("mattes_mi")
        self.metric_comboBox.addItem("joint_hist_mi")
        # self.metric_comboBox.setCurrentIndex(1)
        self.metric_comboBox.setToolTip("The metric to be optimised during "
                                        "image registration.")
        self.gridLayout.addWidget(self.metric_comboBox, 3, 1)

        # Number of Iterations
        self.no_of_iterations_label = QLabel("Number of Iterations")
        self.no_of_iterations_label.setAlignment(
            Qt.AlignLeft | Qt.AlignTrailing | Qt.AlignVCenter)
        self.gridLayout.addWidget(self.no_of_iterations_label, 4, 0)

        self.no_of_iterations_spinBox = QSpinBox(self.gridLayoutWidget)
        self.no_of_iterations_spinBox.setSizePolicy(QSizePolicy.Minimum,
                                                    QSizePolicy.Fixed)
        self.no_of_iterations_spinBox.setRange(0, 100)
        # self.no_of_iterations_spinBox.setValue(50)
        self.no_of_iterations_spinBox.setToolTip("Number of iterations in "
                                                 "each multi-resolution step.")
        self.gridLayout.addWidget(self.no_of_iterations_spinBox, 4, 1)

        # Shrink Factor
        self.shrink_factor_label = QLabel("Shrink Factor")
        self.shrink_factor_label.setAlignment(
            Qt.AlignLeft | Qt.AlignTrailing | Qt.AlignVCenter)
        self.gridLayout.addWidget(self.shrink_factor_label, 5, 0)

        self.shrink_factor_qLineEdit = QLineEdit()
        self.shrink_factor_qLineEdit.setSizePolicy(QSizePolicy.Minimum,
                                                   QSizePolicy.Fixed)
        # self.shrink_factor_qLineEdit.setText("[8]")
        self.shrink_factor_qLineEdit.setToolTip("The multi-resolution "
                                                "downsampling factors. Can be "
                                                "up to three parameters in an "
                                                "array. Example [8, 2, 1]")
        self.gridLayout.addWidget(self.shrink_factor_qLineEdit, 5, 1)

        # Optimiser
        self.optimiser_label = QLabel("Optimiser")
        self.optimiser_label.setAlignment(
            Qt.AlignLeft | Qt.AlignTrailing | Qt.AlignVCenter)
        self.gridLayout.addWidget(self.optimiser_label, 1, 2)

        self.optimiser_comboBox = QComboBox(self.gridLayoutWidget)
        self.optimiser_comboBox.addItem("lbfgsb")
        self.optimiser_comboBox.addItem("gradient_descent")
        self.optimiser_comboBox.addItem("gradient_descent_line_search")
        self.optimiser_comboBox.setToolTip("The optimiser algorithm used for "
                                           "image registration.")
        self.gridLayout.addWidget(self.optimiser_comboBox, 1, 3)

        # Reg Method
        self.reg_method_label = QLabel("Reg Method")
        self.reg_method_label.setAlignment(
            QtCore.Qt.AlignLeft | Qt.AlignTrailing | Qt.AlignVCenter)
        self.gridLayout.addWidget(self.reg_method_label, 2, 2)

        self.reg_method_comboBox = QComboBox()
        self.reg_method_comboBox.addItem("translation")
        self.reg_method_comboBox.addItem("rigid")
        self.reg_method_comboBox.addItem("similarity")
        self.reg_method_comboBox.addItem("affine")
        self.reg_method_comboBox.addItem("scaleversor")
        self.reg_method_comboBox.addItem("scaleskewversor")
        # self.reg_method_comboBox.setCurrentIndex(2)
        self.reg_method_comboBox.setToolTip("The linear transformation model "
                                            "to be used for image "
                                            "registration.")
        self.gridLayout.addWidget(self.reg_method_comboBox, 2, 3)

        # Sampling Rate
        self.sampling_rate_label = QLabel("Sampling Rate")
        self.sampling_rate_label.setAlignment(
            Qt.AlignLeft | Qt.AlignTrailing | Qt.AlignVCenter)
        self.gridLayout.addWidget(self.sampling_rate_label, 3, 2)

        self.sampling_rate_spinBox = QDoubleSpinBox(self.gridLayoutWidget)
        self.sampling_rate_spinBox.setMinimum(0)
        self.sampling_rate_spinBox.setMaximum(1)
        self.sampling_rate_spinBox.setSingleStep(0.01)
        # self.sampling_rate_spinBox.setValue(0.25)
        self.sampling_rate_spinBox.setSizePolicy(QSizePolicy.Minimum,
                                                 QSizePolicy.Fixed)
        self.sampling_rate_spinBox.setToolTip(
            "The fraction of voxels sampled "
            "during each iteration.")
        self.gridLayout.addWidget(self.sampling_rate_spinBox, 3, 3)

        # Smooth Sigmas
        self.smooth_sigma_label = QLabel("Smooth Sigma")
        self.smooth_sigma_label.setAlignment(
            Qt.AlignLeft | Qt.AlignTrailing | Qt.AlignVCenter)
        self.gridLayout.addWidget(self.smooth_sigma_label, 4, 2)

        self.smooth_sigmas_qLineEdit = QLineEdit()
        self.smooth_sigmas_qLineEdit.setSizePolicy(QSizePolicy.Minimum,
                                                   QSizePolicy.Fixed)
        # self.smooth_sigmas_qLineEdit.setText("[10]")
        self.smooth_sigmas_qLineEdit.setToolTip(
            "The multi-resolution smoothing "
            "kernal scale (Gaussian). Can "
            "allow up to 3 integers in an "
            "array. Example [4, 2, 0].")
        self.gridLayout.addWidget(self.smooth_sigmas_qLineEdit, 4, 3)

        # Label to hold warning labels.
        self.warning_label = QLabel()

        self.vertical_layout.addWidget(self.gridLayoutWidget)
        self.vertical_layout.addWidget(self.warning_label)
        # Set layout of frame to the gridlayout widget
        self.auto_image_fusion_frame.setLayout(self.vertical_layout)

    def set_gridLayout(self):

        # If-Elif statements for setting the dict
        # this can only be done in if-else statements.
        if self.dict["reg_method"] == "translation":
            self.reg_method_comboBox.setCurrentIndex(0)
        elif self.dict["reg_method"] == "rigid":
            self.reg_method_comboBox.setCurrentIndex(1)
        elif self.dict["reg_method"] == "similarity":
            self.reg_method_comboBox.setCurrentIndex(2)
        elif self.dict["reg_method"] == "affine":
            self.reg_method_comboBox.setCurrentIndex(3)
        elif self.dict["reg_method"] == "scaleversor":
            self.reg_method_comboBox.setCurrentIndex(4)
        elif self.dict["reg_method"] == "scaleskewversor":
            self.reg_method_comboBox.setCurrentIndex(5)

        if self.dict["metric"] == "coorelation":
            self.metric_comboBox.setCurrentIndex(0)
        elif self.dict["metric"] == "mean_squares":
            self.metric_comboBox.setCurrentIndex(1)
        elif self.dict["metric"] == "mattes_mi":
            self.metric_comboBox.setCurrentIndex(2)
        elif self.dict["metric"] == "joint_hist_mi":
            self.metric_comboBox.setCurrentIndex(3)

        if self.dict["optimiser"] == "lbfgsb":
            self.optimiser_comboBox.setCurrentIndex(0)
        elif self.dict["optimiser"] == "gradient_descent":
            self.optimiser_comboBox.setCurrentIndex(1)
        elif self.dict["optimiser"] == "gradient_descent_line_search":
            self.optimiser_comboBox.setCurrentIndex(2)

        # Shrink_factors is stored as a list in JSON convert the list into
        # a string.
        shrink_factor_list_json = ''.join(str(e) for e in self.dict[
            "shrink_factors"])
        print('Shrink Factor List')
        print(shrink_factor_list_json)
        self.shrink_factor_qLineEdit.setText(shrink_factor_list_json)

        # Since smooth_sigma is stored as a list in JSON convert the list
        # into a string.
        smooth_sigma_list_json = ''.join(str(e) for e in self.dict[
            "smooth_sigmas"])
        print('Smooth Sigma List')
        print(smooth_sigma_list_json)
        self.smooth_sigmas_qLineEdit.setText(smooth_sigma_list_json)

        msg = ""

        try:
            self.sampling_rate_spinBox.setValue(float(self.dict[
                                                          "sampling_rate"]))
        except ValueError:
            msg += 'There was an error setting the Sampling Rate value.\n'
            self.warning_label.setText(msg)

        try:
            self.interp_order_spinbox.setValue(int(self.dict["final_interp"]))
        except ValueError:
            msg += 'There was an error setting the Final Interp value.\n'
            self.warning_label.setText(msg)

        try:
            self.no_of_iterations_spinBox.setValue(int(self.dict[
                                                           "number_of_iterations"]))
        except ValueError:
            msg += 'There was an error setting the Number of iterations ' \
                   'value.\n'
            self.warning_label.setText(msg)

        try:
            self.default_number_spinBox.setValue(int(
                self.dict["default_value"]))
        except ValueError:
            msg += 'There was an error setting the Default Number'
            self.warning_label.setText(msg)

    def get_values_from_UI(self):

        # TO DO: Add in checks to ensure values are correct.

        self.dict["reg_method"] = self.reg_method_comboBox.currentIndex()
        self.dict["metric"] = self.metric_comboBox.currentIndex()
        self.dict["optimiser"] = self.optimiser_comboBox.currentIndex()
        self.dict[
            "shrink_factors"] = self.shrink_factor_qLineEdit.text().split()
        self.dict[
            "smooth_sigmas"] = self.smooth_sigmas_qLineEdit.text().split()
        self.dict["sampling_rate"] = self.sampling_rate_spinBox.value()
        self.dict["final_interp"] = self.interp_order_spinbox.value()
        self.dict[
            "number_of_iterations"] = self.no_of_iterations_spinBox.value()
        self.dict["default_value"] = self.default_number_spinBox.value()
        print(self.dict)
        return self.dict
