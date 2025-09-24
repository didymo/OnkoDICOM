import threading
import logging
from PySide6.QtCore import Slot, QObject, Signal

from src.Model.AutoSegmentation.AutoSegmentViewState import AutoSegmentViewState
from src.Model.AutoSegmentation.AutoSegmentation import AutoSegmentation
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
        self.view_state: AutoSegmentViewState = AutoSegmentViewState() # storing state of view
        self.view_state.set_start_button_callback(self.start_button_clicked) # Start
        self.view_state.set_save_button_callback(self.save_button_clicked) # Save
        self.view_state.set_load_button_callback(self.load_button_clicked) # Load
        self.view_state.set_delete_button_callback(self.delete_button_clicked) # Delete

        self._view = None
        self._model = None
        self.patient_dict_container = PatientDictContainer()
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

    def save_button_clicked(self, value: str) -> None:
        """
        To be called when the button to save the selected segmentation task is clicked
        :rtype: None
        """
        print(f"Save {value}")

    def load_button_clicked(self, value: str) -> None:
        """
        To be called when the button to load the selected saved segmentation is clicked
        :rtype: None
        """
        print(f"Load {value}")

    def delete_button_clicked(self, value: str) -> None:
        """
        To be called when the button to delete the selected segmentation task is clicked
        :rtype: None
        """
        print(f"Delete {value}")

    def show_view(self):
        """
        To Display the view on Screen
        :rtype: None
        """
        if self._view is None:
            self._view = AutoSegmentWindow(self.view_state)
        self._view.show()

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
        # Update the text edit UI
        self.update_progress_text("Loading the RTSTRUCT file")
        load_rtss_file_to_patient_dict(self.patient_dict_container)
        self.update_progress_text("Populating Structures Tab.")
        self.update_structure_list.emit()
        self.update_progress_text("Structures Loaded")

        # Enable once segmentation complete
        self._view.enable_start_button()

    @Slot()
    def on_segmentation_error(self, error) -> None:
        logging.error(error)
        # Enable once segmentation complete
        self._view.enable_start_button()