from PyQt5 import QtWidgets, QtGui, QtCore

from src.Controller.MainPageActionHandler import MainPageActionHandler


class NewToolBar(QtWidgets.QToolBar):

    def __init__(self, action_handler: MainPageActionHandler):
        QtWidgets.QToolBar.__init__(self)
        self.action_handler = action_handler
        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.setMovable(False)

        # Drop-down list for Windowing button on toolbar
        self.button_windowing = QtWidgets.QToolButton()
        self.button_windowing.setMenu(self.action_handler.menu_windowing)
        self.button_windowing.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.button_windowing.setIcon(self.action_handler.icon_windowing)

        # Drop-down list for Export button on toolbar
        self.button_export = QtWidgets.QToolButton()
        self.button_export.setMenu(self.action_handler.menu_export)
        self.button_export.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        self.button_export.setIcon(self.action_handler.icon_export)

        # Spacer for the toolbar
        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        spacer.setFocusPolicy(QtCore.Qt.NoFocus)

        # Add actions to toolbar
        self.addAction(self.action_handler.action_open)
        self.addSeparator()
        self.addAction(self.action_handler.action_zoom_in)
        self.addAction(self.action_handler.action_zoom_out)
        self.addSeparator()
        self.addWidget(self.button_windowing)
        self.addSeparator()
        self.addAction(self.action_handler.action_transect)
        self.addSeparator()
        self.addAction(self.action_handler.action_add_ons)
        self.addWidget(spacer)
        self.addWidget(self.button_export)
        self.addAction(self.action_handler.action_save_as_anonymous)
