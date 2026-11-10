"""
The DVH CSV export's dose columns (Redmine 3093: blank cells), on the real test
data. Each ROI there with a volume must have a dose in every column, and each
dose is read from its curve's 1 cGy bins (Gitea #13).
"""
from pathlib import Path

import numpy as np
import pydicom
import pytest

from dicompylercore import dvh as dcdvh

from src.Model.CalculateDVHs import (DVH_CSV_PERCENTS, calc_dvhs,
                                     dvh2pandas, dvh_csv_curve, dvh_csv_doses,
                                     get_roi_info)

DATA = Path.cwd().joinpath('test', 'testdata', 'DICOM-RT-02')


@pytest.fixture(scope="module")
def dvhs():
    """The DVHs of every ROI in the test data, calculated as the app does."""
    rtss = pydicom.dcmread(DATA / '20191031-215249_m.dcm')
    rtdose = pydicom.dcmread(DATA / 'RTDOSE__Hashed.dcm')
    return calc_dvhs(rtss, rtdose, get_roi_info(rtss))


def assert_is_the_curve_dose(counts, percent, dose):
    """dose is the highest 1 cGy bin whose relative volume is at least percent:
    that bin reaches it, and the next one (if any) does not."""
    d = int(dose)
    assert counts[d] >= percent - 1e-9, (percent, d)
    assert d == len(counts) - 1 or counts[d + 1] < percent - 1e-9, (percent, d)


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
    assert_is_the_curve_dose(counts, percent, doses[percent])


def test_every_dose_is_read_from_the_curve(dvhs):
    for dvh in dvhs.values():
        counts = dvh.relative_volume.counts
        for percent, dose in zip(DVH_CSV_PERCENTS, dvh_csv_doses(counts)):
            assert_is_the_curve_dose(counts, percent, dose)


def test_a_lower_percentage_never_gets_a_lower_dose(dvhs):
    for dvh in dvhs.values():
        doses = [int(d) for d in dvh_csv_doses(dvh.relative_volume.counts)]
        assert doses == sorted(doses), dvh.name


def test_an_roi_with_no_volume_has_no_doses():
    # A curve that is 0% everywhere (an empty ROI) reaches only 0%: its other
    # cells stay blank, as before. What they should show is a clinical question.
    assert dvh_csv_doses(np.zeros(1)) == [''] * (len(DVH_CSV_PERCENTS) - 1) + ['0']


# Curves whose answer is known (connor-227743e6, review of #11).
def test_a_linear_curve_gives_every_dose_exactly():
    # 1 cGy bins from 100% at 0 cGy to 0% at 1000 cGy: p% is received by at
    # least (100 - p) * 10 cGy.
    doses = dvh_csv_doses(np.linspace(100, 0, 1001))
    for percent, dose in zip(DVH_CSV_PERCENTS, doses):
        assert dose == str(round((100 - percent) * 10)), percent


def test_a_steep_target_like_curve_reads_the_bin_not_the_next_sample():
    # 100% up to 500 cGy, then 5% less per cGy to 5% at 519 cGy, where it ends:
    # dicompyler's curves end at the maximum dose, with no zero bins after it
    # (measured on DICOM-RT-02), so 0% reads the maximum. The mirrored
    # interpolation read 99.5% as 510 cGy (Gitea #13); the curve says 500.
    counts = np.concatenate([np.full(500, 100.0), np.linspace(100, 5, 20)])
    doses = dict(zip(DVH_CSV_PERCENTS, dvh_csv_doses(counts)))
    assert (doses[100.0], doses[99.5], doses[95.0], doses[94.5],
            doses[50.0], doses[0.0]) == ('500', '500', '501', '501', '510', '519')


def test_the_monotonicity_case_from_gitea_13():
    # Cumulative DVH, linear between (0, 100), (10, 99.7), (20, 99.5), (30, 98)
    # and (60, 0), in 1 cGy bins.
    counts = np.interp(np.arange(61), [0, 10, 20, 30, 60], [100, 99.7, 99.5, 98, 0])
    doses = dict(zip(DVH_CSV_PERCENTS, dvh_csv_doses(counts)))
    assert (doses[100.0], doses[99.5], doses[99.0], doses[98.0]) == ('0', '20', '23', '30')


def zero_dose_dvh(volume_cm3):
    """An ROI inside the dose grid that receives 0 cGy everywhere, as
    dicompyler-core builds it: one bin at 0, holding the volume."""
    return dcdvh.DVH(counts=np.array([volume_cm3]), bins=np.array([0.0, 0.01]),
                     dvh_type='cumulative', dose_units='Gy',
                     volume_units='cm3', name='Z')


@pytest.mark.parametrize("volume_cm3", [0.5, 1.0, 3.0])
def test_a_zero_dose_roi_has_0_cgy_in_every_cell(volume_cm3):
    # Gitea #23: dicompyler-core leaves this curve at 100 x the volume, so
    # under 1 cm3 the higher percentages were blank.
    zero = zero_dose_dvh(volume_cm3)
    assert zero.max == 0
    assert dvh_csv_doses(dvh_csv_curve(zero)) == ['0'] * len(DVH_CSV_PERCENTS)


def test_an_roi_with_no_volume_counted_stays_blank():
    empty = zero_dose_dvh(0.0)
    doses = dvh_csv_doses(dvh_csv_curve(empty))
    assert doses == [''] * (len(DVH_CSV_PERCENTS) - 1) + ['0']


def test_an_roi_with_dose_uses_its_own_curve(dvhs):
    for dvh in dvhs.values():
        assert dvh.max > 0
        assert np.array_equal(dvh_csv_curve(dvh), dvh.relative_volume.counts)
