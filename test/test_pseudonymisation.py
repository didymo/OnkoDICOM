"""Contract: src.Model.Pseudonymisation gives the same results as pymedphys 0.41.0.

pymedphys is the reference while it is still a dependency. Every test that pseudonymises runs with HOME
pointing at a temporary directory: pymedphys reads the pepper and jitter from ~/.pymedphys/config.toml
there, and OnkoDICOM moves them into ~/.OnkoDICOM/pseudonymisation.toml, so both use the same values.
"""

import base64
import copy
import decimal
import hashlib
import io
import os
from decimal import Decimal
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
    """A home whose ~/.pymedphys/config.toml holds PEPPER and EPOCH_JITTER: pymedphys reads them there,
    and OnkoDICOM moves them into its own configuration on first use, so both use the same values."""
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
    def pmp_randrange(start: int, stop: int) -> int:
        assert (start, stop) == (-2, 2)
        return increment

    def our_randbelow(n: int) -> int:
        assert n == 4  # four steps: -2, -1, 0, 1
        return increment + 2

    monkeypatch.setattr(pmp_strategy.random, "randrange", pmp_randrange)
    monkeypatch.setattr(strategy.secrets, "randbelow", our_randbelow)
    assert pseudo.pseudonymise_value("PatientAge", age) == _pmp_value("PatientAge", age)


def test_age_step_covers_exactly_pymedphys_range(monkeypatch: pytest.MonkeyPatch) -> None:
    """Contract: the age pseudonymiser moves an age by -2, -1, 0 or 1, like pymedphys's randrange(-2, 2).

    Every result the random source can give is fed to the pseudonymiser itself.
    """
    bounds = []

    def randbelow(n: int) -> int:
        bounds.append(n)
        return results.pop()

    monkeypatch.setattr(strategy.secrets, "randbelow", randbelow)
    ages = set()
    for drawn in range(4):
        results = [drawn]
        ages.add(strategy.pseudonymise_AS("015Y"))
    assert set(bounds) == {4}
    assert ages == {"013Y", "014Y", "015Y", "016Y"}


@pytest.mark.parametrize("age", ["000Y", "000M", "000W", "001W"])
@pytest.mark.parametrize("increment", [-2, -1, 0, 1])
def test_a_young_age_never_becomes_negative(
    known_config: Path, monkeypatch: pytest.MonkeyPatch, age: str, increment: int
) -> None:
    """Contract: a step below zero gives zero; otherwise the result is pymedphys's.

    pymedphys turned 000Y into -02M, which is not a DICOM age.
    """
    monkeypatch.setattr(pmp_strategy.random, "randrange", lambda start, stop: increment)
    monkeypatch.setattr(strategy.secrets, "randbelow", lambda n: increment + 2)
    ours = pseudo.pseudonymise_value("PatientAge", age)
    reference = _pmp_value("PatientAge", age)
    assert ours[:3].isdigit() and len(ours) == 4
    if reference.startswith("-"):
        assert ours == "000" + reference[3]
    else:
        assert ours == reference


def _short_hash_ds_values() -> list[str]:
    """Two- and three-digit DS values whose hash starts with too few decimal digits (where pymedphys failed)."""
    found = []
    for number in range(10, 1000):
        text = str(number)
        digest = hashlib.new("sha3_256", text.encode("ASCII")).hexdigest()
        if len(str(int(digest[0 : len(text)], 16))) < len(text):
            found.append(text)
    return found


SHORT_HASH_DS = _short_hash_ds_values()


def test_short_hash_ds_values_exist() -> None:
    """The DS test below needs such values; about one two-digit value in 25 is one."""
    assert any(len(v) == 2 for v in SHORT_HASH_DS) and any(len(v) == 3 for v in SHORT_HASH_DS)


@pytest.mark.parametrize("value", SHORT_HASH_DS[:6])
def test_a_ds_whose_hash_has_too_few_digits_is_still_pseudonymised(known_config: Path, value: str) -> None:
    """Contract: a valid DS is pseudonymised to a valid DS of no more digits, never emptied.

    The padding zeros lead, and a decimal does not print leading zeros, so "04" is written "4".

    In OnkoDICOM only PatientWeight and PatientSize are DS, and Anon.py leaves both unchanged,
    so this protects other callers of the module.

    pymedphys failed on these values, so padding the hash with zeros changes no earlier pseudonym.
    """
    with pytest.raises(ValueError):
        _pmp_value("PatientWeight", DSfloat(value))
    ours = pseudo.pseudonymise_value("PatientWeight", DSfloat(value))
    assert ours.isdigit() and 1 <= len(ours) <= len(value)
    assert ours == str(Decimal(ours))  # a plain decimal, as DS requires
    ds = _small_dataset()
    ds.PatientWeight = value  # Anon.py leaves it unchanged; other callers need not
    assert str(pseudo.pseudonymise_dataset(ds).PatientWeight) == ours


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
        assert any(str(path) in w and keyword in w and tag in w for w in warnings), keyword
        assert not any(value in w for w in warnings), keyword  # the log holds no patient data

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
    assert "not-a-date" not in warning  # the location finds the value; the log does not hold it


@pytest.mark.parametrize(
    "keyword,value",
    [
        ("PatientWeight", MultiValue(DSfloat, ["1.5", "2.5"])),  # decimal.InvalidOperation
        ("PatientAge", "005D"),  # ValueError: nothing smaller than days
        ("PatientAge", "4"),  # shorter than a DICOM age: pymedphys failed with an IndexError
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
    # Computed here, not by the code under test: SHA3-256 of the UTF-8 bytes and the pepper, base64, LO length.
    digest = hashlib.sha3_256("Hôpital Señor".encode("UTF-8") + PEPPER.encode("ASCII")).digest()
    assert ours.InstitutionName == base64.standard_b64encode(digest).decode("ASCII").rstrip("=")[0:64]
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


@pytest.mark.parametrize("where", ["sequence item", "nested sequence item", "file meta"])
def test_tag_unknown_to_pydicom_is_refused_wherever_it_is(known_config: Path, where: str) -> None:
    """Contract: an unknown public element inside a sequence or in the file meta is refused too, with its location.

    pymedphys checked only the top level, so these passed through unchanged.
    """
    ds = _small_dataset()
    unknown = 0x00120099 if where != "file meta" else 0x00020099
    assert unknown not in pydicom.datadict.DicomDictionary
    if where == "sequence item":
        ds.ReferencedStudySequence[0].add_new(unknown, "LO", "who knows")
        location = "ReferencedStudySequence[0] > (0012,0099)"
    elif where == "nested sequence item":
        inner = Dataset()
        inner.add_new(unknown, "LO", "who knows")
        ds.ReferencedStudySequence[0].ReferencedSeriesSequence = [Dataset(), inner]
        location = "ReferencedStudySequence[0] > ReferencedSeriesSequence[1] > (0012,0099)"
    else:
        ds.file_meta = pydicom.dataset.FileMetaDataset()
        ds.file_meta.add_new(unknown, "LO", "who knows")
        location = "file meta > (0002,0099)"
    with pytest.raises(pseudo.UnknownTagsError, match=r"patient/RS\.dcm: ") as refused:
        pseudo.pseudonymise_dataset(ds, source="patient/RS.dcm")
    assert location in str(refused.value)
    assert "who knows" not in str(refused.value)


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




# --- Where the pepper and jitter come from --------------------------------------------------------------------------
# OnkoDICOM's own file first; else moved from pymedphys's (redirects followed); else created in OnkoDICOM's.


def _home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, onkodicom: str | None = None, pymedphys: str | None = None):
    """A home with the given OnkoDICOM and pymedphys configuration contents (None: no file)."""
    home = tmp_path / "home"
    onko_file = home / ".OnkoDICOM" / "pseudonymisation.toml"
    pmp_file = home / ".pymedphys" / "config.toml"
    for path, content in ((onko_file, onkodicom), (pmp_file, pymedphys)):
        if content is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
    _use_home(monkeypatch, home)
    return home, onko_file, pmp_file


def test_the_config_files_are_where_onkodicom_and_pymedphys_keep_theirs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    home, onko_file, pmp_file = _home(tmp_path, monkeypatch)
    assert config.onkodicom_config_path() == onko_file
    assert config.pymedphys_config_path() == pmp_file


def test_onkodicom_config_comes_first(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Contract: once OnkoDICOM holds the values, pymedphys's are not consulted."""
    _, onko_file, pmp_file = _home(
        tmp_path, monkeypatch,
        onkodicom=toml.dumps({"pseudo": {"pepper": "onkodicom-pepper", "epoch_jitter": 11}}),
        pymedphys=toml.dumps({"pseudo": {"pepper": "pymedphys-pepper", "epoch_jitter": 22}}),
    )
    try:
        assert config.get_pepper() == b"onkodicom-pepper"
        assert config.get_epoch_jitter() == 11
    finally:
        _clear_caches()


def test_pymedphys_values_are_moved_to_onkodicom(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Contract: a site's existing pepper and jitter are copied over, so its pseudonyms do not change;
    pymedphys's file is left exactly as it was."""
    _, onko_file, pmp_file = _home(
        tmp_path, monkeypatch, pymedphys=toml.dumps({"pseudo": {"pepper": PEPPER, "epoch_jitter": EPOCH_JITTER}, "other": {"x": 1}})
    )
    before = pmp_file.read_bytes()
    try:
        assert config.get_pepper() == PEPPER.encode("ASCII")
        assert config.get_epoch_jitter() == EPOCH_JITTER
        assert toml.loads(onko_file.read_text()) == {"pseudo": {"pepper": PEPPER, "epoch_jitter": EPOCH_JITTER}}
        assert pmp_file.read_bytes() == before
        # And from now on pymedphys's file is not needed.
        _clear_caches()
        pmp_file.unlink()
        assert config.get_pepper() == PEPPER.encode("ASCII")
        assert config.get_epoch_jitter() == EPOCH_JITTER
    finally:
        _clear_caches()



def test_a_first_run_creates_the_values_in_onkodicom_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Contract: with neither configuration, new values go into OnkoDICOM's file, readable by its owner only."""
    home, onko_file, pmp_file = _home(tmp_path, monkeypatch)
    try:
        pepper = config.get_pepper()
        jitter = config.get_epoch_jitter()
        assert toml.loads(onko_file.read_text()) == {"pseudo": {"pepper": pepper.decode("ASCII"), "epoch_jitter": jitter}}
        assert 0 <= jitter < 1000
        assert not (home / ".pymedphys").exists()
        if os.name == "posix":
            assert onko_file.stat().st_mode & 0o777 == 0o600
    finally:
        _clear_caches()


def test_a_pymedphys_redirect_to_a_shared_config_is_followed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Contract: a site that shared its pepper through a pymedphys redirect gets that pepper moved over."""
    shared = tmp_path / "share" / "config.toml"
    shared.parent.mkdir()
    shared.write_text(toml.dumps({"pseudo": {"pepper": PEPPER, "epoch_jitter": 7}}))
    _, onko_file, pmp_file = _home(tmp_path, monkeypatch, pymedphys=toml.dumps({"redirect": str(shared)}))
    before = (pmp_file.read_bytes(), shared.read_bytes())
    try:
        assert config.get_pepper() == PEPPER.encode("ASCII")
        assert config.get_epoch_jitter() == 7
        assert (pmp_file.read_bytes(), shared.read_bytes()) == before
        assert toml.loads(onko_file.read_text())["pseudo"] == {"pepper": PEPPER, "epoch_jitter": 7}
    finally:
        _clear_caches()


@pytest.mark.parametrize("broken", ["unreachable redirect", "unparseable pymedphys", "unparseable onkodicom"])
def test_an_unreadable_config_stops_pseudonymisation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, broken: str
) -> None:
    """Contract: if a configuration that may hold the pepper cannot be read, nothing is pseudonymised and
    nothing is written: a new pepper would change every pseudonym from then on."""
    if broken == "unreachable redirect":
        kwargs = {"pymedphys": toml.dumps({"redirect": str(tmp_path / "offline-share" / "config.toml")})}
    elif broken == "unparseable pymedphys":
        kwargs = {"pymedphys": "[pseudo\npepper = "}
    else:
        kwargs = {"onkodicom": "[pseudo\npepper = ", "pymedphys": toml.dumps({"pseudo": {"pepper": PEPPER}})}
    home, onko_file, pmp_file = _home(tmp_path, monkeypatch, **kwargs)
    before = {p: p.read_bytes() for p in (onko_file, pmp_file) if p.exists()}
    try:
        with pytest.raises(config.PseudonymisationConfigError):
            config.get_pepper()
        with pytest.raises(config.PseudonymisationConfigError):
            pseudo.pseudonymise_dataset(_small_dataset())
        assert {p: p.read_bytes() for p in (onko_file, pmp_file) if p.exists()} == before
    finally:
        _clear_caches()


@pytest.mark.timeout(20)
@pytest.mark.parametrize("loop", ["self", "two files"])
def test_a_pymedphys_redirect_loop_stops_pseudonymisation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, loop: str
) -> None:
    """Contract (#69): a redirect back to a file already read is reported, not followed forever."""
    other = tmp_path / "other.toml"
    home = tmp_path / "home"
    pmp_file = home / ".pymedphys" / "config.toml"
    target = pmp_file if loop == "self" else other
    _home(tmp_path, monkeypatch, pymedphys=toml.dumps({"redirect": str(target)}))
    if loop == "two files":
        other.write_text(toml.dumps({"redirect": str(pmp_file)}))
    try:
        with pytest.raises(config.PseudonymisationConfigError, match="loop"):
            config.get_pepper()
        assert not config.onkodicom_config_path().exists()
    finally:
        _clear_caches()





@pytest.mark.parametrize("which", ["onkodicom", "pymedphys"])
def test_a_config_link_to_an_unreachable_file_stops_pseudonymisation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, which: str
) -> None:
    """Contract: a configuration that is a link to a file that cannot be reached (an offline share) is an error,
    not an absent configuration: nothing is created, so no new pepper replaces the shared one."""
    home = tmp_path / "home"
    link = home / (".OnkoDICOM/pseudonymisation.toml" if which == "onkodicom" else ".pymedphys/config.toml")
    link.parent.mkdir(parents=True)
    link.symlink_to(tmp_path / "offline-share" / "config.toml")
    _use_home(monkeypatch, home)
    try:
        with pytest.raises(config.PseudonymisationConfigError, match="cannot be reached"):
            config.get_pepper()
        assert link.is_symlink() and not link.exists()
        assert not (tmp_path / "offline-share").exists()
        if which == "pymedphys":
            assert not config.onkodicom_config_path().exists()
    finally:
        _clear_caches()




def test_sync_directory_syncs_that_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Contract: _sync_directory opens the directory itself and fsyncs it (POSIX); elsewhere it does nothing."""
    synced = []
    monkeypatch.setattr(config.os, "fsync", lambda fd: synced.append(os.fstat(fd).st_ino))
    config._sync_directory(tmp_path)
    assert synced == ([os.stat(tmp_path).st_ino] if os.name == "posix" else [])


@pytest.mark.parametrize(
    "pseudo_table,bad",
    [
        ({"pepper": 12345, "epoch_jitter": EPOCH_JITTER}, "pepper"),
        ({"pepper": ["a", "list"], "epoch_jitter": EPOCH_JITTER}, "pepper"),
        ({"pepper": "Señor-pepper", "epoch_jitter": EPOCH_JITTER}, "pepper"),
        ({"pepper": PEPPER, "epoch_jitter": "321"}, "epoch_jitter"),
        ({"pepper": PEPPER, "epoch_jitter": 32.1}, "epoch_jitter"),
        ({"pepper": PEPPER, "epoch_jitter": True}, "epoch_jitter"),
    ],
)
@pytest.mark.parametrize("which", ["onkodicom", "pymedphys"])
def test_a_mistyped_setting_stops_pseudonymisation_clearly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pseudo_table: dict, bad: str, which: str
) -> None:
    """Contract: a pepper that is not ASCII text, or a jitter that is not a whole number, is a configuration
    error naming the setting and the file, not a stray exception; the value is not quoted, and nothing is written."""
    _, onko_file, pmp_file = _home(tmp_path, monkeypatch, **{which: toml.dumps({"pseudo": pseudo_table})})
    before = {p: p.read_bytes() for p in (onko_file, pmp_file) if p.exists()}
    try:
        with pytest.raises(config.PseudonymisationConfigError) as refused:
            config.get_pepper() if bad == "pepper" else config.get_epoch_jitter()
        message = str(refused.value)
        assert bad in message and str(onko_file if which == "onkodicom" else pmp_file) in message
        assert str(pseudo_table[bad]) not in message
        assert {p: p.read_bytes() for p in (onko_file, pmp_file) if p.exists()} == before
    finally:
        _clear_caches()


def test_a_jitter_a_site_set_outside_the_generated_range_is_kept(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Contract: pymedphys accepted any whole number as the jitter, so one a site set by hand still works."""
    _home(tmp_path, monkeypatch, pymedphys=toml.dumps({"pseudo": {"pepper": PEPPER, "epoch_jitter": 1500}}))
    try:
        assert config.get_epoch_jitter() == 1500
    finally:
        _clear_caches()


# --- The configuration is written only to create it (#74) -----------------------------------------------------------


def test_an_incomplete_onkodicom_config_is_refused(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Contract: an OnkoDICOM file without both values is refused, not completed, even when pymedphys has the
    missing one: another OnkoDICOM could be completing it differently at the same moment. Nothing is written."""
    _, onko_file, pmp_file = _home(
        tmp_path, monkeypatch,
        onkodicom=toml.dumps({"pseudo": {"pepper": "onkodicom-pepper"}}),
        pymedphys=toml.dumps({"pseudo": {"pepper": "pymedphys-pepper", "epoch_jitter": 33}}),
    )
    before = {p: p.read_bytes() for p in (onko_file, pmp_file)}
    try:
        for get in (config.get_pepper, config.get_epoch_jitter):
            with pytest.raises(config.PseudonymisationConfigError, match="has no epoch_jitter") as refused:
                get()
            assert "onkodicom-pepper" not in str(refused.value)
        assert {p: p.read_bytes() for p in (onko_file, pmp_file)} == before
        assert sorted(p.name for p in onko_file.parent.iterdir()) == ["pseudonymisation.toml"]
    finally:
        _clear_caches()


def test_a_config_reached_by_a_link_is_read_and_not_written(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Contract: a site's shared configuration, reached by a link, is used as it is; the link and the file are unchanged."""
    shared = tmp_path / "share" / "pseudonymisation.toml"
    shared.parent.mkdir()
    shared.write_text(toml.dumps({"pseudo": {"pepper": PEPPER, "epoch_jitter": EPOCH_JITTER}}))
    before = shared.read_bytes()
    home = tmp_path / "home"
    link = home / ".OnkoDICOM" / "pseudonymisation.toml"
    link.parent.mkdir(parents=True)
    link.symlink_to(shared)
    _use_home(monkeypatch, home)
    try:
        assert (config.get_pepper(), config.get_epoch_jitter()) == (PEPPER.encode("ASCII"), EPOCH_JITTER)
        assert link.is_symlink() and shared.read_bytes() == before
        assert sorted(p.name for p in shared.parent.iterdir()) == ["pseudonymisation.toml"]
    finally:
        _clear_caches()


def test_a_failed_creation_leaves_no_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Contract: creation that fails part-way (a full disk) leaves no configuration and no temporary file behind,
    so nothing half-written is ever read as the pepper."""
    _, onko_file, _ = _home(tmp_path, monkeypatch)

    def fail_part_way(data: dict, f) -> None:
        f.write("[pseudo]\n")  # some bytes reach the file, then the disk is full
        raise OSError(28, "No space left on device")

    monkeypatch.setattr(config.toml, "dump", fail_part_way)
    try:
        with pytest.raises(OSError, match="No space left"):
            config.get_pepper()
        assert list(onko_file.parent.iterdir()) == []
    finally:
        _clear_caches()


def test_a_file_system_without_hard_links_stops_pseudonymisation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Contract: if the file cannot be created exclusively, pseudonymisation stops; no pepper is used unsaved."""
    _, onko_file, _ = _home(tmp_path, monkeypatch)

    def no_links(src, dst):
        raise OSError(1, "Operation not permitted")

    monkeypatch.setattr(config.os, "link", no_links)
    try:
        with pytest.raises(config.PseudonymisationConfigError, match="Cannot create"):
            config.get_pepper()
        assert list(onko_file.parent.iterdir()) == []
    finally:
        _clear_caches()


def test_the_directory_is_synced_after_the_file_is_created(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Contract: once the file is linked into place its directory is synced, so a power loss cannot undo it."""
    _, onko_file, _ = _home(tmp_path, monkeypatch)
    events = []
    real_link = os.link

    def link(src, dst):
        real_link(src, dst)
        events.append(("link", Path(dst)))

    monkeypatch.setattr(config.os, "link", link)
    monkeypatch.setattr(config, "_sync_directory", lambda d: events.append(("sync directory", Path(d))))
    try:
        config.get_pepper()
        assert events == [("link", onko_file), ("sync directory", onko_file.parent)]
    finally:
        _clear_caches()


def test_the_values_of_whoever_created_the_file_first_are_used(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Contract (#74): if another OnkoDICOM creates the file between this one finding it absent and creating it,
    this one uses the other's values, not its own, and writes nothing."""
    _, onko_file, _ = _home(tmp_path, monkeypatch)
    theirs = toml.dumps({"pseudo": {"pepper": "the-other-pepper", "epoch_jitter": 7}})
    real_link = os.link

    def the_other_one_wins(src, dst):
        Path(dst).write_text(theirs)  # the other OnkoDICOM's link landed first
        real_link(src, dst)

    monkeypatch.setattr(config.os, "link", the_other_one_wins)
    try:
        assert config.get_pepper() == b"the-other-pepper"
        assert config.get_epoch_jitter() == 7
        assert onko_file.read_text() == theirs
        assert sorted(p.name for p in onko_file.parent.iterdir()) == ["pseudonymisation.toml"]
    finally:
        _clear_caches()


_RACER = """
import json, os, pathlib, sys, time
sys.path.insert(0, os.getcwd())
from src.Model.Pseudonymisation import config
start = pathlib.Path(sys.argv[1])
while not start.exists():
    time.sleep(0.001)
print(json.dumps([config.get_pepper().decode("ASCII"), config.get_epoch_jitter()]))
"""


@pytest.mark.timeout(120)
def test_processes_starting_at_once_use_one_pepper(tmp_path: Path) -> None:
    """Contract (#74): OnkoDICOMs that pseudonymise for the first time at the same moment all use one pepper and
    one jitter, and the file holds exactly those.

    A real race, so it detects a regression only sometimes: against the code before #74 it failed once in five
    runs (every process had cached jitter 895 while the file held 14). It never fails on correct code. The
    deterministic test above is what guards exclusive creation."""
    import json
    import subprocess
    import sys

    home = tmp_path / "home"
    home.mkdir()
    start = tmp_path / "start"
    env = {**os.environ, "HOME": str(home), "USERPROFILE": str(home)}
    racers = [
        subprocess.Popen([sys.executable, "-c", _RACER, str(start)], env=env, stdout=subprocess.PIPE, text=True)
        for _ in range(8)
    ]
    start.touch()
    results = [json.loads(r.communicate()[0]) for r in racers]
    assert all(r.returncode == 0 for r in racers)
    on_disk = toml.loads((home / ".OnkoDICOM" / "pseudonymisation.toml").read_text())["pseudo"]
    assert {tuple(r) for r in results} == {(on_disk["pepper"], on_disk["epoch_jitter"])}
