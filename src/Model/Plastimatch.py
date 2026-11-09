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

import pydicom
import pydicom.errors


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
    # mkdtemp's directory is new, private (0700) and removed afterwards.
    try:
        scratch = tempfile.TemporaryDirectory(prefix="onkodicom-scifio-")
    except OSError as error:
        raise PlastimatchError(
            f"could not make an empty directory for SCIFIO_PATH: {error}"
        ) from error
    with scratch as empty:
        try:
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


def contoured_roi_names(rtss_path):
    """
    The names of the structures in rtss_path that have at least one contour:
    the ones plastimatch writes a mask for.

    :raises PlastimatchError: the structure set cannot be read.
    """
    try:
        rtss = pydicom.dcmread(str(rtss_path))
        names = {roi.ROINumber: roi.ROIName
                 for roi in rtss.StructureSetROISequence}
        contoured = {item.ReferencedROINumber
                     for item in rtss.ROIContourSequence
                     if getattr(item, "ContourSequence", None)}
    except (OSError, AttributeError, pydicom.errors.InvalidDicomError) \
            as error:
        raise PlastimatchError(
            f"could not read the structures in {rtss_path}: {error}"
        ) from error
    return sorted(names[n] for n in contoured if n in names)


def convert_structures(rtss_path, dicom_dir, mask_dir):
    """
    Write one nrrd mask per structure in rtss_path into mask_dir,
    referenced to the images in dicom_dir.

    plastimatch swallows each failed mask write separately, so a run can
    exit 0 having written only some of them (#31). Fewer fresh masks than
    structures with contours is refused, since radiomics would otherwise
    silently leave the rest out.
    """
    expected = contoured_roi_names(rtss_path)
    masks = Path(mask_dir)
    found = []

    def written(since):
        found[:] = sorted(m.name for m in masks.glob("*.nrrd")
                          if _fresh(m, since)) if masks.is_dir() else []
        # A structure set with nothing to write has written everything
        # (radiomics then reports no ROIs, as before #30).
        return bool(found) or not expected

    convert(["--input", str(rtss_path), "--output-prefix", str(masks),
             "--prefix-format", "nrrd", "--referenced-ct", str(dicom_dir)],
            written)
    if len(found) < len(expected):
        raise PlastimatchError(
            f"plastimatch wrote {len(found)} mask(s) for {len(expected)} "
            f"structure(s) with contours. Structures: {', '.join(expected)}. "
            f"Masks written: {', '.join(found)}")
