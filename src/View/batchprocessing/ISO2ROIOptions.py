import csv
from PySide6 import QtCore, QtGui, QtWidgets
from src.Controller.PathHandler import data_path, resource_path
from src.View.InputDialogs import Dialog_Dose
from src.View.StyleSheetReader import StyleSheetReader


class ISO2ROIOptions(QtWidgets.QWidget):
    """
    ISO2ROI options for batch processing. Includes a table of isodose
    levels and the ability to add, modify, or remove levels.
    """

    def __init__(self):
        """
        Initialise the class
        """
        QtWidgets.QWidget.__init__(self)

        # Create the main layout
        self.main_layout = QtWidgets.QVBoxLayout()

        self.create_table_view()
        self.create_buttons()
        self.setLayout(self.main_layout)

    def create_buttons(self):
        """
        Create buttons to create and delete ROIs from isodose.
        """
        # Button layout
        self.button_layout = QtWidgets.QHBoxLayout()

        # Buttons
        self.add_new_roi = QtWidgets.QPushButton(self)
        self.delete_roi = QtWidgets.QPushButton(self)

        # Set cursor
        self.add_new_roi.setCursor(
            QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.delete_roi.setCursor(
            QtGui.QCursor(QtCore.Qt.PointingHandCursor))

        # Set button class
        self.add_new_roi.setProperty("QPushButtonClass",
                                            "success-button")
        self.delete_roi.setProperty("QPushButtonClass", "fail-button")

        # Set button stylesheet
        stylesheet: StyleSheetReader = StyleSheetReader()
        self.add_new_roi.setStyleSheet(stylesheet.get_stylesheet())
        self.delete_roi.setStyleSheet(stylesheet.get_stylesheet())

        # Set text
        _translate = QtCore.QCoreApplication.translate
        self.add_new_roi.setText(_translate("Add_On_Options",
                                                   "Add new Isodose"))
        self.delete_roi.setText(_translate("Add_On_Options",
                                                  "Remove Isodose"))

        # Add buttons to the layout
        self.button_layout.addWidget(self.delete_roi)
        self.button_layout.addWidget(self.add_new_roi)
        self.main_layout.addLayout(self.button_layout)

        # Connect button clicked events to functions
        self.add_new_roi.clicked.connect(self.new_isodose)
        self.delete_roi.clicked.connect(self.remove_isodose)

    def create_table_view(self):
        """
        Create a table to hold all the isodose levels for ISO2ROI.
        """
        # Create table
        self.table_roi = QtWidgets.QTableWidget(self)
        self.table_roi.setStyleSheet(
            "background-color: rgb(255, 255, 255);")
        self.table_roi.setColumnCount(4)
        self.table_roi.verticalHeader().hide()
        self.table_roi.setHorizontalHeaderLabels(
            [" Isodose Level ", " Unit ", " ROI Name ", " Notes "])

        self.table_roi.horizontalHeaderItem(0).setTextAlignment(
            QtCore.Qt.AlignLeft)
        self.table_roi.horizontalHeaderItem(1).setTextAlignment(
            QtCore.Qt.AlignLeft)
        self.table_roi.horizontalHeaderItem(2).setTextAlignment(
            QtCore.Qt.AlignLeft)
        self.table_roi.horizontalHeaderItem(3).setTextAlignment(
            QtCore.Qt.AlignLeft)

        roi_from_isodose_header = self.table_roi.horizontalHeader()
        roi_from_isodose_header.setSectionResizeMode(
            0, QtWidgets.QHeaderView.Stretch)
        roi_from_isodose_header.setSectionResizeMode(
            1, QtWidgets.QHeaderView.Stretch)
        roi_from_isodose_header.setSectionResizeMode(
            2, QtWidgets.QHeaderView.Stretch)
        roi_from_isodose_header.setSectionResizeMode(
            3, QtWidgets.QHeaderView.Stretch)

        # Removing the ability to edit tables with immediate click
        self.table_roi.setEditTriggers(
            QtWidgets.QTreeView.NoEditTriggers |
            QtWidgets.QTreeView.NoEditTriggers)

        # Add table to the main layout
        self.main_layout.addWidget(self.table_roi)

        # Add right click options
        self.table_roi.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.table_roi.customContextMenuRequested.connect(
            self.on_custom_context_menu_requested_roi)

        # Populate the table with data from batch_isodoseRoi.csv
        with open(data_path('batch_isodoseRoi.csv'), "r") as fileInput:
            # Clear table to prevent displaying data multiple times
            self.table_roi.setRowCount(0)

            # Loop through each row
            for i, row in enumerate(fileInput):
                items = [
                    QtWidgets.QTableWidgetItem(str(item.replace('\n', '')))
                    for item in row.split(',')
                ]

                # Add row to table
                self.table_roi.insertRow(i)
                self.table_roi.setItem(i, 0, items[0])
                self.table_roi.setItem(i, 1, items[1])
                self.table_roi.setItem(i, 2, items[2])
                if len(items) > 3:
                    self.table_roi.setItem(i, 3, items[3])

    @QtCore.Slot(QtCore.QPoint)
    def on_custom_context_menu_requested_roi(self, pos):
        """
        A slot that is called whenever a cell in the table is
        right-clicked. Allows the user to modify or remove the selected
        row.
        """
        it = self.table_roi.itemAt(pos)
        if it is None:
            return
        c = it.row()
        item_range = QtWidgets.QTableWidgetSelectionRange(
            c, 0, c, self.table_roi.columnCount() - 1)
        self.table_roi.setRangeSelected(item_range, True)

        # Add right click menu
        menu = QtWidgets.QMenu()
        modify_row_action = menu.addAction("Modify")
        menu.addSeparator()
        delete_row_action = menu.addAction("Delete")
        action = menu.exec(self.table_roi.viewport().mapToGlobal(pos))

        # Delete row
        if action == delete_row_action:
            self.table_roi.removeRow(c)

        # Insert row
        if action == modify_row_action:
            dialog = Dialog_Dose(self.table_roi.item(
                c, 0).text(), self.table_roi.item(c, 3).text())
            if dialog.exec():
                new_data = dialog.getInputs()
                self.table_roi.setItem(c, 0,
                                       QtWidgets.QTableWidgetItem(new_data[0]))
                self.table_roi.setItem(c, 1,
                                       QtWidgets.QTableWidgetItem(new_data[1]))
                self.table_roi.setItem(c, 2,
                                       QtWidgets.QTableWidgetItem(new_data[2]))
                self.table_roi.setItem(c, 3,
                                       QtWidgets.QTableWidgetItem(new_data[3]))

    def new_isodose(self):
        """
        Function to add a new isodose to the table.
        """
        dialog = Dialog_Dose("", "")
        c = self.table_roi.rowCount()
        if dialog.exec():
            new_data = dialog.getInputs()
            self.table_roi.insertRow(c)
            self.table_roi.setItem(c, 0,
                                   QtWidgets.QTableWidgetItem(new_data[0]))
            self.table_roi.setItem(c, 1,
                                   QtWidgets.QTableWidgetItem(new_data[1]))
            self.table_roi.setItem(c, 2,
                                   QtWidgets.QTableWidgetItem(new_data[2]))
            self.table_roi.setItem(c, 3,
                                   QtWidgets.QTableWidgetItem(new_data[3]))

    def remove_isodose(self):
        """
        Function to remove the selected isodoses from the table.
        """
        # Get selected rows
        rows = sorted(set(index.row() for index in
                          self.table_roi.selectedIndexes()))
        if rows:
            # Remove selected rows. Variable i is needed as, for example
            # if row 0 and 1 are to be removed, row 0 will be removed
            # first, making row 1 now row 0. Therefore, to remove row
            # '1', we need to remove row 1 minus the amount of rows that
            # have already been removed.
            i = 0
            for row in rows:
                self.table_roi.removeRow(row - i)
                i += 1
        else:
            QtWidgets.QMessageBox.warning(self, "No Isodose Selected",
                                "No isodose levels have been selected.")

    def save_isodoses(self):
        """
        Called when batch conversion process starts, to save any changes
        that may have been made to the table.
        """
        with open(data_path('batch_isodoseRoi.csv'), 'w', newline="") \
                as stream:
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
