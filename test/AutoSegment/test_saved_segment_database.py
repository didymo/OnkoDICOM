import pytest
from unittest.mock import patch, MagicMock, Mock
import sqlite3
import pathlib
import asyncio
from src.Model.AutoSegmentation.SavedSegmentDatabase import SavedSegmentDatabase

@pytest.fixture
def patch_db_path(tmp_path):
    # Arrange
    db_file = tmp_path / "test.db"
    with patch("src.Model.AutoSegmentation.SavedSegmentDatabase.database_path", return_value=pathlib.Path(db_file)):
        yield db_file

@pytest.fixture
def patch_text_sanitiser():
    with patch("src.Model.AutoSegmentation.SavedSegmentDatabase.text_sanitiser", side_effect=lambda x: x):
        yield

@pytest.fixture
def patch_logger():
    with patch("src.Model.AutoSegmentation.SavedSegmentDatabase.logger"):
        yield

@pytest.fixture
def patch_asyncio_run():
    with patch("src.Model.AutoSegmentation.SavedSegmentDatabase.asyncio.run") as arun:
        yield arun

def test_init_calls_create_table_and_get_save_list(patch_db_path, patch_text_sanitiser, patch_logger):
    # Arrange
    with patch.object(SavedSegmentDatabase, "_create_table", return_value=True) as create_table, \
         patch.object(SavedSegmentDatabase, "get_save_list", return_value=[]):
        # Act
        db = SavedSegmentDatabase()
        # Assert
        create_table.assert_called_once()
        db.get_save_list.assert_called_once_with("save_name")
        assert db._table_name == "AutoSegmentationSaves"
        assert db._key_column == "save_name"
        assert db._database_location == patch_db_path

def test_send_feedback_calls_callback(patch_db_path, patch_text_sanitiser, patch_logger):
    # Arrange
    feedback = Mock()
    db = SavedSegmentDatabase(feed_back=feedback)
    # Act
    db._send_feedback("msg")
    # Assert
    feedback.assert_called_with("msg")

def test_send_feedback_no_callback(patch_db_path, patch_text_sanitiser, patch_logger):
    # Arrange
    db = SavedSegmentDatabase(feed_back=None)
    # Act
    db._send_feedback("msg")
    # Assert
    # No exception, nothing to assert

def test_row_to_list_filters_key_column(patch_db_path, patch_text_sanitiser, patch_logger):
    # Arrange
    db = SavedSegmentDatabase()
    row = MagicMock()
    row.keys.return_value = ["save_name", "roi1", "roi2"]
    row.__getitem__.side_effect = lambda k: k != "save_name"
    # Act
    result = db._row_to_list(row)
    # Assert
    assert "save_name" not in result
    assert set(result) == {"roi1", "roi2"}

def test_create_connection_returns_sqlite_connection(patch_db_path, patch_text_sanitiser, patch_logger):
    # Arrange
    db = SavedSegmentDatabase()
    # Act
    conn = db._create_connection()
    # Assert
    assert isinstance(conn, sqlite3.Connection)
    conn.close()

# These tests are commented out as they cause resource warnings at the moment I don't think they will cause an issue but I want to make sure before uncommmenting

# def test_get_columns_calls_asyncio_run(patch_db_path, patch_text_sanitiser, patch_logger, patch_asyncio_run):
#     # Arrange
#     db = SavedSegmentDatabase()
#     patch_asyncio_run.return_value = ["col1", "col2"]
#     # Act
#     result = db.get_columns()
#     # Assert
#     patch_asyncio_run.assert_called()
#     assert result == ["col1", "col2"]
#
# def test_get_save_list_calls_asyncio_run(patch_db_path, patch_text_sanitiser, patch_logger, patch_asyncio_run):
#     # Arrange
#     db = SavedSegmentDatabase()
#     patch_asyncio_run.return_value = ["save1", "save2"]
#     # Act
#     result = db.get_save_list("save_name")
#     # Assert
#     patch_asyncio_run.assert_called()
#     assert result == ["save1", "save2"]
#
# def test_insert_row_calls_asyncio_run(patch_db_path, patch_text_sanitiser, patch_logger, patch_asyncio_run):
#     # Arrange
#     db = SavedSegmentDatabase()
#     patch_asyncio_run.return_value = True
#     # Act
#     result = db.insert_row("save1", ["roi1", "roi2"])
#     # Assert
#     patch_asyncio_run.assert_called()
#     assert result is True
#
# def test_select_entry_calls_asyncio_run(patch_db_path, patch_text_sanitiser, patch_logger, patch_asyncio_run):
#     # Arrange
#     db = SavedSegmentDatabase()
#     patch_asyncio_run.return_value = ["roi1", "roi2"]
#     # Act
#     result = db.select_entry("save1")
#     # Assert
#     patch_asyncio_run.assert_called()
#     assert result == ["roi1", "roi2"]
#
# def test_delete_entry_calls_asyncio_run(patch_db_path, patch_text_sanitiser, patch_logger, patch_asyncio_run):
#     # Arrange
#     db = SavedSegmentDatabase()
#     patch_asyncio_run.return_value = True
#     # Act
#     result = db.delete_entry("save1")
#     # Assert
#     patch_asyncio_run.assert_called()
#     assert result is True

@pytest.mark.parametrize(
    "statement,complete,raises,expected_result,expected_feedback,case_id",
    [
        ("VALID", True, None, True, "", "valid_statement"),
        ("INVALID", False, None, False, "Issue: Save Failed", "invalid_statement"),
        ("VALID", True, sqlite3.OperationalError, False, "Issue: Save Failed", "operational_error"),
        ("VALID", True, sqlite3.IntegrityError, False, "Issue: Save Failed", "integrity_error"),
        ("VALID", True, sqlite3.ProgrammingError, False, "Issue: Save Failed", "programming_error"),
    ],
    ids=["valid_statement", "invalid_statement", "operational_error", "integrity_error", "programming_error"]
)
def test_running_write_statement_feedback(patch_db_path, patch_text_sanitiser, patch_logger, statement, complete, raises, expected_result, expected_feedback, case_id):
    # Arrange
    db = SavedSegmentDatabase()
    with patch("src.Model.AutoSegmentation.SavedSegmentDatabase.sqlite3.complete_statement", return_value=complete), \
         patch.object(db, "_run_write_operation", side_effect=raises if raises else None), \
         patch.object(db, "_send_feedback") as feedback:
        # Act
        result = asyncio.run(db._running_write_statement(statement))
        # Assert
        assert result == expected_result
        feedback.assert_called_with(expected_feedback)

@pytest.mark.parametrize(
    "statement,complete,raises,expected_feedback,case_id",
    [
        ("VALID", True, None, "", "valid_read"),
        ("INVALID", False, None, "Invalid Statement: INVALID", "invalid_read"),
        ("VALID", True, sqlite3.OperationalError, "Issue: Read Failed", "operational_error"),
        ("VALID", True, sqlite3.IntegrityError, "Issue: Read Failed", "integrity_error"),
        ("VALID", True, sqlite3.ProgrammingError, "Issue: Read Failed", "programming_error"),
    ],
    ids=["valid_read", "invalid_read", "operational_error", "integrity_error", "programming_error"]
)
def test_running_read_statement_feedback(patch_db_path, patch_text_sanitiser, patch_logger, statement, complete, raises, expected_feedback, case_id):
    # Arrange
    db = SavedSegmentDatabase()
    with patch("src.Model.AutoSegmentation.SavedSegmentDatabase.sqlite3.complete_statement", return_value=complete), \
         patch.object(db, "_run_read_operation", side_effect=raises if raises else [[]]), \
         patch.object(db, "_send_feedback") as feedback:
        # Act
        result = asyncio.run(db._running_read_statement(statement))
        # Assert
        feedback.assert_called_with(expected_feedback)
        if not raises and complete:
            assert isinstance(result, list)
        else:
            assert result is None or result == []

def test_run_write_operation_success(patch_db_path, patch_text_sanitiser, patch_logger):
    # Arrange
    db = SavedSegmentDatabase()
    with patch.object(db, "_create_connection") as conn_patch:
        conn = MagicMock()
        conn_patch.return_value.__enter__.return_value = conn
        # Act
        asyncio.run(db._run_write_operation("INSERT INTO ..."))
        # Assert
        conn.execute.assert_called()
        conn.commit.assert_called()

def test_run_read_operation_success(patch_db_path, patch_text_sanitiser, patch_logger):
    # Arrange
    db = SavedSegmentDatabase()
    with patch.object(db, "_create_connection") as conn_patch:
        conn = MagicMock()
        conn_patch.return_value.__enter__.return_value = conn
        conn.execute.return_value.fetchall.return_value = [MagicMock()]
        # Act
        result = asyncio.run(db._run_read_operation("SELECT ..."))
        # Assert
        assert isinstance(result, list)
