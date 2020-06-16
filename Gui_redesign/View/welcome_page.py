from PyQt5 import QtCore, QtGui, QtWidgets
from Gui_redesign.View.open_patient import *

class Ui_WelcomeWindow(object):
    def setupUi(self, WelcomeWindow):
        WelcomeWindow.setObjectName("MainWindow")
        WelcomeWindow.setWindowTitle("OnkoDICOM")
        WelcomeWindow.setWindowModality(QtCore.Qt.NonModal)
        WelcomeWindow.setEnabled(True)
        WelcomeWindow.setFixedSize(939, 594)
        WelcomeWindow.setFocusPolicy(QtCore.Qt.ClickFocus)
        WelcomeWindow.setAcceptDrops(False)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("../Gui_redesign/src/images/icon.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        WelcomeWindow.setWindowIcon(icon)
        WelcomeWindow.setAutoFillBackground(False)

        self.centralwidget = QtWidgets.QWidget(WelcomeWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout_2.setObjectName("gridLayout_2")

        # Logo
        self.logo = QtWidgets.QLabel(self.centralwidget)
        self.logo.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.logo.sizePolicy().hasHeightForWidth())
        self.logo.setSizePolicy(sizePolicy)
        self.logo.setText("")
        self.logo.setPixmap(QtGui.QPixmap("OnkoDicom/logo.ico"))
        self.logo.setScaledContents(True)
        self.logo.setObjectName("logo")

        # Frame Layout
        self.gridLayout_2.addWidget(self.logo, 4, 0, 1, 1)
        self.frame = QtWidgets.QFrame(self.centralwidget)
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.gridLayout = QtWidgets.QGridLayout(self.frame)
        self.gridLayout.setObjectName("gridLayout")
        self.openButton = QtWidgets.QPushButton(self.frame)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.openButton.sizePolicy().hasHeightForWidth())

        # Button
        self.openButton.setSizePolicy(sizePolicy)
        self.openButton.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.openButton.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.openButton.setAutoDefault(True)
        self.openButton.setDefault(False)
        self.openButton.setFlat(False)
        self.openButton.setObjectName("continueButton")
        self.openButton.setText("Open Patient")
        self.openButton.setStyleSheet("background-color: #9370DB;" "border-width: 8px;" "border-radius: 20px;" "padding: 6px;" "color:white;") # Self added
        self.gridLayout.addWidget(self.openButton, 2, 0, 1, 1, QtCore.Qt.AlignHCenter) # Keeps button in middle

        self.openButton.clicked.connect(self.buttonClicked) # signal opening of Patient

        self.frame_2 = QtWidgets.QFrame(self.frame)
        self.frame_2.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame_2.setObjectName("frame_2")

        self.label = QtWidgets.QLabel(self.frame_2)
        self.label.setGeometry(QtCore.QRect(210, -50, 501, 361))
        self.label.setText("")
        self.label.setPixmap(QtGui.QPixmap("../Gui_redesign/src/images/image.png"))
        self.label.setScaledContents(True)
        self.label.setObjectName("label")

        self.welcomeTxt = QtWidgets.QLabel(self.frame_2)
        self.welcomeTxt.setGeometry(QtCore.QRect(200, 350, 508, 106))
        self.welcomeTxt.setTextFormat(QtCore.Qt.AutoText)
        self.welcomeTxt.setText("<html><head/><body><p align=\"center\"><span style=\" font-size:26pt; font-weight:600;\">Welcome to OnkoDICOM!</span></p><p align=\"center\"><br/></p><p align=\"center\"><span style=\" font-size:9pt;\">OnkoDICOM - the solution for producing data for analysis from your oncology plans and scans</span></p></body></html>")
        self.welcomeTxt.setScaledContents(False)
        self.welcomeTxt.setObjectName("welcome")

        self.gridLayout.addWidget(self.frame_2, 0, 0, 1, 1)
        self.gridLayout_2.addWidget(self.frame, 5, 0, 1, 1)
        WelcomeWindow.setCentralWidget(self.centralwidget)

        self.statusbar = QtWidgets.QStatusBar(WelcomeWindow)
        self.statusbar.setObjectName("statusbar")
        self.statusbar.setSizeGripEnabled(False) # Remove expanding window option
        WelcomeWindow.setStatusBar(self.statusbar)

        QtCore.QMetaObject.connectSlotsByName(WelcomeWindow)

    def buttonClicked(self):
        print("Button has been pressed")


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_WelcomeWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
