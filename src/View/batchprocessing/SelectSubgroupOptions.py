import platform
from os.path import expanduser
from PySide6 import QtWidgets, QtGui
from src.Controller.PathHandler import resource_path


class SelectSubgroupOptions(QtWidgets.QWidget):
    """
    ClinicalData-SR2CSV options for batch processing.
    """

    def __init__(self, _batch_process_filter_model):
        """
        Initialise the class.
        """
        QtWidgets.QWidget.__init__(self)

        # Create the main layout
        self.main_layout = QtWidgets.QVBoxLayout()

        # Get the stylesheet
        if platform.system() == 'Darwin':
            self.stylesheet_path = "res/stylesheet.qss"
        else:
            self.stylesheet_path = "res/stylesheet-win-linux.qss"
        self.stylesheet = open(resource_path(self.stylesheet_path)).read()

        # Info messages
        self.message = QtWidgets.QLabel(
            "No Clinical-data-SR files located in current selected directory"
            )

        # Filter options table
        self.filter_table = QtWidgets.QTableWidget(0, 0)
        self.filter_table.setStyleSheet(self.stylesheet)

        # Set up layout
        self.main_layout.addWidget(self.message)
        self.main_layout.addWidget(self.filter_table)
        self.setLayout(self.main_layout)

        self._batch_process_filter_model = _batch_process_filter_model

        self.filter_table.cellClicked.connect(self.select_filter_option_cell)

    def display_no_data(self):
        print("display no data called")
        self.message.setText("No Clinical-data-SR files located in current selected directory")
        self.filter_table.setRowCount(0)
        self.filter_table.setColumnCount(0)
        self.filter_table.setHorizontalHeaderLabels([])

    def show_filtering_options_in_table(self, options_data_dict):
        if not options_data_dict:
            self.display_no_data()
            return

        self.message.setText("Select values to filter by:")
        
        self.filter_table.setRowCount(0)
        self.filter_table.setColumnCount(0)

        options_data_dict.pop("HASHidentifier")

        for title in options_data_dict.keys():
            col = self.filter_table.columnCount()
            self.filter_table.insertColumn(col)
            
            for row in range(0, len(options_data_dict[title])):
                filter_value = QtWidgets.QTableWidgetItem(str(options_data_dict[title][row]))
                
                if row >= self.filter_table.rowCount():
                    self.filter_table.insertRow(row)

                self.filter_table.setItem(row, col, filter_value)

        self.filter_table.setHorizontalHeaderLabels(options_data_dict.keys())

    def select_filter_option_cell(self, row, column):
        item = self.filter_table.item(row, column)

        # in the case they select empty cell
        if not item:
            return
        
        header = self.filter_table.horizontalHeaderItem(column).text()
        text_filter = item.text()

        if header in self._batch_process_filter_model.selected_filters.keys():
            current_filters = self._batch_process_filter_model.selected_filters[header]

            if text_filter in current_filters:
                item.setBackground(QtGui.QColor(255, 255, 255))

                # and remove item
                self._batch_process_filter_model.remove_selected_filters(header, text_filter)
                return

        item.setBackground(QtGui.QColor(144, 238, 144))

        # store in model for reference at output
        self._batch_process_filter_model.set_selected_filters(header, text_filter)
