"""
Created on Fri Aug  21 12:33:04 2020

@author: sjswerdloff
"""

import logging
import os
import pathlib
import tempfile

import pytest
from pydicom import dataset

from src.Model.Anon import (
    Check_if_folder,
    anonymize,
    check_CSV_folder_exist,
    check_file_hashed,
    check_folder_exist,
    checkFileExist,
    create_hash_csv,
)


def test_check_csv_folder_exist():
    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = pathlib.Path()
        test_path = test_path.joinpath(tmpdir)
        assert not check_CSV_folder_exist(test_path)
        csv_path = pathlib.Path.joinpath(test_path, "CSV")
        pathlib.os.mkdir(csv_path)
        assert check_CSV_folder_exist(tmpdir)


def test_check_specific_csv_file_exists():
    orig_cwd = os.getcwd()
    orig_cwd_path = pathlib.Path().joinpath(orig_cwd)
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = pathlib.Path()
            test_path = test_path.joinpath(tmpdir)
            # csv_path = pathlib.Path.joinpath(test_path, "csv")
            # pathlib.os.mkdir(csv_path)
            os.chdir(test_path)
            csv_filename = "patientHash.csv"
            was_file_present, full_path_to_file = checkFileExist(csv_filename)
            assert not was_file_present
            assert not os.path.exists(full_path_to_file)
            expected_path = test_path.joinpath("src", "data", "csv", csv_filename)
            specified_path = pathlib.Path().joinpath(full_path_to_file)
            assert expected_path == specified_path
            os.makedirs(os.path.dirname(specified_path))
            f = open(specified_path, mode="x")
            f.close()
            was_file_present, full_path_to_file = checkFileExist(csv_filename)
            assert was_file_present
            assert os.path.exists(full_path_to_file)

    finally:
        os.chdir(orig_cwd_path)


def test_create_hash_csv():
    patient_identifier = "ABC123"
    anonymised_identifier = "FakeAnonABC123"
    orig_cwd = os.getcwd()
    orig_cwd_path = pathlib.Path().joinpath(orig_cwd)
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = pathlib.Path()
            test_path = test_path.joinpath(tmpdir)
            csv_filename = "test_identifier_map.csv"
            os.chdir(test_path)
            with pytest.raises(Exception) as e_info:
                create_hash_csv(patient_identifier, anonymised_identifier, csv_filename)
            print(str(e_info))
            csv_filename = "patientHash.csv"
            expected_path = test_path.joinpath("src", "data", "csv", csv_filename)
            # with pytest.raises(Exception) as e_info:
            os.makedirs(os.path.dirname(expected_path))
            assert os.path.exists(os.path.dirname(expected_path))
            create_hash_csv(patient_identifier, anonymised_identifier, csv_filename)
            assert os.path.exists(expected_path)
            f = open(expected_path, mode="a")
            f.close()
            assert os.path.exists(expected_path)
            create_hash_csv(patient_identifier, anonymised_identifier, csv_filename)
            f = open(expected_path, mode="r")
            lines = f.readlines()
            for line in lines:
                print(line)
            f.close()
    finally:
        os.chdir(orig_cwd_path)
