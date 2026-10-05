import sys
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from src.Model.AutoSegmentation.DeviceSelection import DEVICE_ENV_VAR, select_segmentation_device


def _fake_torch(cuda: bool, mps: bool):
    return SimpleNamespace(
        cuda=SimpleNamespace(is_available=lambda: cuda),
        backends=SimpleNamespace(mps=SimpleNamespace(is_available=lambda: mps)),
    )


@pytest.mark.parametrize(
    "cuda, mps, expected",
    [
        (True, True, "gpu"),
        (True, False, "gpu"),
        (False, True, "mps"),
        (False, False, "cpu"),
    ],
    ids=["cuda_and_mps", "cuda_only", "mps_only", "neither"],
)
def test_auto_selection_prefers_cuda_then_mps_then_cpu(cuda, mps, expected):
    # Arrange
    with patch.dict(sys.modules, {"torch": _fake_torch(cuda, mps)}):
        # Act
        device, explicit = select_segmentation_device(environ={})
    # Assert
    assert device == expected
    assert explicit is False


@pytest.mark.parametrize("value", ["cpu", "mps", "gpu", "gpu:0", "gpu:12", "  MPS  ", "CPU"])
def test_valid_override_wins_without_consulting_torch(value):
    # Arrange: a torch that would choose differently, to prove it is not consulted
    with patch.dict(sys.modules, {"torch": _fake_torch(cuda=True, mps=True)}):
        # Act
        device, explicit = select_segmentation_device(environ={DEVICE_ENV_VAR: value})
    # Assert
    assert device == value.strip().lower()
    assert explicit is True


@pytest.mark.parametrize("value", ["cuda", "cuda:0", "gpu:", "gpu:x", "metal", "gpu:0 cpu"])
def test_invalid_override_raises(value):
    with pytest.raises(ValueError, match=DEVICE_ENV_VAR):
        select_segmentation_device(environ={DEVICE_ENV_VAR: value})


@pytest.mark.parametrize("value", ["", "   "])
def test_blank_override_falls_back_to_auto_selection(value):
    with patch.dict(sys.modules, {"torch": _fake_torch(cuda=False, mps=False)}):
        device, explicit = select_segmentation_device(environ={DEVICE_ENV_VAR: value})
    assert (device, explicit) == ("cpu", False)


def test_reads_os_environ_by_default(monkeypatch):
    monkeypatch.setenv(DEVICE_ENV_VAR, "cpu")
    assert select_segmentation_device() == ("cpu", True)
