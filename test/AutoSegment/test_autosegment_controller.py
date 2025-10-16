import pytest
from unittest.mock import patch, Mock

from src.Controller.AutoSegmentationController import AutoSegmentationController


@pytest.fixture
def controller():
    with patch("src.Controller.AutoSegmentationController.AutoSegmentViewState") as vs, \
            patch("src.Controller.AutoSegmentationController.PatientDictContainer"), \
            patch("src.Controller.AutoSegmentationController.SavedSegmentDatabase") as db, \
            patch("src.Controller.AutoSegmentationController.AutoSegmentWindow"):
        ctrl = AutoSegmentationController()
        ctrl._view = Mock()
        ctrl.save_list = ["foo", "bar"]
        return ctrl

def test_init_sets_callbacks_and_members():
    # Arrange
    with patch("src.Controller.AutoSegmentationController.AutoSegmentViewState") as vs, \
            patch("src.Controller.AutoSegmentationController.PatientDictContainer"), \
            patch("src.Controller.AutoSegmentationController.SavedSegmentDatabase") as db, \
            patch("src.Controller.AutoSegmentationController.AutoSegmentWindow"):
        # Act
        ctrl = AutoSegmentationController()
        # Assert
        assert isinstance(ctrl.view_state, type(vs()))
        assert hasattr(ctrl, "database")
        assert hasattr(ctrl, "patient_dict_container")

def test_start_button_clicked_calls_disable_and_run_task(controller):
    # Arrange
    controller._view.get_segmentation_roi_subset.return_value = ["roi1"]
    controller.run_task = Mock()
    # Act
    controller.start_button_clicked("ignored")
    # Assert
    controller._view.disable_start_button.assert_called_once()
    controller.run_task.assert_called_once_with("total", ["roi1"])

def test_save_button_clicked_calls_db_insert(controller):
    # Arrange
    controller.database.insert_row = Mock()
    # Act
    controller.save_button_clicked("foo", ["roi1"])
    # Assert
    controller.database.insert_row.assert_called_once_with("foo", ["roi1"])

def test_load_button_clicked_calls_db_and_view(controller):
    # Arrange
    controller.database.select_entry = Mock(return_value=["roi1", "roi2"])
    controller._view.load_selection = Mock()
    # Act
    controller.load_button_clicked("foo")
    # Assert
    controller.database.select_entry.assert_called_with("foo")
    controller._view.load_selection.assert_called_with(["roi1", "roi2"])

def test_delete_button_clicked_removes_if_in_save_list(controller):
    # Arrange
    controller.database.delete_entry = Mock()
    controller._view.remove_save_item = Mock()
    # Act
    controller.delete_button_clicked("foo")
    # Assert
    controller.database.delete_entry.assert_called_with("foo")
    controller._view.remove_save_item.assert_called_with("foo")

def test_delete_button_clicked_does_nothing_if_not_in_save_list(controller):
    # Arrange
    controller.database.delete_entry = Mock()
    controller._view.remove_save_item = Mock()
    # Act
    controller.delete_button_clicked("not_in_list")
    # Assert
    controller.database.delete_entry.assert_not_called()
    controller._view.remove_save_item.assert_not_called()

def test_get_saved_segmentations_list_calls_db_and_view(controller):
    # Arrange
    controller.database.get_save_list = Mock(return_value=["foo", "bar"])
    controller._view.add_save_list = Mock()
    # Act
    controller.get_saved_segmentations_list()
    # Assert
    controller._view.add_save_list.assert_called_with(["foo", "bar"])
    assert controller.save_list == ["foo", "bar"]

def test_show_view_creates_and_shows_view():
    # Arrange
    with patch("src.Controller.AutoSegmentationController.AutoSegmentViewState") as vs, \
            patch("src.Controller.AutoSegmentationController.PatientDictContainer"), \
            patch("src.Controller.AutoSegmentationController.SavedSegmentDatabase") as db, \
            patch("src.Controller.AutoSegmentationController.AutoSegmentWindow"):

        with patch("src.Controller.AutoSegmentationController.AutoSegmentWindow") as win_cls:
            win = win_cls.return_value
            win.isVisible.return_value = True
            ctrl = AutoSegmentationController()
            ctrl._view = None
            ctrl.get_saved_segmentations_list = Mock()
            # Act
            ctrl.show_view()
            # Assert
            win.show.assert_called_once()
            win.raise_.assert_called_once()
            win.activateWindow.assert_called_once()
            ctrl.get_saved_segmentations_list.assert_called_once()

def test_show_view_existing_view():
    # Arrange
    with patch("src.Controller.AutoSegmentationController.AutoSegmentViewState") as vs, \
            patch("src.Controller.AutoSegmentationController.PatientDictContainer"), \
            patch("src.Controller.AutoSegmentationController.SavedSegmentDatabase") as db, \
            patch("src.Controller.AutoSegmentationController.AutoSegmentWindow"):
        with patch("src.Controller.AutoSegmentationController.AutoSegmentWindow") as win_cls:
            win = win_cls.return_value
            win.isVisible.return_value = True
            ctrl = AutoSegmentationController()
            ctrl._view = win
            ctrl.get_saved_segmentations_list = Mock()
            # Act
            ctrl.show_view()
            # Assert
            win.show.assert_called_once()
            win.raise_.assert_called_once()
            win.activateWindow.assert_called_once()
            ctrl.get_saved_segmentations_list.assert_not_called()

def test_communicate_database_state_shows_and_sets_text(controller):
    # Arrange
    controller._view.database_feedback = Mock()
    # Act
    controller.communicate_database_state("msg")
    # Assert
    controller._view.database_feedback.hide.assert_called_once()
    controller._view.database_feedback.show.assert_called_once()
    controller._view.database_feedback.setText.assert_called_with("msg")

def test_communicate_database_state_hides_if_no_text(controller):
    # Arrange
    controller._view.database_feedback = Mock()
    # Act
    controller.communicate_database_state("")
    # Assert
    controller._view.database_feedback.hide.assert_called_once()
    controller._view.database_feedback.show.assert_not_called()
    controller._view.database_feedback.setText.assert_called_with("")

def test_communicate_database_state_no_view():
    # Arrange
    with patch("src.Controller.AutoSegmentationController.AutoSegmentViewState") as vs, \
            patch("src.Controller.AutoSegmentationController.PatientDictContainer"), \
            patch("src.Controller.AutoSegmentationController.SavedSegmentDatabase") as db, \
            patch("src.Controller.AutoSegmentationController.AutoSegmentWindow"):
        ctrl = AutoSegmentationController()
        ctrl._view = None
        # Act
        ctrl.communicate_database_state("msg")
        # Assert
        # No exception, nothing to assert

def test_update_progress_text_calls_view(controller):
    # Arrange
    controller._view.set_progress_text = Mock()
    # Act
    controller.update_progress_text("progress")
    # Assert
    controller._view.set_progress_text.assert_called_with("progress")

def test_run_task_starts_thread(controller):
    # Arrange
    with patch("src.Controller.AutoSegmentationController.AutoSegmentation") as auto_cls, \
         patch("threading.Thread") as thread_cls:
        auto = auto_cls.return_value
        thread = thread_cls.return_value
        # Act
        controller.run_task("total", ["roi1"])
        # Assert
        thread_cls.assert_called_once()
        thread.start.assert_called_once()

def test_on_segmentation_finished_emits_and_calls_view(controller):
    # Arrange
    controller._view.segmentation_successful_dialog = Mock()
    with patch("src.Controller.AutoSegmentationController.load_rtss_file_to_patient_dict") as load_rtss:
        # Act
        controller.on_segmentation_finished()
        # Assert
        controller._view.segmentation_successful_dialog.assert_called_with(True)

def test_on_segmentation_error_calls_view(controller):
    # Arrange
    controller._view.segmentation_successful_dialog = Mock()
    # Act
    controller.on_segmentation_error("err")
    # Assert
    controller._view.segmentation_successful_dialog.assert_called_with(False)
