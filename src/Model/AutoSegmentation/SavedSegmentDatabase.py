import logging
import asyncio
import pathlib
import random
import sqlite3
from src.Controller.PathHandler import database_path

logger = logging.getLogger(__name__)


class SavedSegmentDatabase:
    """
    Class for accessing the database table for
    AutoSegmentation GUI save options to be stored into and retrieved from
    Default Table Name if `AutoSegmentation` and the Key column is "save_name"
    """

    def __init__(self, data_store=None, table_name: str = "AutoSegmentation", key_column: str = "save_name") -> None:
        """
        Initialize the Database engine to save/get data from persistent storage
        This class is specific to the AutoSegmentation Database handling.

        :param table_name: str
        :return: None
        """
        logger.debug("Initializing SavedSegmentDatabase")
        # Members
        self.table_name: str = table_name
        self.key_column: str = key_column
        self._data_store = data_store

        # Database Column List
        self.column_list: list[str] = []

        logger.debug(
            "Setting value for self.database_location and creating Table"
        )
        self.database_location: pathlib.Path = database_path()

        self._create_table()

# Database Methods
    def get_columns(self) -> list[str]:
        """
        Initiates Async method to get column list
        :return: list[str]
        """
        return asyncio.run(self._get_columns_execution())

    def insert_row(self, values: dict) -> bool:
        """
        Initiates Async method to insert a row to the table
        :return: bool
        """
        return asyncio.run(self._insert_row_execution(values))

    def select_entry(self, save_name: str) -> list[str]:
        """
        Initiates Async method to get an entry from the table
        :return: dict[str, str | bool]
        """
        return asyncio.run(self._select_entry_execution(save_name))

# Internal use Only
    def _send_feedback(self, text: str) -> None:
        """
        Giving the new test feed back to the Controller for
        display on the GUI using Function set using
        `obj.set_feedback_callback(callback_function)`.

        :param text: str
        :return: None
        """
        logger.debug("Sending feedback {}".format(text))
        if self._data_store.data_transfer is not None:
            self._data_store.data_transfer(text)

    def _create_table(self) -> bool:
        """
        Initiates Async method to create a table
        :return: bool
        """
        return asyncio.run(self._create_table_execution(self.key_column))

    def _add_boolean_column(self, column: str) -> bool:
        """
        Initiates Async method add a boolean column to the table
        :return: bool
        """
        return asyncio.run(self._add_boolean_column_execution(column))

    def _row_to_list(self, row: sqlite3.Row) -> list[str]:
        """
        Initiates Async method to convert a sqlite3.Row to a list
        Of the column values which are true
        """
        output_list: list[str] = []
        for key in row.keys():
            if row[key] and key != self.key_column:
                output_list.append(key)
        return output_list

    # Async Methods
    async def _get_columns_execution(self) -> list[str]:
        """
        This method is to retrieve a list of column
        names from the database table

        Async Method as it may take time to process but
        may not need to be running the entire time.
        :return: list[str]
        """
        logger.debug("Getting columns names of {}".format(self.table_name))
        statement: str = "PRAGMA table_info('{}');".format(self.table_name)

        # Getting Column List
        column_info: list[sqlite3.Row] = await self._running_read_statement(statement)

        logger.debug("Converting Column names from {} to dict")
        column_list: list[str] = []
        for column in column_info:
            column_list.append(column[1])  # 1 is the column name column
        return column_list

    async def _create_table_execution(self, key_column: str) -> bool:
        """
        Creating Table in the Database with only one column for the key value.
        if the table does not exist this creates the table
        in the database with the using the string set in
        `self.table_name` as the table name set during
        initialisation with variable table_name: str.

        Async Method as it may take time to process but
        may not need to be running the entire time.
        :param key_column: str: the name of the
        :return: bool
        """
        logger.debug("Creating table {} with column {} in {}"
                     .format(self.table_name,
                             key_column,
                             self.database_location
                             )
                     )
        # Creating table statement and cleaning it
        statement: str = (
                # NOT NULL: Column to find save
                # DEFAULT NULL: So we forced to put in value
                # PRIMARY KEY: Is the main way we are finding the save
                "CREATE TABLE IF NOT EXISTS {} ({} VARCHAR(25) NOT NULL DEFAULT NULL PRIMARY KEY);"
                .format(self.table_name, key_column.strip())
                .strip()
        )

        logger.debug("Executing Create Table")
        return await self._running_write_statement(statement)

    async def _add_boolean_column_execution(self, column_name: str) -> bool:
        """
        Adding a new Boolean column to the table which
        has been created during `self._create_table(key_name)`
        The boolean column DEFAULT value is False.

        Async Method as it may take time to process
        but may not need to be running the entire time.
        :param column_name: str
        :return: bool
        """

        logger.debug("Adding column {} in {}, {}"
                     .format(column_name,
                             self.table_name,
                             self.database_location
                             )
                     )
        statement: str = (
                    # BOOLEAN: as we only need to store if it is saved
                    # NOT NULL: as it is Binary State
                    # DEFAULT FALSE: As it will always be unsaved unless it is saved
                    "ALTER TABLE {} ADD COLUMN {} BOOLEAN NOT NULL DEFAULT FALSE;"
                    .format(self.table_name, column_name.strip())
        )
        logger.debug("Executing Add Column")
        return await self._running_write_statement(statement)

    async def _extend_table(self, column_list: dict[str, str | bool]) -> bool:
        """
        Filtering Out which columns already exist in the table
        than adding all the columns which don't exist in the table to the table

        :param column_list: dict[str, str | bool]
        :return: bool
        """
        success: bool = True
        column_list: list[str] = list(column_list.keys())
        new_column_list: list[str] = []
        logger.debug("Extending table {}".format(self.table_name))
        logger.debug("Creating New Column List")
        for item in column_list:
            if item not in self.column_list:
                new_column_list.append(item)
        logger.debug("New Column List: {}".format(new_column_list))
        for new_column in new_column_list:
            if not await self._add_boolean_column_execution(new_column):
                success: bool = False
            logger.debug("New Columns added {}".format(new_column))
        self.column_list: list[str] = await self._get_columns_execution()
        return success

    async def _insert_row_execution(self, column_values: dict[str, str | bool]) -> bool:
        """
        Inserting a row into the table to be stored for future use.

        Async Method as it may take time to process but may not need to be running the entire time.
        :param column_values: dict
        :return: bool
        """
        logger.debug("Inserting Row in {}".format(self.table_name))
        if not await self._extend_table(column_values):
            logger.debug("Failed to update Table Columns for current Input")
            return False
        statement: str = (
            "INSERT INTO {} ({}) VALUES ('{}', {});"
            .format(self.table_name,
                    ", ".join(column_values.keys()),
                    column_values[self.key_column],
                    ", ".join("{}".format(value)
                              for key, value
                              in column_values.items()
                              if key != self.key_column)
                    )
        )
        logger.debug(statement)
        logger.debug("Executing Insert Row")
        return await self._running_write_statement(statement)

    async def _select_entry_execution(self, save_name: str) -> list[str]:
        """
        Selecting a Specific Entry from the Table.
        This will be a dict which contains with the column name as the key and the
        values as string for the save_name and the Boolean for each option

        :param save_name: str
        :return: dict
        """
        logger.debug("Selecting entry in {}".format(self.table_name))
        statement: str = (
            "SELECT * FROM {} WHERE save_name='{}';"
            .format(self.table_name.strip(), save_name.strip())
        )
        logger.debug(statement)
        logger.debug("Executing Select")
        # to keep the select generalized returning a list of objects is preferable even though
        # it is only ever going to have one
        column_values: list[sqlite3.Row] = await self._running_read_statement(statement)
        column_values: sqlite3.Row = column_values[0] # to dereference out of the array
        column_list: list[str] = self._row_to_list(column_values)

        logger.debug("Select Dict: {}".format(column_list))
        return column_list

    def _create_connection(self) -> sqlite3.Connection:
        """
        Creating the engine which we use to connect to the database to make changes using member
        from `self.database_location`.

        :return: sqlite3.Connection
        """
        logger.debug(f"Creating connection from {self.database_location}")
        return sqlite3.connect(self.database_location, detect_types=sqlite3.PARSE_COLNAMES)

    # Writing to Table
    async def _running_write_statement(self, statement: str) -> bool:
        """
        Making Changes the Database to allow updates such as
        adding tables, column, rows, and
        updating rows.
        This function primarily deals with checking
        if the statement is a valid statement and
        dealing with exceptions raised from the
        attempt at writing to the database table.

        Async Method as it may take time to process but
        may not need to be running the entire time.
        :param statement: str
        :return: bool
        """
        # statement = text_sanitiser(statement).strip().join(";")
        result = False
        if sqlite3.complete_statement(statement):  # Ensuring the statement is a complete statement
            logger.debug("Executing Statement: {}".format(statement))
            try:
                await self._run_write_operation(statement)
                feedback = "Data Written to Database"
                result = True
            except sqlite3.OperationalError:
                feedback = "Operational Error: Transaction not processed."
                logger.debug(feedback)
            except sqlite3.IntegrityError:
                feedback = "Integrity Error: Constraint Error"
                logger.debug(feedback)
            except sqlite3.ProgrammingError:
                feedback = "Programming Error: Check Connection and number of inputs"
                logger.debug(feedback)
        else:
            feedback = "Invalid Statement: {}".format(statement)
            logger.debug(feedback)
        self._send_feedback(feedback)
        return result

    async def _run_write_operation(self,
                                   statement: str,
                                   max_attempts: int = 3,
                                   min_retry_interval: float = 1.0,
                                   max_retry_interval: float = 5.0) -> None:
        """
        Method the attempts to write to the
        database with the given statement.
        This method if an attempt results in a
        sqlite3.OperationalError then method will reattempt
        the transaction a number of times (max_attempts)
        with wait interval of a random number seconds
        within the interval min_retry_interval and max_retry_interval.

        Async Method as it may take time to process but
        may not need to be running the entire time.
        :param statement: str
        :param max_attempts: int
        :param min_retry_interval: float
        :param max_retry_interval: float
        :return: None
        :raises: Exception
        """
        for attempt in range(max_attempts):
            logger.debug("Operational Error: Attempting Retry. Attempt #{}".format(attempt))
            try:
                with self._create_connection() as connection:
                    connection.execute(statement)
                    connection.commit()
                    return
            except Exception as transaction_issue:
                if (transaction_issue.args[0] == sqlite3.OperationalError
                        and attempt < max_attempts):
                    output = ("Operational Error on Write: Attempting Retry. Attempt #{}"
                              .format(attempt+1))
                    logger.debug(output)
                    self._send_feedback(output)
                    await asyncio.sleep(random.uniform(min_retry_interval, max_retry_interval))
                else:
                    raise transaction_issue

    # Reading From Table
    async def _running_read_statement(self, statement: str) -> list[sqlite3.Row]:
        """
        Fetching information from the Database Table
        This function primarily deals with checking
        if the statement is a valid statement and
        dealing with exceptions raised from the
        attempt at writing to the database table.

        Async Method as it may take time to process but
        may not need to be running the entire time.
        :param statement: str
        :return: list[sqlite3.Row]
        """
        # statement = text_sanitiser(statement).strip().join(";")
        # assigning list to be returned; if list cannot retrieve list
        results: list[sqlite3.Row] | None = None  # assigning list to be returned; if list cannot retrieve list
        if sqlite3.complete_statement(statement):  # Ensuring the statement is a complete statement
            logger.debug("Executing Statement: {}".format(statement))
            try:
                results: list[sqlite3.Row] = await self._run_read_operation(statement)
                feedback = "Data Read from Database"
            except sqlite3.OperationalError:
                feedback = "Operational Error: Transaction not processed."
                logger.debug(feedback)
            except sqlite3.IntegrityError:
                feedback = "Integrity Error: Constraint Error"
                logger.debug(feedback)
            except sqlite3.ProgrammingError:
                feedback = "Programming Error: Check Connection and number of inputs"
                logger.debug(feedback)
        else:
            logger.debug("Invalid Statement: {}".format(statement))
            feedback = "Invalid Statement: {}".format(statement)
        self._send_feedback(feedback)
        return results

    async def _run_read_operation(self,
                                  statement: str,
                                  max_attempts: int = 3,
                                  min_retry_interval: float = 1.0,
                                  max_retry_interval: float = 5.0) -> list[sqlite3.Row]:
        """
        Method the attempts to read from the
        database with the given statement.
        This method if an attempt results in
        a sqlite3.OperationalError then method will reattempt
        the transaction a number of times (max_attempts)
        with wait interval of a random number seconds
        within the interval min_retry_interval and max_retry_interval.

        Async Method as it may take time to process but
        may not need to be running the entire time.
        :param statement: str
        :param max_attempts: int
        :param min_retry_interval: float
        :param max_retry_interval: float
        :return: list[sqlite3.Row]
        :raises: Exception
        """
        results: list[sqlite3.Row] = []  # Empty List to show nothing was retrieved
        for attempt in range(max_attempts):
            logger.debug("Operational Error: Attempting Retry. Attempt #{}".format(attempt))
            try:
                with self._create_connection() as connection:
                    connection.row_factory = sqlite3.Row
                    results : list[sqlite3.Row] = connection.execute(statement).fetchall()
            except Exception as transaction_issue:
                if (transaction_issue.args[0] == sqlite3.OperationalError
                        and attempt < max_attempts):
                    output = ("Operational Error on Read: Attempting Retry. Attempt #{}"
                              .format(attempt + 1))
                    logger.debug(output)
                    self._send_feedback(output)
                    await asyncio.sleep(random.uniform(min_retry_interval, max_retry_interval))
                else:
                    raise transaction_issue
        return results
