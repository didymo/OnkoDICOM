from PyQt5 import QtWidgets, QtCore


class NewMenuBar(QtWidgets.QMenuBar):

    def __init__(self, action_handler):
        QtWidgets.QMenuBar.__init__(self)
        self.action_handler = action_handler
        self.setGeometry(QtCore.QRect(0, 0, 901, 35))

        # Menu Bar: File, Edit, Tools, Help
        self.menu_file = QtWidgets.QMenu()
        self.menu_file.setTitle("File")
        self.addMenu(self.menu_file)

        # Create sub-menu for File
        self.menu_file.addAction(self.action_handler.action_open)
