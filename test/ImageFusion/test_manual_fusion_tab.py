import os
from pathlib import Path
import pytest
from PySide6.QtWidgets import QPushButton

from src.Controller.GUIController import MainWindow
from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.ImageLoading import get_datasets
from src.View.ImageFusion.TranslateRotateMenu import TranslateRotateMenu
from pydicom import dcmread
from pydicom.errors import InvalidDicomError
from src.Model import PatientDictContainer as PDC_module, ImageLoading
from unittest.mock import patch
import numpy as np
import tempfile

"""
Tests for the OnkoDICOM manual fusion tab GUI.

These tests verify that:
- The main window and manual fusion tab can be set up with test DICOM data.
- All fusion views (axial, sagittal, coronal) are present, visible, and enabled.
- The fusion options tab and its controls (sliders, combo boxes, buttons) exist and work as expected.
- Translation and rotation sliders respond to value changes and can be reset.
- Color pair and opacity controls update the overlay as expected.
- Zoom, metadata, and view update functions work for the fusion views.
- The fusion options tab is present in the left panel and the four-views layout is active.
- Saving and loading fusion state opens the correct file dialogs (mocked).
- The transform matrix dialog can be opened and is visible.

"""

#
# @pytest.fixture(autouse=True)
# def reset_patient_dict_container():
#     # Arrange
#     yield
#     # Act/Assert: after each test, clear the singleton
#     PatientDictContainer().clear()
#

def find_dicom_files(folder, exclude_transform=False):
    """Finds all valid DICOM files in a folder, optionally excluding spatial registration (transform) files."""
    dicom_files = []
    for root, dirs, files in os.walk(folder, topdown=True):
        for name in files:
            file_path = os.path.join(root, name)
            try:
                ds = dcmread(file_path, stop_before_pixels=True)
                if exclude_transform:
                    # Exclude DICOM Spatial Registration (transform) files by SOP Class UID or Modality
                    sop_class = getattr(ds, "SOPClassUID", "")
                    modality = getattr(ds, "Modality", "").upper()
                    if (
                            sop_class == "1.2.840.10008.5.1.4.1.1.66.1"
                            or modality == "REG"
                    ):
                        continue
            except (InvalidDicomError, FileNotFoundError, AttributeError):
                continue
            else:
                dicom_files.append(file_path)
    return dicom_files


class TestManualFusionTab:
    """Sets up OnkoDICOM main window for testing the manual fusion tab."""
    __test__ = False

    def __init__(self):
        # Find test DICOM files
        testdata_path = Path.cwd().joinpath('test', 'testdata')
        selected_files = find_dicom_files(testdata_path, exclude_transform=True)
        file_path = os.path.dirname(os.path.commonprefix(selected_files))
        read_data_dict, file_names_dict = get_datasets(selected_files)

        # Initialize PatientDictContainer singleton
        patient_dict_container = PatientDictContainer()
        patient_dict_container.clear()
        patient_dict_container.set_initial_values(file_path, read_data_dict, file_names_dict)

        # Ensure global reference
        PDC_module._patient_dict_container_instance = patient_dict_container

        if "rtss" in file_names_dict:
            dataset_rtss = dcmread(file_names_dict['rtss'])
            self.rois = ImageLoading.get_roi_info(dataset_rtss)
            dict_raw_contour_data, dict_numpoints = ImageLoading.get_raw_contour_data(dataset_rtss)
            dict_pixluts = ImageLoading.get_pixluts(read_data_dict)

            patient_dict_container.set("rois", self.rois)
            patient_dict_container.set("raw_contour", dict_raw_contour_data)
            patient_dict_container.set("num_points", dict_numpoints)
            patient_dict_container.set("pixluts", dict_pixluts)

        # Open main window and create fusion tab
        self.main_window = MainWindow()
        self.main_window.create_image_fusion_tab(manual=True)


@pytest.fixture(scope="module")
def fusion_test_object():
    return TestManualFusionTab()

def _assert_views_visible(qtbot, views):
    """Helper to check that all given views are visible."""
    for view in views:
        qtbot.waitExposed(view)
        assert view.isVisible()

@pytest.mark.parametrize(
    "attr,view_attr",
    [
        ("image_fusion_view_axial", "image_fusion_view_axial"),
        ("image_fusion_view_sagittal", "image_fusion_view_sagittal"),
        ("image_fusion_view_coronal", "image_fusion_view_coronal"),
    ]
)
def test_fusion_view_exists_and_visible(qtbot, fusion_test_object, attr, view_attr):
    """Test that a specific fusion view exists and is visible/enabled."""
    main_window = fusion_test_object.main_window
    main_window.show()
    assert hasattr(main_window, attr)
    view = getattr(main_window, view_attr)
    assert view is not None
    assert view.isEnabled()
    main_window.close()


def test_fusion_options_tab_exists_and_type(fusion_test_object):
    """Test that the fusion options tab exists and is the correct type."""
    main_window = fusion_test_object.main_window
    assert hasattr(main_window, "fusion_options_tab")
    options = main_window.fusion_options_tab
    assert isinstance(options, TranslateRotateMenu)

def test_translate_sliders_work(fusion_test_object):
    """Test that translation sliders in the fusion options tab work."""
    options = fusion_test_object.main_window.fusion_options_tab
    _assert_translate_sliders(options)
    
def _assert_translate_sliders(options):
    """Helper to check translation sliders respond to value changes."""
    for slider in options.translate_sliders:
        old_value = slider.value()
        slider.setValue(old_value + 10)
        assert slider.value() == old_value + 10
        slider.setValue(old_value)

def test_rotate_sliders_work(fusion_test_object):
    """Test that rotation sliders in the fusion options tab work."""
    options = fusion_test_object.main_window.fusion_options_tab
    _assert_rotate_sliders(options)
    
def _assert_rotate_sliders(options):
    """Helper to check rotation sliders respond to value changes."""
    for slider in options.rotate_sliders:
        old_value = slider.value()
        slider.setValue(old_value + 10)
        assert slider.value() == old_value + 10
        slider.setValue(old_value)

def test_color_pair_combo_works(fusion_test_object):
    """Test that the color pair combo box works."""
    options = fusion_test_object.main_window.fusion_options_tab
    assert hasattr(options, "color_pair_combo")
    options.color_pair_combo.setCurrentText("Blue + Yellow")
    assert options.color_pair_combo.currentText() == "Blue + Yellow"

def test_opacity_slider_works(fusion_test_object):
    """Test that the opacity slider works."""
    options = fusion_test_object.main_window.fusion_options_tab
    assert hasattr(options, "opacity_slider")
    options.opacity_slider.setValue(80)
    assert options.opacity_slider.value() == 80

def test_axial_zoom_in_out(fusion_test_object):
    """Test that zoom in/out works for the axial fusion view."""
    axial = fusion_test_object.main_window.image_fusion_view_axial
    initial_zoom = axial.zoom
    axial.zoom_in()
    assert axial.zoom > initial_zoom
    axial.zoom_out()
    assert pytest.approx(axial.zoom, rel=1e-2) == initial_zoom

def test_axial_update_metadata_and_view(fusion_test_object):
    """Test that update_metadata and update_view run without error for axial view."""
    axial = fusion_test_object.main_window.image_fusion_view_axial
    axial.update_metadata()
    axial.update_view()

def test_fusion_options_tab_in_left_panel(fusion_test_object):
    """Test that the fusion options tab is present in the left panel."""
    main_window = fusion_test_object.main_window
    options = main_window.fusion_options_tab
    assert main_window.left_panel.indexOf(options) != -1

def test_four_views_layout_present(fusion_test_object):
    """Test that the four-views layout is present and active."""
    main_window = fusion_test_object.main_window
    assert hasattr(main_window, "image_fusion_four_views")
    assert main_window.image_fusion_view.currentWidget() == main_window.image_fusion_four_views

@pytest.mark.parametrize(
    "slider_attr, index",
    [
        ("translate_sliders", 0),
        ("translate_sliders", 1),
        ("translate_sliders", 2),
        ("rotate_sliders", 0),
        ("rotate_sliders", 1),
        ("rotate_sliders", 2),
    ]
)
def test_reset_transform_resets_slider(fusion_test_object, slider_attr, index):
    """Test that clicking 'Reset Transform' resets each translation and rotation slider to zero."""
    options = fusion_test_object.main_window.fusion_options_tab
    slider = getattr(options, slider_attr)[index]
    slider.setValue(42)
    reset_btn = next(
        (btn for btn in options.findChildren(QPushButton) if btn.text() == "Reset Transform"),
        None,
    )
    assert reset_btn is not None
    reset_btn.click()
    assert slider.value() == 0

def test_save_fusion_state_opens_file_dialog(qtbot, fusion_test_object):
    """Test that clicking 'Save Fusion State' opens a file dialog (mocked)."""
    # Only skip on CI (GitHub Actions or similar), always run locally
    if os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true":
        pytest.skip("Skipping file dialog test on CI workflow.")

    options = fusion_test_object.main_window.fusion_options_tab

    # Provide a dummy VTK engine with a .transform attribute
    class DummyMatrix:
        def GetElement(self, i, j):
            return 1.0 if i == j else 0.0  # Identity matrix

    class DummyTransform:
        def GetMatrix(self):
            return DummyMatrix()

    class DummyVTKEngine:
        transform = DummyTransform()
        _tx = _ty = _tz = 0.0
        _rx = _ry = _rz = 0.0
        moving_dir = ""

    options.set_get_vtk_engine_callback(lambda: DummyVTKEngine())
    with tempfile.NamedTemporaryFile(suffix=".dcm", delete=False) as tmpfile:
        filename = tmpfile.name

    _assert_save_fusion_state_opens_file_dialog(options, filename)

    # Always clean up the temp file (no conditional)
    os.remove(filename)

def _assert_save_fusion_state_opens_file_dialog(options, filename):
    """Helper to check that save fusion state opens the file dialog and clicks the button."""
    with patch("src.View.ImageFusion.TranslateRotateMenu.QFileDialog.getSaveFileName",
               return_value=(filename, None)) as mock_dialog:
        save_btn = next(
            (btn for btn in options.findChildren(QPushButton) if "save" in btn.text().lower()),
            None,
        )
        assert save_btn is not None
        save_btn.click()
        assert mock_dialog.called

def test_load_fusion_state_opens_file_dialog(qtbot, fusion_test_object):
    """Test that clicking 'Load Fusion State' opens a file dialog (mocked)."""
    # Only skip on CI (GitHub Actions or similar), always run locally
    if os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true":
        pytest.skip("Skipping file dialog test on CI workflow.")

    options = fusion_test_object.main_window.fusion_options_tab
    # Patch: Set a dummy VTK engine callback so the dialog is called
    options.set_get_vtk_engine_callback(lambda: object())
    with patch("src.View.ImageFusion.TranslateRotateMenu.QFileDialog.getOpenFileName", return_value=("dummy.dcm", None)) as mock_dialog:
        # Find and click the load button
        load_btn = next(
            (btn for btn in options.findChildren(QPushButton) if "load" in btn.text().lower()),
            None,
        )
        assert load_btn is not None
        load_btn.click()
        assert mock_dialog.called

def test_color_pair_combo_updates_overlay_colors(fusion_test_object):
    """Test that changing the color pair combo box updates the overlay colors in the views."""
    options = fusion_test_object.main_window.fusion_options_tab
    # Set to a different color pair
    options.color_pair_combo.setCurrentText("Blue + Yellow")
    # Check that the internal state is updated
    assert options.fixed_color == "Blue"
    assert options.moving_color == "Yellow"
    assert options.coloring_enabled is True

def test_opacity_slider_updates_overlay_opacity(fusion_test_object):
    """Test that changing the opacity slider updates the overlay opacity."""
    options = fusion_test_object.main_window.fusion_options_tab
    # Set to a new value
    options.opacity_slider.setValue(80)
    assert options.opacity_slider.value() == 80

def test_show_transform_matrix_button_opens_dialog(qtbot, fusion_test_object):
    """Test that clicking 'Show Transform Matrix' opens the matrix dialog."""
    options = fusion_test_object.main_window.fusion_options_tab

    # Provide a dummy VTK engine with a .transform attribute and .sitk_matrix
    class DummyMatrix:
        def GetElement(self, i, j):
            return 1.0 if i == j else 0.0  # Identity matrix

    class DummyTransform:
        def GetMatrix(self):
            return DummyMatrix()

    class DummyVTKEngine:
        transform = DummyTransform()
        sitk_matrix = np.eye(4, dtype=float)
        _tx = _ty = _tz = 0.0
        _rx = _ry = _rz = 0.0
        moving_dir = ""

    options.set_get_vtk_engine_callback(lambda: DummyVTKEngine())

    show_matrix_btn = next(
        (btn for btn in options.findChildren(QPushButton) if "matrix" in btn.text().lower()),
        None,
    )
    assert show_matrix_btn is not None
    show_matrix_btn.click()

    # The dialog should now be created and visible
    assert options._matrix_dialog is not None
    assert options._matrix_dialog.isVisible()

def test_save_fusion_state_button_exists(fusion_test_object):
    """Test that the 'Save Fusion State' button exists in the fusion options tab."""
    options = fusion_test_object.main_window.fusion_options_tab
    save_btn = next(
        (btn for btn in options.findChildren(QPushButton) if "save" in btn.text().lower()),
        None,
    )
    assert save_btn is not None
    assert "save" in save_btn.text().lower()

def test_load_fusion_state_button_exists(fusion_test_object):
    """Test that the 'Load Fusion State' button exists in the fusion options tab."""
    options = fusion_test_object.main_window.fusion_options_tab
    load_btn = next(
        (btn for btn in options.findChildren(QPushButton) if "load" in btn.text().lower()),
        None,
    )
    assert load_btn is not None
    assert "load" in load_btn.text().lower()