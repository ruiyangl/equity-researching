"""Chapter 2, Summary Illustration: the program reproduces table 2.1."""

import pytest

import dcf
from figures import ILLUSTRATION, TABLE_2_1, TOTAL_INVESTMENT
from util import BOOK, CLOSE

YEARS = range(1, 6)


@pytest.fixture(scope="module")
def result():
    return dcf.analyse(ILLUSTRATION)


@pytest.mark.parametrize("line", TABLE_2_1)
@pytest.mark.parametrize("year", YEARS)
def test_every_line_of_the_table(result, line, year):
    printed = TABLE_2_1[line][year - 1]
    assert result["rows"][year - 1][line] == pytest.approx(printed, abs=BOOK)


@pytest.mark.parametrize("year", YEARS)
def test_total_investment(result, year):
    row = result["rows"][year - 1]
    both = row["fixed_capital_investment"] + row["working_capital_investment"]
    assert both == pytest.approx(TOTAL_INVESTMENT[year - 1], abs=BOOK)


def test_present_value_of_continuing_value_is_209_63(result):
    assert result["rows"][4]["pv_continuing_value"] == pytest.approx(209.63, abs=BOOK)


def test_shareholder_value_is_257_07(result):
    assert result["dcf"]["shareholder_value"] == pytest.approx(257.07, abs=BOOK)
    assert result["dcf"]["value_per_share"] == pytest.approx(257.07, abs=BOOK)


def test_value_is_free_cash_flow_plus_continuing_value(result):
    # 47.44 + 209.63 = 257.07, as the text says.
    row = result["rows"][4]
    both = row["cumulative_pv_free_cash_flow"] + row["pv_continuing_value"]
    assert both == pytest.approx(result["dcf"]["shareholder_value"], abs=CLOSE)
