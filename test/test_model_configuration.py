import os
import sqlite3
import pytest

from src.Model.Configuration import Configuration, SqlError


@pytest.fixture(scope="function", autouse=True)
def init_config(request):
    configuration = Configuration('TestConfig.db')
    db_file_path = os.environ['USER_HIDDEN'] + 'TestConfig.db'
    configuration.set_db_file_path(db_file_path)
    connection = sqlite3.connect(db_file_path)

    def tear_down():
        connection.close()
        os.remove(db_file_path)

    request.addfinalizer(tear_down)
    return connection


def test_if_config_table_exists(init_config):
    # Select from sqlite_master the info of Configuration table
    cursor = init_config.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type = 'table' AND name='CONFIGURATION'")
    record = cursor.fetchone()

    # Check if Configuration table exists
    assert record is not None


def test_update_default_directory(init_config):
    configuration = Configuration()
    new_default_dir = "/home/test/dir"
    # Update default_dir with configuration object
    configuration.update_default_directory(new_default_dir)

    # Select default dir from the database
    cursor = init_config.cursor()
    cursor.execute("SELECT default_dir FROM CONFIGURATION WHERE id = 1")
    record = cursor.fetchone()

    # Check if the value from database is equal to the one that we want to update into
    assert record[0] == new_default_dir


def test_get_default_directory(init_config):
    configuration = Configuration()
    new_default_dir = "/home/test/dir"
    # Insert new default dir
    init_config.execute("""INSERT INTO configuration (id, default_dir) 
                                    VALUES (1, "%s");""" % new_default_dir)
    init_config.commit()

    # Get default dir from configuration object
    result = configuration.get_default_directory()

    # Compare the value returned from get_default_directory() and the value from database
    assert result == new_default_dir


def test_error_handling(init_config):
    # Drop database file to reproduce SQL error
    configuration = Configuration()
    cursor = init_config.cursor()

    # Lock the database to trigger SqlError
    cursor.execute("""PRAGMA locking_mode = EXCLUSIVE;""")
    cursor.execute("""BEGIN EXCLUSIVE;""")
    with pytest.raises(SqlError):
        configuration.get_default_directory()
    with pytest.raises(SqlError):
        configuration.update_default_directory('')