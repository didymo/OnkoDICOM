from shutil import which

from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtWidgets import QMessageBox

from src.Controller.PathHandler import resource_path
from src.Model.InitialModel import create_initial_model
from src.Model.MovingDictContainer import MovingDictContainer
from src.Model.MovingModel import read_images_for_fusion
from src.Model.PatientDictContainer import PatientDictContainer
from src.View.BatchProcessingWindow import UIBatchProcessingWindow
from src.View.FirstTimeWelcomeWindow import UIFirstTimeWelcomeWindow
from src.View.ImageFusion.ImageFusionWindow import UIImageFusionWindow
from src.View.OpenPatientWindow import UIOpenPatientWindow
from src.View.PyradiProgressBar import PyradiExtended
from src.View.WelcomeWindow import UIWelcomeWindow
from src.View.mainpage.MainPage import UIMainWindow

from src.View.PTCTFusion.OpenPTCTPatientWindow import UIOpenPTCTPatientWindow
from src.Model.PTCTDictContainer import PTCTDictContainer


class FirstTimeWelcomeWindow(QtWidgets.QMainWindow, UIFirstTimeWelcomeWindow):
    update_directory = QtCore.Signal(str)
    go_next_window = QtCore.Signal()

    # Initialisation function to display the UI
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.setup_ui(self)
        self.configured.connect(self.update_new_directory)
        self.skip_button.clicked.connect(self.go_open_patient_window)

    def update_new_directory(self, new_directory):
        """
            Function to update the default directory
        """
        self.update_directory.emit(new_directory)
        self.go_open_patient_window()

    def go_open_patient_window(self):
        """
            Function to progress to the OpenPatientWindow
        """
        self.go_next_window.emit()


class WelcomeWindow(QtWidgets.QMainWindow, UIWelcomeWindow):
    go_next_window = QtCore.Signal()
    go_batch_window = QtCore.Signal()

    # Initialisation function to display the UI
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.setup_ui(self)
        self.open_patient_button.clicked.connect(self.go_open_patient_window)
        self.open_batch_button.clicked.connect(self.open_batch_window)

    def go_open_patient_window(self):
        """
        Function to progress to the OpenPatientWindow
        """
        self.go_next_window.emit()

    def open_batch_window(self):
        """
        Function to progress to the BatchProcessingWindow
        """
        self.go_batch_window.emit()


class OpenPatientWindow(QtWidgets.QMainWindow, UIOpenPatientWindow):
    go_next_window = QtCore.Signal(object)

    # Initialisation function to display the UI
    def __init__(self, default_directory):
        QtWidgets.QMainWindow.__init__(self)
        self.setup_ui(self)
        self.patient_info_initialized.connect(self.open_patient)

        if default_directory is not None:
            self.filepath = default_directory
            self.open_patient_directory_input_box.setText(default_directory)
            self.scan_directory_for_patient()

    def open_patient(self, progress_window):
        self.go_next_window.emit(progress_window)


class ImageFusionWindow(QtWidgets.QMainWindow, UIImageFusionWindow):
    go_next_window = QtCore.Signal(object)

    def __init__(self, directory_in):
        QtWidgets.QMainWindow.__init__(self)
        self.setup_ui(self)
        self.image_fusion_info_initialized.connect(self.open_patient)
        self.update_patient()
        if directory_in is not None:
            self.filepath = directory_in
            self.open_patient_directory_input_box.setText(directory_in)
            self.scan_directory_for_patient()

    def update_ui(self):
        # Instantiate a local new PatientDictContainer
        patient_dict_container = PatientDictContainer()
        patient = patient_dict_container.get("basic_info")

        # Compare local patient with previous instance of ImageFusion
        if self.patient_id != patient['id']:
            self.update_patient()

    def open_patient(self, progress_window):
        self.go_next_window.emit(progress_window)


class OpenPTCTPatientWindow(QtWidgets.QMainWindow, UIOpenPTCTPatientWindow):
    go_next_window = QtCore.Signal(object)

    def __init__(self, directory_in):
        """
        Initialises the OpenPTCTPatientWindow with default directory
        information
        :param directory_in: the default directory of OnkoDICOM
        """
        QtWidgets.QMainWindow.__init__(self)
        self.setup_ui(self)
        self.patient_info_initialized.connect(self.open_patient)
        if directory_in is not None:
            self.filepath = directory_in
            self.open_patient_directory_input_box.setText(directory_in)
            self.scan_directory_for_patient()

    def open_patient(self, progress_window):
        """
        Activates the OpenPTCTPatientWindow for use
        :param progress_window: The OnkoDICOM progress window
        """
        self.go_next_window.emit(progress_window)


class MainWindow(QtWidgets.QMainWindow, UIMainWindow):
    # When a new patient file is opened from the main window
    open_patient_window = QtCore.Signal()
    # When the pyradiomics button is pressed
    run_pyradiomics = QtCore.Signal(str, dict, str)
    # When the image fusion button is pressed
    image_fusion_signal = QtCore.Signal()
    # When pt/ct button is pressed
    pt_ct_signal = QtCore.Signal()

    # Initialising the main window and setting up the UI
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        create_initial_model()
        self.setup_ui(self)
        self.action_handler.action_open.triggered.connect(
            self.open_new_patient)
        self.action_handler.action_image_fusion.triggered.connect(
            self.open_image_fusion)
        self.pyradi_trigger.connect(self.pyradiomics_handler)
        self.pet_ct_tab.load_pt_ct_signal.connect(self.initialise_pt_ct)

    def update_ui(self):
        create_initial_model()
        self.setup_central_widget()
        self.setup_actions()

        self.action_handler.action_open.triggered.connect(
            self.open_new_patient)

        self.action_handler.action_image_fusion.triggered.connect(
            self.open_image_fusion)

        self.pet_ct_tab.load_pt_ct_signal.connect(self.initialise_pt_ct)

    def initialise_pt_ct(self):
        self.pt_ct_signal.emit()

    def load_pt_ct_tab(self):
        pcd = PTCTDictContainer()
        if not pcd.is_empty():
            self.pet_ct_tab.load_pet_ct()
            self.right_panel.setCurrentWidget(self.pet_ct_tab)

    def open_new_patient(self):
        """
        Function to handle the Open patient button being clicked
        """
        confirmation_dialog = QMessageBox.information(
            self, 'Open new patient?',
            'Opening a new patient will close the currently opened patient. '
            'Would you like to continue?',
            QMessageBox.Yes | QMessageBox.No)

        if confirmation_dialog == QMessageBox.Yes:
            self.open_patient_window.emit()

    def open_image_fusion(self):
        self.image_fusion_signal.emit()

    def update_image_fusion_ui(self):
        mvd = MovingDictContainer()
        if not mvd.is_empty():
            read_images_for_fusion()
            self.create_image_fusion_tab()

    def pyradiomics_handler(self, path, filepaths, hashed_path):
        """
        Sends signal to initiate pyradiomics analysis
        """
        if which('plastimatch') is not None:
            if hashed_path == '':
                confirm_pyradi = QMessageBox.information(
                    self, "Confirmation",
                    "Are you sure you want to perform pyradiomics? Once "
                    "started the process cannot be terminated until it "
                    "finishes.",
                    QMessageBox.Yes,
                    QMessageBox.No)
                if confirm_pyradi == QMessageBox.Yes:
                    self.run_pyradiomics.emit(path, filepaths, hashed_path)
                if confirm_pyradi == QMessageBox.No:
                    pass
            else:
                self.run_pyradiomics.emit(path, filepaths, hashed_path)
        else:
            exe_not_found = QMessageBox.information(
                self, "Error",
                "Plastimatch not installed. Please install Plastimatch "
                "(https://sourceforge.net/projects/plastimatch/) to carry out "
                "pyradiomics analysis. If using Windows, please ensure that "
                "your system's PATH variable inlcudes the directory where "
                "Plastimatch's executable is installed.")

    def cleanup(self):
        patient_dict_container = PatientDictContainer()
        patient_dict_container.clear()
        # Close 3d vtk widget
        self.three_dimension_view.close()
        self.cleanup_image_fusion()
        self.cleanup_pt_ct_viewer()

    def cleanup_image_fusion(self):
        # Explicity destroy objects - the purpose of this is to clear
        # any image fusion tabs that have been used previously.
        # Try-catch in the event user has not prompted image-fusion.
        try:
            del self.image_fusion_view_coronal
            del self.image_fusion_view_sagittal
            del self.image_fusion_view_axial
            del self.image_fusion_four_views_layout
            del self.image_fusion_four_views
            del self.image_fusion_single_view
            del self.image_fusion_view
        except:
            pass

        moving_dict_container = MovingDictContainer()
        moving_dict_container.clear()

    def cleanup_pt_ct_viewer(self):

        pt_ct_dict_container = PTCTDictContainer()
        pt_ct_dict_container.clear()
        self.pet_ct_tab.initialised = False
        try:
            del self.pet_ct_tab
        except:
            pass

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        patient_dict_container = PatientDictContainer()
        if patient_dict_container.get("rtss_modified") \
                and hasattr(self, "structures_tab"):
            confirmation_dialog = QMessageBox.information(
                self,
                'Close without saving?',
                'The RTSTRUCT file has been modified. Would you like to save '
                'before exiting the program?',
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)

            if confirmation_dialog == QMessageBox.Save:
                self.structures_tab.save_new_rtss_to_fixed_image_set()
                event.accept()
                self.cleanup()
            elif confirmation_dialog == QMessageBox.Discard:
                event.accept()
                self.cleanup()
            else:
                event.ignore()
        else:
            self.cleanup()


class BatchWindow(QtWidgets.QWidget, UIBatchProcessingWindow):
    go_next_window = QtCore.Signal()

    # Initialize the batch window and set up the UI
    def __init__(self):
        QtWidgets.QWidget.__init__(self)
        self.setup_ui(self)


class PyradiProgressBar(QtWidgets.QWidget):
    progress_complete = QtCore.Signal()

    def __init__(self, path, filepaths, target_path):
        super().__init__()

        self.w = QtWidgets.QWidget()
        self.setWindowTitle("Running Pyradiomics")
        self.setWindowFlags(
            QtCore.Qt.Window
            | QtCore.Qt.CustomizeWindowHint
            | QtCore.Qt.WindowTitleHint
            | QtCore.Qt.WindowMinimizeButtonHint
        )
        qt_rectangle = self.w.frameGeometry()
        center_point = QtGui.QScreen.availableGeometry(
            QtWidgets.QApplication.primaryScreen()).center()
        qt_rectangle.moveCenter(center_point)
        self.w.move(qt_rectangle.topLeft())
        self.setWindowIcon(QtGui.QIcon(
            resource_path("res/images/btn-icons/onkodicom_icon.png")))

        self.setGeometry(300, 300, 460, 100)
        self.label = QtWidgets.QLabel(self)
        self.label.setGeometry(30, 15, 400, 20)
        self.progress_bar = QtWidgets.QProgressBar(self)
        self.progress_bar.setGeometry(30, 40, 400, 25)
        self.progress_bar.setMaximum(100)
        self.ext = PyradiExtended(path, filepaths, target_path)
        self.ext.copied_percent_signal.connect(self.on_update)
        self.ext.start()

    def on_update(self, value, text=""):
        """
        Update percentage and text of progress bar.
        :param value:   Percentage value to be displayed
        :param text:    To display what ROI currently being processed
        """

        # When generating the nrrd file, the percentage starts at 0
        # and reaches 25
        if value == 0:
            self.label.setText("Generating nrrd file")
        # The segmentation masks are generated between the range 25 and
        # 50
        elif value == 25:
            self.label.setText("Generating segmentation masks")
        # Above 50, pyradiomics analysis is carried out over each
        # segmentation mask
        elif value in range(50, 100):
            self.label.setText("Calculating features for " + text)
        # Set the percentage value
        self.progress_bar.setValue(value)

        # When the percentage reaches 100, send a signal to close
        # progress bar
        if value == 100:
            completion = QMessageBox.information(
                self, "Complete", "Task has been completed successfully"
            )
            self.progress_complete.emit()
