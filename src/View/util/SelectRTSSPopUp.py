import platform

from pydicom import dcmread

from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import QDialog, QLabel, QWidget, QPushButton, \
    QHBoxLayout, QVBoxLayout, QCheckBox, QScrollArea, QButtonGroup

from src.Model.DICOMStructure import Series
from src.Controller.PathHandler import resource_path

"""
This Class handles the RTSS Pop Up when users need to select a RTSS from a list
of RTSSs attached to the selected image set to proceed.       
"""


class SelectRTSSPopUp(QDialog):
    signal_rtss_selected = QtCore.Signal(Series)

    def __init__(self, existing_rtss):
        QDialog.__init__(self)

        if platform.system() == 'Darwin':
            self.stylesheet_path = "res/stylesheet.qss"
        else:
            self.stylesheet_path = "res/stylesheet-win-linux.qss"
        stylesheet = open(resource_path(self.stylesheet_path)).read()
        self.setStyleSheet(stylesheet)

        self.setWindowTitle("Multiple RTSTRUCTs detected!")
        self.setMinimumSize(350, 180)

        self.icon = QtGui.QIcon()
        self.icon.addPixmap(
            QtGui.QPixmap(resource_path("res/images/icon.ico")),
            QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(self.icon)

        self.explanation_text = QLabel("Multiple RTSTRUCTs attached to the "
                                       "selected image set have been "
                                       "identified."
                                       "\nPlease select 1 "
                                       "RTSTRUCTs to continue!")

        # Create scrolling area widget to contain the content.
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.scroll_area_content = QWidget(self.scroll_area)
        self.scroll_area.ensureWidgetVisible(self.scroll_area_content)

        # Create layout for checkboxes
        self.layout_content = QVBoxLayout(self.scroll_area_content)
        self.layout_content.setContentsMargins(5, 5, 5, 5)
        self.layout_content.setSpacing(0)
        self.layout_content.setAlignment(QtCore.Qt.AlignTop
                                         | QtCore.Qt.AlignTop)

        # Add all the attached RTSSs as checkboxes
        self.checkbox_group = QButtonGroup()
        self.checkbox_group.setExclusive(True)
        for i in range(len(existing_rtss)):
            checkbox = QCheckBox()
            checkbox.rtss = existing_rtss[i]
            rtss = dcmread(checkbox.rtss.get_files()[0])
            checkbox.setFocusPolicy(QtCore.Qt.NoFocus)
            checkbox.setText("Series: %s (%s, %s %s)" % (
                checkbox.rtss.series_description,
                checkbox.rtss.get_series_type(),
                len(rtss.StructureSetROISequence),
                "ROIs" if len(rtss.StructureSetROISequence) > 1 else "ROI"
            ))
            self.checkbox_group.addButton(checkbox)
            self.layout_content.addWidget(checkbox)
        self.checkbox_group.buttonClicked.connect(self.on_checkbox_clicked)

        # Create a cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.on_cancel_clicked)

        # Create a continue button
        self.continue_button = QPushButton("Continue Process")
        self.continue_button.setDisabled(True)
        self.continue_button.clicked.connect(self.on_continue_clicked)

        # Create a widget to contain cancel and continue buttons
        self.button_area = QWidget()
        self.button_layout = QHBoxLayout()
        self.button_layout.addWidget(self.cancel_button)
        self.button_layout.addWidget(self.continue_button)
        self.button_area.setLayout(self.button_layout)

        # Add all components to a vertical layout
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.explanation_text)
        self.layout.addWidget(self.scroll_area)
        self.layout.addWidget(self.button_area)
        self.setLayout(self.layout)

    def on_checkbox_clicked(self, checkbox):
        """
        function to control selected rtss
        """
        self.continue_button.setDisabled(False)
        self.selected_rtss = checkbox.rtss

    def on_continue_clicked(self):
        """
        function to continue the process
        """
        # Emit the selected RTSS
        self.signal_rtss_selected.emit(self.selected_rtss)
        self.close()

    def on_cancel_clicked(self):
        """
        function to cancel the operation
        """
        self.close()


