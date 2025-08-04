import threading
from src.Model.AutoSegmentation import AutoSegmentation

class AutoSegmentationController:
    """
    For the controlling of the UI elements in the View Class and the sending data to the Model class
    As well as modifying data to communicate between the View and Model Classes
    """

    def __init__(self, view) -> None:
        """
        Initialising the Controller for Auto Segmentation Feature.
        Creating the requirements to run the feature
        :param view: AutoSegmentationTab
        :rtype: None
        """
        self._view = view
        self._model = None
        # self.threadpool = QThreadPool() - Raises Seg Fault

    def set_view(self, view) -> None:
        """
        To change the view reference if a new view is
        constructed to replace the old view
        :param view:
        :rtype: None
        """
        self._view = view

    # View related methods
    def start_button_clicked(self) -> None:
        """
        To be called when the button to start the selected segmentation task is clicked
        :rtype: None
        """
        self.run_task(self._view.get_segmentation_task(), self._view.get_fast_value())

    def update_progress_bar_value(self, value: int) -> None:
        """
        Access the view of the feature and updates the progress bar on the UI element
        :param value: int
        :rtype: None

        """
        self._view.set_progress_bar_value(value)

    def update_progress_text(self, text: str) -> None:
        """
        Access the view of the feature and updates the progress text on the UI element
        :param text: str
        :rtype: None
        """
        self._view.set_progress_text(text)

    # Model related methods
    def run_task(self, task: str, fast: bool) -> None:
        """
        Run the segmentation task from the model class.
        Performing the Segmentation for the Dicom Images
        :param task: str
        :param fast: bool
        :rtype: None
        """
        # Instantiate AutoSegmentation passing the required settings from the UI
        auto_segmentation = AutoSegmentation(task, fast, controller=self)

        # Run tasks on separate thread
        auto_seg_thread = threading.Thread(target=auto_segmentation.run_segmentation_workflow)
        auto_seg_thread.start() # Will auto terminate at the called functions conclusion