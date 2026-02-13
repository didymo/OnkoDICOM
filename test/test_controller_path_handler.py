from pathlib import Path

from src.Controller.PathHandler import data_path, read_line_fill_configuration


def test_data_path_finds_file_from_current_working_tree(tmp_path, monkeypatch):
    nested = tmp_path / "some" / "nested"
    nested.mkdir(parents=True)
    target = nested / "sample.csv"
    target.write_text("a,b\n1,2\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)

    resolved = data_path("sample.csv")
    assert Path(resolved) == target


def test_data_path_missing_file_returns_hidden_data_path(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.chdir(tmp_path)

    resolved = data_path("missing_file.csv")
    expected = tmp_path / ".OnkoDICOM" / "data" / "missing_file.csv"
    assert Path(resolved) == expected


def test_read_line_fill_configuration_handles_partial_invalid_file(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    config_dir = tmp_path / ".OnkoDICOM" / "data"
    config_dir.mkdir(parents=True)
    config_path = config_dir / "line&fill_configuration"
    config_path.write_text("3\nbad\n4\n\ninvalid\n", encoding="utf-8")

    roi_line, roi_opacity, iso_line, iso_opacity, line_width = (
        read_line_fill_configuration()
    )

    assert roi_line == 3
    assert roi_opacity == 10
    assert iso_line == 4
    assert iso_opacity == 5
    assert line_width == 2.0
