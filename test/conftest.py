import os
import sys
import shutil
import sqlite3
from pathlib import Path
import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import qInstallMessageHandler
import traceback
import faulthandler, sys, threading

from src.Model.Configuration import Configuration

def qt_message_handler(msg_type, context, message):
    print(f"Qt Message - Type: {msg_type}")
    print(f"Context: {context}")
    print(f"Message: {message}")
    print(f"Stack trace: {traceback.format_stack()}")


@pytest.fixture(scope="module", autouse=True)
def init_config(request):
    configuration = Configuration('TestConfig.db')
    db_file_path = Path(os.environ['USER_ONKODICOM_HIDDEN']).joinpath('TestConfig.db')
    configuration.set_db_file_path(db_file_path)
    connection = sqlite3.connect(db_file_path)
    configuration.update_default_directory(Path.cwd().joinpath('test', 'testdata'))

    def tear_down():
        connection.close()
        if os.path.isfile(db_file_path):
            os.remove(db_file_path)

    request.addfinalizer(tear_down)
    return connection


@pytest.fixture(scope="session", autouse=True)
def qapp_auto():
    app = QApplication(sys.argv)
    qInstallMessageHandler(qt_message_handler)
    yield app
    app.processEvents()
    app.quit()


REPO_ROOT = Path(__file__).resolve().parent.parent
# Directories the tests change in place: test_merge_rtss rewrites the RTSS in
# test/testdata, the batch tests rewrite test/batchtestdata and delete the
# tracked data/csv/dvh_data.csv and pyradiomics_data.csv.
MUTABLE_DIRS = ("test/testdata", "test/batchtestdata", "data/csv")


def restore_dir(saved, target):
    """
    Put the directory saved back at target, replacing what is there.

    The copy is made beside target first, and target is replaced only once it
    is complete, so a copy that fails or is interrupted leaves target as it
    was. On failure the error names saved, which is not removed.
    """
    saved = Path(saved)
    target = Path(target)
    staging = target.with_name(f".{target.name}.restoring")
    old = target.with_name(f".{target.name}.replaced")
    # A leftover old copy is data an earlier restore failed to put back, and
    # its error said it is there (data/csv can hold real patient identifiers).
    # Never delete it: a person decides.
    if old.exists():
        raise RuntimeError(
            f"{old} is left from an earlier restore that failed, and may be the "
            f"only copy of what was in {target}. Nothing restored; the snapshot "
            f"is kept in {saved}. Move {old} back or remove it, then run again.")
    try:
        # A leftover staging copy is only a partial copy of a snapshot.
        if staging.exists():
            shutil.rmtree(staging)
        shutil.copytree(saved, staging, symlinks=True)
        if target.exists():
            target.rename(old)
        staging.rename(target)
        if old.exists():
            shutil.rmtree(old)
    except OSError as error:
        raise RuntimeError(
            f"could not restore {target}; the snapshot is kept in {saved}"
            + (f", and the data that was there is in {old}" if old.exists() else "")
        ) from error


@pytest.fixture(scope="session", autouse=True)
def restore_mutable_dirs(tmp_path_factory):
    """
    Snapshot the directories the tests change, and put them back when the
    session ends, so a second local run starts from the same data as the
    first. A copy per test would cost ~185 MB for each of ~270 tests.
    A session that is killed restores nothing.
    """
    snapshot = tmp_path_factory.mktemp("mutable_dirs")
    saved = []
    for rel in MUTABLE_DIRS:
        target = REPO_ROOT / rel
        if target.is_symlink():
            raise RuntimeError(
                f"{target} is a symbolic link; the restore would replace "
                "what it points at. Use a real directory.")
        if target.is_dir():
            shutil.copytree(target, snapshot / rel, symlinks=True)
            saved.append(rel)
    yield
    for rel in saved:
        target = REPO_ROOT / rel
        if target.is_symlink():
            raise RuntimeError(
                f"{target} became a symbolic link during the session; "
                f"not restored. The snapshot is in {snapshot / rel}.")
        restore_dir(snapshot / rel, target)
    # data/csv/patientHash.csv can hold real identifier-to-hash pairs (Anon.py
    # appends to it), and pytest keeps old base temp directories, so no copy
    # is left behind once the restore has succeeded.
    shutil.rmtree(snapshot)


def pytest_configure(config):
    """Configure pytest with settings that may help prevent segfaults"""
    config.option.tb_locals = False  # Disable locals in tracebacks
    config.option.showlocals = False  # Disable showing locals in output


@pytest.fixture(autouse=True)
def cleanup_after_test():
    """Cleanup after each test"""
    yield
    import gc
    gc.collect()
