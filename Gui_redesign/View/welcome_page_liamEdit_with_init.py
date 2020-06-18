from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMainWindow, QApplication

from Gui_redesign.View.open_patient import *

class UIWelcomeWindow(object):

    open_patient_window = QtCore.pyqtSignal()

    def __init__(self):
        super(UIWelcomeWindow, self).__init__()

        self.setObjectName("WelcomePage")
        self.setWindowTitle("OnkoDICOM")
        self.setWindowIcon(QtGui.QIcon("../../Gui_redesign/src/images/icon.ico"))
        self.setFixedSize(844, 528)
        self.setStyleSheet("background-color: rgb(244, 245, 245);")

        self.setup_ui()

    # the ui constructor function
    def setup_ui(self):

        self.centralwidget = QtWidgets.QWidget(self)
        self.centralwidget.setObjectName("centralwidget")
        self.welcomeLabel = QtWidgets.QLabel(self.centralwidget)
        self.welcomeLabel.setGeometry(QtCore.QRect(270, 340, 351, 41))
        self.welcomeLabel.setStyleSheet("font: 57 18pt;\n"
                                        "font: 57 18pt;")
        self.welcomeLabel.setObjectName("welcomeLabel")
        # the sentence below welcome
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(80, 390, 671, 21))
        self.label_2.setObjectName("label_2")
        # button to open a patient
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setGeometry(QtCore.QRect(350, 440, 121, 31))
        self.pushButton.setStyleSheet("background-color: rgb(238, 238, 236);\n"
                                      "color:rgb(75,0,130);\n"
                                      "font-weight: bold;\n")
        self.pushButton.setObjectName("pushButton")
        self.pushButton.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.pushButton.clicked.connect(self.button_clicked)

        # logo holder
        self.logo = QtWidgets.QLabel(self.centralwidget)
        self.logo.setGeometry(QtCore.QRect(185, 60, 480, 261))
        self.logo.setText("")
        self.logo.setPixmap(QtGui.QPixmap("View/image.png"))
        self.logo.setScaledContents(True)
        self.logo.setObjectName("logo")
        self.setCentralWidget(self.centralwidget)
        self.retranslateUi(self)
        QtCore.QMetaObject.connectSlotsByName(self)

    # this function inserts all the text in the welcome page
    def retranslateUi(self, WelcomePage):
        _translate = QtCore.QCoreApplication.translate
        WelcomePage.setWindowTitle(_translate("WelcomePage", "OnkoDICOM"))
        self.welcomeLabel.setText(_translate("WelcomePage", "Welcome to OnkoDICOM!"))
        self.label_2.setText(_translate("WelcomePage",
                                        "OnkoDICOM - the solution for producing data for analysis from your oncology plans and scans."))
        self.pushButton.setText(_translate("WelcomePage", "Continue"))


    def button_clicked(self):
        print("Button has been pressed")
        UIOpenPatientWindow.run_open_patient()


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    welcome_ui = UIWelcomeWindow()
    welcome_ui.show()
    sys.exit(app.exec_())
