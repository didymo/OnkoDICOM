from src.Controller.GUIController import OpenPatientWindow


def test_open_patient_window(qtbot):
    open_patient_window = OpenPatientWindow(None)
    open_patient_window.show()
    qtbot.addWidget(open_patient_window)

    assert open_patient_window.windowTitle() == "OnkoDICOM - Select Patient"
    assert open_patient_window.open_patient_directory_prompt.text() == \
           "Choose the path of the folder containing DICOM files to load Patient's details:"
    assert open_patient_window.open_patient_directory_input_box.placeholderText() == \
           'Enter DICOM Files Path (For example, C:\path\\to\your\DICOM\Files)'
    assert open_patient_window.open_patient_directory_input_box.text() == \
           ""
    assert open_patient_window.open_patient_directory_choose_button.text() == "Choose"
    assert open_patient_window.open_patient_directory_appear_prompt.text() == \
           "Patient File directory shown below once file path chosen. Please select the file(s) you want to open:"
    assert open_patient_window.open_patient_directory_result_label.text() == \
           "The selected directory(s) above will be opened in the OnkoDICOM program."
    assert open_patient_window.open_patient_window_stop_button.text() == "Stop Search"
    assert open_patient_window.open_patient_window_exit_button.text() == "Exit"
    assert open_patient_window.open_patient_window_confirm_button.text() == "Confirm"


def test_open_patient_window_with_default_dir(qtbot):
    open_patient_window = OpenPatientWindow("test/testdata/DICOM-RT-TEST")
    open_patient_window.show()

    while not open_patient_window.threadpool.waitForDone():
        assert open_patient_window.open_patient_window_stop_button.isVisible()
        assert not open_patient_window.open_patient_directory_choose_button.isEnabled()
        pass

    def check_search_finished():
        assert not open_patient_window.open_patient_window_stop_button.isVisible()
        assert open_patient_window.open_patient_directory_choose_button.isEnabled()

    qtbot.waitUntil(check_search_finished)
    # test result patients tree structure
    patients_tree = open_patient_window.open_patient_window_patients_tree
    assert patients_tree.topLevelItemCount() == 1
    assert patients_tree.topLevelItem(0).text(0).startswith("Patient")
    assert patients_tree.topLevelItem(0).childCount() == 1
    study = patients_tree.topLevelItem(0).child(0)
    assert study.text(0).startswith("Study")
    assert study.childCount() == 4

    assert open_patient_window.open_patient_directory_input_box.text() == \
           "test/testdata/DICOM-RT-TEST"
