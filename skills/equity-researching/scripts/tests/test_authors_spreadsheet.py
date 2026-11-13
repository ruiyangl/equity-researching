"""The program reproduces the authors' own spreadsheets: Domino's Pizza
(expectationsinvesting.com, Online Tutorial 8) and, from the first edition,
Gateway (Online Tutorial 9). Sources in figures.py."""

import pytest

import dcf
from figures import (DOMINOS_VALUE_PER_SHARE, DOMINOS_YEAR_1, DOMINOS_YEAR_8, GATEWAY,
                     GATEWAY_MARKET_IMPLIED_YEARS, GATEWAY_VALUE_PER_SHARE, GATEWAY_YEAR_1,
                     GATEWAY_YEAR_7)
from util import EXACT, SHEET


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


# --- Gateway: every number is the spreadsheet's cached value ----------------

@pytest.fixture(scope="module")
def gateway():
    return dcf.analyse(GATEWAY)


@pytest.mark.parametrize("year, figure", list(enumerate(GATEWAY_VALUE_PER_SHARE, 1)))
def test_gateway_value_per_share_for_all_25_forecast_periods(gateway, year, figure):
    assert gateway["rows"][year - 1]["value_per_share"] == pytest.approx(figure, rel=EXACT)


@pytest.mark.parametrize("year, line, figure", [
    (year, line, figure)
    for year, column in ((1, GATEWAY_YEAR_1), (7, GATEWAY_YEAR_7))
    for line, figure in column.items()
])
def test_gateway_every_line_of_year_1_and_year_7(gateway, year, line, figure):
    assert gateway["rows"][year - 1][line] == pytest.approx(figure, rel=EXACT)


def test_gateway_market_implied_forecast_period_is_7_years(gateway):
    # Year 7 is worth 51.99, a cent under the $52 price, and year 8 57.97: the
    # sheet counts the years worth no more than the price, so 7.
    assert gateway["reverse_dcf"]["years"] == GATEWAY_MARKET_IMPLIED_YEARS
