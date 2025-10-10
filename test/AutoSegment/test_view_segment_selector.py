import pytest
import pathlib
from PySide6.QtWidgets import QTreeWidgetItem, QTreeWidget

from src.View.AutoSegmentation.SegmentSelectorWidget import SegmentSelectorWidget


@pytest.fixture(scope="function")
def selection_object() -> SegmentSelectorWidget:
    """
    to create the object run tests with a list with no values on
    This is so we don't need to create the object in every test

    :return: SegmentSelectorWidget
    """
    return SegmentSelectorWidget()

@pytest.fixture(scope="function")
def tree_widget_item() -> QTreeWidgetItem:
    """
    To create a tree widget item with children to run tests on

    :return: QTreeWidget
    """
    test_parent: QTreeWidgetItem = QTreeWidgetItem()
    test_parent.setText(0, "parent")
    test_child1: QTreeWidgetItem = QTreeWidgetItem(test_parent)
    test_child1.setText(1,"child1")
    test_child2: QTreeWidgetItem = QTreeWidgetItem(test_parent)
    test_child2.setText(1,"child2")

    return test_parent

def test_object_created(selection_object: SegmentSelectorWidget) -> None:
    """
    Test to show object is created

    :return: None
    """
    assert selection_object is not None

def test_object_correct_type(selection_object: SegmentSelectorWidget) -> None:
    """
    Test to show the object is the correct type

    :return: None
    """
    assert type(selection_object) is SegmentSelectorWidget

def test_size_hint(selection_object: SegmentSelectorWidget) -> None:
    """
    Test to show the sizeHint of the object exists and returns valid values for a sizeHint

    :return: None
    """
    size = selection_object.sizeHint()
    assert type(size.height()) is int
    assert type(size.width()) is int

def test_create_selection_tree(selection_object: SegmentSelectorWidget) -> None:
    """
    Test to show the selection tree is created

    :return: None
    """
    assert type(selection_object._create_selection_tree(selection_object._body_section_clicked))
    assert type(selection_object._create_selection_tree(selection_object._body_section_clicked)) is not None

def test_get_segment_list(selection_object: SegmentSelectorWidget) -> None:
    """
    Test to show an empty selection list  can be can have value added to it

    :return: None
    """
    assert selection_object.get_segment_list() == []
    assert not selection_object._selected_list_add_or_remove("skull", 2)
    assert selection_object.get_segment_list() == ["skull"]

@pytest.fixture(scope="function")
def test_add_selection(selection_object: SegmentSelectorWidget) -> SegmentSelectorWidget:
    """
    Testing if adding a selection to empty list adds the value to the selection list

    :return: None
    """
    assert selection_object.get_segment_list() == []
    assert not selection_object._selected_list_add_or_remove("skull", 2)
    assert selection_object.get_segment_list()
    assert selection_object.get_segment_list() != ["skul"]
    assert selection_object.get_segment_list() != ["kull"]
    assert selection_object.get_segment_list() != ["skll"]
    assert selection_object.get_segment_list() != ["skulll"]
    assert selection_object.get_segment_list() == ["skull"]
    assert not selection_object._selected_list_add_or_remove("brain", 3)
    assert selection_object.get_segment_list() != ["skull"]
    assert selection_object.get_segment_list() == ["skull", "brain"]

    return selection_object

def test_remove_selection(test_add_selection: SegmentSelectorWidget) -> None:
    """
    Testing if adding a selection to empty list adds the value to the selection list
    test_add_selection test which adds an item to the list to just test removing item from the list

    :return: None
    """
    assert test_add_selection.get_segment_list() != []
    assert test_add_selection.get_segment_list() == ["skull", "brain"]
    assert not test_add_selection._selected_list_add_or_remove("skull", 0)
    assert test_add_selection.get_segment_list() != ["skull", "brain"]
    assert test_add_selection.get_segment_list() == ["brain"]
    assert not test_add_selection._selected_list_add_or_remove("brain", -5)
    assert test_add_selection.get_segment_list() != ["brain"]
    assert test_add_selection.get_segment_list() != ["skull"]
    assert test_add_selection.get_segment_list() == []
    assert not test_add_selection._selected_list_add_or_remove("brain", -5)
    assert not test_add_selection._selected_list_add_or_remove("not_brain", -5)

def test_enter_tree_data(selection_object) -> None:
    """
    Test to see if entering data into tree works correctly
    This clears the options in the tree converting all items to None
    Tests to ensure that the QTreeWidget has no item at position 0,0
    Loads the data into the tree again
    Tests to see if there is an object at position 0,0

    :return: None
    """
    assert selection_object._selection_tree.itemAt(0, 0) is not None
    assert not selection_object._selection_tree.clear()
    assert selection_object._selection_tree.itemAt(0, 0) is None
    assert selection_object._enter_tree_data(
        csv_location=pathlib.Path("data/csv") / "segmentation_lists.csv",
        tree=selection_object._selection_tree)
    assert selection_object._selection_tree.itemAt(0, 0) is not None

def test_get_csv_data(selection_object) -> None:
    """
    Test to determine if data can be read from a csv file

    :return: None
    """
    dataframe = selection_object._get_csv_data(path=pathlib.Path("data/csv") / "segmentation_lists.csv")
    # DataFrame.any().any() the first any is for any series in the dataframe the second any is any value in the dataframe
    assert dataframe.any().any()
    assert not dataframe.empty
    assert dataframe.shape[0] > 0
    assert dataframe.shape[1] > 0
    assert not dataframe.shape[0] < 0
    assert not dataframe.shape[1] < 0

def test_load_selections(selection_object) -> None:
    """
    Testing to see if multiple selections can be loaded into the selection tree

    :return: None
    """
    assert selection_object.get_segment_list() == []
    assert not selection_object.load_selections(["skull", "brain"])
    assert selection_object.get_segment_list() == ["skull", "brain"]
    assert not selection_object.get_segment_list() == []

def test_uniform_selection(selection_object) -> None:
    """
    Test to for setting a uniform selection works correctly in every state

    :return: None
    """
    assert not selection_object._uniform_selection(-3)
    assert not selection_object._uniform_selection(-2)
    assert not selection_object._uniform_selection(-1)
    assert not selection_object._uniform_selection(0)
    assert not selection_object._uniform_selection(1)
    assert not selection_object._uniform_selection(2)
    assert not selection_object._uniform_selection(3)

def test_select_all(selection_object) -> None:
    """
    Test to ensure that the select all method will run without errors occurring

    :return: None
    """
    assert not selection_object.select_all()

def test_deselect_all(selection_object):
    """
    Test to ensure that the deselect all method will run without errors occurring

    :return: None
    """
    assert not selection_object.deselect_all()

def test_resize_columns(selection_object) -> None:
    """
    Test to if resizing each of the columns int hte selection Tree works correctly

    :return: None
    """
    assert selection_object._resize_columns(selection_object._selection_tree)

def test_input_structure(selection_object, tree_widget_item) -> None:
    """
    Testing is adding a Tree Widget item to a parent Tree Widget item works correctly

    :param selection_object: SegmentSelectorWidget
    :param tree_widget_item: QtWidgets.QTreeWidgetItem
    :return: None
    """
    assert not tree_widget_item.child(2)
    assert selection_object._input_structure(1, "child3", tree_widget_item)
    assert tree_widget_item.child(2)
    assert tree_widget_item.child(2).text(1).strip() == "child3"

def test_body_section_clicked(selection_object, tree_widget_item) -> None:
    pass

def test_parent_states(selection_object, tree_widget_item) -> None:
    pass

def test_child_states(selection_object, tree_widget_item) -> None:
    pass

def test_parent_section_changed(selection_object, tree_widget_item) -> None:
    pass

def test_specific_structure_changed(selection_object, tree_widget_item) -> None:
    pass

def test_setting_parent_states(selection_object, tree_widget_item) -> None:
    pass






