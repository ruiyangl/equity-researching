"""End to end on real companies: management's projections go in through the
command line, and the result is checked against the value per share that the
company's bank published in an SEC merger filing (sources in figures.py).

The banks discount at year end from a fiscal year end, as the book does. They
differ from the book in one place: their continuing value starts from the
final year's free cash flow, where the book starts from NOPAT. The two differ
by that year's investment. So the tests check two things:

  - the bank's answer, rebuilt from the program's output by taking off the
    present value of continuing the final year's investment forever;
  - the program's own (book) answer, which must be close to the bank's.
"""

import json

import pytest

from figures import NIC, PRE_PAID_LEGAL
from util import growth_after, log, log_comparison

# How far each published answer can be from the rebuilt one, given how the
# filing rounds its figures. NIC gives "approximately 67.4 million" shares,
# good to 0.05 in 67.4 (0.07%). Pre-Paid Legal prints every figure in whole
# $ millions: one million more or less in 2015 moves its value by about 0.9%.
CASES = {
    "NIC": (NIC, 0.001),
    "Pre-Paid Legal": (PRE_PAID_LEGAL, 0.01),
}

# The book's continuing value differs from the bank's by under 0.6% here.
BOOK_VERSUS_BANK = 0.01


def investments(case):
    """Each year's fixed- and working-capital investment, from the filing's lines."""
    if case is NIC:
        fixed = [capex - depreciation for capex, depreciation in
                 zip(case["capital_expenditures"], case["depreciation_and_amortization"])]
        working = list(case["change_in_working_capital"])
        return fixed, working
    depreciation = [ebitda - ebit for ebitda, ebit in zip(case["ebitda"], case["ebit"])]
    # Cash in from selling investments counts as negative investment.
    fixed = [capex - dep - sold for capex, dep, sold in
             zip(case["capital_expenditures"], depreciation, case["investments_sold_cash_flow"])]
    working = [-cash_flow for cash_flow in case["working_capital_cash_flow"]]
    return fixed, working


def inputs(case, answer):
    """dcf.py inputs: the company's projections, as amounts."""
    fixed, working = investments(case)
    log.debug("fixed-capital investment %s; working-capital investment %s", fixed, working)
    return {
        "sales": case["revenue"],
        "operating_profit": case["ebit"],
        "cash_taxes": case["taxes"],
        "fixed_capital_investment": fixed,
        "working_capital_investment": working,
        "cost_of_capital": answer["cost_of_capital"],
        **growth_after(answer["growth"]),
        "nonoperating_assets": case["cash"],
        "debt": case["debt"],
        "shares_outstanding": case["diluted_shares"],
        "forecast_years": len(case["years"]),
    }


def value(run, save, case, answer):
    """Run dcf.py on the case, as a user would, and read its JSON output."""
    code, out, err = run(save(inputs(case, answer)), "--json")
    assert code == 0, err
    return json.loads(out)


ENDS = [pytest.param(case, tolerance, answer, id=f"{name} {answer['value_per_share']:.2f}")
        for name, (case, tolerance) in CASES.items() for answer in case["answers"]]


@pytest.mark.parametrize("year", range(5))
def test_free_cash_flow_matches_nics_filing(run, save, year):
    # The filing rounds every line to 0.1, so its sum can be 0.1 out
    # (2024 prints 103.6; its own lines add up to 103.7).
    result = value(run, save, NIC, NIC["answers"][0])
    free_cash_flow = result["rows"][year]["free_cash_flow"]
    log_comparison(f"NIC {NIC['years'][year]} free cash flow", free_cash_flow,
                   NIC["unlevered_free_cash_flow"][year], 0.1)
    assert free_cash_flow == pytest.approx(NIC["unlevered_free_cash_flow"][year], abs=0.1 + 1e-9)


@pytest.mark.parametrize("case, tolerance, answer", ENDS)
def test_the_banks_value_per_share(run, save, case, tolerance, answer):
    result = value(run, save, case, answer)
    years, r, g = len(case["years"]), answer["cost_of_capital"], answer["growth"]
    last = result["rows"][years - 1]
    investment = last["fixed_capital_investment"] + last["working_capital_investment"]
    gap = investment * (1 + g) / (r - g) / (1 + r) ** years
    banks = result["dcf"]["shareholder_value"] - gap
    log.debug("shareholder value %.4f, less the continuing value gap %.4f", result["dcf"]["shareholder_value"], gap)
    per_share = banks / case["diluted_shares"]
    log_comparison("bank's value per share", per_share, answer["value_per_share"],
                   tolerance * answer["value_per_share"])
    assert per_share == pytest.approx(answer["value_per_share"], rel=tolerance)


@pytest.mark.parametrize("case, tolerance, answer", ENDS)
def test_the_books_value_is_close_to_the_banks(run, save, case, tolerance, answer):
    result = value(run, save, case, answer)
    log_comparison("book's value per share", result["dcf"]["value_per_share"], answer["value_per_share"],
                   BOOK_VERSUS_BANK * answer["value_per_share"])
    assert result["dcf"]["value_per_share"] == pytest.approx(answer["value_per_share"], rel=BOOK_VERSUS_BANK)
