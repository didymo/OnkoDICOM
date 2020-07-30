from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt


class StructureWidget(QtWidgets.QWidget):

    def __init__(self, roi_id, color, text, structure_tab):
        super(StructureWidget, self).__init__()

        self.roi_id = roi_id
        self.color = color
        self.text = text
        self.structure_tab = structure_tab
        self.standard_name = None
        self.layout = QtWidgets.QHBoxLayout()

        # Create color square
        color_square_label = QtWidgets.QLabel()
        color_square_pix = QtGui.QPixmap(15, 15)
        color_square_pix.fill(self.color)
        color_square_label.setPixmap(color_square_pix)
        self.layout.addWidget(color_square_label)

        # Create checkbox
        checkbox = QtWidgets.QCheckBox()
        checkbox.setFocusPolicy(QtCore.Qt.NoFocus)
        checkbox.clicked.connect(lambda state, text=roi_id: structure_tab.structure_checked(state, text))
        if text in structure_tab.standard_organ_names or text in structure_tab.standard_volume_names:
            self.standard_name = True
            checkbox.setStyleSheet("font: 10pt \"Laksaman\";")
        else:
            self.standard_name = False
            checkbox.setStyleSheet("font: 10pt \"Laksaman\"; color: red;")
        checkbox.setText(text)
        self.layout.addWidget(checkbox)

        self.layout.setAlignment(Qt.AlignLeft)

        self.setLayout(self.layout)

    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu(self)
        menu.setStyleSheet("QMenu::item::selected { background-color: #9370DB; }")

        menu.addAction(self.text)
        rename_action = menu.addAction("Rename")

        # If the structure name is not in the list of standard names, then add some name suggestions to the menu
        if not self.standard_name:
            menu.addSeparator()
            suggested_action1 = menu.addAction("Suggestion 1")
            suggested_action2 = menu.addAction("Suggestion 2")
            suggested_action3 = menu.addAction("Suggestion 3")

        action = menu.exec_(self.mapToGlobal(event.pos()))
        if action == rename_action:
            print("Rename")

        if not self.standard_name:
            if action == suggested_action1:
                print("1")
            elif action == suggested_action2:
                print("2")
            elif action == suggested_action3:
                print("3")
