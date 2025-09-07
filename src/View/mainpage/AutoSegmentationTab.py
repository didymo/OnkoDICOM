from typing import Callable
from PySide6 import QtWidgets
from PySide6.QtGui import QTextCursor
from src.Controller.AutoSegmentationController import AutoSegmentationController
from src.View.StyleSheetReader import StyleSheetReader


class AutoSegmentationTab(QtWidgets.QWidget):
    """
    Tab for the Auto Segmentation User Interface
    """

    # Static member maintain the controller outside a specific instance
    _controller: AutoSegmentationController | None = None

    def __init__(self, style_sheet: StyleSheetReader) -> None:
        super().__init__()
        """
        Initialising the User Interface for the Auto Segmentation Feature.
        Creating all the required elements for the User Interface to function.
        :param style_sheet:
        :rtype: None
        """
        self.style_sheet: StyleSheetReader = style_sheet  # Making Member for Style Sheet
        self._auto_segmentation_layout: QtWidgets.QFormLayout = QtWidgets.QFormLayout()  # Declaring the layout of the User interface
        self._make_segmentation_task_selection()  # Adding Segmentation Task Combo Box
        self._make_fast_checkbox()  # Adding Fast Option Checkbox
        self._make_progress_bar()  # Adding a progress bar
        self._make_progress_text()  # Adding Progress Text
        self._make_start_button(self._start_button_clicked)  # Adding Start Button Button
        self._fast_compatible_tasks = {"total",
                                       "body",
        }

        self.setLayout(self._auto_segmentation_layout)  # Setting the layout to the Main Window

        # Create Controller Class if one does not already exist
        # or Change view to new instance of view
        # there should only be one instance
        # which is created when MainPage class is created
        if AutoSegmentationTab._controller is None:
            AutoSegmentationTab._controller = AutoSegmentationController(self)
        else:
            AutoSegmentationTab._controller.set_view(self)

        # Check task setting against fast mode - set check box false if not compatible
        self._task_combo.currentIndexChanged.connect(self._check_task_is_fast_compatible)

    def _make_segmentation_task_selection(self) -> None:
        """
        Protected method to create the segmentation task label and
        combo box for segmentation task selection.
        :rtype: None
        """
        _task_label: QtWidgets.QLabel = QtWidgets.QLabel("Segmentation Task:")
        _task_label.setStyleSheet(self.style_sheet())
        self._auto_segmentation_layout.addWidget(_task_label)

        self._task_combo: QtWidgets.QComboBox = QtWidgets.QComboBox()
        # List of items which can be selected and segmented for
        self._task_combo.addItems([
            "total", "total_mr", "lung_vessels", "body", "body_mr",
            "vertebrae_mr", "hip_implant", "pleural_pericard_effusion", "cerebral_bleed",
            "head_glands_cavities", "head_muscles", "headneck_bones_vessels",
            "headneck_muscles", "liver_vessels", "oculomotor_muscles",
            "lung_nodules", "kidney_cysts", "breasts", "liver_segments",
            "liver_segments_mr", "craniofacial_structures", "abdominal_muscles"
        ])  # Need to figure out if we can make this an Enum
        self._task_combo.setCurrentIndex(0)
        self._task_combo.setToolTip("Select for Segmentation Task to be completed.\n"
                                    "This will be the specific area of the body to create a segment for")
        self._task_combo.setStyleSheet(self.style_sheet())
        self._auto_segmentation_layout.addWidget(self._task_combo)

    def _make_fast_checkbox(self) -> None:
        """
        Protected method to create the checkbox with label to
        determine if the fast option is selected.
        :rtype: None
        """
        self._fast_checkbox: QtWidgets.QCheckBox = QtWidgets.QCheckBox("Fast")
        self._fast_checkbox.setToolTip("When Activated this will allow for faster processing times with the \n"
                                       "downside of lower resolution of the resulting segmentations.\n"
                                       "This option is only available on particular tasks such as total. \n"
                                       "BENEFIT: Faster Segmentations\n"
                                       "DOWNSIDE: Not as Accurate Segmentations")
        self._fast_checkbox.setStyleSheet(self.style_sheet())
        self._auto_segmentation_layout.addWidget(self._fast_checkbox)

    def _make_progress_bar(self) -> None:
        """
        Protected method to create the progress bar label and progress bar.
        To show the user that there is activity when processing and to estimate
        how much longer till the task is completed.
        :rtype: None
        """
        _progress_bar_label: QtWidgets.QLabel = QtWidgets.QLabel("\n\nProgress:")
        _progress_bar_label.setStyleSheet(self.style_sheet())
        self._auto_segmentation_layout.addWidget(_progress_bar_label)

        self._progress_bar: QtWidgets.QProgressBar = QtWidgets.QProgressBar(minimum=0, maximum=100, value=20)
        self._progress_bar.setToolTip("The progress of the task currently being processed.")
        self._progress_bar.setStyleSheet(self.style_sheet())
        self._auto_segmentation_layout.addWidget(self._progress_bar)

    def _make_progress_text(self) -> None:
        """
        Protected method to create the progress text label and progress text box.
        To give the user feedback on what the current activity which is occurring.
        :rtype: None
        """
        _progress_text_label: QtWidgets.QLabel = QtWidgets.QLabel("\n\nCurrent Task:")
        _progress_text_label.setStyleSheet(self.style_sheet())
        self._auto_segmentation_layout.addWidget(_progress_text_label)

        self._progress_text = QtWidgets.QTextEdit()
        self._progress_text.setText("Waiting...")
        self._progress_text.setReadOnly(True)
        self._progress_text.setToolTip("What task the auto-segmentator is currently performing")
        self._progress_text.setStyleSheet(self.style_sheet())
        self._auto_segmentation_layout.addWidget(self._progress_text)

    def _make_start_button(self, button_action: Callable[[], None]) -> None:
        """
        Protected Method to create the start button
        To start the auto-segmentation task which has been selected.
        :param button_action: function
        :rtype: None
        """
        self._start_button: QtWidgets.QPushButton = QtWidgets.QPushButton("Start")
        self._start_button.setObjectName("start_button")
        self._start_button.setStyleSheet(self.style_sheet())
        # self._start_button.Alignment = QtCore.Qt.AlignmentFlag.AlignBottom
        # Button Action
        self._start_button.clicked.connect(button_action)
        self._auto_segmentation_layout.addWidget(self._start_button)

    def _start_button_clicked(self) -> None:
        """
        Protected method to be called when the start button is clicked.
        :rtype: None
        """
        self._controller.start_button_clicked()

    def get_segmentation_task(self) -> str:
        """
        Public Method to retrieve the current selection
        from the segmentation task combo box.
        :rtype: str
        """
        return self._task_combo.currentText()

    def get_fast_value(self) -> bool:
        """
        Public Method to retrieve the value of the fast checkbox.
        TO see if the fast option has been selected.
        :rtype: bool
        """
        return self._fast_checkbox.isChecked()

    def set_progress_bar_value(self, value: int) -> None:
        """
        Public Method to set the progress bar value.
        To display the estimated completion of the task
        :param value: int
        :rtype: None
        """
        self._progress_bar.setValue(value)

    def set_progress_text(self, text: str) -> None:
        """
        Public Method to set the progress text in the progress text box.
        To display the text to the user of what is currently being performed,
        to inform the user as to the current aspect of the task being performed.
        :param text: str
        :rtype: None
        """
        self._progress_text.append(text)
        cursor = self._progress_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self._progress_text.setTextCursor(cursor)
        self._progress_text.ensureCursorVisible()

    def enable_start_button(self):
        """Enables the start button and sets its text to "Start".

        This method is used to reactivate the start button after it has been
        disabled, typically after a segmentation task has completed or failed.
        """
        self._start_button.setEnabled(True)
        self._start_button.setText("Start")

    def disable_start_button(self):
        """Disables the start button and sets its text to "Wait".

        This method is used to deactivate the start button,
        typically during the segmentation process.
        """
        self._start_button.setEnabled(False)
        self._start_button.setText("Wait")

    def _check_task_is_fast_compatible(self):
        """
        Protected method to check if the currently selected task
        is compatible with the fast option. If the task is not
        compatible then the fast checkbox is disabled and unchecked.
        :rtype: None
        """
        if self._task_combo.currentText() not in self._fast_compatible_tasks:
            self._fast_checkbox.setChecked(False)
            self._fast_checkbox.setEnabled(False)
        else:
            self._fast_checkbox.setEnabled(True)

    def get_autoseg_controller(self):
        return self._controller