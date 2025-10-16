import pytest
import pandas as pd
from unittest.mock import patch

from src.Model.AutoSegmentation.SegmentationListFilter import read_csv_to_pandas

@pytest.mark.parametrize(
    "csv_data, row_filter_column, row_filter_words, column_list, expected_df, test_id",
    [
        # Happy path: filter by column, dict filter, and select columns
        (
            pd.DataFrame({
                "A": ["x", "y", "z"],
                "B": ["foo", "bar", "baz"],
                "C": ["1", "2", "3"]
            }),
            "A",
            {"A": "x"},
            ["B", "C"],
            pd.DataFrame({"B": ["foo"], "C": ["1"]}),
            "happy_path_dict_filter"
        ),
        # Happy path: filter by column, list filter, and select columns
        (
            pd.DataFrame({
                "A": ["x", "y", "z"],
                "B": ["foo", "bar", "baz"],
                "C": ["1", "2", "3"]
            }),
            "A",
            ["y", "z"],
            ["A", "B"],
            pd.DataFrame({"A": ["y", "z"], "B": ["bar", "baz"]}),
            "happy_path_list_filter"
        ),
        # Edge case: no filter, select all columns
        (
            pd.DataFrame({
                "A": ["x", "y"],
                "B": ["foo", "bar"]
            }),
            None,
            None,
            None,
            pd.DataFrame({"A": ["x", "y"], "B": ["foo", "bar"]}),
            "edge_no_filter_all_columns"
        ),
        # Edge case: filter column but filter values is empty list
        (
            pd.DataFrame({
                "A": ["x", "y"],
                "B": ["foo", "bar"]
            }),
            "A",
            [],
            ["A", "B"],
            pd.DataFrame({
                "A": ["x", "y"],
                "B": ["foo", "bar"]
            }),
            "edge_empty_list_filter"
        ),
        # Edge case: filter column but filter values is None
        (
            pd.DataFrame({
                "A": ["x", "y"],
                "B": ["foo", "bar"]
            }),
            "A",
            None,
            ["A", "B"],
            pd.DataFrame({"A": ["x", "y"], "B": ["foo", "bar"]}),
            "edge_none_filter"
        ),
        # Edge case: column_list contains non-existent column
        (
            pd.DataFrame({
                "A": ["x", "y"],
                "B": ["foo", "bar"]
            }),
            None,
            None,
            ["A", "C"],
            pd.DataFrame({"A": ["x", "y"]}),
            "edge_nonexistent_column"
        ),
        # Edge case: all whitespace in string columns
        (
            pd.DataFrame({
                "A": [" x ", " y "],
                "B": [" foo ", " bar "]
            }),
            None,
            None,
            ["A", "B"],
            pd.DataFrame({"A": ["x", "y"], "B": ["foo", "bar"]}),
            "edge_whitespace"
        ),
        # Edge case: empty DataFrame
        (
            pd.DataFrame(columns=["A", "B"]),
            None,
            None,
            ["A", "B"],
            pd.DataFrame(columns=["A", "B"]),
            "edge_empty_dataframe"
        ),
    ],
    ids=[
        "happy_path_dict_filter",
        "happy_path_list_filter",
        "edge_no_filter_all_columns",
        "edge_empty_list_filter",
        "edge_none_filter",
        "edge_nonexistent_column",
        "edge_whitespace",
        "edge_empty_dataframe"
    ]
)
def test_read_csv_to_pandas_various_cases(csv_data, row_filter_column, row_filter_words, column_list, expected_df, test_id):
    # Arrange
    with patch("src.Model.AutoSegmentation.SegmentationListFilter.resource_path", side_effect=lambda x: x), \
         patch("src.Model.AutoSegmentation.SegmentationListFilter._read_csv_data_to_pandas", return_value=csv_data):

        # Act
        result = read_csv_to_pandas("fake.csv", row_filter_column, row_filter_words, column_list)

        # Assert
        pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_df.reset_index(drop=True))

def test_read_csv_to_pandas_file_not_found():
    # Arrange
    with patch("src.Model.AutoSegmentation.SegmentationListFilter.resource_path", side_effect=lambda x: x), \
         patch("src.Model.AutoSegmentation.SegmentationListFilter._read_csv_data_to_pandas", side_effect=FileNotFoundError("not found")):

        # Act & Assert
        with pytest.raises(FileNotFoundError):
            read_csv_to_pandas("notfound.csv")

def test_read_csv_to_pandas_column_list_none_and_empty():
    # Arrange
    df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
    with patch("src.Model.AutoSegmentation.SegmentationListFilter.resource_path", side_effect=lambda x: x), \
         patch("src.Model.AutoSegmentation.SegmentationListFilter._read_csv_data_to_pandas", return_value=df):

        # Act
        result = read_csv_to_pandas("fake.csv", column_list=None)

        # Assert
        pd.testing.assert_frame_equal(result, df)
