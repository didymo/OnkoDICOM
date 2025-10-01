import copy
from typing import Callable
from PySide6 import QtWidgets, QtCore
from PySide6.QtGui import QTextCursor, QPixmap, QIcon
from PySide6.QtCore import QSize

from src.Model.AutoSegmentation.AutoSegmentViewState import AutoSegmentViewState
from src.View.AutoSegmentation.ButtonInputBox import ButtonInputBox
from src.View.AutoSegmentation.SegmentSelectorWidget import SegmentSelectorWidget
import src.View.StyleSheetReader as StyleSheetReader
from src.Controller.PathHandler import resource_path
from src.View.WindowBarIconSetup import setup_window


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
        self.setProperty("WidgetClass", "widget-window")
        self.setMinimumSize(QSize(800, 600))
        setup_window(self, "OnkoDICOM: Auto-Segmentation") # Setting Up Window

        # Member Variables
        self._view_state = view_state
        self._tree_selector: SegmentSelectorWidget = SegmentSelectorWidget(self, view_state.segmentation_list, update_callback=self.update_save_button)
        self._start_button: QtWidgets.QPushButton = QtWidgets.QPushButton("Start")
        self._start_button.setEnabled(False)
        self._progress_text: QtWidgets.QTextEdit = QtWidgets.QTextEdit()
        self._select_save: QtWidgets.QListWidget = QtWidgets.QListWidget()
        self.save_list: list[str] = []
        self._save_window: ButtonInputBox | None = None
        self.running: bool = False

        # Left Section of the Window
        save_load_layout: QtWidgets.QLayout = QtWidgets.QVBoxLayout()
        save_load_layout.addWidget(self._select_save_widget())
        save_load_layout.addWidget(self._select_button_widget())
        save_load_widget: QtWidgets.QWidget = QtWidgets.QWidget()
        save_load_widget.setLayout(save_load_layout)
        text_start_widget: QtWidgets.QWidget = self._progress_start_widget()

        # Right Section of the Window
        tree_selector_label: QtWidgets.QLabel = QtWidgets.QLabel("Select Segments:")
        self._tree_selector.setMinimumWidth(400)
        right_buttons: QtWidgets.QWidget = (
            self._right_button_widget(self._right_select_buttons(self._tree_selector), self._close_button_widget()))
        splitter: QtWidgets.QSplitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # Setting the Window Layout with splitter and widgets
        splitter.addWidget(self._setup_left_widget(save_load_widget, text_start_widget))
        splitter.addWidget(self._right_setup_widget(tree_selector_label, self._tree_selector, right_buttons))
        window_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        window_layout.addWidget(splitter)

        self.setLayout(window_layout)

    def sizeHint(self) -> QSize:
        """
        Concreate Method of the Virtual Method which determine the size of the widget

        :returns: QSize:
        """
        return QSize(700, 600)

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
        self.running: bool = False
        self._start_button.setEnabled(True)
        self._start_button.setText("Start")

    def disable_start_button(self) -> None:
        """Disables the start button and sets its text to "Wait".

        This method is used to deactivate the start button,
        typically during the segmentation process.

        :return: None
        """
        self.running: bool = True
        self._start_button.setEnabled(False)
        self._start_button.setText("Wait")

    def get_segmentation_roi_subset(self) -> list[str]:
        """
        Public Method to retrieve the current selection
        from the segmentation selection tree.

        :return: list[str]
        """
        return self._tree_selector.get_segment_list()

    def load_selection(self, load_list: list[str]) -> None:
        self._tree_selector.deselect_all()
        self._tree_selector.load_selections(load_list)

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

    def _select_save_widget(self) -> QtWidgets.QWidget:
        # List Widget for Loafing Saved selections
        select_save_label: QtWidgets.QLabel = QtWidgets.QLabel("Save Selections:")
        self.database_feedback = QtWidgets.QLabel()
        self.database_feedback.setProperty("QLabelClass", "info-feedback")
        select_save_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout()
        select_save_layout.addWidget(select_save_label)
        select_save_layout.addWidget(self.database_feedback)
        select_save_layout.addWidget(self._select_save)
        select_save_widget: QtWidgets.QWidget = QtWidgets.QWidget()
        select_save_widget.setLayout(select_save_layout)

        return select_save_widget

    def _select_button_widget(self) -> QtWidgets.QWidget:
        # Delete Button
        self._delete_button = QtWidgets.QPushButton("Delete")
        self._delete_button.setProperty("QPushButtonClass", "fail-button")
        self._delete_button.clicked.connect(self._delete_button_clicked)
        self._delete_button.setEnabled(False)

        # Save Button
        self._save_button: QtWidgets.QPushButton = QtWidgets.QPushButton("Save")
        self._save_button.setProperty("QPushButtonClass", "success-button")
        self._save_button.clicked.connect(self._save_button_clicked)
        self._save_button.setEnabled(False)

        # Load Button
        self._load_button: QtWidgets.QPushButton = QtWidgets.QPushButton("Load")
        self._load_button.clicked.connect(self._load_button_clicked)
        self._load_button.setEnabled(False)

        # Adding Button Layout
        button_layout: QtWidgets.QLayout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self._delete_button)
        button_layout.addWidget(self._save_button)
        button_layout.addWidget(self._load_button)

        # Button Widget
        button_widget: QtWidgets.QWidget = QtWidgets.QWidget()
        button_widget.setLayout(button_layout)

        return button_widget

    def _setup_left_widget(self, save_load_widget: QtWidgets.QWidget, text_start_widget: QtWidgets.QWidget) -> QtWidgets.QSplitter:
        left_splitter: QtWidgets.QSplitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)
        left_splitter.addWidget(save_load_widget)
        left_splitter.addWidget(text_start_widget)
        left_splitter.setChildrenCollapsible(False)
        save_load_widget.setMinimumHeight(200)
        text_start_widget.setMinimumHeight(200)
        left_splitter.setMinimumWidth(300)

        return left_splitter

    def _progress_start_widget(self) -> QtWidgets.QWidget:

        text_start_layout: QtWidgets.QLayout = self._make_progress_text()
        text_start_layout: QtWidgets.QLayout = self._make_start_button(self._start_button_clicked, text_start_layout)
        text_start_widget: QtWidgets.QWidget = QtWidgets.QWidget()
        text_start_widget.setLayout(text_start_layout)

        return text_start_widget

    def _right_select_buttons(self, selector: SegmentSelectorWidget) -> QtWidgets.QWidget:
        select_all_button: QtWidgets.QPushButton = QtWidgets.QPushButton("Select All")
        select_all_button.clicked.connect(selector.select_all)
        select_all_button.setMaximumWidth(120)
        deselect_all_button: QtWidgets.QPushButton = QtWidgets.QPushButton("Deselect All")
        deselect_all_button.clicked.connect(selector.deselect_all)
        deselect_all_button.setMaximumWidth(120)
        selector_button_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        selector_button_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        selector_button_layout.addWidget(select_all_button)
        selector_button_layout.addWidget(deselect_all_button)
        selector_button: QtWidgets.QWidget = QtWidgets.QWidget()
        selector_button.setLayout(selector_button_layout)

        return selector_button

    def _close_button_widget(self) -> QtWidgets.QWidget:
        close_button: QtWidgets.QPushButton = QtWidgets.QPushButton("Close")
        close_button.clicked.connect(self.close)
        close_button.setMaximumWidth(120)
        close_button_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        close_button_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        close_button_layout.addWidget(close_button)
        close_button_widget: QtWidgets.QWidget = QtWidgets.QWidget()
        close_button_widget.setLayout(close_button_layout)

        return close_button_widget

    def _right_button_widget(self, selector_buttons: QtWidgets.QWidget, close_button_widget: QtWidgets.QWidget) -> QtWidgets.QWidget:
        right_button_layout: QtWidgets.QLayout = QtWidgets.QHBoxLayout()
        right_button_layout.addWidget(selector_buttons)
        right_button_layout.addWidget(close_button_widget)
        right_button: QtWidgets.QWidget = QtWidgets.QWidget()
        right_button.setLayout(right_button_layout)

        return right_button

    def _right_setup_widget(self,
                            label: QtWidgets.QLabel,
                            tree: SegmentSelectorWidget,
                            buttons: QtWidgets.QWidget
                            ) -> QtWidgets.QWidget:
        right_side_layout: QtWidgets.QLayout = QtWidgets.QVBoxLayout()
        right_side_layout.addWidget(label)
        right_side_layout.addWidget(tree)
        right_side_layout.addWidget(buttons)
        right_side: QtWidgets.QWidget = QtWidgets.QWidget()
        right_side.setLayout(right_side_layout)

        return right_side

    def _make_progress_text(self) -> QtWidgets.QLayout:
        """
        Protected method to create the progress text label and progress text box.
        To give the user feedback on what the current activity which is occurring.

        :return: None
        """
        progress_text_label: QtWidgets.QLabel = QtWidgets.QLabel("Current Task:")

        text_start_layout: QtWidgets.QLayout = QtWidgets.QVBoxLayout()
        text_start_layout.addWidget(progress_text_label)

        self._progress_text: QtWidgets.QTextEdit = QtWidgets.QTextEdit()
        self._progress_text.setText("Waiting...")
        self._progress_text.setReadOnly(True)
        self._progress_text.setToolTip("What task the auto-segmentator is currently performing")
        text_start_layout.addWidget(self._progress_text)

        return text_start_layout

    def _make_start_button(self, button_action: Callable[[], None], layout: QtWidgets.QLayout) -> QtWidgets.QLayout:
        """
        Protected Method to create the start button
        To start the auto-segmentation task which has been selected.

        :param button_action: function
        :return: None
        """
        self._start_button.setObjectName("seg_start_button")
        # Button Action
        self._start_button.clicked.connect(button_action)
        layout.addWidget(self._start_button)

        return layout

    def _start_button_clicked(self) -> None:
        """
        Protected method to be called when the start button is clicked.

        :return: None
        """
        self._view_state.start_button_connection("")

    def _get_list_text(self) -> str:
        """
        To get the text out the List Selector

        :return: str
        """
        return self._select_save.currentItem().text()

    def _delete_send(self, output: str) -> None:
        """
        Protected method to be called when the delete button is clicked.

        :return: None
        """
        if output:
            self._view_state.delete_button_connection(output)
        if not self.save_list:
            self._disable_load_button()
            self._disable_delete_button()

    def _delete_button_clicked(self) -> None:
        """
        Events to occur when the delete button is clicked:

        :return: None
        """
        try:
            output: str = copy.deepcopy(self._get_list_text())
            self._delete_window: ButtonInputBox = ButtonInputBox("Are You Sure You would like to Delete: {}". format(output),
                                                                 self._delete_send,
                                                                 self._delete_close,
                                                                 text_box=False,
                                                                 reversed_buttons=True,
                                                                 delete_word=output)
        except AttributeError:
            return
        self._delete_window.show()
        self._delete_window.raise_()
        self._delete_window.activateWindow()

    def _delete_close(self) -> None:
        """
        When the Cancel Button is clicked on the Delete window

        :return: None
        """
        if self._delete_window is not None:
            self._delete_window.close()
            self._delete_window: None = None

    def _disable_delete_button(self):
        """
        Disabling the delete button when cannot be used

        :return: None
        """
        self._delete_button.setEnabled(False)

    def _enable_delete_button(self):
        """
        Enabling the delete button when can be used

        :return: None
        """
        self._delete_button.setEnabled(True)

    def _save_button_clicked(self) -> None:
        """
        Opening the window for text input when the save button is clicked.
        Will also rais the window to the fron if is already open

        :return: None
        """
        self._save_window: ButtonInputBox = ButtonInputBox("Input Save Name:",
                                                          self._save_send,
                                                          self._save_close,
                                                          text_box=True)
        self._save_window.show()
        self._save_window.raise_()
        self._save_window.activateWindow()

    def update_save_button(self) -> None:
        """
        To disable and enable the save button is a selection has been selected
        """
        if self._view_state.segmentation_list:
            self._save_button.setEnabled(True)
            if not self.running:
                self._start_button.setEnabled(True)
            return
        self._save_button.setEnabled(False)
        self._start_button.setEnabled(False)


    def _load_button_clicked(self) -> None:
        """
        Protected method to be called when the load button is clicked.

        :return: None
        """
        try:
            output: str = self._get_list_text()
        except AttributeError:
            return
        if output:
            self._view_state.load_button_connection(output)

    def _disable_load_button(self):
        """
        Disabling the load button when cannot be used

        :return: None
        """
        self._load_button.setEnabled(False)

    def _enable_load_button(self):
        """
        Enabling the load button when can be used

        :return: None
        """
        self._load_button.setEnabled(True)

    def _save_send(self, text: str) -> None:
        """
        Chack and Transmit information to the Controller then update feed back to the user

        :param text: str
        :return: None
        """
        if text != "" and text not in self.save_list:
            self.add_save_item(text)
            self._view_state.save_button_connection(text)
            self._save_close()
            return
        if text:
            self._save_window.feedback.setText("Name already exists use unused name")
        else:
            self._save_window.feedback.setText("Please enter save name")
        self._save_window.setFixedSize(QSize(400, 175))
        self._save_window.feedback.show()

    def _save_close(self):
        """
        To close the save window after OK or Cancel have been clicked

        :return: None
        """
        self._save_window.close()
        self._save_window: None = None

    def add_save_item(self, text: str) -> None:
        """
        Adding a new item to the Selector Widget
        :param text: str
        """
        self.save_list.append(text)
        if self.save_list:
            self._enable_load_button()
            self._enable_delete_button()
        self._select_save.addItem(text)

    def add_save_list(self, saves: list[str]) -> None:
        """
        Adding a list of save names to the Selector Widget
        :param saves: list[str]
        :return: None
        """
        self.save_list = saves
        if self.save_list:
            self._enable_load_button()
            self._enable_delete_button()
        self._select_save.clear()
        self._select_save.addItems(saves)

    def remove_save_item(self, output: str) -> None:
        """
        Deleting Selected Row from the Selector Widget

        :param output: str
        :return: None
        """
        self._select_save.takeItem(self._select_save.currentRow())
        self.save_list.remove(output)