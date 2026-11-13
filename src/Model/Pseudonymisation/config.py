"""The pseudonymisation pepper and date jitter, kept in ``~/.pymedphys/config.toml``.

The file, its ``[pseudo]`` table and the ``pepper`` and ``epoch_jitter`` keys are the
ones pymedphys uses. A site that has already pseudonymised data with pymedphys keeps
its pepper and jitter, and so keeps producing the same pseudonyms. Moving the file
would silently change every pseudonym and break the link between old and new data.
"""

import functools
import pathlib
import secrets

import toml

CONFIG_FILENAME = "config.toml"


def get_config_dir() -> pathlib.Path:
    """Return ``~/.pymedphys``, creating it if it does not exist."""
    config_dir = pathlib.Path.home().joinpath(".pymedphys")
    config_dir.mkdir(exist_ok=True)
    return config_dir


def get_config(path: pathlib.Path | None = None) -> dict:
    """Read the configuration, following any ``redirect`` entries.

    Raises:
        OSError: if a configuration file cannot be read.
    """
    if path is None:
        path = get_config_dir()
    config_path = pathlib.Path(path).joinpath(CONFIG_FILENAME)
    while True:
        with open(config_path) as f:
            results = toml.load(f)
        try:
            config_path = pathlib.Path(results["redirect"])
        except KeyError:
            break
    return results


def _store_pseudo_value(config: dict | None, key: str, value) -> None:
    """Add ``[pseudo] key = value`` to the configuration and write it to ``~/.pymedphys``.

    Other keys in the configuration are kept. As in pymedphys, the write goes to
    ``~/.pymedphys/config.toml`` even when the configuration was read through a redirect.
    """
    if config is None:
        config = {}
    pseudo_config = config.setdefault("pseudo", {})
    pseudo_config.setdefault(key, value)
    with open(get_config_dir().joinpath(CONFIG_FILENAME), "w") as f:
        toml.dump(config, f)


@functools.lru_cache()
def get_pepper() -> bytes:
    """Return the pepper added to every hashed value, creating and storing one if needed.

    The pepper is not stored with the pseudonymised data, which makes a dictionary
    attack on the pseudonyms harder.
    """
    config = None
    try:
        config = get_config()
        return config["pseudo"]["pepper"].encode("ASCII")
    except (KeyError, OSError):
        pepper = secrets.token_urlsafe(32)
        _store_pseudo_value(config, "pepper", pepper)
        return pepper.encode("ASCII")


@functools.lru_cache()
def get_epoch_jitter() -> int:
    """Return the number of days (0 to 999) added to shifted dates, creating and storing it if needed."""
    config = None
    try:
        config = get_config()
        return config["pseudo"]["epoch_jitter"]
    except (KeyError, OSError):
        epoch_jitter = secrets.randbelow(1000)
        _store_pseudo_value(config, "epoch_jitter", epoch_jitter)
        return epoch_jitter


def clear_cache() -> None:
    """Forget the pepper and jitter read so far, so the next call reads the configuration again."""
    get_pepper.cache_clear()
    get_epoch_jitter.cache_clear()


__all__ = ["get_config", "get_config_dir", "get_epoch_jitter", "get_pepper", "clear_cache"]
