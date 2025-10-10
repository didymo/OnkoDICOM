import os
from pathlib import Path
import pytest
from src.Controller.GUIController import MainWindow
from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.ImageLoading import get_datasets
from src.View.ImageFusion.TranslateRotateMenu import TranslateRotateMenu
from src.View.ImageFusion.ImageFusionAxialView import ImageFusionAxialView
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


def test_fusion_tab_loads(qtbot, fusion_test_object):
    """Test that the manual fusion tab loads and axial view is visible."""
    main_window = fusion_test_object.main_window
    main_window.show()

    # Check all fusion views exist and are visible
    assert hasattr(main_window, "image_fusion_view_axial")
    assert hasattr(main_window, "image_fusion_view_sagittal")
    assert hasattr(main_window, "image_fusion_view_coronal")
    assert hasattr(main_window, "image_fusion_single_view")
    # Check all fusion views exist and are visible
    assert hasattr(main_window, "image_fusion_view_axial")
    assert hasattr(main_window, "image_fusion_view_sagittal")
    assert hasattr(main_window, "image_fusion_view_coronal")
    assert hasattr(main_window, "image_fusion_single_view")
    _assert_views_visible(qtbot, [
        main_window.image_fusion_view_axial,
        main_window.image_fusion_view_sagittal,
        main_window.image_fusion_view_coronal,
        main_window.image_fusion_single_view,
    ])

    # Check fusion options tab and its controls
    assert hasattr(main_window, "fusion_options_tab")
    options: TranslateRotateMenu = main_window.fusion_options_tab
    assert isinstance(options, TranslateRotateMenu)
    _assert_translate_sliders(options)
    _assert_rotate_sliders(options)
    # Check color pair combo box
    assert hasattr(options, "color_pair_combo")
    options.color_pair_combo.setCurrentText("Blue + Yellow")
    assert options.color_pair_combo.currentText() == "Blue + Yellow"
    # Check opacity slider
    assert hasattr(options, "opacity_slider")
    options.opacity_slider.setValue(80)
    assert options.opacity_slider.value() == 80

    # Check that zoom in/out works for axial view
    axial = main_window.image_fusion_view_axial
    initial_zoom = axial.zoom
    axial.zoom_in()
    assert axial.zoom > initial_zoom
    axial.zoom_out()
    assert pytest.approx(axial.zoom, rel=1e-2) == initial_zoom

    # Optionally, check that update_metadata and update_view run without error
    axial.update_metadata()
    axial.update_view()

    # Check that the fusion options tab is present in the left panel
    assert main_window.left_panel.indexOf(options) != -1

    # Optionally, check that the four-views layout is present
    assert hasattr(main_window, "image_fusion_four_views")
    assert main_window.image_fusion_view.currentWidget() == main_window.image_fusion_four_views


def _assert_views_visible(qtbot, views):
    """Helper to assert all views are visible."""
    for view in views:
        qtbot.addWidget(view)
        view.show()
        assert view.isVisible()


def _assert_translate_sliders(options):
    """Helper to assert translation sliders work."""
    assert len(options.translate_sliders) == 3
    options.translate_sliders[0].setValue(10)
    assert options.translate_sliders[0].value() == 10
    options.translate_sliders[1].setValue(20)
    assert options.translate_sliders[1].value() == 20
    options.translate_sliders[2].setValue(-10)
    assert options.translate_sliders[2].value() == -10


def _assert_rotate_sliders(options):
    """Helper to assert rotation sliders work."""
    assert len(options.rotate_sliders) == 3
    options.rotate_sliders[0].setValue(30)
    assert options.rotate_sliders[0].value() == 30
    options.rotate_sliders[1].setValue(-30)
    assert options.rotate_sliders[1].value() == -30
    options.rotate_sliders[2].setValue(0)
    assert options.rotate_sliders[2].value() == 0


def _assert_color_pair_combo(options):
    """Helper to assert color pair combo box works."""
    assert hasattr(options, "color_pair_combo")
    options.color_pair_combo.setCurrentText("Blue + Yellow")
    assert options.color_pair_combo.currentText() == "Blue + Yellow"


def _assert_opacity_slider(options):
    """Helper to assert opacity slider works."""
    assert hasattr(options, "opacity_slider")
    options.opacity_slider.setValue(80)
    assert options.opacity_slider.value() == 80


def _assert_zoom_in_out(view):
    """Helper to assert zoom in/out works."""
    initial_zoom = view.zoom
    view.zoom_in()
    assert view.zoom > initial_zoom
    view.zoom_out()
    assert pytest.approx(view.zoom, rel=1e-2) == initial_zoom

