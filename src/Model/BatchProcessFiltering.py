"""Declares BatchProcessingFilterModel for the application"""
from PyQt6.QtCore import QObject, pyqtSignal


class BatchProcessingFilterModel(QObject):
    """
    BatchProcessingFilterModel that serves as a central 
    data store to maintain state for the filtering pipeline 
    using Clinical Data while in BatchProcessing 
    """

    def __init__(self):
        super().__init__()

        self._selected_csv_directory = ""
        self._selected_filters = {}

    @property
    def selected_filters(self):
        """
        Getter for the selected filters
        """
        return self._selected_filters

    @selected_filters.setter
    def selected_filters(self, values):
        """
        Setter for the selected csv directory
        """
        filter_type, value = values

        if filter_type not in self._selected_filters.keys():
            self._selected_filters[filter_type] = [value]
        else:
            self._selected_filters[filter_type].append(value)

    def remove_selected_filters(self, values):
        """
        Remove filter from the selected_filters store
        """

        filter_type, value = values

        if filter_type not in self._selected_filters.keys():
            return
        else:
            self._selected_filters[filter_type] = self._selected_filters[filter_type].remove(value)
            
            if self._selected_filters[filter_type] == None:
                self._selected_filters[filter_type] = []
