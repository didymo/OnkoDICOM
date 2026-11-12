"""Pseudonymisation of DICOM datasets for OnkoDICOM, relying only on pydicom.

Rewritten from the pseudonymisation and anonymisation in pymedphys 0.41.0
(``pymedphys._experimental.pseudonymisation`` and ``pymedphys._dicom.anonymise``).
Stuart Swerdloff, who wrote the pymedphys pseudonymisation code, agreed on
13 November 2026 to its use here under OnkoDICOM's licence.

For the same pepper and jitter, ``pseudonymise_dataset`` gives the same dataset as
``pymedphys.dicom.anonymise`` called with pymedphys's pseudonymisation strategy and
keywords, as OnkoDICOM called it before. The intended differences:

- An element is "known" if pydicom's data dictionary has it, where pymedphys used its
  own older copy of that dictionary. pydicom knows 838 more standard tags, and pymedphys
  refused a dataset containing any of them.
- The file meta is pseudonymised too. pymedphys left the original SOP Instance UID in
  ``file_meta.MediaStorageSOPInstanceUID`` of every file (#63).

No claim of conformance to any DICOM Application Level Confidentiality Profile is made.
"""

import copy
import logging
import os

import pydicom
from pydicom import datadict

from src.Model.Pseudonymisation import strategy
from src.Model.Pseudonymisation.keywords import IDENTIFYING_KEYWORDS, IDENTIFYING_UIDS

logger = logging.getLogger(__name__)

# The pseudonymisation keywords: the identifying keywords other than sequences (whose
# contents are pseudonymised instead, pymedphys issue #1034), plus the identifying UIDs.
PSEUDONYMISATION_KEYWORDS: tuple[str, ...] = tuple(
    sorted(
        {k for k in IDENTIFYING_KEYWORDS if not k.endswith("Sequence")} | set(IDENTIFYING_UIDS)
    )
)

SOP_CLASS_NAME_FILENAME_PREFIXES = {
    "CT Image Storage": "CT",
    "Enhanced CT Image Storage": "CTE",
    "MR Image Storage": "MR",
    "Enhanced MR Image Storage": "MRE",
    "Positron Emission Tomography Image Storage": "PT",
    "Enhanced PET Image Storage": "PTE",
    "RT Image Storage": "RI",
    "RT Dose Storage": "RD",
    "RT Plan Storage": "RP",
    "RT Ion Plan Storage": "RN",
    "RT Structure Set Storage": "RS",
    "Computed Radiography Image Storage": "CR",
    "Ultrasound Image Storage": "US",
    "Enhanced Ultrasound Image Storage": "USE",
    "X-Ray Angiographic Image Storage": "XA",
    "Enhanced XA Image Storage": "XAE",
    "Nuclear Medicine Image Storage": "NM",
    "Secondary Capture Image Storage": "SC",
    "RT Beams Treatment Record Storage": "RBT",
    "RT Ion Beams Treatment Record Storage": "RIBT",
}


class UnknownTagsError(ValueError):
    """The dataset has public elements that pydicom's data dictionary does not know.

    An unknown element might hold identifying information, so the dataset is refused
    rather than passed through with it.
    """


def vr_for_keyword(keyword: str) -> str:
    """Return the VR that pydicom's data dictionary gives for a keyword.

    Raises:
        KeyError: if pydicom does not know the keyword.
    """
    tag = datadict.tag_for_keyword(keyword)
    if tag is None:
        raise KeyError(f"{keyword} is not a DICOM keyword known to pydicom")
    return datadict.dictionary_VR(tag)


def pseudonymise_value(keyword: str, value):
    """Return the pseudonymous replacement for ``value`` as the element ``keyword``.

    Raises:
        KeyError: if no replacement is defined for the keyword's VR.
    """
    vr = vr_for_keyword(keyword)
    if vr == "CS":
        logger.warning(
            "Keyword %s has Value Representation CS and may require special processing to "
            "avoid breaking DICOM conformance or interoperability",
            keyword,
        )
    try:
        replace = strategy.DISPATCH[vr]
    except KeyError:
        logger.error("Unable to pseudonymise %s with VR %s", keyword, vr)
        raise
    return replace(value)


def _is_known_tag(tag: pydicom.tag.BaseTag) -> bool:
    return tag in datadict.DicomDictionary or bool(datadict.mask_match(tag))


def unknown_tags(ds: pydicom.Dataset) -> list[pydicom.tag.BaseTag]:
    """Return the top-level public tags of ``ds`` that pydicom's data dictionary does not know.

    Retired group length elements (element 0 of groups above 6) are ignored, as in pymedphys.
    """
    return [
        elem.tag
        for elem in ds
        if not elem.tag.is_private
        and not (elem.tag.element == 0 and elem.tag.group > 6)
        and not _is_known_tag(elem.tag)
    ]


def _pseudonymise_elements(ds: pydicom.Dataset, keywords: list[str]) -> None:
    """Replace each listed element of ``ds`` that has a value, then do the same inside every sequence."""
    for keyword in keywords:
        if hasattr(ds, keyword):
            current_value = ds[keyword].value
            if current_value in ("", None, []):
                continue
            setattr(ds, keyword, pseudonymise_value(keyword, current_value))
    # pymedphys skips a sequence whose *name* is in the keyword list. Names contain spaces
    # and keywords do not, so in practice it recursed into every sequence; so does this.
    for elem in [e for e in ds if e.VR == "SQ"]:
        for item in elem.value:
            _pseudonymise_elements(item, keywords)


def pseudonymise_dataset(
    ds: pydicom.Dataset, keywords_to_leave_unchanged: tuple[str, ...] | list[str] = ()
) -> pydicom.Dataset:
    """Return a pseudonymised copy of ``ds``; ``ds`` itself is not changed.

    Private elements are removed. Every element in PSEUDONYMISATION_KEYWORDS, other than
    those in ``keywords_to_leave_unchanged``, is replaced wherever it occurs, including
    inside sequences.

    Raises:
        UnknownTagsError: if ``ds`` has public elements that pydicom does not know.
        ValueError: if a value cannot be pseudonymised, for example a non-conformant date.
    """
    ds_pseudo = copy.deepcopy(ds)
    unknown = unknown_tags(ds_pseudo)
    if unknown:
        raise UnknownTagsError(
            "These public elements are not in pydicom's DICOM dictionary and may hold "
            "identifying information, so the dataset was not pseudonymised: "
            + ", ".join(str(tag) for tag in unknown)
        )
    ds_pseudo.remove_private_tags()
    keywords = [k for k in PSEUDONYMISATION_KEYWORDS if k not in keywords_to_leave_unchanged]
    _pseudonymise_elements(ds_pseudo, keywords)
    # The file meta (group 0002) is a separate dataset. Its MediaStorageSOPInstanceUID holds
    # the original SOP Instance UID, and pymedphys left it there (#63). UIDs are hashed
    # without the pepper, so it becomes the same UID as the pseudonymised SOPInstanceUID.
    file_meta = getattr(ds_pseudo, "file_meta", None)
    if file_meta is not None:
        _pseudonymise_elements(file_meta, keywords)
    return ds_pseudo


def filename_for_dataset(ds: pydicom.Dataset, dirpath: str | os.PathLike = "") -> str:
    """Return ``<dirpath>/<prefix>.<SOPInstanceUID>.dcm``, the prefix naming the SOP class.

    Raises:
        KeyError: if the SOP class is not in SOP_CLASS_NAME_FILENAME_PREFIXES.
    """
    prefix = SOP_CLASS_NAME_FILENAME_PREFIXES[ds.SOPClassUID.name]
    return os.path.join(dirpath, f"{prefix}.{ds.SOPInstanceUID}.dcm")
