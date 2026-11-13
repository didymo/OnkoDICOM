import os
import sqlite3
import pytest
from pathlib import Path

from src.Model.Configuration import Configuration, SqlError


@pytest.fixture(scope="function", autouse=True)
def init_sqlite_config(request):
    configuration = Configuration('TestSqliteConfig.db')
    db_file_path = Path(os.environ['USER_ONKODICOM_HIDDEN']).joinpath('TestSqliteConfig.db')
    configuration.set_db_file_path(db_file_path)
    connection = sqlite3.connect(db_file_path)

    def tear_down():
        connection.close()
        if os.path.isfile(db_file_path):
            os.remove(db_file_path)

    request.addfinalizer(tear_down)
    return connection


def test_if_config_table_exists(init_sqlite_config):
    # Select from sqlite_master the info of Configuration table
    cursor = init_sqlite_config.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name='CONFIGURATION'")
    record = cursor.fetchone()

    # Check if Configuration table exists
    assert record is not None


def test_update_default_directory(init_sqlite_config):
    configuration = Configuration()
    new_default_dir = "/home/test/dir"
    # Update default_dir with configuration object
    configuration.update_default_directory(new_default_dir)

    # Select default dir from the database
    cursor = init_sqlite_config.cursor()
    cursor.execute("SELECT default_dir FROM CONFIGURATION WHERE id = 1")
    record = cursor.fetchone()

    # Check if the value from database is equal to the one that we want to update into
    assert record[0] == new_default_dir


def test_get_default_directory(init_sqlite_config):
    configuration = Configuration()
    new_default_dir = "/home/test/dir"
    # Insert new default dir
    init_sqlite_config.execute("""INSERT INTO configuration (id, default_dir) 
                                    VALUES (1, "%s");""" % new_default_dir)
    init_sqlite_config.commit()

    # Get default dir from configuration object
    result = configuration.get_default_directory()

    # Compare the value returned from get_default_directory() and the value from database
    assert result == new_default_dir


def test_error_handling(init_sqlite_config):
    # Drop database file to reproduce SQL error
    configuration = Configuration()
    cursor = init_sqlite_config.cursor()

    # Lock the database to trigger SqlError
    cursor.execute("""PRAGMA locking_mode = EXCLUSIVE;""")
    cursor.execute("""BEGIN EXCLUSIVE;""")
    with pytest.raises(SqlError):
        configuration.get_default_directory()
    with pytest.raises(SqlError):
        configuration.update_default_directory('')


@pytest.mark.parametrize("call,args", [
    ("get_default_directory", ()),
    ("update_default_directory", ("/tmp/new_dir",)),
    ("get_clinical_data_csv_dir", ()),
    ("update_clinical_data_csv_dir", ("/tmp/csv_dir",)),
])
def test_sqlite_connections_are_closed_on_error(init_sqlite_config, monkeypatch, call, args):
    """The #19 regression: a query that raises (a locked database) must not leak
    its connection open, or Windows cannot delete the file (WinError 32). Each
    query method must close every connection it opens, even when the SQL raises.

    Every connection the code opens is tracked; a leaked one stays in
    open_connections, so the assertion fails with the fix removed — even if
    another method's or __init__'s connection closes normally."""
    import src.Model.Configuration as configuration_module

    open_connections = set()

    class TrackingConnection:
        def __init__(self, connection):
            self._connection = connection
            open_connections.add(self)

        def cursor(self):
            return self._connection.cursor()

        def execute(self, *args):
            return self._connection.execute(*args)

        def commit(self):
            return self._connection.commit()

        def close(self):
            open_connections.discard(self)
            return self._connection.close()

    real_connect = sqlite3.connect

    def tracking_connect(*args, **kwargs):
        return TrackingConnection(real_connect(*args, **kwargs))

    monkeypatch.setattr(configuration_module.sqlite3, "connect", tracking_connect)

    configuration = Configuration()
    # Configuration() itself opens and closes a connection (set_up_config_db);
    # forget it so a normally-closed __init__ connection can't satisfy the
    # assertion while a query method leaks its own.
    open_connections.clear()

    cursor = init_sqlite_config.cursor()
    cursor.execute("PRAGMA locking_mode = EXCLUSIVE;")
    cursor.execute("BEGIN EXCLUSIVE;")
    try:
        with pytest.raises(SqlError):
            getattr(configuration, call)(*args)
    finally:
        cursor.execute("ROLLBACK;")

    assert not open_connections, \
        "a connection opened by a query must be closed even when the SQL raises (WinError 32 on Windows)"

# Paths are stored as given, whatever characters they hold. Before the values were passed as
# query parameters, a '"' made the statement fail, and a crafted path set other columns.
DIRECTORY_PATHS = [
    '/home/test/Dr "Smith" patients',
    "/home/test/O'Brien",
    '/home/test/x", csv_dir = "/elsewhere',
    "/home/test/semi;colon -- dash",
    "C:\\Users\\test\\Patients",
]


@pytest.mark.parametrize("new_dir", DIRECTORY_PATHS)
@pytest.mark.parametrize("existing_row", [False, True], ids=["insert", "update"])
def test_default_directory_is_stored_as_given(init_sqlite_config, new_dir, existing_row):
    configuration = Configuration()
    if existing_row:
        configuration.update_default_directory("/home/test/first")
    configuration.update_default_directory(new_dir)

    assert configuration.get_default_directory() == new_dir
    rows = init_sqlite_config.execute("SELECT id, default_dir, csv_dir FROM CONFIGURATION").fetchall()
    assert rows == [(1, new_dir, None)]


@pytest.mark.parametrize("new_dir", DIRECTORY_PATHS)
@pytest.mark.parametrize("existing_row", [False, True], ids=["insert", "update"])
def test_clinical_data_csv_dir_is_stored_as_given(init_sqlite_config, new_dir, existing_row):
    configuration = Configuration()
    if existing_row:
        # The row exists, so update_clinical_data_csv_dir takes its UPDATE statement.
        configuration.update_default_directory("/home/test/default")
        configuration.update_clinical_data_csv_dir("/home/test/first")
    # Otherwise there is no row, so it takes its INSERT statement.
    configuration.update_clinical_data_csv_dir(new_dir)

    assert configuration.get_clinical_data_csv_dir() == new_dir
    rows = init_sqlite_config.execute("SELECT id, default_dir, csv_dir FROM CONFIGURATION").fetchall()
    expected_default = "/home/test/default" if existing_row else None
    assert rows == [(1, expected_default, new_dir)]
