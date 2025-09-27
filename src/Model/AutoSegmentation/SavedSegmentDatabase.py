import logging
import pathlib
import sqlite3

from src.Controller.PathHandler import path_sanitizer, text_sanitiser

# from src.Controller.PathHandler import path_sanitizer
logger = logging.getLogger(__name__)

class SavedSegmentDatabase:
    def __init__(self, table_name: str) -> None:
        """
        Initialize the Database engine to save/get data from persistent storage
        This class is specific to the AutoSegmentation Database handling

        :param table_name: str
        :return: None
        """
        logger.debug("Initializing SavedSegmentDatabase")
        self.table_name = table_name
        # Location of the database being accessed
        # self.database_location: pathlib.Path = path_sanitizer(pathlib.Path.home().joinpath('.OnkoDICOM', self.database_name()))
        self.database_location: pathlib.Path = path_sanitizer(self.database_name())
        self._create_table("save_name")
        self._get_columns()
        # self._create_table("save_name")
        # self._add_column("heart")

    def database_name(self) -> str:
        """
        For child classes to overwrite and change the name of the database for other table implementations
        This is basically single use so this also ensures the smallest possible lifetime.
        As all it needs to do is get pulled in to the creation of the database location.

        :return: name
        """
        logger.debug("Setting database name")
        return "OnkoDICOMtest1.db"

    def _create_connection(self) -> sqlite3.Connection:
        """
        Creating the engine which we use to connect to the database to make changes
        """
        logger.debug(f"Creating connection from {self.database_location}")
        return sqlite3.connect(self.database_location, detect_types=sqlite3.PARSE_COLNAMES)

    def _running_statement(self, statement: str) -> bool:
        """

        """
        # statement = text_sanitiser(statement).strip().join(";")
        if sqlite3.complete_statement(statement): # Ensuring the statement is a complete statement
            logger.debug("Executing Statement: {}".format(statement))
            try:
                with self._create_connection() as connection:
                    connection.execute(statement)
                    connection.commit()
                    return True
            except sqlite3.OperationalError:
               logger.error("Operational Error: Transaction not processed. Try again ")
               return False
            except sqlite3.IntegrityError:
                logger.error("Integrity Error: Constraint Error")
                return False
            except sqlite3.ProgrammingError:
                logger.error("Programming Error: Check Connection and number of inputs")
                return False
        else:
            logger.debug("Invalid Statement: {}".format(statement))
            print("Fail")
            raise sqlite3.ProgrammingError("Invalid Statement: {}".format(statement))

    def _get_columns(self):
        """

        """
        statement = "PRAGMA table_info('{}')".format(self.table_name)
        with self._create_connection() as connection:
            column_info = connection.execute(statement).fetchall()
        columns = []
        for column in column_info:
            columns.append(column[1])
        print(columns.sort())

    def _create_table(self, first_column: str) -> None:
        """
        Creating Table in the Database if one does not exist

        :param first_column: str

        :return: None
        """
        logger.debug("Creating table {} with column {} in {}".format(self.table_name, first_column, self.database_location))
        # Creating table statement and cleaning it
        statement = (
                "CREATE TABLE IF NOT EXISTS {} ({});"
                .format(self.table_name, first_column.strip())
                .strip()
        )

        logger.debug("Executing Create Table")
        self._running_statement(statement)

    def _add_column(self, column_name: str):
        """
        """
        logger.debug("Adding column {} in {}, {}".format(column_name, self.table_name, self.database_location))
        statement = (
                    "ALTER TABLE {} ADD COLUMN {} BOOL NOT NULL DEFAULT FALSE;"
                    .format(self.table_name, column_name.strip())
        )
        logger.debug("Executing Add Column")
        self._running_statement(statement)

    def insert_Row(self, column_values: dict) -> None:
        logger.debug("Inserting Row in {}".format(self.table_name))
        statement = (
            "INSERT INTO {} ({}) VALUES ({});"
            .format(self.table_name,
                    ", ".join(column_values.keys()),
                    ", ".join(column_values.values())
                    )
        )
        logger.debug("Executing Insert Row")
        self._running_statement(statement)

    def select_entry(self, save_name: str) -> dict:
        logger.debug("Selecting entry in {}".format(self.table_name))
        statement  = (
            "SELECT * FROM {} WHERE save_name={};"
            .format(self.table_name.strip(), save_name.strip())
        )
        column_values = self._running_statement(statement)
        result = self._running_statement(statement)
        output = {}
        return output


if __name__ == '__main__':
    database_engine = "Onko"
    SavedSegmentDatabase("segmentation_save")