"""The pseudonymisation pepper and date jitter, kept in OnkoDICOM's configuration.

They live in ``~/.OnkoDICOM/pseudonymisation.toml``, as ``pepper`` and ``epoch_jitter`` in a
``[pseudo]`` table. A site that pseudonymised data with pymedphys, or with OnkoDICOM before
this file existed, has them in ``~/.pymedphys/config.toml``. When OnkoDICOM's file lacks a
value and pymedphys's has it, the value is copied into OnkoDICOM's file, so the site keeps
producing the same pseudonyms; pymedphys's file is never changed. Only when neither has it
is a new value created.

Losing or replacing the pepper or jitter would silently change every pseudonym from then on,
so a configuration that exists but cannot be read stops pseudonymisation instead.
"""

import functools
import logging
import os
import pathlib
import secrets
import stat
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


def _read_onkodicom_config() -> dict:
    """OnkoDICOM's configuration, or an empty one if the file does not exist yet."""
    path = onkodicom_config_path()
    return _read_toml(path) if path.exists() else {}


def _read_pymedphys_config() -> dict:
    """pymedphys's configuration, following its ``redirect`` entries; empty if there is none.

    Raises:
        PseudonymisationConfigError: if it, or a file it redirects to, cannot be read, or the
            redirects loop.
    """
    config_path = pymedphys_config_path()
    if not config_path.exists():
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


def _get_or_move_or_create(key: str, create):
    """Return ``[pseudo] key``: from OnkoDICOM's configuration, else moved from pymedphys's, else new.

    A value moved or created is written to OnkoDICOM's configuration, keeping its other keys.
    """
    onkodicom = _read_onkodicom_config()
    if key in onkodicom.get("pseudo", {}):
        return onkodicom["pseudo"][key]
    pymedphys = _read_pymedphys_config().get("pseudo", {})
    if key in pymedphys:
        value = pymedphys[key]
        logger.info("Pseudonymisation %s copied from the pymedphys configuration to %s", key, onkodicom_config_path())
    else:
        value = create()
        logger.info("Pseudonymisation %s created in %s", key, onkodicom_config_path())
    onkodicom.setdefault("pseudo", {})[key] = value
    path = onkodicom_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    _write_atomically(path, onkodicom)
    return value


def _write_atomically(path: pathlib.Path, config: dict) -> None:
    """Replace ``path`` with ``config`` in one step, so a failure part-way leaves the old file whole.

    Rewriting in place could leave the file empty or partial (a crash, a full disk), and the
    next run would then create a new pepper, changing every pseudonym (#69). The new file
    keeps the old one's permissions; a first file is readable by its owner only.
    """
    # Through a symlink, the file to replace is its target: os.replace would replace the link
    # itself, and a configuration reached by a link would stop being written.
    path = path.resolve()
    mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o600
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            toml.dump(config, f)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp_name, mode)
        os.replace(tmp_name, path)
    except BaseException:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise


@functools.lru_cache()
def get_pepper() -> bytes:
    """Return the pepper added to every hashed value.

    The pepper is not stored with the pseudonymised data, which makes a dictionary attack on
    the pseudonyms harder.

    Raises:
        PseudonymisationConfigError: if a configuration exists but cannot be read.
    """
    return _get_or_move_or_create("pepper", lambda: secrets.token_urlsafe(32)).encode("ASCII")


@functools.lru_cache()
def get_epoch_jitter() -> int:
    """Return the number of days (0 to 999) added to shifted dates.

    Raises:
        PseudonymisationConfigError: if a configuration exists but cannot be read.
    """
    return _get_or_move_or_create("epoch_jitter", lambda: secrets.randbelow(1000))


def clear_cache() -> None:
    """Forget the pepper and jitter read so far, so the next call reads the configuration again."""
    get_pepper.cache_clear()
    get_epoch_jitter.cache_clear()


__all__ = [
    "PseudonymisationConfigError",
    "clear_cache",
    "get_epoch_jitter",
    "get_pepper",
    "onkodicom_config_path",
    "pymedphys_config_path",
]
