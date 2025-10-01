import copy
import logging
import asyncio
import pathlib
import random
import sqlite3
from collections.abc import Callable

from src.Controller.PathHandler import database_path, text_sanitiser

logger = logging.getLogger(__name__)


class SavedSegmentDatabase:
    """
    Class for accessing the database table for
    AutoSegmentation GUI save options to be stored into and retrieved from
    Default Table Name if `AutoSegmentation` and the Key column is "save_name"
    """

    def __init__(self,
                 table_name: str = "AutoSegmentationSaves",
                 key_column: str = "save_name",
                 feed_back: Callable[[str], None] = None,
                 max_retry: int = 3,
                 min_retry_interval: float = 1.0,
                 max_retry_interval: float = 5.0
                 ) -> None:
        """
        Initialize the Database engine to save/get data from persistent storage
        This class is specific to the AutoSegmentation Database handling.

        :param table_name: str
        :param key_column: str
        :param feed_back: Callable[[str], None]
        :param max_retry: int
        :param min_retry_interval: float
        :param max_retry_interval: float
        :return: None
        """
        logger.debug("Initializing SavedSegmentDatabase")
        # Ensuring all inputs are with in the set [. _0-9a-zA-Z]
        table_name: str = text_sanitiser(table_name)
        key_column: str = text_sanitiser(key_column)

        # Members
        self._table_name: str = table_name
        self._key_column: str = key_column
        self._feedback: Callable[[str], None] = feed_back
        self._max_attempts: int = max_retry
        self._min_retry_interval: float = min_retry_interval
        self._max_retry_interval: float = max_retry_interval

        # Database Column List
        self._column_list: list[str] = []

        logger.debug(
            "Setting value for self.database_location and creating Table"
        )
        self._database_location: pathlib.Path = database_path()

        self._create_table()
        self.get_save_list(key_column)

# Database Methods
    def get_columns(self) -> list[str]:
        """
        Initiates Async method to get column list

        :return: list[str]
        """
        return asyncio.run(self._get_columns_execution())

    def get_save_list(self, save_column: str = None) -> list[str]:
        """
        Gets the list of save names stored in the database this will be the key column of that table

        :return: list[str]
        """
        if save_column is None:
            save_column: str = self._key_column
        save_column: str = text_sanitiser(save_column)
        return asyncio.run(self._get_column_execution(save_column))

    def insert_row(self, save_name: str, values: list[str]) -> bool:
        """
        Initiates Async method to insert a row to the table

        :return: bool
        """
        # Ensuring all inputs are with in the set [. _0-9a-zA-Z]
        save_name: str = text_sanitiser(save_name)
        return asyncio.run(self._insert_row_execution(save_name , copy.deepcopy(values)))

    def select_entry(self, save_name: str) -> list[str]:
        """
        Initiates Async method to get an entry from the table

        :param save_name: str
        :return: dict[str, str | bool]
        """
        # Ensuring all inputs are with in the set [. _0-9a-zA-Z]
        save_name: str = text_sanitiser(save_name)
        return asyncio.run(self._select_entry_execution(copy.deepcopy(save_name)))

    def delete_entry(self, save_name: str) -> bool:
        """
        Initiates Async method to delete an entry from the table

        :param save_name: str
        :return: None
        """
        # Ensuring all inputs are with in the set [. _0-9a-zA-Z]
        save_name: str = text_sanitiser(save_name)
        return asyncio.run(self._delete_entry_execution(copy.deepcopy(save_name)))

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
        if self._feedback is not None:
            self._feedback(text)

    def _create_table(self) -> bool:
        """
        Initiates Async method to create a table

        :return: bool
        """
        return asyncio.run(self._create_table_execution())

    def _add_boolean_column(self, column: str) -> bool:
        """
        Initiates Async method add a boolean column to the table

        :param column: str
        :return: bool
        """
        return asyncio.run(self._add_boolean_column_execution(column))

    def _row_to_list(self, row: sqlite3.Row) -> list[str]:
        """
        Initiates Async method to convert a sqlite3.Row to a list
        Of the column values which are true

        :param row: sqlite3.Row
        :return: list[str]
        """
        output_list: list[str] = []
        for key in row.keys():
            if row[key] and key != self._key_column:
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
        logger.debug("Getting columns names of {}".format(self._table_name))
        statement: str = "PRAGMA table_info('{}');".format(self._table_name)

        # Getting Column List
        column_info: list[sqlite3.Row] = await self._running_read_statement(statement, map_obj=True)

        logger.debug("Converting Column names from {} to dict")
        column_list: list[str] = []
        for column in column_info:
            column_list.append(column[1])  # 1 is the column name column
        return column_list

    async def _get_column_execution(self, column_name: str) -> list[str]:
        """
        Getting a list of values from the specified column will default to the self._key_column of non specified

        :param column_name: str
        :return: list[str]
        """
        logger.debug("Getting columns values of {} from {}".format(column_name, self._table_name))
        statement: str = "SELECT {} FROM {};".format(column_name, self._table_name)
        values = await self._running_read_statement(statement)

        logger.debug("Converting Column values from list[tuple[str]] to list[str]")
        save_list: list[str] = []
        for value in values:
            save_list.append(value[0])
        return save_list

    async def _create_table_execution(self) -> bool:
        """
        Creating Table in the Database with only one column for the key value.
        if the table does not exist this creates the table
        in the database with the using the string set in
        `self.table_name` as the table name set during
        initialisation with variable table_name: str.

        Async Method as it may take time to process but
        may not need to be running the entire time.
        :return: bool
        """
        logger.debug("Creating table {} with column {} in {}"
                     .format(self._table_name,
                             self._key_column,
                             self._database_location
                             )
                     )
        # Creating table statement and cleaning it
        statement: str = (
                # NOT NULL: Column to find save
                # DEFAULT NULL: So we forced to put in value
                # PRIMARY KEY: Is the main way we are finding the save
                "CREATE TABLE IF NOT EXISTS {} ({} VARCHAR(25) NOT NULL DEFAULT NULL PRIMARY KEY);"
                .format(self._table_name, self._key_column.strip())
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
                             self._table_name,
                             self._database_location
                             )
                     )
        statement: str = (
                    # BOOLEAN: as we only need to store if it is saved
                    # NOT NULL: as it is Binary State
                    # DEFAULT FALSE: As it will always be unsaved unless it is saved
                    "ALTER TABLE {} ADD COLUMN {} BOOLEAN NOT NULL DEFAULT FALSE;"
                    .format(self._table_name, column_name.strip())
        )
        logger.debug("Executing Add Column")
        return await self._running_write_statement(statement)

    async def _extend_table(self, column_list: list[str]) -> bool:
        """
        Filtering Out which columns already exist in the table
        than adding all the columns which don't exist in the table to the table

        Async Method as it may take time to process but
        may not need to be running the entire time.
        :param column_list: dict[str, str | bool]
        :return: bool
        """
        success: bool = True
        new_column_list: list[str] = []
        logger.debug("Extending table {}".format(self._table_name))
        logger.debug("Creating New Column List")
        for item in column_list:
            if item not in self._column_list:
                new_column_list.append(item)
        logger.debug("New Column List: {}".format(new_column_list))
        for new_column in new_column_list:
            if not await self._add_boolean_column_execution(new_column):
                success: bool = False
            logger.debug("New Columns added {}".format(new_column))
        self.column_list: list[str] = await self._get_columns_execution()
        return success

    async def _insert_row_execution(self, save_name: str, column_values: list[str]) -> bool:
        """
        Inserting a row into the table to be stored for future use.

        Async Method as it may take time to process but
        may not need to be running the entire time.
        :param column_values: dict
        :return: bool
        """
        logger.debug("Inserting Row in {}".format(self._table_name))
        if not await self._extend_table(column_values):
            logger.debug("Failed to update Table Columns for current Input")
        statement: str = (
            "INSERT INTO {} ({}, {}) VALUES ('{}', {});"
            .format(self._table_name,
                    self._key_column,
                    ", ".join(item for item in column_values),
                    save_name,
                    ", ".join("{}".format(True) for _ in column_values)
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

        Async Method as it may take time to process but
        may not need to be running the entire time.
        :param save_name: str
        :return: dict
        """
        logger.debug("Selecting entry in {}".format(self._table_name))
        statement: str = (
            "SELECT * FROM {} WHERE save_name='{}';"
            .format(self._table_name.strip(), save_name)
        )
        logger.debug(statement)
        logger.debug("Executing Select")
        # to keep the select generalized returning a list of objects is preferable even though
        # it is only ever going to have one
        column_values: list[sqlite3.Row] = await self._running_read_statement(statement, map_obj=True)
        column_values: sqlite3.Row = column_values[0] # to dereference out of the array
        column_list: list[str] = self._row_to_list(column_values)

        logger.debug("Select Dict: {}".format(column_list))
        return column_list

    async def _delete_entry_execution(self, save_name: str) -> bool:
        """
        Deleting a Specific Entry from the Table.

        Async Method as it may take time to process but
        may not need to be running the entire time.

        :param save_name: str
        :return: bool
        """
        logger.debug("Deleting entry in {}".format(self._table_name))

        statement: str = (
            "DELETE FROM {} WHERE save_name='{}';"
            .format(self._table_name, save_name)
        )
        logger.debug("Executing Delete Column")
        return await self._running_write_statement(statement)

    def _create_connection(self) -> sqlite3.Connection:
        """
        Creating the engine which we use to connect to the database to make changes using member
        from `self.database_location`.

        Async Method as it may take time to process but
        may not need to be running the entire time.
        :return: sqlite3.Connection
        """
        logger.debug(f"Creating connection from {self._database_location}")
        return sqlite3.connect(self._database_location, detect_types=sqlite3.PARSE_COLNAMES)

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
                feedback = ""
                result = True
            except sqlite3.OperationalError:
                feedback = "Issue: Save Failed"
                logger.debug("Operational Error: Transaction not processed.")
            except sqlite3.IntegrityError:
                feedback = "Issue: Save Failed"
                logger.debug("Integrity Error: Constraint Error")
            except sqlite3.ProgrammingError:
                feedback = "Issue: Save Failed"
                logger.debug("Programming Error: Check Connection and number of inputs")
        else:
            feedback = "Issue: Save Failed"
            logger.debug(feedback)
        self._send_feedback(feedback)
        return result

    async def _run_write_operation(self, statement: str) -> None:
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
        :return: None
        :raises: Exception
        """
        for attempt in range(self._max_attempts):
            logger.debug("Attempting to Write to Database")
            try:
                with self._create_connection() as connection:
                    connection.execute(statement)
                    connection.commit()
                    return
            except Exception as transaction_issue:
                if (transaction_issue.args[0] == sqlite3.OperationalError
                        and attempt < self._max_attempts):
                    output = ("Write Error: Attempt #{}"
                              .format(attempt+1))
                    logger.debug(output)
                    self._send_feedback(output)
                    await asyncio.sleep(random.uniform(self._min_retry_interval, self._max_retry_interval))
                else:
                    raise transaction_issue

    # Reading From Table
    async def _running_read_statement(self, statement: str , map_obj:bool = True) -> list[sqlite3.Row] | tuple:
        """
        Fetching information from the Database Table
        This function primarily deals with checking
        if the statement is a valid statement and
        dealing with exceptions raised from the
        attempt at writing to the database table.

        Async Method as it may take time to process but
        may not need to be running the entire time.
        :param statement: str
        :param map_obj: bool
        :return: list[sqlite3.Row] | tuple
        """
        # statement = text_sanitiser(statement).strip().join(";")
        # assigning list to be returned; if list cannot retrieve list
        results: list[sqlite3.Row] | tuple | None = None  # assigning list to be returned; if list cannot retrieve list
        if sqlite3.complete_statement(statement):  # Ensuring the statement is a complete statement
            logger.debug("Executing Statement: {}".format(statement))
            try:
                results: list[sqlite3.Row] | tuple = await self._run_read_operation(statement, map_obj)
                feedback = ""
            except sqlite3.OperationalError:
                feedback = "Issue: Read Failed"
                logger.debug("Operational Error: Transaction not processed.")
            except sqlite3.IntegrityError:
                feedback = "Issue: Read Failed"
                logger.debug("Operational Error: Transaction not processed.")
            except sqlite3.ProgrammingError:
                feedback = "Issue: Read Failed"
                logger.debug("Operational Error: Transaction not processed.")
        else:
            logger.debug("Invalid Statement: {}".format(statement))
            feedback = "Invalid Statement: {}".format(statement)
        self._send_feedback(feedback)
        return results

    async def _run_read_operation(self, statement: str, map_obj: bool = True) -> list[sqlite3.Row] | tuple:
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
        :param map_obj: bool
        :return: list[sqlite3.Row] | tuple
        :raises: Exception
        """
        results: list[sqlite3.Row] = []  # Empty List to show nothing was retrieved
        for attempt in range(self._max_attempts):
            logger.debug("Attempting to Read from Database")
            try:
                with self._create_connection() as connection:
                    if map_obj:
                        connection.row_factory = sqlite3.Row
                    results: list[sqlite3.Row] | tuple = connection.execute(statement).fetchall()
            except Exception as transaction_issue:
                if (transaction_issue.args[0] == sqlite3.OperationalError
                        and attempt < self._max_attempts):
                    output = ("Read Error: Attempt #{}"
                              .format(attempt + 1))
                    logger.debug(output)
                    self._send_feedback(output)
                    await asyncio.sleep(random.uniform(self._min_retry_interval, self._max_retry_interval))
                else:
                    raise transaction_issue
        return results
