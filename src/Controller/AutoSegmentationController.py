import threading
import logging
from PySide6.QtCore import Slot, QObject, Signal

from src.Model.AutoSegmentation.AutoSegmentViewState import AutoSegmentViewState
from src.Model.AutoSegmentation.AutoSegmentation import AutoSegmentation
from src.Model.AutoSegmentation.SavedSegmentDatabase import SavedSegmentDatabase
from src.Model.PatientDictContainer import PatientDictContainer
from src.Controller.RTStructFileLoader import load_rtss_file_to_patient_dict
from src.View.AutoSegmentation.AutoSegmentWindow import AutoSegmentWindow


class AutoSegmentationController(QObject):
    """
    For the controlling of the UI elements in the View Class and the sending data to the Model class
    As well as modifying data to communicate between the View and Model Classes
    """
    update_structure_list = Signal()

    def __init__(self) -> None:
        super().__init__()
        """
        Initialising the Controller for Auto Segmentation Feature.
        Creating the requirements to run the feature
        :rtype: None
        """
        # creating connections
        self.view_state: AutoSegmentViewState = AutoSegmentViewState()
        self.view_state.set_start_button_callback(self.start_button_clicked)
        self.view_state.set_save_button_callback(self.save_button_clicked)
        self.view_state.set_load_button_callback(self.load_button_clicked)
        self.view_state.set_delete_button_callback(self.delete_button_clicked)

        # Object Connections
        self._view = None
        self._model = None
        self.patient_dict_container = PatientDictContainer()
        self.database: SavedSegmentDatabase = SavedSegmentDatabase("AutoSegmentationSaves",
                                                                   "save_name",
                                                                   self.communicate_database_state)
        # Member Variables
        self.save_list: list[str] | None = None # Will be initialized on window open

        # self.threadpool = QThreadPool() - Raises Seg Fault

    # View related methods
    def start_button_clicked(self, value: str) -> None:
        """
        To be called when the button to start the selected segmentation task is clicked
        :rtype: None
        """
        # Disable start button while segmentation processes
        self._view.disable_start_button()

        self.run_task("total", self._view.get_segmentation_roi_subset())

    def save_button_clicked(self, save_name: str, save_list: list[str]) -> None:
        """
        To be called when the button to save the selected segmentation task is clicked
        :rtype: None
        """
        self.database.insert_row(save_name, save_list)

    def load_button_clicked(self, value: str) -> None:
        """
        To be called when the button to load the selected saved segmentation is clicked
        :rtype: None
        """
        self.database.select_entry(value)
        self._view.load_selection(self.database.select_entry(value))

    def delete_button_clicked(self, value: str) -> None:
        """
        To be called when the button to delete the selected segmentation task is clicked
        :rtype: None
        """
        if value in self.save_list:
            self.database.delete_entry(value)
            self._view.remove_save_item(value)

    def get_saved_segmentations_list(self) -> None:
        """
        Gets a list of all saved segmentation choices and adds them to the Selector widget
        :rtype: None
        """
        self.save_list: list[str] = self.database.get_save_list()
        self._view.add_save_list(self.save_list)

    def show_view(self):
        """
        Checks if self._view has an instance of AutoSegmentWindow instanced,
        if it does not then creates a new instance of AutoSegmentWindow,
        Retrieves the list of saves from the database to display in the view
        adds it to the view the brings the view to the fron to front of the window stack
        :rtype: None
        """
        if self._view is None:
            self._view = AutoSegmentWindow(self.view_state)
            self.get_saved_segmentations_list()
        self._view.show()

        # Bring window to front and make active (if already visible)
        if self._view.isVisible():
            self._view.raise_()
            self._view.activateWindow()

    def communicate_database_state(self, text: str) -> None:
        """
        To communicate to the user about database states which may result in the Database
        failing to read or write and retry attempts. This will communicate to the user
        the latest issue user feed back information about the issue being handled in regard
        to the database

        :param text: str
        :rtype: None
        """
        if self._view is not None:
            self._view.database_feedback.hide()
            if text:
                self._view.database_feedback.show()
            self._view.database_feedback.setText(text)

    def update_progress_text(self, text: str) -> None:
        """
        Access the view of the feature and updates the progress text on the UI element
        :param text: str
        :rtype: None
        """
        self._view.set_progress_text(text)

    # Model related methods
    def run_task(self, task: str, roi_subset: list[str]) -> None:
        """
        Run the segmentation task from the model class.
        Performing the Segmentation for the Dicom Images
        :param task: str
        :param roi_subset: list[str]
        :rtype: None
        """
        # Instantiate AutoSegmentation passing the required settings from the UI
        auto_segmentation = AutoSegmentation(self)
        # Run tasks on separate thread
        auto_seg_thread = threading.Thread(target=auto_segmentation.run_segmentation_workflow, args=(task, roi_subset))
        auto_seg_thread.start() # Will auto terminate at the called functions conclusion

    @Slot()
    def on_segmentation_finished(self) -> None:
        self.update_progress_text("Loading the RTSTRUCT file")
        load_rtss_file_to_patient_dict(self.patient_dict_container)
        self.update_progress_text("Populating Structures Tab.")
        self.update_structure_list.emit()

        self._view.segmentation_successful_dialog(True)

    @Slot()
    def on_segmentation_error(self, error) -> None:
        logging.error(error)

        self._view.segmentation_successful_dialog(False)
