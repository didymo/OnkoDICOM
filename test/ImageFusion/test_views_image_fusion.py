import pytest
import os
from pathlib import Path
from pydicom import dcmread
from pydicom.errors import InvalidDicomError

from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.ImageLoading import get_datasets
from src.View.ImageFusion.ManualFusionLoader import ManualFusionLoader
from src.Model.VTKEngine import VTKEngine
from src.View.ImageFusion.MovingImageLoader import MovingImageLoader

"""
Tests for OnkoDICOM's image fusion infrastructure.

These tests verify that:
- DICOM image slices (CT, MR, PT) can be found and loaded from test data directories.
- The MovingImageLoader and ManualFusionLoader can load moving image series for fusion.
- The VTKEngine can load both fixed and moving image series for manual fusion.
- The fusion infrastructure works without requiring RTSS/ROI data or GUI components.

No GUI is launched; these are logic and engine-level tests only.
"""

def find_image_slices(folder):
    """
    Finds only image slice DICOM files (CT, MR, PT) in a folder.

    Args:
        folder (str or Path): The folder to search for DICOM files.

    Returns:
        list: List of file paths to DICOM image slices.
    """
    dicom_files = []
    for root, dirs, files in os.walk(folder, topdown=True):
        for name in files:
            filepath = os.path.join(root, name)
            try:
                ds = dcmread(filepath, stop_before_pixels=True)
                modality = getattr(ds, "Modality", "").upper()
                if modality in ("CT", "MR", "PT"):
                    dicom_files.append(filepath)
            except (InvalidDicomError, FileNotFoundError, AttributeError):
                continue
    return dicom_files

def find_first_two_image_dirs(testdata_path):
    """
    Finds the first two subdirectories with image slices in testdata_path.

    Args:
        testdata_path (Path): Path to the test data directory.

    Returns:
        tuple: The first two subdirectories containing image slices.
    """
    image_dirs = []
    for subdir in sorted(testdata_path.iterdir()):
        if subdir.is_dir():
            if files := find_image_slices(subdir):
                image_dirs.append(subdir)
            if len(image_dirs) == 2:
                break
    if len(image_dirs) < 2:
        raise RuntimeError("Not enough image series found in testdata for fusion test.")
    return image_dirs[0], image_dirs[1]

class DummyInterruptFlag:
    """
    Dummy interrupt flag for simulating an interruptible process.
    """
    def is_set(self):
        return False

class DummyProgressCallback:
    """
    Dummy progress callback for simulating progress reporting.
    """
    def emit(self, *args, **kwargs):
        pass

def test_moving_image_loader_debug(fusion_test_data):
    """
    Test that the MovingImageLoader can load moving images in manual mode.

    Args:
        fusion_test_data (tuple): Test data fixture.
    """
    _, _, _, moving_files = fusion_test_data
    loader = MovingImageLoader(moving_files, None, None)
    result = loader.load_manual_mode(DummyInterruptFlag(), DummyProgressCallback())
    print("MovingImageLoader.load_manual_mode result:", result)
    assert result

def sort_by_instance_number(files):
    """
    Sorts a list of DICOM files by their InstanceNumber attribute.

    Args:
        files (list): List of DICOM file paths.

    Returns:
        list: Sorted list of file paths.
    """
    def get_instance_number(f):
        try:
            return int(dcmread(f, stop_before_pixels=True).InstanceNumber)
        except (InvalidDicomError, FileNotFoundError, AttributeError, ValueError):
            return 0
    return sorted(files, key=get_instance_number)

@pytest.fixture
def fusion_test_data():
    """
    Pytest fixture to provide test data for fusion tests.

    Returns:
        tuple: (file_path, read_data_dict, file_names_dict, moving_files)
    """
    testdata_path = Path.cwd().joinpath('test', 'testdata')
    fixed_dir, moving_dir = find_first_two_image_dirs(testdata_path)
    fixed_files = find_image_slices(fixed_dir)
    moving_files = find_image_slices(moving_dir)
    moving_files = sort_by_instance_number(moving_files)
    file_path = str(fixed_dir)
    read_data_dict, file_names_dict = get_datasets(fixed_files)
    # Remove any RTSS from the dicts if present
    read_data_dict.pop("rtss", None)
    file_names_dict.pop("rtss", None)
    return file_path, read_data_dict, file_names_dict, moving_files

def test_manual_fusion_vtk_engine_exists(fusion_test_data):
    """
    Test that the VTK engine is created for manual fusion (no RTSS required).

    Args:
        fusion_test_data (tuple): Test data fixture.
    """
    file_path, read_data_dict, file_names_dict, moving_files = fusion_test_data
    patient_dict_container = PatientDictContainer()
    patient_dict_container.clear()
    patient_dict_container.set_initial_values(file_path, read_data_dict, file_names_dict)

    loader = MovingImageLoader(moving_files, None, None)
    result = loader.load_manual_mode(DummyInterruptFlag(), DummyProgressCallback())
    print("MovingImageLoader.load_manual_mode result:", result)
    assert result, "MovingImageLoader failed to load moving images"
    # Now try loading into VTKEngine
    engine = VTKEngine()
    fixed_loaded = engine.load_fixed(file_path)
    assert fixed_loaded, "VTKEngine failed to load fixed image"
    moving_dir = os.path.dirname(moving_files[0])
    moving_loaded = engine.load_moving(moving_dir)
    assert moving_loaded, "VTKEngine failed to load moving image"

def test_manual_fusion_fixed_and_moving_images_loaded(fusion_test_data):
    """
    Test that both fixed and moving images are loaded in the VTK engine.

    Args:
        fusion_test_data (tuple): Test data fixture.
    """
    file_path, read_data_dict, file_names_dict, moving_files = fusion_test_data
    patient_dict_container = PatientDictContainer()
    patient_dict_container.clear()
    patient_dict_container.set_initial_values(file_path, read_data_dict, file_names_dict)

    loader = ManualFusionLoader(moving_files)
    result = {}

    def _capture_result(res):
        result["value"] = res

    loader.signal_loaded.connect(_capture_result)
    loader.load(DummyInterruptFlag(), DummyProgressCallback())
    _wait_for_loader(result)
    _assert_vtk_engine_images_loaded(result["value"])

def _wait_for_loader(result_dict):
    """
    Waits for the loader to finish by checking for the "value" key in the result_dict.

    Args:
        result_dict (dict): Dictionary to check for loader result.

    Raises:
        RuntimeError: If the loader does not finish in time.
    """
    import time
    for _ in range(100):
        if "value" in result_dict:
            return
        time.sleep(0.1)
    raise RuntimeError("Loader did not finish in time")

def _assert_vtk_engine_images_loaded(loaded_tuple):
    """
    Asserts that the VTK engine has loaded both fixed and moving images.

    Args:
        loaded_tuple (tuple): (success, data) tuple from loader.
    """
    success, data = loaded_tuple
    assert success
    vtk_engine = data["vtk_engine"]
    fixed_image = _get_fixed_image_from_engine(vtk_engine)
    moving_image = _get_moving_image_from_engine(vtk_engine)
    assert fixed_image is not None
    assert moving_image is not None

def _get_fixed_image_from_engine(vtk_engine):
    """
    Helper to extract the fixed image from the VTK engine.

    Args:
        vtk_engine (VTKEngine): The VTK engine instance.

    Returns:
        The fixed image object, or None if not found.
    """
    if hasattr(vtk_engine, "get_fixed_image"):
        return vtk_engine.get_fixed_image()
    if hasattr(vtk_engine, "fixed_reader") and hasattr(vtk_engine.fixed_reader, "GetOutput"):
        return vtk_engine.fixed_reader.GetOutput()
    return None

def _get_moving_image_from_engine(vtk_engine):
    """
    Helper to extract the moving image from the VTK engine.

    Args:
        vtk_engine (VTKEngine): The VTK engine instance.

    Returns:
        The moving image object, or None if not found.
    """
    if hasattr(vtk_engine, "get_moving_image"):
        return vtk_engine.get_moving_image()
    if hasattr(vtk_engine, "moving_reader") and hasattr(vtk_engine.moving_reader, "GetOutput"):
        return vtk_engine.moving_reader.GetOutput()
    return None