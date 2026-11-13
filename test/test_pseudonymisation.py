"""Contract: src.Model.Pseudonymisation gives the same results as pymedphys 0.41.0.

pymedphys is the reference while it is still a dependency. Both read the pepper and
jitter from ~/.pymedphys/config.toml, so every test that pseudonymises runs with HOME
pointing at a temporary directory holding a known configuration.
"""

import copy
import decimal
import io
import os
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
    ("PatientAge", "021Y"),  # AS, lowest age rounded to a decade
    ("PatientAge", "080Y"),  # AS, decade and cap agree
    ("PatientAge", "081Y"),  # AS, lowest capped age
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
        ("PatientAge", "005D"),  # nothing smaller than days
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


def test_pymedphys_refused_non_ascii_and_multi_valued_ui(known_config: Path) -> None:
    """The reference for the two cases below: pymedphys had no pseudonym for either, so none can change."""
    with pytest.raises(UnicodeEncodeError):
        _pmp_value("InstitutionName", "Señor")
    with pytest.raises(AttributeError):
        _pmp_value("StudyInstanceUID", MultiValue(str, ["1.2.3", "1.2.4"]))


@pytest.mark.parametrize("charset", ["ISO_IR 100", "ISO_IR 192"])
def test_non_ascii_name_is_pseudonymised_the_same_in_any_character_set(known_config: Path, charset: str) -> None:
    """Contract: a non-ASCII name is pseudonymised, and its file's character set does not change the pseudonym."""
    ds = _small_dataset()
    ds.SpecificCharacterSet = charset
    ds.PatientName = "Müller^Jürgen"
    ds.InstitutionName = "Hôpital Señor"
    ds.file_meta = pydicom.dataset.FileMetaDataset()
    ds.file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian
    written = io.BytesIO()
    ds.save_as(written, enforce_file_format=False)
    read_back = pydicom.dcmread(io.BytesIO(written.getvalue()), force=True)
    assert str(read_back.PatientName) == "Müller^Jürgen"  # decoded from the file's character set

    ours = pseudo.pseudonymise_dataset(read_back)
    assert ours.PatientName == pseudo.pseudonymise_value("PatientName", "Müller^Jürgen")
    assert ours.InstitutionName == pseudo.pseudonymise_value("InstitutionName", "Hôpital Señor")
    assert "Müller" not in str(ours.PatientName) and ours.InstitutionName != "Hôpital Señor"
    assert ours.PatientName.family_name.isascii() and ours.InstitutionName.isascii()


def test_multi_valued_ui_is_pseudonymised_value_by_value(known_config: Path) -> None:
    """Contract: each UID of a multi-valued UI maps to the same pseudonym it gets on its own."""
    ds = _small_dataset()
    ds.StudyInstanceUID = "1.2.3"
    ours = pseudo.pseudonymise_dataset(ds)
    single = ours.StudyInstanceUID
    ds.StudyInstanceUID = MultiValue(str, ["1.2.3", "1.2.4"])
    ours = pseudo.pseudonymise_dataset(ds)
    assert list(ours.StudyInstanceUID) == [single, pseudo.pseudonymise_value("StudyInstanceUID", "1.2.4")]
    assert "1.2.3" not in ours.StudyInstanceUID and "1.2.4" not in ours.StudyInstanceUID


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


def _redirected_home(tmp_path: Path, shared_content: str) -> tuple[Path, Path, Path]:
    """A home whose ~/.pymedphys/config.toml redirects to a shared file, as a site might set up."""
    home, share = tmp_path / "home", tmp_path / "share"
    (home / ".pymedphys").mkdir(parents=True)
    share.mkdir()
    shared = share / "config.toml"
    shared.write_text(shared_content)
    main = home / ".pymedphys" / "config.toml"
    main.write_text(toml.dumps({"redirect": str(shared), "other": {"setting": "kept"}}))
    return home, main, shared


def test_redirect_to_shared_pepper_is_followed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Contract: a redirect to a shared configuration supplies the site's pepper and jitter."""
    home, main, _ = _redirected_home(tmp_path, toml.dumps({"pseudo": {"pepper": PEPPER, "epoch_jitter": 7}}))
    before = main.read_bytes()
    _use_home(monkeypatch, home)
    try:
        assert config.get_pepper() == PEPPER.encode("ASCII")
        assert config.get_epoch_jitter() == 7
        assert main.read_bytes() == before
    finally:
        _clear_caches()


def test_missing_pepper_is_stored_in_the_shared_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Contract: through a redirect, a new pepper goes into the shared file; the redirect survives.

    pymedphys wrote the shared file's content over ~/.pymedphys/config.toml instead.
    """
    home, main, shared = _redirected_home(tmp_path, toml.dumps({"shared": {"note": "site"}}))
    before = main.read_bytes()
    _use_home(monkeypatch, home)
    try:
        pepper = config.get_pepper()
        jitter = config.get_epoch_jitter()
        assert main.read_bytes() == before
        stored = toml.loads(shared.read_text())
        assert stored["shared"] == {"note": "site"}
        assert stored["pseudo"] == {"pepper": pepper.decode("ASCII"), "epoch_jitter": jitter}
    finally:
        _clear_caches()


def test_unreachable_shared_config_stops_pseudonymisation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Contract: if the shared configuration cannot be read (a share offline), nothing is pseudonymised
    and nothing is written. A new pepper would change every pseudonym from then on, and pymedphys
    wrote one over ~/.pymedphys/config.toml, losing the redirect.
    """
    home, main, shared = _redirected_home(tmp_path, toml.dumps({"pseudo": {"pepper": PEPPER, "epoch_jitter": 7}}))
    shared.unlink()
    before = main.read_bytes()
    _use_home(monkeypatch, home)
    try:
        with pytest.raises(config.PseudonymisationConfigError, match="share"):
            config.get_pepper()
        with pytest.raises(config.PseudonymisationConfigError):
            pseudo.pseudonymise_dataset(_small_dataset())
        assert main.read_bytes() == before
        assert not shared.exists()
    finally:
        _clear_caches()


def test_unparseable_config_stops_pseudonymisation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Contract: a configuration that is not valid TOML is reported, never replaced."""
    (tmp_path / ".pymedphys").mkdir()
    main = tmp_path / ".pymedphys" / "config.toml"
    main.write_text("[pseudo\npepper = ")
    before = main.read_bytes()
    _use_home(monkeypatch, tmp_path)
    try:
        with pytest.raises(config.PseudonymisationConfigError):
            config.get_epoch_jitter()
        assert main.read_bytes() == before
    finally:
        _clear_caches()


@pytest.mark.timeout(20)
@pytest.mark.parametrize("loop", ["self", "two files"])
def test_a_redirect_loop_stops_pseudonymisation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, loop: str) -> None:
    """Contract (#69): a redirect back to a file already read is reported, not followed forever."""
    (tmp_path / ".pymedphys").mkdir()
    main = tmp_path / ".pymedphys" / "config.toml"
    other = tmp_path / "other.toml"
    if loop == "self":
        main.write_text(toml.dumps({"redirect": str(main)}))
    else:
        main.write_text(toml.dumps({"redirect": str(other)}))
        other.write_text(toml.dumps({"redirect": str(main)}))
    before = main.read_bytes()
    _use_home(monkeypatch, tmp_path)
    try:
        with pytest.raises(config.PseudonymisationConfigError, match="loop"):
            config.get_pepper()
        assert main.read_bytes() == before
    finally:
        _clear_caches()


def test_a_failed_write_leaves_the_pepper_in_place(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Contract (#69): storing a new jitter fails part-way; the file still holds the pepper, whole.

    Before, the file was truncated first, so the pepper was lost and the next run made a new one.
    """
    (tmp_path / ".pymedphys").mkdir()
    main = tmp_path / ".pymedphys" / "config.toml"
    main.write_text(toml.dumps({"pseudo": {"pepper": PEPPER}, "other": {"setting": "kept"}}))
    before = main.read_bytes()
    _use_home(monkeypatch, tmp_path)

    def fail_part_way(data: dict, f) -> None:
        f.write("[pseudo]\n")  # some bytes reach the file, then the disk is full
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(config.toml, "dump", fail_part_way)
    try:
        with pytest.raises(OSError, match="No space left"):
            config.get_epoch_jitter()
        assert main.read_bytes() == before
        assert sorted(p.name for p in main.parent.iterdir()) == ["config.toml"]  # no temporary file left
    finally:
        _clear_caches()


def test_a_rewritten_config_keeps_its_permissions(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Contract: replacing the file does not change who can read it; a first file is the owner's only."""
    (tmp_path / ".pymedphys").mkdir()
    main = tmp_path / ".pymedphys" / "config.toml"
    main.write_text(toml.dumps({"pseudo": {"pepper": PEPPER}}))
    main.chmod(0o640)
    _use_home(monkeypatch, tmp_path)
    try:
        config.get_epoch_jitter()
        assert main.stat().st_mode & 0o777 == 0o640
        assert "epoch_jitter" in toml.loads(main.read_text())["pseudo"]
    finally:
        _clear_caches()
    fresh = tmp_path / "fresh"
    _use_home(monkeypatch, fresh)
    fresh.mkdir()
    try:
        config.get_pepper()
        if os.name == "posix":
            assert (fresh / ".pymedphys" / "config.toml").stat().st_mode & 0o777 == 0o600
    finally:
        _clear_caches()


def test_a_symlinked_config_is_written_through_the_link(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Contract: a config reached by a symlink (a site's shared file) gets the new value; the link stays a link."""
    shared = tmp_path / "share" / "config.toml"
    shared.parent.mkdir()
    shared.write_text(toml.dumps({"pseudo": {"pepper": PEPPER}}))
    (tmp_path / "home" / ".pymedphys").mkdir(parents=True)
    link = tmp_path / "home" / ".pymedphys" / "config.toml"
    link.symlink_to(shared)
    _use_home(monkeypatch, tmp_path / "home")
    try:
        jitter = config.get_epoch_jitter()
        assert link.is_symlink() and link.resolve() == shared.resolve()
        assert toml.loads(shared.read_text())["pseudo"] == {"pepper": PEPPER, "epoch_jitter": jitter}
        assert sorted(p.name for p in shared.parent.iterdir()) == ["config.toml"]
    finally:
        _clear_caches()
