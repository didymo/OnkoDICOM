from collections.abc import Callable
from src.Model.Singleton import Singleton


class AutoSegmentViewState(metaclass=Singleton):
    """
    Singleton Structure to store the state of the AutoSegmentationView
    To allow all data to be passed to view in a single object
    Allowing Construction in any object while having the same data.
    """
    def __init__(self, callback: Callable[[], None]) -> None:
        """
        initialising members for struct class.
        """
        self.callback: Callable[[], None] = callback

        self.segmentation_list: list[str] = []


    def start_button_connection(self) -> None:
        """
        To communicate to controller the start button was clicked.
        """
        self.callback()