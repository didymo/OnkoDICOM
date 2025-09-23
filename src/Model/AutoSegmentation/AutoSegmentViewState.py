import logging
from collections.abc import Callable
from src.Model.Singleton import Singleton

logger = logging.Logger(__name__)

def _communication_debug(word: str, member: Callable[[], None]) -> None:
    if member is None:
        logger.debug(f"{word} function not set: call {word}_button_callback({word}_function) to assign a function first")


class AutoSegmentViewState(metaclass=Singleton):
    """
    Singleton Structure to store the state of the AutoSegmentationView
    To allow all data to be passed to view in a single object
    Allowing Construction in any object while having the same data.
    """
    def __init__(self) -> None:
        """
        initialising members for struct class.
        """
        # callback list in format Start, Save, Load, Delete function pointers
        self._start: Callable[[], None] | None = None # Start
        self._save: Callable[[], None] | None = None # Save
        self._load: Callable[[], None] | None = None # Load
        self._delete: Callable[[], None] | None = None # Delete

        self.segmentation_list: list[str] = []

    def _communicate_connection(self, member: Callable[[], None]) -> None:
        if member is not None:
            member()

    def start_button_connection(self) -> None:
        """
        To communicate to controller the start button was clicked.

        :return: None
        """
        self._communicate_connection(self._start)
        _communication_debug("Start", self._start)

    def set_start_button_callback(self, start_function: Callable[[], None]) -> None:
        """
        To set the function called in the controller when the start Button is clicked

        :param start_function: Callable[[], None]
        :return: None
        """
        self._start = start_function


    def save_button_connection(self) -> None:
        """
        To communicate to controller the save button was clicked.

        :return: None
        """
        self._communicate_connection(self._save)
        _communication_debug("Save", self._save)

    def set_save_button_callback(self, save_function: Callable[[], None]) -> None:
        """
        To set the function called in the controller when the save button is clicked

        :param save_function: Callable[[], None]
        :return: None
        """
        self._save = save_function

    def load_button_connection(self) -> None:
        """
        To communicate to controller the load button was clicked.

        :return: None
        """
        self._communicate_connection(self._load)
        _communication_debug("Load", self._load)

    def set_load_button_callback(self, load_function: Callable[[], None]) -> None:
        """
        To set the function called in the controller when the load button is clicked

        :param load_function: Callable[[], None]
        :return: None
        """
        self._load = load_function

    def delete_button_connection(self) -> None:
        """
        To communicate to controller the delete button was clicked.

        :return: None
        """
        self._communicate_connection(self._delete)
        _communication_debug("Delete", self._delete)

    def set_delete_button_callback(self, delete_function: Callable[[], None]) -> None:
        """
        To set the function called in the controller when the delete button is clicked

        :param delete_function: Callable[[], None]
        :return: None
        """
        self._delete = delete_function