from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_PluginManager(object):
    def setupUi(self, PluginManager):
        PluginManager.setObjectName("PluginManager")
        PluginManager.resize(766, 600)
        PluginManager.setStyleSheet("")
        self.centralwidget = QtWidgets.QWidget(PluginManager)
        self.centralwidget.setObjectName("centralwidget")
        self.optionTitle = QtWidgets.QLabel(self.centralwidget)
        self.optionTitle.setGeometry(QtCore.QRect(290, 50, 281, 31))
        self.optionTitle.setStyleSheet("font: 57 12pt \"Ubuntu\";\n"
                                       "font-weight: bold;")
        self.optionTitle.setObjectName("optionTitle")
        self.table_modules = QtWidgets.QTableWidget(self.centralwidget)
        self.table_modules.setGeometry(QtCore.QRect(290, 90, 451, 370))
        self.table_modules.setObjectName("table_modules")
        self.table_modules.setStyleSheet("background-color: rgb(255, 255, 255);")

        # buttons per view
        self.add_new_window = QtWidgets.QPushButton(self.centralwidget)
        self.add_new_window.setGeometry(QtCore.QRect(598, 470, 141, 31))
        self.add_new_window.setStyleSheet("background-color: rgb(238, 238, 236);\n"
                                          "font: 57 11pt \\\"Ubuntu\\\";\n"
                                          "color:rgb(75,0,130);\n"
                                          "font-weight: bold;")
        self.add_new_window.setObjectName("add_new_window")
        self.add_new_window.setVisible(False)
        self.table_view = QtWidgets.QTableWidget(self.centralwidget)
        self.table_view.setGeometry(QtCore.QRect(290, 90, 451, 370))
        self.table_view.setObjectName("table_view")
        self.table_view.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.table_view.setColumnCount(4)
        self.table_view.setHorizontalHeaderLabels([" Window Name ", " Scan ", " Window ", " Level "])
        self.table_view.horizontalHeaderItem(0).setTextAlignment(QtCore.Qt.AlignLeft)
        self.table_view.horizontalHeaderItem(1).setTextAlignment(QtCore.Qt.AlignLeft)
        self.table_view.horizontalHeaderItem(2).setTextAlignment(QtCore.Qt.AlignLeft)
        self.table_view.horizontalHeaderItem(3).setTextAlignment(QtCore.Qt.AlignLeft)
        self.table_view.verticalHeader().hide()
        header1 = self.table_view.horizontalHeader()
        header1.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header1.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        header1.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        header1.setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch)
        self.table_view.setVisible(False)
        # organ
        self.add_standard_organ_name = QtWidgets.QPushButton(self.centralwidget)
        self.add_standard_organ_name.setGeometry(QtCore.QRect(578, 470, 161, 31))
        self.add_standard_organ_name.setStyleSheet("background-color: rgb(238, 238, 236);\n"
                                                   "font: 57 11pt \\\"Ubuntu\\\";\n"
                                                   "color:rgb(75,0,130);\n"
                                                   "font-weight: bold;")
        self.add_standard_organ_name.setObjectName("add_standard_organ_name")
        self.table_organ = QtWidgets.QTableWidget(self.centralwidget)
        self.table_organ.setGeometry(QtCore.QRect(290, 90, 451, 370))
        self.table_organ.setObjectName("table_organ")
        self.table_organ.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.table_organ.setColumnCount(3)
        self.table_organ.setHorizontalHeaderLabels([" Standard Name ", " FMA ID ", " Organ "])
        self.table_organ.horizontalHeaderItem(0).setTextAlignment(QtCore.Qt.AlignLeft)
        self.table_organ.horizontalHeaderItem(1).setTextAlignment(QtCore.Qt.AlignLeft)
        self.table_organ.horizontalHeaderItem(2).setTextAlignment(QtCore.Qt.AlignLeft)
        header2 = self.table_organ.horizontalHeader()
        header2.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header2.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        header2.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        self.table_organ.setVisible(False)
        self.table_organ.verticalHeader().hide()
        self.add_standard_organ_name.setVisible(False)

        self.import_organ_csv = QtWidgets.QPushButton(self.centralwidget)
        self.import_organ_csv.setGeometry(QtCore.QRect(406, 470, 161, 31))
        self.import_organ_csv.setStyleSheet("background-color: rgb(238, 238, 236);\n"
                                            "font: 57 11pt \\\"Ubuntu\\\";\n"
                                            "color:rgb(75,0,130);\n"
                                            "font-weight: bold;")
        self.import_organ_csv.setObjectName("import_organ_csv")
        self.import_organ_csv.setVisible(False)

        # volume
        self.add_standard_volume_name = QtWidgets.QPushButton(self.centralwidget)
        self.add_standard_volume_name.setGeometry(QtCore.QRect(578, 470, 161, 31))
        self.add_standard_volume_name.setStyleSheet("background-color: rgb(238, 238, 236);\n"
                                                    "font: 57 11pt \\\"Ubuntu\\\";\n"
                                                    "color:rgb(75,0,130);\n"
                                                    "font-weight: bold;")
        self.add_standard_volume_name.setObjectName("add_standard_volume_name")
        self.add_standard_volume_name.setVisible(False)
        self.table_volume = QtWidgets.QTableWidget(self.centralwidget)
        self.table_volume.setGeometry(QtCore.QRect(290, 90, 451, 370))
        self.table_volume.setObjectName("table_volume")
        self.table_volume.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.table_volume.setColumnCount(2)
        self.table_volume.setHorizontalHeaderLabels([" Standard Name ", " Volume Name"])
        self.table_volume.horizontalHeaderItem(0).setTextAlignment(QtCore.Qt.AlignLeft)
        self.table_volume.horizontalHeaderItem(1).setTextAlignment(QtCore.Qt.AlignLeft)
        header3 = self.table_volume.horizontalHeader()
        self.table_volume.verticalHeader().hide()
        header3.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header3.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self.table_volume.setVisible(False)
        # roi
        self.add_new_roi = QtWidgets.QPushButton(self.centralwidget)
        self.add_new_roi.setGeometry(QtCore.QRect(578, 470, 161, 31))
        self.add_new_roi.setStyleSheet("background-color: rgb(238, 238, 236);\n"
                                       "font: 57 11pt \\\"Ubuntu\\\";\n"
                                       "color:rgb(75,0,130);\n"
                                       "font-weight: bold;")
        self.add_new_roi.setObjectName("add_new_roi")
        self.add_new_roi.setVisible(False)
        self.table_roi = QtWidgets.QTableWidget(self.centralwidget)
        self.table_roi.setGeometry(QtCore.QRect(290, 90, 451, 370))
        self.table_roi.setObjectName("table_roi")
        self.table_roi.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.table_roi.setColumnCount(2)
        self.table_roi.verticalHeader().hide()
        self.table_roi.setHorizontalHeaderLabels([" Isodose Level (cGy) ", " ROI Name "])
        self.table_roi.horizontalHeaderItem(0).setTextAlignment(QtCore.Qt.AlignLeft)
        self.table_roi.horizontalHeaderItem(1).setTextAlignment(QtCore.Qt.AlignLeft)
        header4 = self.table_roi.horizontalHeader()
        header4.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header4.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self.table_roi.setVisible(False)

        self.table_Ids = QtWidgets.QTableWidget(self.centralwidget)
        self.table_Ids.setGeometry(QtCore.QRect(290, 90, 451, 410))
        self.table_Ids.setObjectName("table_Ids")
        self.table_Ids.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.table_Ids.setColumnCount(2)
        self.table_Ids.setHorizontalHeaderLabels([" Patient ID ", " Hash ID "])
        self.table_Ids.horizontalHeaderItem(0).setTextAlignment(QtCore.Qt.AlignLeft)
        self.table_Ids.horizontalHeaderItem(1).setTextAlignment(QtCore.Qt.AlignLeft)
        header5 = self.table_Ids.horizontalHeader()
        self.table_Ids.verticalHeader().hide()
        header5.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header5.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self.table_Ids.setVisible(False)

        self.cancel_button = QtWidgets.QPushButton(self.centralwidget)
        self.cancel_button.setGeometry(QtCore.QRect(638, 554, 101, 31))
        self.cancel_button.setStyleSheet("background-color: rgb(238, 238, 236);\n"
                                         " font: 57 11pt \\\"Ubuntu\\\";\n"
                                         "\n"
                                         "font-weight: bold;\n"
                                         "color: rgb(85, 87, 83);")
        self.cancel_button.setObjectName("cancel_button")
        self.apply_button = QtWidgets.QPushButton(self.centralwidget)
        self.apply_button.setGeometry(QtCore.QRect(510, 554, 111, 31))
        self.apply_button.setStyleSheet("background-color: rgb(238, 238, 236);\n"
                                        "font: 57 11pt \\\"Ubuntu\\\";\n"
                                        "color:rgb(75,0,130);\n"
                                        "font-weight: bold;")
        self.apply_button.setObjectName("apply_button")
        self.treeList = QtWidgets.QTreeView(self.centralwidget)
        self.treeList.setGeometry(QtCore.QRect(10, 40, 256, 461))
        self.treeList.setObjectName("treeList")
        self.treeList.setStyleSheet("QTreeView::item { padding: 10px }")
        PluginManager.setCentralWidget(self.centralwidget)
        self.treeList.setHeaderHidden(True)
        self.table_modules.setEditTriggers(QtWidgets.QTreeView.NoEditTriggers)
        self.table_view.setEditTriggers(QtWidgets.QTreeView.NoEditTriggers)
        self.table_organ.setEditTriggers(QtWidgets.QTreeView.NoEditTriggers)
        self.table_volume.setEditTriggers(QtWidgets.QTreeView.NoEditTriggers)
        self.table_roi.setEditTriggers(QtWidgets.QTreeView.NoEditTriggers)
        self.table_Ids.setEditTriggers(QtWidgets.QTreeView.NoEditTriggers)

        self.retranslateUi(PluginManager)
        QtCore.QMetaObject.connectSlotsByName(PluginManager)

    def retranslateUi(self, PluginManager):
        _translate = QtCore.QCoreApplication.translate
        PluginManager.setWindowTitle(_translate("PluginManager", "Plugin Manager"))
        self.optionTitle.setText(_translate("PluginManager", ""))
        self.cancel_button.setText(_translate("PluginManager", "Cancel"))
        self.apply_button.setText(_translate("PluginManager", "Apply"))
        self.add_new_window.setText(_translate("PluginManager", "Add New Window"))
        self.add_standard_organ_name.setText(_translate("PluginManager", "Add Standard Name"))
        self.add_standard_volume_name.setText(_translate("PluginManager", "Add Standard Name"))
        self.import_organ_csv.setText(_translate("PluginManager", "Import Spreadsheet"))
        self.add_new_roi.setText(_translate("PluginManager", "Add new Isodose"))


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    PluginManager = QtWidgets.QMainWindow()
    ui = Ui_PluginManager()
    ui.setupUi(PluginManager)
    PluginManager.show()
    sys.exit(app.exec_())
