import ctypes
import os
import types

import src.Model.Configuration as configuration_module
from src.Model.Configuration import set_up_hidden_dir

FILE_ATTRIBUTE_HIDDEN = 2


def _fake_windll(calls):
    """A kernel32 stand-in that converts arguments the way ctypes does.

    Without declared argtypes, ctypes passes a str as a wide string and
    refuses anything else (a Path included) with ctypes.ArgumentError.
    """
    def set_file_attributes_w(path, attributes):
        if not isinstance(path, str):
            raise ctypes.ArgumentError(
                "argument 1: TypeError: Don't know how to convert parameter 1")
        calls.append((path, attributes))
        return 1

    kernel32 = types.SimpleNamespace(SetFileAttributesW=set_file_attributes_w)
    return types.SimpleNamespace(kernel32=kernel32)


def test_first_run_on_windows_creates_and_hides_dir(tmp_path, monkeypatch):
    """Contract: on a first run under Windows (no hidden directory yet), the
    directory is created and marked hidden instead of raising."""
    calls = []
    # Restore the session's hidden-dir env var when the test ends.
    monkeypatch.setenv('USER_ONKODICOM_HIDDEN',
                       os.environ.get('USER_ONKODICOM_HIDDEN', ''))
    monkeypatch.setattr(configuration_module.Path, 'home',
                        classmethod(lambda cls: tmp_path))
    monkeypatch.setattr(configuration_module.platform, 'system',
                        lambda: 'Windows')
    monkeypatch.setattr(configuration_module.ctypes, 'windll',
                        _fake_windll(calls), raising=False)

    set_up_hidden_dir('.OnkoDICOM')

    hidden = tmp_path / '.OnkoDICOM'
    assert hidden.is_dir()
    assert os.environ['USER_ONKODICOM_HIDDEN'] == str(hidden)
    assert calls == [(str(hidden), FILE_ATTRIBUTE_HIDDEN)]
