from pathlib import Path
import sys
import os


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


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
    hidden_dir = home_dir.joinpath('OnkoDICOM', 'data')
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
