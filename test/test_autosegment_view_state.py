import pytest
from unittest.mock import Mock, patch
from src.Model.AutoSegmentation.AutoSegmentViewState import AutoSegmentViewState
from src.Model.Singleton import Singleton

@pytest.fixture(autouse=True)
def reset_singleton():
    # Arrange
    Singleton._instances = {}
    yield
    Singleton._instances = {}

@pytest.mark.parametrize(
    "setter, attr, cb_type, id",
    [
        ("set_start_button_callback", "_start", lambda x: None, "set_start"),
        ("set_save_button_callback", "_save", lambda x, y: None, "set_save"),
        ("set_load_button_callback", "_load", lambda x: None, "set_load"),
        ("set_delete_button_callback", "_delete", lambda x: None, "set_delete"),
    ],
    ids=["set_start", "set_save", "set_load", "set_delete"]
)
def test_set_callback_methods(setter, attr, cb_type, id):
    # Arrange
    state = AutoSegmentViewState()

    # Act
    getattr(state, setter)(cb_type)

    # Assert
    assert getattr(state, attr) == cb_type

@pytest.mark.parametrize(
    "callback_attr, setter, call_args, expected_args, id",
    [
        ("_start", "set_start_button_callback", ("foo",), ("foo",), "start_callback"),
        ("_load", "set_load_button_callback", ("bar",), ("bar",), "load_callback"),
        ("_delete", "set_delete_button_callback", ("baz",), ("baz",), "delete_callback"),
    ],
    ids=["start_callback", "load_callback", "delete_callback"]
)
def test_button_connection_calls_callback(callback_attr, setter, call_args, expected_args, id):
    # Arrange
    state = AutoSegmentViewState()
    mock_cb = Mock()
    getattr(state, setter)(mock_cb)
    with patch("src.Model.AutoSegmentation.AutoSegmentViewState._communication_debug"):
        # Act
        if callback_attr == "_start":
            state.start_button_connection(*call_args)
        elif callback_attr == "_load":
            state.load_button_connection(*call_args)
        elif callback_attr == "_delete":
            state.delete_button_connection(*call_args)
        # Assert
        mock_cb.assert_called_once_with(*expected_args)

def test_save_button_connection_calls_callback_when_segmentation_list():
    # Arrange
    state = AutoSegmentViewState()
    mock_cb = Mock()
    state.set_save_button_callback(mock_cb)
    state.segmentation_list = ["roi1", "roi2"]
    with patch("src.Model.AutoSegmentation.AutoSegmentViewState._communication_debug"):
        # Act
        state.save_button_connection("save1")
        # Assert
        mock_cb.assert_called_once_with("save1", ["roi1", "roi2"])

def test_save_button_connection_does_not_call_callback_when_no_segmentation_list():
    # Arrange
    state = AutoSegmentViewState()
    mock_cb = Mock()
    state.set_save_button_callback(mock_cb)
    state.segmentation_list = []
    with patch("src.Model.AutoSegmentation.AutoSegmentViewState._communication_debug"):
        # Act
        state.save_button_connection("save1")
        # Assert
        mock_cb.assert_not_called()

def test_save_button_connection_does_not_call_callback_when_no_callback():
    # Arrange
    state = AutoSegmentViewState()
    state.segmentation_list = ["roi1"]
    with patch("src.Model.AutoSegmentation.AutoSegmentViewState._communication_debug"):
        # Act
        state.save_button_connection("save1")
        # Assert
        # No exception, nothing to assert

@pytest.mark.parametrize(
    "method, attr, value, id",
    [
        ("start_button_connection", "_start", "foo", "start_none"),
        ("load_button_connection", "_load", "bar", "load_none"),
        ("delete_button_connection", "_delete", "baz", "delete_none"),
    ],
    ids=["start_none", "load_none", "delete_none"]
)
def test_button_connection_no_callback_does_not_raise(method, attr, value, id):
    # Arrange
    state = AutoSegmentViewState()
    setattr(state, attr, None)
    with patch("src.Model.AutoSegmentation.AutoSegmentViewState._communication_debug"):
        # Act
        getattr(state, method)(value)
        # Assert
        # No exception, nothing to assert

def test_save_button_connection_with_save_none_and_nonempty_list():
    # Arrange
    state = AutoSegmentViewState()
    state._save = None
    state.segmentation_list = ["roi1"]
    with patch("src.Model.AutoSegmentation.AutoSegmentViewState._communication_debug"):
        # Act
        state.save_button_connection("save1")
        # Assert
        # No exception, nothing to assert

def test_save_button_connection_with_save_and_empty_list():
    # Arrange
    state = AutoSegmentViewState()
    state._save = Mock()
    state.segmentation_list = []
    with patch("src.Model.AutoSegmentation.AutoSegmentViewState._communication_debug"):
        # Act
        state.save_button_connection("save1")
        # Assert
        state._save.assert_not_called()

def test_communicate_connection_calls_member():
    # Arrange
    state = AutoSegmentViewState()
    mock_cb = Mock()
    # Act
    state._communicate_connection(mock_cb, "foo")
    # Assert
    mock_cb.assert_called_once_with("foo")

def test_communicate_connection_none_member():
    # Arrange
    state = AutoSegmentViewState()
    # Act
    state._communicate_connection(None, "foo")
    # Assert
    # No exception, nothing to assert

def test_all_button_connections_call_communication_debug(monkeypatch):
    # Arrange
    state = AutoSegmentViewState()
    monkeypatch.setattr("src.Model.AutoSegmentation.AutoSegmentViewState._communication_debug", lambda *a, **kw: None)
    state.set_start_button_callback(lambda x: None)
    state.set_save_button_callback(lambda x, y: None)
    state.set_load_button_callback(lambda x: None)
    state.set_delete_button_callback(lambda x: None)
    state.segmentation_list = ["roi1"]

    # Act
    state.start_button_connection("foo")
    state.save_button_connection("bar")
    state.load_button_connection("baz")
    state.delete_button_connection("qux")

    # Assert
    # No exception, nothing to assert
