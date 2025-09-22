from typing import Callable
from PySide6 import QtWidgets, QtCore
from PySide6.QtGui import QTextCursor, QPixmap, QIcon
from PySide6.QtCore import QSize
from PySide6.QtWidgets import QSizePolicy, QMessageBox

from src.Model.AutoSegmentation.AutoSegmentViewState import AutoSegmentViewState
from src.View.AutoSegmentation.SegmentSelectorWidget import SegmentSelectorWidget
import src.View.StyleSheetReader as StyleSheetReader
from src.Controller.PathHandler import resource_path


class AutoSegmentWindow(QtWidgets.QWidget):
    """
    Class for the AutoSegmentation Window.
    A feature that allows an algorithm to be able creates segments of the human body.
    """

    def __init__(self, view_state: AutoSegmentViewState) -> None:
        """
        Initialization of the AutoSegmentWindow class.
        Setting up the window attributes,
        Creating Widgets and setting up layout

        :param view_state: AutoSegmentViewState
        :returns: None
        """
        super(AutoSegmentWindow, self).__init__()
        self._view_state = view_state
        self._setup_window(self) # Setting Up Window
        self.setWindowTitle("OnkoDICOM: Auto-Segmentation")
        self.setMinimumSize(QSize(800, 600))

        # Left Section of the Window
        # List Widget for Loafing Saved selections
        self._select_save: QtWidgets.QListWidget = QtWidgets.QListWidget()
        # TODO: Remove these add items
        self._select_save.addItems(["One", "Two", "Three", "Four"])
        self._select_save.addItems(["Five", "Six", "Seven", "Eight", "Nine"])

        # Button Widget for Save, Load Buttons
        self._delete_button = QtWidgets.QPushButton("Delete")
        self._save_button: QtWidgets.QPushButton = QtWidgets.QPushButton("Save")
        self._load_button: QtWidgets.QPushButton = QtWidgets.QPushButton("Load")
        self._delete_button.setProperty("QPushButtonClass", "fail-button")
        self._save_button.setProperty("QPushButtonClass", "success-button")
        self._button_layout: QtWidgets.QLayout = QtWidgets.QHBoxLayout()
        self._button_layout.addWidget(self._delete_button)
        self._button_layout.addWidget(self._save_button)
        self._button_layout.addWidget(self._load_button)
        self._button_widget: QtWidgets.QWidget = QtWidgets.QWidget()
        self._button_widget.setLayout(self._button_layout)
        self.setup_dialog()
        self._save_button.clicked.connect(self.click_save)

        # Widget for Saving and Loading
        self._save_load_layout: QtWidgets.QLayout = QtWidgets.QVBoxLayout()
        self._save_load_layout.addWidget(self._select_save)
        self._save_load_layout.addWidget(self._button_widget)
        self._save_load_widget: QtWidgets.QWidget = QtWidgets.QWidget()
        self._save_load_widget.setLayout(self._save_load_layout)

        # Widget for text output and start button
        self._text_start_layout: QtWidgets.QLayout = QtWidgets.QVBoxLayout()
        self._make_progress_text()
        self._make_start_button(self._start_button_clicked)
        self._text_start_widget: QtWidgets.QWidget = QtWidgets.QWidget()
        self._text_start_widget.setLayout(self._text_start_layout)

        # Splitting the left side Vertically
        # Wrapping left side in widget
        self._left_splitter: QtWidgets.QSplitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)
        self._left_splitter.addWidget(self._save_load_widget)
        self._left_splitter.addWidget(self._text_start_widget)
        self._left_splitter.setChildrenCollapsible(False)
        self._save_load_widget.setMinimumHeight(200)
        self._text_start_widget.setMinimumHeight(200)

        # Right Section of the Window
        self._tree_selector: SegmentSelectorWidget = SegmentSelectorWidget(self, self._view_state.segmentation_list)

        self._splitter: QtWidgets.QSplitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)

        # Set minimum widths for both panels
        self._splitter.setChildrenCollapsible(False)
        self._left_splitter.setMinimumWidth(300)
        self._tree_selector.setMinimumWidth(400)

        # Setting the Window Layout with splitter and widgets
        window_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        self._splitter.addWidget(self._left_splitter)
        self._splitter.addWidget(self._tree_selector)
        window_layout.addWidget(self._splitter)

        self.setLayout(window_layout)

    def sizeHint(self) -> QSize:
        """
        Concreate Method of the Virtual Method which determine the size of the widget

        :returns: QSize:
        """
        return QSize(700, 600)

    def setup_dialog(self) -> None:
        self._save_message_box: QtWidgets.QWidget = QtWidgets.QWidget()
        self._save_message_box.setProperty("AutoSegmentSave", "save-message-box")
        self._setup_window(self._save_message_box)
        self._save_message_box.setFixedSize(QSize(400, 150))

        self._box_save_button: QtWidgets.QPushButton = QtWidgets.QPushButton("Save")
        self._box_cancel_button: QtWidgets.QPushButton = QtWidgets.QPushButton("Cancel")
        self._box_save_button.setProperty("QPushButtonClass", "success-button")
        self._box_cancel_button.setProperty("QPushButtonClass", "fail-button")

        self._save_button_widget: QtWidgets.QWidget = QtWidgets.QWidget()
        self._save_box_buttons: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        self._save_box_buttons.addWidget(self._box_save_button)
        self._save_box_buttons.addWidget(self._box_cancel_button)
        self._save_button_widget.setLayout(self._save_box_buttons)

        self._save_text: QtWidgets.QLineEdit = QtWidgets.QLineEdit()
        self._save_text.setPlaceholderText("Selection Name")
        self._save_text.setMaxLength(25)
        self._save_text_label: QtWidgets.QLabel = QtWidgets.QLabel("Enter Selection Name:")
        self._save_box_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout()
        self._save_box_layout.addWidget(self._save_text_label)
        self._save_box_layout.addWidget(self._save_text)
        self._save_box_layout.addWidget(self._save_button_widget)
        self._save_message_box.setLayout(self._save_box_layout)

    def click_save(self) -> None:
        self._save_message_box.show()

    def _setup_window(self, window: QtWidgets.QWidget | QtWidgets.QMessageBox) -> None:
        """
        Protected Method for Setting up the window, with Title, StyleSheet, MinimumSize and Icon

        :returns: None
        """
        # Adding Window Attributes
        window.setStyleSheet(StyleSheetReader.get_stylesheet())

        # Adding Window Icon
        window_icon: QIcon() = QIcon()
        window_icon.addPixmap(QPixmap(resource_path("res/images/icon.ico")), QIcon.Mode.Normal, QIcon.State.Off)
        window.setWindowIcon(window_icon)

    def _make_progress_text(self) -> None:
        """
        Protected method to create the progress text label and progress text box.
        To give the user feedback on what the current activity which is occurring.

        :return: None
        """
        _progress_text_label: QtWidgets.QLabel = QtWidgets.QLabel("\n\nCurrent Task:")
        self._text_start_layout.addWidget(_progress_text_label)

        self._progress_text: QtWidgets.QTextEdit = QtWidgets.QTextEdit()
        self._progress_text.setText("Waiting...")
        self._progress_text.setReadOnly(True)
        self._progress_text.setToolTip("What task the auto-segmentator is currently performing")
        self._text_start_layout.addWidget(self._progress_text)

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
        self._text_start_layout.addWidget(self._start_button)

    def _start_button_clicked(self) -> None:
        """
        Protected method to be called when the start button is clicked.

        :return: None
        """
        self._view_state.start_button_connection()

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