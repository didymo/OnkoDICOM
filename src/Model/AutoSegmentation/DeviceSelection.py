import os
import re

DEVICE_ENV_VAR = "ONKODICOM_SEGMENTATION_DEVICE"

# TotalSegmentator's own device vocabulary, so the value is passed through unchanged.
_VALID_DEVICE = re.compile(r"^(cpu|mps|gpu|gpu:\d+)$")


def select_segmentation_device(environ=None) -> tuple[str, bool]:
    """
    Chooses the device TotalSegmentator should run on.

    An explicit setting in the ONKODICOM_SEGMENTATION_DEVICE environment
    variable wins. Otherwise the fastest available device is chosen: an
    NVIDIA GPU through CUDA, then Apple Silicon through MPS, then the CPU.

    Args:
        environ: Mapping to read the override from. Defaults to os.environ.

    Returns:
        tuple: (device, explicit) where device is "gpu", "gpu:N", "mps" or
        "cpu", and explicit is True when it came from the environment variable.

    Raises:
        ValueError: If the environment variable is set to an unknown device.
    """
    environ = os.environ if environ is None else environ
    override = environ.get(DEVICE_ENV_VAR, "").strip().lower()
    if override:
        if not _VALID_DEVICE.match(override):
            raise ValueError(
                f"{DEVICE_ENV_VAR}={override!r} is not a valid device. "
                "Use cpu, mps, gpu or gpu:N."
            )
        return override, True

    import torch  # deferred: torch is heavy and only needed when segmenting

    if torch.cuda.is_available():
        return "gpu", False
    if torch.backends.mps.is_available():
        return "mps", False
    return "cpu", False
