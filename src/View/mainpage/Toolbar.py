from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QToolBar, QToolButton, QWidget, QSizePolicy

from src.Controller.ActionHandler import ActionHandler
from src.Model.PatientDictContainer import PatientDictContainer


class Toolbar(QToolBar):

    def __init__(self, action_handler: ActionHandler):
        QToolBar.__init__(self)
        self.action_handler = action_handler
        self.patient_dict_container = PatientDictContainer()
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setMovable(False)
        self.setFloatable(False)
        self.setContextMenuPolicy(Qt.PreventContextMenu)

        # Drop-down list for Windowing button on toolbar
        self.button_windowing = QToolButton()
        self.button_windowing.setMenu(self.action_handler.menu_windowing)
        self.button_windowing.setPopupMode(QToolButton.InstantPopup)
        self.button_windowing.setIcon(self.action_handler.icon_windowing)

        # Drop-down list for Export button on toolbar
        self.button_export = QToolButton()
        self.button_export.setMenu(self.action_handler.menu_export)
        self.button_export.setPopupMode(QToolButton.InstantPopup)
        self.button_export.setIcon(self.action_handler.icon_export)

        # Spacer for the toolbar
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        spacer.setFocusPolicy(Qt.NoFocus)

        # Add actions to toolbar
        self.addAction(self.action_handler.action_open)
        self.addSeparator()
        self.addAction(self.action_handler.action_zoom_out)
        self.addAction(self.action_handler.action_zoom_in)
        self.addSeparator()
        self.addWidget(self.button_windowing)
        self.addSeparator()
        self.addAction(self.action_handler.action_transect)
        self.addSeparator()
        self.addAction(self.action_handler.action_suv2roi)
        self.addSeparator()
        self.addAction(self.action_handler.action_add_ons)
        self.addWidget(spacer)
        self.addWidget(self.button_export)
        self.addAction(self.action_handler.action_save_as_anonymous)
        if self.patient_dict_container.has_modality('rtss'):
            self.addAction(self.action_handler.action_save_structure)
