import sys
import pandas
import functools
from typing import Callable
from PySide6 import QtWidgets
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

        # Getting Fast Compatible
        # self._get_fast_lists()
        # self._make_fast_checkbox()
        # TODO: Intentionally Disabled while we are making sure the new GUI works will be looking into if we can reimplement this in the future

        # Left Section of the Window
        self._left_layout: QtWidgets.QLayout = QtWidgets.QFormLayout()
        self._make_progress_text()
        self._make_start_button(self._start_button_clicked)

        # Right Section of the Window
        self._tree_selector: SegmentSelectorWidget = SegmentSelectorWidget(self)

        # Setting the Window Layout
        window_layout: QtWidgets.QHBoxLayout = QtWidgets.QHBoxLayout()
        window_layout.addLayout(self._left_layout, stretch=1) # Stretch so it take up 1 unit of the window
        window_layout.addWidget(self._tree_selector, stretch=2) # Stretch so it Takes 2 Units of the screen
        self.setLayout(window_layout)

        # Setting up connections
        self._setup_connections()

    def sizeHint(self) -> QSize:
        """
        Concreate Method of the Virtual Method which determine the size of the widget

        :returns: QSize:
        """
        return QSize(600, 600)

    def _create_controller(self, controller) -> None:
        """
        Protected Method Creating the Controller for the AutoSegmentation Feature or Connecting to it if it already exists
        :param _controller: AutoSegmentationController instance

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

    def _setup_connections(self) -> None:
        """
        Protected Method to set up connections within the widget/Window

        :returns: None
        """
        # Check task setting against fast mode - set check box false if not compatible
        #self._task_combo.currentIndexChanged.connect(self._check_task_is_fast_compatible)

    @functools.lru_cache(maxsize=128, typed=False)
    def _get_lists_from_csv(self) -> tuple[list[str], list[str], list[str]]:
        """
        Protected Cached Method to read the CSV File and retrieve the Structures, Fast, and Fastest Lists from it,

        :returns: tuple[list[str], list[str], list[str]]
        """
        fast_fastest_lists: pandas.DataFrame = pandas.read_csv(resource_path("data\\csv\\segmentation_lists.csv"))
        fast_fastest: pandas.DataFrame = fast_fastest_lists.filter(["Structure", "Fast", "Fastest"])
        fast_list: list[str] = fast_fastest[fast_fastest["Fast"]]["Structure"].str.strip().tolist()
        fastest_list: list[str] = fast_fastest[fast_fastest["Fastest"] == "true"]["Structure"].str.strip().tolist()
        structure_list: list[str] = fast_fastest["Structure"].str.strip().tolist()
        return structure_list ,fast_list, fastest_list

    def _make_fast_checkbox(self) -> None:
        """
        Protected method to create the checkbox with label to
        determine if the fast option is selected.

        :return: None
        """
        self._fast_checkbox: QtWidgets.QCheckBox = QtWidgets.QCheckBox("Fast")
        self._fast_checkbox.setToolTip("When Activated this will allow for faster processing times with the \n"
                                       "downside of lower resolution of the resulting segmentations.\n"
                                       "This option is only available on particular tasks such as total. \n"
                                       "BENEFIT: Faster Segmentations\n"
                                       "DOWNSIDE: Not as Accurate Segmentations")
        self._left_layout.addWidget(self._fast_checkbox)

    def _get_fast_lists(self):
        """
        Getting Fast Compatible Lists from CSV File

        :returns: None
        """
        seg_lists: tuple[list[str], list[str], list[str]] = self._get_lists_from_csv()
        self._fast_compatible_tasks: list[str] = seg_lists[1]
        self._fastest_compatible_tasks: list[str] = seg_lists[2]

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

    def _check_task_is_fast_compatible(self) -> None:
        """
        Protected method to check if the currently selected task
        is compatible with the fast option. If the task is not
        compatible then the fast checkbox is disabled and unchecked.

        :return: None
        """
        # TODO: Find a new way to implement this
        if self._task_combo.currentText() not in self._fast_compatible_tasks:
            self._fast_checkbox.setChecked(False)
            self._fast_checkbox.setEnabled(False)
        else:
            self._fast_checkbox.setEnabled(True)

    def get_segmentation_task(self) -> list[str]:
        """
        Public Method to retrieve the current selection
        from the segmentation selection tree.

        :return: list[str]
        """
        return self._tree_selector.get_segment_list()

    def get_fast_value(self) -> bool:
        """
        Public Method to retrieve the value of the fast checkbox.
        TO see if the fast option has been selected.

        :return: bool
        """
        return False
        # TODO: Intentionally Disabled while we are making sure the new GUI works will be looking into if we can reimplement this in the future
        # return self._fast_checkbox.isChecked()

    def get_autoseg_controller(self):
        return self._controller