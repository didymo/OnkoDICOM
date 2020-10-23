import webbrowser

from PyQt5 import QtWidgets, QtCore, QtGui

from src.Model.PatientDictContainer import PatientDictContainer


# TODO this class needs to be able to recognise when an RTSTRUCT/DVH is present, and add new actions accordingly
class NewMenuBar(QtWidgets.QMenuBar):

    def __init__(self, action_handler):
        QtWidgets.QMenuBar.__init__(self)
        self.action_handler = action_handler
        self.setGeometry(QtCore.QRect(0, 0, 901, 35))

        # Menu Bar: File, Tools, Export, Help
        self.menu_file = QtWidgets.QMenu()
        self.menu_file.setTitle("File")
        self.addMenu(self.menu_file)

        self.menu_tools = QtWidgets.QMenu()
        self.menu_tools.setTitle("Tools")
        self.addMenu(self.menu_tools)

        self.menu_export = QtWidgets.QMenu()
        self.menu_export.setTitle("Export")
        self.addMenu(self.menu_export)

        # Help button opens OnkoDICOM website
        self.action_help = QtWidgets.QAction()
        self.action_help.setText("Help")
        self.action_help.triggered.connect(lambda: webbrowser.open("https://onkodicom.com.au/"))

        self.addAction(self.action_help)

        # Add actions to File menu
        self.menu_file.addAction(self.action_handler.action_open)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.action_handler.action_save_as_anonymous)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.action_handler.action_exit)

        # Add actions to Tool menu
        self.menu_tools.addAction(self.action_handler.action_zoom_in)
        self.menu_tools.addAction(self.action_handler.action_zoom_out)
        self.menu_tools.addMenu(self.action_handler.menu_windowing)
        self.menu_tools.addAction(self.action_handler.action_transect)
        self.menu_tools.addAction(self.action_handler.action_add_ons)

        # Add actions to Export menu
        self.menu_export.addAction(self.action_handler.action_clinical_data_export)
        self.menu_export.addAction(self.action_handler.action_pyradiomics_export)
