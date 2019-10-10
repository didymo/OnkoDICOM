import csv
import sys
from collections import deque

from PyQt5.QtWidgets import QFileDialog

from src.View.PluginManager import *
from src.data.csv import *
from src.View.InputDialogs import *

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
        self.add_new_window.clicked.connect(self.new_windowing)
        self.add_standard_organ_name.clicked.connect(self.new_organ)
        self.add_standard_volume_name.clicked.connect(self.new_volume)
        self.add_new_roi.clicked.connect(self.new_isodose)
        self.import_organ_csv.clicked.connect(self.import_organs)

        #adding the menus
        self.table_view.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(self.on_customContextMenuRequested_Window)
        self.table_organ.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.table_organ.customContextMenuRequested.connect(self.on_customContextMenuRequested_Organ)
        self.table_volume.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.table_volume.customContextMenuRequested.connect(self.on_customContextMenuRequested_Volume)
        self.table_roi.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.table_roi.customContextMenuRequested.connect(self.on_customContextMenuRequested_Roi)


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
            dialog = Dialog_Windowing(self.table_view.item(c,0).text(),self.table_view.item(c,1).text(),self.table_view.item(c,2).text(),self.table_view.item(c,3).text())
            if dialog.exec():
                new_data = dialog.getInputs()
                self.table_view.setItem(c,0, QTableWidgetItem(new_data[0]))
                self.table_view.setItem(c, 1, QTableWidgetItem(new_data[1]))
                self.table_view.setItem(c, 2, QTableWidgetItem(new_data[2]))
                self.table_view.setItem(c, 3, QTableWidgetItem(new_data[3]))

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
            dialog = Dialog_Organ(self.table_organ.item(c, 0).text(), self.table_organ.item(c, 1).text(),
                                      self.table_organ.item(c, 2).text())
            if dialog.exec():
                new_data = dialog.getInputs()
                self.table_organ.setItem(c, 0, QTableWidgetItem(new_data[0]))
                self.table_organ.setItem(c, 1, QTableWidgetItem(new_data[1]))
                self.table_organ.setItem(c, 2, QTableWidgetItem(new_data[2]))

    #volume
    @QtCore.pyqtSlot(QtCore.QPoint)
    def on_customContextMenuRequested_Volume(self, pos):
        it = self.table_volume.itemAt(pos)
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
            dialog = Dialog_Volume(self.table_volume.item(c, 0).text(), self.table_volume.item(c, 1).text())
            if dialog.exec():
                new_data = dialog.getInputs()
                self.table_volume.setItem(c, 0, QTableWidgetItem(new_data[0]))
                self.table_volume.setItem(c, 1, QTableWidgetItem(new_data[1]))

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
            dialog = Dialog_Dose(self.table_roi.item(c, 0).text(), self.table_roi.item(c,2).text())
            if dialog.exec():
                new_data = dialog.getInputs()
                self.table_roi.setItem(c, 0, QTableWidgetItem(new_data[0]))
                self.table_roi.setItem(c, 1, QTableWidgetItem(new_data[1]))
                self.table_roi.setItem(c, 2, QTableWidgetItem(new_data[2]))


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
        #starting save
        with open('src/data/csv/imageWindowing.csv', 'w') as stream:
            writer = csv.writer(stream)
            writer.writerow(["Organ","Scan","Window","Level"])
            for row in range(self.table_view.rowCount()):
                rowdata = []
                for column in range(self.table_view.columnCount()):
                    item = self.table_view.item(row, column)
                    if item is not None:
                        rowdata.append(item.text())
                    else:
                        rowdata.append('')
                writer.writerow(rowdata)

        with open('src/data/csv/organName.csv', 'w') as stream:
            writer = csv.writer(stream)
            writer.writerow(["Standard Name","FMA ID","Organ"])
            for row in range(self.table_organ.rowCount()):
                rowdata = []
                for column in range(self.table_organ.columnCount()):
                    item = self.table_organ.item(row, column)
                    if item is not None:
                        rowdata.append(item.text())
                    else:
                        rowdata.append('')
                writer.writerow(rowdata)

        with open('src/data/csv/volumeName.csv', 'w') as stream:
            writer = csv.writer(stream)
            for row in range(self.table_volume.rowCount()):
                rowdata = []
                for column in range(self.table_volume.columnCount()):
                    item = self.table_volume.item(row, column)
                    if item is not None:
                        rowdata.append(item.text())
                    else:
                        rowdata.append('')
                writer.writerow(rowdata)

        with open('src/data/csv/isodoseRoi.csv', 'w') as stream:
            writer = csv.writer(stream)
            for row in range(self.table_roi.rowCount()):
                rowdata = []
                for column in range(self.table_roi.columnCount()):
                    item = self.table_roi.item(row, column)
                    if item is not None:
                        rowdata.append(item.text())
                    else:
                        rowdata.append('')
                writer.writerow(rowdata)

        self.close()

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
            self.note.setVisible(False)
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
            self.note.setVisible(False)
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
            self.note.setVisible(False)
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
            self.note.setVisible(False)
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
            self.note.setVisible(True)
        elif type == "User Plugins":
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
            self.note.setVisible(False)

    def fillTables(self):
        with open('src/data/csv/imageWindowing.csv', "r") as fileInput:
            next(fileInput)
            i=0;
            for row in fileInput:
                items = [
                    QTableWidgetItem(str(item.replace('\n', '')))
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
            next(fileInput)
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
                if len(items) > 2 :
                    self.table_roi.setItem(i, 2, items[2])
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

    def new_windowing(self):
        dialog = Dialog_Windowing('','','','')
        c = self.table_view.rowCount()
        if dialog.exec():
            new_data = dialog.getInputs()
            self.table_view.insertRow(c)
            self.table_view.setItem(c, 0, QTableWidgetItem(new_data[0]))
            self.table_view.setItem(c, 1, QTableWidgetItem(new_data[1]))
            self.table_view.setItem(c, 2, QTableWidgetItem(new_data[2]))
            self.table_view.setItem(c, 3, QTableWidgetItem(new_data[3]))

    def new_organ(self):
        dialog = Dialog_Organ('','','')
        c = self.table_organ.rowCount()
        if dialog.exec():
            new_data = dialog.getInputs()
            self.table_organ.insertRow(c)
            self.table_organ.setItem(c, 0, QTableWidgetItem(new_data[0]))
            self.table_organ.setItem(c, 1, QTableWidgetItem(new_data[1]))
            self.table_organ.setItem(c, 2, QTableWidgetItem(new_data[2]))

    def new_volume(self):
        dialog = Dialog_Volume('','')
        c = self.table_volume.rowCount()
        if dialog.exec():
            new_data = dialog.getInputs()
            self.table_volume.insertRow(c)
            self.table_volume.setItem(c, 0, QTableWidgetItem(new_data[0]))
            self.table_volume.setItem(c, 1, QTableWidgetItem(new_data[1]))

    def new_isodose(self):
        dialog = Dialog_Dose('')
        c = self.table_roi.rowCount()
        if dialog.exec():
            new_data = dialog.getInputs()
            self.table_roi.insertRow(c)
            self.table_roi.setItem(c, 0, QTableWidgetItem(new_data[0]))
            self.table_roi.setItem(c, 1, QTableWidgetItem(new_data[1]))


    def import_organs(self):
        self.check_change = False
        path = QFileDialog.getOpenFileName(
            self, "Open Data File", "", "CSV data files (*.csv)")[0]

        if path != '':
            with open(path, newline='') as stream:
                next(stream)
                for rowdata in csv.reader(stream):
                    if len(rowdata)!= 3:
                        buttonReply = QMessageBox.warning(self, "Error Message",
                                                          "Import a csv with 3 columns and the data with the displayed order!", QMessageBox.Ok)
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


class PManager:

    def __init__(self):
        pass

    def show_plugin_manager(self):
        self.plugin_window = PluginManager()
        self.plugin_window.show()
