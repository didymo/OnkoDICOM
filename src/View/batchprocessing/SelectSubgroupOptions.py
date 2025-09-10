from PySide6 import QtWidgets, QtGui
import logging

from src.View.StyleSheetReader import StyleSheetReader


class SelectSubgroupOptions(QtWidgets.QWidget):
    """
    Select subgroup options for batch processing.
    """

    def __init__(self):
        """
        Initialise the class.
        """
        QtWidgets.QWidget.__init__(self)

        # Create the main layout
        self.main_layout = QtWidgets.QVBoxLayout()

        # Info messages
        self.message = QtWidgets.QLabel(
            "No Clinical-data-SR files located in current selected directory"
            )

        # Filter options table
        self.filter_table = QtWidgets.QTableWidget(0, 0)
        self.filter_table.setStyleSheet(StyleSheetReader().get_stylesheet())

        # Set up layout
        self.main_layout.addWidget(self.message)
        self.main_layout.addWidget(self.filter_table)
        self.setLayout(self.main_layout)

        # storing the currently selected filter options
        self._selected_filters = {}

        self.filter_table.cellClicked.connect(self.select_filter_option_cell)
        logging.debug("SelectSubgroupOptions successfully initialised.")

    def get_selected_filter_options(self):
        """
        Getter for the selected filters
        """
        return self._selected_filters

    def display_no_data(self):
        """
        Utility method to display an empty table and appropriate message
        """
        self.message.setText(
            "No Clinical-data-SR files located in current selected directory"
            )
        self.filter_table.setRowCount(0)
        self.filter_table.setColumnCount(0)
        self.filter_table.setHorizontalHeaderLabels([])

    def show_filtering_options_in_table(self, options_data_dict):
        """
        Displays the data in the table
        :param options_data_dict: dictionary of clinical
        data attributes and values
        """

        if not options_data_dict:
            self.display_no_data()
            return

        self.message.setText("Select values to filter by:")

        self.filter_table.setRowCount(0)
        self.filter_table.setColumnCount(0)

        # removes the Patient Identifier (assumed to be first column
        # in the dataset) 
        # As the column name may be changing we cannot hard code the 
        # column name
        # not a necessary filter option as specified in requirements
        options_data_dict.pop(list(options_data_dict)[0])

        columns_to_remove = []

        # remove the keys with an empty list of options
        for title, values_list in options_data_dict.items():
            filtered_values = [x for x in values_list if x != ""]
            if len(filtered_values) == 0:
                columns_to_remove.append(title)

        for title in columns_to_remove:
            options_data_dict.pop(title)

        for title in options_data_dict.keys():
            col = self.filter_table.columnCount()
            self.filter_table.insertColumn(col)

            for row in range(0, len(options_data_dict[title])):
                str_value = str(options_data_dict[title][row])
                # filters out blank options
                if str_value == "":
                    continue
                filter_value = QtWidgets.QTableWidgetItem(str_value)

                if row >= self.filter_table.rowCount():
                    self.filter_table.insertRow(row)

                self.filter_table.setItem(row, col, filter_value)

        self.filter_table.setHorizontalHeaderLabels(options_data_dict.keys())

    def select_filter_option_cell(self, row, column):
        """
        Toggles the selected options green and stores value
        :param row: row index that was clicked
        :param column: column index that was clicked
        """
        item = self.filter_table.item(row, column)

        # in the case they select empty cell
        if not item:
            return

        header = self.filter_table.horizontalHeaderItem(column).text()
        text_filter = item.text()

        logging.debug(f"Cell selected: ({row}, {column}). " \
        "Column header: '{header}'. String-value: '{text_filter}'")

        if header in self._selected_filters.keys():
            current_filters = self._selected_filters[header]

            if text_filter in current_filters:
                item.setBackground(QtGui.QColor(255, 255, 255))

                # and remove item
                self.remove_selected_filters(header, text_filter)

                logging.debug(f"Value: '{text_filter}' deselected")

                return

        item.setBackground(QtGui.QColor(144, 238, 144))

        # store in model for reference at output
        self.set_selected_filters(header, text_filter)

        logging.debug(f"Value: '{text_filter}' selected")

    def set_selected_filters(self, filter_type, value):
        """
        Setter for the selected filters
        :param filter_type: the column name
        :param value: the actual value within that column
        """

        if filter_type not in self._selected_filters.keys():
            self._selected_filters[filter_type] = [value]
        else:
            self._selected_filters[filter_type].append(value)

    def remove_selected_filters(self, filter_type, value):
        """
        Remove filter from the selected_filters store
        :param filter_type: the column name
        :param value: the actual value within that column
        """

        if filter_type not in self._selected_filters.keys():
            return
        else:
            self._selected_filters[filter_type].remove(value)
