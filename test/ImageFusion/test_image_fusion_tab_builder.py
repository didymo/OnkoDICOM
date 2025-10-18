# test/test_view_image_fusion_tab_builder.py
import pytest
from unittest.mock import MagicMock

from src.View.ImageFusion.ImageFusionTabBuilder import ImageFusionTabBuilder

class DummyMainWindow:
    """
    Dummy main window class for testing ImageFusionTabBuilder.

    This mock class records calls to setup methods and simulates the attributes and methods
    expected by the ImageFusionTabBuilder. It is used to verify that the builder interacts
    with the main window as expected during tab construction.
    """
    def __init__(self):
        self.structures_tab = MagicMock()
        self.structures_tab.rois = {}
        self.structures_tab.update_ui = MagicMock()
        self.left_panel = MagicMock()
        self.right_panel = MagicMock()
        self.last_fusion_slice_orientation = None
        self.last_fusion_slice_idx = None
        self.images = {"vtk_engine": "dummy_engine"}
        self.action_handler = MagicMock()
        self.setup_calls = []

    def _init_fusion_views(self, vtk_engine):
        """Record initialization of fusion views."""
        self.setup_calls.append(("init_fusion_views", vtk_engine))
        self.image_fusion_single_view = MagicMock()
        self.image_fusion_view_axial = MagicMock()
        self.image_fusion_view_sagittal = MagicMock()
        self.image_fusion_view_coronal = MagicMock()

    def init_windowing_slider(self):
        """Record windowing slider initialization."""
        self.setup_calls.append("init_windowing_slider")

    def init_roi_transfer_option_view(self):
        """Record ROI transfer option view initialization."""
        self.setup_calls.append("init_roi_transfer_option_view")

    def init_fusion_slice_tracking(self):
        """Record fusion slice tracking initialization."""
        self.setup_calls.append("init_fusion_slice_tracking")

    def apply_transform_if_present(self, vtk_engine):
        """Record application of transform if present."""
        self.setup_calls.append(("apply_transform_if_present", vtk_engine))

    def connect_slider_callbacks(self):
        """Record connection of slider callbacks."""
        self.setup_calls.append("connect_slider_callbacks")

    def set_slider_ranges(self):
        """Record setting of slider ranges."""
        self.setup_calls.append("set_slider_ranges")

    def setup_static_overlays_if_no_vtk(self, vtk_engine):
        """Record setup of static overlays if no VTK engine is present."""
        self.setup_calls.append(("setup_static_overlays_if_no_vtk", vtk_engine))

    def rescale_and_update_fusion_views(self):
        """Record rescaling and updating of fusion views."""
        self.setup_calls.append("rescale_and_update_fusion_views")

    def setup_fusion_four_views_layout(self):
        """Record setup of the four-views layout."""
        self.setup_calls.append("setup_fusion_four_views_layout")

    def finalize_fusion_tab(self):
        """Record finalization of the fusion tab."""
        self.setup_calls.append("finalize_fusion_tab")

@pytest.fixture
def dummy_main_window():
    """
    Pytest fixture to provide a fresh DummyMainWindow instance for each test.
    """
    return DummyMainWindow()

@pytest.mark.parametrize(
    "manual,expected_methods",
    [
        (
            True,
            [
                "init_windowing_slider",
                "init_roi_transfer_option_view",
                "init_fusion_slice_tracking",
                "connect_slider_callbacks",
                "set_slider_ranges",
                "rescale_and_update_fusion_views",
                "setup_fusion_four_views_layout",
                "finalize_fusion_tab",
            ],
        ),
        (
            False,
            [
                "init_windowing_slider",
                "init_roi_transfer_option_view",
                "init_fusion_slice_tracking",
                "connect_slider_callbacks",
                "set_slider_ranges",
                "rescale_and_update_fusion_views",
                "setup_fusion_four_views_layout",
                "finalize_fusion_tab",
            ],
        ),
    ],
)
def test_image_fusion_tab_builder(dummy_main_window, manual, expected_methods):
    """
    Test that ImageFusionTabBuilder correctly sets up the main window for both manual and auto fusion.

    This test verifies that the builder creates the fusion options tab (for manual) and calls all
    expected setup methods on the main window when building the fusion tab.
    """
    builder = ImageFusionTabBuilder(dummy_main_window, manual=manual)
    builder.build()

    # Check that the fusion options tab was created (should always exist for compatibility)
    assert hasattr(dummy_main_window, "fusion_options_tab")

    # Assert each expected method was called at least once, without using a loop in the test logic
    assert any("init_windowing_slider" in str(call) for call in dummy_main_window.setup_calls)
    assert any("init_roi_transfer_option_view" in str(call) for call in dummy_main_window.setup_calls)
    assert any("init_fusion_slice_tracking" in str(call) for call in dummy_main_window.setup_calls)
    assert any("connect_slider_callbacks" in str(call) for call in dummy_main_window.setup_calls)
    assert any("set_slider_ranges" in str(call) for call in dummy_main_window.setup_calls)
    assert any("rescale_and_update_fusion_views" in str(call) for call in dummy_main_window.setup_calls)
    assert any("setup_fusion_four_views_layout" in str(call) for call in dummy_main_window.setup_calls)
    assert any("finalize_fusion_tab" in str(call) for call in dummy_main_window.setup_calls)