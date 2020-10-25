######################################################################################################
#                                                                                                    #
#   This file handles all the processes done within the Add-On Options button                        #
#                                                                                                    #
######################################################################################################
import csv
import webbrowser
from collections import deque

from PyQt5.QtWidgets import QFileDialog

from src.View.AddOnOptions import *
from src.View.InputDialogs import *


######################################################################################################
#                                                                                                    #
#   Create the Add-On Options class based on the UI from the file in View/Add-On Options             #
#                                                                                                    #
######################################################################################################


class AddOnOptions(QtWidgets.QMainWindow, UIAddOnOptions):
    def __init__(self, window):  # initialization function
        super(AddOnOptions, self).__init__()
        # read configuration file for line and fill options
        with open("src/data/line&fill_configuration", "r") as stream:
            elements = stream.readlines()
            # if file is not empty, each line represents the last saved configuration in the given order
            if len(elements) > 0:
                roi_line = int(elements[0].replace("\n", ""))
                roi_opacity = int(elements[1].replace("\n", ""))
                iso_line = int(elements[2].replace("\n", ""))
                iso_opacity = int(elements[3].replace("\n", ""))
                line_width = float(elements[4].replace("\n", ""))
            else:  # if file is empty for some reason, use the default measures below
                roi_line = 1
                roi_opacity = 10
                iso_line = 2
                iso_opacity = 5
                line_width = 2.0
            stream.close()
        # initialise the UI
        self.window = window
        self.setup_ui(self, roi_line, roi_opacity, iso_line, iso_opacity, line_width)
        # this data is used to create the tree view of functionalities on the left of the window
        # each entrie will be used as a button to change the view on the right accordingly
        data = [
            {"level": 0, "dbID": 442, "parent_ID": 6, "short_name": "User Options"},
            {
                "level": 1,
                "dbID": 522,
                "parent_ID": 442,
                "short_name": "Image Windowing",
            },
            {
                "level": 1,
                "dbID": 556,
                "parent_ID": 442,
                "short_name": "Standard Organ Names",
            },
            {
                "level": 1,
                "dbID": 527,
                "parent_ID": 442,
                "short_name": "Standard Volume Names",
            },
            # {'level': 1, 'dbID': 528, 'parent_ID': 442, 'short_name': 'Create ROI from Isodose'}, # extra option not fully supported
            {
                "level": 1,
                "dbID": 520,
                "parent_ID": 442,
                "short_name": "Patient ID - Hash ID",
            },
            {
                "level": 1,
                "dbID": 523,
                "parent_ID": 442,
                "short_name": "Line & Fill configuration",
            },
        ]
        # create a model for the tree view of options and attach the data
        self.model = QtGui.QStandardItemModel()
        self.treeList.setModel(self.model)
        self.importData(data)
        self.treeList.expandAll()
        # fill the corresponding tables with the corresponding data from the csv files
        self.fillTables()
        self.treeList.setEditTriggers(
            QtWidgets.QTreeView.NoEditTriggers
        )  # make the tree entries not editable
        # Functionalities of the Apply and Cancel button
        self.cancel_button.clicked.connect(
            self.close
        )  # Close the window by discarding all changes
        self.apply_button.clicked.connect(self.accepting)
        # Connecting the functionalities of the view dependant buttons
        self.add_new_window.clicked.connect(self.new_windowing)
        self.add_standard_organ_name.clicked.connect(self.new_organ)
        self.add_standard_volume_name.clicked.connect(self.new_volume)
        # self.add_new_roi.clicked.connect(self.new_isodose) # extra functionality
        self.import_organ_csv.clicked.connect(self.import_organs)

        # adding the right click menus for each table
        self.table_view.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(
            self.on_customContextMenuRequested_Window
        )
        self.table_organ.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.table_organ.customContextMenuRequested.connect(
            self.on_customContextMenuRequested_Organ
        )
        self.table_volume.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.table_volume.customContextMenuRequested.connect(
            self.on_customContextMenuRequested_Volume
        )
        # self.table_roi.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        # self.table_roi.customContextMenuRequested.connect(self.on_customContextMenuRequested_Roi)
        # making the URL column a double clicked link
        self.table_organ.itemDoubleClicked.connect(self.open_link)

    # function to open the corresponding URL in a new browser
    def open_link(self, item):
        if item.column() == 3 and item.text() != "":
            # checking if the url has http entered or not
            if "http://" in item.text():
                webbrowser.open_new(item.text())
            else:
                webbrowser.open_new("http://" + item.text())

    ######################################################################################################
    #                                                                                                    #
    #   The right click menus for each table (First one is explained and the same logic applies for all  #
    #                                                                                                    #
    ######################################################################################################
    # windowing
    @QtCore.pyqtSlot(QtCore.QPoint)
    def on_customContextMenuRequested_Window(self, pos):
        # gets the position of the right click for the windowing table
        it = self.table_view.itemAt(pos)
        if it is None:
            return
        c = it.row()
        item_range = QtWidgets.QTableWidgetSelectionRange(
            c, 0, c, self.table_view.columnCount() - 1
        )
        # selects the row
        self.table_view.setRangeSelected(item_range, True)
        # creates the menu
        menu = QtWidgets.QMenu()
        modify_row_action = menu.addAction("Modify")
        menu.addSeparator()
        delete_row_action = menu.addAction("Delete")
        action = menu.exec_(self.table_view.viewport().mapToGlobal(pos))
        if action == delete_row_action:
            self.table_view.removeRow(c)
        if action == modify_row_action:
            # open an input dialog as a pop up with the current values to be modified
            dialog = Dialog_Windowing(
                self.table_view.item(c, 0).text(),
                self.table_view.item(c, 1).text(),
                self.table_view.item(c, 2).text(),
                self.table_view.item(c, 3).text(),
            )
            # If Okay is pressed then display the new entries in the table
            # They will only be saved if Apply is pressed before exiting Add-On Options
            if dialog.exec():
                new_data = dialog.getInputs()
                self.table_view.setItem(c, 0, QTableWidgetItem(new_data[0]))
                self.table_view.setItem(c, 1, QTableWidgetItem(new_data[1]))
                self.table_view.setItem(c, 2, QTableWidgetItem(new_data[2]))
                self.table_view.setItem(c, 3, QTableWidgetItem(new_data[3]))

    # standard organ name table
    @QtCore.pyqtSlot(QtCore.QPoint)
    def on_customContextMenuRequested_Organ(self, pos):
        it = self.table_organ.itemAt(pos)
        if it is None:
            return
        c = it.row()
        item_range = QtWidgets.QTableWidgetSelectionRange(
            c, 0, c, self.table_organ.columnCount() - 1
        )
        self.table_organ.setRangeSelected(item_range, True)

        menu = QtWidgets.QMenu()
        modify_row_action = menu.addAction("Modify")
        menu.addSeparator()
        delete_row_action = menu.addAction("Delete")
        action = menu.exec_(self.table_organ.viewport().mapToGlobal(pos))
        if action == delete_row_action:
            self.table_organ.removeRow(c)
        if action == modify_row_action:
            dialog = Dialog_Organ(
                self.table_organ.item(c, 0).text(),
                self.table_organ.item(c, 1).text(),
                self.table_organ.item(c, 2).text(),
                self.table_organ.item(c, 3).text(),
            )
            if dialog.exec():
                new_data = dialog.getInputs()
                self.table_organ.setItem(c, 0, QTableWidgetItem(new_data[0]))
                self.table_organ.setItem(c, 1, QTableWidgetItem(new_data[1]))
                self.table_organ.setItem(c, 2, QTableWidgetItem(new_data[2]))
                self.table_organ.setItem(c, 3, QTableWidgetItem(new_data[3]))

    # standard volume table
    @QtCore.pyqtSlot(QtCore.QPoint)
    def on_customContextMenuRequested_Volume(self, pos):
        it = self.table_volume.itemAt(pos)
        if it is None:
            return
        c = it.row()
        item_range = QtWidgets.QTableWidgetSelectionRange(
            c, 0, c, self.table_volume.columnCount() - 1
        )
        self.table_volume.setRangeSelected(item_range, True)

        menu = QtWidgets.QMenu()
        modify_row_action = menu.addAction("Modify")
        menu.addSeparator()
        delete_row_action = menu.addAction("Delete")
        action = menu.exec_(self.table_volume.viewport().mapToGlobal(pos))
        if action == delete_row_action:
            self.table_volume.removeRow(c)
        if action == modify_row_action:
            dialog = Dialog_Volume(
                self.table_volume.item(c, 0).text(), self.table_volume.item(c, 1).text()
            )
            if dialog.exec():
                new_data = dialog.getInputs()
                self.table_volume.setItem(c, 0, QTableWidgetItem(new_data[0]))
                self.table_volume.setItem(c, 1, QTableWidgetItem(new_data[1]))

    # This option is extra and not fully supported yet, TO DO in the future
    # # ROI from IsoDoses
    # @QtCore.pyqtSlot(QtCore.QPoint)
    # def on_customContextMenuRequested_Roi(self, pos):
    #     it = self.table_roi.itemAt(pos)
    #     if it is None:
    #         return
    #     c = it.row()
    #     item_range = QtWidgets.QTableWidgetSelectionRange(
    #         c, 0, c, self.table_roi.columnCount() - 1)
    #     self.table_roi.setRangeSelected(item_range, True)
    #
    #     menu = QtWidgets.QMenu()
    #     modify_row_action = menu.addAction("Modify")
    #     menu.addSeparator()
    #     delete_row_action = menu.addAction("Delete")
    #     action = menu.exec_(self.table_roi.viewport().mapToGlobal(pos))
    #     if action == delete_row_action:
    #         self.table_roi.removeRow(c)
    #     if action == modify_row_action:
    #         dialog = Dialog_Dose(self.table_roi.item(
    #             c, 0).text(), self.table_roi.item(c, 2).text())
    #         if dialog.exec():
    #             new_data = dialog.getInputs()
    #             self.table_roi.setItem(c, 0, QTableWidgetItem(new_data[0]))
    #             self.table_roi.setItem(c, 1, QTableWidgetItem(new_data[1]))
    #             self.table_roi.setItem(c, 2, QTableWidgetItem(new_data[2]))

    ######################################################################################################
    #                                                                                                    #
    #  This function creates the tree view on the left according to the given data                       #
    #                                                                                                    #
    ######################################################################################################

    def importData(self, data, root=None):
        self.model.setRowCount(0)
        if root is None:
            root = self.model.invisibleRootItem()
        seen = {}
        values = deque(data)
        while values:
            value = values.popleft()
            if value["level"] == 0:
                parent = root
            else:
                pid = value["parent_ID"]
                if pid not in seen:
                    values.append(value)
                    continue
                parent = seen[pid]
            dbid = value["dbID"]
            parent.appendRow([QtGui.QStandardItem(value["short_name"])])
            seen[dbid] = parent.child(parent.rowCount() - 1)

    ######################################################################################################
    #                                                                                                    #
    # If APPLY is clicked, save the contents of each option and table into their corresponding files     #
    #                                                                                                    #
    ######################################################################################################

    def accepting(self):
        # starting save
        # Saving the Windowing options
        with open("src/data/csv/imageWindowing.csv", "w", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["Organ", "Scan", "Window", "Level"])
            for row in range(self.table_view.rowCount()):
                rowdata = []
                for column in range(self.table_view.columnCount()):
                    item = self.table_view.item(row, column)
                    if item is not None:
                        rowdata.append(item.text())
                    else:
                        rowdata.append("")
                writer.writerow(rowdata)
        # saving the Standard Organ names
        with open("src/data/csv/organName.csv", "w", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["Standard Name", "FMA ID", "Organ", "Url"])
            for row in range(self.table_organ.rowCount()):
                rowdata = []
                for column in range(self.table_organ.columnCount()):
                    item = self.table_organ.item(row, column)
                    if item is not None:
                        rowdata.append(item.text())
                    else:
                        rowdata.append("")
                writer.writerow(rowdata)
        # Saving the Standard Volume Names
        with open("src/data/csv/volumeName.csv", "w", newline="") as stream:
            writer = csv.writer(stream)
            for row in range(self.table_volume.rowCount()):
                rowdata = []
                for column in range(self.table_volume.columnCount()):
                    item = self.table_volume.item(row, column)
                    if item is not None:
                        rowdata.append(item.text())
                    else:
                        rowdata.append("")
                writer.writerow(rowdata)

        # saves the new ROI from Isodoses, To Do in the future
        # with open('src/data/csv/isodoseRoi.csv', 'w') as stream:
        #     writer = csv.writer(stream)
        #     for row in range(self.table_roi.rowCount()):
        #         rowdata = []
        #         for column in range(self.table_roi.columnCount()):
        #             item = self.table_roi.item(row, column)
        #             if item is not None:
        #                 rowdata.append(item.text())
        #             else:
        #                 rowdata.append('')
        #         writer.writerow(rowdata)

        # save configuration file
        with open("src/data/line&fill_configuration", "w") as stream:
            stream.write(str(self.line_style_ROI.currentIndex()))
            stream.write("\n")
            stream.write(str(self.opacity_ROI.value()))
            stream.write("\n")
            stream.write(str(self.line_style_ISO.currentIndex()))
            stream.write("\n")
            stream.write(str(self.opacity_ISO.value()))
            stream.write("\n")
            stream.write(str(self.line_width.currentText()))
            stream.write("\n")
            stream.close()
        # Close the Add-On Options Window after saving

        if hasattr(self.window, 'structures_tab'):
            self.window.structures_tab.init_standard_names()
            self.window.structures_tab.update_content()

        self.close()

    ###################################################################################################################
    #                                                                                                                 #
    # This function populates the tables with the last known entries based on the corresponding files                 #
    #                                                                                                                 #
    ###################################################################################################################

    def fillTables(self):
        # Fill the Windowing table
        with open("src/data/csv/imageWindowing.csv", "r") as fileInput:
            next(fileInput)
            i = 0
            for row in fileInput:
                items = [
                    QTableWidgetItem(str(item.replace("\n", "")))
                    for item in row.split(",")
                ]
                self.table_view.insertRow(i)
                self.table_view.setItem(i, 0, items[0])
                self.table_view.setItem(i, 1, items[1])
                self.table_view.setItem(i, 2, items[2])
                self.table_view.setItem(i, 3, items[3])
                i += 1

        # organ names table
        with open("src/data/csv/organName.csv", "r") as fileInput:
            next(fileInput)
            i = 0
            for row in fileInput:
                items = [
                    QTableWidgetItem(str(item.replace("\n", "")))
                    for item in row.split(",")
                ]
                self.table_organ.insertRow(i)
                self.table_organ.setItem(i, 0, items[0])
                self.table_organ.setItem(i, 1, items[1])
                self.table_organ.setItem(i, 2, items[2])
                if len(items) > 3:
                    self.table_organ.setItem(i, 3, items[3])
                i += 1

        # volume name table
        with open("src/data/csv/volumeName.csv", "r") as fileInput:
            i = 0
            for row in fileInput:
                items = [
                    QTableWidgetItem(str(item.replace("\n", "")))
                    for item in row.split(",")
                ]
                self.table_volume.insertRow(i)
                self.table_volume.setItem(i, 0, items[0])
                self.table_volume.setItem(i, 1, items[1])
                i += 1

        # roi isodose table, TO DO in the future

        # with open('src/data/csv/isodoseRoi.csv', "r") as fileInput:
        #     i = 0;
        #     for row in fileInput:
        #         items = [
        #             QTableWidgetItem(str(item.replace('\n', '')))
        #             for item in row.split(',')
        #         ]
        #         self.table_roi.insertRow(i)
        #         self.table_roi.setItem(i, 0, items[0])
        #         self.table_roi.setItem(i, 1, items[1])
        #         if len(items) > 2:
        #             self.table_roi.setItem(i, 2, items[2])
        #         i += 1

        # patient hash ID table, which is just for displaying all the patients anonymized byt the software since intallation
        with open("src/data/csv/patientHash.csv", "r") as fileInput:
            next(fileInput)
            i = 0
            for row in fileInput:
                items = [
                    QTableWidgetItem(str(item.replace("\n", "")))
                    for item in row.split(",")
                ]
                if len(items) >= 2:
                    self.table_Ids.insertRow(i)
                    self.table_Ids.setItem(i, 0, items[0])
                    self.table_Ids.setItem(i, 1, items[1])
                i += 1

    ###################################################################################################################
    #                                                                                                                 #
    # The following function show a pop up window to add a new entry in the corresponding table                       #
    #                                                                                                                 #
    ###################################################################################################################
    # This function shows an Input dialog pop up to insert a new windowing entry
    def new_windowing(self):
        dialog = Dialog_Windowing("", "", "", "")
        c = self.table_view.rowCount()
        if dialog.exec():
            new_data = dialog.getInputs()
            self.table_view.insertRow(c)
            self.table_view.setItem(c, 0, QTableWidgetItem(new_data[0]))
            self.table_view.setItem(c, 1, QTableWidgetItem(new_data[1]))
            self.table_view.setItem(c, 2, QTableWidgetItem(new_data[2]))
            self.table_view.setItem(c, 3, QTableWidgetItem(new_data[3]))

    # This function shows an input dialog for a new standard organ name
    def new_organ(self):
        dialog = Dialog_Organ("", "", "", "")
        c = self.table_organ.rowCount()
        if dialog.exec():
            new_data = dialog.getInputs()
            self.table_organ.insertRow(c)
            self.table_organ.setItem(c, 0, QTableWidgetItem(new_data[0]))
            self.table_organ.setItem(c, 1, QTableWidgetItem(new_data[1]))
            self.table_organ.setItem(c, 2, QTableWidgetItem(new_data[2]))
            self.table_organ.setItem(c, 3, QTableWidgetItem(new_data[3]))

    # This function enables the entry of a new volume name
    def new_volume(self):
        dialog = Dialog_Volume("", "")
        c = self.table_volume.rowCount()
        if dialog.exec():
            new_data = dialog.getInputs()
            self.table_volume.insertRow(c)
            self.table_volume.setItem(c, 0, QTableWidgetItem(new_data[0]))
            self.table_volume.setItem(c, 1, QTableWidgetItem(new_data[1]))

    # def new_isodose(self):
    #     dialog = Dialog_Dose('')
    #     c = self.table_roi.rowCount()
    #     if dialog.exec():
    #         new_data = dialog.getInputs()
    #         self.table_roi.insertRow(c)
    #         self.table_roi.setItem(c, 0, QTableWidgetItem(new_data[0]))
    #         self.table_roi.setItem(c, 1, QTableWidgetItem(new_data[1]))

    ###################################################################################################################
    #                                                                                                                 #
    # the following function lets you import a csv of organ names into the table if the csv is in the given format    #
    #                                                                                                                 #
    ###################################################################################################################

    def import_organs(self):
        self.check_change = False
        path = QFileDialog.getOpenFileName(
            self, "Open Data File", "", "CSV data files (*.csv)"
        )[0]

        if path != "":
            with open(path, newline="") as stream:
                next(stream)
                for rowdata in csv.reader(stream):
                    if len(rowdata) != 3 or len(rowdata) != 4:
                        buttonReply = QMessageBox.warning(
                            self,
                            "Error Message",
                            "Import a csv with 3 or 4 columns and the data with the displayed order!",
                            QMessageBox.Ok,
                        )
                        if buttonReply == QMessageBox.Ok:
                            pass
                    else:
                        row = self.table_organ.rowCount()
                        self.table_organ.insertRow(row)
                        self.table_organ.setColumnCount(len(rowdata))
                        for column, data in enumerate(rowdata):
                            item = QTableWidgetItem(data)
                            self.table_organ.setItem(row, column, item)

        self.check_change = True


###################################################################################################################
#                                                                                                                 #
# The class that will be called by the main page to access the Add-On Options controller                          #
#                                                                                                                 #
###################################################################################################################


class AddOptions:
    def __init__(self, window):
        self.window = window

    def show_add_on_options(self):
        self.options_window = AddOnOptions(self.window)
        self.options_window.show()
