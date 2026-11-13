"""Lists, named parts, notes, and inputs the program must refuse."""

import pytest

import dcf
from figures import ILLUSTRATION, TABLE_2_1
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
    assert "'shares_outstanding' is missing" in problems(shares_outstanding=None)
    assert "give 'cash_taxes' (yearly amounts) or 'cash_tax_rate' (a rate)" in problems(cash_tax_rate=None)


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
    for expected in ("give 'cash_taxes'", "'shares_outstanding' must be greater than 0",
                     "'price' is not an input"):
        assert expected in text


def test_discounting_must_be_one_of_the_three():
    assert "'discounting' must be one of" in problems(discounting="midyear")


# --- The forecast as amounts, rates, or both ---------------------------------

AMOUNTS = {line: TABLE_2_1[line] for line in dcf.LINES}       # the book's table 2.1
RATES_ONLY = changed(ILLUSTRATION, starting_sales=None, **{driver: None for driver in dcf.DRIVERS})


def test_amounts_are_used_as_given():
    rows = dcf.analyse(dict(RATES_ONLY, **AMOUNTS))["rows"]
    for line, amounts in AMOUNTS.items():
        assert [row[line] for row in rows] == amounts


def test_the_books_table_in_amounts_gives_the_books_value():
    # The table prints cents, so its amounts are a little off the exact ones.
    result = dcf.analyse(dict(RATES_ONLY, **AMOUNTS))
    assert result["dcf"]["value_per_share"] == pytest.approx(257.07, abs=0.05)
    assert [row["free_cash_flow"] for row in result["rows"]] == pytest.approx(TABLE_2_1["free_cash_flow"], abs=0.011)


def test_the_same_numbers_as_amounts_or_rates_give_the_same_value():
    from_rates = dcf.analyse(ILLUSTRATION)
    amounts = {line: [row[line] for row in from_rates["rows"][:5]] for line in dcf.LINES}
    from_amounts = dcf.analyse(dict(RATES_ONLY, **amounts))
    assert from_amounts["dcf"]["value_per_share"] == pytest.approx(from_rates["dcf"]["value_per_share"], abs=CLOSE)


def test_rates_carry_on_after_the_amounts():
    rows = dcf.analyse(changed(ILLUSTRATION, sales=[110, 125]))["rows"]
    assert [row["sales"] for row in rows[:3]] == pytest.approx([110, 125, 137.5], abs=CLOSE)
    # Year 3's investment: its rate on the sales added after the last amount.
    assert rows[2]["fixed_capital_investment"] == pytest.approx((137.5 - 125) * 0.15, abs=CLOSE)


def test_amounts_can_be_given_for_some_lines_and_rates_for_others():
    rows = dcf.analyse(changed(ILLUSTRATION, cash_tax_rate=None, cash_taxes=[5, 5, 5, 5, 5],
                               max_years=10, forecast_years=5))["rows"]
    assert [row["cash_taxes"] for row in rows] == [5, 5, 5, 5, 5]
    assert rows[0]["operating_profit"] == pytest.approx(16.5, abs=CLOSE)          # 110 x 15%


def test_a_line_with_amounts_and_no_rate_ends_the_table():
    inputs = changed(ILLUSTRATION, cash_tax_rate=None, cash_taxes=[4, 4, 4])
    assert "'forecast_years' must be a whole number from 1 to 3" in problems(
        cash_tax_rate=None, cash_taxes=[4, 4, 4])
    assert len(dcf.analyse(dict(inputs, forecast_years=3))["rows"]) == 3


def test_investment_amounts_need_no_rate_however_little_sales_change():
    # As a rate this year's investment would be 10 per $0.01 of added sales:
    # 1000, refused as a typing mistake. As an amount it is just 10.
    rows = dcf.analyse(changed(ILLUSTRATION, sales=[110, 110.01], fixed_capital_investment=[10, 10],
                               incremental_fixed_capital_rate=None, forecast_years=2))["rows"]
    assert rows[1]["fixed_capital_investment"] == 10


def test_starting_sales_is_needed_only_when_year_1_comes_from_a_rate():
    dcf.analyse(dict(RATES_ONLY, **AMOUNTS))                       # no starting_sales: fine
    assert "'starting_sales' is missing: year 1 of 'sales' comes from a rate" in problems(
        starting_sales=None, fixed_capital_investment=[1.5], working_capital_investment=[1.0])


def test_neither_amounts_nor_a_rate_is_refused():
    assert "give 'sales' (yearly amounts) or 'sales_growth_rate' (a rate)" in problems(sales_growth_rate=None)


@pytest.mark.parametrize("amounts, problem", [
    (110, "'sales' must be a list of yearly amounts"),
    ([], "'sales' must be a list of yearly amounts"),
    ([110, "121"], "'sales' year 2 must be a number"),
    ([110, 0], "'sales' year 2 must be greater than 0"),
])
def test_bad_amounts_are_refused(amounts, problem):
    assert problem in problems(sales=amounts)


def test_amounts_win_over_rates_for_the_years_they_cover():
    # Every line has the book's amounts for years 1 to 5 and the book's rates.
    # The amounts are printed to the cent, so they differ from what the rates
    # give: years 1 to 5 must be the amounts, year 6 the rates applied to them.
    rows = dcf.analyse(dict(ILLUSTRATION, **AMOUNTS))["rows"]
    for line, amounts in AMOUNTS.items():
        assert [row[line] for row in rows[:5]] == amounts
    assert rows[5]["sales"] == pytest.approx(161.05 * 1.10, abs=CLOSE)
    assert rows[5]["fixed_capital_investment"] == pytest.approx((161.05 * 1.10 - 161.05) * 0.15, abs=CLOSE)
    assert len(rows) == 25
