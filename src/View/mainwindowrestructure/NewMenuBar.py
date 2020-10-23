from PyQt5 import QtWidgets, QtCore, QtGui

from src.Model.PatientDictContainer import PatientDictContainer


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

        self.menu_help = QtWidgets.QMenu()
        self.menu_help.setTitle("Help")
        self.addMenu(self.menu_help)

        # Create sub-menu for Windowing
        self.menu_windowing = QtWidgets.QMenu(self.menu_tools)
        self.init_windowing_menu()

        # Add actions to File menu
        self.menu_file.addAction(self.action_handler.action_open)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.action_handler.action_save_as_anonymous)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.action_handler.action_exit)

        # Add actions to Tool menu
        self.menu_tools.addAction(self.action_handler.action_zoom_in)
        self.menu_tools.addAction(self.action_handler.action_zoom_out)
        self.menu_tools.addMenu(self.menu_windowing)
        self.menu_tools.addAction(self.action_handler.action_transect)
        self.menu_tools.addAction(self.action_handler.action_add_ons)

        # Add actions to Export menu
        self.menu_export.addAction(self.action_handler.action_clinical_data_export)
        self.menu_export.addAction(self.action_handler.action_pyradiomics_export)

    def init_windowing_menu(self):
        icon_windowing = QtGui.QIcon()
        icon_windowing.addPixmap(
            QtGui.QPixmap(":/images/Icon/windowing.png"),
            QtGui.QIcon.Normal,
            QtGui.QIcon.On
        )
        self.menu_windowing.setIcon(icon_windowing)
        self.menu_windowing.setTitle("Windowing")

        patient_dict_container = PatientDictContainer()
        dict_windowing = patient_dict_container.get("dict_windowing")

        # Get the right order for windowing names
        names_ordered = sorted(dict_windowing.keys())
        if "Normal" in dict_windowing.keys():
            old_index = names_ordered.index("Normal")
            names_ordered.insert(0, names_ordered.pop(old_index))

        # Create actions for each windowing item
        for name in names_ordered:
            text = str(name)
            print(text)
            action_windowing_item = QtWidgets.QAction()
            action_windowing_item.triggered.connect(
                lambda state, text=name: self.action_handler.windowing_handler(state, text)
            )
            action_windowing_item.setText(text)
            self.menu_windowing.addAction(action_windowing_item)
