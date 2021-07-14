import os
import sqlite3

import pytest

from src.Model.Configuration import Configuration


@pytest.fixture(scope="module", autouse=True)
def init_config(request):
    configuration = Configuration('TestConfig.db')
    db_file_path = os.environ['USER_ONKODICOM_HIDDEN'] + 'TestConfig.db'
    configuration.set_db_file_path(db_file_path)
    connection = sqlite3.connect(db_file_path)
    configuration.update_default_directory("../testdata/DICOM-RT-TEST")

    def tear_down():
        connection.close()
        if os.path.isfile(db_file_path):
            os.remove(db_file_path)

    request.addfinalizer(tear_down)
    return connection
