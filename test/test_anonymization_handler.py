"""Contract: when pseudonymisation refuses, the Anonymize action tells the user why instead of failing with a traceback."""

from unittest.mock import MagicMock

import pytest
from PySide6 import QtWidgets

from src.Controller.ActionHandler import ActionHandler
from src.Model.Pseudonymisation import UnknownTagsError
from src.Model.Pseudonymisation.config import PseudonymisationConfigError


def _handler(run_anonymization) -> tuple[ActionHandler, MagicMock]:
    """An ActionHandler with only what anonymization_handler uses: the main page and the patient container."""
    handler = ActionHandler.__new__(ActionHandler)
    main_page = MagicMock()
    main_page.call_class.run_anonymization.side_effect = run_anonymization
    handler._ActionHandler__main_page = main_page
    handler.patient_dict_container = MagicMock()
    return handler, main_page


@pytest.mark.parametrize(
    "error",
    [
        PseudonymisationConfigError("Cannot read the pseudonymisation configuration /home/x/.OnkoDICOM/pseudonymisation.toml"),
        UnknownTagsError("These public elements are not in pydicom's DICOM dictionary: RS.dcm: (0012,0099)"),
    ],
)
def test_a_refusal_is_shown_to_the_user(monkeypatch: pytest.MonkeyPatch, error: Exception) -> None:
    shown = []
    monkeypatch.setattr(QtWidgets.QMessageBox, "information", lambda *args: QtWidgets.QMessageBox.Yes)
    monkeypatch.setattr(QtWidgets.QMessageBox, "critical", lambda parent, title, text: shown.append((title, text)))

    def refuse(raw_dvh):
        raise error

    handler, main_page = _handler(refuse)
    handler.anonymization_handler()

    ((title, text),) = shown
    assert title == "Anonymization stopped"
    assert str(error) in text and "incomplete" in text
    handler.patient_dict_container.set.assert_not_called()  # no hashed_path for a run that stopped
    main_page.pyradi_trigger.emit.assert_not_called()


def test_other_errors_are_not_swallowed(monkeypatch: pytest.MonkeyPatch) -> None:
    """Contract: only the deliberate refusals become a message; anything else still raises."""
    monkeypatch.setattr(QtWidgets.QMessageBox, "information", lambda *args: QtWidgets.QMessageBox.Yes)
    monkeypatch.setattr(QtWidgets.QMessageBox, "critical", lambda *args: pytest.fail("a message was shown"))

    def fail(raw_dvh):
        raise RuntimeError("something else")

    handler, _ = _handler(fail)
    with pytest.raises(RuntimeError, match="something else"):
        handler.anonymization_handler()
