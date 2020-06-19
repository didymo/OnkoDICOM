from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QApplication

#from Gui_redesign.View.welcome_page import UIWelcomeWindow


class UIOpenPatientWindow(QMainWindow):

    def __init__(self):
        super(UIOpenPatientWindow, self).__init__()

        self.setWindowTitle("OnkoDICOM")
        self.setObjectName("MainWindow")
        self.resize(942, 600)
        self.setWindowTitle("OnkoDICOM")

        self.setup_ui()


    def setup_ui(self):
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("../Gui_redesign/res/images/icon.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(icon)
        self.setAutoFillBackground(False)

        self.central_widget = QtWidgets.QWidget(self)
        self.central_widget.setObjectName("centralwidget")
        self.grid_layout = QtWidgets.QGridLayout(self.central_widget)
        self.grid_layout.setObjectName("gridLayout")

        self.path_label = QtWidgets.QLabel(self.central_widget)
        self.path_label.setObjectName("path_label")
        self.path_label.setText("<html><head/><body><p><span style=\" font-size:10pt;\">Path:</span></p></body></html>")
        self.grid_layout.addWidget(self.path_label, 1, 0, 1, 1)

        self.cancel_button = QtWidgets.QPushButton(self.central_widget)
        self.cancel_button.setObjectName("cancelButton")
        self.cancel_button.setText("Cancel")
        self.cancel_button.clicked.connect(self.cancel_button_clicked)  # Signal Closing Application

        self.grid_layout.addWidget(self.cancel_button, 9, 3, 1, 1)
        self.choose_button = QtWidgets.QPushButton(self.central_widget)
        self.choose_button.setObjectName("chooseButton")
        self.choose_button.setText("Choose")
        self.choose_button.clicked.connect(self.choose_button_clicked)

        self.grid_layout.addWidget(self.choose_button, 1, 2, 1, 1)
        self.path_text_browser = QtWidgets.QTextBrowser(self.central_widget)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Ignored)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.path_text_browser.sizePolicy().hasHeightForWidth())
        self.path_text_browser.setSizePolicy(size_policy)
        self.path_text_browser.setObjectName("pathTextBrowser")
        self.grid_layout.addWidget(self.path_text_browser, 1, 1, 1, 1)
        self.choose_label = QtWidgets.QLabel(self.central_widget)
        self.choose_label.setObjectName("choose_label")
        self.choose_label.setText("<html><head/><body><p><span style=\" font-size:10pt;\">Choose the file path of a "
                                  "folder containing DICOM files to create the Patient file "
                                  "directory:</span></p></body></html>")
        self.grid_layout.addWidget(self.choose_label, 0, 1, 1, 3)

        self.patient_file_label = QtWidgets.QLabel(self.central_widget)
        self.patient_file_label.setObjectName("patient_file_label")
        self.patient_file_label.setText("<html><head/><body><p><span style=\" font-size:10pt;\">Patient File "
                                        "directory shown below once file path chosen. Please select the file(s) you "
                                        "want to open:</span></p></body></html>")
        self.grid_layout.addWidget(self.patient_file_label, 6, 1, 1, 3)

        self.confirm_Button = QtWidgets.QPushButton(self.central_widget)
        self.confirm_Button.setObjectName("confirmButton")
        self.confirm_Button.setText("Confirm")
        self.grid_layout.addWidget(self.confirm_Button, 9, 4, 1, 1)

        self.selected_directory_label = QtWidgets.QLabel(self.central_widget)
        self.selected_directory_label.setObjectName("selected_directory_label")
        self.selected_directory_label.setText("<html><head/><body><p><span style=\" font-size:10pt;\">The selected "
                                              "directory(s) above will be opened in the OnkoDICOM "
                                              "program.</span></p></body></html>")
        self.grid_layout.addWidget(self.selected_directory_label, 9, 1, 1, 2)

        self.tree_widget = QtWidgets.QTreeWidget(self.central_widget)
        self.tree_widget.setObjectName("treeWidget")
        self.grid_layout.addWidget(self.tree_widget, 7, 1, 1, 1)

        self.setCentralWidget(self.central_widget)
        self.status_bar = QtWidgets.QStatusBar(self)
        self.status_bar.setObjectName("statusbar")
        self.setStatusBar(self.status_bar)


    def cancel_button_clicked(self):
        sys.exit(app.exec_())

    def choose_button_clicked(self):
        self.filepath = QtWidgets.QFileDialog.getExistingDirectory(None, 'Select patient folder...', '')
        self.path_text_browser.setText(self.filepath) # added functionality


    def run_open_patient(self):
        patient_browser_ui = UIOpenPatientWindow()
        patient_browser_ui.show()

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    patient_browser_ui = UIOpenPatientWindow()
    patient_browser_ui.show()
    sys.exit(app.exec_())
