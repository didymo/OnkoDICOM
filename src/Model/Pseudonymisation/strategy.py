"""Replacement values for pseudonymisation, one function per DICOM value representation (VR).

Each function gives the same result as the function for that VR in pymedphys 0.41.0
(``pymedphys._experimental.pseudonymisation.strategy``), so data pseudonymised before
and after the move to this module stays linked. That includes behaviour that looks
odd but is load-bearing for equivalence, and each such case is commented where it occurs.

Strings are hashed with SHA3-256 and the pepper, then cut to the VR's maximum length.
Dates are shifted. Ages are coarsened. Times and binary values are left unchanged.
"""

import base64
import datetime
import hashlib
import secrets
from collections.abc import Callable
from decimal import Decimal

import pydicom

from src.Model.Pseudonymisation.config import get_epoch_jitter, get_pepper

# The root UID that pymedphys registered with Medical Connections. Pseudonymous UIDs
# are created under it, as pymedphys does, so that existing pseudonymous UIDs are reproduced.
PSEUDONYM_ROOT_UID = "1.2.826.0.1.3680043.10.188"

EPOCH_START = "20000101"
DEFAULT_EARLIEST_STUDY_DATE = "20040415"
DICOM_DATE_FORMAT_STR = "%Y%m%d"
DICOM_DATETIME_FORMAT_STR = "%Y%m%d%H%M%S.%f"


def hash_text(value) -> str:
    """Return the base64 SHA3-256 hash of ``value`` with the pepper, without its trailing ``=``.

    A value that is not a string is hashed as ``str(value)``. For a multi-valued element
    that is the text of the whole list, so the element gets one pseudonym, as in pymedphys.

    The text is encoded as UTF-8. For ASCII text that is the same bytes as pymedphys's ASCII
    encoding, so every pseudonym pymedphys made is unchanged; pymedphys refused non-ASCII
    text, so no earlier pseudonym of such text exists. pydicom has already decoded the value
    from the file's character set, so the same name gives the same pseudonym whichever
    character set its file used.
    """
    try:
        encoded_value = value.encode("UTF-8")
    except AttributeError:
        encoded_value = str(value).encode("UTF-8")
    hash_func = hashlib.new("sha3_256")
    hash_func.update(encoded_value)
    hash_func.update(get_pepper())
    text = base64.standard_b64encode(hash_func.digest()).decode("ASCII")
    # A 32-byte digest always encodes to 43 characters plus one "=".
    if text.endswith("="):
        text = text[:-1]
    return text


def pseudonymise_AE(value) -> str:
    return hash_text(value)[0:16]


def pseudonymise_AS(value) -> str:
    """Return an age near ``value`` (DICOM AS, e.g. ``"045Y"``).

    Over 80 becomes 80. From 21 to 80 is rounded down to the decade. From 11 to 20 is
    moved by a random step. At 10 or under, the age is converted to the next smaller unit
    (years to months, months to weeks, weeks to days) and moved by a random step. The step
    is -2, -1, 0 or 1: pymedphys's ``random.randrange(-2, 2)`` excludes 2, and that range is kept.

    An age of zero stays zero: pymedphys could turn ``000Y`` into ``-02M``, which is not a DICOM
    age, so a step below zero is the one place this differs from pymedphys.

    Raises:
        ValueError: for an age of 10 days or fewer, which pymedphys also cannot pseudonymise
            (it fails there with an UnboundLocalError), and for a value shorter than the four
            characters of a DICOM age, where pymedphys failed with an IndexError.
    """
    if len(value) < 4:
        raise ValueError(f"Cannot pseudonymise an age of {value!r}: a DICOM age has four characters")
    increment = secrets.randbelow(4) - 2
    numeric = int(value[0:3])
    unit = value[3]
    pseudo_unit = unit
    if numeric > 20:
        pseudo_numeric = numeric - (numeric % 10)
        if numeric > 80:
            pseudo_numeric = 80
    elif numeric > 10:
        pseudo_numeric = numeric + increment
    elif unit == "Y":
        pseudo_numeric = 12 * numeric + increment
        pseudo_unit = "M"
    elif unit == "M":
        pseudo_numeric = 4 * numeric + increment
        pseudo_unit = "W"
    elif unit == "W":
        pseudo_numeric = 7 * numeric + increment
        pseudo_unit = "D"
    else:
        raise ValueError(f"Cannot pseudonymise an age of {value!r}: no unit smaller than days")
    return str(max(pseudo_numeric, 0)).zfill(3) + pseudo_unit


def pseudonymise_CS(value) -> str:
    """Upper case, with ``+`` removed and ``/`` replaced by ``_``, cut to 15 characters."""
    return str(hash_text(value).upper().replace("+", "").replace("/", "_"))[0:15]


def _with_tzinfo(d: datetime.datetime, tz: datetime.tzinfo | None) -> datetime.datetime:
    return datetime.datetime.combine(d.date(), d.time(), tz)


def pseudonymise_DA(value, format_str: str = DICOM_DATE_FORMAT_STR) -> str:
    """Shift a date so that DEFAULT_EARLIEST_STUDY_DATE lands on EPOCH_START plus the jitter.

    Intervals between dates are kept. The value is parsed as a DICOM DT, as pymedphys does,
    which also accepts a DA.

    Raises:
        ValueError: if the value is not a conformant DICOM date or date-time.
    """
    my_datetime = pydicom.valuerep.DT(value)
    tz = my_datetime.tzinfo
    earliest_study = _with_tzinfo(pydicom.valuerep.DT(DEFAULT_EARLIEST_STUDY_DATE), tz)
    epoch_start = _with_tzinfo(pydicom.valuerep.DT(EPOCH_START), tz)
    epoch_start = epoch_start + datetime.timedelta(days=get_epoch_jitter())
    my_datetime = _with_tzinfo(my_datetime, tz)
    return (epoch_start + (my_datetime - earliest_study)).strftime(format_str)


def pseudonymise_DT(value) -> str:
    """As DA, written as a date-time with microseconds and no time zone."""
    return pseudonymise_DA(value, format_str=DICOM_DATETIME_FORMAT_STR)


def pseudonymise_DS(value) -> str:
    """Keep the sign and exponent of a decimal string and replace its digits from a hash.

    The hash has no pepper, as in pymedphys.

    The digits come from the first hexadecimal digits of the hash, read as one integer. That
    integer can have fewer decimal digits than the value (``"00"`` is 0), and pymedphys then
    failed, so about one valid two-digit value in 25 could not be pseudonymised. Here it is
    padded with leading zeros instead; wherever pymedphys gave a result, this gives the same.

    Raises:
        decimal.InvalidOperation: if the value (for example a multi-valued element) is not one decimal.
    """
    # str() gives the original text of a pydicom DSfloat or DSdecimal.
    original = str(value)
    as_tuple = Decimal(original).as_tuple()
    count_digits = len(as_tuple.digits)
    hex_digest = hashlib.new("sha3_256", original.encode("ASCII")).hexdigest()
    integer_string = str(int(hex_digest[0:count_digits], 16)).zfill(count_digits)
    new_digits = tuple(int(integer_string[i : i + 1]) for i in range(count_digits))
    return str(Decimal((as_tuple.sign, new_digits, as_tuple.exponent)))


def pseudonymise_LO(value) -> str:
    return hash_text(value)[0:64]


def pseudonymise_LT(value) -> str:
    return hash_text(value)[0:10240]


def _strip_plus_slash(value: str) -> str:
    return value.replace("+", "").replace("/", "")


def pseudonymise_PN(value, max_component_length: int = 64) -> str:
    """Hash the family, given and middle names separately; drop the prefix and suffix.

    A missing component is hashed as an empty string, so every component of the result
    is non-empty, as in pymedphys.
    """
    name = pydicom.valuerep.PersonName(value)
    family = _strip_plus_slash(hash_text(name.family_name))[0:max_component_length]
    given = _strip_plus_slash(hash_text(name.given_name))[0:max_component_length]
    middle = _strip_plus_slash(hash_text(name.middle_name))[0:max_component_length]
    return f"{family}^{given}^{middle}^^"


def pseudonymise_SH(value) -> str:
    return hash_text(value)[0:16]


def pseudonymise_ST(value) -> str:
    return hash_text(value)[0:1024]


def pseudonymise_UI(value) -> str | list[str]:
    """Return a UID under PSEUDONYM_ROOT_UID made from the hash of ``value``.

    The hash has no pepper, as in pymedphys. A multi-valued element gets each UID
    pseudonymised separately, so each still matches the same UID wherever else it appears;
    pymedphys refused a multi-valued UI.
    """
    if not isinstance(value, str):
        return [pseudonymise_UI(uid) for uid in value]
    hex_digest = hashlib.new("sha3_256", value.encode("ASCII")).hexdigest()
    chars_available = 63 - len(PSEUDONYM_ROOT_UID)
    big_int = int(hex_digest[0:chars_available], 16)
    return PSEUDONYM_ROOT_UID + "." + str(big_int)[0:chars_available]


def unchanged(value):
    return value


DISPATCH: dict[str, Callable] = {
    "AE": pseudonymise_AE,
    "AS": pseudonymise_AS,
    "CS": pseudonymise_CS,
    "DA": pseudonymise_DA,
    "DS": pseudonymise_DS,
    "DT": pseudonymise_DT,
    "LO": pseudonymise_LO,
    "LT": pseudonymise_LT,
    "OB": unchanged,
    "OB or OW": unchanged,
    "OW": unchanged,
    "PN": pseudonymise_PN,
    "SH": pseudonymise_SH,
    "ST": pseudonymise_ST,
    "TM": unchanged,
    "UI": pseudonymise_UI,
    "US": unchanged,
}
