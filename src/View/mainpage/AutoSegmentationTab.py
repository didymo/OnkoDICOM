from PySide6 import QtCore, QtWidgets

from src.View.StyleSheetReader import StyleSheetReader


class AutoSegmentationTab(QtWidgets.QWidget):
    """
    Tab for the Auto Segmentation User Interface
    """
    
    def __init__(self, style_sheet: StyleSheetReader) -> None:
        """
        Initialising the User Interface for the Auto Segmentation Feature.
        Creating all the required elements for the User Interface to function.
        :param style_sheet: 
        :rtype: None
        """
        QtWidgets.QWidget.__init__(self)

        self.style_sheet: StyleSheetReader = style_sheet                                # Making Member for Style Sheet
        self.auto_segmentation_layout: QtWidgets.QFormLayout = QtWidgets.QFormLayout()  # Declaring the layout of the User interface
        self._make_segmentation_task_selection()                                        # Adding Segmentation Task Combo Box
        self._make_fast_checkbox()                                                      # Adding Fast Option Checkbox
        self._make_progress_bar()                                                       # Adding a progress bar
        self._make_progress_text()                                                      # Adding Progress Text
        self._make_start_button(self._start_button_clicked)                             # Adding Start Button Button

        self.setLayout(self.auto_segmentation_layout)                                   # Setting the layout to the Main Window

    def _make_segmentation_task_selection(self) -> None:
        """
        Protected method to create the segmentation task label and
        combo box for segmentation task selection.
        :rtype: None
        """
        task_label: QtWidgets.QLabel = QtWidgets.QLabel("Segmentation Task:")
        task_label.setStyleSheet(self.style_sheet())
        self.auto_segmentation_layout.addWidget(task_label)

        self.task_combo: QtWidgets.QComboBox = QtWidgets.QComboBox()
        # List of items which can be selected and segmented for
        self.task_combo.addItems([
            "total", "total_mr", "lung_vessels", "body", "body_mr",
            "vertebrae_mr", "hip_implant", "pleural_pericard_effusion", "cerebral_bleed",
            "head_glands_cavities", "head_muscles", "headneck_bones_vessels",
            "headneck_muscles", "liver_vessels", "oculomotor_muscles",
            "lung_nodules", "kidney_cysts", "breasts", "liver_segments",
            "liver_segments_mr", "craniofacial_structures", "abdominal_muscles"
        ]) # Need to figure out if we can make this an Enum
        self.task_combo.setCurrentIndex(0)
        self.task_combo.setToolTip("Select for Segmentation Task to be completed.\n"
                                     "This will be the specific area of the body to create a segment for")
        self.task_combo.setStyleSheet(self.style_sheet())
        self.auto_segmentation_layout.addWidget(self.task_combo)

    def _make_fast_checkbox(self) -> None:
        """
        Protected method to create the checkbox with label to
        determine if the fast option is selected.
        :rtype: None
        """
        self.fast_checkbox: QtWidgets.QCheckBox = QtWidgets.QCheckBox("Fast")
        self.fast_checkbox.setToolTip("When Activated this will allow for faster processing times with the \n"
                                      "downside of lower resolution of the resulting segmentations.\n"
                                      "This option is only available on particular tasks such as total. \n"
                                      "BENEFIT: Faster Segmentations\n"
                                      "DOWNSIDE: Not as Accurate Segmentations")
        self.fast_checkbox.setStyleSheet(self.style_sheet())
        self.auto_segmentation_layout.addWidget(self.fast_checkbox)

    def _make_progress_bar(self) -> None:
        """
        Protected method to create the progress bar label and progress bar.
        To show the user that there is activity when processing and to estimate
        how much longer till the task is completed.
        :rtype: None
        """
        progress_bar_label: QtWidgets.QLabel = QtWidgets.QLabel("\n\nProgress:")
        progress_bar_label.setStyleSheet(self.style_sheet())
        self.auto_segmentation_layout.addWidget(progress_bar_label)

        self.progress_bar: QtWidgets.QProgressBar = QtWidgets.QProgressBar(minimum=0, maximum=100, value=20)
        self.progress_bar.setToolTip("The progress of the task currently being processed.")
        self.progress_bar.setStyleSheet(self.style_sheet())
        self.auto_segmentation_layout.addWidget(self.progress_bar)

    def _make_progress_text(self) -> None:
        """
        Protected method to create the progress text label and progress text box.
        To give the user feedback on what the current activity which is occurring.
        :rtype: None
        """
        progress_text_label: QtWidgets.QLabel = QtWidgets.QLabel("\n\nCurrent Task:")
        progress_text_label.setStyleSheet(self.style_sheet())
        self.auto_segmentation_layout.addWidget(progress_text_label)

        self.progress_text = QtWidgets.QTextEdit()
        self.progress_text.setText("Waiting...")
        self.progress_text.setReadOnly(True)
        self.progress_text.setToolTip("What task the auto-segmentator is currently performing")
        self.progress_text.setStyleSheet(self.style_sheet())
        self.auto_segmentation_layout.addWidget(self.progress_text)

    def _make_start_button(self, button_action: ()) -> None:
        """
        Protected Method to create the start button
        To start the auto-segmentation task which has been selected.
        :param button_action: function
        :rtype: None
        """
        self.start_button: QtWidgets.QPushButton = QtWidgets.QPushButton("Start")
        self.start_button.setObjectName("start_button")
        self.start_button.setStyleSheet(self.style_sheet())
        self.start_button.Alignment = QtCore.Qt.AlignmentFlag.AlignBottom
        # Button Action
        self.start_button.clicked.connect(button_action)
        self.auto_segmentation_layout.addWidget(self.start_button)

    def _start_button_clicked(self) -> None:
        """
        Protected method to be called when the start button is clicked.
        :rtype: None
        """
        #TODO: Add Start functionality
        pass # This will need to call a method or function from another class

    def get_segmentation_task(self) -> str:
        """
        Public Method to retrieve the current selection
        from the segmentation task combo box.
        :rtype: str
        """
        return self.task_combo.currentText()

    def get_fast_value(self) -> bool:
        """
        Public Method to retrieve the balue of the fast checkbox.
        TO see if the fast option has been selected.
        :rtype: bool
        """
        return self.fast_checkbox.isChecked()

    def set_progress_bar_value(self, value: int) -> None:
        """
        Public Method to set the progress bar value.
        To display the estimated completion of the task
        :param value: int
        :rtype: None
        """
        self.progress_bar.setValue(value)

    def set_progress_text(self, text: str) -> None:
        """
        Public Method to set the progress text in the progress text box.
        To display the text to the user of what is currently being performed,
        to inform the user as to the current aspect of the task being performed.
        :param text: str
        :rtype: None
        """
        self.progress_text.setText(text)
