"""
Which plastimatch OnkoDICOM runs (Gitea #93): the copy inside the macOS app
first, else plastimatch on PATH.
"""
import sys

import pytest

from src.Model import Plastimatch


@pytest.fixture
def on_path(monkeypatch, tmp_path):
    """shutil.which answers with a plastimatch on PATH, and records the call."""
    found = str(tmp_path / "on-path" / "plastimatch")
    asked = []

    def which(name):
        asked.append(name)
        return found

    monkeypatch.setattr(Plastimatch.shutil, "which", which)
    return found, asked


def _frozen(monkeypatch, meipass):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(meipass), raising=False)


def test_frozen_app_runs_its_own_plastimatch(monkeypatch, tmp_path, on_path):
    """Contract: inside the app, the bundled plastimatch wins over PATH."""
    bundled = tmp_path / "Frameworks" / Plastimatch.BUNDLED
    bundled.parent.mkdir(parents=True)
    bundled.write_bytes(b"#!/bin/sh\n")
    _frozen(monkeypatch, tmp_path / "Frameworks")

    assert Plastimatch.executable() == str(bundled)
    assert on_path[1] == []


def test_frozen_app_without_a_bundled_copy_uses_path(monkeypatch, tmp_path, on_path):
    """Contract: the Windows and Linux apps carry none, and still find it on PATH."""
    (tmp_path / "Frameworks").mkdir()
    _frozen(monkeypatch, tmp_path / "Frameworks")

    assert Plastimatch.executable() == on_path[0]
    assert on_path[1] == ["plastimatch"]


def test_a_directory_at_the_bundled_path_is_not_plastimatch(monkeypatch, tmp_path, on_path):
    """Contract: only a file counts as the bundled copy."""
    (tmp_path / "Frameworks" / Plastimatch.BUNDLED).mkdir(parents=True)
    _frozen(monkeypatch, tmp_path / "Frameworks")

    assert Plastimatch.executable() == on_path[0]


def test_from_source_uses_path_even_beside_a_bundle(monkeypatch, tmp_path, on_path):
    """Contract: run from source, sys._MEIPASS is not consulted."""
    bundled = tmp_path / Plastimatch.BUNDLED
    bundled.parent.mkdir(parents=True)
    bundled.write_bytes(b"#!/bin/sh\n")
    monkeypatch.delattr(sys, "frozen", raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)

    assert Plastimatch.executable() == on_path[0]


def test_no_plastimatch_anywhere_is_none(monkeypatch, tmp_path):
    """Contract: None, so the GUI can say plastimatch is missing."""
    monkeypatch.setattr(Plastimatch.shutil, "which", lambda name: None)
    _frozen(monkeypatch, tmp_path)

    assert Plastimatch.executable() is None
