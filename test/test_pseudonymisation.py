"""Contract: src.Model.Pseudonymisation gives the same results as pymedphys 0.41.0.

pymedphys is the reference while it is still a dependency. Both read the pepper and
jitter from ~/.pymedphys/config.toml, so every test that pseudonymises runs with HOME
pointing at a temporary directory holding a known configuration.
"""

import copy
import decimal
import io
from pathlib import Path

import pydicom
import pytest
import toml
from pydicom.dataset import Dataset
from pydicom.multival import MultiValue
from pydicom.valuerep import DSfloat

import pymedphys._experimental.pseudonymisation.strategy as pmp_strategy
import pymedphys.experimental.pseudonymisation as pmp_pseudonymise
from pymedphys._dicom.anonymise.core import create_filename_from_dataset
from pymedphys.dicom import anonymise as pmp_anonymise
from src.Model import Pseudonymisation as pseudo
from src.Model.Pseudonymisation import config, strategy

DATA = Path.cwd().joinpath("test", "testdata", "DICOM-RT-02")
PEPPER = "a-known-pepper-for-tests-only"
EPOCH_JITTER = 321
# As in Anon.py
LEAVE_UNCHANGED = ["PatientSex", "PatientWeight", "PatientSize"]


def _clear_caches() -> None:
    config.clear_cache()
    pmp_strategy._get_pepper.cache_clear()
    pmp_strategy._get_epoch_jitter.cache_clear()


def _use_home(monkeypatch: pytest.MonkeyPatch, home: Path) -> None:
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    _clear_caches()


@pytest.fixture
def known_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """A home directory whose ~/.pymedphys/config.toml holds PEPPER and EPOCH_JITTER."""
    config_dir = tmp_path / ".pymedphys"
    config_dir.mkdir()
    (config_dir / "config.toml").write_text(
        toml.dumps({"pseudo": {"pepper": PEPPER, "epoch_jitter": EPOCH_JITTER}})
    )
    _use_home(monkeypatch, tmp_path)
    yield tmp_path
    _clear_caches()


def _pmp_value(keyword: str, value):
    return pmp_strategy.get_pseudonymous_replacement_value(keyword, value)


# (keyword, value), at least one per VR in the pseudonymisation keywords.
VALUES = [
    ("StationAETitle", "ONKO_SCP"),  # AE
    ("Manufacturer", "Varian Medical Systems"),  # LO
    ("Manufacturer", ""),  # LO, empty (Anon.py's caller skips it; the function still answers)
    ("Manufacturer", MultiValue(str, ["first", "second"])),  # LO, multi-valued: hashed as one text
    ("PatientID", "123456789"),  # LO
    ("AdditionalPatientHistory", "Line one\r\nline two"),  # LT
    ("StudyID", "STUDY-0001"),  # SH
    ("InstitutionAddress", "1 Hospital Road, Wanaka"),  # ST
    ("PatientName", "Doe^Jane^Q^Dr^III"),  # PN, all five components
    ("PatientName", "Doe"),  # PN, family name only
    ("PatientName", "^Jane"),  # PN, given name only
    ("PatientName", pydicom.valuerep.PersonName("Smith^John")),  # PN, already a PersonName
    ("PatientSex", "F"),  # CS
    ("StudyDate", "20190101"),  # DA
    ("StudyDate", "20000229"),  # DA, leap day
    ("StudyDate", "19000101"),  # DA, before the earliest study date
    ("AcquisitionDateTime", "20190101123456.789012"),  # DT
    ("AcquisitionDateTime", "20190101123456+1300"),  # DT with a time zone
    ("AcquisitionDateTime", "2019"),  # DT, year only
    ("PatientWeight", DSfloat("72.5")),  # DS
    ("PatientWeight", DSfloat("-0.000123")),  # DS, negative with leading zeros
    ("PatientWeight", DSfloat("1.5E3")),  # DS, exponent
    ("PatientWeight", "1234567890123456"),  # DS, 16 digits
    ("StudyTime", "123456.789"),  # TM, unchanged
    ("StudyInstanceUID", "1.2.840.10008.5.1.4.1.1.481.5"),  # UI
    ("StudyInstanceUID", "2.25.329800735698586629295641978511506172918"),  # UI, long
    ("PatientAge", "045Y"),  # AS, decade
    ("PatientAge", "095Y"),  # AS, over 80
]


@pytest.mark.parametrize("keyword,value", VALUES, ids=[f"{k}={v!s}"[:60] for k, v in VALUES])
def test_value_matches_pymedphys(known_config: Path, keyword: str, value) -> None:
    """Contract: each VR's replacement equals pymedphys's for the same pepper and jitter."""
    assert pseudo.pseudonymise_value(keyword, value) == _pmp_value(keyword, value)


@pytest.mark.parametrize("age", ["015Y", "020Y", "011M", "010Y", "005M", "003W", "001Y"])
@pytest.mark.parametrize("increment", [-2, -1, 0, 1])
def test_age_matches_pymedphys_for_each_random_step(
    known_config: Path, monkeypatch: pytest.MonkeyPatch, age: str, increment: int
) -> None:
    """Contract: for the same random step, an age of 20 or under gets pymedphys's result.

    pymedphys draws the step with random.randrange(-2, 2): -2, -1, 0 or 1.
    """
    monkeypatch.setattr(pmp_strategy.random, "randrange", lambda start, stop: increment)
    monkeypatch.setattr(strategy.secrets, "randbelow", lambda n: increment + 2)
    assert pseudo.pseudonymise_value("PatientAge", age) == _pmp_value("PatientAge", age)


def test_age_step_covers_exactly_pymedphys_range() -> None:
    """Contract: the random step is one of -2, -1, 0, 1, like pymedphys's randrange(-2, 2)."""
    steps = {strategy.secrets.randbelow(4) - 2 for _ in range(400)}
    assert steps == {-2, -1, 0, 1}


@pytest.mark.parametrize(
    "keyword,value",
    [
        ("StudyDate", "61d6b371-5759-36d4-a66b-402c0333d1a9"),  # non-conformant date (DICOM-RT-02)
        ("AcquisitionDateTime", "not a date"),
        ("PatientWeight", MultiValue(DSfloat, ["1.5", "2.5"])),  # multi-valued DS
        ("StudyInstanceUID", MultiValue(str, ["1.2.3", "1.2.4"])),  # multi-valued UI
        ("PatientAge", "005D"),  # nothing smaller than days
        ("Manufacturer", "Señor"),  # not ASCII
    ],
)
def test_value_that_pymedphys_refuses_is_refused(known_config: Path, keyword: str, value) -> None:
    """Contract: a value pymedphys cannot pseudonymise raises here too, never passes through."""
    with pytest.raises(Exception):
        _pmp_value(keyword, value)
    with pytest.raises((ValueError, AttributeError, decimal.InvalidOperation, UnicodeEncodeError)):
        pseudo.pseudonymise_value(keyword, value)


def test_keywords_match_pymedphys() -> None:
    """Contract: the same keywords are pseudonymised, with the same VR from pydicom's dictionary."""
    pmp_keywords = pmp_pseudonymise.get_default_pseudonymisation_keywords()
    assert set(pseudo.PSEUDONYMISATION_KEYWORDS) == set(pmp_keywords)
    assert len(pseudo.PSEUDONYMISATION_KEYWORDS) == len(pmp_keywords)
    baseline_vr = pmp_strategy.get_baseline_keyword_vr_dict()
    for keyword in pmp_keywords:
        assert pseudo.vr_for_keyword(keyword) == baseline_vr[keyword], keyword


def _with_conformant_dates(ds: Dataset) -> Dataset:
    """DICOM-RT-02 holds UUID strings in some DA elements; give them a valid date (issue #61)."""
    for elem in ds.iterall():
        if elem.VR == "DA" and elem.value and not str(elem.value).isdigit():
            elem.value = "20200101"
    return ds


DICOM_FILES = sorted(DATA.rglob("*.dcm"))


def test_dicom_rt_02_is_present() -> None:
    """The dataset comparison below needs DICOM-RT-02; without it, fail rather than pass empty."""
    assert len(DICOM_FILES) == 108, f"expected the 108 files of DICOM-RT-02 in {DATA}"


@pytest.mark.parametrize("path", DICOM_FILES, ids=[p.name for p in DICOM_FILES])
def test_dataset_matches_pymedphys(known_config: Path, path: Path) -> None:
    """Contract: a whole dataset, sequences included, pseudonymises as pymedphys did for Anon.py."""
    original = _with_conformant_dates(pydicom.dcmread(path))
    before = copy.deepcopy(original)

    ours = pseudo.pseudonymise_dataset(original, keywords_to_leave_unchanged=LEAVE_UNCHANGED)
    reference = pmp_anonymise(
        _with_conformant_dates(pydicom.dcmread(path)),
        keywords_to_leave_unchanged=LEAVE_UNCHANGED,
        replacement_strategy=pmp_pseudonymise.pseudonymisation_dispatch,
        identifying_keywords=pmp_pseudonymise.get_default_pseudonymisation_keywords(),
    )

    assert ours == reference  # Dataset equality does not include the file meta
    # The file meta matches pymedphys's except where pymedphys left the original UID (#63).
    ours_meta, reference_meta = copy.deepcopy(ours.file_meta), copy.deepcopy(reference.file_meta)
    assert ours_meta.MediaStorageSOPInstanceUID == ours.SOPInstanceUID
    assert reference_meta.MediaStorageSOPInstanceUID == before.SOPInstanceUID
    del ours_meta.MediaStorageSOPInstanceUID, reference_meta.MediaStorageSOPInstanceUID
    assert ours_meta == reference_meta
    assert ours.PatientID != before.PatientID  # it did pseudonymise
    assert original == before  # the input is not changed
    assert original.file_meta == before.file_meta
    if ours.SOPClassUID.name != "Comprehensive SR Storage":
        assert pseudo.filename_for_dataset(ours, "out") == create_filename_from_dataset(reference, "out")


@pytest.mark.parametrize("path", DICOM_FILES, ids=[p.name for p in DICOM_FILES])
def test_no_original_uid_in_written_file(known_config: Path, path: Path) -> None:
    """Contract: no original identifying UID survives anywhere in the written file (#63).

    Searches the bytes save_as writes, file meta included, for every original value of an
    identifying UID found anywhere in the source, sequences and file meta included.
    """
    source = _with_conformant_dates(pydicom.dcmread(path))
    originals = {
        str(elem.value): elem.keyword
        for elem in [*source.iterall(), *source.file_meta]
        if elem.keyword in pseudo.IDENTIFYING_UIDS and elem.value
    }
    assert str(source.SOPInstanceUID) in originals  # the probe has something to find
    written = io.BytesIO()
    pseudo.pseudonymise_dataset(source, keywords_to_leave_unchanged=LEAVE_UNCHANGED).save_as(written)
    data = written.getvalue()
    leaked = {keyword for uid, keyword in originals.items() if uid.encode("ASCII") in data}
    assert leaked == set()


@pytest.mark.parametrize("path", DICOM_FILES, ids=[p.name for p in DICOM_FILES])
def test_invalid_dates_are_emptied_and_logged(
    known_config: Path, caplog: pytest.LogCaptureFixture, path: Path
) -> None:
    """Contract (#61): DICOM-RT-02 as published, with UUIDs in date elements, is pseudonymised.

    pymedphys refuses it. Here each invalid date is emptied, with a warning naming the source,
    the element, its tag and the value; everything else is as for the same data with valid dates.
    """
    raw = pydicom.dcmread(path)
    invalid = {
        e.keyword: str(e.value)
        for e in raw
        if e.VR == "DA" and e.value and not str(e.value).isdigit()
    }
    assert invalid  # the probe has something to find
    with pytest.raises(ValueError):
        pmp_anonymise(
            copy.deepcopy(raw),
            keywords_to_leave_unchanged=LEAVE_UNCHANGED,
            replacement_strategy=pmp_pseudonymise.pseudonymisation_dispatch,
            identifying_keywords=pmp_pseudonymise.get_default_pseudonymisation_keywords(),
        )

    with caplog.at_level("WARNING", logger="src.Model.Pseudonymisation"):
        ours = pseudo.pseudonymise_dataset(raw, keywords_to_leave_unchanged=LEAVE_UNCHANGED, source=str(path))
    for keyword in invalid:
        assert ours[keyword].value == ""
    warnings = [r.getMessage() for r in caplog.records if "Invalid value emptied" in r.getMessage()]
    assert len(warnings) == len(invalid)
    for keyword, value in invalid.items():
        tag = str(raw[keyword].tag)
        assert any(str(path) in w and keyword in w and tag in w and value in w for w in warnings), keyword

    valid = pseudo.pseudonymise_dataset(
        _with_conformant_dates(pydicom.dcmread(path)), keywords_to_leave_unchanged=LEAVE_UNCHANGED
    )
    for keyword in invalid:
        del ours[keyword], valid[keyword]
    assert ours == valid


def test_invalid_value_inside_sequence_is_located(known_config: Path, caplog: pytest.LogCaptureFixture) -> None:
    """Contract (#61): the warning gives each sequence and item number down to the invalid element."""
    ds = _small_dataset()
    second_item = Dataset()
    second_item.PatientBirthDate = "not-a-date"
    ds.ReferencedStudySequence.append(second_item)
    with caplog.at_level("WARNING", logger="src.Model.Pseudonymisation"):
        ours = pseudo.pseudonymise_dataset(ds, source="patient/RS.dcm")
    assert ours.ReferencedStudySequence[1].PatientBirthDate == ""
    assert ours.StudyDate != "" and ours.StudyDate != ds.StudyDate  # valid dates still shifted
    (warning,) = [r.getMessage() for r in caplog.records if "Invalid value emptied" in r.getMessage()]
    assert "patient/RS.dcm: ReferencedStudySequence[1] > PatientBirthDate (0010,0030) VR DA" in warning
    assert "'not-a-date'" in warning


@pytest.mark.parametrize(
    "keyword,value",
    [
        ("PatientWeight", MultiValue(DSfloat, ["1.5", "2.5"])),  # decimal.InvalidOperation
        ("PatientAge", "005D"),  # ValueError: nothing smaller than days
        ("AcquisitionDateTime", "not a date"),
    ],
)
def test_other_invalid_values_are_emptied(known_config: Path, caplog: pytest.LogCaptureFixture, keyword: str, value) -> None:
    """Contract (#61): any value invalid for its VR is emptied and logged, not passed through."""
    ds = _small_dataset()
    setattr(ds, keyword, value)
    with caplog.at_level("WARNING", logger="src.Model.Pseudonymisation"):
        ours = pseudo.pseudonymise_dataset(ds)
    assert ours[keyword].value in ("", None)
    assert any(keyword in r.getMessage() for r in caplog.records if "Invalid value emptied" in r.getMessage())


@pytest.mark.parametrize(
    "keyword,value,error",
    [
        ("InstitutionName", "Se\u00f1or", UnicodeEncodeError),  # valid DICOM text, but not ASCII
        ("StudyInstanceUID", MultiValue(str, ["1.2.3", "1.2.4"]), AttributeError),  # multi-valued UI
    ],
)
def test_values_that_are_not_invalid_still_refuse(known_config: Path, keyword: str, value, error) -> None:
    """Contract: a value that is valid DICOM but cannot be hashed is not emptied as if invalid; it raises."""
    ds = _small_dataset()
    setattr(ds, keyword, value)
    with pytest.raises(error):
        pseudo.pseudonymise_dataset(ds)


def _small_dataset() -> Dataset:
    ds = Dataset()
    ds.PatientID = "123456789"
    ds.PatientName = "Doe^Jane"
    ds.StudyDate = "20190101"
    seq_item = Dataset()
    seq_item.ReferencedSOPInstanceUID = "1.2.840.10008.1.2.3"
    seq_item.PatientName = "Nested^Name"
    ds.ReferencedStudySequence = [seq_item]
    return ds


def test_private_elements_are_removed(known_config: Path) -> None:
    """Contract: private elements are removed, at the top level and inside sequences."""
    ds = _small_dataset()
    ds.add_new(0x00091010, "LO", "a private value")
    ds.ReferencedStudySequence[0].add_new(0x00111010, "LO", "a nested private value")
    ours = pseudo.pseudonymise_dataset(ds)
    assert 0x00091010 not in ours
    assert 0x00111010 not in ours.ReferencedStudySequence[0]
    assert ours.ReferencedStudySequence[0].PatientName != "Nested^Name"


def test_tag_unknown_to_pydicom_is_refused(known_config: Path) -> None:
    """Contract: a public element no dictionary knows may be identifying, so the dataset is refused."""
    ds = _small_dataset()
    unknown = 0x00120099
    assert unknown not in pydicom.datadict.DicomDictionary
    ds.add_new(unknown, "LO", "who knows")
    with pytest.raises(ValueError):
        pmp_anonymise(ds, replacement_strategy=pmp_pseudonymise.pseudonymisation_dispatch,
                      identifying_keywords=pmp_pseudonymise.get_default_pseudonymisation_keywords())
    with pytest.raises(pseudo.UnknownTagsError):
        pseudo.pseudonymise_dataset(ds)


def test_tag_known_to_pydicom_but_not_to_pymedphys_is_accepted(known_config: Path) -> None:
    """Contract, the one intended difference: pydicom's newer dictionary decides what is known.

    pymedphys refuses SourcePresentationAddress (absent from its older copy of the dictionary).
    """
    ds = _small_dataset()
    ds.SourcePresentationAddress = "https://example.org"
    with pytest.raises(ValueError):
        pmp_anonymise(ds, replacement_strategy=pmp_pseudonymise.pseudonymisation_dispatch,
                      identifying_keywords=pmp_pseudonymise.get_default_pseudonymisation_keywords())
    ours = pseudo.pseudonymise_dataset(ds)
    assert ours.SourcePresentationAddress == "https://example.org"
    assert ours.PatientID != "123456789"


def test_existing_pepper_and_jitter_are_read(known_config: Path) -> None:
    """Contract: an existing site's pepper and jitter are used, so its pseudonyms do not change."""
    assert config.get_pepper() == PEPPER.encode("ASCII")
    assert config.get_epoch_jitter() == EPOCH_JITTER


def test_missing_config_is_created_and_other_keys_kept(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Contract: without a pepper and jitter, new ones are stored; other configuration survives."""
    config_dir = tmp_path / ".pymedphys"
    config_dir.mkdir()
    config_file = config_dir / "config.toml"
    config_file.write_text(toml.dumps({"other": {"setting": "kept"}}))
    _use_home(monkeypatch, tmp_path)
    try:
        pepper = config.get_pepper()
        jitter = config.get_epoch_jitter()
        stored = toml.loads(config_file.read_text())
        assert stored["other"] == {"setting": "kept"}
        assert stored["pseudo"]["pepper"].encode("ASCII") == pepper
        assert stored["pseudo"]["epoch_jitter"] == jitter
        assert 0 <= jitter < 1000
        # pymedphys reads the same values from the file written here.
        pmp_strategy._get_pepper.cache_clear()
        pmp_strategy._get_epoch_jitter.cache_clear()
        assert pmp_strategy._get_pepper() == pepper
        assert pmp_strategy._get_epoch_jitter() == jitter
    finally:
        _clear_caches()


def test_no_config_directory_at_all(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Contract: a first run with no ~/.pymedphys creates it and stores both values."""
    _use_home(monkeypatch, tmp_path)
    try:
        pepper = config.get_pepper()
        jitter = config.get_epoch_jitter()
        stored = toml.loads((tmp_path / ".pymedphys" / "config.toml").read_text())
        assert stored == {"pseudo": {"pepper": pepper.decode("ASCII"), "epoch_jitter": jitter}}
    finally:
        _clear_caches()
