import pytest
import os
from PySide6 import QtCore, QtWidgets
from pathlib import Path

from src.Controller.GUIController import FirstTimeWelcomeWindow
from src.Model.Configuration import Configuration


@pytest.fixture(scope="session", autouse=True)
def init_first_time_window_config(request):
    configuration = Configuration('TestFirstTimeWelcomeWindow.db')
    db_file_path = Path(os.environ['USER_ONKODICOM_HIDDEN']).joinpath('TestFirstTimeWelcomeWindow.db')
    configuration.set_db_file_path(db_file_path)

    def tear_down():
        if os.path.isfile(db_file_path):
            os.remove(db_file_path)

    request.addfinalizer(tear_down)


def test_first_time_welcome_window(qtbot, tmpdir, init_first_time_window_config):
    first_time_welcome_window = FirstTimeWelcomeWindow()
    first_time_welcome_window.show()
    qtbot.addWidget(first_time_welcome_window)
    db_file_path = Path(os.environ['USER_ONKODICOM_HIDDEN']).joinpath('TestFirstTimeWelcomeWindow.db')

    assert first_time_welcome_window.first_time_welcome_message_label.text() == "Welcome to OnkoDICOM!"
    assert first_time_welcome_window.first_time_welcome_message_slogan.text() == "OnkoDICOM - the solution for producing data for analysis from your oncology plans and scans."
    assert first_time_welcome_window.first_time_welcome_default_dir_prompt.text() == "Choose the path of the default directory containing all DICOM files:"
    assert first_time_welcome_window.first_time_welcome_input_box.placeholderText() == "Enter DICOM Files Path (For example, C:\\path\\to\\your\\DICOM\\Files)"
    assert first_time_welcome_window.first_time_welcome_choose_button.text() == "Choose"
    assert first_time_welcome_window.save_dir_button.text() == "Confirm"
    assert first_time_welcome_window.skip_button.text() == "Skip"

    # Test with directory box empty
    first_time_welcome_window.first_time_welcome_input_box.clear()

    def test_message_window():
        messagebox = QtWidgets.QApplication.activeWindow()
        assert messagebox is not None
        ok_button = messagebox.button(QtWidgets.QMessageBox.Ok)
        assert ok_button is not None
        qtbot.mouseClick(ok_button, QtCore.Qt.LeftButton, delay=1)

    QtCore.QTimer.singleShot(1000, test_message_window)
    qtbot.mouseClick(first_time_welcome_window.save_dir_button, QtCore.Qt.LeftButton)

    # Create temp csv
    csv_path = Path.cwd().joinpath('test', 'testdata', 'temp.csv')
    with open(csv_path, "w") as file:
        file.write("test")
        file.close()

    # Test with directory box filled
    qtbot.keyClicks(first_time_welcome_window.first_time_welcome_input_box, str(tmpdir))
    qtbot.keyClicks(first_time_welcome_window.clinical_data_csv_input_box,
                    str(csv_path))
    with qtbot.waitSignal(first_time_welcome_window.go_next_window, raising=True):
        qtbot.mouseClick(first_time_welcome_window.save_dir_button, QtCore.Qt.LeftButton)

    # Test if the database has been created
    assert os.path.isfile(db_file_path) == True

    # Delete temp csv
    os.remove(csv_path)
