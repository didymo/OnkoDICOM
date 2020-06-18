from PyQt5 import QtCore, QtGui, QtWidgets
from Gui_redesign.View.open_patient import *


class UIWelcomeWindow(object):

    # the ui constructor function
    def setup_ui(self, welcome_page):
        welcome_page.setObjectName("WelcomePage")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("../Gui_redesign/src/images/icon.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off) # adding icon
        welcome_page.setWindowIcon(icon)
        welcome_page.setFixedSize(844, 528)
        welcome_page.setStyleSheet("background-color: rgb(244, 245, 245);")
        self.centralwidget = QtWidgets.QWidget(welcome_page)
        self.centralwidget.setObjectName("centralwidget")
        self.welcome_label = QtWidgets.QLabel(self.centralwidget)
        self.welcome_label.setGeometry(QtCore.QRect(270, 340, 351, 41))
        self.welcome_label.setStyleSheet("font: 57 18pt;\n"
                                        "font: 57 18pt;")
        self.welcome_label.setObjectName("welcomeLabel")
        # the sentence below welcome
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(150, 390, 671, 21)) # previously had 80 in place of 150.
        self.label_2.setObjectName("label_2")
        # button to open a patient
        self.push_button = QtWidgets.QPushButton(self.centralwidget)
        self.push_button.setGeometry(QtCore.QRect(350, 440, 121, 31))
        self.push_button.setStyleSheet("background-color: #9370DB;" "border-width: 8px;" "border-radius: 20px;" "padding: 6px;" "color:white;" "font-weight: bold;")
        """
        If the original button is desired, the code is below.;
        
        self.pushButton.setStyleSheet("background-color: rgb(238, 238, 236);\n"
                                      "color:rgb(75,0,130);\n"
                                      "font-weight: bold;\n")
        """
        self.push_button.setObjectName("pushButton")
        self.push_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        # logo holder
        self.logo = QtWidgets.QLabel(self.centralwidget)
        self.logo.setGeometry(QtCore.QRect(185, 60, 480, 261))
        self.logo.setText("")
        self.logo.setPixmap(QtGui.QPixmap("View/image.png"))
        self.logo.setScaledContents(True)
        self.logo.setObjectName("logo")
        welcome_page.setCentralWidget(self.centralwidget)
        self.retranslate_ui(welcome_page)
        QtCore.QMetaObject.connectSlotsByName(welcome_page)

    # this function inserts all the text in the welcome page
    def retranslate_ui(self, WelcomePage):
        _translate = QtCore.QCoreApplication.translate
        WelcomePage.setWindowTitle(_translate("WelcomePage", "OnkoDICOM"))
        self.welcome_label.setText(_translate("WelcomePage", "Welcome to OnkoDICOM!"))
        self.label_2.setText(_translate("WelcomePage",
                                        "OnkoDICOM - the solution for producing data for analysis from your oncology plans and scans."))
        self.push_button.setText(_translate("WelcomePage", "Continue"))

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
