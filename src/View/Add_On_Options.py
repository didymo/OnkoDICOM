from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Add_On_Options(object):
    """
    Create all UI components for the Add-On options window.
    """

    def __init__(self):
        self.table_view = None
        self.table_organ = None
        self.table_volume = None
        # self.table_roi = None
        self.table_Ids = None
        self.add_new_window = None
        self.add_standard_organ_name = None
        self.import_organ_csv = None
        self.add_standard_volume_name = None
        # self.add_new_roi = None
        self.note = None
        self.fill_options = None

    def setupUi(self, Add_On_Options, roi_line, roi_opacity, iso_line, iso_opacity, line_width):
        """
        Create the window and the components for each option view.
        """
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
        # The following line is commented out as it contains the possibility to create ROI from isodoses which is not
        # yet supported
        # self.roi_from_isodose_options = RoiFromIsodoseOptions(self)
        self.patient_hash_options = PatientHashId(self)
        self.line_fill_options = LineFillOptions(self, roi_line, roi_opacity, iso_line, iso_opacity, line_width)

        self.create_cancel_button()
        self.create_apply_button()
        self.init_tree_list()

        Add_On_Options.setCentralWidget(self.widget)
        QtCore.QMetaObject.connectSlotsByName(Add_On_Options)

    def create_cancel_button(self):
        """
        Create CANCEL button for the whole window.
        """
        self.cancel_button = QtWidgets.QPushButton(self.widget)
        self.cancel_button.setCursor(
            QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.cancel_button.setGeometry(QtCore.QRect(638, 554, 101, 31))
        self.cancel_button.setStyleSheet("background-color: rgb(238, 238, 236);\n"
                                         " font: 57 11pt \\\"Ubuntu\\\";\n"
                                         "\n"
                                         "font-weight: bold;\n"
                                         "color: rgb(85, 87, 83);")

        _translate = QtCore.QCoreApplication.translate
        self.cancel_button.setText(_translate("Add_On_Options", "Cancel"))


    def create_apply_button(self):
        """
        Create APPLY button to save all changes made.
        """
        self.apply_button = QtWidgets.QPushButton(self.widget)
        self.apply_button.setCursor(
            QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.apply_button.setGeometry(QtCore.QRect(510, 554, 111, 31))
        self.apply_button.setStyleSheet("background-color: rgb(238, 238, 236);\n"
                                        "font: 57 11pt \\\"Ubuntu\\\";\n"
                                        "color:rgb(75,0,130);\n"
                                        "font-weight: bold;")

        _translate = QtCore.QCoreApplication.translate
        self.apply_button.setText(_translate("Add_On_Options", "Apply"))


    def init_user_options_header(self):
        """
        Create title that holds the chosen option from the tree and its description.
        """
        #label that holds the chosen option from the tree
        self.optionTitle = QtWidgets.QLabel(self.widget)
        self.optionTitle.setGeometry(QtCore.QRect(290, 50, 281, 31))
        self.optionTitle.setStyleSheet("font: 57 12pt \"Ubuntu\";\n"
                                       "font-weight: bold;")
        _translate = QtCore.QCoreApplication.translate
        self.optionTitle.setText(_translate("Add_On_Options", "User Options"))

        #description holder widget
        self.table_modules = QtWidgets.QLabel(self.widget)
        self.table_modules.setGeometry(QtCore.QRect(290, 90, 451, 70))
        self.table_modules.setStyleSheet("font: 57 11pt \\\"Ubuntu\\\";\n"
                                         "color:rgb(0,0,0);\n")
        self.table_modules.setText(
            " Here are listed all the user options used in Onko. By using \n "
            "Add-On Options you will be able to Add/Modify/Delete the \n"
            " settings for the displayed options on the left. ")


    def init_tree_list(self):
        """
        Create a tree view that holds the different options.
        """
        self.treeList = QtWidgets.QTreeView(self.widget)
        self.treeList.setGeometry(QtCore.QRect(10, 40, 256, 461))
        self.treeList.setStyleSheet("QTreeView::item { padding: 10px }")
        self.treeList.setHeaderHidden(True)
        #Triggering the view change according to the row selected in the tree
        self.treeList.clicked.connect(self.display)

    def display(self, index):
        """
        Function triggered when an item from the tree view on the left column is clicked.
        Change the display of the right view of the window in regards to the option chosen from the tree.
        """
        item = self.treeList.selectedIndexes()[0]
        self.optionTitle.setText(item.model().itemFromIndex(index).text()) #changes the title
        self.changeDisplay(item.model().itemFromIndex(index).text()) #changes the display

    def changeDisplay(self, type):
        """
        Update the right view display of the window.
        """
        # Check which option is chosen and update the views
        # commented out lines are for the extra option (ROI by Isodose)
        if type == "Image Windowing":
            self.table_modules.setVisible(False)
            self.table_view.setVisible(True)
            self.table_organ.setVisible(False)
            self.table_volume.setVisible(False)
            # self.table_roi.setVisible(False)
            self.table_Ids.setVisible(False)
            self.add_new_window.setVisible(True)
            # self.add_new_roi.setVisible(False)
            self.add_standard_volume_name.setVisible(False)
            self.add_standard_organ_name.setVisible(False)
            self.import_organ_csv.setVisible(False)
            self.note.setVisible(False)
            self.fill_options.setVisible(False)
        elif type == "Standard Organ Names":
            self.table_modules.setVisible(False)
            self.table_view.setVisible(False)
            self.table_organ.setVisible(True)
            self.table_volume.setVisible(False)
            # self.table_roi.setVisible(False)
            self.table_Ids.setVisible(False)
            self.add_new_window.setVisible(False)
            # self.add_new_roi.setVisible(False)
            self.add_standard_volume_name.setVisible(False)
            self.add_standard_organ_name.setVisible(True)
            self.import_organ_csv.setVisible(True)
            self.note.setVisible(False)
            self.fill_options.setVisible(False)
        elif type == "Standard Volume Names":
            self.table_modules.setVisible(False)
            self.table_view.setVisible(False)
            self.table_organ.setVisible(False)
            self.table_volume.setVisible(True)
            # self.table_roi.setVisible(False)
            self.table_Ids.setVisible(False)
            self.add_new_window.setVisible(False)
            # self.add_new_roi.setVisible(False)
            self.add_standard_volume_name.setVisible(True)
            self.add_standard_organ_name.setVisible(False)
            self.import_organ_csv.setVisible(False)
            self.note.setVisible(False)
            self.fill_options.setVisible(False)
        # elif type == "Create ROI from Isodose":
        #     self.table_modules.setVisible(False)
        #     self.table_view.setVisible(False)
        #     self.table_organ.setVisible(False)
        #     self.table_volume.setVisible(False)
        #     self.table_roi.setVisible(True)
        #     self.table_Ids.setVisible(False)
        #     self.add_new_window.setVisible(False)
        #     self.add_new_roi.setVisible(True)
        #     self.add_standard_volume_name.setVisible(False)
        #     self.add_standard_organ_name.setVisible(False)
        #     self.import_organ_csv.setVisible(False)
        #     self.note.setVisible(False)
        #     self.fill_options.setVisible(False)
        elif type == "Patient ID - Hash ID":
            self.table_modules.setVisible(False)
            self.table_view.setVisible(False)
            self.table_organ.setVisible(False)
            self.table_volume.setVisible(False)
            # self.table_roi.setVisible(False)
            self.table_Ids.setVisible(True)
            self.add_new_window.setVisible(False)
            # self.add_new_roi.setVisible(False)
            self.add_standard_volume_name.setVisible(False)
            self.add_standard_organ_name.setVisible(False)
            self.import_organ_csv.setVisible(False)
            self.note.setVisible(True)
            self.fill_options.setVisible(False)
        elif type == "User Options":
            self.add_new_window.setVisible(False)
            # self.add_new_roi.setVisible(False)
            self.add_standard_volume_name.setVisible(False)
            self.add_standard_organ_name.setVisible(False)
            self.import_organ_csv.setVisible(False)
            self.table_modules.setVisible(True)
            self.table_view.setVisible(False)
            self.table_organ.setVisible(False)
            self.table_volume.setVisible(False)
            # self.table_roi.setVisible(False)
            self.table_Ids.setVisible(False)
            self.note.setVisible(False)
            self.fill_options.setVisible(False)
        elif type == 'Line & Fill configuration':
            self.add_new_window.setVisible(False)
            # self.add_new_roi.setVisible(False)
            self.add_standard_volume_name.setVisible(False)
            self.add_standard_organ_name.setVisible(False)
            self.import_organ_csv.setVisible(False)
            self.table_modules.setVisible(False)
            self.table_view.setVisible(False)
            self.table_organ.setVisible(False)
            self.table_volume.setVisible(False)
            # self.table_roi.setVisible(False)
            self.table_Ids.setVisible(False)
            self.note.setVisible(False)
            self.fill_options.setVisible(True)





class WindowingOptions(object):
    """
    Manage the UI of Windowing option.
    """
    def __init__(self, window_options):
        """
        Create the components for the UI of Windowing view.
        """
        self.window = window_options
        self.create_add_button()
        self.create_table_view()

    def create_add_button(self):
        """
        Create a button to add a new window view.
        """
        self.window.add_new_window = QtWidgets.QPushButton(self.window.widget)
        self.window.add_new_window.setGeometry(QtCore.QRect(598, 470, 141, 31))
        self.window.add_new_window.setCursor(
            QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.window.add_new_window.setStyleSheet("background-color: rgb(238, 238, 236);\n"
                                          "font: 57 11pt \\\"Ubuntu\\\";\n"
                                          "color:rgb(75,0,130);\n"
                                          "font-weight: bold;")
        self.window.add_new_window.setVisible(False)

        _translate = QtCore.QCoreApplication.translate
        self.window.add_new_window.setText(_translate("Add_On_Options", "Add New Window"))

    def create_table_view(self):
        """
        Create a table to hold all the windowing options.
        """
        self.window.table_view = QtWidgets.QTableWidget(self.window.widget)
        self.window.table_view.setGeometry(QtCore.QRect(290, 90, 451, 370))
        self.window.table_view.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.window.table_view.setColumnCount(4)
        self.window.table_view.setHorizontalHeaderLabels([" Window Name ", " Scan ", " Window ", " Level "])
        self.window.table_view.horizontalHeaderItem(0).setTextAlignment(QtCore.Qt.AlignLeft)
        self.window.table_view.horizontalHeaderItem(1).setTextAlignment(QtCore.Qt.AlignLeft)
        self.window.table_view.horizontalHeaderItem(2).setTextAlignment(QtCore.Qt.AlignLeft)
        self.window.table_view.horizontalHeaderItem(3).setTextAlignment(QtCore.Qt.AlignLeft)
        self.window.table_view.verticalHeader().hide()
        header1 = self.window.table_view.horizontalHeader()
        header1.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header1.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        header1.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        header1.setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch)
        self.window.table_view.setVisible(False)
        #removing the ability to edit tables with immediate click
        self.window.table_view.setEditTriggers(QtWidgets.QTreeView.NoEditTriggers)


class StandardOrganOptions(object):
    """
    Manage the UI of Standard Organ option.
    """
    def __init__(self, window_options):
        """
        Create the components for the UI of Standard Organ view.
        """
        self.window = window_options
        self.create_add_button()
        self.create_import_csv_button()
        self.create_table_view()


    def create_add_button(self):
        """
        Create a button to add a new standard organ name.
        """
        self.window.add_standard_organ_name = QtWidgets.QPushButton(self.window.widget)
        self.window.add_standard_organ_name.setGeometry(QtCore.QRect(578, 470, 161, 31))
        self.window.add_standard_organ_name.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.window.add_standard_organ_name.setStyleSheet("background-color: rgb(238, 238, 236);\n"
                                                   "font: 57 11pt \\\"Ubuntu\\\";\n"
                                                   "color:rgb(75,0,130);\n"
                                                   "font-weight: bold;")
        self.window.add_standard_organ_name.setVisible(False)

        _translate = QtCore.QCoreApplication.translate
        self.window.add_standard_organ_name.setText(_translate("Add_On_Options", "Add Standard Name"))

    def create_import_csv_button(self):
        """
        Create a button to import a csv of standard organs.
        """
        self.window.import_organ_csv = QtWidgets.QPushButton(self.window.widget)
        self.window.import_organ_csv.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.window.import_organ_csv.setGeometry(QtCore.QRect(406, 470, 161, 31))
        self.window.import_organ_csv.setStyleSheet("background-color: rgb(238, 238, 236);\n"
                                            "font: 57 11pt \\\"Ubuntu\\\";\n"
                                            "color:rgb(75,0,130);\n"
                                            "font-weight: bold;")
        self.window.import_organ_csv.setVisible(False)

        _translate = QtCore.QCoreApplication.translate
        self.window.import_organ_csv.setText(_translate("Add_On_Options", "Import Spreadsheet"))

    def create_table_view(self):
        """
        Create a table to hold all the standard organ entries.
        """
        self.window.table_organ = QtWidgets.QTableWidget(self.window.widget)
        self.window.table_organ.setGeometry(QtCore.QRect(290, 90, 451, 370))
        self.window.table_organ.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.window.table_organ.setColumnCount(4)
        self.window.table_organ.setHorizontalHeaderLabels([" Standard Name ", " FMA ID ", " Organ ", " Url "])
        self.window.table_organ.horizontalHeaderItem(0).setTextAlignment(QtCore.Qt.AlignLeft)
        self.window.table_organ.horizontalHeaderItem(1).setTextAlignment(QtCore.Qt.AlignLeft)
        self.window.table_organ.horizontalHeaderItem(2).setTextAlignment(QtCore.Qt.AlignLeft)
        self.window.table_organ.horizontalHeaderItem(3).setTextAlignment(QtCore.Qt.AlignLeft)

        header2 = self.window.table_organ.horizontalHeader()
        header2.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header2.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        header2.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        header2.setSectionResizeMode(3, QtWidgets.QHeaderView.Stretch)
        self.window.table_organ.setVisible(False)
        self.window.table_organ.verticalHeader().hide()
        #removing the ability to edit tables with immediate click
        self.window.table_organ.setEditTriggers(QtWidgets.QTreeView.NoEditTriggers)


class StandardVolumeOptions(object):
    """
    Manage the UI of Standard Volume option.
    """
    def __init__(self, window_options):
        """
        Create the components for the UI of Standard Volume view.
        """
        self.window = window_options
        self.create_add_button()
        self.create_table_view()

    def create_add_button(self):
        """
        Create a button to add a new standard volume name.
        """
        self.window.add_standard_volume_name = QtWidgets.QPushButton(self.window.widget)
        self.window.add_standard_volume_name.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.window.add_standard_volume_name.setGeometry(QtCore.QRect(578, 470, 161, 31))
        self.window.add_standard_volume_name.setStyleSheet("background-color: rgb(238, 238, 236);\n"
                                                    "font: 57 11pt \\\"Ubuntu\\\";\n"
                                                    "color:rgb(75,0,130);\n"
                                                    "font-weight: bold;")
        self.window.add_standard_volume_name.setVisible(False)

        _translate = QtCore.QCoreApplication.translate
        self.window.add_standard_volume_name.setText(_translate("Add_On_Options", "Add Standard Name"))

    def create_table_view(self):
        """
        Create a table to hold the volume entries.
        """
        self.window.table_volume = QtWidgets.QTableWidget(self.window.widget)
        self.window.table_volume.setGeometry(QtCore.QRect(290, 90, 451, 370))
        self.window.table_volume.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.window.table_volume.setColumnCount(2)
        self.window.table_volume.setHorizontalHeaderLabels([" Standard Name ", " Volume Name"])
        self.window.table_volume.horizontalHeaderItem(0).setTextAlignment(QtCore.Qt.AlignLeft)
        self.window.table_volume.horizontalHeaderItem(1).setTextAlignment(QtCore.Qt.AlignLeft)
        header3 = self.window.table_volume.horizontalHeader()
        self.window.table_volume.verticalHeader().hide()
        header3.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header3.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self.window.table_volume.setVisible(False)
        #removing the ability to edit tables with immediate click
        self.window.table_volume.setEditTriggers(QtWidgets.QTreeView.NoEditTriggers)


class RoiFromIsodoseOptions(object):
    """
    Manage the UI of ROI from isodose option.
    """
    def __init__(self, window_options):
        """
        Create the components for the UI of ROI from Isodose view.
        """
        self.window = window_options

    def create_add_button(self):
        """
        Create a button to create a new ROI from isodose.
        """
        self.window.add_new_roi = QtWidgets.QPushButton(self.window.widget)
        self.window.add_new_roi.setCursor(
            QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.window.add_new_roi.setGeometry(QtCore.QRect(578, 470, 161, 31))
        self.window.add_new_roi.setStyleSheet("background-color: rgb(238, 238, 236);\n"
                                       "font: 57 11pt \\\"Ubuntu\\\";\n"
                                       "color:rgb(75,0,130);\n"
                                       "font-weight: bold;")
        self.window.add_new_roi.setVisible(False)

        _translate = QtCore.QCoreApplication.translate
        self.window.add_new_roi.setText(_translate("Add_On_Options", "Add new Isodose"))

    def create_table_view(self):
        """
        Create a table to hold all the ROI creation by isodose entries.
        """
        self.window.table_roi = QtWidgets.QTableWidget(self.window.widget)
        self.window.table_roi.setGeometry(QtCore.QRect(290, 90, 451, 370))
        self.window.table_roi.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.window.table_roi.setColumnCount(3)
        self.window.table_roi.verticalHeader().hide()
        self.window.table_roi.setHorizontalHeaderLabels([" Isodose Level (cGy) ", " ROI Name ", " Notes "])
        self.window.table_roi.horizontalHeaderItem(0).setTextAlignment(QtCore.Qt.AlignLeft)
        self.window.table_roi.horizontalHeaderItem(1).setTextAlignment(QtCore.Qt.AlignLeft)
        self.window.table_roi.horizontalHeaderItem(2).setTextAlignment(QtCore.Qt.AlignLeft)
        header4 = self.window.table_roi.horizontalHeader()
        header4.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header4.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        header4.setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        self.window.table_roi.setVisible(False)
        # removing the ability to edit tables with immediate click
        self.window.table_roi.setEditTriggers(QtWidgets.QTreeView.NoEditTriggers)


class PatientHashId(object):
    """
    Manage the UI of Patient ID - Hash ID option.
    """
    def __init__(self, window_options):
        """
        Create the components for the UI of Patient ID - Hash ID view.
        """
        self.window = window_options
        self.create_table_view()
        self.create_note()

    def create_table_view(self):
        """
        Create a table to hold all the patients and their hash that the software has anonymised.
        """
        self.window.table_Ids = QtWidgets.QTableWidget(self.window.widget)
        self.window.table_Ids.setGeometry(QtCore.QRect(290, 90, 451, 370))
        self.window.table_Ids.setStyleSheet("background-color: rgb(255, 255, 255);")
        self.window.table_Ids.setColumnCount(2)
        self.window.table_Ids.setHorizontalHeaderLabels([" Patient ID ", " Hash ID "])
        self.window.table_Ids.horizontalHeaderItem(0).setTextAlignment(QtCore.Qt.AlignLeft)
        self.window.table_Ids.horizontalHeaderItem(1).setTextAlignment(QtCore.Qt.AlignLeft)
        header5 = self.window.table_Ids.horizontalHeader()
        self.window.table_Ids.verticalHeader().hide()
        header5.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header5.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self.window.table_Ids.setVisible(False)
        #removing the ability to edit tables with immediate click
        self.window.table_Ids.setEditTriggers(QtWidgets.QTreeView.NoEditTriggers)

    def create_note(self):
        """
        Create a note for the user about data privacy.
        """
        self.window.note = QtWidgets.QLabel(self.window.widget)
        self.window.note.setGeometry(QtCore.QRect(295, 457, 451, 50))
        self.window.note.setStyleSheet("font: 57 11pt \\\"Ubuntu\\\";\n"
                                "color:rgb(0,0,0)")
        self.window.note.setVisible(False)

        _translate = QtCore.QCoreApplication.translate
        self.window.note.setText(_translate("Add_On_Options",
                                     "Note: This is a list of all the patients anonymized using Onko.\n "
                                     "It is your responsability to ensure their privacy."))


class LineFillOptions(object):
    """
    Manage the UI of Line and Fill Configuration options for ROIs and Isodoses display.
    """
    def __init__(self, window_options, roi_line, roi_opacity, iso_line, iso_opacity, line_width):
        """
        Create the components for the UI of Line and Fill options and set the layout.
        """
        self.window = window_options
        self.roi_line = roi_line
        self.roi_opacity = roi_opacity
        self.iso_line = iso_line
        self.iso_opacity = iso_opacity
        self.line_width = line_width

        window_options.fill_layout = QtWidgets.QFormLayout(window_options.widget)
        window_options.fill_options = QtWidgets.QWidget(window_options.widget)
        self.create_combobox_line_style_ROI()
        self.create_slider_opacity_ROI()
        self.create_combobox_line_style_isodoses()
        self.create_slider_opacity_isodose()
        self.create_combobox_line_width()
        self.set_layout()

    def set_layout(self):
        """
        Add the components into a layout and initialize the values according to the last configuration settings.
        """
        #adding the components into a layout
        self.window.fill_layout.addRow(QtWidgets.QLabel("ROI Line Style: "), self.window.line_style_ROI)
        self.window.fill_layout.addRow(QtWidgets.QLabel(""))
        self.window.fill_layout.addRow(self.window.opacityLabel_ROI, self.window.opacity_ROI)
        self.window.fill_layout.addRow(QtWidgets.QLabel(""))
        self.window.fill_layout.addRow(QtWidgets.QLabel("ISO Line Style: "), self.window.line_style_ISO)
        self.window.fill_layout.addRow(QtWidgets.QLabel(""))
        self.window.fill_layout.addRow(self.window.opacityLabel_ISO, self.window.opacity_ISO)
        self.window.fill_layout.addRow(QtWidgets.QLabel(""))
        self.window.fill_layout.addRow(QtWidgets.QLabel("Line Width: "), self.window.line_width)

        #inserting the last configuration settings on initialisation
        self.window.line_style_ROI.setCurrentIndex(self.roi_line)
        self.window.line_style_ISO.setCurrentIndex(self.iso_line)
        self.window.line_width.setCurrentText(str(self.line_width))

        self.window.fill_options.setLayout(self.window.fill_layout)
        self.window.fill_options.setGeometry(QtCore.QRect(290, 90, 451, 370))
        self.window.fill_options.setVisible(False)


    def create_combobox_line_style_ROI(self):
        """
        Create combobox with the available lines for ROIs.
        """
        self.window.line_style_ROI = QtWidgets.QComboBox(self.window.fill_options)
        self.window.line_style_ROI.addItem("No Pen")
        self.window.line_style_ROI.addItem("Solid Line")
        self.window.line_style_ROI.addItem("Dash Line")
        self.window.line_style_ROI.addItem("Dot Line")
        self.window.line_style_ROI.addItem("Dash-Dot Line")
        self.window.line_style_ROI.addItem("Dash-Dot-Dot Line")

    def create_slider_opacity_ROI(self):
        """
        Create slider to determine the opacity of the fill for ROIs
        """
        self.window.opacity_ROI = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.window.opacity_ROI.setMinimum(0)
        self.window.opacity_ROI.setMaximum(100)
        self.window.opacity_ROI.setTickPosition(QtWidgets.QSlider.TicksLeft)
        self.window.opacity_ROI.setTickInterval(10)
        self.window.opacity_ROI.setValue(self.roi_opacity)
        self.window.opacity_ROI.valueChanged.connect(self.update_ROI_opacity)
        self.window.opacityLabel_ROI = QtWidgets.QLabel(
            "ROI Fill Opacity: \t {}%".format(int(self.window.opacity_ROI.value())))

    def create_combobox_line_style_isodoses(self):
        """
        Create combobox with the available lines for isodoses
        """
        self.window.line_style_ISO = QtWidgets.QComboBox(self.window.fill_options)
        self.window.line_style_ISO.addItem("No Pen")
        self.window.line_style_ISO.addItem("Solid Line")
        self.window.line_style_ISO.addItem("Dash Line")
        self.window.line_style_ISO.addItem("Dot Line")
        self.window.line_style_ISO.addItem("Dash-Dot Line")
        self.window.line_style_ISO.addItem("Dash-Dot-Dot Line")

    def create_slider_opacity_isodose(self):
        """
        Create slider to determine opacity of the fill for isodoses
        """
        self.window.opacity_ISO = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.window.opacity_ISO.setMinimum(0)
        self.window.opacity_ISO.setMaximum(100)
        self.window.opacity_ISO.setTickPosition(QtWidgets.QSlider.TicksLeft)
        self.window.opacity_ISO.setTickInterval(10)
        self.window.opacity_ISO.setValue(self.iso_opacity)
        self.window.opacity_ISO.valueChanged.connect(self.update_ISO_opacity)
        self.window.opacityLabel_ISO = QtWidgets.QLabel(
            "ISO Fill Opacity: \t {}%".format(int(self.window.opacity_ISO.value())))

    def create_combobox_line_width(self):
        """
        Create combobox to hold the line width options
        """
        self.window.line_width = QtWidgets.QComboBox(self.window.fill_options)
        self.window.line_width.addItem("0.5")
        self.window.line_width.addItem("1")
        self.window.line_width.addItem("1.5")
        self.window.line_width.addItem("2")
        self.window.line_width.addItem("2.5")

    def update_ROI_opacity(self):
        """
        Update the percentage on slider change for ROIs.
        """
        self.window.opacityLabel_ROI.setText("ROI Fill Opacity: \t {}%".format(int(self.window.opacity_ROI.value())))

    def update_ISO_opacity(self):
        """
        Update the percentage on slider change for isodoses.
        """
        self.window.opacityLabel_ISO.setText("ISO Fill Opacity: \t {}%".format(int(self.window.opacity_ISO.value())))
