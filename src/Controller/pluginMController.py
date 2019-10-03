import csv
import sys
from collections import deque

from PyQt5.QtCore import Qt, QModelIndex
from PyQt5.QtGui import QStandardItem, QDropEvent
from PyQt5.QtWidgets import QTableWidgetItem, QMessageBox, QAbstractItemView, QTableView, QTableWidget

from src.View.PluginManager import *
from src.data.csv import *


class PluginManager(QtWidgets.QMainWindow, Ui_PluginManager):

    def __init__(self):
        super(PluginManager, self).__init__()
        self.setupUi(self)
        data = [
            {'level': 0, 'dbID': 442, 'parent_ID': 6, 'short_name': 'User Plugins'},
            {'level': 1, 'dbID': 522, 'parent_ID': 442, 'short_name': 'Image Windowing'},
            {'level': 1, 'dbID': 556, 'parent_ID': 442, 'short_name': 'Standard Organ Names'},
            {'level': 1, 'dbID': 527, 'parent_ID': 442, 'short_name': 'Standard Volume Names'},
            {'level': 1, 'dbID': 528, 'parent_ID': 442, 'short_name': 'Create ROI from Isodose'},
            {'level': 1, 'dbID': 520, 'parent_ID': 442, 'short_name': 'Patient ID - Hash ID'}
        ]
        self.model = QtGui.QStandardItemModel()
        self.treeList.setModel(self.model)
        self.importData(data)
        self.treeList.expandAll()
        self.fillTables()
        self.treeList.setEditTriggers(QtWidgets.QTreeView.NoEditTriggers)
        self.cancel_button.clicked.connect(self.close)
        self.apply_button.clicked.connect(self.applyChanges)
        self.treeList.clicked.connect(self.display)
        #adding the menus
        self.table_view.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self.on_customContextMenuRequested_Window)
        self.table_organ.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.table_organ.customContextMenuRequested.connect(self.on_customContextMenuRequested_Organ)
        self.table_volume.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.table_volume.customContextMenuRequested.connect(self.on_customContextMenuRequested_Volume)
        self.table_roi.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.table_roi.customContextMenuRequested.connect(self.on_customContextMenuRequested_Roi)
        self.table_Ids.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.table_Ids.customContextMenuRequested.connect(self.on_customContextMenuRequested_Ids)


    #windowing
    @QtCore.pyqtSlot(QtCore.QPoint)
    def on_customContextMenuRequested_Window(self, pos):
        it = self.table_view.itemAt(pos)
        if it is None: return
        c = it.row()
        item_range = QtWidgets.QTableWidgetSelectionRange(c,0,c,self.table_view.columnCount()-1)
        self.table_view.setRangeSelected(item_range, True)

        menu = QtWidgets.QMenu()
        modify_row_action = menu.addAction("Modify")
        menu.addSeparator()
        delete_row_action = menu.addAction("Delete")
        action = menu.exec_(self.table_view.viewport().mapToGlobal(pos))
        if action == delete_row_action:
            self.table_view.removeRow(c)
        if action == modify_row_action:
            pass
    #organ
    @QtCore.pyqtSlot(QtCore.QPoint)
    def on_customContextMenuRequested_Organ(self, pos):
        it = self.table_organ.itemAt(pos)
        if it is None: return
        c = it.row()
        item_range = QtWidgets.QTableWidgetSelectionRange(c, 0, c, self.table_organ.columnCount() - 1)
        self.table_organ.setRangeSelected(item_range, True)

        menu = QtWidgets.QMenu()
        modify_row_action = menu.addAction("Modify")
        menu.addSeparator()
        delete_row_action = menu.addAction("Delete")
        action = menu.exec_(self.table_organ.viewport().mapToGlobal(pos))
        if action == delete_row_action:
            self.table_organ.removeRow(c)
        if action == modify_row_action:
            pass

    #volume
    @QtCore.pyqtSlot(QtCore.QPoint)
    def on_customContextMenuRequested_Volume(self, pos):
        it = self.table_volume.itemAt(pos)
        print(pos)
        if it is None: return
        c = it.row()
        item_range = QtWidgets.QTableWidgetSelectionRange(c, 0, c, self.table_volume.columnCount() - 1)
        self.table_volume.setRangeSelected(item_range, True)

        menu = QtWidgets.QMenu()
        modify_row_action = menu.addAction("Modify")
        menu.addSeparator()
        delete_row_action = menu.addAction("Delete")
        action = menu.exec_(self.table_volume.viewport().mapToGlobal(pos))
        if action == delete_row_action:
            self.table_volume.removeRow(c)
        if action == modify_row_action:
            pass

    #ROI
    @QtCore.pyqtSlot(QtCore.QPoint)
    def on_customContextMenuRequested_Roi(self, pos):
        it = self.table_roi.itemAt(pos)
        if it is None: return
        c = it.row()
        item_range = QtWidgets.QTableWidgetSelectionRange(c, 0, c, self.table_roi.columnCount() - 1)
        self.table_roi.setRangeSelected(item_range, True)

        menu = QtWidgets.QMenu()
        modify_row_action = menu.addAction("Modify")
        menu.addSeparator()
        delete_row_action = menu.addAction("Delete")
        action = menu.exec_(self.table_roi.viewport().mapToGlobal(pos))
        if action == delete_row_action:
            self.table_roi.removeRow(c)
        if action == modify_row_action:
            pass

    @QtCore.pyqtSlot(QtCore.QPoint)
    def on_customContextMenuRequested_Ids(self, pos):
        it = self.table_Ids.itemAt(pos)
        if it is None: return
        c = it.row()
        item_range = QtWidgets.QTableWidgetSelectionRange(c, 0, c, self.table_Ids.columnCount() - 1)
        self.table_Ids.setRangeSelected(item_range, True)

        menu = QtWidgets.QMenu()
        modify_row_action = menu.addAction("Modify")
        menu.addSeparator()
        delete_row_action = menu.addAction("Delete")
        action = menu.exec_(self.table_Ids.viewport().mapToGlobal(pos))
        if action == delete_row_action:
            self.table_Ids.removeRow(c)
        if action == modify_row_action:
            pass


    def importData(self, data, root=None):
        self.model.setRowCount(0)
        if root is None:
            root = self.model.invisibleRootItem()
        seen = {}
        values = deque(data)
        while values:
            value = values.popleft()
            if value['level'] == 0:
                parent = root
            else:
                pid = value['parent_ID']
                if pid not in seen:
                    values.append(value)
                    continue
                parent = seen[pid]
            dbid = value['dbID']
            parent.appendRow([
                QtGui.QStandardItem(value['short_name'])
            ])
            seen[dbid] = parent.child(parent.rowCount() - 1)

    def applyChanges(self):
        pass

    def display(self, index):
        item = self.treeList.selectedIndexes()[0]
        self.optionTitle.setText(item.model().itemFromIndex(index).text())
        self.changeDislpay(item.model().itemFromIndex(index).text())

    def changeDislpay(self, type):
        # create a file that keeps a record of the tables and call to populate the given table
        if type == "Image Windowing":
            self.table_modules.setVisible(False)
            self.table_view.setVisible(True)
            self.table_organ.setVisible(False)
            self.table_volume.setVisible(False)
            self.table_roi.setVisible(False)
            self.table_Ids.setVisible(False)
            self.add_new_window.setVisible(True)
            self.add_new_roi.setVisible(False)
            self.add_standard_volume_name.setVisible(False)
            self.add_standard_organ_name.setVisible(False)
            self.import_organ_csv.setVisible(False)
        elif type == "Standard Organ Names":
            self.table_modules.setVisible(False)
            self.table_view.setVisible(False)
            self.table_organ.setVisible(True)
            self.table_volume.setVisible(False)
            self.table_roi.setVisible(False)
            self.table_Ids.setVisible(False)
            self.add_new_window.setVisible(False)
            self.add_new_roi.setVisible(False)
            self.add_standard_volume_name.setVisible(False)
            self.add_standard_organ_name.setVisible(True)
            self.import_organ_csv.setVisible(True)
        elif type == "Standard Volume Names":
            self.table_modules.setVisible(False)
            self.table_view.setVisible(False)
            self.table_organ.setVisible(False)
            self.table_volume.setVisible(True)
            self.table_roi.setVisible(False)
            self.table_Ids.setVisible(False)
            self.add_new_window.setVisible(False)
            self.add_new_roi.setVisible(False)
            self.add_standard_volume_name.setVisible(True)
            self.add_standard_organ_name.setVisible(False)
            self.import_organ_csv.setVisible(False)
        elif type == "Create ROI from Isodose":
            self.table_modules.setVisible(False)
            self.table_view.setVisible(False)
            self.table_organ.setVisible(False)
            self.table_volume.setVisible(False)
            self.table_roi.setVisible(True)
            self.table_Ids.setVisible(False)
            self.add_new_window.setVisible(False)
            self.add_new_roi.setVisible(True)
            self.add_standard_volume_name.setVisible(False)
            self.add_standard_organ_name.setVisible(False)
            self.import_organ_csv.setVisible(False)
        elif type == "Patient ID - Hash ID":
            self.table_modules.setVisible(False)
            self.table_view.setVisible(False)
            self.table_organ.setVisible(False)
            self.table_volume.setVisible(False)
            self.table_roi.setVisible(False)
            self.table_Ids.setVisible(True)
            self.add_new_window.setVisible(False)
            self.add_new_roi.setVisible(False)
            self.add_standard_volume_name.setVisible(False)
            self.add_standard_organ_name.setVisible(False)
            self.import_organ_csv.setVisible(False)
        elif type  == "User Plugins":
            self.add_new_window.setVisible(False)
            self.add_new_roi.setVisible(False)
            self.add_standard_volume_name.setVisible(False)
            self.add_standard_organ_name.setVisible(False)
            self.import_organ_csv.setVisible(False)
            self.table_modules.setVisible(True)
            self.table_view.setVisible(False)
            self.table_organ.setVisible(False)
            self.table_volume.setVisible(False)
            self.table_roi.setVisible(False)
            self.table_Ids.setVisible(False)

    def fillTables(self):
        with open('src/data/csv/imageWindowing.csv', "r") as fileInput:
            next(fileInput)
            i=0;
            for row in fileInput:
                items = [
                    QTableWidgetItem(str(item))
                    for item in row.split(',')
                ]

                self.table_view.insertRow(i)
                self.table_view.setItem(i, 0, items[0])
                self.table_view.setItem(i, 1, items[1])
                self.table_view.setItem(i, 2, items[2])
                self.table_view.setItem(i, 3, items[3])
                i+=1

        #organ names
        with open('src/data/csv/organName.csv', "r") as fileInput:
            i = 0;
            for row in fileInput:
                items = [
                    QTableWidgetItem(str(item.replace('\n', '')))
                    for item in row.split(',')
                ]

                self.table_organ.insertRow(i)
                self.table_organ.setItem(i, 0, items[0])
                self.table_organ.setItem(i, 1, items[1])
                self.table_organ.setItem(i, 2, items[2])
                i += 1

        #volume name
        with open('src/data/csv/volumeName.csv', "r") as fileInput:
            i = 0;
            for row in fileInput:
                items = [
                    QTableWidgetItem(str(item.replace('\n', '')))
                    for item in row.split(',')
                ]
                self.table_volume.insertRow(i)
                self.table_volume.setItem(i, 0, items[0])
                self.table_volume.setItem(i, 1, items[1])
                i += 1

        #roi isodose
        with open('src/data/csv/isodoseRoi.csv', "r") as fileInput:
            i = 0;
            for row in fileInput:
                items = [
                    QTableWidgetItem(str(item.replace('\n', '')))
                    for item in row.split(',')
                ]

                self.table_roi.insertRow(i)
                self.table_roi.setItem(i, 0, items[0])
                self.table_roi.setItem(i, 1, items[1])
                i += 1
        #patient hash
        with open('src/data/csv/patientHash.csv', "r") as fileInput:
            i = 0;
            for row in fileInput:
                items = [
                    QTableWidgetItem(str(item.replace('\n', '')))
                    for item in row.split(',')
                ]

                self.table_Ids.insertRow(i)
                self.table_Ids.setItem(i, 0, items[0])
                self.table_Ids.setItem(i, 1, items[1])
                i += 1



class PManager:

    def __init__(self):
        pass

    def show_plugin_manager(self):
        self.plugin_window = PluginManager()
        self.plugin_window.show()
