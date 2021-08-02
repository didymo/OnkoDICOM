from PySide6 import QtWidgets, QtGui


class DicomStackedWidget(QtWidgets.QStackedWidget):
    """
    A child of QStackedWidget that contains the single view and the four views
    """

    def __init__(self, format_metadata):
        super(DicomStackedWidget, self).__init__()
        self.format_metadata = format_metadata

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        """
        Format the margin and font size of the meta data when the window is resized
        """
        self.format_metadata(event.size())
