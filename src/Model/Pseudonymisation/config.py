"""The pseudonymisation pepper and date jitter, kept in ``~/.pymedphys/config.toml``.

The file, its ``[pseudo]`` table and the ``pepper`` and ``epoch_jitter`` keys are the
ones pymedphys uses. A site that has already pseudonymised data with pymedphys keeps
its pepper and jitter, and so keeps producing the same pseudonyms. Moving the file
would silently change every pseudonym and break the link between old and new data.

Where this differs from pymedphys it is only when the configuration cannot be read, or
is read through a ``redirect``: pymedphys then created a new pepper and overwrote
``~/.pymedphys/config.toml``, losing the redirect and every other setting in it.
"""

import functools
import os
import pathlib
import secrets
import stat
import tempfile

import toml

CONFIG_FILENAME = "config.toml"


def get_config_dir() -> pathlib.Path:
    """Return ``~/.pymedphys``, creating it if it does not exist."""
    config_dir = pathlib.Path.home().joinpath(".pymedphys")
    config_dir.mkdir(exist_ok=True)
    return config_dir


class PseudonymisationConfigError(OSError):
    """The configuration exists but cannot be read, so the pepper and jitter are unknown.

    Pseudonymisation stops rather than create a new pepper: a new pepper would silently
    change every pseudonym from then on, and writing it would overwrite the configuration
    that could not be read (including any ``redirect`` to a shared configuration).
    """


def _read_config() -> tuple[dict, pathlib.Path] | None:
    """Read the configuration, following ``redirect`` entries.

    Returns:
        ``(configuration, path of the file it came from)``, or ``None`` when there is no
        ``~/.pymedphys/config.toml`` at all (a first run).

    Raises:
        PseudonymisationConfigError: if the file, or a file it redirects to, cannot be read.
    """
    config_path = get_config_dir().joinpath(CONFIG_FILENAME)
    if not config_path.exists():
        return None
    read_already: set[pathlib.Path] = set()
    while True:
        resolved = config_path.resolve()
        if resolved in read_already:
            raise PseudonymisationConfigError(
                f"The pseudonymisation configuration redirects in a loop back to {config_path}. "
                "Pseudonymisation stopped so that the pepper and jitter are not replaced."
            )
        read_already.add(resolved)
        try:
            with open(config_path) as f:
                results = toml.load(f)
        except (OSError, toml.TomlDecodeError) as error:
            raise PseudonymisationConfigError(
                f"Cannot read the pseudonymisation configuration {config_path}: {error}. "
                "Pseudonymisation stopped so that the pepper and jitter are not replaced."
            ) from error
        try:
            config_path = pathlib.Path(results["redirect"])
        except KeyError:
            return results, config_path


def get_config() -> dict:
    """Return the configuration (empty on a first run), following ``redirect`` entries.

    Raises:
        PseudonymisationConfigError: if the configuration exists but cannot be read.
    """
    read = _read_config()
    return {} if read is None else read[0]


def _get_or_create(key: str, create):
    """Return ``[pseudo] key`` from the configuration, creating and storing it if it is missing.

    A created value is stored in the file the configuration was read from: through a
    ``redirect``, that is the shared file, and ``~/.pymedphys/config.toml`` keeps its redirect.
    Every other key in that file is kept.
    """
    read = _read_config()
    config, path = read if read is not None else ({}, get_config_dir().joinpath(CONFIG_FILENAME))
    pseudo_config = config.get("pseudo", {})
    if key in pseudo_config:
        return pseudo_config[key]
    value = create()
    config.setdefault("pseudo", {})[key] = value
    _write_atomically(path, config)
    return value


def _write_atomically(path: pathlib.Path, config: dict) -> None:
    """Replace ``path`` with ``config`` in one step, so a failure part-way leaves the old file whole.

    Rewriting in place could leave the file empty or partial (a crash, a full disk), and the
    next run would then find no pepper and create a new one, changing every pseudonym (#69).
    The new file keeps the old one's permissions; a first file is readable by its owner only.
    """
    # Through a symlink, the file to replace is its target: os.replace would replace the link
    # itself, and a shared configuration reached by a link would stop being written (Connor).
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
    """Return the pepper added to every hashed value, creating and storing one if needed.

    The pepper is not stored with the pseudonymised data, which makes a dictionary
    attack on the pseudonyms harder.

    Raises:
        PseudonymisationConfigError: if the configuration exists but cannot be read.
    """
    return _get_or_create("pepper", lambda: secrets.token_urlsafe(32)).encode("ASCII")


@functools.lru_cache()
def get_epoch_jitter() -> int:
    """Return the number of days (0 to 999) added to shifted dates, creating and storing it if needed.

    Raises:
        PseudonymisationConfigError: if the configuration exists but cannot be read.
    """
    return _get_or_create("epoch_jitter", lambda: secrets.randbelow(1000))


def clear_cache() -> None:
    """Forget the pepper and jitter read so far, so the next call reads the configuration again."""
    get_pepper.cache_clear()
    get_epoch_jitter.cache_clear()


__all__ = ["PseudonymisationConfigError", "get_config", "get_config_dir", "get_epoch_jitter", "get_pepper", "clear_cache"]
