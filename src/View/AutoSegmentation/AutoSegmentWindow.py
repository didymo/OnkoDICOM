from typing import Callable
from PySide6 import QtWidgets, QtCore
from PySide6.QtGui import QTextCursor, QPixmap, QIcon
from PySide6.QtCore import QSize

from src.View.AutoSegmentation.SegmentSelectorWidget import SegmentSelectorWidget
import src.View.StyleSheetReader as StyleSheetReader
from src.Controller.PathHandler import resource_path


class AutoSegmentWindow(QtWidgets.QWidget):
    """
    Class for the AutoSegmentation Window.
    A feature that allows an algorithm to be able creates segments of the human body.
    """
    _controller = None

    def __init__(self, controller) -> None:
        """
        Initialization of the AutoSegmentWindow class.
        Includes aspects as creating a controller, setting up the window attributes,
        Creating Widgets and setting up layout

        :param controller: AutoSegmentationController instance
        :returns: None
        """
        super(AutoSegmentWindow, self).__init__()
        self._create_controller(controller)

        # Setting Up Window
        self._setup_window()

        # Left Section of the Window
        self._left_layout: QtWidgets.QLayout = QtWidgets.QVBoxLayout()
        self._make_progress_text()
        self._make_start_button(self._start_button_clicked)

        # Wrap left layout in widget for splitter resizing
        self._left_layout_container: QtWidgets.QWidget = QtWidgets.QWidget()
        self._left_layout_container.setLayout(self._left_layout)

        # Right Section of the Window
        self._tree_selector: SegmentSelectorWidget = SegmentSelectorWidget(self, controller.segmentation_list)

        self._splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)

        # Set minimum widths for both panels
        self._splitter.setChildrenCollapsible(False)
        self._left_layout_container.setMinimumWidth(200)
        self._tree_selector.setMinimumWidth(200)

        # Setting the Window Layout with splitter and widgets
        window_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        self._splitter.addWidget(self._left_layout_container)
        self._splitter.addWidget(self._tree_selector)
        window_layout.addWidget(self._splitter)

        self.setLayout(window_layout)

    def sizeHint(self) -> QSize:
        """
        Concreate Method of the Virtual Method which determine the size of the widget

        :returns: QSize:
        """
        return QSize(600, 600)

    def _create_controller(self, controller) -> None:
        """
        Protected Method Creating the Controller for the AutoSegmentation Feature or Connecting to it if it already exists
        :param controller: AutoSegmentationController instance

        :returns: None
        """
        self._controller = controller

    def _setup_window(self) -> None:
        """
        Protected Method for Setting up the window, with Title, StyleSheet, MinimumSize and Icon

        :returns: None
        """
        # Adding Window Attributes
        self.setWindowTitle("OnkoDICOM: Auto-Segmentation")
        self.setStyleSheet(StyleSheetReader.get_stylesheet())
        self.setMinimumSize(QSize(600, 600))

        # Adding Window Icon
        window_icon: QIcon() = QIcon()
        window_icon.addPixmap(QPixmap(resource_path("res/images/icon.ico")), QIcon.Mode.Normal, QIcon.State.Off)
        self.setWindowIcon(window_icon)

    def _make_progress_text(self) -> None:
        """
        Protected method to create the progress text label and progress text box.
        To give the user feedback on what the current activity which is occurring.

        :return: None
        """
        _progress_text_label: QtWidgets.QLabel = QtWidgets.QLabel("\n\nCurrent Task:")
        self._left_layout.addWidget(_progress_text_label)

        self._progress_text: QtWidgets.QTextEdit = QtWidgets.QTextEdit()
        self._progress_text.setText("Waiting...")
        self._progress_text.setReadOnly(True)
        self._progress_text.setToolTip("What task the auto-segmentator is currently performing")
        self._left_layout.addWidget(self._progress_text)

    def _make_start_button(self, button_action: Callable[[], None]) -> None:
        """
        Protected Method to create the start button
        To start the auto-segmentation task which has been selected.

        :param button_action: function
        :return: None
        """
        self._start_button: QtWidgets.QPushButton = QtWidgets.QPushButton("Start")
        self._start_button.setObjectName("start_button")
        # Button Action
        self._start_button.clicked.connect(button_action)
        self._left_layout.addWidget(self._start_button)

    def _start_button_clicked(self) -> None:
        """
        Protected method to be called when the start button is clicked.

        :return: None
        """
        self._controller.start_button_clicked()

    def set_progress_text(self, text: str) -> None:
        """
        Public Method to set the progress text in the progress text box.
        To display the text to the user of what is currently being performed,
        to inform the user as to the current aspect of the task being performed.

        :param text: str
        :return: None
        """
        self._progress_text.append(text)
        cursor: QTextCursor = self._progress_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self._progress_text.setTextCursor(cursor)
        self._progress_text.ensureCursorVisible()

    def enable_start_button(self) -> None:
        """Enables the start button and sets its text to "Start".

        This method is used to reactivate the start button after it has been
        disabled, typically after a segmentation task has completed or failed.

        :return: None
        """
        self._start_button.setEnabled(True)
        self._start_button.setText("Start")

    def disable_start_button(self) -> None:
        """Disables the start button and sets its text to "Wait".

        This method is used to deactivate the start button,
        typically during the segmentation process.

        :return: None
        """
        self._start_button.setEnabled(False)
        self._start_button.setText("Wait")

    def get_segmentation_roi_subset(self) -> list[str]:
        """
        Public Method to retrieve the current selection
        from the segmentation selection tree.

        :return: list[str]
        """
        return self._tree_selector.get_segment_list()

    def get_autoseg_controller(self):
        return self._controller