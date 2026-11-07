"""
The DVH CSV export's dose columns (Redmine 3093: blank cells), on the real test
data. Each ROI there with a volume must have a dose in every column, and each
dose must agree with its curve to within the export's 10 cGy sampling step.
"""
from pathlib import Path

import numpy as np
import pydicom
import pytest

from src.Model.CalculateDVHs import (DVH_CSV_PERCENTS, DVH_CSV_STEP,
                                     calc_dvhs, dvh2pandas, dvh_csv_doses,
                                     get_roi_info)

DATA = Path.cwd().joinpath('test', 'testdata', 'DICOM-RT-02')


@pytest.fixture(scope="module")
def dvhs():
    """The DVHs of every ROI in the test data, calculated as the app does."""
    rtss = pydicom.dcmread(DATA / '20191031-215249_m.dcm')
    rtdose = pydicom.dcmread(DATA / 'RTDOSE__Hashed.dcm')
    return calc_dvhs(rtss, rtdose, get_roi_info(rtss))


def curve_dose(counts, percent):
    """The highest 1 cGy bin whose relative volume is at least percent."""
    return np.nonzero(counts >= percent - 1e-9)[0][-1]


def test_no_blank_cells_for_an_roi_with_volume(dvhs):
    rows = dvh2pandas(dvhs, 'P')
    for dvh in dvhs.values():
        assert dvh.volume > 0
        row = rows[rows['ROI'] == dvh.name].iloc[0]
        blank = [col for col in rows.columns[2:] if row[col] == '']
        assert blank == [], dvh.name


@pytest.mark.parametrize("name, percent", [
    # Its curve starts at 99.99999999999999%, never exactly 100%.
    ('LUNG_L', 100.0),
    # Its only sample above these percentages is the first (minimum 0.01 Gy).
    ('SPINALCORD', 100.0),
    ('SPINALCORD', 89.0),
    # The curve falls from 100% past 99.5% within one 10 cGy step.
    ('LIVER', 99.5),
])
def test_the_cells_that_were_blank(dvhs, name, percent):
    dvh = next(d for d in dvhs.values() if d.name == name)
    counts = dvh.relative_volume.counts
    doses = dict(zip(DVH_CSV_PERCENTS, dvh_csv_doses(counts)))
    assert doses[percent] != ''
    assert abs(int(doses[percent]) - curve_dose(counts, percent)) \
        <= DVH_CSV_STEP


def test_every_dose_is_within_one_step_of_the_curve(dvhs):
    for dvh in dvhs.values():
        counts = dvh.relative_volume.counts
        for percent, dose in zip(DVH_CSV_PERCENTS, dvh_csv_doses(counts)):
            assert abs(int(dose) - curve_dose(counts, percent)) \
                <= DVH_CSV_STEP, (dvh.name, percent)


def test_an_roi_with_no_volume_has_no_doses():
    # A curve that is 0% everywhere (an empty ROI) reaches only 0%: its other
    # cells stay blank, as before. What they should show is a clinical question.
    assert dvh_csv_doses(np.zeros(1)) == [''] * (len(DVH_CSV_PERCENTS) - 1) + ['0']


# Curves whose answer is known (connor-227743e6, review of #11). On real curves a
# sample rarely meets a percentage exactly, so these are where exact hits are
# tested: a sample that met a percentage must be the one above for the next.
def test_a_linear_curve_gives_every_dose_exactly():
    # 1 cGy bins from 100% at 0 cGy to 0% at 1000 cGy: p% is received by at
    # least (100 - p) * 10 cGy, and every percentage is a sample or exactly
    # half-way between two, where even the export's mirrored interpolation (see
    # dvh_csv_doses) is exact.
    doses = dvh_csv_doses(np.linspace(100, 0, 1001))
    for percent, dose in zip(DVH_CSV_PERCENTS, doses):
        assert dose == str(round((100 - percent) * 10)), percent


def test_a_steep_target_like_curve_gives_every_dose_within_one_step():
    # 100% up to 500 cGy, then falling linearly to 0% at 520 cGy. Between two
    # samples the export's interpolation is mirrored, so a dose can be off by up
    # to one step (99.5% reads 510; the answer is 500.1), but never by more.
    counts = np.concatenate([np.full(500, 100.0),
                             np.linspace(100, 0, 21), np.zeros(10)])
    doses = dvh_csv_doses(counts)
    for percent, dose in zip(DVH_CSV_PERCENTS, doses):
        assert abs(int(dose) - (500 + (100 - percent) * 0.2)) \
            <= DVH_CSV_STEP, percent
