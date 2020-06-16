from PyQt5 import QtCore, QtGui, QtWidgets
from Gui_redesign.View.open_patient import *

class UIWelcomeWindow(object):

    def setup_ui(self, welcome_window):
        welcome_window.setObjectName("MainWindow")
        welcome_window.setWindowTitle("OnkoDICOM")
        welcome_window.setWindowModality(QtCore.Qt.NonModal)
        welcome_window.setEnabled(True)
        welcome_window.setFixedSize(939, 594)
        welcome_window.setFocusPolicy(QtCore.Qt.ClickFocus)
        welcome_window.setAcceptDrops(False)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("../Gui_redesign/src/images/icon.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        welcome_window.setWindowIcon(icon)
        welcome_window.setAutoFillBackground(False)

        self.central_widget = QtWidgets.QWidget(welcome_window)
        self.central_widget.setObjectName("centralwidget")
        self.grid_layout2 = QtWidgets.QGridLayout(self.central_widget)
        self.grid_layout2.setObjectName("gridLayout_2")

        # Logo
        self.logo = QtWidgets.QLabel(self.central_widget)
        self.logo.setEnabled(True)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Fixed)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.logo.sizePolicy().hasHeightForWidth())
        self.logo.setSizePolicy(size_policy)
        self.logo.setPixmap(QtGui.QPixmap("OnkoDicom/logo.ico"))
        self.logo.setScaledContents(True)
        self.logo.setObjectName("logo")

        # Frame Layout
        self.grid_layout2.addWidget(self.logo, 4, 0, 1, 1)
        self.frame = QtWidgets.QFrame(self.central_widget)
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame.setObjectName("frame")
        self.grid_layout = QtWidgets.QGridLayout(self.frame)
        self.grid_layout.setObjectName("gridLayout")
        self.open_button = QtWidgets.QPushButton(self.frame)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(self.open_button.sizePolicy().hasHeightForWidth())

        # Button
        self.open_button.setSizePolicy(size_policy)
        self.open_button.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.open_button.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.open_button.setAutoDefault(True)
        self.open_button.setDefault(False)
        self.open_button.setFlat(False)
        self.open_button.setObjectName("continueButton")
        self.open_button.setText("Open Patient")
        self.open_button.setStyleSheet("background-color: #9370DB;" "border-width: 8px;" "border-radius: 20px;" "padding: 6px;" "color:white;") # Self added
        self.grid_layout.addWidget(self.open_button, 2, 0, 1, 1, QtCore.Qt.AlignHCenter) # Keeps button in middle

        self.open_button.clicked.connect(self.button_clicked) # signal opening of Patient

        self.frame2 = QtWidgets.QFrame(self.frame)
        self.frame2.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame2.setFrameShadow(QtWidgets.QFrame.Raised)
        self.frame2.setObjectName("frame2")

        self.label = QtWidgets.QLabel(self.frame2)
        self.label.setGeometry(QtCore.QRect(210, -50, 501, 361))
        self.label.setPixmap(QtGui.QPixmap("../Gui_redesign/src/images/image.png"))
        self.label.setScaledContents(True)
        self.label.setObjectName("label")

        self.welcome_text = QtWidgets.QLabel(self.frame2)
        self.welcome_text.setGeometry(QtCore.QRect(200, 350, 508, 106))
        self.welcome_text.setTextFormat(QtCore.Qt.AutoText)
        self.welcome_text.setText("<html><head/><body><p align=\"center\"><span style=\" font-size:26pt; "
                                  "font-weight:600;\">Welcome to OnkoDICOM!</span></p><p align=\"center\"><br/></p><p "
                                  "align=\"center\"><span style=\" font-size:9pt;\">OnkoDICOM - the solution for "
                                  "producing data for analysis from your oncology plans and "
                                  "scans</span></p></body></html>")
        self.welcome_text.setScaledContents(False)
        self.welcome_text.setObjectName("welcome")

        self.grid_layout.addWidget(self.frame2, 0, 0, 1, 1)
        self.grid_layout2.addWidget(self.frame, 5, 0, 1, 1)
        welcome_window.setCentralWidget(self.central_widget)

        self.status_bar = QtWidgets.QStatusBar(welcome_window)
        self.status_bar.setObjectName("statusbar")
        self.status_bar.setSizeGripEnabled(False) # Remove expanding window option
        welcome_window.setStatusBar(self.status_bar)

        QtCore.QMetaObject.connectSlotsByName(welcome_window)

    def button_clicked(self):
        print("Button has been pressed")


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = UIWelcomeWindow()
    ui.setup_ui(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
