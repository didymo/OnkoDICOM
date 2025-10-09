
import platform
import ctypes
import sqlite3
import os
import functools
from pathlib import Path

from src.Model.Singleton import Singleton


def set_up_hidden_dir(directory: str) -> None:
    """
    Set up the hidden directory

    :param directory: str
    :return: None
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
        except (sqlite3.Error, sqlite3.OperationalError) as e:
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
    default directory for the DICOM files, and the CSV file containing
    patient clinical data. The object will contain the
    connection to a sqlite database set below, and the user can update the
    default directory and clinical data csv during runtime. When a class needs
    to access the instance of this class, it can simply call the class's
    constructor and it will return the only instance of this class.
    Example usage:
    config = Configuration()

    This class also moves data from the data folder into files in the
    hidden folder the first time the user opens the program/the first time an
    instance of this class is created.
    """

    def __init__(self, db_file='OnkoDICOM.db'):
        self.directory: str = ".OnkoDICOM"
        set_up_hidden_dir(self.directory)
        self.db_file_path = Path(
            os.environ['USER_ONKODICOM_HIDDEN']).joinpath(db_file)
        self.set_up_config_db()
        self.copy_data_folder()

    def set_up_config_db(self):
        """
        Create the CONFIGURATION table inside the SQLite database
        """
        connection = sqlite3.connect(self.db_file_path)
        connection.execute("""
                    CREATE TABLE IF NOT EXISTS CONFIGURATION (
                        id INTEGER PRIMARY KEY,
                        default_dir TEXT,
                        csv_dir TEXT
                    );
                """)
        connection.commit()
        connection.close()

    def copy_data_folder(self):
        """
        Copies data from the data folder into files in the hidden
        directory. Done to overcome permission errors for compiled executables.
        """
        # Walk through data folder, get list of data files
        data_file_tree = []
        data_file_absolute_tree = []
        for root, dirs, files in os.walk('data', topdown=True):
            for name in files:
                data_file_tree.append(name)
                data_file_absolute_tree.append(os.path.join(root, name))

        # Walk through directory, get the list of files
        path = Path.home().joinpath(self.directory)
        if not os.path.exists(path):
            os.mkdir(path)

        hidden_folder_tree = []
        for root, dirs, files in os.walk(path, topdown=True):
            for name in files:
                hidden_folder_tree.append(name)

        # Check for each expected DB in the hidden directory. Copy it if it
        # does not exist
        for i, file in enumerate(data_file_tree):
            if file in hidden_folder_tree:
                continue
            else:
                self.copy_data_file(data_file_absolute_tree[i], file)

    def copy_data_file(self, old_file, new_file):
        """
        Copies the passed-in 'old_file' into 'new_file' in the hidden
        directory.
        :param old_file: The absolute path of the file to copy from.
        :param new_file: The file name of the file to copy to.
        """
        # Make new data folder if it does not exist
        new_data_folder = str(Path.home().joinpath(self.directory, 'data'))
        if not os.path.exists(new_data_folder):
            os.mkdir(new_data_folder)

        # Get the new path of the file
        new_path = os.path.join(new_data_folder, new_file)

        # Skip the pickle file
        # TODO: find out what this is
        if new_path[-3:] == 'pkl':
            return

        # Copy each line from the old file into the new file
        with open(old_file, "r") as old:
            with open(new_path, "w+") as new:
                for line in old:
                    new.write(line)

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

    @error_handling
    def check_csv_attribute(self, cursor):
        """
        Check for the csv_dir attribute in the SQLite table. Add it if
        it is not there. Included in case database exists, but is from
        an old version of OnkoDICOM.
        :param cursor: cursor to the SQLite database.
        """
        # Check to see if csv_dir exists
        cursor.execute("SELECT * FROM CONFIGURATION")
        attribs = list(map(lambda x: x[0], cursor.description))

        # Add the column
        if 'csv_dir' not in attribs:
            cursor.execute("ALTER TABLE CONFIGURATION ADD COLUMN csv_dir TEXT")

    @error_handling
    def get_clinical_data_csv_dir(self):
        """
        Get the clinical data CSV directory from the database.
        """
        # Connect to the database
        connection = sqlite3.connect(self.db_file_path)
        cursor = connection.cursor()

        self.check_csv_attribute(cursor)

        # Get the data
        cursor.execute("SELECT csv_dir FROM CONFIGURATION WHERE id = 1")
        record = cursor.fetchone()
        connection.close()

        # If data does not exist, return nothing
        if record is None:
            return None

        # Return the data
        return record[0]

    @error_handling
    def update_clinical_data_csv_dir(self, new_dir):
        """
        Updates the clinical data CSV import directory in the database.
        :param new_dir: the new CSV directory.
        """
        # Open database
        connection = sqlite3.connect(self.db_file_path)
        cursor = connection.cursor()

        self.check_csv_attribute(cursor)

        cursor.execute("SELECT COUNT(*) FROM CONFIGURATION;")
        result = cursor.fetchone()

        # Close the connection if no CSV dir set
        if result[0] == 0:
            # insert a new CSV dir if there is none
            cursor.execute("""INSERT INTO configuration (id, csv_dir) 
                                            VALUES (1, "%s");""" % new_dir)
        else:
            cursor.execute("""UPDATE CONFIGURATION
                                    SET csv_dir = "%s"
                                    WHERE id = 1;""" % new_dir)
        connection.commit()
        connection.close()

    def set_db_file_path(self, new_path):
        self.db_file_path = new_path
        self.set_up_config_db()
