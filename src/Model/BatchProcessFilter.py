"""Declares BatchProcessFilterModel for the application"""


class BatchProcessFilterModel(object):
    """
    BatchProcessFilterModel that serves as a central 
    data store to maintain state for the filtering pipeline 
    using Clinical Data while in BatchProcessing 
    """

    def __init__(self):
        super().__init__()

        self._selected_filters = {}

    @property
    def selected_filters(self):
        """
        Getter for the selected filters
        """
        return self._selected_filters

    def set_selected_filters(self, filter_type, value):
        """
        Setter for the selected csv directory
        """

        if filter_type not in self._selected_filters.keys():
            self._selected_filters[filter_type] = [value]
        else:
            self._selected_filters[filter_type].append(value)

    def remove_selected_filters(self, filter_type, value):
        """
        Remove filter from the selected_filters store
        """

        if filter_type not in self._selected_filters.keys():
            return
        else:
            self._selected_filters[filter_type].remove(value)
