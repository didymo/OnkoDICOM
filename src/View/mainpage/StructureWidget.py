from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtCore import Qt
from fuzzywuzzy import process

from src.Model.PatientDictContainer import PatientDictContainer
from src.View.mainpage.RenameROIWindow import RenameROIWindow


class StructureWidget(QtWidgets.QWidget):
    structure_renamed = QtCore.Signal(tuple)  # (new_dataset, change_description)

    def __init__(self, roi_id, color, text, structure_tab):
        super(StructureWidget, self).__init__()

        patient_dict_container = PatientDictContainer()
        self.dataset_rtss = patient_dict_container.get("dataset_rtss")
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
        checkbox.clicked.connect(self.checkbox_clicked)
        if text in structure_tab.standard_organ_names or text in structure_tab.standard_volume_names:
            self.standard_name = True
            checkbox.setStyleSheet("font: 10pt \"Laksaman\";")
        else:
            self.standard_name = False
            checkbox.setStyleSheet("font: 10pt \"Laksaman\"; color: red;")
        for item in structure_tab.standard_volume_names:  # Any suffix number will still be considered standard.
            if text.startswith(item):
                self.standard_name = True
                checkbox.setStyleSheet("font: 10pt \"Laksaman\";")
        checkbox.setText(text)
        self.layout.addWidget(checkbox)

        self.layout.setAlignment(Qt.AlignLeft)

        self.setLayout(self.layout)

    def checkbox_clicked(self, checked):
        self.structure_tab.structure_checked(checked, self.roi_id)

    def roi_suggestions(self):
        """
        Get the top 3 suggestions for the selected ROI based on string matching with standard ROIs provided in .csv
        format.

        :return: two dimensional list with ROI name and string match percent
        i.e [('MANDIBLE', 100), ('SUBMAND_L', 59), ('LIVER', 51)]
        """

        roi_list = self.structure_tab.standard_organ_names + self.structure_tab.standard_volume_names
        suggestions = process.extract(self.text, roi_list, limit=3)  # will get the top 3 matches

        return suggestions

    def contextMenuEvent(self, event):
        """
        This function is called whenever the QWidget is right clicked.
        This creates a right click menu for the widget.
        """
        # Part 1: Construct context menu
        menu = QtWidgets.QMenu(self)
        menu.setStyleSheet("QMenu::item::selected {background-color: #9370DB}")
        rename_action = menu.addAction("Rename")

        if not self.standard_name:
            menu.addSeparator()

            suggestions = self.roi_suggestions()
            suggested_action1 = menu.addAction(suggestions[0][0])
            suggested_action2 = menu.addAction(suggestions[1][0])
            suggested_action3 = menu.addAction(suggestions[2][0])

        # Part 2: Determine action taken
        action = menu.exec(self.mapToGlobal(event.pos()))
        if action == rename_action:
            rename_window = RenameROIWindow(self.structure_tab.standard_volume_names,
                                            self.structure_tab.standard_organ_names,
                                            self.dataset_rtss,
                                            self.roi_id, self.text, self.structure_renamed)
            rename_window.exec_()

        if not self.standard_name:
            if action == suggested_action1:
                rename_window = RenameROIWindow(self.structure_tab.standard_volume_names,
                                                self.structure_tab.standard_organ_names,
                                                self.dataset_rtss,
                                                self.roi_id, self.text, self.structure_renamed, suggestions[0][0])
                rename_window.exec_()
            elif action == suggested_action2:
                rename_window = RenameROIWindow(self.structure_tab.standard_volume_names,
                                                self.structure_tab.standard_organ_names,
                                                self.dataset_rtss,
                                                self.roi_id, self.text, self.structure_renamed, suggestions[1][0])
                rename_window.exec_()
            elif action == suggested_action3:
                rename_window = RenameROIWindow(self.structure_tab.standard_volume_names,
                                                self.structure_tab.standard_organ_names,
                                                self.dataset_rtss,
                                                self.roi_id, self.text, self.structure_renamed, suggestions[2][0])
                rename_window.exec_()
