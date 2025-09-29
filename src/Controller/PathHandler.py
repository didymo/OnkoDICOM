import os
import sys
import re
from pathlib import Path
import sys


def resource_path(relative_path, sanitizing=False):
    """
    Get absolute path to resource, works for dev and for PyInstaller
    :param relative_path: str
    :param sanitizing: bool: to remove any characters which may cause escape from the string
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    path: str = str(os.path.join(base_path, relative_path))

    if sanitizing: # to Remove anything not ^. _0-9a-zA-Z
        path: Path = path_sanitizer(path)
    return path

def path_sanitizer(path: str | Path) -> Path:
    """
    Converts str to Path breaks the path into individual components of the path.
    Runs the PathHandler,text_filter(text: str) -> str method on each component
    then rebuild the file path using Path("path").joinpath("word").

    :param path: str | Path
    :return: Path
    """
    filtered_path: Path = Path()
    for word in Path(path).parts:
        text_sanitiser(word)
        filtered_path: Path = Path(filtered_path).joinpath(text_sanitiser(word))
    return filtered_path

def text_sanitiser(text: str) -> str:
    """
    Removes all characters which are not . (fullstop),  (space), _(underscore), 0 to 9, a to z, or A to Z
    From any text entered into it.

    :param text: str
    :return: str
    """
    return re.sub(r"[^. _0-9a-zA-Z]", "", text)

def data_path(relative_path):
    """
    Get absolute path to data. Checks to see if the file is in the hidden
    directory. If not, returns the file from the 'data' folder. May crash
    if the file is not in the hidden directory and the program wants to
    write to the file.
    :param relative_path: relative path to get the absolute path of.
    """
    # Get the absolute path (hidden directory)
    home_dir = Path.home()
    hidden_dir = home_dir.joinpath('.OnkoDICOM', 'data')
    absolute_path = hidden_dir.joinpath(relative_path)

    # Check to see if the file exists in the hidden directory. Return if it
    # does.
    if os.path.exists(absolute_path):
        return absolute_path

    # Get the file from the data folder
    base_path = Path.cwd()
    data_folder = base_path.joinpath(base_path)

    # Walk through directory
    for root, dirs, files in os.walk(str(data_folder), topdown=True):
        for name in files:
            if name == relative_path:
                return os.path.join(root, name)

def database_path() -> Path:
    """
    To get the path of the database.

    :return: Path
    """
    return Path.home().joinpath('.OnkoDICOM', 'OnkoDICOM.db')