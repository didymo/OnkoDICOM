"""The session restore of the directories the tests change (Gitea #7)."""
import subprocess

import pytest

from conftest import MUTABLE_DIRS, REPO_ROOT, restore_dir


def tree(root):
    """Every file under root, as {relative path: text}."""
    return {str(p.relative_to(root)): p.read_text()
            for p in sorted(root.rglob("*")) if p.is_file()}


@pytest.fixture
def saved(tmp_path):
    saved = tmp_path / "snapshot" / "csv"
    (saved / "sub").mkdir(parents=True)
    (saved / "a.csv").write_text("original")
    (saved / "sub" / "b.csv").write_text("nested")
    return saved


def test_restore_puts_back_exactly_what_was_saved(tmp_path, saved):
    target = tmp_path / "data" / "csv"
    target.mkdir(parents=True)
    (target / "a.csv").write_text("changed by a test")
    (target / "added.csv").write_text("written by a test")

    restore_dir(saved, target)

    assert tree(target) == tree(saved)
    assert sorted(p.name for p in target.parent.iterdir()) == ["csv"]


def test_restore_recreates_a_directory_the_tests_deleted(tmp_path, saved):
    target = tmp_path / "data" / "csv"
    target.parent.mkdir()

    restore_dir(saved, target)

    assert tree(target) == tree(saved)


def test_a_failed_copy_leaves_the_directory_as_it_was(tmp_path):
    target = tmp_path / "data" / "csv"
    target.mkdir(parents=True)
    (target / "a.csv").write_text("still here")
    missing = tmp_path / "snapshot" / "csv"

    with pytest.raises(RuntimeError, match=str(missing)):
        restore_dir(missing, target)

    assert tree(target) == {"a.csv": "still here"}


def test_data_an_earlier_restore_left_aside_is_never_deleted(tmp_path, saved):
    target = tmp_path / "data" / "csv"
    target.parent.mkdir()
    left = tmp_path / "data" / ".csv.replaced"
    left.mkdir()
    (left / "patientHash.csv").write_text("the only copy")

    with pytest.raises(RuntimeError, match=str(left)):
        restore_dir(saved, target)

    assert tree(left) == {"patientHash.csv": "the only copy"}
    assert not target.exists()


@pytest.mark.parametrize("rel", MUTABLE_DIRS)
@pytest.mark.parametrize("suffix", ["restoring", "replaced"])
def test_what_a_failed_restore_leaves_is_ignored_by_git(rel, suffix):
    """data/.csv.replaced can hold patientHash.csv: it must never be committed."""
    target = REPO_ROOT / rel
    leftover = target.with_name(f".{target.name}.{suffix}") / "patientHash.csv"
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "check-ignore", "-q",
         str(leftover.relative_to(REPO_ROOT))])
    assert result.returncode == 0, f"{leftover} is not ignored by git"
