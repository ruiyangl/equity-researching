"""Mid-year discounting, end to end on a real company (sources in figures.py).

Cornerstone Building Brands' bank, Centerview, discounted the free cash flows
and the continuing value mid-year: "mid_year_including_continuing_value". Its
board book gives a 3 x 3 grid of prices, the debt and cash it took off, and how
its share count, so every input comes from the source. The one printed count,
133.7mm, is used for every price.

The prices are rounded to $0.25, and the inputs behind them to $1mm, which can
move a price by up to $0.071 more (worked out in figures.py). Eight prices are
within the $0.25 rounding alone; $20.50 needs the inputs' rounding too and is
marked as a known miss of the stricter check.

As in test_real_companies.py, the bank's continuing value starts from free
cash flow where the book's starts from NOPAT, and the tests take that gap off.
"""

import json

import pytest

import dcf
from figures import CORNERSTONE
from util import CLOSE, growth_after, log, log_comparison

C = CORNERSTONE
YEARS = 5


def inputs(answer, discounting):
    fixed = [capex - dep - settlement for capex, dep, settlement in zip(
        C["capital_expenditures"], C["depreciation_and_amortization"], C["cash_settlement"])]
    working = [-cash_flow for cash_flow in C["working_capital_cash_flow"]]
    log.debug("fixed-capital investment %s; working-capital investment %s", fixed, working)
    return {
        "sales": C["revenue"],
        "operating_profit": C["ebit"],
        "cash_taxes": C["taxes"],
        "fixed_capital_investment": fixed,
        "working_capital_investment": working,
        "cost_of_capital": answer["cost_of_capital"],
        **growth_after(answer["growth"]),
        "nonoperating_assets": C["cash"],
        "debt": C["debt"],
        "shares_outstanding": C["diluted_shares"],
        "forecast_years": YEARS,
        "discounting": discounting,
    }


def banks_value_per_share(run, save, answer, discounting):
    """Run dcf.py as a user would, then take off the gap between the bank's
    continuing value (from terminal free cash flow) and the book's (NOPAT)."""
    code, out, err = run(save(inputs(answer, discounting)), "--json")
    assert code == 0, err
    result = json.loads(out)
    r, g = answer["cost_of_capital"], answer["growth"]
    nopat = result["rows"][YEARS - 1]["nopat"]
    earlier = dcf.DISCOUNTING[discounting][1]
    gap = (nopat - C["terminal_free_cash_flow"]) * (1 + g) / (r - g) / (1 + r) ** (YEARS - earlier)
    log.debug("%s: shareholder value %.4f, less the continuing value gap %.4f",
              discounting, result["dcf"]["shareholder_value"], gap)
    return (result["dcf"]["shareholder_value"] - gap) / result["inputs"]["shares_outstanding"]


def grid_id(answer):
    return f"{answer['cost_of_capital']:.2%} {answer['growth']:.3%}"


GRID = [pytest.param(answer, id=grid_id(answer)) for answer in C["answers"]]

# Off by $0.154 against $0.125: within the inputs' rounding, not the price's alone.
KNOWN_MISS = 20.50
STRICT_GRID = [pytest.param(answer, id=grid_id(answer), marks=pytest.mark.xfail(
                   strict=True, reason="$0.154 out: needs the inputs' rounding too (figures.py)"))
               if answer["value_per_share"] == KNOWN_MISS else pytest.param(answer, id=grid_id(answer))
               for answer in C["answers"]]


@pytest.mark.parametrize("year", range(YEARS))
def test_free_cash_flow_matches_the_filing(run, save, year):
    # The filing prints whole millions: 2026 adds up to 583 against 582 printed.
    code, out, err = run(save(inputs(C["answers"][0], C["discounting"])), "--json")
    free_cash_flow = json.loads(out)["rows"][year]["free_cash_flow"]
    log_comparison(f"{C['years'][year]} free cash flow", free_cash_flow, C["free_cash_flow"][year], 1)
    assert free_cash_flow == pytest.approx(C["free_cash_flow"][year], abs=1 + 1e-9)


@pytest.mark.parametrize("answer", STRICT_GRID)
def test_every_published_price_within_its_own_rounding(run, save, answer):
    # Prices are "rounded to the nearest $0.25", so each is within $0.125.
    value = banks_value_per_share(run, save, answer, C["discounting"])
    log_comparison("price, its own rounding", value, answer["value_per_share"], C["price_rounding"] / 2)
    assert value == pytest.approx(answer["value_per_share"], abs=C["price_rounding"] / 2)


@pytest.mark.parametrize("answer", GRID)
def test_every_published_price_within_its_rounding_and_the_inputs(run, save, answer):
    value = banks_value_per_share(run, save, answer, C["discounting"])
    allowed = C["price_rounding"] / 2 + C["input_rounding"]
    log_comparison("price, with the inputs' rounding", value, answer["value_per_share"], allowed)
    assert value == pytest.approx(answer["value_per_share"], abs=allowed)


@pytest.mark.parametrize("discounting", [d for d in dcf.DISCOUNTING if d != C["discounting"]])
@pytest.mark.parametrize("answer", GRID)
def test_the_other_conventions_miss_every_price(run, save, answer, discounting):
    value = banks_value_per_share(run, save, answer, discounting)
    allowed = C["price_rounding"] / 2 + C["input_rounding"]
    log_comparison(f"price under {discounting}", value, answer["value_per_share"], allowed, should_match=False)
    assert abs(value - answer["value_per_share"]) > allowed


def test_mid_year_moves_each_free_cash_flow_half_a_year():
    year_end = dcf.analyse(dict(dcf.EXAMPLE))["rows"]
    mid_year = dcf.analyse(dict(dcf.EXAMPLE, discounting="mid_year"))["rows"]
    half_year = (1 + dcf.EXAMPLE["cost_of_capital"]) ** 0.5
    for before, after in zip(year_end, mid_year):
        assert after["pv_free_cash_flow"] == pytest.approx(before["pv_free_cash_flow"] * half_year, abs=CLOSE)
        assert after["pv_continuing_value"] == pytest.approx(before["pv_continuing_value"], abs=CLOSE)


def test_including_the_continuing_value_moves_the_whole_value_half_a_year():
    year_end = dcf.analyse(dict(dcf.EXAMPLE))["rows"]
    mid_year = dcf.analyse(dict(dcf.EXAMPLE, discounting="mid_year_including_continuing_value"))["rows"]
    half_year = (1 + dcf.EXAMPLE["cost_of_capital"]) ** 0.5
    for before, after in zip(year_end, mid_year):
        assert after["corporate_value"] == pytest.approx(before["corporate_value"] * half_year, abs=CLOSE)
