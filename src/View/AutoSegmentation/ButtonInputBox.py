from collections.abc import Callable

from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QLabel, QLineEdit, QHBoxLayout
from PySide6.QtCore import QSize

from src.View.StyleSheetReader import StyleSheetReader
from src.View.WindowBarIconSetup import setup_window


class ButtonInputBox(QWidget):
    """
    A Message Box which has the with labels and actions to run when buttons are clicked
    With optional Text box and ability to reverse the colours of the buttons
    """
    def __init__(self,
                 input_text: str="[Input Text]",
                 positive_action: Callable[[str | None], None]=None,
                 negative_action: Callable[[], None]=None,
                 text_box=False,
                 reversed_buttons=False,
                 delete_word = None) -> None:
        """
        A Message Box which has the with labels and actions to run when buttons are clicked
        With optional Text box and ability to reverse the colours of the buttons

        :param input_text: str
        :param positive_action: Callable[[str], None]
        :param negative_action: Callable[[], None]
        :param text_box: bool
        :param reversed_buttons: bool
        :returns: None
        """
        super(ButtonInputBox, self).__init__()
        self.setProperty("WidgetClass", "widget-window")
        self.setStyleSheet(StyleSheetReader().get_stylesheet())
        setup_window(self, "Save Name")
        self.setFixedSize(QSize(400, 150))
        self._send: Callable[[str], None] = positive_action
        self._close: Callable[[], None] = negative_action
        self.typed_text: str = ""
        self.delete_word: str = delete_word

        box_layout: QVBoxLayout = QVBoxLayout()
        text_label: QLabel = QLabel(input_text)
        box_layout.addWidget(text_label)
        self.feedback = QLabel()
        self.feedback.setProperty("QLabelClass", "info-feedback")
        box_layout.addWidget(self.feedback)
        self.feedback.hide()
        self.text = None
        if text_box:
            self.text: QLineEdit = QLineEdit()
            self.text.setPlaceholderText("Selection Name")
            self.text.setMaxLength(25)
            box_layout.addWidget(self.text)

        positive_button: QPushButton = QPushButton("OK")
        positive_button.setProperty("QPushButtonClass", "success-button")
        if reversed_buttons:
            positive_button.setProperty("QPushButtonClass", "fail-button")
        else:
            positive_button.setProperty("QPushButtonClass", "success-button")
        if positive_action is not None:
            positive_button.clicked.connect(self._positive_action)

        box_cancel_button: QPushButton = QPushButton("Cancel")
        if reversed_buttons:
            box_cancel_button.setProperty("QPushButtonClass", "success-button")
        else:
            box_cancel_button.setProperty("QPushButtonClass", "fail-button")
        box_cancel_button.clicked.connect(self.close)
        if negative_action is not None:
            box_cancel_button.clicked.connect(self._negative_action)

        button_widget: QWidget = QWidget()
        box_buttons: QHBoxLayout = QHBoxLayout()
        box_buttons.addWidget(positive_button)
        box_buttons.addWidget(box_cancel_button)
        button_widget.setLayout(box_buttons)

        box_layout.addWidget(button_widget)
        self.setLayout(box_layout)

    def _positive_action(self) -> None:
        """
        Action Being Performed if the OK(Green) button is clicked

        :returns: None
        """
        if self.text is not None:
            self.typed_text = self.text.text()
        if self.delete_word:
            self.typed_text = self.delete_word
        return self._send(self.typed_text)

    def _negative_action(self) -> None:
        """
        Action Being Performed if the Cancel(Red) button is clicked

        :returns: None
        """
        self._close()