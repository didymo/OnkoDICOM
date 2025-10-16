import pytest
from unittest.mock import patch, MagicMock, Mock
import os

from src.Model.AutoSegmentation.AutoSegmentation import AutoSegmentation

@pytest.fixture
def controller_mock():
    ctrl = Mock()
    ctrl.update_progress_text = Mock()
    ctrl.on_segmentation_finished = Mock()
    ctrl.on_segmentation_error = Mock()
    return ctrl

@pytest.fixture
def patient_dict_container_patch(tmp_path):
    # Arrange
    with patch("src.Model.AutoSegmentation.AutoSegmentation.PatientDictContainer") as pdc:
        instance = pdc.return_value
        instance.path = str(tmp_path)
        instance.filepaths = {
            "ct1": str(tmp_path / "ct1.dcm"),
            "rtdose": str(tmp_path / "dose.dcm"),
            "rtss": str(tmp_path / "rtss.dcm"),
            "rtplan": str(tmp_path / "rtplan.dcm"),
        }
        # Create dummy files for copy
        for k, v in instance.filepaths.items():
            if not os.path.exists(v):
                with open(v, "w") as f:
                    f.write("dummy")
        yield

@pytest.fixture
def signals_patch():
    with patch("src.Model.AutoSegmentation.AutoSegmentation.SegmentationWorkerSignals") as signals_cls:
        signals = signals_cls.return_value
        signals.progress_updated = Mock()
        signals.finished = Mock()
        signals.error = Mock()
        signals.progress_updated.emit = Mock()
        signals.finished.emit = Mock()
        signals.error.emit = Mock()
        yield signals

@pytest.fixture
def deps_patch():
    with patch("src.Model.AutoSegmentation.AutoSegmentation.ConsoleOutputStream") as cos, \
         patch("src.Model.AutoSegmentation.AutoSegmentation.redirect_output_to_gui"), \
         patch("src.Model.AutoSegmentation.AutoSegmentation.setup_logging"):
        yield

def test_init_connects_signals(controller_mock, patient_dict_container_patch, signals_patch):
    # Arrange
    # Act
    auto = AutoSegmentation(controller_mock)
    # Assert
    signals_patch.progress_updated.connect.assert_called_with(controller_mock.update_progress_text)
    signals_patch.finished.connect.assert_called_with(controller_mock.on_segmentation_finished)
    signals_patch.error.connect.assert_called_with(controller_mock.on_segmentation_error)

def test_connect_terminal_stream_to_gui(controller_mock, patient_dict_container_patch, deps_patch):
    # Arrange
    auto = AutoSegmentation(controller_mock)
    # Act
    auto._connect_terminal_stream_to_gui()
    # Assert
    # Should connect output_stream.new_text to controller.update_progress_text
    # and call redirect_output_to_gui and setup_logging (patched)

def test_prepare_output_paths_creates_dir(tmp_path, controller_mock, patient_dict_container_patch):
    # Arrange
    with patch("src.Model.AutoSegmentation.AutoSegmentation.PatientDictContainer") as pdc:
        instance = pdc.return_value
        instance.path = str(tmp_path)
        instance.filepaths = {}
        auto = AutoSegmentation(controller_mock)
        # Act
        out_dir, out_rt = auto._prepare_output_paths()
        # Assert
        assert os.path.exists(out_dir)
        assert out_dir.endswith("segmentations")
        assert out_rt.endswith("rtss.dcm")

def test_copy_temp_dicom_dir_copies_files(controller_mock, patient_dict_container_patch, signals_patch):
    # Arrange
    auto = AutoSegmentation(controller_mock)
    auto.file_paths = {
        "ct1": auto.dicom_dir + "/ct1.dcm",
        "rtdose": auto.dicom_dir + "/dose.dcm",
        "rtss": auto.dicom_dir + "/rtss.dcm",
        "rtplan": auto.dicom_dir + "/rtplan.dcm",
    }
    # Act
    auto._copy_temp_dicom_dir()
    # Assert
    assert auto.dicom_temp_dir is not None
    # Only ct1 should be copied
    copied = os.listdir(auto.dicom_temp_dir.name)
    assert "ct1.dcm" in copied
    assert "dose.dcm" not in copied
    assert "rtss.dcm" not in copied
    assert "rtplan.dcm" not in copied

def test_copy_temp_dicom_dir_raises_value_error(controller_mock, patient_dict_container_patch):
    # Arrange
    auto = AutoSegmentation(controller_mock)
    auto.file_paths = {}
    # Act & Assert
    with pytest.raises(ValueError):
        auto._copy_temp_dicom_dir()

def test_copy_temp_dicom_dir_emits_error_on_copy_failure(controller_mock, patient_dict_container_patch, signals_patch):
    # Arrange
    auto = AutoSegmentation(controller_mock)
    auto.file_paths = {"ct1": "/nonexistent/file.dcm"}
    # Act
    auto._copy_temp_dicom_dir()
    # Assert
    signals_patch.error.emit.assert_called()

def test_run_totalsegmentation_calls_totalsegmentator(controller_mock, patient_dict_container_patch):
    # Arrange
    auto = AutoSegmentation(controller_mock)
    auto.dicom_temp_dir = MagicMock()
    auto.dicom_temp_dir.name = "tempdir"
    with patch("src.Model.AutoSegmentation.AutoSegmentation.totalsegmentator") as totalseg:
        # Act
        auto._run_totalsegmentation("total", ["roi1", "roi2"], "outdir")
        # Assert
        totalseg.assert_called_once()
        args, kwargs = totalseg.call_args
        assert kwargs["input"] == "tempdir"
        assert kwargs["output"] == "outdir"
        assert kwargs["task"] == "total"
        assert set(kwargs["roi_subset"]) == {"roi1", "roi2"}
        assert kwargs["output_type"] == "nifti"
        assert kwargs["device"] == "gpu"

def test_convert_to_rtstruct_calls_conversion_and_emits(controller_mock, patient_dict_container_patch, signals_patch):
    # Arrange
    auto = AutoSegmentation(controller_mock)
    auto.dicom_temp_dir = MagicMock()
    auto.dicom_temp_dir.name = "tempdir"
    with patch("src.Model.AutoSegmentation.AutoSegmentation.nifti_to_rtstruct_conversion") as conv:
        # Act
        auto._convert_to_rtstruct("nifti_dir", "output_rt")
        # Assert
        conv.assert_called_once_with("nifti_dir", "tempdir", "output_rt")
        signals_patch.progress_updated.emit.assert_called_with("Conversion to RTSTRUCT complete.")

@pytest.mark.parametrize(
    "exists, rmtree_raises, expected_emit, id",
    [
        (True, False, "Nifti files removed.", "happy_path"),
        (False, False, "Nifti files not found for removal.", "not_found"),
        (True, True, "Failed to remove Nifti files: test", "rmtree_error"),
    ],
    ids=["happy_path", "not_found", "rmtree_error"]
)
def test_cleanup_nifti_dir_various(controller_mock, patient_dict_container_patch, signals_patch, exists, rmtree_raises, expected_emit, id):
    # Arrange
    auto = AutoSegmentation(controller_mock)
    with patch("os.path.exists", return_value=exists), \
         patch("shutil.rmtree", side_effect=Exception("test") if rmtree_raises else None):
        # Act
        auto._cleanup_nifti_dir("outdir")
        # Assert
        signals_patch.progress_updated.emit.assert_called_with(expected_emit)

def test_cleanup_temp_dir_calls_cleanup(controller_mock, patient_dict_container_patch):
    # Arrange
    auto = AutoSegmentation(controller_mock)
    auto.dicom_temp_dir = MagicMock()
    # Act
    auto._cleanup_temp_dir()
    # Assert
    auto.dicom_temp_dir.cleanup.assert_called_once()

def test_cleanup_temp_dir_none(controller_mock, patient_dict_container_patch):
    # Arrange
    auto = AutoSegmentation(controller_mock)
    auto.dicom_temp_dir = None
    # Act
    auto._cleanup_temp_dir()
    # Assert
    # Should not raise

def test_run_segmentation_workflow_happy_path(controller_mock, patient_dict_container_patch, signals_patch, deps_patch):
    # Arrange
    auto = AutoSegmentation(controller_mock)
    with patch.object(auto, "_prepare_output_paths", return_value=("outdir", "out_rt")), \
         patch.object(auto, "_copy_temp_dicom_dir"), \
         patch.object(auto, "_run_totalsegmentation"), \
         patch.object(auto, "_convert_to_rtstruct"), \
         patch.object(auto, "_cleanup_nifti_dir"), \
         patch.object(auto, "_cleanup_temp_dir"):
        # Act
        auto.run_segmentation_workflow("total", ["roi1"])
        # Assert
        signals_patch.progress_updated.emit.assert_any_call("Starting segmentation workflow...")
        signals_patch.finished.emit.assert_called_once()

def test_run_segmentation_workflow_error(controller_mock, patient_dict_container_patch, signals_patch, deps_patch):
    # Arrange
    auto = AutoSegmentation(controller_mock)
    with patch.object(auto, "_prepare_output_paths", return_value=("outdir", "out_rt")), \
         patch.object(auto, "_copy_temp_dicom_dir", side_effect=Exception("fail")), \
         patch.object(auto, "_cleanup_temp_dir"):
        # Act
        auto.run_segmentation_workflow("total", ["roi1"])
        # Assert
        signals_patch.error.emit.assert_called()
