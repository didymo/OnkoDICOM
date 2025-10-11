import pytest
import os
from pathlib import Path
from pydicom import dcmread
from pydicom.errors import InvalidDicomError

from src.Model.MovingDictContainer import MovingDictContainer
from src.Model.PatientDictContainer import PatientDictContainer
from src.Model.ImageLoading import get_datasets
from src.View.ImageFusion.ManualFusionLoader import ManualFusionLoader
from src.Model.VTKEngine import VTKEngine

from src.View.ImageFusion.MovingImageLoader import MovingImageLoader


def find_image_slices(folder):
    """Finds only image slice DICOM files (CT, MR, PT) in a folder."""
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
    """Finds the first two subdirectories with image slices in testdata_path."""
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
    def is_set(self):
        return False

class DummyProgressCallback:
    def emit(self, *args, **kwargs):
        pass

def test_moving_image_loader_debug(fusion_test_data):
    _, _, _, moving_files = fusion_test_data
    loader = MovingImageLoader(moving_files, None, None)
    result = loader.load_manual_mode(DummyInterruptFlag(), DummyProgressCallback())
    print("MovingImageLoader.load_manual_mode result:", result)
    assert result

def sort_by_instance_number(files):
    def get_instance_number(f):
        try:
            return int(dcmread(f, stop_before_pixels=True).InstanceNumber)
        except Exception:
            return 0
    return sorted(files, key=get_instance_number)

@pytest.fixture
def fusion_test_data():
    # Dynamically find the first two image series directories
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
    """Test that the VTK engine is created for manual fusion (no RTSS required)."""
    file_path, read_data_dict, file_names_dict, moving_files = fusion_test_data
    patient_dict_container = PatientDictContainer()
    patient_dict_container.clear()
    patient_dict_container.set_initial_values(file_path, read_data_dict, file_names_dict)
    # Try loading the moving images directly

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
    # If you get here, both fixed and moving images loaded successfully

def test_manual_fusion_fixed_and_moving_images_loaded(qtbot, fusion_test_data):
    """Test that both fixed and moving images are loaded in the VTK engine."""
    file_path, read_data_dict, file_names_dict, moving_files = fusion_test_data
    patient_dict_container = PatientDictContainer()
    patient_dict_container.clear()
    patient_dict_container.set_initial_values(file_path, read_data_dict, file_names_dict)

    moving_dir = os.path.dirname(moving_files[0])
    moving_files_sorted = sorted(moving_files)
    moving_read_data_dict, moving_file_names_dict = get_datasets(moving_files_sorted)
    moving_dict_container = MovingDictContainer()
    moving_dict_container.clear()
    moving_dict_container.set_initial_values(moving_dir, moving_read_data_dict, moving_file_names_dict)

    print("fixed_dir:", file_path)
    print("fixed_files:", sorted(find_image_slices(file_path)))
    print("moving_dir:", moving_dir)
    print("moving_files:", moving_files_sorted)
    loader = ManualFusionLoader(moving_files)
    result = {}

    def on_loaded(res):
        result["value"] = res

    loader.signal_loaded.connect(on_loaded)
    loader.load(DummyInterruptFlag(), DummyProgressCallback())
    qtbot.waitUntil(lambda: "value" in result, timeout=10000)
    success, data = result["value"]
    assert success

    vtk_engine = data["vtk_engine"]
    # Debug: check what is actually loaded in the engine
    print("VTKEngine:", vtk_engine)
    if hasattr(vtk_engine, "fixed_reader"):
        print("fixed_reader:", vtk_engine.fixed_reader)
        if hasattr(vtk_engine.fixed_reader, "GetOutput"):
            print("fixed_reader.GetOutput():", vtk_engine.fixed_reader.GetOutput())
    if hasattr(vtk_engine, "moving_reader"):
        print("moving_reader:", vtk_engine.moving_reader)
        if hasattr(vtk_engine.moving_reader, "GetOutput"):
            print("moving_reader.GetOutput():", vtk_engine.moving_reader.GetOutput())
    if hasattr(vtk_engine, "get_fixed_image"):
        print("get_fixed_image():", vtk_engine.get_fixed_image())
    if hasattr(vtk_engine, "get_moving_image"):
        print("get_moving_image():", vtk_engine.get_moving_image())
    fixed_image = None
    if hasattr(vtk_engine, "get_fixed_image"):
        fixed_image = vtk_engine.get_fixed_image()
    if fixed_image is None and hasattr(vtk_engine, "fixed_reader") and hasattr(vtk_engine.fixed_reader, "GetOutput"):
        fixed_image = vtk_engine.fixed_reader.GetOutput()
    moving_image = None
    if hasattr(vtk_engine, "get_moving_image"):
        moving_image = vtk_engine.get_moving_image()
    if moving_image is None and hasattr(vtk_engine, "moving_reader") and hasattr(vtk_engine.moving_reader, "GetOutput"):
        moving_image = vtk_engine.moving_reader.GetOutput()
    assert fixed_image is not None
    assert moving_image is not None