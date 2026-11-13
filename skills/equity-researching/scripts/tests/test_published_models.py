"""Worked DCF models published online, matched to full precision: every
expected number is a spreadsheet's cached cell value (sources in figures.py).

    Wall Street Prep, Quick Lesson     year end, with a balance sheet and share count
    Wall Street Prep, Terminal Growth  mid_year
    Edward Bodmer, Proof of Timing     year_end and mid_year_including_continuing_value

These models give free cash flow, not the book's forecast lines, and grow it
into the continuing value: FCF x (1+g)/(r-g), where the book uses NOPAT. Two
ways to enter such a model:

  - Its own drivers (sales growth, margin, tax, investment). The continuing
    value then differs from the model's by an exact amount, taken off below.
  - Its free cash flow as sales, with a margin of 1, no tax and no investment,
    so NOPAT is the free cash flow. Nothing is taken off: this checks the
    discounting and the continuing value arithmetic on their own.
"""

import pytest

import dcf
from figures import BODMER, WSP_QUICK_LESSON, WSP_TERMINAL_GROWTH
from util import EXACT


def cash_flow_inputs(free_cash_flow_0, growth, cost_of_capital, long_term_growth, years, discounting):
    """A model given as free cash flow, entered as sales with a margin of 1.
    These models stop at enterprise value and give no share count, so the
    tests compare enterprise values; the count of 1 is never read."""
    return {
        "starting_sales": free_cash_flow_0,
        "sales_growth_rate": growth,
        "operating_profit_margin": 1,
        "cash_tax_rate": 0,
        "incremental_fixed_capital_rate": 0,
        "incremental_working_capital_rate": 0,
        "cost_of_capital": cost_of_capital,
        "continuing_value_method": "perpetuity_with_inflation",
        "inflation": long_term_growth,
        "nonoperating_assets": 0,
        "debt": 0,
        "shares_outstanding": 1,
        "forecast_years": years,
        "discounting": discounting,
    }


# --- Wall Street Prep, Quick Lesson (year end) -------------------------------

QL = WSP_QUICK_LESSON
YEARS = 5


def quick_lesson_with_its_drivers():
    """The sheet's own growth, margin and tax rate, and its investment amounts:
    capex less D&A, and the working-capital changes."""
    capex = [-cash_flow for cash_flow in QL["capital_expenditures_cash_flow"]]
    fixed = [c - d for c, d in zip(capex, QL["depreciation_and_amortization"])]
    working = [-sum(year) for year in zip(*QL["working_capital_cash_flows"])]
    return dcf.analyse({
        "starting_sales": QL["revenue_2012"],
        "sales_growth_rate": QL["growth"],
        "operating_profit_margin": QL["ebit_margin"],
        "cash_tax_rate": QL["tax_rate"],
        "fixed_capital_investment": fixed,
        "working_capital_investment": working,
        "cost_of_capital": QL["wacc"],
        "continuing_value_method": "perpetuity_with_inflation",
        "inflation": QL["long_term_growth"],
        "nonoperating_assets": QL["cash"],
        "debt": QL["debt"],
        "shares_outstanding": QL["diluted_shares"],
        "forecast_years": YEARS,
    })


@pytest.fixture(scope="module")
def quick_lesson():
    return quick_lesson_with_its_drivers()


@pytest.mark.parametrize("year", range(YEARS))
def test_quick_lesson_nopat_free_cash_flow_and_present_value(quick_lesson, year):
    row = quick_lesson["rows"][year]
    assert row["nopat"] == pytest.approx(QL["ebiat"][year], rel=EXACT)
    assert row["free_cash_flow"] == pytest.approx(QL["unlevered_free_cash_flow"][year], rel=EXACT)
    assert row["pv_free_cash_flow"] == pytest.approx(QL["pv_free_cash_flow"][year], rel=EXACT)


def test_quick_lesson_value_per_share_with_its_drivers(quick_lesson):
    # The sheet grows year 5's free cash flow, the book its NOPAT: add the
    # present value of growing the difference forever.
    r, g = QL["wacc"], QL["long_term_growth"]
    last = quick_lesson["rows"][YEARS - 1]
    gap = (last["free_cash_flow"] - last["nopat"]) * (1 + g) / (r - g) / (1 + r) ** YEARS
    assert last["pv_continuing_value"] + gap == pytest.approx(QL["pv_terminal_value"], rel=EXACT)
    assert quick_lesson["dcf"]["corporate_value"] + gap == pytest.approx(QL["enterprise_value"], rel=EXACT)
    per_share = (quick_lesson["dcf"]["shareholder_value"] + gap) / QL["diluted_shares"]
    assert per_share == pytest.approx(QL["value_per_share"], rel=EXACT)


def test_quick_lesson_value_per_share_from_its_cash_flows():
    sales = [QL["revenue_2012"]]
    for growth in QL["growth"]:
        sales.append(sales[-1] * (1 + growth))
    result = dcf.analyse({
        "starting_sales": QL["revenue_2012"],
        "sales_growth_rate": QL["growth"],
        "operating_profit_margin": [f / s for f, s in zip(QL["unlevered_free_cash_flow"], sales[1:])],
        "cash_tax_rate": 0,
        "incremental_fixed_capital_rate": 0,
        "incremental_working_capital_rate": 0,
        "cost_of_capital": QL["wacc"],
        "continuing_value_method": "perpetuity_with_inflation",
        "inflation": QL["long_term_growth"],
        "nonoperating_assets": QL["cash"],
        "debt": QL["debt"],
        "shares_outstanding": QL["diluted_shares"],
        "forecast_years": YEARS,
    })
    assert result["dcf"]["corporate_value"] == pytest.approx(QL["enterprise_value"], rel=EXACT)
    assert result["dcf"]["value_per_share"] == pytest.approx(QL["value_per_share"], rel=EXACT)


# --- Wall Street Prep, Terminal Growth Rate (mid_year) -----------------------

TG = WSP_TERMINAL_GROWTH


@pytest.fixture(scope="module")
def terminal_growth():
    return dcf.analyse(cash_flow_inputs(TG["free_cash_flow_0"], TG["growth"], TG["wacc"],
                                        TG["terminal_growth"], YEARS, "mid_year"))


@pytest.mark.parametrize("year", range(YEARS))
def test_terminal_growth_present_value_of_each_mid_year_cash_flow(terminal_growth, year):
    assert terminal_growth["rows"][year]["pv_free_cash_flow"] == pytest.approx(
        TG["pv_free_cash_flow"][year], rel=EXACT)


def test_terminal_growth_continuing_value_is_discounted_from_year_end(terminal_growth):
    assert terminal_growth["rows"][YEARS - 1]["pv_continuing_value"] == pytest.approx(
        TG["pv_terminal_value"], rel=EXACT)


def test_terminal_growth_enterprise_value(terminal_growth):
    assert terminal_growth["dcf"]["corporate_value"] == pytest.approx(TG["enterprise_value"], rel=EXACT)


# --- Edward Bodmer, Proof of Timing (year_end and mid-year) -------------------

def bodmer(discounting):
    return dcf.analyse(cash_flow_inputs(BODMER["free_cash_flow_0"], BODMER["growth"], BODMER["wacc"],
                                        BODMER["long_term_growth"], BODMER["years"], discounting))


def test_bodmer_year_end():
    result = bodmer("year_end")
    last = result["rows"][BODMER["years"] - 1]
    assert last["cumulative_pv_free_cash_flow"] == pytest.approx(BODMER["pv_free_cash_flow_year_end"], rel=EXACT)
    assert last["pv_continuing_value"] == pytest.approx(BODMER["pv_terminal_value_year_end"], rel=EXACT)
    assert result["dcf"]["corporate_value"] == pytest.approx(BODMER["enterprise_value_year_end"], rel=EXACT)


def test_bodmer_mid_year_including_continuing_value():
    result = bodmer("mid_year_including_continuing_value")
    assert result["dcf"]["corporate_value"] == pytest.approx(BODMER["enterprise_value_mid_year"], rel=EXACT)
