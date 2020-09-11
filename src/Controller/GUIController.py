from shutil import which
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import QMessageBox

from src.View.mainpage.MainPage import UIMainWindow
from src.View.PyradiProgressBar import PyradiExtended
from src.View.WelcomeWindow import UIWelcomeWindow
from src.View.OpenPatientWindow import UIOpenPatientWindow
from src.View.mainwindowrestructure.NewMainPage import UINewMainWindow


class WelcomeWindow(QtWidgets.QMainWindow, UIWelcomeWindow):

    go_next_window = QtCore.pyqtSignal()

    # Initialisation function to display the UI
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.setup_ui(self)
        self.open_patient_button.clicked.connect(self.go_open_patient_window)

    def go_open_patient_window(self):
        """
        Function to progress to the OpenPatientWindow
        """
        self.go_next_window.emit()


class OpenPatientWindow(QtWidgets.QMainWindow, UIOpenPatientWindow):

    go_next_window = QtCore.pyqtSignal(tuple)

    # Initialisation function to display the UI
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        self.setup_ui(self)
        self.patient_info_initialized.connect(self.open_patient)

    def open_patient(self, patient_attributes):
        self.go_next_window.emit(patient_attributes)


class MainWindow(QtWidgets.QMainWindow, UINewMainWindow):

    # When a new patient file is opened from the main window
    open_patient_window = QtCore.pyqtSignal()
    # When the pyradiomics button is pressed
    run_pyradiomics = QtCore.pyqtSignal(str, dict, str)

    # Initialising the main window and setting up the UI
    def __init__(self, patient_dict_container):
        QtWidgets.QMainWindow.__init__(self)
        self.setup_ui(self, patient_dict_container)
        self.button_open_patient.clicked.connect(self.open_new_patient)
        #self.menu_bar.actionOpen.triggered.connect(self.open_new_patient)
        #self.menu_bar.actionPyradiomics.triggered.connect(self.pyradiomics_handler)
        #self.pyradi_trigger.connect(self.pyradiomics_handler)

    def open_new_patient(self):
        """
        Function to handle the Open patient button being clicked
        """
        confirmation_dialog = QMessageBox.information(self, 'Open new patient?',
                                                      'Opening a new patient will close the currently opened patient. '
                                                      'Would you like to continue?',
                                                      QMessageBox.Yes | QMessageBox.No)

        if confirmation_dialog == QMessageBox.Yes:
            self.open_patient_window.emit()

    def pyradiomics_handler(self):
        """
        Sends signal to initiate pyradiomics analysis
        """
        if which('plastimatch') is not None:
            if self.hashed_path == '':
                confirm_pyradi = QMessageBox.information(self, "Confirmation",
                                                    "Are you sure you want to perform pyradiomics? "
                                                    "Once started the process cannot be terminated until it finishes.",
                                                    QMessageBox.Yes, QMessageBox.No)
                if confirm_pyradi == QMessageBox.Yes:
                    self.run_pyradiomics.emit(self.path, self.filepaths, self.hashed_path)
                if confirm_pyradi == QMessageBox.No:
                    pass
            else:
                self.run_pyradiomics.emit(self.path, self.filepaths, self.hashed_path)
        else:
            exe_not_found = QMessageBox.information(self, "Error",
                                                 "Plastimatch not installed. Please install Plastimatch "
                                                 "(https://sourceforge.net/projects/plastimatch/) to carry out "
                                                 "pyradiomics analysis.")

    def cleanup(self):
        del self.dataset

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        if self.rtss_modified and hasattr(self, "structures_tab"):
            confirmation_dialog = QMessageBox.information(self, 'Close without saving?',
                                                          'The RTSTRUCT file has been modified. Would you like to save '
                                                          'before exiting the program?',
                                                          QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)

            if confirmation_dialog == QMessageBox.Save:
                self.structures_tab.save_new_rtss()
                event.accept()
                self.cleanup()
            elif confirmation_dialog == QMessageBox.Discard:
                event.accept()
                self.cleanup()
            else:
                event.ignore()
        else:
            self.cleanup()


class PyradiProgressBar(QtWidgets.QWidget):
    progress_complete = QtCore.pyqtSignal()

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
        qtRectangle = self.w.frameGeometry()
        centerPoint = QtWidgets.QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.w.move(qtRectangle.topLeft())
        self.setWindowIcon(QtGui.QIcon("src/Icon/DONE.png"))

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
        # The segmentation masks are generated between the range 25 and 50
        elif value == 25:
            self.label.setText("Generating segmentation masks")
        # Above 50, pyradiomics analysis is carried out over each segmentation mask
        elif value in range(50, 100):
            self.label.setText("Calculating features for " + text)
        # Set the percentage value
        self.progress_bar.setValue(value)

        # When the percentage reaches 100, send a signal to close progress bar
        if value == 100:
            completion = QMessageBox.information(
                self, "Complete", "Task has been completed successfully"
            )
            self.progress_complete.emit()
