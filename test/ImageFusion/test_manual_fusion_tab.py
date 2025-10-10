import os
from pathlib import Path
import pytest
from src.Controller.GUIController import MainWindow
from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.ImageLoading import get_datasets
from src.View.ImageFusion.TranslateRotateMenu import TranslateRotateMenu
from pydicom import dcmread
from pydicom.errors import InvalidDicomError
from src.Model import PatientDictContainer as PDC_module, ImageLoading


def find_dicom_files(folder):
    """Finds all valid DICOM files in a folder."""
    dicom_files = []
    for root, dirs, files in os.walk(folder, topdown=True):
        for name in files:
            try:
                dcmread(os.path.join(root, name))
            except (InvalidDicomError, FileNotFoundError):
                continue
            else:
                dicom_files.append(os.path.join(root, name))
    return dicom_files


class TestManualFusionTab:
    """Sets up OnkoDICOM main window for testing the manual fusion tab."""
    __test__ = False

    def __init__(self):
        # Find test DICOM files
        testdata_path = Path.cwd().joinpath('test', 'testdata')
        selected_files = find_dicom_files(testdata_path)
        file_path = os.path.dirname(os.path.commonprefix(selected_files))
        read_data_dict, file_names_dict = get_datasets(selected_files)

        # Legacy: reindex CT if needed
        if "ct" in read_data_dict:
            read_data_dict = dict(enumerate(read_data_dict["ct"]))

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
