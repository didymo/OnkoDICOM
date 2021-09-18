import webbrowser

from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtCore import Qt

from src.Controller.ActionHandler import ActionHandler
from src.Model.PatientDictContainer import PatientDictContainer


class MenuBar(QtWidgets.QMenuBar):

    def __init__(self, action_handler: ActionHandler):
        QtWidgets.QMenuBar.__init__(self)
        self.action_handler = action_handler
        self.patient_dict_container = PatientDictContainer()
        self.setGeometry(QtCore.QRect(0, 0, 901, 35))
        self.setContextMenuPolicy(Qt.PreventContextMenu)

        # Menu Bar: File, Tools, Export, Help
        self.menu_file = QtWidgets.QMenu()
        self.menu_file.setTitle("File")
        self.addMenu(self.menu_file)

        self.menu_tools = QtWidgets.QMenu()
        self.menu_tools.setTitle("Tools")
        self.addMenu(self.menu_tools)

        self.addMenu(self.action_handler.menu_export)

        # Help button opens OnkoDICOM website
        self.action_help = QtGui.QAction()
        self.action_help.setText("Help")
        self.action_help.triggered.connect(lambda: webbrowser.open("https://onkodicom.com.au/"))

        self.addAction(self.action_help)

        # Add actions to File menu
        self.menu_file.addAction(self.action_handler.action_open)
        self.menu_file.addSeparator()
        if self.patient_dict_container.has_modality('rtss'):
            self.menu_file.addAction(self.action_handler.action_save_structure)
        self.menu_file.addAction(self.action_handler.action_save_as_anonymous)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.action_handler.action_exit)

        # Add actions to Tool menu
        self.menu_tools.addAction(self.action_handler.action_zoom_in)
        self.menu_tools.addAction(self.action_handler.action_zoom_out)
        self.menu_tools.addSeparator()
        self.menu_tools.addMenu(self.action_handler.menu_windowing)
        self.menu_tools.addSeparator()
        self.menu_tools.addAction(self.action_handler.action_transect)
        self.menu_tools.addSeparator()
        self.menu_tools.addAction(self.action_handler.action_add_ons)
