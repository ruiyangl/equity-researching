"""The answers the reverse DCF can give."""

import pytest

import dcf
from figures import DOMINOS_VALUE_PER_SHARE, ILLUSTRATION
from util import changed


def reverse(**changes):
    return dcf.analyse(changed(dcf.EXAMPLE, **changes))["reverse_dcf"]


@pytest.mark.parametrize("years, value", list(enumerate(DOMINOS_VALUE_PER_SHARE, 1)))
def test_a_price_equal_to_the_value_at_n_years_gives_n(years, value):
    assert reverse(share_price=value + 0.001)["years"] == (years if years < 25 else None)


def test_price_below_the_one_year_value():
    answer = reverse(share_price=200.0)         # year 1 is worth 285.18
    assert (answer["status"], answer["years"]) == ("less_than_1", None)
    assert answer["label"] == "less than 1 year"


def test_price_above_the_last_year_in_the_table():
    answer = reverse(share_price=1000.0)        # year 25 is worth 806.16
    assert (answer["status"], answer["years"]) == ("more_than_max", None)
    assert answer["label"] == "more than 25 years"


def test_growth_that_destroys_value_never_reaches_the_price():
    # A 2% margin cannot pay for 80 cents of investment per dollar of new
    # sales, so every extra year of growth lowers the value.
    result = dcf.analyse(changed(
        ILLUSTRATION, operating_profit_margin=0.02,
        incremental_fixed_capital_rate=0.60, incremental_working_capital_rate=0.20,
        continuing_value_method="perpetuity", share_price=50.0))
    values = [row["value_per_share"] for row in result["rows"]]
    assert values == sorted(values, reverse=True)
    assert result["reverse_dcf"]["status"] == "none"


def test_a_longer_table_finds_a_longer_period():
    answer = reverse(share_price=1000.0, max_years=40)
    assert answer["status"] == "found"
    assert answer["years"] > 25


def test_reverse_dcf_alone_needs_no_forecast_period():
    result = dcf.analyse(changed(dcf.EXAMPLE, forecast_years=None))
    assert result["dcf"] is None
    assert result["reverse_dcf"]["years"] == 8


def test_dcf_alone_needs_no_share_price():
    assert dcf.analyse(ILLUSTRATION)["reverse_dcf"] is None
