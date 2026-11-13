"""The program reproduces the authors' Domino's Pizza spreadsheet
(expectationsinvesting.com, Online Tutorial 8)."""

import pytest

import dcf
from figures import DOMINOS_VALUE_PER_SHARE, DOMINOS_YEAR_1, DOMINOS_YEAR_8
from util import SHEET


@pytest.fixture(scope="module")
def result():
    return dcf.analyse(dcf.EXAMPLE)


def test_the_table_has_25_forecast_periods(result):
    assert len(result["rows"]) == 25


@pytest.mark.parametrize("year, figure", list(enumerate(DOMINOS_VALUE_PER_SHARE, 1)))
def test_value_per_share_for_all_25_forecast_periods(result, year, figure):
    assert result["rows"][year - 1]["value_per_share"] == pytest.approx(figure, abs=SHEET)


@pytest.mark.parametrize("year, line, figure", [
    (year, line, figure)
    for year, column in ((1, DOMINOS_YEAR_1), (8, DOMINOS_YEAR_8))
    for line, figure in column.items()
])
def test_every_line_of_year_1_and_year_8(result, year, line, figure):
    assert result["rows"][year - 1][line] == pytest.approx(figure, abs=SHEET)


def test_market_implied_forecast_period_is_8_years(result):
    # At $418 the sheet's answer is 8: $417.71 with 8 years, $437.84 with 9.
    reverse = result["reverse_dcf"]
    assert reverse["status"] == "found"
    assert reverse["years"] == 8
    assert reverse["label"] == "8 years"


def test_dcf_reads_the_row_of_the_chosen_forecast_period(result):
    # The example asks for 10 years: the tenth figure in the sheet.
    assert result["dcf"]["forecast_years"] == 10
    assert result["dcf"]["value_per_share"] == pytest.approx(458.288887, abs=SHEET)
