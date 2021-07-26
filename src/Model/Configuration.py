
import platform
import ctypes
import sqlite3
import os
import functools
from pathlib import Path

from src.Model.Singleton import Singleton


def set_up_hidden_dir():
    """
    Set up the hidden directory
    """
    path = Path.home().joinpath('.OnkoDICOM')
    os.environ['USER_ONKODICOM_HIDDEN'] = str(path)

    # Create and hide the hidden directory
    if not os.path.exists(path):
        os.mkdir(path)
        if platform.system() == 'Windows':
            # Hide the directory for Windows machines
            ctypes.windll.kernel32.SetFileAttributesW(path, 2)


class SqlError(Exception):
    pass


def error_handling(function):
    @functools.wraps(function)
    def wrapper(*args):
        try:
            result = function(*args)
            return result
        except (sqlite3.Error, sqlite3.OperationalError):
            try:
                if os.path.exists(os.environ['USER_ONKODICOM_HIDDEN']):
                    os.remove(os.environ['USER_ONKODICOM_HIDDEN'])
                set_up_hidden_dir()
                raise SqlError()
            except OSError:
                raise SqlError()
    return wrapper


class Configuration(metaclass=Singleton):
    """
    This Singleton class represents the user configuration. It contains the
    default directory for the DICOM files. The object will contain the
    connection to a sqlite database set below, and the user can update the
    default directory during runtime. When a class needs to access the
    instance of this class, it can simply call the class's constructor and
    it will return the only instance of this class.
    Example usage: config = Configuration()
    """

    def __init__(self, db_file='OnkoDICOM.db'):
        set_up_hidden_dir()
        self.db_file_path = Path(
            os.environ['USER_ONKODICOM_HIDDEN']).joinpath(db_file)
        self.set_up_config_db()

    def set_up_config_db(self):
        """
        Create the CONFIGURATION table inside the SQLite database
        """
        connection = sqlite3.connect(self.db_file_path)
        connection.execute("""
                    CREATE TABLE IF NOT EXISTS CONFIGURATION (
                        id INTEGER PRIMARY KEY,
                        default_dir TEXT
                    );
                """)
        connection.commit()
        connection.close()

    @error_handling
    def get_default_directory(self):
        """
        Get the default directory's path from the database
        """
        connection = sqlite3.connect(self.db_file_path)
        cursor = connection.cursor()
        cursor.execute("SELECT default_dir FROM CONFIGURATION WHERE id = 1")
        record = cursor.fetchone()
        connection.close()
        if record is None:
            # no directory has been set as the default directory
            return None
        return record[0]

    @error_handling
    def update_default_directory(self, new_dir):
        """
        Change the default directory's path in the database
        """
        connection = sqlite3.connect(self.db_file_path)
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM CONFIGURATION;")
        result = cursor.fetchone()
        if result[0] == 0:
            # insert a new default directory if there is none
            connection.execute("""INSERT INTO configuration (id, default_dir) 
                                VALUES (1, "%s");""" % new_dir)
        else:
            connection.execute("""UPDATE CONFIGURATION
                            SET default_dir = "%s"
                            WHERE id = 1;""" % new_dir)
        connection.commit()
        connection.close()

    def set_db_file_path(self, new_path):
        self.db_file_path = new_path
        self.set_up_config_db()
