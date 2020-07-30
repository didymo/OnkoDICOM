from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt
from fuzzywuzzy import fuzz, process

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

    def getOrganNames(self):
        organNames = []
        with open("src/data/csv/organName.csv", 'r') as file:
            for line in file:
                organName = line.split(',', 1)[0]  # add nsplits = 1 for efficiency
                organNames.append(organName)

        del organNames[0] # removing "Standard name"

        return organNames

    def roiSuggestions(self):
        """
        Get the top 3 suggestions for the selected ROI based on string matching with standard ROIs provided in .csv format.

        :return: two dimensional list with ROI name and string match percent
        i.e [('MANDIBLE', 100), ('SUBMAND_L', 59), ('LIVER', 51)]
        """

        # TODO extra conditions need to be added for a more accurate suggestion
        roi_list = self.structure_tab.standard_organ_names + self.structure_tab.standard_volume_names
        suggestions = process.extract(self.text, roi_list, limit=3) # will get the top 3 matches

        return suggestions


    def contextMenuEvent(self, event):
        """
        This function is called whenever the QWidget is right clicked.
        This creates a right click menu for the widget.
        """
        menu = QtWidgets.QMenu(self)
        menu.setStyleSheet("QMenu::item::selected {background-color: #9370DB}")
        menu.addAction(self.text)
        rename_action = menu.addAction("Rename")
        menu.addSeparator()

        suggestions = self.roiSuggestions()
        suggested_action1 = menu.addAction(suggestions[0][0])
        suggested_action2 = menu.addAction(suggestions[1][0])
        suggested_action3 = menu.addAction(suggestions[2][0])

        action = menu.exec_(self.mapToGlobal(event.pos()))
        if action == rename_action:
            print("Rename")
        elif action == suggested_action1:
            print("1")
            print(type(suggestions))
        elif action == suggested_action2:
            print("2")
        elif action == suggested_action3:
            print("3")
