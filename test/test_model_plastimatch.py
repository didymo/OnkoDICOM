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
        (d / "Body.nrrd").write_bytes(b"NRRD0004")
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


def test_masks_that_are_written_are_accepted(tmp_path, fake):
    fake("write")
    masks = tmp_path / "nrrd" / "structures"
    Plastimatch.convert_structures(tmp_path / "rtss.dcm", tmp_path, masks)
    assert [m.name for m in masks.glob("*.nrrd")] == ["Body.nrrd"]


def test_success_without_any_mask_is_refused(tmp_path, fake):
    fake("silent")
    masks = tmp_path / "structures"
    masks.mkdir()
    with pytest.raises(PlastimatchError, match="wrote nothing"):
        Plastimatch.convert_structures(tmp_path / "rtss.dcm", tmp_path, masks)


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
