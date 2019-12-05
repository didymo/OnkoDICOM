#####################################################################################################################
#                                                                                                                   #
#   This file creates all the UI components for the Add-On options window                                           #
#                                                                                                                   #
#####################################################################################################################
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QLabel


class Ui_Add_On_Options(object):

    # creator function
    def setupUi(self, Add_On_Options, roi_line, roi_opacity, iso_line, iso_opacity, line_width):
        Add_On_Options.setObjectName("Add_On_Options")
        Add_On_Options.setMinimumSize(766, 600)
        Add_On_Options.setStyleSheet("")
        Add_On_Options.setWindowIcon(QtGui.QIcon("src/Icon/DONE.png"))

        _translate = QtCore.QCoreApplication.translate
        Add_On_Options.setWindowTitle(_translate("Add_On_Options", "Add-On Options"))
        
        self.widget = QtWidgets.QWidget(Add_On_Options)

        self.init_user_options_header()

        self.windowing_options = WindowingOptions(self)
        self.standard_organ_options = StandardOrganOptions(self)
        self.standard_volume_options = StandardVolumeOptions(self)
        # The following line is commented out as it contains the possibility to create ROI from isodoses
        # which is not yet supported
        # self.roi_from_isodose_options = RoiFromIsodoseOptions(self)
        self.patient_hash_options = PatientHashId(self)
        self.line_fill_options = LineFillOptions(self, roi_line, roi_opacity, iso_line, iso_opacity, line_width)

        self.create_cancel_button()
        self.create_apply_button()
        self.init_tree_list()

        Add_On_Options.setCentralWidget(self.widget)
        QtCore.QMetaObject.connectSlotsByName(Add_On_Options)

    def create_cancel_button(self):
        #CANCEL button for the whole window
        self.cancel_button = QtWidgets.QPushButton(self.widget)
        self.cancel_button.setCursor(
            QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.cancel_button.setGeometry(QtCore.QRect(638, 554, 101, 31))
        self.cancel_button.setStyleSheet("background-color: rgb(238, 238, 236);\n"
                                         " font: 57 11pt \\\"Ubuntu\\\";\n"
                                         "\n"
                                         "font-weight: bold;\n"
                                         "color: rgb(85, 87, 83);")
        self.cancel_button.setObjectName("cancel_button")

        _translate = QtCore.QCoreApplication.translate
        self.cancel_button.setText(_translate("Add_On_Options", "Cancel"))


    def create_apply_button(self):
        #APPLY button to save all changes made
        self.apply_button = QtWidgets.QPushButton(self.widget)
        self.apply_button.setCursor(
            QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.apply_button.setGeometry(QtCore.QRect(510, 554, 111, 31))
        self.apply_button.setStyleSheet("background-color: rgb(238, 238, 236);\n"
                                        "font: 57 11pt \\\"Ubuntu\\\";\n"
                                        "color:rgb(75,0,130);\n"
                                        "font-weight: bold;")
        self.apply_button.setObjectName("apply_button")

        _translate = QtCore.QCoreApplication.translate
        self.apply_button.setText(_translate("Add_On_Options", "Apply"))


    def init_user_options_header(self):
        #label that holds the chosen option from the tree
        self.optionTitle = QtWidgets.QLabel(self.widget)
        self.optionTitle.setGeometry(QtCore.QRect(290, 50, 281, 31))
        self.optionTitle.setStyleSheet("font: 57 12pt \"Ubuntu\";\n"
                                       "font-weight: bold;")
        self.optionTitle.setObjectName("optionTitle")
        _translate = QtCore.QCoreApplication.translate
        self.optionTitle.setText(_translate("Add_On_Options", "User Options"))
        #description holder widget
        self.table_modules = QtWidgets.QLabel(self.widget)
        self.table_modules.setGeometry(QtCore.QRect(290, 90, 451, 70))
        self.table_modules.setObjectName("table_modules")
        self.table_modules.setStyleSheet("font: 57 11pt \\\"Ubuntu\\\";\n"
                                         "color:rgb(0,0,0);\n")
        self.table_modules.setText(
            " Here are listed all the user options used in Onko. By using \n "
            "Add-On Options you will be able to Add/Modify/Delete the \n"
            " settings for the displayed options on the left. ")


    def init_tree_list(self):
        #TREE VIEW  that holds the different Options
        self.treeList = QtWidgets.QTreeView(self.widget)
        self.treeList.setGeometry(QtCore.QRect(10, 40, 256, 461))
        self.treeList.setObjectName("treeList")
        self.treeList.setStyleSheet("QTreeView::item { padding: 10px }")
        self.treeList.setHeaderHidden(True)


class WindowingOptions(object):
    def __init__(self, window_options):
        # adding a new window view
        window_options.add_new_window = QtWidgets.QPushButton(window_options.widget)
        window_options.add_new_window.setGeometry(QtCore.QRect(598, 470, 141, 31))
        window_options.add_new_window.setCursor(
            QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        window_options.add_new_window.setStyleSheet("background-color: rgb(238, 238, 236);\n"
                                          "font: 57 11pt \\\"Ubuntu\\\";\n"
                                          "color:rgb(75,0,130);\n"
                                          "font-weight: bold;")
        window_options.add_new_window.setObjectName("add_new_window")
        window_options.add_new_window.setVisible(False)

        # table to hold all the windowing options
        window_options.table_view = QtWidgets.QTableWidget(window_options.widget)
        window_options.table_view.setGeometry(QtCore.QRect(290, 90, 451, 370))
        window_options.table_view.setObjectName("table_view")
        window_options.table_view.setStyleSheet("background-color: rgb(255, 255, 255);")
        window_options.table_view.setColumnCount(4)
        window_options.table_view.setHorizontalHeaderLabels([" Window Name ", " Scan ", " Window ", " Level "])
        window_options.table_view.horizontalHeaderItem(0).setTextAlignment(QtCore.Qt.AlignLeft)
        window_options.table_view.horizontalHeaderItem(1).setTextAlignment(QtCore.Qt.AlignLeft)
        window_options.table_view.horizontalHeaderItem(2).setTextAlignment(QtCore.Qt.AlignLeft)
        window_options.table_view.horizontalHeaderItem(3).setTextAlignment(QtCore.Qt.AlignLeft)
        window_options.table_view.verticalHeader().hide()
        header1 = window_options.table_view.horizontalHeader()
        header1.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header1.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        header1.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        header1.setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch)
        window_options.table_view.setVisible(False)
        #removing the ability to edit tables with immediate click
        window_options.table_view.setEditTriggers(QtWidgets.QTreeView.NoEditTriggers)

        _translate = QtCore.QCoreApplication.translate
        window_options.add_new_window.setText(_translate("Add_On_Options", "Add New Window"))


class StandardOrganOptions(object):
    def __init__(self, window_options):
        # button to add a new standard organ name
        window_options.add_standard_organ_name = QtWidgets.QPushButton(
            window_options.widget)
        window_options.add_standard_organ_name.setGeometry(
            QtCore.QRect(578, 470, 161, 31))
        window_options.add_standard_organ_name.setCursor(
            QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        window_options.add_standard_organ_name.setStyleSheet("background-color: rgb(238, 238, 236);\n"
                                                   "font: 57 11pt \\\"Ubuntu\\\";\n"
                                                   "color:rgb(75,0,130);\n"
                                                   "font-weight: bold;")
        window_options.add_standard_organ_name.setObjectName("add_standard_organ_name")
        #table to hold all the entries
        window_options.table_organ = QtWidgets.QTableWidget(window_options.widget)
        window_options.table_organ.setGeometry(QtCore.QRect(290, 90, 451, 370))
        window_options.table_organ.setObjectName("table_organ")
        window_options.table_organ.setStyleSheet("background-color: rgb(255, 255, 255);")
        window_options.table_organ.setColumnCount(4)
        window_options.table_organ.setHorizontalHeaderLabels([" Standard Name ", " FMA ID ", " Organ ", " Url "])
        window_options.table_organ.horizontalHeaderItem(0).setTextAlignment(QtCore.Qt.AlignLeft)
        window_options.table_organ.horizontalHeaderItem(1).setTextAlignment(QtCore.Qt.AlignLeft)
        window_options.table_organ.horizontalHeaderItem(2).setTextAlignment(QtCore.Qt.AlignLeft)
        window_options.table_organ.horizontalHeaderItem(3).setTextAlignment(QtCore.Qt.AlignLeft)

        header2 = window_options.table_organ.horizontalHeader()
        header2.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header2.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        header2.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        header2.setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch)
        window_options.table_organ.setVisible(False)
        window_options.table_organ.verticalHeader().hide()
        #removing the ability to edit tables with immediate click
        window_options.table_organ.setEditTriggers(QtWidgets.QTreeView.NoEditTriggers)

        window_options.add_standard_organ_name.setVisible(False)
        # button to import a csv of standard organs
        window_options.import_organ_csv = QtWidgets.QPushButton(window_options.widget)
        window_options.import_organ_csv.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        window_options.import_organ_csv.setGeometry(QtCore.QRect(406, 470, 161, 31))
        window_options.import_organ_csv.setStyleSheet("background-color: rgb(238, 238, 236);\n"
                                            "font: 57 11pt \\\"Ubuntu\\\";\n"
                                            "color:rgb(75,0,130);\n"
                                            "font-weight: bold;")
        window_options.import_organ_csv.setObjectName("import_organ_csv")
        window_options.import_organ_csv.setVisible(False)

        _translate = QtCore.QCoreApplication.translate
        window_options.add_standard_organ_name.setText(_translate("Add_On_Options", "Add Standard Name"))
        window_options.import_organ_csv.setText(_translate("Add_On_Options", "Import Spreadsheet"))


class StandardVolumeOptions(object):
    def __init__(self, window_options):
        # button to add a new standard volume name
        window_options.add_standard_volume_name = QtWidgets.QPushButton(window_options.widget)
        window_options.add_standard_volume_name.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        window_options.add_standard_volume_name.setGeometry(QtCore.QRect(578, 470, 161, 31))
        window_options.add_standard_volume_name.setStyleSheet("background-color: rgb(238, 238, 236);\n"
                                                    "font: 57 11pt \\\"Ubuntu\\\";\n"
                                                    "color:rgb(75,0,130);\n"
                                                    "font-weight: bold;")
        window_options.add_standard_volume_name.setObjectName("add_standard_volume_name")
        window_options.add_standard_volume_name.setVisible(False)
        # table to hold the volume entries
        window_options.table_volume = QtWidgets.QTableWidget(window_options.widget)
        window_options.table_volume.setGeometry(QtCore.QRect(290, 90, 451, 370))
        window_options.table_volume.setObjectName("table_volume")
        window_options.table_volume.setStyleSheet("background-color: rgb(255, 255, 255);")
        window_options.table_volume.setColumnCount(2)
        window_options.table_volume.setHorizontalHeaderLabels([" Standard Name ", " Volume Name"])
        window_options.table_volume.horizontalHeaderItem(0).setTextAlignment(QtCore.Qt.AlignLeft)
        window_options.table_volume.horizontalHeaderItem(1).setTextAlignment(QtCore.Qt.AlignLeft)
        header3 = window_options.table_volume.horizontalHeader()
        window_options.table_volume.verticalHeader().hide()
        header3.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header3.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        window_options.table_volume.setVisible(False)
        #removing the ability to edit tables with immediate click
        window_options.table_volume.setEditTriggers(QtWidgets.QTreeView.NoEditTriggers)

        _translate = QtCore.QCoreApplication.translate
        window_options.add_standard_volume_name.setText(_translate("Add_On_Options", "Add Standard Name"))


class RoiFromIsodoseOptions(object):
    def __init__(self, window_options):
        window_options.add_new_roi = QtWidgets.QPushButton(window_options.widget)
        window_options.add_new_roi.setCursor(
            QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        window_options.add_new_roi.setGeometry(QtCore.QRect(578, 470, 161, 31))
        window_options.add_new_roi.setStyleSheet("background-color: rgb(238, 238, 236);\n"
                                       "font: 57 11pt \\\"Ubuntu\\\";\n"
                                       "color:rgb(75,0,130);\n"
                                       "font-weight: bold;")
        window_options.add_new_roi.setObjectName("add_new_roi")
        window_options.add_new_roi.setVisible(False)
        window_options.table_roi = QtWidgets.QTableWidget(window_options.widget)
        window_options.table_roi.setGeometry(QtCore.QRect(290, 90, 451, 370))
        window_options.table_roi.setObjectName("table_roi")
        window_options.table_roi.setStyleSheet("background-color: rgb(255, 255, 255);")
        window_options.table_roi.setColumnCount(3)
        window_options.table_roi.verticalHeader().hide()
        window_options.table_roi.setHorizontalHeaderLabels(
            [" Isodose Level (cGy) ", " ROI Name ", " Notes "])
        window_options.table_roi.horizontalHeaderItem(
            0).setTextAlignment(QtCore.Qt.AlignLeft)
        window_options.table_roi.horizontalHeaderItem(
            1).setTextAlignment(QtCore.Qt.AlignLeft)
        window_options.table_roi.horizontalHeaderItem(
            2).setTextAlignment(QtCore.Qt.AlignLeft)
        header4 = window_options.table_roi.horizontalHeader()
        header4.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header4.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        header4.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        window_options.table_roi.setVisible(False)
        # removing the ability to edit tables with immediate click
        window_options.table_roi.setEditTriggers(QtWidgets.QTreeView.NoEditTriggers)

        _translate = QtCore.QCoreApplication.translate
        window_options.add_new_roi.setText(_translate("Add_On_Options", "Add new Isodose"))


class PatientHashId(object):
    def __init__(self, window_options):

        # table to hold all the patients and their hash that the software has anonymised
        window_options.table_Ids = QtWidgets.QTableWidget(window_options.widget)
        window_options.table_Ids.setGeometry(QtCore.QRect(290, 90, 451, 370))
        window_options.table_Ids.setObjectName("table_Ids")
        window_options.table_Ids.setStyleSheet("background-color: rgb(255, 255, 255);")
        window_options.table_Ids.setColumnCount(2)
        window_options.table_Ids.setHorizontalHeaderLabels([" Patient ID ", " Hash ID "])
        window_options.table_Ids.horizontalHeaderItem(0).setTextAlignment(QtCore.Qt.AlignLeft)
        window_options.table_Ids.horizontalHeaderItem(1).setTextAlignment(QtCore.Qt.AlignLeft)
        header5 = window_options.table_Ids.horizontalHeader()
        window_options.table_Ids.verticalHeader().hide()
        header5.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header5.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        window_options.table_Ids.setVisible(False)
        # Note for the user
        window_options.note = QtWidgets.QLabel(window_options.widget)
        window_options.note.setGeometry(QtCore.QRect(295, 457, 451, 50))
        window_options.note.setObjectName('note')
        window_options.note.setStyleSheet("font: 57 11pt \\\"Ubuntu\\\";\n"
                                "color:rgb(0,0,0)")
        window_options.note.setVisible(False)
        #removing the ability to edit tables with immediate click
        window_options.table_Ids.setEditTriggers(QtWidgets.QTreeView.NoEditTriggers)

        _translate = QtCore.QCoreApplication.translate
        window_options.note.setText(_translate("Add_On_Options",
                                     "Note: This is a list of all the patients anonymized using Onko.\n "
                                     "It is your responsability to ensure their privacy."))


class LineFillOptions(object):
    def __init__(self, window_options, roi_line, roi_opacity, iso_line, iso_opacity, line_width):
        self.window_options = window_options

        window_options.fill_layout = QtWidgets.QFormLayout(window_options.widget)
        window_options.fill_options = QtWidgets.QWidget(window_options.widget)

        #combo bow with the available lines for ROIs
        window_options.line_style_ROI = QtWidgets.QComboBox(window_options.fill_options)
        window_options.line_style_ROI.addItem("No Pen")
        window_options.line_style_ROI.addItem("Solid Line")
        window_options.line_style_ROI.addItem("Dash Line")
        window_options.line_style_ROI.addItem("Dot Line")
        window_options.line_style_ROI.addItem("Dash-Dot Line")
        window_options.line_style_ROI.addItem("Dash-Dot-Dot Line")

        #slider to determine opacity of the fill for ROIs
        window_options.opacity_ROI = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        window_options.opacity_ROI.setMinimum(0)
        window_options.opacity_ROI.setMaximum(100)
        window_options.opacity_ROI.setTickPosition(QtWidgets.QSlider.TicksLeft)
        window_options.opacity_ROI.setTickInterval(10)
        window_options.opacity_ROI.setValue(roi_opacity)
        window_options.opacity_ROI.valueChanged.connect(self.update_ROI_opacity)
        window_options.opacityLabel_ROI = QtWidgets.QLabel(
            "ROI Fill Opacity: \t {}%".format(int(window_options.opacity_ROI.value())))

        #combo bow with the available lines for ISODoses
        window_options.line_style_ISO = QtWidgets.QComboBox(window_options.fill_options)
        window_options.line_style_ISO.addItem("No Pen")
        window_options.line_style_ISO.addItem("Solid Line")
        window_options.line_style_ISO.addItem("Dash Line")
        window_options.line_style_ISO.addItem("Dot Line")
        window_options.line_style_ISO.addItem("Dash-Dot Line")
        window_options.line_style_ISO.addItem("Dash-Dot-Dot Line")

        #slider to determine opacity of the fill for ISODoses
        window_options.opacity_ISO = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        window_options.opacity_ISO.setMinimum(0)
        window_options.opacity_ISO.setMaximum(100)
        window_options.opacity_ISO.setTickPosition(QtWidgets.QSlider.TicksLeft)
        window_options.opacity_ISO.setTickInterval(10)
        window_options.opacity_ISO.setValue(iso_opacity)
        window_options.opacity_ISO.valueChanged.connect(self.update_ISO_opacity)
        window_options.opacityLabel_ISO = QtWidgets.QLabel(
            "ISO Fill Opacity: \t {}%".format(int(window_options.opacity_ISO.value())))

        #combo box to hold the line width options
        window_options.line_width = QtWidgets.QComboBox(window_options.fill_options)
        window_options.line_width.addItem("0.5")
        window_options.line_width.addItem("1")
        window_options.line_width.addItem("1.5")
        window_options.line_width.addItem("2")
        window_options.line_width.addItem("2.5")

        #adding the components into a layout
        window_options.fill_layout.addRow(
            QLabel("ROI Line Style: "), window_options.line_style_ROI)
        window_options.fill_layout.addRow(QLabel(""))
        window_options.fill_layout.addRow(window_options.opacityLabel_ROI, window_options.opacity_ROI)
        window_options.fill_layout.addRow(QLabel(""))
        window_options.fill_layout.addRow(
            QLabel("ISO Line Style: "), window_options.line_style_ISO)
        window_options.fill_layout.addRow(QLabel(""))
        window_options.fill_layout.addRow(window_options.opacityLabel_ISO, window_options.opacity_ISO)
        window_options.fill_layout.addRow(QLabel(""))
        window_options.fill_layout.addRow(
            QLabel("Line Width: "), window_options.line_width)

        #inserting the last configuration settings on initialisation
        window_options.line_style_ROI.setCurrentIndex(roi_line)
        window_options.line_style_ISO.setCurrentIndex(iso_line)
        window_options.line_width.setCurrentText(str(line_width))
        window_options.fill_options.setLayout(window_options.fill_layout)
        window_options.fill_options.setGeometry(QtCore.QRect(290, 90, 451, 370))
        window_options.fill_options.setVisible(False)
        window_options.fill_options.setObjectName('fill_options')

    # updating the % on slider change for ROIs
    def update_ROI_opacity(self):
        self.window_options.opacityLabel_ROI.setText(
            "ROI Fill Opacity: \t {}%".format(int(self.window_options.opacity_ROI.value())))

    # updating the % on slider change for ISODoses
    def update_ISO_opacity(self):
        self.window_options.opacityLabel_ISO.setText(
            "ISO Fill Opacity: \t {}%".format(int(self.window_options.opacity_ISO.value())))
