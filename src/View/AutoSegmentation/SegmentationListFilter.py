import pandas

from src.Controller.PathHandler import resource_path


def read_csv_to_pandas(csv: str, row_filter_column:str=None, row_filter_words: dict | list[str]=None, column_list: list[str]=None) -> pandas.DataFrame:
    """
    Imports Segments list then filters it to the specified columns then return them as a dataFrame

    :param csv: str: location of the csv file
    :param row_filter_column: str: column name to filter rows to of the csv file
    :param row_filter_words: dict: dictionary with column names as keys and values as values
    :param column_list: list[str]: list of column names
    :return: pandas.DataFrame
    """
    data: pandas.DataFrame = _read_csv_data_to_pandas(resource_path(csv))
    data: pandas.DataFrame = _strip_whitespace(data)
    data: pandas.DataFrame = _dict_row_filter(data, row_filter_column, row_filter_words)
    return _column_filter(data, column_list)

def _dict_row_filter(data: pandas.DataFrame, csv_column: str = None, filter_values: dict | list[...] = None):
    """
    Method to read filter out irrelevant rows

    :param data: pandas.DataFrame
    :param csv_column: str: column name to filter rows to of the csv file
    :param filter: dict | list[...] dictionary with column names as keys and values as values
    :return: pandas.DataFrame
    """

    if filter_values is not None and csv_column is not None:
        filter_list: dict | list[...] | None = None
        if isinstance(filter_values, dict):
            filter_list: list[str] = list(filter_values.values())
        if isinstance(filter_values, list):
            filter_list: list[str] = filter_values
        if filter_list is not None:
            return data[data[csv_column].isin(filter_list)]
    return data

def _column_filter(data: pandas.DataFrame, column_list: list[str]) -> pandas.DataFrame:
    """
    Method To filter Columns
    :param data: pandas.DataFrame
    :param *args: list[str]: list of column to filter to
    :return: pandas.DataFrame
    """
    output: pandas.DataFrame = pandas.DataFrame()
    if column_list is not None:
        for column in column_list:
            try:
                output[column]: pandas.Series = data[column]
            finally:
                pass
    return output

def _strip_whitespace(data: pandas.DataFrame) -> pandas.DataFrame:
    """
    FOr removing white space from every cell with a string
    :param data: pandas.DataFrame
    :return: pandas.DataFrame
    """
    for column in data.columns:
        if pandas.api.types.is_string_dtype(data[column]):
            data[column]: pandas.Series = data[column].str.strip()
    return data

def _read_csv_data_to_pandas(csv: str) -> pandas.DataFrame:
    """
    Cached Method to return the row filtered pandas DataFrame
    :param csv: str: location of the csv file
    :return: pandas.DataFrame
    """
    return pandas.read_csv(csv)
