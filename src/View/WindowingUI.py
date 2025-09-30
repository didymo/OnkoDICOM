from PySide6 import QtWidgets, QtCore
from PySide6.QtWidgets import QDialog, QLabel, QVBoxLayout, QHBoxLayout
from PySide6.QtGui import QIcon, QPixmap

from src.Controller.PathHandler import resource_path

from src.Model.PTCTDictContainer import PTCTDictContainer
from src.Model.MovingDictContainer import MovingDictContainer

from src.Model.Windowing import windowing_model
from src.View.StyleSheetReader import StyleSheetReader


class Windowing(QDialog):
    done_signal = QtCore.Signal()

    def __init__(self, text):
        """
        Initialises the widget
        :param text: the window selected
        """
        super(Windowing, self).__init__()

        self.pt_ct_dict_container = PTCTDictContainer()
        self.moving_dict_container = MovingDictContainer()

        window_icon = QIcon()
        window_icon.addPixmap(QPixmap(resource_path("res/images/icon.ico")),
                              QIcon.Normal, QIcon.Off)

        self.setWindowIcon(window_icon)
        self.setStyleSheet(StyleSheetReader().get_stylesheet())

        self.text = text

        self.layout = QVBoxLayout()
        self.buttons = QHBoxLayout()

        self.setWindowTitle("Select Views")

        self.label = QLabel("Select views to apply windowing to:")
        self.normal = QtWidgets.QCheckBox("DICOM View")
        self.pet = QtWidgets.QCheckBox("PET/CT: PET")
        self.ct = QtWidgets.QCheckBox("PET/CT: CT")
        self.fusion = QtWidgets.QCheckBox("Image Fusion")
        self.confirm = QtWidgets.QPushButton("Confirm")
        self.cancel = QtWidgets.QPushButton("Cancel")

        self.confirm.clicked.connect(self.confirmed)
        self.confirm.setProperty("QPushButtonClass", "success-button")
        self.cancel.clicked.connect(self.exit_button)
        self.cancel.setProperty("QPushButtonClass", "fail-button")

        self.buttons.addWidget(self.cancel)
        self.buttons.addWidget(self.confirm)

        self.layout.addWidget(self.label)
        self.layout.addWidget(self.normal)
        if not self.pt_ct_dict_container.is_empty():
            self.layout.addWidget(self.pet)
            self.layout.addWidget(self.ct)
        if not self.moving_dict_container.is_empty():
            self.layout.addWidget(self.fusion)
        self.layout.addLayout(self.buttons)

        self.setLayout(self.layout)

    def confirmed(self):
        """
        Triggers when confirm button is clicked
        """
        send = [
            self.normal.isChecked(),
            self.pet.isChecked(),
            self.ct.isChecked(),
            self.fusion.isChecked()]
        windowing_model(self.text, send)
        self.cleanup()
        self.done_signal.emit()

    def set_window(self, text):
        """
        Sets the windowing option
        """
        self.text = text

    def exit_button(self):
        """
        Triggers on exit
        """
        self.cleanup()

    def cleanup(self):
        """
        Resets window for next use
        """
        self.normal.setChecked(False)
        self.pet.setChecked(False)
        self.ct.setChecked(False)
        self.fusion.setChecked(False)
        self.close()
