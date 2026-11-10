"""
The app's PyRadiomics run with a structure set that has no structure with a
closed contour, only points or open lines or none (Gitea #37): no masks, so nothing to calculate. It must say so and stop,
not divide by the number of masks or write an empty CSV.
"""
import threading

import pytest
from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian

from src.Model import Radiomics
from src.Model.Plastimatch import PlastimatchError
from src.Model.batchprocessing.BatchProcessPyrad2PyradSR import \
    BatchProcessPyRad2PyRadSR
from src.View.PyradiProgressBar import (NO_ROIS_MESSAGE, PLASTIMATCH_FAILED,
                                        PyradiExtended)


def ct(path):
    ds = Dataset()
    ds.file_meta = FileMetaDataset()
    ds.file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
    ds.file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.2"
    ds.file_meta.MediaStorageSOPInstanceUID = "1.2.3.5"
    ds.PatientID = "P123"
    ds.save_as(str(path), enforce_file_format=True)
    return str(path)


def test_no_masks_gives_no_dataframe(qtbot, tmp_path):
    ext = PyradiExtended(str(tmp_path), {}, "")
    masks = tmp_path / "structures"
    masks.mkdir()
    assert ext.get_radiomics_df(str(tmp_path), "P", "img.nrrd", str(masks),
                                lambda *a: None) is None


def test_a_run_with_no_masks_says_so_and_writes_nothing(qtbot, tmp_path, monkeypatch):
    target = tmp_path / "out"
    ext = PyradiExtended(str(tmp_path), {0: ct(tmp_path / "ct.dcm"), "rtss": "rtss.dcm"},
                         str(target))
    said = []
    monkeypatch.setattr(ext, "my_callback", lambda percent, text: said.append((percent, text)))
    monkeypatch.setattr(ext, "convert_to_nrrd", lambda *a: None)
    # plastimatch accepted the structure set and wrote no mask (#38)
    monkeypatch.setattr(ext, "convert_rois_to_nrrd", lambda *a: None)
    ext.run()
    assert said[-1] == (100, NO_ROIS_MESSAGE)
    assert not (target / "nrrd").exists()
    assert not (target / "CSV").exists()


def test_a_plastimatch_failure_is_said_and_ends_the_run(qtbot, tmp_path, monkeypatch):
    """The window gets 100% and the reason, instead of waiting forever."""
    target = tmp_path / "out"
    ext = PyradiExtended(str(tmp_path), {0: ct(tmp_path / "ct.dcm"), "rtss": "rtss.dcm"},
                         str(target))
    said = []
    monkeypatch.setattr(ext, "my_callback", lambda percent, text: said.append((percent, text)))
    monkeypatch.setattr(ext, "convert_to_nrrd", lambda *a: None)

    def fails(*a):
        raise PlastimatchError("plastimatch convert exited 3: cannot read input")
    monkeypatch.setattr(ext, "convert_rois_to_nrrd", fails)
    ext.run()
    assert said[-1] == (100, PLASTIMATCH_FAILED + "plastimatch convert exited 3: cannot read input")
    assert not (target / "CSV").exists()


class Container:
    """The parts of PatientDictContainer that start() reads."""

    def __init__(self, path):
        self.path = path
        self.filepaths = {"rtss": "rtss.dcm"}
        rtss = Dataset()
        rtss.PatientID = "P123"
        self.dataset = {"rtss": rtss}
        self.cleared = False

    def clear(self):
        self.cleared = True


class Signal:
    def emit(self, *args):
        pass


@pytest.mark.parametrize("step", ["convert_to_nrrd", "convert_rois_to_nrrd"])
def test_a_batch_plastimatch_failure_is_recorded_for_the_patient(tmp_path, monkeypatch, step):
    """Either conversion failing ends this patient's run with its own
    summary, and the batch goes on."""
    process = BatchProcessPyRad2PyRadSR.__new__(BatchProcessPyRad2PyRadSR)
    process.patient_dict_container = Container(str(tmp_path))
    process.interrupt_flag = threading.Event()
    process.progress_callback = Signal()
    process.ready = True
    monkeypatch.setattr(Radiomics, "convert_to_nrrd", lambda *a: None)

    def fails(*a):
        raise PlastimatchError("wrote nothing")
    monkeypatch.setattr(Radiomics, step, fails)
    assert process.start() is False
    assert process.summary == "PLASTIMATCH_FAILED"
    assert process.patient_dict_container.cleared
