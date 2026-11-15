"""The pseudonymisation pepper and date jitter, kept in OnkoDICOM's configuration.

They live in ``~/.OnkoDICOM/pseudonymisation.toml``, as ``pepper`` and ``epoch_jitter`` in a
``[pseudo]`` table. A site that pseudonymised data with pymedphys, or with OnkoDICOM before
this file existed, has them in ``~/.pymedphys/config.toml``. When OnkoDICOM's file does not
exist, it is created with both values: each copied from pymedphys's file if it is there, so
the site keeps producing the same pseudonyms, and otherwise new. pymedphys's file is never
changed.

OnkoDICOM writes its file only to create it, never to change it (#74). Two OnkoDICOMs
starting at once both try to create it; the file appears whole or not at all, only one
succeeds, and the other uses the values that one wrote, so both use one pepper. A file that
exists without both values was changed outside OnkoDICOM, and is refused rather than
completed, since another OnkoDICOM could be completing it differently at the same moment.

Losing or replacing the pepper or jitter would silently change every pseudonym from then on,
so a configuration that exists but cannot be read, or is incomplete, stops pseudonymisation.

Sharing the pepper and jitter, so that several users or machines produce linked pseudonyms
(#72): copy ``~/.OnkoDICOM/pseudonymisation.toml`` from the first user's home directory into
each other user's ``~/.OnkoDICOM/``, before that user pseudonymises anything. A user who
pseudonymises first makes a pepper of their own, and their pseudonyms will not link to the
others'. Keep the copy readable by its owner only. The same user on several machines with a
networked home directory already shares the one file. The file has no ``redirect`` of its own,
unlike pymedphys's; pymedphys's redirect is followed only to copy existing values on first use.
"""

import contextlib
import functools
import logging
import os
import pathlib
import secrets
import tempfile

import toml

logger = logging.getLogger(__name__)

ONKODICOM_CONFIG_DIR = ".OnkoDICOM"
ONKODICOM_CONFIG_FILENAME = "pseudonymisation.toml"
PYMEDPHYS_CONFIG_DIR = ".pymedphys"
PYMEDPHYS_CONFIG_FILENAME = "config.toml"


class PseudonymisationConfigError(OSError):
    """A configuration exists but cannot be read, so the pepper and jitter are unknown.

    Pseudonymisation stops rather than create a new pepper, which would silently change
    every pseudonym from then on.
    """


def onkodicom_config_path() -> pathlib.Path:
    """``~/.OnkoDICOM/pseudonymisation.toml``, in the directory OnkoDICOM keeps its configuration."""
    return pathlib.Path.home().joinpath(ONKODICOM_CONFIG_DIR, ONKODICOM_CONFIG_FILENAME)


def pymedphys_config_path() -> pathlib.Path:
    """``~/.pymedphys/config.toml``, where pymedphys kept the pepper and jitter."""
    return pathlib.Path.home().joinpath(PYMEDPHYS_CONFIG_DIR, PYMEDPHYS_CONFIG_FILENAME)


def _read_toml(path: pathlib.Path) -> dict:
    """Read one TOML file.

    Raises:
        PseudonymisationConfigError: if it cannot be read or is not valid TOML.
    """
    try:
        with open(path) as f:
            return toml.load(f)
    except (OSError, toml.TomlDecodeError) as error:
        raise PseudonymisationConfigError(
            f"Cannot read the pseudonymisation configuration {path}: {error}. "
            "Pseudonymisation stopped so that the pepper and jitter are not replaced."
        ) from error


def _exists(path: pathlib.Path) -> bool:
    """Whether ``path`` exists; a symlink whose target cannot be reached is an error, not absence.

    ``Path.exists()`` is false for such a link (a shared configuration on a share that is
    offline), and treating that as "no configuration" would create a new pepper.

    Raises:
        PseudonymisationConfigError: if ``path`` is a symlink whose target does not exist.
    """
    if path.exists():
        return True
    if path.is_symlink():
        raise PseudonymisationConfigError(
            f"The pseudonymisation configuration {path} is a link to {os.readlink(path)}, which cannot "
            "be reached. Pseudonymisation stopped so that the pepper and jitter are not replaced."
        )
    return False


def _read_onkodicom_config() -> dict:
    """OnkoDICOM's configuration, or an empty one if the file does not exist yet.

    Raises:
        PseudonymisationConfigError: if it exists but cannot be read, or is a broken link.
    """
    path = onkodicom_config_path()
    return _read_toml(path) if _exists(path) else {}


def _read_pymedphys_config() -> dict:
    """pymedphys's configuration, following its ``redirect`` entries; empty if there is none.

    Raises:
        PseudonymisationConfigError: if it, or a file it redirects to, cannot be read, or the
            redirects loop.
    """
    config_path = pymedphys_config_path()
    if not _exists(config_path):
        return {}
    read_already: set[pathlib.Path] = set()
    while True:
        resolved = config_path.resolve()
        if resolved in read_already:
            raise PseudonymisationConfigError(
                f"The pymedphys configuration redirects in a loop back to {config_path}. "
                "Pseudonymisation stopped so that the pepper and jitter are not replaced."
            )
        read_already.add(resolved)
        results = _read_toml(config_path)
        try:
            config_path = pathlib.Path(results["redirect"])
        except KeyError:
            return results


KEYS = ("pepper", "epoch_jitter")


def _valid_pepper(value) -> bool:
    return isinstance(value, str) and value.isascii()


def _valid_jitter(value) -> bool:
    # A new jitter is from 0 to 999, but pymedphys accepted any whole number, and a site may have set one.
    return isinstance(value, int) and not isinstance(value, bool)


_VALID = {"pepper": _valid_pepper, "epoch_jitter": _valid_jitter}
_NEW = {"pepper": lambda: secrets.token_urlsafe(32), "epoch_jitter": lambda: secrets.randbelow(1000)}


def _checked(key: str, value, path: pathlib.Path):
    """Return ``value`` if it is valid for ``key``.

    Raises:
        PseudonymisationConfigError: otherwise; the value is not quoted, since it may be the pepper.
    """
    if not _VALID[key](value):
        raise PseudonymisationConfigError(
            f"The pseudonymisation {key} in {path} is not valid (a {type(value).__name__}). "
            "Pseudonymisation stopped so that the pepper and jitter are not replaced."
        )
    return value


def _complete(config: dict, path: pathlib.Path) -> dict:
    """Return the pepper and jitter of OnkoDICOM's configuration, which must hold both.

    Raises:
        PseudonymisationConfigError: if either is missing or not valid.
    """
    pseudo = config.get("pseudo", {})
    missing = [key for key in KEYS if key not in pseudo]
    if missing:
        raise PseudonymisationConfigError(
            f"The pseudonymisation configuration {path} has no {' and no '.join(missing)}. OnkoDICOM writes that file "
            "only when it creates it, with both values, so it was changed by something else. Pseudonymisation stopped "
            "rather than add a value that another OnkoDICOM could be adding differently at the same moment. Add the "
            "missing value from wherever this site keeps it; if this site has never pseudonymised data, the file can "
            "be deleted, and it will be created again."
        )
    return {key: _checked(key, pseudo[key], path) for key in KEYS}


def _create(path: pathlib.Path) -> dict:
    """Create OnkoDICOM's configuration with both values, from pymedphys's where it has them, else new.

    If another OnkoDICOM creates it first, its values are used instead, so both use one pepper.

    Raises:
        PseudonymisationConfigError: if pymedphys's configuration cannot be read or holds an
            invalid value, or OnkoDICOM's cannot be created.
    """
    pymedphys = _read_pymedphys_config().get("pseudo", {})
    values = {}
    for key in KEYS:
        if key in pymedphys:
            values[key] = _checked(key, pymedphys[key], pymedphys_config_path())
            logger.info("Pseudonymisation %s copied from the pymedphys configuration to %s", key, path)
        else:
            values[key] = _NEW[key]()
            logger.info("Pseudonymisation %s created in %s", key, path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if _create_exclusively(path, {"pseudo": values}):
        return values
    logger.info("Pseudonymisation configuration %s was created by another OnkoDICOM first; its values are used", path)
    return _complete(_read_toml(path), path)


def _create_exclusively(path: pathlib.Path, config: dict) -> bool:
    """Create ``path`` holding ``config``, unless it already exists. Return whether this call created it.

    The file is written and synced under a temporary name and then hard-linked to ``path``.
    A link fails if ``path`` exists, so of several processes creating it at once exactly one
    succeeds, and no process ever reads it partly written. The directory is synced after the
    link, so a power loss cannot undo it. The file is readable by its owner only: it holds the
    pepper.

    Raises:
        PseudonymisationConfigError: if the file cannot be created, for example on a file
            system without hard links.
    """
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            toml.dump(config, f)
            f.flush()
            os.fsync(f.fileno())
        try:
            os.link(tmp_name, path)
        except FileExistsError:
            return False
        except OSError as error:
            raise PseudonymisationConfigError(
                f"Cannot create the pseudonymisation configuration {path}: {error}. Pseudonymisation stopped."
            ) from error
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(tmp_name)
    _sync_directory(path.parent)
    return True


def _sync_directory(directory: pathlib.Path) -> None:
    """Make a new entry in ``directory`` durable. POSIX only: Windows cannot open a directory to sync it."""
    if os.name != "posix":
        return
    fd = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


@functools.lru_cache()
def _settings() -> dict:
    """The pepper and jitter, read once per process: from OnkoDICOM's configuration, or by creating it.

    Raises:
        PseudonymisationConfigError: if a configuration cannot be read, is incomplete or
            holds an invalid value, or OnkoDICOM's cannot be created.
    """
    path = onkodicom_config_path()
    if _exists(path):
        return _complete(_read_toml(path), path)
    return _create(path)


def get_pepper() -> bytes:
    """Return the pepper added to every hashed value.

    The pepper is not stored with the pseudonymised data, which makes a dictionary attack on
    the pseudonyms harder.

    Raises:
        PseudonymisationConfigError: see ``_settings``.
    """
    return _settings()["pepper"].encode("ASCII")


def get_epoch_jitter() -> int:
    """Return the number of days added to shifted dates (a new jitter is from 0 to 999).

    Raises:
        PseudonymisationConfigError: see ``_settings``.
    """
    return _settings()["epoch_jitter"]


def clear_cache() -> None:
    """Forget the pepper and jitter read so far, so the next call reads the configuration again."""
    _settings.cache_clear()


__all__ = [
    "PseudonymisationConfigError",
    "clear_cache",
    "get_epoch_jitter",
    "get_pepper",
    "onkodicom_config_path",
    "pymedphys_config_path",
]
