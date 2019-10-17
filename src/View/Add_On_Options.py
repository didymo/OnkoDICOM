from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QLabel


class Ui_Add_On_Options(object):
    def setupUi(self, Add_On_Options, roi_line,roi_opacity, iso_line, iso_opacity):
        Add_On_Options.setObjectName("Add_On_Options")
        Add_On_Options.setMinimumSize(766, 600)
        Add_On_Options.setWindowIcon(QtGui.QIcon("src/Icon/logo.png"))
        Add_On_Options.setStyleSheet("")
        self.centralwidget = QtWidgets.QWidget(Add_On_Options)
        self.centralwidget.setObjectName("centralwidget")
        self.optionTitle = QtWidgets.QLabel(self.centralwidget)
        self.optionTitle.setGeometry(QtCore.QRect(290, 50, 281, 31))
        self.optionTitle.setStyleSheet("font: 57 12pt \"Ubuntu\";\n"
                                       "font-weight: bold;")
        self.optionTitle.setObjectName("optionTitle")
        self.table_modules = QtWidgets.QLabel(self.centralwidget)
        self.table_modules.setGeometry(QtCore.QRect(290, 90, 451, 70))
        self.table_modules.setObjectName("table_modules")
        self.table_modules.setStyleSheet("font: 57 11pt \\\"Ubuntu\\\";\n"
                                          "color:rgb(0,0,0);\n")
        self.table_modules.setText(" Here are listed all the user options used in Onko. By using \n Add-On Options you will be able to Add/Modify/Delete the \n settings for the displayed options on the left. ")
        # buttons per view
        self.add_new_window = QtWidgets.QPushButton(self.centralwidget)
        self.add_new_window.setGeometry(QtCore.QRect(598, 470, 141, 31))
        self.add_new_window.setCursor(
            QtGui.QCursor(QtCore.Qt.PointingHandCursor))
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
        self.add_standard_organ_name.setCursor(
            QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.add_standard_organ_name.setStyleSheet("background-color: rgb(238, 238, 236);\n"
                                                   "font: 57 11pt \\\"Ubuntu\\\";\n"
                                                   "color:rgb(75,0,130);\n"
                                                   "font-weight: bold;")
        self.add_standard_organ_name.setObjectName("add_standard_organ_name")
        self.table_organ = QtWidgets.QTableWidget(self.centralwidget)
        self.table_organ.setGeometry(QtCore.QRect(290, 90, 451, 370))
        self.table_organ.setObjectName("table_organ")
        self.table_organ.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.table_organ.setColumnCount(4)
        self.table_organ.setHorizontalHeaderLabels([" Standard Name ", " FMA ID ", " Organ ", " Url "])
        self.table_organ.horizontalHeaderItem(0).setTextAlignment(QtCore.Qt.AlignLeft)
        self.table_organ.horizontalHeaderItem(1).setTextAlignment(QtCore.Qt.AlignLeft)
        self.table_organ.horizontalHeaderItem(2).setTextAlignment(QtCore.Qt.AlignLeft)
        self.table_organ.horizontalHeaderItem(3).setTextAlignment(QtCore.Qt.AlignLeft)
        header2 = self.table_organ.horizontalHeader()
        header2.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header2.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        header2.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        header2.setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch)
        self.table_organ.setVisible(False)
        self.table_organ.verticalHeader().hide()
        self.add_standard_organ_name.setVisible(False)

        self.import_organ_csv = QtWidgets.QPushButton(self.centralwidget)
        self.import_organ_csv.setCursor(
            QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.import_organ_csv.setGeometry(QtCore.QRect(406, 470, 161, 31))
        self.import_organ_csv.setStyleSheet("background-color: rgb(238, 238, 236);\n"
                                            "font: 57 11pt \\\"Ubuntu\\\";\n"
                                            "color:rgb(75,0,130);\n"
                                            "font-weight: bold;")
        self.import_organ_csv.setObjectName("import_organ_csv")
        self.import_organ_csv.setVisible(False)

        # volume
        self.add_standard_volume_name = QtWidgets.QPushButton(self.centralwidget)
        self.add_standard_volume_name.setCursor(
            QtGui.QCursor(QtCore.Qt.PointingHandCursor))
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
        self.add_new_roi.setCursor(
            QtGui.QCursor(QtCore.Qt.PointingHandCursor))
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
        self.table_roi.setColumnCount(3)
        self.table_roi.verticalHeader().hide()
        self.table_roi.setHorizontalHeaderLabels([" Isodose Level (cGy) ", " ROI Name ", " Notes "])
        self.table_roi.horizontalHeaderItem(0).setTextAlignment(QtCore.Qt.AlignLeft)
        self.table_roi.horizontalHeaderItem(1).setTextAlignment(QtCore.Qt.AlignLeft)
        self.table_roi.horizontalHeaderItem(2).setTextAlignment(QtCore.Qt.AlignLeft)
        header4 = self.table_roi.horizontalHeader()
        header4.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header4.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        header4.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        self.table_roi.setVisible(False)

        self.table_Ids = QtWidgets.QTableWidget(self.centralwidget)
        self.table_Ids.setGeometry(QtCore.QRect(290, 90, 451, 370))
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
        self.note=QtWidgets.QLabel(self.centralwidget)
        self.note.setGeometry(QtCore.QRect(295, 457, 451, 50))
        self.note.setObjectName('note')
        self.note.setStyleSheet("font: 57 11pt \\\"Ubuntu\\\";\n"
                                        "color:rgb(0,0,0)")
        self.note.setVisible(False)
        self.cancel_button = QtWidgets.QPushButton(self.centralwidget)
        self.cancel_button.setCursor(
            QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.cancel_button.setGeometry(QtCore.QRect(638, 554, 101, 31))
        self.cancel_button.setStyleSheet("background-color: rgb(238, 238, 236);\n"
                                         " font: 57 11pt \\\"Ubuntu\\\";\n"
                                         "\n"
                                         "font-weight: bold;\n"
                                         "color: rgb(85, 87, 83);")
        self.cancel_button.setObjectName("cancel_button")
        self.apply_button = QtWidgets.QPushButton(self.centralwidget)
        self.apply_button.setCursor(
            QtGui.QCursor(QtCore.Qt.PointingHandCursor))
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
        Add_On_Options.setCentralWidget(self.centralwidget)
        self.treeList.setHeaderHidden(True)
        self.table_view.setEditTriggers(QtWidgets.QTreeView.NoEditTriggers)
        self.table_organ.setEditTriggers(QtWidgets.QTreeView.NoEditTriggers)
        self.table_volume.setEditTriggers(QtWidgets.QTreeView.NoEditTriggers)
        self.table_roi.setEditTriggers(QtWidgets.QTreeView.NoEditTriggers)
        self.table_Ids.setEditTriggers(QtWidgets.QTreeView.NoEditTriggers)
        self.fill_layout = QtWidgets.QFormLayout(self.centralwidget)
        self.fill_options = QtWidgets.QWidget(self.centralwidget)
        self.line_style_ROI = QtWidgets.QComboBox(self.fill_options)
        self.line_style_ROI.addItem("No Pen")
        self.line_style_ROI.addItem("Solid Line")
        self.line_style_ROI.addItem("Dash Line")
        self.line_style_ROI.addItem("Dot Line")
        self.line_style_ROI.addItem("Dash-Dot Line")
        self.line_style_ROI.addItem("Dash-Dot-Dot Line")
        self.opacity_ROI = QtWidgets.QSlider(QtCore.Qt.Horizontal)

        self.opacity_ROI.setMinimum(0)
        self.opacity_ROI.setMaximum(100)
        self.opacity_ROI.setTickPosition(QtWidgets.QSlider.TicksLeft)
        self.opacity_ROI.setTickInterval(10)
        self.opacity_ROI.setValue(roi_opacity)
        self.opacityLabel_ROI = QtWidgets.QLabel("ROI Fill Opacity: \t {}%".format(int(self.opacity_ROI.value())))
        self.line_style_ISO = QtWidgets.QComboBox(self.fill_options)
        self.line_style_ISO.addItem("No Pen")
        self.line_style_ISO.addItem("Solid Line")
        self.line_style_ISO.addItem("Dash Line")
        self.line_style_ISO.addItem("Dot Line")
        self.line_style_ISO.addItem("Dash-Dot Line")
        self.line_style_ISO.addItem("Dash-Dot-Dot Line")
        self.opacity_ISO = QtWidgets.QSlider(QtCore.Qt.Horizontal)

        self.opacity_ISO.setMinimum(0)
        self.opacity_ISO.setMaximum(100)
        self.opacity_ISO.setTickPosition(QtWidgets.QSlider.TicksLeft)
        self.opacity_ISO.setTickInterval(10)
        self.opacity_ISO.setValue(iso_opacity)
        self.opacityLabel_ISO = QtWidgets.QLabel("ISO Fill Opacity: \t {}%".format(int(self.opacity_ISO.value())))
        self.opacity_ISO.valueChanged.connect(self.update_ISO_opacity)
        self.fill_layout.addRow(QLabel("ROI Line Style: "), self.line_style_ROI)
        self.fill_layout.addRow(QLabel(""))
        self.fill_layout.addRow(self.opacityLabel_ROI, self.opacity_ROI)
        self.fill_layout.addRow(QLabel(""))
        self.opacity_ROI.valueChanged.connect(self.update_ROI_opacity)
        self.fill_layout.addRow(QLabel("ISO Line Style: "), self.line_style_ISO)
        self.fill_layout.addRow(QLabel(""))
        self.fill_layout.addRow(self.opacityLabel_ISO,self.opacity_ISO)
        self.line_style_ROI.setCurrentIndex(roi_line)
        self.line_style_ISO.setCurrentIndex(iso_line)



        self.fill_options.setLayout(self.fill_layout)

        self.fill_options.setGeometry(QtCore.QRect(290, 90, 451, 370))
        self.fill_options.setVisible(False)
        self.fill_options.setObjectName('fill_options')


        self.retranslateUi(Add_On_Options)
        QtCore.QMetaObject.connectSlotsByName(Add_On_Options)

    def update_ROI_opacity(self):
        self.opacityLabel_ROI.setText("ROI Fill Opacity: \t {}%".format(int(self.opacity_ROI.value())))
    def update_ISO_opacity(self):
        self.opacityLabel_ISO.setText("ISO Fill Opacity: \t {}%".format(int(self.opacity_ISO.value())))

    def retranslateUi(self, Add_On_Options):
        _translate = QtCore.QCoreApplication.translate
        Add_On_Options.setWindowTitle(_translate("Add_On_Options", "Add-On Options"))
        self.optionTitle.setText(_translate("Add_On_Options", "User Options"))
        self.note.setText(_translate("Add_On_Options", "Note: This is a list of all the patients anonymized using Onko.\n It is your responsability to ensure their privacy."))
        self.cancel_button.setText(_translate("Add_On_Options", "Cancel"))
        self.apply_button.setText(_translate("Add_On_Options", "Apply"))
        self.add_new_window.setText(_translate("Add_On_Options", "Add New Window"))
        self.add_standard_organ_name.setText(_translate("Add_On_Options", "Add Standard Name"))
        self.add_standard_volume_name.setText(_translate("Add_On_Options", "Add Standard Name"))
        self.import_organ_csv.setText(_translate("Add_On_Options", "Import Spreadsheet"))
        self.add_new_roi.setText(_translate("Add_On_Options", "Add new Isodose"))


# if __name__ == "__main__":
#     import sys
#
#     app = QtWidgets.QApplication(sys.argv)
#     Add_On_Options = QtWidgets.QMainWindow()
#     ui = Ui_Add_On_Options()
#     ui.setupUi(Add_On_Options)
#     Add_On_Options.show()
#     sys.exit(app.exec_())
