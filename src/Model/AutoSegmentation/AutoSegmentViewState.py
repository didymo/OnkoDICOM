from src.Model.Singleton import Singleton


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
        self.segmentation_list = []