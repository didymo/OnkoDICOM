import logging
from collections.abc import Callable
from src.Model.Singleton import Singleton

logger = logging.Logger(__name__)

def _communication_debug(word: str, member: Callable[[str], None] | Callable[[str, list[str]], None]) -> None:
    """
    Debug statement to log any potential issues

    :param word: str
    :param member: Callable[[str], None] | Callable[[str, list[str]], None]
    :return: None
    """
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
        self._start: Callable[[str], None] | None = None # Start
        self._save: Callable[[str, list[str]], None] | None = None # Save
        self._load: Callable[[str], None] | None = None # Load
        self._delete: Callable[[str], None] | None = None # Delete

        self.segmentation_list: list[str] = []

    def _communicate_connection(self, member: Callable[[str], None], value: str) -> None:
        """
        Checking is call back exists and execute the call back

        :param member: Callable[[str], None]
        :param value: str
        """
        if member is not None:
            member(value)

    def start_button_connection(self, value: str) -> None:
        """
        To communicate to controller the start button was clicked.

        :return: None
        """
        self._communicate_connection(self._start, value)
        _communication_debug("Start", self._start)

    def set_start_button_callback(self, start_function: Callable[[str], None]) -> None:
        """
        To set the function called in the controller when the start Button is clicked

        :param start_function: Callable[[], None]
        :return: None
        """
        self._start = start_function


    def save_button_connection(self, save_name:str) -> None:
        """
        To communicate to controller the save button was clicked and
        to transfer information such as the save name and the saved data list

        :param save_name: str
        :return: None
        """
        if self._save is not None:
            self._save(save_name, self.segmentation_list)
        _communication_debug("Save", self._save)

    def set_save_button_callback(self, save_function: Callable[[str, list[str]], None]) -> None:
        """
        To set the function called in the controller when the save button is clicked

        :param save_function: Callable[[], None]
        :return: None
        """
        self._save = save_function

    def load_button_connection(self, value: str) -> None:
        """
        To communicate to controller the load button was clicked.

        :return: None
        """
        self._communicate_connection(self._load, value)
        _communication_debug("Load", self._load)

    def set_load_button_callback(self, load_function: Callable[[str], None]) -> None:
        """
        To set the function called in the controller when the load button is clicked

        :param load_function: Callable[[], None]
        :return: None
        """
        self._load = load_function

    def delete_button_connection(self, value: str) -> None:
        """
        To communicate to controller the delete button was clicked.

        :return: None
        """
        self._communicate_connection(self._delete, value)
        _communication_debug("Delete", self._delete)

    def set_delete_button_callback(self, delete_function: Callable[[str], None]) -> None:
        """
        To set the function called in the controller when the delete button is clicked

        :param delete_function: Callable[[], None]
        :return: None
        """
        self._delete = delete_function