# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'open_page.ui'
#
# Created by: PyQt5 UI code generator 5.13.0
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets, Qt


class WelcomePage(object):

    def setupUi(self, WelcomePage):
        WelcomePage.setObjectName("WelcomePage")
        WelcomePage.setWindowIcon(QtGui.QIcon("src/Icon/logo.png"))
        WelcomePage.setFixedSize(844, 528)
        WelcomePage.setStyleSheet("background-color: rgb(244, 245, 245);")
        self.centralwidget = QtWidgets.QWidget(WelcomePage)
        self.centralwidget.setObjectName("centralwidget")
        self.welcomeLabel = QtWidgets.QLabel(self.centralwidget)
        self.welcomeLabel.setGeometry(QtCore.QRect(270, 310, 351, 41))
        self.welcomeLabel.setStyleSheet("font: 57 18pt \"Ubuntu\";\n"
        "font: 57 18pt \"Ubuntu\";")
        self.welcomeLabel.setObjectName("welcomeLabel")
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(80, 360, 671, 21))
        self.label_2.setStyleSheet("font: 57 12pt \"Ubuntu\";")
        self.label_2.setObjectName("label_2")
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setGeometry(QtCore.QRect(350, 410, 121, 31))
        self.pushButton.setStyleSheet("background-color: rgb(238, 238, 236);\n"
                                       "font: 57 12pt \"Ubuntu\";\n"
                                       "color:rgb(75,0,130);\n"
                                       "font-weight: bold;\n")
        self.pushButton.setObjectName("pushButton")
        self.pushButton.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.logo = QtWidgets.QLabel(self.centralwidget)
        self.logo.setGeometry(QtCore.QRect(185, 30, 480, 261))
        self.logo.setText("")
        self.logo.setPixmap(QtGui.QPixmap("src/Icon/logo.png"))
        self.logo.setScaledContents(True)
        self.logo.setObjectName("logo")


        WelcomePage.setCentralWidget(self.centralwidget)
       # self.centralwidget.resizeEvent()

        self.retranslateUi(WelcomePage)
        QtCore.QMetaObject.connectSlotsByName(WelcomePage)

    def retranslateUi(self, WelcomePage):
        _translate = QtCore.QCoreApplication.translate
        WelcomePage.setWindowTitle(_translate("WelcomePage", "OnkoDICOM"))
        self.welcomeLabel.setText(_translate("WelcomePage", "Welcome to OnkoDICOM!"))
        self.label_2.setText(_translate("WelcomePage", "OnkoDICOM - the solution for producing data for analysis from your oncology plans and scans."))
        self.pushButton.setText(_translate("WelcomePage", "Open Patient"))

