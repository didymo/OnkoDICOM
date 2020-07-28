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
