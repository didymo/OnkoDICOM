"""
plastimatch convert's result is checked, not only its exit code (Gitea #26).

A fake plastimatch on PATH stands in for the real one: it writes its output,
or exits 0 having written nothing (what a SCIFIO without its JARs does), or
fails. It records the arguments and SCIFIO_PATH it was given.
"""
import json
import os
import sys
import tempfile
import time
from pathlib import Path

import pytest
from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian

from src.Model import Plastimatch
from src.Model.Plastimatch import PlastimatchError

pytestmark = pytest.mark.skipif(
    sys.platform == "win32",
    reason="the fake plastimatch is a script; Windows runs only .exe "
           "without a shell")

FAKE = r'''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
args = sys.argv[1:]
scifio = os.environ.get("SCIFIO_PATH")
d = Path(scifio) if scifio else None
state = None
if d is not None and d.is_dir():
    state = {"entries": sorted(p.name for p in d.iterdir()),
             "mode": oct(d.stat().st_mode & 0o777)}
Path(os.environ["FAKE_LOG"]).write_text(json.dumps(
    {"args": args, "scifio": scifio, "scifio_dir": state}))
mode = os.environ["FAKE_MODE"]
if mode == "fail":
    print("cannot read input", file=sys.stderr)
    sys.exit(3)
if mode == "write":
    if "--output-img" in args:
        Path(args[args.index("--output-img") + 1]).write_bytes(b"NRRD0004")
    else:
        d = Path(args[args.index("--output-prefix") + 1])
        d.mkdir(parents=True, exist_ok=True)
        for name in os.environ.get("FAKE_MASKS", "Body").split(","):
            if name:
                (d / f"{name}.nrrd").write_bytes(b"NRRD0004")
print("done")
'''


@pytest.fixture
def fake(tmp_path, monkeypatch):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    script = bin_dir / "plastimatch"
    script.write_text(FAKE)
    script.chmod(0o755)
    log = tmp_path / "log.json"
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    monkeypatch.setenv("FAKE_LOG", str(log))
    monkeypatch.delenv("SCIFIO_PATH", raising=False)

    def use(mode):
        monkeypatch.setenv("FAKE_MODE", mode)
        return lambda: json.loads(log.read_text())
    return use


def test_an_image_that_is_written_is_accepted(tmp_path, fake):
    fake("write")
    out = tmp_path / "patient it's.nrrd"
    Plastimatch.convert_image(tmp_path / "dicom dir", out)
    assert out.read_bytes() == b"NRRD0004"


def test_success_without_the_image_is_refused(tmp_path, fake):
    fake("silent")
    out = tmp_path / "patient.nrrd"
    with pytest.raises(PlastimatchError, match="reported success but wrote nothing"):
        Plastimatch.convert_image(tmp_path, out)


def test_an_image_left_by_an_earlier_run_is_not_this_runs_output(tmp_path, fake):
    fake("silent")
    out = tmp_path / "patient.nrrd"
    out.write_bytes(b"old")
    old = time.time() - 3600
    os.utime(out, (old, old))
    with pytest.raises(PlastimatchError, match="wrote nothing"):
        Plastimatch.convert_image(tmp_path, out)


def test_a_failed_conversion_says_why(tmp_path, fake):
    fake("fail")
    with pytest.raises(PlastimatchError, match="exited 3: cannot read input"):
        Plastimatch.convert_image(tmp_path, tmp_path / "patient.nrrd")


def contour(kind="CLOSED_PLANAR"):
    item = Dataset()
    item.ContourGeometricType = kind
    item.ContourData = [0, 0, 0, 1, 0, 0, 1, 1, 0] if kind != "POINT" else [0, 0, 0]
    item.NumberOfContourPoints = len(item.ContourData) // 3
    return item


def rtss(path, contoured=("Body",), empty=(), contours=None):
    """A structure set: ROIs with a closed contour each, and ROIs with none.
    contours maps an ROI name to its own list of contour items."""
    ds = Dataset()
    ds.file_meta = FileMetaDataset()
    ds.file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
    ds.file_meta.MediaStorageSOPClassUID = "1.2.840.10008.5.1.4.1.1.481.3"
    ds.file_meta.MediaStorageSOPInstanceUID = "1.2.3.4"
    ds.SOPClassUID = ds.file_meta.MediaStorageSOPClassUID
    ds.SOPInstanceUID = ds.file_meta.MediaStorageSOPInstanceUID
    contours = contours or {}
    names = list(contoured) + list(empty) + [n for n in contours if n not in contoured]
    ds.StructureSetROISequence = []
    ds.ROIContourSequence = []
    for number, name in enumerate(names, 1):
        roi = Dataset()
        roi.ROINumber, roi.ROIName = number, name
        ds.StructureSetROISequence.append(roi)
        item = Dataset()
        item.ReferencedROINumber = number
        if name in contours:
            item.ContourSequence = contours[name]
        elif name in contoured:
            item.ContourSequence = [contour()]
        ds.ROIContourSequence.append(item)
    ds.save_as(str(path), enforce_file_format=True)
    return path


def test_masks_that_are_written_are_accepted(tmp_path, fake):
    fake("write")
    masks = tmp_path / "nrrd" / "structures"
    Plastimatch.convert_structures(rtss(tmp_path / "rtss.dcm"), tmp_path, masks)
    assert [m.name for m in masks.glob("*.nrrd")] == ["Body.nrrd"]


def test_success_without_any_mask_is_refused(tmp_path, fake):
    fake("silent")
    masks = tmp_path / "structures"
    masks.mkdir()
    with pytest.raises(PlastimatchError, match="wrote nothing"):
        Plastimatch.convert_structures(rtss(tmp_path / "rtss.dcm"), tmp_path, masks)


def test_fewer_masks_than_contoured_structures_is_refused(tmp_path, fake, monkeypatch):
    """#31: plastimatch swallows each failed mask write, so some can be missing."""
    fake("write")
    monkeypatch.setenv("FAKE_MASKS", "Body,Liver")
    path = rtss(tmp_path / "rtss.dcm", contoured=("Body", "Liver", "Spinal Cord"))
    with pytest.raises(PlastimatchError, match=r"2 mask\(s\) for 3 structure\(s\)") as error:
        Plastimatch.convert_structures(path, tmp_path, tmp_path / "structures")
    assert "Spinal Cord" in str(error.value)


def test_a_mask_left_by_an_earlier_run_does_not_make_up_the_count(tmp_path, fake, monkeypatch):
    fake("write")
    masks = tmp_path / "structures"
    masks.mkdir()
    old = masks / "Liver.nrrd"
    old.write_bytes(b"old")
    os.utime(old, (time.time() - 3600,) * 2)
    monkeypatch.setenv("FAKE_MASKS", "Body")
    with pytest.raises(PlastimatchError, match=r"1 mask\(s\) for 2"):
        Plastimatch.convert_structures(rtss(tmp_path / "rtss.dcm", contoured=("Body", "Liver")),
                                       tmp_path, masks)


def test_a_structure_without_contours_is_not_expected(tmp_path, fake):
    fake("write")
    path = rtss(tmp_path / "rtss.dcm", contoured=("Body",), empty=("Marker",))
    Plastimatch.convert_structures(path, tmp_path, tmp_path / "structures")


def test_a_structure_with_only_a_point_is_not_expected(tmp_path, fake):
    """Clement, review of #38: plastimatch skips POINT contours, so a
    reference point gets no mask and must not be counted."""
    fake("write")
    path = rtss(tmp_path / "rtss.dcm", contours={"Iso": [contour("POINT")]})
    assert Plastimatch.contoured_roi_names(path) == ["Body"]
    Plastimatch.convert_structures(path, tmp_path, tmp_path / "structures")


def test_a_point_beside_a_closed_contour_is_expected(tmp_path, fake):
    fake("write")
    path = rtss(tmp_path / "rtss.dcm",
                contours={"Liver": [contour("POINT"), contour()]})
    assert Plastimatch.contoured_roi_names(path) == ["Body", "Liver"]
    with pytest.raises(PlastimatchError, match=r"1 mask\(s\) for 2"):
        Plastimatch.convert_structures(path, tmp_path, tmp_path / "structures")


def test_open_and_pointless_contours_are_not_expected(tmp_path, fake):
    no_points = contour()
    no_points.NumberOfContourPoints = 0
    path = rtss(tmp_path / "rtss.dcm", contoured=(),
                contours={"Line": [contour("OPEN_PLANAR")], "Empty": [no_points]})
    assert Plastimatch.contoured_roi_names(path) == []


def test_nothing_to_write_is_not_a_failure(tmp_path, fake):
    """No contoured structure: an empty result is right, and radiomics reports no ROIs."""
    fake("silent")
    path = rtss(tmp_path / "rtss.dcm", contoured=(), empty=("Marker",))
    Plastimatch.convert_structures(path, tmp_path, tmp_path / "structures")


def test_an_unreadable_structure_set_is_said(tmp_path, fake):
    fake("write")
    bad = tmp_path / "rtss.dcm"
    bad.write_bytes(b"not dicom")
    with pytest.raises(PlastimatchError, match="could not read the structures"):
        Plastimatch.convert_structures(bad, tmp_path, tmp_path / "structures")


def test_paths_go_through_as_arguments_not_shell_words(tmp_path, fake):
    seen = fake("write")
    awkward = tmp_path / 'a "quoted" dir; rm -rf x'
    Plastimatch.convert_image(awkward, tmp_path / "out.nrrd")
    assert seen()["args"][:3] == ["convert", "--input", str(awkward)]


def test_scifio_is_pointed_at_nothing_only_when_unset(tmp_path, fake, monkeypatch):
    seen = fake("write")
    Plastimatch.convert_image(tmp_path, tmp_path / "a.nrrd")
    unset = seen()
    assert unset["scifio_dir"] == {"entries": [], "mode": "0o700"}
    monkeypatch.setenv("SCIFIO_PATH", "/opt/scifio/jars")
    Plastimatch.convert_image(tmp_path, tmp_path / "b.nrrd")
    assert seen()["scifio"] == "/opt/scifio/jars"


def test_scifio_directory_is_new_each_run_and_removed(tmp_path, fake):
    """#32: never a name another user could have created first."""
    seen = fake("write")
    Plastimatch.convert_image(tmp_path, tmp_path / "a.nrrd")
    first = seen()["scifio"]
    Plastimatch.convert_image(tmp_path, tmp_path / "b.nrrd")
    second = seen()["scifio"]
    assert first != second
    assert not Path(first).exists() and not Path(second).exists()


def test_a_planted_directory_of_the_old_fixed_name_is_not_used(tmp_path, fake, monkeypatch):
    """#32: JARs left in the name #30 used must not reach SCIFIO."""
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path / "tmp"))
    planted = tmp_path / "tmp" / "onkodicom-scifio-none"
    planted.mkdir(parents=True)
    (planted / "bioformats_package.jar").write_bytes(b"not a jar")
    seen = fake("write")
    Plastimatch.convert_image(tmp_path, tmp_path / "a.nrrd")
    assert Path(seen()["scifio"]).parent == tmp_path / "tmp"
    assert Path(seen()["scifio"]) != planted
    assert seen()["scifio_dir"]["entries"] == []


def test_a_directory_that_cannot_be_made_is_said(tmp_path, fake, monkeypatch):
    fake("write")
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path / "missing"))
    with pytest.raises(PlastimatchError, match="could not make an empty directory"):
        Plastimatch.convert_image(tmp_path, tmp_path / "a.nrrd")


def test_no_plastimatch_at_all_is_said(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", str(tmp_path))
    with pytest.raises(PlastimatchError, match="could not run plastimatch"):
        Plastimatch.convert_image(tmp_path, tmp_path / "a.nrrd")


@pytest.mark.plastimatch
def test_real_plastimatch_writes_one_mask_per_contoured_structure(tmp_path):
    """#31, on the real test data and the real plastimatch: the count the
    check relies on is what plastimatch actually writes."""
    data = Path.cwd() / "test" / "testdata" / "DICOM-RT-02"
    structures = data / "20191031-215249_m.dcm"
    expected = Plastimatch.contoured_roi_names(structures)
    masks = tmp_path / "structures"
    Plastimatch.convert_structures(structures, data, masks)
    assert len(list(masks.glob("*.nrrd"))) == len(expected) == 9
