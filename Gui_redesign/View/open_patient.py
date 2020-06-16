from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_OpenPatientWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(942, 600)
        MainWindow.setWindowTitle("OnkoDICOM")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("../Gui_redesign/src/images/icon.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MainWindow.setWindowIcon(icon)

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")

        self.path_label = QtWidgets.QLabel(self.centralwidget)
        self.path_label.setObjectName("path_label")
        self.path_label.setText("<html><head/><body><p><span style=\" font-size:10pt;\">Path:</span></p></body></html>")
        self.gridLayout.addWidget(self.path_label, 1, 0, 1, 1)

        self.cancelButton = QtWidgets.QPushButton(self.centralwidget)
        self.cancelButton.setObjectName("cancelButton")
        self.cancelButton.setText("Cancel")
        self.cancelButton.clicked.connect(self.cancelButtonClicked) # Signal Closing Application

        self.gridLayout.addWidget(self.cancelButton, 9, 3, 1, 1)
        self.chooseButton = QtWidgets.QPushButton(self.centralwidget)
        self.chooseButton.setObjectName("chooseButton")
        self.chooseButton.setText("Choose")
        self.chooseButton.clicked.connect(self.chooseButtonClicked)

        self.gridLayout.addWidget(self.chooseButton, 1, 2, 1, 1)
        self.pathTextBrowser = QtWidgets.QTextBrowser(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Ignored)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pathTextBrowser.sizePolicy().hasHeightForWidth())
        self.pathTextBrowser.setSizePolicy(sizePolicy)
        self.pathTextBrowser.setObjectName("pathTextBrowser")
        self.gridLayout.addWidget(self.pathTextBrowser, 1, 1, 1, 1)
        self.choose_label = QtWidgets.QLabel(self.centralwidget)
        self.choose_label.setObjectName("choose_label")
        self.choose_label.setText("<html><head/><body><p><span style=\" font-size:10pt;\">Choose the file path of a folder containing DICOM files to create the Patient file directory:</span></p></body></html>")
        self.gridLayout.addWidget(self.choose_label, 0, 1, 1, 3)

        self.patient_file_label = QtWidgets.QLabel(self.centralwidget)
        self.patient_file_label.setObjectName("patient_file_label")
        self.patient_file_label.setText("<html><head/><body><p><span style=\" font-size:10pt;\">Patient File directory shown below once file path chosen. Please select the file(s) you want to open:</span></p></body></html>")
        self.gridLayout.addWidget(self.patient_file_label, 6, 1, 1, 3)

        self.confirmButton = QtWidgets.QPushButton(self.centralwidget)
        self.confirmButton.setObjectName("confirmButton")
        self.confirmButton.setText("Confirm")
        self.gridLayout.addWidget(self.confirmButton, 9, 4, 1, 1)

        self.selected_directory_label = QtWidgets.QLabel(self.centralwidget)
        self.selected_directory_label.setObjectName("selected_directory_label")
        self.selected_directory_label.setText("<html><head/><body><p><span style=\" font-size:10pt;\">The selected directory(s) above will be opened in the OnkoDICOM program.</span></p></body></html>")
        self.gridLayout.addWidget(self.selected_directory_label, 9, 1, 1, 2)

        self.treeWidget = QtWidgets.QTreeWidget(self.centralwidget)
        self.treeWidget.setObjectName("treeWidget")
        self.gridLayout.addWidget(self.treeWidget, 7, 1, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def cancelButtonClicked(self):
        sys.exit(app.exec_())

    def chooseButtonClicked(self):
        self.filepath = QtWidgets.QFileDialog.getExistingDirectory(None, 'Select patient folder...', '')
        self.pathTextBrowser.setText(self.filepath) # added functionality


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_OpenPatientWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
