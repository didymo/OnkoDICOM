"""
Created on Fri Aug  21 12:33:04 2020

@author: sjswerdloff
"""

import os
import pathlib
import tempfile
import pytest

from src.Model.Anon import (
    _check_identity_mapping_file_exists,
    _create_reidentification_spreadsheet,
    _trim_bracketing_single_quotes,
    anonymize,
    anon_file_name,
)


def test_trim_single_quotes():
    no_quotes = "LAST^FIRST"
    left_quote = "'LAST^FIRST"
    both_quotes = "'LAST^FIRST'"
    middle_only_quotes = "LAST'S^FIRST"
    middle_with_both_quotes = "'LAST'S^FIRST"
    assert no_quotes == _trim_bracketing_single_quotes(no_quotes)
    assert no_quotes == _trim_bracketing_single_quotes(left_quote)
    assert no_quotes == _trim_bracketing_single_quotes(both_quotes)
    assert no_quotes != _trim_bracketing_single_quotes(middle_only_quotes)
    assert middle_only_quotes == _trim_bracketing_single_quotes(middle_with_both_quotes)


def test_check_specific_csv_file_exists():
    orig_cwd = os.getcwd()
    orig_cwd_path = pathlib.Path().joinpath(orig_cwd)
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = pathlib.Path()
            test_path = test_path.joinpath(tmpdir)
            os.chdir(test_path)
            csv_filename = "patientHash.csv"
            was_file_present, full_path_to_file = _check_identity_mapping_file_exists(
                csv_filename
            )
            assert not was_file_present
            assert not os.path.exists(full_path_to_file)
            expected_path = test_path.joinpath("data", "csv", csv_filename)
            specified_path = pathlib.Path().joinpath(full_path_to_file)
            assert expected_path == specified_path
            os.makedirs(os.path.dirname(specified_path))
            f = open(specified_path, mode="x")
            f.close()
            was_file_present, full_path_to_file = _check_identity_mapping_file_exists(
                csv_filename
            )
            assert was_file_present
            assert os.path.exists(full_path_to_file)
            os.chdir(orig_cwd_path)
    finally:
        os.chdir(orig_cwd_path)


def test_create_hash_csv():
    patient_identifier = "ABC123"
    anonymised_identifier = "FakeAnonABC123"
    patient_two_identifier = "DEF456"
    patient_two_anonymised_id = "FakeAnonDEF456"
    orig_cwd = os.getcwd()
    orig_cwd_path = pathlib.Path().joinpath(orig_cwd)
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            test_path = pathlib.Path()
            test_path = test_path.joinpath(tmpdir)
            # expect a filename that is not patientHash.csv to fail
            csv_filename = "test_identifier_map.csv"
            os.chdir(test_path)
            with pytest.raises(Exception) as e_info:
                _create_reidentification_spreadsheet(
                    patient_identifier, anonymised_identifier, csv_filename
                )
            # print(str(e_info))

            csv_filename = "patientHash.csv"
            expected_path = test_path.joinpath("data", "csv", csv_filename)
            # the _create_reidentification_spreadsheet() will fail unless the path is already in place
            # it will not create the directories on its own.
            # so... create the directory in advance for the csv file
            os.makedirs(os.path.dirname(expected_path))
            assert os.path.exists(os.path.dirname(expected_path))
            # test that the file will be created if it is not there
            _create_reidentification_spreadsheet(
                patient_identifier, anonymised_identifier, csv_filename
            )
            assert os.path.exists(expected_path)
            f = open(expected_path, mode="a")
            f.close()
            # test that the file will be appended if it is already there
            assert os.path.exists(expected_path)
            _create_reidentification_spreadsheet(
                patient_two_identifier, patient_two_anonymised_id, csv_filename
            )
            f = open(expected_path, mode="r")
            lines = f.readlines()
            # header plus first row plus second row makes for three rows
            assert 3 == len(lines)
            # print(f"Found {len(lines)} rows including header in {expected_path}")
            f.close()
            # make sure duplicate entries are not created
            _create_reidentification_spreadsheet(
                patient_two_identifier, patient_two_anonymised_id, csv_filename
            )
            f = open(expected_path, mode="r")
            lines = f.readlines()
            f.close()
            # attempt to add a duplicate row does not result in an additional row
            assert 3 == len(lines)
            os.chdir(orig_cwd_path)
    finally:
        os.chdir(orig_cwd_path)

def test_anon_file_name():
    hashed_patient_id = "./mybad\@:;filename$with%problematic~chara&ters"
    file_name_hashed_patient_id = "__mybad_@__filename_with%problematic_chara_ters"
    all_special_characters = ".!@#$%^&*()[]{};:,./<>?\|`~-=_+"
    file_name_all_special_characters = "_!@#_%^__()[]{}___.______`_-=_+"
    assert file_name_hashed_patient_id == anon_file_name(hashed_patient_id)
    assert file_name_all_special_characters == anon_file_name(all_special_characters)
