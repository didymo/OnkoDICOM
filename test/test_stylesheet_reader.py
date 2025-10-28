import pytest
from unittest.mock import patch

from src.Model.Singleton import Singleton
from src.View.StyleSheetReader import get_stylesheet, StyleSheetReader

@pytest.mark.parametrize(
    "mock_stylesheet,expected",
    [
        ("body { background: #fff; }", "body { background: #fff; }"),
        ("QLabel { color: red; }", "QLabel { color: red; }"),
        ("", ""),  # Edge case: empty stylesheet
    ],
    ids=[
        "happy_path_simple_css",
        "happy_path_label_css",
        "edge_case_empty_stylesheet",
    ]
)
def test_get_stylesheet_happy_and_edge_cases(mock_stylesheet, expected):
    Singleton._instances = {}
    # Arrange
    with patch.object(StyleSheetReader, "get_stylesheet", return_value=mock_stylesheet):

        # Act
        result = get_stylesheet()

        # Assert
        assert result == expected

@pytest.mark.parametrize(
    "side_effect,expected_exception,expected_message",
    [
        (ValueError("No StyleSheet"), ValueError, "No StyleSheet"),
        (Exception("Unexpected error"), Exception, "Unexpected error"),
    ],
    ids=[
        "error_case_no_stylesheet",
        "error_case_unexpected_exception",
    ]
)
def test_get_stylesheet_error_cases(side_effect, expected_exception, expected_message):
    Singleton._instances = {}
    # Arrange
    with patch.object(StyleSheetReader, "get_stylesheet", side_effect=side_effect):

        # Act & Assert
        with pytest.raises(expected_exception) as exc_info:
            get_stylesheet()
        assert expected_message in str(exc_info.value)

@pytest.mark.parametrize(
    "platform_name,expected_location,expected_id",
    [
        ("Darwin", "res/stylesheet.qss", "darwin_platform"),
        ("Windows", "res/stylesheet-win-linux.qss", "windows_platform"),
        ("Linux", "res/stylesheet-win-linux.qss", "linux_platform"),
        ("", "res/stylesheet-win-linux.qss", "empty_platform"),
        ("UnknownOS", "res/stylesheet-win-linux.qss", "unknown_platform"),
    ],
    ids=[
        "darwin_platform",
        "windows_platform",
        "linux_platform",
        "empty_platform",
        "unknown_platform",
    ]
)
def test_get_platform_stylesheet(platform_name, expected_location, expected_id):
    # Arrange
    Singleton._instances = {}
    reader = StyleSheetReader()

    # Act
    result = reader._get_platform_stylesheet(platform_name)

    # Assert
    assert result == expected_location

@pytest.mark.parametrize(
    "platform_name,read_text_return,expected_result,expected_id",
    [
        ("Darwin", "body { background: #fff; }", "body { background: #fff; }", "darwin_happy"),
        ("Windows", "QLabel { color: red; }", "QLabel { color: red; }", "windows_happy"),
        ("Linux", "", "", "linux_empty"),
    ],
    ids=[
        "darwin_happy",
        "windows_happy",
        "linux_empty",
    ]
)
def test_get_layout_data_happy_and_edge(platform_name, read_text_return, expected_result, expected_id):
    # Arrange
    Singleton._instances = {}
    reader = StyleSheetReader()
    expected_location = reader._get_platform_stylesheet(platform_name)
    with patch("src.View.StyleSheetReader.platform.system", return_value=platform_name), \
         patch("src.View.StyleSheetReader.resource_path", return_value=expected_location), \
         patch("src.View.StyleSheetReader.pathlib.Path.read_text", return_value=read_text_return):

        # Act
        result = reader._get_layout_data()

        # Assert
        assert result == expected_result

@pytest.mark.parametrize(
    "platform_name,read_text_return,expected_exception,expected_message,expected_id",
    [
        ("Darwin", None, ValueError, "No StyleSheet", "darwin_none_error"),
        ("Windows", None, ValueError, "No StyleSheet", "windows_none_error"),
    ],
    ids=[
        "darwin_none_error",
        "windows_none_error",
    ]
)
def test_read_stylesheet_error_cases(platform_name, read_text_return, expected_exception, expected_message, expected_id):
    # Arrange
    Singleton._instances = {}
    reader = StyleSheetReader()
    with patch.object(reader, "_get_layout_data", return_value=read_text_return):

        # Act & Assert
        with pytest.raises(expected_exception) as exc_info:
            reader._read_stylesheet()
        assert expected_message in str(exc_info.value)

@pytest.mark.parametrize(
    "platform_name,read_text_return,expected_result,expected_id",
    [
        ("Darwin", "body { background: #fff; }", "body { background: #fff; }", "darwin_happy"),
        ("Windows", "QLabel { color: red; }", "QLabel { color: red; }", "windows_happy"),
        ("Linux", "", "", "linux_empty"),
    ],
    ids=[
        "darwin_happy",
        "windows_happy",
        "linux_empty",
    ]
)
def test_read_stylesheet_happy_and_edge(platform_name, read_text_return, expected_result, expected_id):
    # Arrange
    Singleton._instances = {}
    reader = StyleSheetReader()
    with patch.object(reader, "_get_layout_data", return_value=read_text_return):
        # Act
        result = reader._read_stylesheet()

        # Assert
        assert result == expected_result

@pytest.mark.parametrize(
    "platform_name,read_text_return,expected_result,expected_id",
    [
        ("Darwin", "body { background: #fff; }", "body { background: #fff; }", "darwin_happy"),
        ("Windows", "QLabel { color: red; }", "QLabel { color: red; }", "windows_happy"),
        ("Linux", "", "", "linux_empty"),
    ],
    ids=[
        "darwin_happy",
        "windows_happy",
        "linux_empty",
    ]
)
def test_get_stylesheet_method_happy_and_edge(platform_name, read_text_return, expected_result, expected_id):
    # Arrange
    Singleton._instances = {}
    reader = StyleSheetReader()
    with patch.object(reader, "_read_stylesheet", return_value=read_text_return):
        # Act
        result = reader.get_stylesheet()

        # Assert
        assert result == expected_result

def test_get_stylesheet_method_lru_cache():
    # Arrange
    Singleton._instances = {}
    reader = StyleSheetReader()
    with patch.object(reader, "_read_stylesheet", return_value="cached") as mock_read:
        # Act
        result1 = reader.get_stylesheet()
        result2 = reader.get_stylesheet()
        # Assert
        assert result1 == "cached"
        assert result2 == "cached"
        # Only called once due to lru_cache
        assert mock_read.call_count == 1
        # Checking if correct result is cache is cleared
        assert reader.get_stylesheet.cache_info().hits != 0
        assert not reader.get_stylesheet.cache_clear()
        result3 = reader.get_stylesheet()
        assert result3 == "cached"
        assert reader.get_stylesheet.cache_info().hits == 0

if __name__ == '__main__':
    pytest.main()
