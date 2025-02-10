import os
import sys
import sqlite3
from pathlib import Path
import pytest
from PySide6.QtWidgets import QApplication

from src.Model.Configuration import Configuration


@pytest.fixture(scope="module", autouse=True)
def init_config(request):
    configuration = Configuration('TestConfig.db')
    db_file_path = Path(os.environ['USER_ONKODICOM_HIDDEN']).joinpath('TestConfig.db')
    configuration.set_db_file_path(db_file_path)
    connection = sqlite3.connect(db_file_path)
    configuration.update_default_directory(Path.cwd().joinpath('test', 'testdata'))

    def tear_down():
        connection.close()
        if os.path.isfile(db_file_path):
            os.remove(db_file_path)

    request.addfinalizer(tear_down)
    return connection


@pytest.fixture(scope="session", autouse=True)
def qapp_auto():
    app = QApplication(sys.argv)
    yield app
    app.processEvents()
    app.quit()
