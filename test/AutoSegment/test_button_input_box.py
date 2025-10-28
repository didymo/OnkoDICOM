import pytest
from unittest.mock import Mock, patch
from PySide6.QtWidgets import QApplication

from src.View.AutoSegmentation.ButtonInputBox import ButtonInputBox

@pytest.fixture(scope="module", autouse=True)
def qapp():
    # Arrange
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app

@pytest.mark.parametrize(
    "text_box, reversed_buttons, delete_word, input_text, expected_typed, id",
    [
        (False, False, None, "Prompt", "", "no_textbox_no_delete"),
        (True, False, None, "Prompt", "userinput", "textbox_no_delete"),
        (True, True, None, "Prompt", "userinput", "textbox_reversed"),
        (False, False, "delword", "Prompt", "delword", "no_textbox_with_delete"),
        (True, False, "delword", "Prompt", "delword", "textbox_with_delete"),
    ],
    ids=[
        "no_textbox_no_delete",
        "textbox_no_delete",
        "textbox_reversed",
        "no_textbox_with_delete",
        "textbox_with_delete"
    ]
)
def test_positive_action_various_cases(text_box, reversed_buttons, delete_word, input_text, expected_typed, id, qapp):
    # Arrange
    send_mock = Mock()
    close_mock = Mock()
    with patch("src.View.AutoSegmentation.ButtonInputBox.StyleSheetReader.get_stylesheet", return_value=""), \
         patch("src.View.AutoSegmentation.ButtonInputBox.setup_window"):
        box = ButtonInputBox(
            input_text=input_text,
            positive_action=send_mock,
            negative_action=close_mock,
            text_box=text_box,
            reversed_buttons=reversed_buttons,
            delete_word=delete_word
        )
        if text_box and not delete_word:
            # Simulate user typing in the QLineEdit
            box.text.setText("userinput")

        # Act
        box._positive_action()

        # Assert
        send_mock.assert_called_once_with(expected_typed)

def test_negative_action_calls_close(qapp):
    # Arrange
    send_mock = Mock()
    close_mock = Mock()
    with patch("src.View.AutoSegmentation.ButtonInputBox.StyleSheetReader.get_stylesheet", return_value=""), \
         patch("src.View.AutoSegmentation.ButtonInputBox.setup_window"):
        box = ButtonInputBox(
            positive_action=send_mock,
            negative_action=close_mock
        )

        # Act
        box._negative_action()

        # Assert
        close_mock.assert_called_once_with()

def test_feedback_label_and_properties(qapp):
    # Arrange
    with patch("src.View.AutoSegmentation.ButtonInputBox.StyleSheetReader.get_stylesheet", return_value=""), \
         patch("src.View.AutoSegmentation.ButtonInputBox.setup_window"):
        box = ButtonInputBox(input_text="Test", text_box=True)
        # Act
        feedback_label = box.feedback
        # Assert
        assert feedback_label.isHidden()
        assert feedback_label.property("QLabelClass") == "info-feedback"

def test_buttoninputbox_properties_and_layout(qapp):
    # Arrange
    with patch("src.View.AutoSegmentation.ButtonInputBox.StyleSheetReader.get_stylesheet", return_value=""), \
         patch("src.View.AutoSegmentation.ButtonInputBox.setup_window"):
        box = ButtonInputBox(input_text="Test", text_box=True, reversed_buttons=True)
        # Act & Assert
        assert box.property("WidgetClass") == "widget-window"
        assert box.text.placeholderText() == "Selection Name"
        assert box.text.maxLength() == 25
        assert box.delete_word is None or isinstance(box.delete_word, str)
        assert box.layout() is not None

def test_positive_action_with_no_send_callback(qapp):
    # Arrange
    with patch("src.View.AutoSegmentation.ButtonInputBox.StyleSheetReader.get_stylesheet", return_value=""), \
         patch("src.View.AutoSegmentation.ButtonInputBox.setup_window"):
        box = ButtonInputBox(positive_action=None)
        # Act & Assert
        # Should not raise, but nothing happens
        assert box._positive_action() is None

def test_negative_action_with_no_close_callback(qapp):
    # Arrange
    with patch("src.View.AutoSegmentation.ButtonInputBox.StyleSheetReader.get_stylesheet", return_value=""), \
         patch("src.View.AutoSegmentation.ButtonInputBox.setup_window"):
        box = ButtonInputBox(negative_action=None)
        # Act & Assert
        # Should not raise, but nothing happens
        assert box._negative_action() is None
