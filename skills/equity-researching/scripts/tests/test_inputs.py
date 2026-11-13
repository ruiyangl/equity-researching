"""Lists, named parts, notes, and inputs the program must refuse."""

import pytest

import dcf
from figures import ILLUSTRATION
from util import BOOK, CLOSE, changed


def problems(**changes):
    with pytest.raises(dcf.InputError) as caught:
        dcf.analyse(changed(ILLUSTRATION, **changes))
    return " | ".join(caught.value.problems)


def test_a_list_gives_each_year_its_own_number_and_repeats_the_last():
    rows = dcf.analyse(changed(ILLUSTRATION, sales_growth_rate=[0.20, 0.10]))["rows"]
    assert rows[0]["sales"] == pytest.approx(120.0, abs=CLOSE)     # 100 x 1.20
    assert rows[1]["sales"] == pytest.approx(132.0, abs=CLOSE)     # x 1.10
    assert rows[2]["sales"] == pytest.approx(145.2, abs=CLOSE)     # x 1.10 again


def test_a_list_of_equal_numbers_matches_a_single_number():
    one = dcf.analyse(ILLUSTRATION)["dcf"]["value_per_share"]
    many = dcf.analyse(changed(ILLUSTRATION, operating_profit_margin=[0.15] * 3))["dcf"]["value_per_share"]
    assert one == pytest.approx(many, abs=CLOSE)


def test_named_parts_are_added_up():
    plain = dcf.analyse(changed(ILLUSTRATION, debt=30, nonoperating_assets=12))
    parts = dcf.analyse(changed(ILLUSTRATION, debt={"bonds": 25, "leases": 5},
                                nonoperating_assets={"cash": 10, "stake": 2}))
    value = plain["dcf"]["shareholder_value"]
    assert value == pytest.approx(parts["dcf"]["shareholder_value"], abs=CLOSE)
    assert value == pytest.approx(257.07 + 12 - 30, abs=BOOK)


def test_value_per_share_divides_by_the_share_count():
    result = dcf.analyse(changed(ILLUSTRATION, shares_outstanding=10))
    assert result["dcf"]["value_per_share"] == pytest.approx(25.707, abs=BOOK / 10)


def test_keys_starting_with_underscore_are_notes():
    result = dcf.analyse(changed(ILLUSTRATION, _sources={"sales": "10-K"}))
    assert "_sources" not in result["inputs"]


def test_a_missing_input_is_named():
    assert "'cash_tax_rate' is missing" in problems(cash_tax_rate=None)


def test_a_percentage_typed_as_7_is_refused():
    assert "write 7% as 0.07" in problems(sales_growth_rate=7)
    assert "'operating_profit_margin' year 2" in problems(operating_profit_margin=[0.15, 15])


def test_an_unknown_input_is_refused():
    assert "'price' is not an input" in problems(price=40)


def test_each_method_asks_for_its_own_inputs():
    assert "'inflation_recouped' is missing" in problems(
        continuing_value_method="perpetuity_with_partial_inflation")
    assert "'decline_rate' is missing" in problems(continuing_value_method="perpetuity_with_decline")
    assert "must be one of" in problems(continuing_value_method="gordon")


def test_cost_of_capital_must_exceed_growth_after_the_forecast_period():
    assert "'cost_of_capital' must be higher" in problems(inflation=0.08)


def test_something_to_solve_for_is_required():
    assert "give 'forecast_years'" in problems(forecast_years=None)


def test_the_forecast_period_must_fit_in_the_table():
    assert "'forecast_years' must be a whole number from 1 to 25" in problems(forecast_years=26)
    assert "'forecast_years' must be a whole number" in problems(forecast_years=5.5)


def test_all_problems_are_reported_together():
    text = problems(cash_tax_rate=None, shares_outstanding=0, price=40)
    for expected in ("'cash_tax_rate' is missing", "'shares_outstanding' must be greater than 0",
                     "'price' is not an input"):
        assert expected in text
