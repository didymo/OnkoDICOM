"""
Running plastimatch convert, and refusing a result that was not written.

plastimatch can exit 0 without writing its output: when ITK's SCIFIO
module cannot find its JARs (a relocated or upgraded Homebrew ITK), every
image write fails inside ITK, and plastimatch swallows the exception
(itk_image_save.cxx, 1.9.4 to master). The caller then reads a missing
file, and pyradiomics fails later with "Error reading image". So the
exit code is not enough: each conversion checks the file it was asked for.
"""
import os
import subprocess
import tempfile
import time
from pathlib import Path


class PlastimatchError(RuntimeError):
    """plastimatch convert failed, or reported success without its output."""


def _environment(empty_dir):
    """
    The environment for plastimatch. SCIFIO_PATH, when unset, points at
    empty_dir: SCIFIO then declines every format and ITK's own writers do
    the work, so a SCIFIO without its JARs cannot fail the write. A
    SCIFIO_PATH already set is left as it is.

    :param empty_dir: a directory only this process can write to, created
                      empty for this run (#32: a fixed name in a shared temp
                      directory could be created first by another user, with
                      JARs SCIFIO would then load).
    """
    env = dict(os.environ)
    if not env.get("SCIFIO_PATH"):
        env["SCIFIO_PATH"] = str(empty_dir)
    return env


def convert(args, written):
    """
    Run plastimatch convert with args, and check that it wrote its output.

    :param args: the arguments after "convert", as a list (no shell, so
                 paths with spaces or quotes need no quoting).
    :param written: a function of the start time, returning True when the
                    expected output exists, is not empty, and was written
                    since then (a file left by an earlier run is not output).
    :raises PlastimatchError: plastimatch is missing, exited non-zero, or
                              exited 0 without writing its output.
    """
    command = ["plastimatch", "convert", *args]
    # A second's slack: some filesystems keep modification times in whole seconds.
    started = time.time() - 1
    try:
        # mkdtemp's directory is new, private (0700) and removed afterwards.
        with tempfile.TemporaryDirectory(prefix="onkodicom-scifio-") as empty:
            result = subprocess.run(command, capture_output=True, text=True,
                                    env=_environment(empty), check=False)
    except OSError as error:
        raise PlastimatchError(
            f"could not run plastimatch: {error}") from error
    said = (result.stderr or result.stdout or "").strip()[-2000:]
    if result.returncode != 0:
        raise PlastimatchError(
            f"plastimatch convert exited {result.returncode}: {said}")
    if not written(started):
        raise PlastimatchError(
            "plastimatch convert reported success but wrote nothing "
            f"(command: {' '.join(command)}). Its output: {said or '(none)'}")


def _fresh(path, since):
    """path is a non-empty file written at or after since."""
    return path.is_file() and path.stat().st_size > 0 \
        and path.stat().st_mtime >= since


def convert_image(dicom_dir, image_path):
    """Convert the DICOM images in dicom_dir to the image file image_path."""
    image = Path(image_path)
    convert(["--input", str(dicom_dir), "--output-img", str(image)],
            lambda since: _fresh(image, since))


def convert_structures(rtss_path, dicom_dir, mask_dir):
    """
    Write one nrrd mask per structure in rtss_path into mask_dir,
    referenced to the images in dicom_dir.
    """
    masks = Path(mask_dir)
    convert(["--input", str(rtss_path), "--output-prefix", str(masks),
             "--prefix-format", "nrrd", "--referenced-ct", str(dicom_dir)],
            lambda since: masks.is_dir() and any(
                _fresh(m, since) for m in masks.glob("*.nrrd")))
