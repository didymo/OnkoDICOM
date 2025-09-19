import functools
import pathlib
from collections.abc import Callable

import pandas
from PySide6 import QtWidgets
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QSizePolicy
from PySide6.QtCore import Qt, QSize

from src.Controller.PathHandler import resource_path
from src.View.StyleSheetReader import StyleSheetReader

class SegmentSelectorWidget(QtWidgets.QWidget):
    """
    Widget for selecting a segments for the Auto-Segmentation feature Window of the Application
    This widget gets its data from the "res/segmentation_list.csv" to which it inputs it
    into the tree as selectable items.

    It then Produces a list of the selected items which chan then be used by other aspects of the application.
    The list is Retrieved though the
    Object.get_segment_list() method
    which returns a list[str]
    """

    def __init__(self, parent=None, data_location="data") -> None:
        """
        Initialisation of the SegmentSelectorWidget.
        Constructs the parent class of QtWidgets.QWidget
        Creates the list for the storage of the selected segments
        Generates Tree
        Sets up the layout of the Widget

        :returns: None
        """

        super(SegmentSelectorWidget, self).__init__(parent)
        self.setStyleSheet(StyleSheetReader().get_stylesheet()) # To style the Widget

        # Class Members
        self._selected_list: list[str] = [] # To store the selected segments

        # Creating Tree using PySide6
        # Nesting methods here to Indicate that each one is intended to feed into each other
        self._selection_tree = self._resize_columns(
            self._enter_tree_data(csv_location=pathlib.Path(data_location)/"segmentation_lists.csv", tree=self._create_selection_tree(
                self._body_section_clicked)))

        # Adding the layout and the Widget to the parent Widget
        layout: QtWidgets.QLayout = QtWidgets.QFormLayout() # Creating Window Layout
        layout.addWidget(self._selection_tree)
        self.setLayout(layout)

    def sizeHint(self) -> QSize:
        """
        Making Concreate Method of the Virtual Method which determine the size of the widget

        :returns: QSize:
        """
        return QSize(400, 600)

    def get_segment_list(self) -> list[str]:
        """
        Returns the list of all the selected items from the Segment selector tree

        :returns: list[str]:
        """
        return self._selected_list

    def _create_selection_tree(self, callback_method: Callable[[QTreeWidgetItem, int], None]) -> QtWidgets.QTreeWidget:
        """
        Creates the Selection Tree for the Widget including styling and the header label
        As well as setting the Size Policy, the number of column and connects the callback method.

        :param callback_method: Callable[[QTreeWidgetItem, int], None]
        :return: QtWidgets.QTreeWidget
        """
        tree: QTreeWidget = QtWidgets.QTreeWidget(self)
        # StyleSheet for tree otherwise spacings between branches are inconsistent
        tree.setStyleSheet(StyleSheetReader().get_stylesheet())
        tree.setHeaderLabels(["Body Section", "Organ Structure"])
        tree.setSizePolicy(QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding))
        tree.setColumnCount(2)
        tree.itemClicked.connect(callback_method) # Call back for when item is clicked
        return tree

    def _enter_tree_data(self,csv_location: pathlib.Path, tree: QTreeWidget) -> QtWidgets.QTreeWidget:
        """
        Gets the Structure Data inf the form of a pandas.DataFrame
        Which is then into the TreeWidget under their respective parents

        :param tree: QtWidgets.QTreeWidget
        :return: QtWidgets.QTreeWidget
        """
        structure_data: pandas.DataFrame = self._get_csv_data(csv_location)
        # Getting the parent names for the organ structures
        for BodySection in structure_data ["BodySection"].unique():
            body_input: QtWidgets.QTreeWidgetItem = self._input_structure(0, BodySection, tree)

            # Getting the Structure list from the Pandas Table
            structure_list: pandas.DataFrame = structure_data.loc[structure_data["BodySection"] == BodySection]
            for StructureName in structure_list.Structure.unique():
                self._input_structure(1, StructureName, body_input)
        return tree

    @functools.lru_cache(maxsize=128, typed=False)
    def _get_csv_data(self, path: pathlib.Path) -> pandas.DataFrame:
        """
        Cached method to get the structure data
        Reads and Extracts the useful columns out of the "data/segmentation_list.csv" file.

        :param path: str
        :returns: pandas.DataFrame
        """
        structure_data_full: pandas.DataFrame = pandas.read_csv(resource_path(path))
        structure_data: pandas.DataFrame = structure_data_full.filter(["BodySection", "Structure"])
        structure_data["BodySection"]: pandas.Series = structure_data["BodySection"].str.strip()
        structure_data["Structure"]: pandas.Series = structure_data["Structure"].str.strip()
        return structure_data

    def _input_structure(self,
                         column: int,
                         structure: str,
                         body_tree: QtWidgets.QTreeWidgetItem | QtWidgets.QTreeWidget
                         ) -> QtWidgets.QTreeWidgetItem:
        """
        Creates a QTreeWidgetItem sets the flags and add the name to the item.
        As well as left pads the names a little with spaces so check boxes and names don't overlap

        :param column: int
        :param structure: str
        :param body_tree: QtWidgets.QTreeWidgetItem | QtWidgets.QTreeWidget
        :return: QtWidgets.QTreeWidgetItem
        """
        structure_input: QTreeWidgetItem = QTreeWidgetItem(body_tree)
        structure_input.setFlags(structure_input.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        structure_input.setCheckState(column, Qt.CheckState.Unchecked)
        # Spaces added here to prevent check box from going over the first letter
        structure_input.setText(column, f"   {structure}")
        return structure_input

    def _resize_columns(self, tree: QTreeWidget) -> QtWidgets.QTreeWidget:
        """
        Goes though each column in the Tree and resizes them so the contents fit the columns

        :param tree: QtWidgets.QTreeWidget
        :return: QtWidgets.QTreeWidget
        """
        for column in range(tree.columnCount()):
            tree.resizeColumnToContents(column)
        return tree

    def _body_section_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """
        Callback method to determine what to do when an item or check box is clicked in the selection tree

        :param item: QtWidgets.QTreeWidgetItem
        :param column: int
        :returns: None
        """
        body_text: str = item.text(column).strip()
        if column == 0:
            self._parent_states(item)
            return
        self._child_states(item, body_text)

    def _parent_states(self, item: QTreeWidgetItem) -> None:
        """
        Determines if check box was checked or unchecked then determines the action it needs to take

        :param item: QtWidgets.QTreeWidgetItem
        :returns: None
        """
        # Adds full body section when the body section is checked
        if item.checkState(0) == Qt.CheckState.Checked:
            self._parent_section_changed(item, Qt.CheckState.Checked)
            return
        # Removes full body section when the body section unchecked
        self._parent_section_changed(item, Qt.CheckState.Unchecked)

    def _child_states(self, item: QTreeWidgetItem, body_text) -> None:
        """
        Determines if check box was checked or unchecked then determines the action it needs to take

        :param item: QtWidgets.QTreeWidgetItem
        :param body_text: str
        :returns: None
        """
        # Adds the specific Structure to the list when checked
        if item.checkState(1) == Qt.CheckState.Checked:
            self._specific_structure_changed(item, body_text, Qt.CheckState.Checked)
            return
        # Removes the specific structure from the list when unchecked
        self._specific_structure_changed(item, body_text, Qt.CheckState.Unchecked)

    def _parent_section_changed(self, item: QTreeWidgetItem, state: Qt.CheckState) -> None:
        """
        Loop to Uncheck or Check each checkbox of child items of a parent Item

        :param item: QtWidgets.QTreeWidgetItem
        :param state: Qt.CheckState
        :returns: None
        """
        for i in range(item.childCount()):
            item.child(i).setCheckState(1, state)
            item_text: str = item.child(i).text(1).strip()
            self._selected_list_add_or_remove(item_text, state)

    def _specific_structure_changed(self, item: QTreeWidgetItem, body_text: str, state: Qt.CheckState) -> None:
        """
        Determines how many of the child objects are checked or Checked
        Changes the parents checkbox state
        adds or removes items from self._selection_list

        :param item: QtWidgets.QTreeWidgetItem
        :param body_text: str
        :param state: Qt.CheckState
        :returns: None
        """
        # Counting the number of checked child boxes
        parent_child_count: int = item.parent().childCount()
        active_count = sum(item.parent().child(i).checkState(1) == Qt.CheckState.Checked for i in range(parent_child_count))
        self._setting_parent_states(item, active_count, parent_child_count)
        self._selected_list_add_or_remove(body_text, state)

    def _setting_parent_states(self, item: QTreeWidgetItem, active_count:int, parent_child_count: int) -> None:
        """
        Sets the state of a parent checkbox for when a child check box has been changed

        :param item: QtWidgets.QTreeWidgetItem
        :param active_count: int
        :param parent_child_count: int
        :returns: None
        """
        if active_count == parent_child_count:
            item.parent().setCheckState(0, Qt.CheckState.Checked)
            return
        if active_count == 0:
            item.parent().setCheckState(0, Qt.CheckState.Unchecked)
            return
        item.parent().setCheckState(0, Qt.CheckState.PartiallyChecked)

    def _selected_list_add_or_remove(self, body_text: str , state: Qt.CheckState) -> None:
        """
        To add or remove an item from the self._selection_list member when a selection has changed

        :param body_text: str
        :param state: Qt.CheckState
        :returns: None
        """
        if state == Qt.CheckState.Checked and body_text not in self._selected_list:
            self._selected_list.append(body_text)
            return
        if state == Qt.CheckState.Unchecked and body_text in self._selected_list:
            self._selected_list.remove(body_text)






