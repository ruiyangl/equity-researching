#!/usr/bin/env python3
"""
Tests for dcf.py. Run:  python3 test_dcf.py        (standard library only)

Expected values are computed here by hand arithmetic or by small independent
loops, never by calling the engine's own helpers, so a wrong formula in dcf.py
cannot agree with itself.

HOW TO RUN
----------
    python3 test_dcf.py                       everything (a few seconds); the last line is "OK"
    python3 test_dcf.py -v                    the same, naming each test as it runs
    python3 test_dcf.py HandArithmetic        one group
    python3 test_dcf.py HandArithmetic.test_drivers_build_and_gordon_terminal      one test

HOW TO READ A TEST
------------------
Every test builds a small inputs file, runs some part of dcf.py on it, and states what the
answer has to be. The statements are the self.assert... lines:
    assertAlmostEqual(a, b, places=9)   a and b agree to nine decimals (exact equality is too
                                        strict for computer arithmetic: 0.1 + 0.2 is not quite 0.3)
    assertEqual(a, b)                   exactly equal
    assertIn(x, things)                 x is among them - usually "this flag was raised"
    assertRaises(dcf.InputError)        the code inside the `with` block must be rejected
A test passes when every statement in it holds. When one does not, the run prints which
statement failed and the two values it compared.

THE GROUPS
----------
    HandArithmetic     two-year models checked line by line against calculator arithmetic
    TimingAndStub      when cash is taken to arrive: mid-year, and a partly elapsed first year
    PathsAndFade       input shorthand (flat / list / ramp), fade years, shared scenario defaults
    LegacyReports      reproduces the figures in the October 2026 CRM, NVDA and GOOGL reports
    Dilution           options (treasury-stock method) and convertibles (if-converted)
    DiscountRate       CAPM, WACC, choosing r* and r_hi; scenario values do not read the price
    ReverseDcf         implied growth, margin and terminal value; the F1, F3 and F5 inversions
    HandOff            bear / base / bull values, PWV, PWR; the cyclical mean-reversion check
    FlagsAndQuality    each warning fires when it should, and stays quiet when it should not
    Sensitivity        the rate x terminal-growth grid; value moves the right way with each input
    Validation         bad inputs are rejected, with a message that says how to fix them
    Output             the report and the JSON carry the right numbers; the command line works

THE STANDARD TEST COMPANY
-------------------------
Most tests start from inputs() below: a company small enough to follow on a calculator.
    Revenue was 100 last year and grows 10% a year for two forecast years, then 2% for ever.
    EBIT margin 20%, tax 25%, D&A 5% of revenue, capex 8%, working capital 10% of NEW revenue.
    100 shares, no cash, no debt, cash counted at each year-end.

                         Year 1     Year 2     Terminal year
    Revenue              110.00     121.00       123.42
    EBIT (20%)            22.00      24.20        24.684
    - tax (25%)            5.50       6.05         6.171
    + D&A (5%)             5.50       6.05         6.171
    - capex (8%)           8.80       9.68         9.8736
    - change in NWC        1.00       1.10         0.242     (10% of the INCREASE in revenue)
    = free cash flow      12.20      13.42        14.5684

    At a 10% discount rate:
        12.20 / 1.1  +  13.42 / 1.1^2  +  (14.5684 / (0.10 - 0.02)) / 1.1^2
      =    11.09     +      11.09      +             150.50                  =  172.68
    or 1.73 per share. The numbers 12.2, 13.42, 123.42 and 14.5684 recur all through this file.
"""
import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest

# Make `import dcf` find the dcf.py that sits next to this file, wherever the tests are run from.
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dcf  # noqa: E402

DCF = os.path.join(HERE, "dcf.py")      # the script's path, for the tests that run it as a command


# ---------------------------------------------------------------------------
# Helpers shared by every test. They keep each test down to the one thing it is about.
# ---------------------------------------------------------------------------


def inputs(mode="drivers", **over):
    """A small valid inputs file; tests override the parts they exercise.

    Returns the standard test company (the table at the top of this file) as an inputs dict.
    Keyword arguments replace or extend its top-level sections:
        inputs("drivers", market={"price": 2.0})            adds a section
        inputs("drivers", model={"timing": "mid_year"})     changes one key inside "model"
    The four modes describe the same sort of business, each in its own vocabulary:
        drivers      the full build - the table at the top of this file
        fcf_margin   revenue 110 and 121, with a flat 15% free-cash-flow margin
        eps          EPS of 4.00 growing 10% a year, 80% of it turning into cash; equity basis
        direct       cash flows of 100 and 110, supplied as they are
    The discount-rate inputs give a cost of equity of 4% + 1.2 x 5% = 10%, and there is no debt,
    so in every unmodified fixture r* is 10% and r_hi is 12%.
    """
    base = {
        "meta": {"ticker": "TST", "valuation_date": "2026-01-01"},
        "shares": {"count": 100.0},
        "bridge": {"cash_and_investments": 0.0, "debt": 0.0},
        "discount_rate": {"risk_free": 0.04, "equity_risk_premium": 0.05, "beta": 1.2},
        "model": {"mode": mode, "timing": "end_year", "explicit_years": 2},
        "sources": {"all": "test fixture"},
    }
    if mode == "drivers":
        base["scenarios"] = [{
            "name": "base", "slot": "base", "label": "analyst construction",
            "revenue": {"base": 100.0, "growth": [0.10, 0.10]},
            "ebit_margin": 0.20, "tax_rate": 0.25, "da_pct_revenue": 0.05,
            "capex_pct_revenue": 0.08, "nwc_pct_incremental_revenue": 0.10,
            "terminal": {"growth": 0.02},
        }]
    elif mode == "fcf_margin":
        base["scenarios"] = [{
            "name": "base", "slot": "base", "label": "analyst construction",
            "revenue": {"base": 100.0, "growth": [0.10, 0.10]},
            "fcf_margin": 0.15, "sbc_deducted": True, "terminal": {"growth": 0.02},
        }]
    elif mode == "eps":
        base["model"]["basis"] = "equity"
        base["scenarios"] = [{
            "name": "base", "slot": "base", "label": "analyst construction",
            "eps": {"base": 4.0, "growth": [0.10, 0.10]},
            "fcf_conversion": 0.8, "terminal": {"growth": 0.02},
        }]
    else:
        del base["model"]["explicit_years"]
        base["scenarios"] = [{
            "name": "base", "slot": "base", "label": "analyst construction",
            "fcf": [100.0, 110.0], "terminal": {"growth": 0.02},
        }]
    # Apply the caller's overrides: a dict is merged into the existing section (so the other keys
    # of that section survive); anything else, or a section that did not exist, is simply set.
    for key, val in over.items():
        if isinstance(val, dict) and isinstance(base.get(key), dict):
            base[key].update(val)
        else:
            base[key] = val
    return base


def three(sc, bear=0.8, bull=1.25, weights=(0.25, 0.5, 0.25), scale_key=None):
    """Bear/base/bull scenarios by scaling one field of a base scenario.

    Many tests need three scenarios without caring how they differ. This copies `sc` three times,
    names and slots the copies bear / base / bull with the given weights, and multiplies one
    field (scale_key) by 0.8 for the bear and 1.25 for the bull: scale_key="ebit_margin" turns a
    20% margin into 16% / 20% / 25%. With scale_key=None the three copies are identical and the
    test edits them itself.
    """
    out = []
    for name, slot, k, w in (("bear", "bear", bear, weights[0]), ("base", "base", 1.0, weights[1]),
                             ("bull", "bull", bull, weights[2])):
        s = copy.deepcopy(sc)
        s.update({"name": name, "slot": slot, "weight": w})
        if scale_key == "fcf":
            s["fcf"] = [x * k for x in s["fcf"]]
        elif scale_key:
            s[scale_key] = s[scale_key] * k
        out.append(s)
    return out


def value(raw, r, idx=0, ov=None):
    """Validate `raw`, then value its scenario number `idx` at discount rate r. Returns the dict
    that dcf.value_at() produces ("operating_value", "value_per_share", ...). `ov` passes
    overrides straight through, e.g. {"terminal_growth": 0.025}."""
    inp = dcf.normalize(raw)
    return dcf.scenario_value(inp["scenarios"][idx], r, inp, ov)


def codes(res, level=None):
    """The set of flag codes raised in a run - all of them, or only the "WARN"s or the "NOTE"s -
    so a test can say assertIn("W-TV-SHARE", codes(res))."""
    return {f["code"] for f in res["flags"] if level is None or f["level"] == level}


def run(raw):
    """The whole analysis, as `dcf.py run` performs it, minus reading and writing files."""
    return dcf.analyze(dcf.normalize(raw))


# ---------------------------------------------------------------------------
class HandArithmetic(unittest.TestCase):
    """Two-year models small enough to check with a calculator.

    Every expected number in this group is written out as arithmetic on the standard test
    company (the table at the top of the file): 12.2 and 13.42 are its two forecast cash flows,
    123.42 its terminal-year revenue, and 1.1 and 1.21 are (1 + 10%) and (1 + 10%) squared.
    If a test here fails, the engine's core arithmetic has changed.
    """

    def test_drivers_build_and_gordon_terminal(self):
        """The full build, line by line: each year's cash flow, the terminal year, the value,
        and the share of that value which is terminal."""
        raw = inputs("drivers")
        inp = dcf.normalize(raw)
        proj = dcf.project(inp["scenarios"][0], inp)
        # Year 1: revenue 110, EBIT 22, tax 5.5, D&A 5.5, capex 8.8, dNWC 1.0
        self.assertAlmostEqual(proj["flows"][0], 22 - 5.5 + 5.5 - 8.8 - 1.0, places=9)        # 12.2
        # Year 2: revenue 121, EBIT 24.2, tax 6.05, D&A 6.05, capex 9.68, dNWC 1.1
        self.assertAlmostEqual(proj["flows"][1], 24.2 - 6.05 + 6.05 - 9.68 - 1.1, places=9)   # 13.42
        # Terminal year: revenue 123.42; working capital is sized for 2% growth, not 10%.
        fcf_t = 123.42 * 0.20 * 0.75 + 123.42 * 0.05 - 123.42 * 0.08 - 0.10 * (123.42 - 121.0)
        self.assertAlmostEqual(proj["terminal_fcf"], fcf_t, places=9)                          # 14.5684
        v = dcf.value_at(proj, 0.10, inp)
        want = 12.2 / 1.1 + 13.42 / 1.21 + (fcf_t / 0.08) / 1.21
        self.assertAlmostEqual(v["operating_value"], want, places=9)
        self.assertAlmostEqual(v["value_per_share"], want / 100.0, places=9)
        self.assertAlmostEqual(v["tv_share"], (fcf_t / 0.08) / 1.21 / want, places=9)

    def test_mid_year_shifts_every_flow_half_a_year(self):
        """Mid-year timing discounts every cash flow, and the perpetuity, half a year less. So
        the whole value must be exactly (1.1)^0.5 = 1.0488 times the year-end value."""
        raw = inputs("drivers", model={"timing": "mid_year"})
        v = value(raw, 0.10)
        fcf_t = 123.42 * 0.20 * 0.75 + 123.42 * 0.05 - 123.42 * 0.08 - 0.10 * 2.42
        want = 12.2 / 1.1 ** 0.5 + 13.42 / 1.1 ** 1.5 + (fcf_t / 0.08) / 1.1 ** 1.5
        self.assertAlmostEqual(v["operating_value"], want, places=9)
        self.assertAlmostEqual(v["operating_value"] / value(inputs("drivers"), 0.10)["operating_value"],
                               1.1 ** 0.5, places=9)

    def test_value_driver_terminal(self):
        """value_driver: terminal cash flow = NOPAT x (1 - g / RONIC). Growing 2% while earning
        10% on new capital means reinvesting 20% of profit and keeping 80% of it."""
        raw = inputs("drivers")
        raw["scenarios"][0]["terminal"] = {"method": "value_driver", "growth": 0.02, "ronic": 0.10}
        v = value(raw, 0.10)
        nopat_t = 123.42 * 0.20 * 0.75
        tv = nopat_t * (1 - 0.02 / 0.10) / 0.08
        self.assertAlmostEqual(v["operating_value"], 12.2 / 1.1 + 13.42 / 1.21 + tv / 1.21, places=9)

    def test_exit_multiple_terminal_and_implied_growth(self):
        """exit_multiple: terminal value = 10 x year-2 EBITDA (EBIT 24.2 + D&A 6.05 = 30.25).
        The perpetual growth rate that multiple quietly assumes is reported alongside."""
        raw = inputs("drivers")
        raw["scenarios"][0]["terminal"] = {"method": "exit_multiple", "growth": 0.02,
                                           "exit_multiple": 10.0, "exit_metric": "ebitda"}
        v = value(raw, 0.10)
        tv = (24.2 + 6.05) * 10.0
        self.assertAlmostEqual(v["operating_value"], 12.2 / 1.1 + 13.42 / 1.21 + tv / 1.21, places=9)
        # TV = FCF2 (1+g)/(r-g)  =>  g = (TV r - FCF2)/(TV + FCF2)
        self.assertAlmostEqual(v["implied_perpetual_growth"], (tv * 0.10 - 13.42) / (tv + 13.42), places=9)

    def test_non_gaap_margin_deducts_sbc(self):
        """A 28% "adjusted" margin with SBC at 8% of revenue is the same business as a 20% GAAP
        margin, and has to be worth exactly the same."""
        raw = inputs("drivers")
        raw["scenarios"][0].update({"ebit_margin": 0.28, "ebit_margin_basis": "non_gaap", "sbc_pct_revenue": 0.08})
        self.assertAlmostEqual(value(raw, 0.10)["operating_value"],
                               value(inputs("drivers"), 0.10)["operating_value"], places=9)

    def test_losses_carry_forward_and_shield_later_tax(self):
        """A loss pays no tax and joins the pool of losses carried forward; the next profit is
        sheltered by that pool. Margins of -10% then +30%, with 4.0 of losses brought forward:
        year 1 loses 11 (pool becomes 15); year 2 earns 36.3 and is taxed on 36.3 - 15 = 21.3."""
        raw = inputs("drivers")
        raw["scenarios"][0].update({"ebit_margin": [-0.10, 0.30], "nol_balance": 4.0, "nol_usage_limit": 0.8})
        inp = dcf.normalize(raw)
        rows = dcf.project(inp["scenarios"][0], inp)["rows"]
        self.assertAlmostEqual(rows[0]["ebit"], -11.0, places=9)
        self.assertEqual(rows[0]["tax"], 0.0)
        self.assertAlmostEqual(rows[0]["nol_end"], 15.0, places=9)             # 4 opening + 11 loss
        # Year 2 EBIT 36.3: shield = min(15, 0.8 x 36.3 = 29.04) = 15; tax = 25% x 21.3
        self.assertAlmostEqual(rows[1]["tax"], 0.25 * (36.3 - 15.0), places=9)
        self.assertAlmostEqual(rows[1]["nol_end"], 0.0, places=9)

    def test_nol_usage_limit_binds(self):
        """With a pool (100) far larger than the profit (22), only 80% of the year's profit may
        be sheltered: 17.6 is used, tax is due on the remaining 4.4, and 82.4 is carried on."""
        raw = inputs("drivers")
        raw["scenarios"][0].update({"nol_balance": 100.0, "nol_usage_limit": 0.8})
        inp = dcf.normalize(raw)
        rows = dcf.project(inp["scenarios"][0], inp)["rows"]
        self.assertAlmostEqual(rows[0]["tax"], 0.25 * (22.0 - 0.8 * 22.0), places=9)
        self.assertAlmostEqual(rows[0]["nol_end"], 100.0 - 17.6, places=9)

    def test_fcf_margin_mode(self):
        """The shortcut mode: cash flow = revenue x 15%, then the same discounting as above."""
        v = value(inputs("fcf_margin"), 0.10)
        want = 110 * 0.15 / 1.1 + 121 * 0.15 / 1.21 + (123.42 * 0.15 / 0.08) / 1.21
        self.assertAlmostEqual(v["operating_value"], want, places=9)

    def test_fcf_margin_before_sbc_is_reduced_by_sbc(self):
        """A 22% free-cash-flow margin stated before SBC, with SBC at 7% of revenue, is the
        standard 15% margin after SBC - same value."""
        raw = inputs("fcf_margin")
        raw["scenarios"][0].update({"fcf_margin": 0.22, "sbc_deducted": False, "sbc_pct_revenue": 0.07})
        self.assertAlmostEqual(value(raw, 0.10)["operating_value"],
                               value(inputs("fcf_margin"), 0.10)["operating_value"], places=9)

    def test_eps_mode_equity_basis(self):
        """EPS of 4.40 and 4.84, 80% of each converting to cash; the perpetuity starts from the
        next year's EPS, 4.84 x 1.02. Everything is per share, so no share count is involved."""
        v = value(inputs("eps"), 0.10)
        want = 4.4 * 0.8 / 1.1 + 4.84 * 0.8 / 1.21 + (4.84 * 1.02 * 0.8 / 0.08) / 1.21
        self.assertAlmostEqual(v["value_per_share"], want, places=9)

    def test_eps_mode_firm_basis_adds_net_cash_per_share(self):
        """On a firm basis the same EPS stream is worth net cash per share more:
        (900 cash - 400 debt) / 100 shares = 5.00."""
        raw = inputs("eps", bridge={"cash_and_investments": 900.0, "debt": 400.0})
        raw["model"]["basis"] = "firm"
        self.assertAlmostEqual(value(raw, 0.10)["value_per_share"],
                               value(inputs("eps"), 0.10)["value_per_share"] + 5.0, places=9)

    def test_eps_terminal_override_and_exit_multiple(self):
        """Two other ways to end an EPS model. First, a stated terminal EPS (3.00) and terminal
        conversion (90%) in place of "last year grown at g" - how a cyclical caught at a peak is
        brought back to mid-cycle. Second, an exit P/E of 15 on year-2 EPS."""
        raw = inputs("eps")
        raw["scenarios"][0]["terminal"] = {"growth": 0.02, "eps": 3.0, "fcf_conversion": 0.9}
        want = 4.4 * 0.8 / 1.1 + 4.84 * 0.8 / 1.21 + (3.0 * 0.9 / 0.08) / 1.21
        self.assertAlmostEqual(value(raw, 0.10)["value_per_share"], want, places=9)
        raw["scenarios"][0]["terminal"] = {"growth": 0.02, "method": "exit_multiple", "exit_multiple": 15.0,
                                           "exit_metric": "eps"}
        want = 4.4 * 0.8 / 1.1 + 4.84 * 0.8 / 1.21 + 4.84 * 15.0 / 1.21
        self.assertAlmostEqual(value(raw, 0.10)["value_per_share"], want, places=9)

    def test_direct_mode(self):
        """Supplied cash flows of 100 and 110. The terminal cash flow is 110 x 1.02 by default,
        or the scenario's own figure (90) when it gives one."""
        v = value(inputs("direct"), 0.10)
        self.assertAlmostEqual(v["operating_value"], 100 / 1.1 + 110 / 1.21 + (110 * 1.02 / 0.08) / 1.21, places=9)
        raw = inputs("direct")
        raw["scenarios"][0]["terminal"] = {"growth": 0.02, "fcf": 90.0}
        self.assertAlmostEqual(value(raw, 0.10)["operating_value"],
                               100 / 1.1 + 110 / 1.21 + (90 / 0.08) / 1.21, places=9)

    def test_bridge_to_equity(self):
        """Every line of the bridge, each with its sign: + cash 500 + non-operating assets 100
        - debt 300 - preferred 50 - minorities 20 - other claims 30 = +200 on top of operating value."""
        raw = inputs("direct", bridge={"cash_and_investments": 500.0, "non_operating_assets": 100.0, "debt": 300.0,
                                       "preferred_equity": 50.0, "minority_interest": 20.0, "other_claims": 30.0})
        op = 100 / 1.1 + 110 / 1.21 + (110 * 1.02 / 0.08) / 1.21
        v = value(raw, 0.10)
        self.assertAlmostEqual(v["equity_value"], op + 500 + 100 - 300 - 50 - 20 - 30, places=9)
        self.assertAlmostEqual(v["value_per_share"], (op + 200) / 100.0, places=9)

    def test_equity_basis_ignores_cash_and_debt(self):
        """On an equity basis the cash flows are already after interest, so cash and debt must
        not be counted a second time: the value is the same as with an empty balance sheet."""
        raw = inputs("direct", bridge={"cash_and_investments": 500.0, "debt": 300.0})
        raw["model"]["basis"] = "equity"
        self.assertAlmostEqual(value(raw, 0.10)["value_per_share"], value(inputs("direct"), 0.10)["value_per_share"],
                               places=9)

    def test_equity_wiped_floors_at_zero(self):
        """Debt of 5,000 against a business worth about 1,300. The raw value per share is
        negative, the reported value is zero (shareholders cannot lose more than everything),
        and the run raises the warning that says so."""
        raw = inputs("direct", bridge={"cash_and_investments": 0.0, "debt": 5000.0},
                     discount_rate={"debt_to_capital": 0.5, "pre_tax_cost_of_debt": 0.08, "tax_rate": 0.21})
        v = value(raw, 0.10)
        self.assertLess(v["value_per_share_raw"], 0)
        self.assertEqual(v["value_per_share"], 0.0)
        self.assertIn("W-EQUITY-WIPED", codes(run(raw)))


# ---------------------------------------------------------------------------
class TimingAndStub(unittest.TestCase):
    """WHEN a cash flow is taken to arrive - which decides how hard it is discounted.

    The stub tests value the company on 2026-07-01 with its fiscal year ending 2026-12-31: 183
    days, half of year 1, are still to come. `s` in the arithmetic below is that fraction,
    183 / 365.25 = 0.501.
    """

    def stub_inputs(self, timing):
        """Cash flows of 100 (FY2026) and 110 (FY2027), valued half-way through FY2026, with the
        business sold at the end of FY2027 for 10 x 110 = 1,100. An exit value is used so that
        the three pieces - stub year, full year, terminal - can be told apart in the arithmetic."""
        raw = inputs("direct", model={"timing": timing},
                     meta={"valuation_date": "2026-07-01", "first_forecast_year_end": "2026-12-31",
                           "first_forecast_label": "FY2026"})
        raw["scenarios"][0]["terminal"] = {"growth": 0.02, "method": "exit_multiple", "exit_multiple": 10.0,
                                           "exit_metric": "fcf"}
        return raw

    def test_stub_end_year(self):
        """Only the half of year 1 still to come counts (s x 100), received at the year-end, s
        years away. Year 2's cash flow and the exit value arrive one year after that."""
        raw = self.stub_inputs("end_year")
        s = 183 / 365.25
        self.assertAlmostEqual(dcf.normalize(raw)["meta"]["stub"], s, places=12)
        v = value(raw, 0.10)
        want = s * 100 / 1.1 ** s + 110 / 1.1 ** (s + 1) + 1100 / 1.1 ** (s + 1)
        self.assertAlmostEqual(v["operating_value"], want, places=9)

    def test_stub_mid_year(self):
        """The same company with mid-year timing: each cash flow moves to the middle of its own
        period, while the exit value - a sale on a date - stays at the end of year 2."""
        raw = self.stub_inputs("mid_year")
        s = 183 / 365.25
        v = value(raw, 0.10)
        # stub flow at the middle of the stub; year 2 at the middle of year 2; exit value at the end of year 2
        want = s * 100 / 1.1 ** (s / 2) + 110 / 1.1 ** (s + 0.5) + 1100 / 1.1 ** (s + 1)
        self.assertAlmostEqual(v["operating_value"], want, places=9)

    def test_stub_with_gordon_terminal_mid_year(self):
        """Unlike an exit value, a perpetuity IS a stream of cash flows, so under mid-year timing
        it too arrives half a year sooner: discounted over s + 0.5 years rather than s + 1."""
        raw = self.stub_inputs("mid_year")
        raw["scenarios"][0]["terminal"] = {"growth": 0.02}
        s = 183 / 365.25
        want = s * 100 / 1.1 ** (s / 2) + 110 / 1.1 ** (s + 0.5) + (110 * 1.02 / 0.08) / 1.1 ** (s + 0.5)
        self.assertAlmostEqual(value(raw, 0.10)["operating_value"], want, places=9)

    def test_no_dates_means_year_one_is_the_next_twelve_months(self):
        """With no fiscal dates in the file there is no stub: year 1 counts in full."""
        self.assertEqual(dcf.normalize(inputs("direct"))["meta"]["stub"], 1.0)

    def test_first_year_must_be_in_progress(self):
        """Valued on 2026-01-01, year 1 cannot be a year that already ended (2025-12-31), one
        that ends on the valuation date itself, or one ending more than twelve months out
        (2027-06-30) - that last would silently skip a year of cash flow."""
        for fye in ("2025-12-31", "2026-01-01", "2027-06-30"):
            raw = inputs("direct", meta={"first_forecast_year_end": fye})
            with self.assertRaises(dcf.InputError):
                dcf.normalize(raw)

    def test_growing_perpetuity_is_horizon_invariant(self):
        """FCF growing at g forever is worth FCF1/(r-g) wherever the explicit period is cut.

        The single most useful check on the engine. Revenue grows 2.5% a year in the forecast
        AND in perpetuity, so where the forecast stops is arbitrary: 1, 3, 7 or 15 explicit years
        must all give 200 x 1.025 x 30% / (9% - 2.5%) = 946.15. A slip anywhere - the projection,
        the discounting, the terminal value, the hand-over between them - breaks the equality.
        """
        for timing, factor in (("end_year", 1.0), ("mid_year", 1.09 ** 0.5)):
            for n in (1, 3, 7, 15):
                raw = inputs("fcf_margin", model={"timing": timing, "explicit_years": n})
                raw["scenarios"][0].update({"revenue": {"base": 200.0, "growth": 0.025}, "fcf_margin": 0.3,
                                            "terminal": {"growth": 0.025}})
                self.assertAlmostEqual(value(raw, 0.09)["operating_value"],
                                       200 * 1.025 * 0.3 / (0.09 - 0.025) * factor, places=7)

    def test_year_labels(self):
        """Year labels count up from the first one, keeping whatever surrounds the digits (the
        "E" in FY27E) and rolling 99 over to 00. A label with no year in it falls back to Y1, Y2."""
        self.assertEqual(dcf.year_labels({"first_forecast_label": "FY2027"}, 2), ["FY2027", "FY2028", "FY2029"])
        self.assertEqual(dcf.year_labels({"first_forecast_label": "FY27E"}, 1), ["FY27E", "FY28E"])
        self.assertEqual(dcf.year_labels({"first_forecast_label": "FY99"}, 1), ["FY99", "FY00"])
        self.assertEqual(dcf.year_labels({"first_forecast_label": "NTM"}, 1), ["Y1", "Y2"])
        self.assertEqual(dcf.year_labels({}, 1), ["Y1", "Y2"])


# ---------------------------------------------------------------------------
class PathsAndFade(unittest.TestCase):
    """How the shorthand in an inputs file becomes year-by-year numbers: paths, the fade years,
    scenario defaults - and a check that two different modes agree with each other."""

    def test_ramp_scalar_list(self):
        """The three ways to write a path (one number, a list, a ramp), then the three ways to
        get one wrong: a list of the wrong length, 12 typed for 12%, a ramp with a key missing.
        The bad ones return None and each leaves one message in the problem list P."""
        P = dcf.Problems()
        self.assertEqual(dcf.resolve_path(0.2, 3, "x", P), [0.2, 0.2, 0.2])
        self.assertEqual(dcf.resolve_path([0.1, 0.2, 0.3], 3, "x", P), [0.1, 0.2, 0.3])
        got = dcf.resolve_path({"from": 0.34, "to": 0.36, "years": 3}, 5, "x", P)
        for a, b in zip(got, [0.34, 0.35, 0.36, 0.36, 0.36]):
            self.assertAlmostEqual(a, b, places=12)
        self.assertEqual(dcf.resolve_path({"from": 0.1, "to": 0.3, "years": 1}, 2, "x", P), [0.3, 0.3])
        self.assertEqual(P.items, [])
        self.assertIsNone(dcf.resolve_path([0.1, 0.2], 3, "x", P))
        self.assertIsNone(dcf.resolve_path(12, 3, "x", P))                      # 12 means 12%: rejected
        self.assertIsNone(dcf.resolve_path({"from": 0.1, "to": 0.2}, 3, "x", P))
        self.assertEqual(len(P.items), 3)

    def test_levels_then_growth_then_fade(self):
        """A revenue path in all three stages: one year given as a level (120), two as growth
        rates (20%, 14%), then three fade years in which growth steps evenly down towards the 2%
        terminal rate, and the margin steps evenly up towards its 18% terminal value."""
        raw = inputs("fcf_margin", model={"explicit_years": 3, "fade_years": 3})
        raw["scenarios"][0].update({"revenue": {"base": 100.0, "levels": [120.0], "growth": [0.20, 0.14]},
                                    "fcf_margin": 0.10, "terminal": {"growth": 0.02, "fcf_margin": 0.18}})
        inp = dcf.normalize(raw)
        rows = dcf.project(inp["scenarios"][0], inp)["rows"]
        growth = [r["growth"] for r in rows]
        # explicit: 20% (120/100), 20%, 14%; fade 14% -> 2% in 4 equal steps: 11%, 8%, 5%, then 2% terminal
        for got, want in zip(growth, [0.20, 0.20, 0.14, 0.11, 0.08, 0.05]):
            self.assertAlmostEqual(got, want, places=12)
        self.assertAlmostEqual(rows[-1]["revenue"], 120 * 1.2 * 1.14 * 1.11 * 1.08 * 1.05, places=9)
        # margin holds at 10% then fades to the 18% terminal value in the same four steps
        for got, want in zip([r["fcf_margin"] for r in rows], [0.10, 0.10, 0.10, 0.12, 0.14, 0.16]):
            self.assertAlmostEqual(got, want, places=12)
        proj = dcf.project(inp["scenarios"][0], inp)
        self.assertAlmostEqual(proj["terminal_row"]["fcf_margin"], 0.18, places=12)
        self.assertAlmostEqual(proj["terminal_row"]["revenue"], rows[-1]["revenue"] * 1.02, places=9)

    def test_scenario_defaults_merge(self):
        """Assumptions moved out of the scenario into scenario_defaults must give the same value
        as when they were written in the scenario. The second half checks the other direction:
        a default the scenario overrides (its own flat margin against a default ramp) is
        replaced outright, never blended."""
        raw = inputs("drivers")
        sc = raw["scenarios"][0]
        raw["scenario_defaults"] = {"tax_rate": sc.pop("tax_rate"), "da_pct_revenue": sc.pop("da_pct_revenue"),
                                    "terminal": {"growth": 0.02, "capex_pct_revenue": 0.08},
                                    "revenue": {"base": 100.0}}
        sc["revenue"] = {"growth": [0.10, 0.10]}
        sc["terminal"] = {"growth": 0.02}
        self.assertAlmostEqual(value(raw, 0.10)["operating_value"],
                               value(inputs("drivers"), 0.10)["operating_value"], places=9)
        # a scenario value replaces the default outright (ramps are not merged key by key)
        raw["scenario_defaults"]["ebit_margin"] = {"from": 0.5, "to": 0.6, "years": 2}
        self.assertAlmostEqual(value(raw, 0.10)["operating_value"],
                               value(inputs("drivers"), 0.10)["operating_value"], places=9)

    def test_scenario_can_override_horizon(self):
        """The model says 2 explicit years; this scenario asks for 4 and gets 4."""
        raw = inputs("fcf_margin")
        raw["scenarios"][0].update({"explicit_years": 4, "revenue": {"base": 100.0, "growth": 0.10}})
        inp = dcf.normalize(raw)
        self.assertEqual(dcf.project(inp["scenarios"][0], inp)["n"], 4)

    def test_cross_mode_consistency(self):
        """A drivers scenario's own cash flows, fed back through mode 'direct', give the same value.

        Two routes to one number. If building cash flows and valuing them really are separate
        jobs, the cash flows a drivers model produces can be typed into a direct model and must
        be worth exactly the same - here with ramps, a fade and mid-year timing all in play.
        """
        raw = inputs("drivers", model={"explicit_years": 5, "fade_years": 3, "timing": "mid_year"})
        raw["scenarios"][0].update({"revenue": {"base": 100.0, "growth": {"from": 0.25, "to": 0.12, "years": 5}},
                                    "ebit_margin": {"from": 0.15, "to": 0.25, "years": 4}})
        inp = dcf.normalize(raw)
        proj = dcf.project(inp["scenarios"][0], inp)
        direct = inputs("direct", model={"timing": "mid_year"})
        direct["scenarios"][0].update({"fcf": proj["flows"], "terminal": {"growth": 0.02, "fcf": proj["terminal_fcf"]}})
        self.assertAlmostEqual(value(direct, 0.11)["operating_value"], dcf.value_at(proj, 0.11, inp)["operating_value"],
                               places=8)


# ---------------------------------------------------------------------------
class LegacyReports(unittest.TestCase):
    """The engine reproduces the hand-rolled models behind the October 2026 reports when
    configured the way they were (end-of-year discounting). Reference figures are recomputed
    here with the original scripts' own loops.

    Each test has the same two halves. First the old one-off script's loop is repeated as it
    was written, producing `legacy`, and that is checked against the number the report printed
    (CRM $272.1, NVDA $193.58, GOOGL $307.49) - so we know the loop is a faithful copy. Then the
    same model is written as a dcf.py inputs file, and the engine has to match `legacy` to nine
    decimals. Together they show the new program is a superset of what the old scripts did.

    Names kept from the old scripts: w = discount rate, g = terminal growth, r = revenue (inside
    the loops), pv = running present value, bridge / assets = net cash added at the end.
    Figures are in billions, shares included (0.84 = 840 million shares).
    """

    def test_software_batch_crm_base(self):
        """Salesforce base case, 2026-10-16 report: ten years of revenue x free-cash-flow margin,
        a perpetuity on the last year grown 3%, less $24B net debt, over 0.84B shares = $272.1.
        Maps onto mode fcf_margin."""
        rev0, growth = 48.0, [.10, .10, .09, .08, .07, .06, .05, .04, .03]
        margins = [.26 + i * .003 for i in range(10)]
        w, g, bridge, shares = .10, .03, -24.0, .84
        r, pv, last = rev0, 0.0, None
        for i in range(10):                                   # software-valuation.py, verbatim logic
            if i:
                r *= 1 + growth[i - 1]
            last = r * margins[i]
            pv += last / (1 + w) ** (i + 1)
        legacy = (pv + last * (1 + g) / (w - g) / (1 + w) ** 10 + bridge) / shares
        self.assertAlmostEqual(legacy, 272.1, places=1)       # the figure printed in the CRM report

        raw = inputs("fcf_margin", meta={"units": "billions"}, shares={"count": shares},
                     bridge={"cash_and_investments": 0.0, "debt": 24.0}, model={"explicit_years": 10})
        raw["scenarios"][0].update({"revenue": {"base": 43.0, "levels": [rev0], "growth": growth},
                                    "fcf_margin": margins, "terminal": {"growth": g}})
        self.assertAlmostEqual(value(raw, w)["value_per_share"], legacy, places=9)

    def test_nvda_value_driver_base(self):
        """NVIDIA base case, 2026-10-08 report: revenue given year by year, an EBIT margin sliding
        from 60% to 48%, and a terminal value from the value-driver formula with a 25% return on
        new capital = $193.58. Maps onto mode drivers with terminal method value_driver."""
        revs = [500, 625, 750, 862.5, 948.75, 1024.65, 1086.129, 1140.43545, 1186.052868, 1221.63445404]
        w, g, term, tax, roic, bridge, shares = .10, .03, .48, .18, .25, 23.220, 24.147
        last, pv = 384.884, 0.0
        for i, r in enumerate(revs):                          # valuation_model.py nvda(), verbatim logic
            m = .60 + (term - .60) * i / 9
            fcff = r * m * (1 - tax) + .02 * r - .03 * r - .12 * (r - last)
            pv += fcff / (1 + w) ** (i + 1)
            last = r
        t_fcf = revs[-1] * (1 + g) * term * (1 - tax) * (1 - g / roic)
        legacy = (pv + t_fcf / (w - g) / (1 + w) ** 10 + bridge) / shares
        self.assertAlmostEqual(legacy, 193.583, places=3)     # the figure in the NVDA report

        raw = inputs("drivers", meta={"units": "billions"}, shares={"count": shares},
                     bridge={"cash_and_investments": bridge, "debt": 0.0}, model={"explicit_years": 10})
        raw["scenarios"][0] = {
            "name": "base", "slot": "base", "revenue": {"base": 384.884, "levels": revs},
            "ebit_margin": [.60 + (term - .60) * i / 9 for i in range(10)], "tax_rate": tax,
            "da_pct_revenue": .02, "capex_pct_revenue": .03, "nwc_pct_incremental_revenue": .12,
            "terminal": {"method": "value_driver", "growth": g, "ronic": roic, "ebit_margin": term}}
        self.assertAlmostEqual(value(raw, w)["value_per_share"], legacy, places=9)

    def test_googl_base_cash_flows(self):
        """Alphabet base case, 2026-10-16 report ($307.49): the one place the engine differs from
        the old script on purpose, so the test pins down exactly how.

        The ten forecast cash flows match to nine decimals. The terminal year does not: the old
        script took year ten's cash flow and grew it 3%, which carries year ten's working-capital
        build (sized for 6% growth) into perpetuity. The engine rebuilds the terminal year with
        working capital sized for 3% growth, which comes out a little higher - within 1%.
        Fed the old script's cash flows through mode direct, the engine gives $307.49 exactly.
        """
        growth = [.20, .18, .16, .14, .12, .10, .09, .08, .06]
        margin = [.34, .35] + [.36] * 8
        capex = [.34, .30, .26, .22, .19, .17, .15, .14, .13, .12]
        da = [.08, .09] + [.10] * 8
        w, g, tax, assets, shares, prior = .10, .03, .18, 160.0, 12.4, 445.866
        r, last, pv, flows = 560.0, prior, 0.0, []
        for i in range(10):                                   # googl-valuation.py, verbatim logic
            if i:
                r *= 1 + growth[i - 1]
            fcf = r * margin[i] * (1 - tax) + r * da[i] - r * capex[i] - .05 * (r - last)
            pv += fcf / (1 + w) ** (i + 1)
            flows.append(fcf)
            last = r
        legacy = (pv + flows[-1] * (1 + g) / (w - g) / (1 + w) ** 10 + assets) / shares
        self.assertAlmostEqual(legacy, 307.49, places=2)      # the figure in the GOOGL report

        raw = inputs("drivers", meta={"units": "billions"}, shares={"count": shares},
                     bridge={"cash_and_investments": assets, "debt": 0.0}, model={"explicit_years": 10})
        raw["scenarios"][0] = {
            "name": "base", "slot": "base", "revenue": {"base": prior, "levels": [560.0], "growth": growth},
            "ebit_margin": margin, "tax_rate": tax, "da_pct_revenue": da, "capex_pct_revenue": capex,
            "nwc_pct_incremental_revenue": .05, "terminal": {"growth": g}}
        inp = dcf.normalize(raw)
        proj = dcf.project(inp["scenarios"][0], inp)
        for got, want in zip(proj["flows"], flows):           # identical explicit cash flows
            self.assertAlmostEqual(got, want, places=9)
        # The engine's terminal year sizes working capital for 3% growth rather than carrying
        # year ten's build, so it is slightly higher than "final-year FCF x 1.03".
        rev_t = r * (1 + g)
        fcf_t = rev_t * .36 * (1 - tax) + rev_t * .10 - rev_t * .12 - .05 * (rev_t - r)
        self.assertAlmostEqual(proj["terminal_fcf"], fcf_t, places=9)
        want = (pv + fcf_t / (w - g) / (1 + w) ** 10 + assets) / shares
        self.assertAlmostEqual(dcf.value_at(proj, w, inp)["value_per_share"], want, places=9)
        self.assertLess(abs(want / legacy - 1), 0.01)
        # Fed through mode 'direct' the legacy figure is reproduced exactly.
        direct = inputs("direct", meta={"units": "billions"}, shares={"count": shares},
                        bridge={"cash_and_investments": assets, "debt": 0.0})
        direct["scenarios"][0].update({"fcf": flows, "terminal": {"growth": g}})
        self.assertAlmostEqual(value(direct, w)["value_per_share"], legacy, places=9)


# ---------------------------------------------------------------------------
class Dilution(unittest.TestCase):
    """From equity value to value per share, when the share count itself depends on the answer.

    Most tests here call dcf.per_share_value(equity, shares, basis) directly with equity of 1,000
    and 100 shares, so the undiluted value is 10.00 a share and every effect is easy to see.
    It returns (value per share, diluted share count, principal of the notes that converted).
    """

    def test_options_treasury_stock_method(self):
        """10 options struck at 5.00. In the money, so they dilute - but only by their
        in-the-money part. The value V has to satisfy V x (100 + 10 x (1 - 5/V)) = 1,000, which
        rearranges to 110 V = 1,050, so V = 9.545."""
        sh = {"count": 100.0, "options": [{"count": 10.0, "strike": 5.0}], "convertibles": []}
        v, n, conv = dcf.per_share_value(1000.0, sh, "firm")
        # V (100 + 10 (1 - 5/V)) = 1000  =>  110 V = 1050
        self.assertAlmostEqual(v, 1050.0 / 110.0, places=9)
        self.assertAlmostEqual(n, 100 + 10 * (1 - 5 / v), places=9)
        self.assertEqual(conv, 0.0)

    def test_out_of_the_money_options_do_not_dilute(self):
        """Options struck at 50 on a 10.00 share will not be exercised: no dilution at all."""
        sh = {"count": 100.0, "options": [{"count": 10.0, "strike": 50.0}], "convertibles": []}
        v, n, _ = dcf.per_share_value(1000.0, sh, "firm")
        self.assertAlmostEqual(v, 10.0, places=9)
        self.assertAlmostEqual(n, 100.0, places=9)

    def test_convertible_in_the_money_converts(self):
        """A 200 note convertible at 8.00 into 25 shares, with the share worth 10.00: it converts.
        The 200 stops being debt (equity 1,000 -> 1,200) and 25 shares appear (100 -> 125):
        1,200 / 125 = 9.60, still above 8.00, so converting was indeed the right assumption."""
        sh = {"count": 100.0, "options": [], "convertibles": [{"principal": 200.0, "conversion_price": 8.0, "shares": 25.0}]}
        v, n, conv = dcf.per_share_value(1000.0, sh, "firm")       # equity is already net of the 200 as debt
        self.assertAlmostEqual(v, 1200.0 / 125.0, places=9)
        self.assertEqual((n, conv), (125.0, 200.0))

    def test_convertible_out_of_the_money_stays_debt(self):
        """The same note convertible at 12.00, above the 10.00 share value: holders keep the
        bond. It stays debt, no shares are added, and the value stays 10.00."""
        sh = {"count": 100.0, "options": [], "convertibles": [{"principal": 200.0, "conversion_price": 12.0, "shares": 200 / 12}]}
        v, n, conv = dcf.per_share_value(1000.0, sh, "firm")
        self.assertAlmostEqual(v, 10.0, places=9)
        self.assertEqual((n, conv), (100.0, 0.0))

    def test_convertible_between_the_two_values_converts(self):
        """The awkward case: a conversion price (9.50) between the value before conversion (10.00)
        and the value after it (9.913). The answer has to be self-consistent - converted, and
        still worth more than the conversion price once converted."""
        # 10.00 unconverted > 9.50 strike, and the converted value (9.913) is still above the strike
        sh = {"count": 100.0, "options": [], "convertibles": [{"principal": 200.0, "conversion_price": 9.5, "shares": 200 / 9.5}]}
        v, _, conv = dcf.per_share_value(1000.0, sh, "firm")
        self.assertAlmostEqual(v, 1200.0 / (100 + 200 / 9.5), places=9)
        self.assertEqual(conv, 200.0)

    def test_fixed_point_with_options_and_two_convertibles(self):
        """Everything at once: two option grants and two notes, some in the money and some not.
        No hand formula here; instead the result must be consistent with itself - the value
        equals (equity + converted principal) / the share count that value implies - with only
        the 7.00 note converting and only the 4.00 options diluting."""
        sh = {"count": 100.0, "options": [{"count": 8.0, "strike": 4.0}, {"count": 5.0, "strike": 30.0}],
              "convertibles": [{"principal": 150.0, "conversion_price": 7.0, "shares": 150 / 7.0},
                               {"principal": 300.0, "conversion_price": 20.0, "shares": 15.0}]}
        v, n, conv = dcf.per_share_value(1200.0, sh, "firm")
        self.assertAlmostEqual(v, (1200.0 + conv) / n, places=9)
        self.assertEqual(conv, 150.0)                                  # only the 7.00 note is in the money
        self.assertAlmostEqual(n, 100 + 8 * (1 - 4 / v) + 150 / 7.0, places=9)

    def test_negative_equity_is_not_diluted(self):
        """When equity is worthless nothing is in the money: -500 over the plain 100 shares."""
        sh = {"count": 100.0, "options": [{"count": 10.0, "strike": 5.0}], "convertibles": []}
        self.assertEqual(dcf.per_share_value(-500.0, sh, "firm"), (-5.0, 100.0, 0.0))

    def test_end_to_end_convertible_default_principal_over_price(self):
        """The same logic through a whole valuation. Debt of 400 is entirely one convertible at
        5.00; the business is worth far more per share than that, so the note converts: the debt
        disappears from the bridge and 400 / 5 = 80 new shares appear (the default share count
        when the file gives none)."""
        raw = inputs("direct", bridge={"cash_and_investments": 0.0, "debt": 400.0},
                     shares={"count": 100.0, "convertibles": [{"principal": 400.0, "conversion_price": 5.0}]})
        op = 100 / 1.1 + 110 / 1.21 + (110 * 1.02 / 0.08) / 1.21
        v = value(raw, 0.10)
        self.assertAlmostEqual(v["value_per_share"], op / 180.0, places=9)   # debt gone, 80 new shares
        self.assertAlmostEqual(v["converted_principal"], 400.0, places=9)


# ---------------------------------------------------------------------------
class DiscountRate(unittest.TestCase):
    """CAPM, WACC, and how the anchor is rounded onto the grid to give r* and r_hi."""

    def disc(self, raw):
        """Run only the discount-rate step. Returns (its results, the flags it raised)."""
        flags = dcf.Flags()
        return dcf.compute_discount(dcf.normalize(raw), flags), flags

    def test_capm_and_wacc(self):
        """Cost of equity 4.3% + 1.3 x 5% + 1% = 11.8%. Market cap 20 x 100 shares = 2,000 against
        500 of debt gives weights of 80% / 20%, and debt at 7% costs 7% x (1 - 21%) after tax."""
        raw = inputs("direct", market={"price": 20.0}, bridge={"cash_and_investments": 0.0, "debt": 500.0},
                     discount_rate={"risk_free": 0.043, "equity_risk_premium": 0.05, "beta": 1.3,
                                    "additional_premium": 0.01, "pre_tax_cost_of_debt": 0.07, "tax_rate": 0.21})
        d, _ = self.disc(raw)
        ke = 0.043 + 1.3 * 0.05 + 0.01
        self.assertAlmostEqual(d["cost_of_equity"], ke, places=12)
        self.assertAlmostEqual(d["debt_weight"], 500 / 2500, places=12)
        self.assertAlmostEqual(d["wacc"], 0.8 * ke + 0.2 * 0.07 * 0.79, places=12)
        self.assertEqual(d["anchor_name"], "WACC")

    def test_in_the_money_convertible_counts_as_equity_in_the_weights(self):
        """At a 20.00 share price a note convertible at 10.00 is equity in all but name. For the
        WACC weights its 20 shares join the market cap (120 x 20) and its 200 leaves debt (300)."""
        raw = inputs("direct", market={"price": 20.0}, bridge={"cash_and_investments": 0.0, "debt": 500.0},
                     shares={"count": 100.0, "convertibles": [{"principal": 200.0, "conversion_price": 10.0}]},
                     discount_rate={"pre_tax_cost_of_debt": 0.07, "tax_rate": 0.21})
        d, _ = self.disc(raw)
        self.assertAlmostEqual(d["market_cap"], 20.0 * 120.0, places=9)
        self.assertAlmostEqual(d["debt_for_weights"], 300.0, places=9)

    def test_equity_basis_anchors_on_cost_of_equity(self):
        """Cash flows after interest belong to shareholders alone, so they are discounted at the
        cost of equity however much debt there is. No WACC is computed at all."""
        raw = inputs("eps", bridge={"cash_and_investments": 0.0, "debt": 900.0})
        d, _ = self.disc(raw)
        self.assertEqual(d["anchor_name"], "cost of equity")
        self.assertAlmostEqual(d["anchor"], 0.04 + 1.2 * 0.05, places=12)
        self.assertIsNone(d["wacc"])

    def primary(self, ke, grid=None, **extra):
        """A debt-free company whose cost of equity - and so its anchor - is exactly `ke`
        (beta 1, a 5% risk premium, risk-free rate ke - 5%). Returns the discount-rate results
        and the set of flag codes raised, so the tests below can ask "anchor x -> r* y?"."""
        dr = {"risk_free": ke - 0.05, "equity_risk_premium": 0.05, "beta": 1.0}
        if grid:
            dr["grid"] = grid
        dr.update(extra)
        d, flags = self.disc(inputs("direct", discount_rate=dr))
        return d, {f["code"] for f in flags.items}

    def test_primary_rate_is_nearest_grid_rate_ties_up(self):
        """Each triple is (anchor, expected r*, expected r_hi) on the default 10/12/14 grid.
        10.48% and 9.49% round to 10%; 11% is exactly half-way and goes UP to 12%, while 10.99%
        stays at 10%; 13% is another tie and goes to 14%, whose r_hi is one step past the grid."""
        for anchor, r_star, r_hi in ((0.1048, 0.10, 0.12), (0.0949, 0.10, 0.12), (0.11, 0.12, 0.14),
                                     (0.1099, 0.10, 0.12), (0.125, 0.12, 0.14), (0.13, 0.14, 0.16), (0.14, 0.14, 0.16)):
            d, _ = self.primary(anchor)
            self.assertEqual((d["primary_rate"], d["sensitivity_rate"]), (r_star, r_hi), anchor)
            self.assertIn(r_hi, d["rates"])

    def test_grid_extends_upward_never_rounding_far_below_the_anchor(self):
        """A risky company's 16.5% must not be "rounded" to the grid's top rate of 14%. The grid
        grows a step to 16%; a 19% anchor takes it on to 20% (a tie between 18 and 20, upward).
        14.9% is nearer 14% than 16%, so nothing is added."""
        d, c = self.primary(0.165)
        self.assertEqual(d["grid"], [0.10, 0.12, 0.14, 0.16])
        self.assertEqual((d["primary_rate"], d["sensitivity_rate"]), (0.16, 0.18))
        self.assertIn("N-GRID-EXTENDED", c)
        d, _ = self.primary(0.19)
        self.assertEqual((d["primary_rate"], d["sensitivity_rate"]), (0.20, 0.22))
        d, c = self.primary(0.149)                             # within a point of the top: no extension
        self.assertEqual(d["primary_rate"], 0.14)
        self.assertNotIn("N-GRID-EXTENDED", c)

    def test_low_anchor_is_held_at_the_floor(self):
        """The grid does NOT grow downward: a 7.5% anchor is held at the 10% floor, with a note.
        To use 8% the analyst must put it on the grid deliberately - then 7.5% rounds to it."""
        d, c = self.primary(0.075)
        self.assertEqual(d["primary_rate"], 0.10)
        self.assertIn("N-GRID-FLOOR", c)
        d, c = self.primary(0.075, grid=[0.08, 0.10, 0.12, 0.14])
        self.assertEqual((d["primary_rate"], d["sensitivity_rate"]), (0.08, 0.10))
        self.assertNotIn("N-GRID-FLOOR", c)

    def test_override_needs_a_reason_and_is_flagged(self):
        """r* may be set by hand (primary_rate) - a rule-based or investor-chosen required
        return - but not silently: without a reason the file is rejected, and with one the
        override is still reported as a warning. r_hi follows as the next grid rate above it."""
        with self.assertRaises(dcf.InputError):
            self.primary(0.10, primary_rate=0.11)
        d, c = self.primary(0.10, primary_rate=0.11, primary_rate_reason="regulated utility")
        self.assertEqual((d["primary_rate"], d["sensitivity_rate"]), (0.11, 0.12))
        self.assertIn(0.11, d["rates"])
        self.assertIn("W-RATE-OVERRIDE", c)

    def test_wacc_needs_weights_and_cost_of_debt(self):
        """A company with debt cannot get a WACC by default. It needs something to weight debt
        against equity by (a price, or debt_to_capital) and a cost for that debt; each missing
        piece is rejected in turn, and with all three the WACC is 70% x 10% + 30% x 8% x 0.75."""
        raw = inputs("direct", bridge={"cash_and_investments": 0.0, "debt": 500.0})
        with self.assertRaises(dcf.InputError):            # debt, but neither a price nor debt_to_capital
            self.disc(raw)
        raw["discount_rate"]["debt_to_capital"] = 0.3
        with self.assertRaises(dcf.InputError):            # weights, but no cost of debt
            self.disc(raw)
        raw["discount_rate"].update({"pre_tax_cost_of_debt": 0.08, "tax_rate": 0.25})
        d, _ = self.disc(raw)
        self.assertAlmostEqual(d["wacc"], 0.7 * 0.10 + 0.3 * 0.08 * 0.75, places=12)

    def test_forward_values_do_not_read_the_price(self):
        """Run the same company with no price, then at 0.50, 7.00 and 400.00 a share: every
        scenario value at every rate, the rates themselves and the PWV must be identical.

        Note what makes this hold: the inputs give debt_to_capital, so the WACC weights do not
        come from the market cap. Without it the weights - and through them, possibly r* - would
        move with the price, which is the one price channel the engine has (see compute_discount).
        """
        raw = inputs("drivers", bridge={"cash_and_investments": 50.0, "debt": 400.0},
                     shares={"count": 100.0, "options": [{"count": 5.0, "strike": 1.0}]},
                     discount_rate={"debt_to_capital": 0.25, "pre_tax_cost_of_debt": 0.07, "tax_rate": 0.21})
        raw["scenarios"] = three(raw["scenarios"][0], scale_key="ebit_margin")
        without = run(raw)
        for price in (0.5, 7.0, 400.0):
            with_price = run(dict(raw, market={"price": price}))
            self.assertEqual(with_price["discount"]["rates"], without["discount"]["rates"])
            for a, b in zip(with_price["results"], without["results"]):
                for r in without["discount"]["rates"]:
                    self.assertEqual(a["values"][r]["value_per_share"], b["values"][r]["value_per_share"])
            self.assertEqual(with_price["handoff"]["pwv_primary"], without["handoff"]["pwv_primary"])
        self.assertIsNone(without["implied"])
        self.assertIn("N-NO-PRICE", codes(without))


# ---------------------------------------------------------------------------
class ReverseDcf(unittest.TestCase):
    """The reverse DCF: "given the price, what would have to be true?"

    The main device in this group is the round trip. Value a scenario; call that value the
    market price; then ask the solver what the price implies. It has to hand back the very
    assumptions the scenario was built on - 13% growth, no change in margin, the modelled
    terminal cash flow. If the forward and reverse models disagreed in any detail (the bridge,
    the options, the convertible, mid-year timing, the fade) the round trip would not close.
    """

    def model(self, **over):
        """A deliberately awkward company, so that the round trip has to get everything right:
        net debt, options, a convertible note, mid-year timing, a consensus level in year 1, a
        margin ramp and two fade years. Growth after year 1 is 13% - the number to be recovered."""
        raw = inputs("drivers", market={"price": 1.0},
                     bridge={"cash_and_investments": 300.0, "debt": 500.0},
                     shares={"count": 100.0, "options": [{"count": 6.0, "strike": 2.0}],
                             "convertibles": [{"principal": 200.0, "conversion_price": 6.0}]},
                     discount_rate={"pre_tax_cost_of_debt": 0.07, "tax_rate": 0.21, "debt_to_capital": 0.2},
                     model={"timing": "mid_year", "explicit_years": 6, "fade_years": 2})
        raw["scenarios"][0].update({"revenue": {"base": 1000.0, "levels": [1150.0], "growth": 0.13},
                                    "ebit_margin": {"from": 0.18, "to": 0.24, "years": 6},
                                    "terminal": {"growth": 0.025}})
        raw.update(over)
        return raw

    def priced_at_own_value(self, raw, r):
        """Set the market price to the scenario's own value at rate r and run the analysis.
        Returns (the results, the reverse-DCF answers for the base case at that rate)."""
        raw["market"] = {"price": value(raw, r)["value_per_share_raw"]}
        res = run(raw)
        return res, res["implied"]["f2"][0]["by_rate"][r]

    def test_round_trips_at_the_model_value(self):
        """Priced at its own value, the scenario must imply exactly its own assumptions."""
        for r in (0.10, 0.12, 0.14):
            res, row = self.priced_at_own_value(self.model(), r)
            self.assertTrue(row["growth"]["solved"])
            # implied growth is the 13% that was put in, leading to the same revenue at the horizon...
            self.assertAlmostEqual(row["growth"]["x"], 0.13, places=6)
            self.assertAlmostEqual(row["growth"]["level_n"] / row["growth"]["base_level_n"], 1.0, places=5)
            self.assertTrue(row["growth"]["value_rises_with_growth"])
            # ...and margins need not move at all: the terminal margin stays at the modelled 24%
            self.assertAlmostEqual(row["margin"]["x"], 0.0, places=6)
            self.assertAlmostEqual(row["margin"]["terminal_margin"], 0.24, places=6)
            # closed form, through the bridge, the options and the convertible
            self.assertAlmostEqual(row["terminal"]["required"] / row["terminal"]["modelled"], 1.0, places=7)

    def test_growth_window_excludes_fixed_levels(self):
        """Year 1 is pinned to a level (1,150 - "consensus"), so the years whose growth the
        solver may change run from year 2 to year 6."""
        res, _ = self.priced_at_own_value(self.model(), 0.12)
        self.assertEqual(res["implied"]["f2"][0]["growth_window"], (2, 6))

    def test_higher_price_needs_more(self):
        """At one and a half times the model's value, the price asks more of everything: faster
        growth, a wider margin, a larger terminal cash flow. And the solved growth and margin,
        fed back into the forward model, really do reproduce that price."""
        raw = self.model()
        raw["market"] = {"price": value(raw, 0.12)["value_per_share_raw"] * 1.5}
        row = run(raw)["implied"]["f2"][0]["by_rate"][0.12]
        self.assertGreater(row["growth"]["x"], 0.13)
        self.assertGreater(row["margin"]["x"], 0.0)
        self.assertGreater(row["terminal"]["required"], row["terminal"]["modelled"])
        # and the solved inputs really do reproduce the price
        self.assertAlmostEqual(value(raw, 0.12, ov={"constant_growth": row["growth"]["x"]})["value_per_share_raw"],
                               raw["market"]["price"], places=6)
        self.assertAlmostEqual(value(raw, 0.12, ov={"margin_shift": row["margin"]["x"]})["value_per_share_raw"],
                               raw["market"]["price"], places=6)

    def test_exit_multiple_requirement(self):
        """When the scenario ends in an exit multiple, the "terminal requirement" is stated as
        the multiple the price needs. Priced at its own value, that is the modelled 11x."""
        raw = self.model()
        raw["scenarios"][0]["terminal"] = {"growth": 0.025, "method": "exit_multiple", "exit_multiple": 11.0,
                                           "exit_metric": "ebitda"}
        _, row = self.priced_at_own_value(raw, 0.12)
        self.assertEqual(row["terminal"]["kind"], "exit_multiple")
        self.assertAlmostEqual(row["terminal"]["required"], 11.0, places=7)

    def test_direct_mode_scale(self):
        """Mode direct has no growth rate or margin to solve for, so the answer is given as the
        multiple of every cash flow the price requires: 1.00x when priced at its own value."""
        raw = inputs("direct", market={"price": 1.0}, bridge={"cash_and_investments": 100.0, "debt": 0.0})
        raw["market"] = {"price": value(raw, 0.12)["value_per_share_raw"]}
        row = run(raw)["implied"]["f2"][0]["by_rate"][0.12]
        self.assertAlmostEqual(row["flow_scale"]["x"], 1.0, places=6)

    def test_eps_mode_growth(self):
        """The growth round trip in EPS terms (9%). Mode eps has no margin, so no margin answer
        is offered."""
        raw = inputs("eps", model={"explicit_years": 5})
        raw["scenarios"][0]["eps"] = {"base": 4.0, "levels": [4.6], "growth": 0.09}
        _, row = self.priced_at_own_value(raw, 0.12)
        self.assertAlmostEqual(row["growth"]["x"], 0.09, places=6)
        self.assertNotIn("margin", row)

    def test_no_growth_rate_reaches_the_price_is_reported_not_raised(self):
        """A business spending 40% of revenue on capex against a 10% margin burns cash however
        fast it grows. At a price of 500 nothing in the search range works - and that has to come
        back as a finding printed in the report ("none - price is above every value..."), not a crash."""
        raw = inputs("drivers", market={"price": 500.0}, model={"explicit_years": 5})
        raw["scenarios"][0].update({"revenue": {"base": 100.0, "growth": 0.3}, "ebit_margin": 0.10,
                                    "capex_pct_revenue": 0.40, "da_pct_revenue": 0.10})
        res = run(raw)
        g = res["implied"]["f2"][0]["by_rate"][res["discount"]["primary_rate"]]["growth"]
        self.assertFalse(g["solved"])
        self.assertIn("above every value", g["reason"])
        self.assertIn("none - price is above every value", dcf.render_markdown(res))

    def test_value_destroying_growth_is_marked(self):
        """Each new dollar of revenue ties up $1.40 of working capital and earns 7.5 cents a year
        after tax. The solver still finds the growth rate at which value equals the price (10%),
        but it must be marked - a double dagger in the report - so that nobody reads it as a
        hurdle the company has to clear: here, growing FASTER makes the business worth less."""
        # Growth costs more capital than it earns: value falls as growth rises.
        raw = inputs("drivers", model={"explicit_years": 5})
        raw["scenarios"][0].update({"revenue": {"base": 100.0, "growth": 0.05}, "ebit_margin": 0.10,
                                    "capex_pct_revenue": 0.05, "nwc_pct_incremental_revenue": 1.4})
        raw["market"] = {"price": value(raw, 0.10, ov={"constant_growth": 0.10})["value_per_share_raw"]}
        res = run(raw)
        g = res["implied"]["f2"][0]["by_rate"][0.10]["growth"]
        self.assertTrue(g["solved"])
        self.assertFalse(g["value_rises_with_growth"])
        self.assertIn("‡", dcf.render_markdown(res))

    def test_extra_scenarios_marked_reverse_are_solved_too(self):
        """The reverse DCF always runs on the base case; a scenario marked "reverse": true (here
        the bull) gets its own set of answers as well."""
        raw = self.model()
        raw["scenarios"] = three(raw["scenarios"][0], scale_key=None)
        raw["scenarios"][2]["ebit_margin"] = 0.30
        raw["scenarios"][0]["ebit_margin"] = 0.12
        raw["scenarios"][2]["reverse"] = True
        res = run(raw)
        self.assertEqual([f["scenario"] for f in res["implied"]["f2"]], ["base", "bull"])

    def test_f1_gordon_inversion(self):
        """The valuation framework's own worked example. Price $930 less $18 of net cash a share
        = $912 of operating value. At r 12%, g 3% and 75% conversion the price needs sustained
        EPS of 912 x (0.12 - 0.03) / (0.75 x 1.03) = $106.25. Then the same at 10% and 14%, and
        under mid-year timing, where the answer is smaller by (1.12)^0.5."""
        raw = inputs("eps", market={"price": 930.0}, bridge={"cash_and_investments": 18.0, "debt": 0.0},
                     shares={"count": 1.0}, discount_rate={"risk_free": 0.04, "equity_risk_premium": 0.05, "beta": 1.6},
                     implied={"fcf_conversion": 0.75, "terminal_growth": 0.03,
                              "eps_anchors": {"forward_consensus": 100.0, "mid_cycle": 8.0}})
        raw["model"]["basis"] = "firm"
        res = run(raw)
        f1 = {row["rate"]: row["implied_eps"] for row in res["implied"]["f1"]["rows"]}
        self.assertAlmostEqual(f1[0.12], 912 * 0.09 / 0.7725, places=9)          # the framework's worked example
        self.assertAlmostEqual(f1[0.10], 912 * 0.07 / 0.7725, places=9)
        self.assertAlmostEqual(f1[0.14], 912 * 0.11 / 0.7725, places=9)
        raw["model"]["timing"] = "mid_year"                                       # same timing as the forward model
        f1 = {row["rate"]: row["implied_eps"] for row in run(raw)["implied"]["f1"]["rows"]}
        self.assertAlmostEqual(f1[0.12], 912 * 0.09 / 0.7725 / 1.12 ** 0.5, places=9)

    def test_f1_is_the_inverse_of_the_forward_model(self):
        """A flat-growth EPS stream priced by the engine implies its own starting EPS.

        EPS of 5.00 growing 3% for ever is valued by the forward model, and that value is used as
        the price. F1 then has to answer "5.00" - under either timing convention. This is why F1
        applies the model's own timing instead of the textbook formula alone.
        """
        for timing in ("end_year", "mid_year"):
            raw = inputs("eps", model={"timing": timing, "explicit_years": 3},
                         implied={"fcf_conversion": 0.8, "terminal_growth": 0.03})
            raw["scenarios"][0].update({"eps": {"base": 5.0, "growth": 0.03}, "terminal": {"growth": 0.03}})
            raw["market"] = {"price": value(raw, 0.12)["value_per_share"]}
            f1 = {row["rate"]: row["implied_eps"] for row in run(raw)["implied"]["f1"]["rows"]}
            self.assertAlmostEqual(f1[0.12], 5.0, places=9)

    def test_f3_mid_cycle_multiples(self):
        """Operating value of $912 a share divided by through-cycle multiples: at 12x and 14x the
        price is paying for mid-cycle EPS of $76 and $65 - the figures in the worked example."""
        raw = inputs("eps", market={"price": 930.0}, bridge={"cash_and_investments": 18.0, "debt": 0.0},
                     shares={"count": 1.0})
        raw["model"]["basis"] = "firm"
        rows = run(raw)["implied"]["f3"]["rows"]
        self.assertEqual([r["multiple"] for r in rows], [10.0, 12.0, 14.0, 16.0])
        self.assertAlmostEqual(rows[1]["implied_eps"], 912 / 12.0, places=9)     # $76, as in the worked example
        self.assertAlmostEqual(rows[2]["implied_eps"], 912 / 14.0, places=9)     # $65

    def test_f5_market_implied_probability(self):
        """p = (price - bear) / (bull - bear): the weight on the bull case that makes the
        expected value equal the price. Then the two cases where no such weight exists: a price
        above the bull value (p over 100%) and one below the bear value (p under 0%)."""
        raw = inputs("direct", market={"price": 12.0})
        raw["scenarios"] = three(raw["scenarios"][0], bear=0.5, bull=2.0, scale_key="fcf")
        res = run(raw)
        r = res["discount"]["primary_rate"]
        row = [x for x in res["implied"]["f5"]["rows"] if x["rate"] == r][0]
        pb, pu = row["pv_bear"], row["pv_bull"]
        self.assertAlmostEqual(row["p_bull"], (12.0 - pb) / (pu - pb), places=12)
        self.assertEqual(row["state"], "ok")
        raw["market"] = {"price": pu * 1.2}
        row = [x for x in run(raw)["implied"]["f5"]["rows"] if x["rate"] == r][0]
        self.assertGreater(row["p_bull"], 1.0)
        self.assertEqual(row["state"], "price above the bull PV")
        self.assertTrue(row["above_every_scenario"])
        raw["market"] = {"price": pb * 0.5}
        row = [x for x in run(raw)["implied"]["f5"]["rows"] if x["rate"] == r][0]
        self.assertLess(row["p_bull"], 0.0)
        self.assertTrue(row["below_every_scenario"])

    def test_market_frame_converts_in_the_money_notes(self):
        """Reading a market price backwards into operating value. At 10.00 a share the options
        (struck at 2.00) and the note (convertible at 6.00) are both in the money: shares are
        100 + 4.8 + 33.33, and the note's 200 is no longer debt, so net cash is 300 - 500 + 200
        = 0. At 4.00 the note is still a bond, and net cash is -200."""
        raw = self.model()
        inp = dcf.normalize(raw)
        fr = dcf.market_frame(inp, 10.0)                       # above the 6.00 conversion price and 2.00 strike
        n = 100 + 6 * (1 - 2 / 10.0) + 200 / 6.0
        self.assertAlmostEqual(fr["diluted_shares"], n, places=9)
        self.assertAlmostEqual(fr["net_cash"], 300 - 500 + 200, places=9)
        self.assertAlmostEqual(fr["operating_value"], 10.0 * n - 0.0, places=9)
        fr = dcf.market_frame(inp, 4.0)                        # below the conversion price
        self.assertAlmostEqual(fr["net_cash"], -200.0, places=9)


# ---------------------------------------------------------------------------
class HandOff(unittest.TestCase):
    """The numbers passed on to the Entry & Exit Plan: the bear / base / bull values at r* and at
    r_hi, the probability-weighted value (PWV) and return (PWR), and the checks on the three
    slots - including the rule that a cyclical's scenario must come back to mid-cycle."""

    def test_pwv_pwr_and_both_rates(self):
        """Bear, base and bull are 0.4x, 1x and 1.9x the standard cash flows, weighted 20/50/30.
        The hand-off must carry exactly those three values at 10% and at 12%, their weighted
        averages, and PWR = PWV / price - 1."""
        raw = inputs("direct", market={"price": 10.0})
        raw["scenarios"] = three(raw["scenarios"][0], bear=0.4, bull=1.9, weights=(0.2, 0.5, 0.3), scale_key="fcf")
        res = run(raw)
        ho = res["handoff"]
        r, rh = ho["primary_rate"], ho["sensitivity_rate"]
        self.assertEqual((r, rh), (0.10, 0.12))
        for tag, rate in (("at_primary", r), ("at_sensitivity", rh)):
            for i, slot in enumerate(("bear", "base", "bull")):
                self.assertEqual(ho[tag][slot], value(raw, rate, idx=i)["value_per_share"])
        p = ho["at_primary"]
        self.assertAlmostEqual(ho["pwv_primary"], 0.2 * p["bear"] + 0.5 * p["base"] + 0.3 * p["bull"], places=12)
        h = ho["at_sensitivity"]
        self.assertAlmostEqual(ho["pwv_sensitivity"], 0.2 * h["bear"] + 0.5 * h["base"] + 0.3 * h["bull"], places=12)
        self.assertAlmostEqual(ho["pwr"], ho["pwv_primary"] / 10.0 - 1, places=12)
        self.assertTrue(ho["ordered"])
        self.assertEqual(ho["names"], {"bear": "bear", "base": "base", "bull": "bull"})

    def test_context_scenarios_do_not_enter_the_hand_off(self):
        """A fourth scenario with no slot ("blue sky", worth far more than the bull) is valued
        and shown, but it must not become the bull or leak into the PWV."""
        raw = inputs("direct", market={"price": 10.0})
        scs = three(raw["scenarios"][0], bear=0.4, bull=1.9, scale_key="fcf")
        extra = copy.deepcopy(raw["scenarios"][0])
        extra.update({"name": "blue sky", "slot": None, "fcf": [900.0, 990.0]})
        extra.pop("slot")
        raw["scenarios"] = scs + [extra]
        res = run(raw)
        self.assertEqual(len(res["results"]), 4)
        self.assertEqual(res["handoff"]["names"]["bull"], "bull")
        self.assertAlmostEqual(res["handoff"]["pwv_primary"],
                               sum(w * res["handoff"]["at_primary"][s] for s, w in
                                   (("bear", 0.25), ("base", 0.5), ("bull", 0.25))), places=12)

    def test_misordered_slots_are_flagged(self):
        """A "bear" with 1.5x the cash flows and a "bull" with half of them: the values come out
        upside down, and the run says the slots are mis-assigned."""
        raw = inputs("direct")
        scs = three(raw["scenarios"][0], bear=1.5, bull=0.5, scale_key="fcf")
        raw["scenarios"] = scs
        res = run(raw)
        self.assertFalse(res["handoff"]["ordered"])
        self.assertIn("W-SLOT-ORDER", codes(res, "WARN"))

    def test_missing_slots_or_weights(self):
        """A single scenario gives no hand-off at all (W-NO-SLOTS). Three slotted scenarios
        without weights hand over their values, but no PWV can be formed (W-NO-WEIGHTS), and
        the report says "PWV: not computed" rather than inventing default weights."""
        res = run(inputs("direct"))
        self.assertFalse(res["handoff"]["complete"])
        self.assertIn("W-NO-SLOTS", codes(res, "WARN"))
        raw = inputs("direct")
        raw["scenarios"] = three(raw["scenarios"][0], scale_key="fcf")
        for s in raw["scenarios"]:
            del s["weight"]
        res = run(raw)
        self.assertTrue(res["handoff"]["complete"])
        self.assertNotIn("pwv_primary", res["handoff"])
        self.assertIn("W-NO-WEIGHTS", codes(res, "WARN"))
        self.assertIn("PWV: not computed", dcf.render_markdown(res))

    def test_cyclical_admissibility(self):
        """Mid-cycle margin 20%. A 12% bear and a 20% base pass. A bull that holds a 35% margin
        for ever capitalises the boom: inadmissible, and not allowed to sit in the bull slot.
        A bull that peaks at 35% and 30% but ends at 22% - within 10% of mid-cycle - is fine."""
        raw = inputs("drivers", model={"cyclical": True, "mid_cycle_ebit_margin": 0.20})
        raw["scenarios"] = three(raw["scenarios"][0], scale_key=None)
        raw["scenarios"][0]["ebit_margin"] = 0.12
        raw["scenarios"][2]["ebit_margin"] = 0.35                # peak margin carried into perpetuity
        res = run(raw)
        status = {s["name"]: s["admissibility"]["status"] for s in res["results"]}
        self.assertEqual(status, {"bear": "admissible", "base": "admissible", "bull": "inadmissible"})
        self.assertLessEqual({"W-CYCLICAL-INADMISSIBLE", "W-BULL-SLOT-INADMISSIBLE"}, codes(res, "WARN"))
        # a bull that peaks but reverts to within tolerance of mid-cycle is admissible
        raw["scenarios"][2]["ebit_margin"] = [0.35, 0.30]
        raw["scenarios"][2]["terminal"] = {"growth": 0.02, "ebit_margin": 0.22}
        res = run(raw)
        self.assertEqual(res["results"][2]["admissibility"]["status"], "admissible")
        self.assertNotIn("W-BULL-SLOT-INADMISSIBLE", codes(res))

    def test_cyclical_without_anchor_is_unverified(self):
        """Marked cyclical, but with no mid-cycle figure to test against: the scenario is
        reported as unverified - a warning - rather than waved through."""
        raw = inputs("drivers", model={"cyclical": True})
        res = run(raw)
        self.assertEqual(res["results"][0]["admissibility"]["status"], "unverified")
        self.assertIn("W-CYCLICAL-UNVERIFIED", codes(res, "WARN"))

    def test_cyclical_eps_anchor(self):
        """The same rule in EPS terms, against a mid-cycle EPS of 5.00 at the horizon. A terminal
        EPS of 4.94 passes; EPS compounding 50% a year does not; and stating a normalised
        terminal EPS of 5.20 (within the 10% tolerance) brings that scenario back inside."""
        raw = inputs("eps", model={"cyclical": True, "mid_cycle_eps_at_horizon": 5.0})
        self.assertEqual(run(raw)["results"][0]["admissibility"]["status"], "admissible")     # 4.84 x 1.02 = 4.94
        raw["scenarios"][0]["eps"] = {"base": 4.0, "growth": [0.5, 0.5]}
        self.assertEqual(run(raw)["results"][0]["admissibility"]["status"], "inadmissible")
        raw["scenarios"][0]["terminal"] = {"growth": 0.02, "eps": 5.2}                         # normalised terminal
        self.assertEqual(run(raw)["results"][0]["admissibility"]["status"], "admissible")


# ---------------------------------------------------------------------------
class FlagsAndQuality(unittest.TestCase):
    """Every warning has two jobs: to fire when its condition is met, and to stay quiet when it
    is not. Most tests here do both - break one thing, see the flag; repair it, see it go.

    A flag is identified by its code. codes(res, "WARN") is the set of warning codes raised in
    a run, so `assertIn("W-TV-SHARE", codes(res, "WARN"))` reads "this warning was raised".
    """

    def test_clean_model_is_robust(self):
        """The control case: a sensible ten-year model (growth easing from 8% to 4%, margins and
        capex in line with the history supplied, three properly ordered scenarios) must raise
        no warning at all and be labelled robust. If a new check starts crying wolf, this fails."""
        raw = inputs("drivers", market={"price": 2.0}, model={"explicit_years": 10},
                     history={"periods": ["FY24", "FY25"], "revenue": [90.0, 100.0], "ebit": [17.0, 19.5],
                              "capex": [7.5, 8.0], "roic": [0.14, 0.15]})
        raw["scenarios"][0].update({"revenue": {"base": 100.0, "growth": {"from": 0.08, "to": 0.04, "years": 10}},
                                    "terminal": {"growth": 0.02, "capex_pct_revenue": 0.075}})
        raw["scenarios"] = three(raw["scenarios"][0], bear=0.8, bull=1.1, scale_key="ebit_margin")
        res = run(raw)
        self.assertEqual(codes(res, "WARN"), set(), [f for f in res["flags"] if f["level"] == "WARN"])
        self.assertEqual(res["quality"]["label"], "robust")

    def test_terminal_growth_cap(self):
        """3.5% perpetual growth is above the default 3% cap: warned. Raise the cap to 4% (a
        deliberate choice in the inputs) and the same growth passes."""
        raw = inputs("direct")
        raw["scenarios"][0]["terminal"]["growth"] = 0.035
        self.assertIn("W-TG-CAP", codes(run(raw), "WARN"))
        raw["model"]["terminal_growth_cap"] = 0.04
        self.assertNotIn("W-TG-CAP", codes(run(raw)))

    def test_terminal_value_share_and_directional_quality(self):
        """Cash flows of 1 and then 100: almost all of the value sits beyond the forecast. The
        scenario is warned about, and the whole valuation is labelled directional, with the reason."""
        raw = inputs("direct")
        raw["scenarios"][0]["fcf"] = [1.0, 100.0]
        res = run(raw)
        self.assertIn("W-TV-SHARE", codes(res, "WARN"))
        self.assertEqual(res["quality"]["label"], "directional")
        self.assertTrue(any("terminal value" in x for x in res["quality"]["reasons"]))

    def test_thin_spread(self):
        """A low-beta company on a low grid: cost of equity 4% + 0.5 x 5% = 6.5%, which rounds to
        r* = 6%. With 3% terminal growth the perpetuity divides by only 3 points - too thin."""
        raw = inputs("direct", discount_rate={"grid": [0.06, 0.08, 0.10], "beta": 0.5})
        raw["scenarios"][0]["terminal"]["growth"] = 0.03
        res = run(raw)
        self.assertEqual(res["discount"]["primary_rate"], 0.06)
        self.assertIn("W-THIN-SPREAD", codes(res, "WARN"))

    def test_growth_cliff_and_its_cure(self):
        """Growth of 25% in the last forecast year, then 2% for ever, with nothing in between: a
        cliff. Adding five fade years lets growth glide down instead, and the warning goes."""
        raw = inputs("fcf_margin")
        raw["scenarios"][0]["revenue"] = {"base": 100.0, "growth": [0.30, 0.25]}
        self.assertIn("W-GROWTH-CLIFF", codes(run(raw), "WARN"))
        raw["model"]["fade_years"] = 5
        self.assertNotIn("W-GROWTH-CLIFF", codes(run(raw)))

    def test_terminal_reinvestment_checks(self):
        """Is the terminal year's growth paid for? Three settings of capex against D&A of 5%:
          4%          less than depreciation while still growing 2%: growth from nothing
          5.2%        net reinvestment of 0.2% of revenue against profit of 15%: to produce 2%
                      growth that sliver would have to earn 150% - implausibly high
          9% + NWC    28% of profit reinvested for 2% growth is a 7% return - below the 10%
                      discount rate, so growth destroys value. Legitimate; a note, not a warning."""
        raw = inputs("drivers")
        raw["scenarios"][0].update({"capex_pct_revenue": 0.04, "nwc_pct_incremental_revenue": 0.0})
        self.assertIn("W-NO-REINVESTMENT", codes(run(raw), "WARN"))            # capex below D&A, growing 2%
        raw["scenarios"][0].update({"capex_pct_revenue": 0.052})
        res = run(raw)                                                         # net reinvestment 0.2% of revenue
        self.assertIn("W-RONIC-HIGH", codes(res, "WARN"))
        inp = dcf.normalize(raw)
        d = dcf.project(inp["scenarios"][0], inp)["diag"]
        nopat, net = 123.42 * 0.2 * 0.75, 123.42 * 0.002
        self.assertAlmostEqual(d["implied_ronic"], 0.02 / (net / nopat), places=9)
        raw["scenarios"][0].update({"capex_pct_revenue": 0.09, "nwc_pct_incremental_revenue": 0.1})
        res = run(raw)
        self.assertNotIn("W-RONIC-HIGH", codes(res))
        self.assertIn("N-RONIC-BELOW-RATE", codes(res, "NOTE"))                # 2% / 28% reinvestment = 7% < 10%

    def test_value_driver_low_ronic_note(self):
        """The same note when the return on new capital is typed in (value_driver, 7%) rather
        than implied by the capex ratios."""
        raw = inputs("drivers")
        raw["scenarios"][0]["terminal"] = {"method": "value_driver", "growth": 0.02, "ronic": 0.07}
        self.assertIn("N-RONIC-BELOW-RATE", codes(run(raw), "NOTE"))

    def test_terminal_step_up(self):
        """A 20% margin through the forecast and 30% in perpetuity: the improvement appears only
        where nobody can inspect it. Warned until the forecast itself gets (nearly) there."""
        raw = inputs("drivers")
        raw["scenarios"][0]["terminal"] = {"growth": 0.02, "ebit_margin": 0.30}
        self.assertIn("W-TERMINAL-STEP-UP", codes(run(raw), "WARN"))
        # Four fade years carry the margin up to 28% by the last modelled year - still 2 points
        # short of the terminal 30%, so the warning stands.
        raw["model"]["fade_years"] = 4
        self.assertIn("W-TERMINAL-STEP-UP", codes(run(raw), "WARN"))
        # With the forecast itself reaching 29.5%, the terminal year is only half a point higher.
        raw["scenarios"][0]["ebit_margin"] = [0.20, 0.295]
        raw["model"]["fade_years"] = 0
        self.assertNotIn("W-TERMINAL-STEP-UP", codes(run(raw)))

    def test_history_benchmarks(self):
        """The assumptions against the company's own record. History here: margins of 10% and 12%,
        capex at 20% of revenue. The standard company assumes a 20% margin and 8% capex, so three
        warnings fire: terminal margin above anything achieved, an 8-point jump in year 1, capex
        under half its historical level. Margin 13% and capex 19% clear all three. With no
        history supplied there is nothing to compare with, and a note says so."""
        hist = {"periods": ["FY24", "FY25"], "revenue": [90.0, 100.0], "ebit": [9.0, 12.0], "capex": [18.0, 20.0],
                "roic": [0.05, 0.06]}
        raw = inputs("drivers", history=hist)
        got = codes(run(raw), "WARN")
        self.assertLessEqual({"W-MARGIN-ABOVE-HISTORY", "W-MARGIN-JUMP", "W-CAPEX-BELOW-HISTORY"}, got)
        raw["scenarios"][0].update({"ebit_margin": 0.13, "capex_pct_revenue": 0.19})
        got = codes(run(raw))
        self.assertFalse({"W-MARGIN-ABOVE-HISTORY", "W-MARGIN-JUMP", "W-CAPEX-BELOW-HISTORY"} & got)
        self.assertIn("N-NO-HISTORY", codes(run(inputs("drivers"))))

    def test_history_checks_are_notes_outside_the_base_case(self):
        """A bull case is supposed to go beyond the record, so "margin above history" is only a
        NOTE for the bull (26% against a best of 19%). The year-1 jump stays a WARN in any
        scenario, because that one usually means a mis-typed margin rather than optimism."""
        hist = {"periods": ["FY24", "FY25"], "revenue": [90.0, 100.0], "ebit": [16.0, 19.0]}
        raw = inputs("drivers", history=hist)
        raw["scenarios"] = three(raw["scenarios"][0], bear=0.8, bull=1.3, scale_key="ebit_margin")
        res = run(raw)
        flags = {(f["code"], f["scenario"]) for f in res["flags"]}
        self.assertIn(("N-MARGIN-ABOVE-HISTORY", "bull"), flags)                # 26% vs best 19%
        self.assertIn(("W-MARGIN-JUMP", "bull"), flags)
        self.assertNotIn(("W-MARGIN-ABOVE-HISTORY", "base"), flags)             # 20% is within two points

    def test_units_mismatch(self):
        """The company is worth about 13.4 a share. Against a "price" of 0.01 that is 1,300 times
        too much - not a bargain but a units mistake - and the run says so. Against 15.00: quiet."""
        raw = inputs("direct", market={"price": 0.01})
        self.assertIn("W-UNITS", codes(run(raw), "WARN"))
        raw = inputs("direct", market={"price": 15.0})
        self.assertNotIn("W-UNITS", codes(run(raw)))

    def test_funding_gap(self):
        """Cash flows of -80, -40, +300: the running total bottoms out at -120. With 50 of cash
        the company would run dry and need outside money the model does not charge for (warned);
        with 150 it gets through on its own."""
        raw = inputs("direct", bridge={"cash_and_investments": 50.0, "debt": 0.0})
        raw["scenarios"][0]["fcf"] = [-80.0, -40.0, 300.0]
        res = run(raw)
        self.assertIn("W-FUNDING-GAP", codes(res, "WARN"))
        self.assertAlmostEqual(res["results"][0]["values"][0.10]["funding_trough"], 120.0, places=9)
        raw["bridge"]["cash_and_investments"] = 150.0
        self.assertNotIn("W-FUNDING-GAP", codes(run(raw)))

    def test_stale_balance_sheet(self):
        """Valued on 2026-01-01. A balance sheet from 2025-06-30 is 185 days old - a newer filing
        must exist - and is warned about; one from 2025-09-30 (93 days) is the latest available."""
        raw = inputs("direct", meta={"balance_sheet_date": "2025-06-30"})
        self.assertIn("W-STALE-BALANCE-SHEET", codes(run(raw), "WARN"))
        raw = inputs("direct", meta={"balance_sheet_date": "2025-09-30"})
        self.assertNotIn("W-STALE-BALANCE-SHEET", codes(run(raw)))

    def test_missing_sources_and_labels(self):
        """No "sources" section is a warning (every input needs a source before it reaches a
        memo); a scenario without an authorship label is a note."""
        raw = inputs("direct")
        del raw["sources"]
        del raw["scenarios"][0]["label"]
        got = codes(run(raw))
        self.assertLessEqual({"W-NO-SOURCES", "N-NO-LABEL"}, got)

    def test_exit_multiple_checks(self):
        """Selling the business at 30x EBITDA when mature peers trade at 9x: warned twice - the
        multiple is richer than the peers', and it implies 8% growth for ever. At 6x both checks
        pass (it implies 2.4% growth)."""
        raw = inputs("drivers", model={"mature_peer_multiple": {"metric": "ebitda", "value": 9.0}})
        raw["scenarios"][0]["terminal"] = {"growth": 0.02, "method": "exit_multiple", "exit_multiple": 30.0,
                                           "exit_metric": "ebitda"}
        got = codes(run(raw), "WARN")
        self.assertLessEqual({"W-EXIT-IMPLIED-GROWTH", "W-TERMINAL-MULTIPLE"}, got)
        raw["scenarios"][0]["terminal"]["exit_multiple"] = 6.0
        self.assertFalse({"W-EXIT-IMPLIED-GROWTH", "W-TERMINAL-MULTIPLE"} & codes(run(raw)))

    def test_gordon_terminal_richer_than_mature_peers(self):
        """The peer check applies to a perpetuity too: the standard company's terminal value is
        6.0x its year-2 EBITDA, which is above a mature-peer multiple of 4x."""
        raw = inputs("drivers", model={"mature_peer_multiple": {"metric": "ebitda", "value": 4.0}})
        self.assertIn("W-TERMINAL-MULTIPLE", codes(run(raw), "WARN"))

    def test_eps_firm_basis_with_material_net_cash(self):
        """Mode eps on a firm basis adds net cash per share - correct only if the EPS path
        excludes interest. With 10.00 of net cash on a 50.00 share (20%) a mistake there would
        be material, so the run warns; with 1.00 (2%) it would be noise, and it does not."""
        raw = inputs("eps", market={"price": 50.0}, bridge={"cash_and_investments": 1000.0, "debt": 0.0})
        raw["model"]["basis"] = "firm"
        self.assertIn("W-EPS-BASIS", codes(run(raw), "WARN"))
        raw["bridge"]["cash_and_investments"] = 100.0
        self.assertNotIn("W-EPS-BASIS", codes(run(raw)))

    def test_negative_terminal_cash_flow(self):
        """A business still burning cash in its last forecast year has a negative perpetuity. The
        arithmetic goes through, but the number means nothing, and the run says so."""
        raw = inputs("direct")
        raw["scenarios"][0]["fcf"] = [50.0, -10.0]
        self.assertIn("W-TERMINAL-NEGATIVE", codes(run(raw), "WARN"))

    def test_hypergrowth_note(self):
        """Growth of 220% is accepted - it happens - but pointed out, since 2.2 is also what
        "2.2%" looks like when someone forgets to divide by 100."""
        raw = inputs("fcf_margin", model={"fade_years": 6})
        raw["scenarios"][0]["revenue"] = {"base": 100.0, "growth": [2.2, 0.9]}
        self.assertIn("N-HYPERGROWTH", codes(run(raw), "NOTE"))


# ---------------------------------------------------------------------------
class Sensitivity(unittest.TestCase):
    """The sensitivity table, and common sense: does value move the right way with each input?"""

    def test_rate_by_terminal_growth_grid(self):
        """Columns are terminal growth one point lower, half a point lower, as modelled and half
        a point higher (1%, 1.5%, 2%, 2.5%); rows are the rates. Every cell must equal a separate
        valuation with that growth rate, values must rise along each row (more growth) and fall
        down each column (a higher discount rate)."""
        raw = inputs("drivers")
        res = run(raw)
        sens = res["sensitivity"]
        self.assertEqual(sens["columns"], [0.01, 0.015, 0.02, 0.025])
        self.assertEqual([row["rate"] for row in sens["rows"]], res["discount"]["rates"])
        for row in sens["rows"]:
            for g, got in zip(sens["columns"], row["values"]):
                self.assertAlmostEqual(got, value(raw, row["rate"], ov={"terminal_growth": g})["value_per_share"], places=12)
            self.assertEqual(row["values"], sorted(row["values"]))             # more terminal growth, more value
        centre = [row["values"][2] for row in sens["rows"]]
        self.assertEqual(centre, sorted(centre, reverse=True))                 # higher rate, less value

    def test_exit_multiple_grid(self):
        """When the scenario ends in an exit multiple (10x), the columns vary the multiple
        instead of growth: 8x to 12x."""
        raw = inputs("drivers")
        raw["scenarios"][0]["terminal"] = {"growth": 0.02, "method": "exit_multiple", "exit_multiple": 10.0,
                                           "exit_metric": "ebitda"}
        sens = run(raw)["sensitivity"]
        self.assertEqual(sens["axis"], "exit multiple")
        self.assertEqual(sens["columns"], [8.0, 9.0, 10.0, 11.0, 12.0])

    def test_monotonic_in_the_obvious_directions(self):
        """Common sense, as a test. A lower discount rate, a wider margin and faster growth must
        each raise the value; more tax, more capex and more working capital must each lower it.
        A sign error anywhere in the build shows up here even if the magnitudes look plausible."""
        raw = inputs("drivers", model={"explicit_years": 8, "fade_years": 2, "timing": "mid_year"})
        raw["scenarios"][0]["revenue"] = {"base": 100.0, "growth": 0.12}
        base = value(raw, 0.11)["value_per_share"]
        self.assertGreater(value(raw, 0.10)["value_per_share"], base)
        self.assertGreater(value(raw, 0.11, ov={"margin_shift": 0.01})["value_per_share"], base)
        self.assertGreater(value(raw, 0.11, ov={"constant_growth": 0.14})["value_per_share"], base)
        for key, worse in (("tax_rate", 0.30), ("capex_pct_revenue", 0.10), ("nwc_pct_incremental_revenue", 0.2)):
            alt = copy.deepcopy(raw)
            alt["scenarios"][0][key] = worse
            self.assertLess(value(alt, 0.11)["value_per_share"], base, key)


# ---------------------------------------------------------------------------
class Validation(unittest.TestCase):
    """Bad inputs must be refused - and with a message that says where the problem is and how to
    fix it. Each test takes a valid file, damages it in one specific way, and checks that the
    list of problems contains the expected wording. Nothing is valued in this group."""

    def problems(self, raw):
        """Check that `raw` is rejected, and return every problem message joined into one string,
        so a test can look for a phrase in it with assertIn."""
        with self.assertRaises(dcf.InputError) as ctx:
            dcf.normalize(raw)
        return " | ".join(ctx.exception.problems)

    def test_template_is_refused_until_edited(self):
        """What `dcf.py template` prints is full of invented numbers. With its "_template" marker
        still in place it must not run."""
        self.assertIn("still the template", self.problems(dcf.template("drivers")))

    def test_all_templates_are_otherwise_valid(self):
        """...and with the marker removed, each of the four examples must run, come out ordered
        bear < base < bull, and raise no warning: they are there to show what a clean file looks
        like. (subTest tries all four modes and reports each separately, instead of stopping at
        the first one that fails.)"""
        for mode in dcf.MODES:
            with self.subTest(mode=mode):
                tpl = dcf.template(mode)
                tpl.pop("_template")
                res = run(tpl)
                self.assertTrue(res["handoff"]["ordered"])
                self.assertEqual(codes(res, "WARN"), set(), res["flags"])

    def test_unknown_keys_are_errors_with_a_suggestion(self):
        """A misspelt key is an error, not something to ignore - in a scenario ("capex_pct"), in
        the bridge ("net_debt") or inside a terminal block - and the nearest valid name is offered."""
        raw = inputs("drivers")
        raw["scenarios"][0]["capex_pct"] = 0.1
        self.assertIn("unknown key 'capex_pct' (did you mean 'capex_pct_revenue'?)", self.problems(raw))
        raw = inputs("drivers")
        raw["bridge"]["net_debt"] = 5
        self.assertIn("unknown key 'net_debt'", self.problems(raw))
        raw = inputs("drivers")
        raw["scenarios"][0]["terminal"]["terminal_growth"] = 0.02
        self.assertIn("unknown key 'terminal_growth'", self.problems(raw))

    def test_comment_keys_are_ignored_everywhere(self):
        """A key beginning with "_" is a comment at every level of the file, and changes nothing."""
        raw = inputs("drivers")
        raw["_note"] = "x"
        raw["meta"]["_c"] = "x"
        raw["scenarios"][0]["_c"] = "x"
        raw["scenarios"][0]["terminal"]["_c"] = "x"
        raw["scenarios"][0]["revenue"]["_c"] = "x"
        self.assertAlmostEqual(value(raw, 0.10)["operating_value"], value(inputs("drivers"), 0.10)["operating_value"])

    def test_percentages_entered_as_whole_numbers(self):
        """The commonest slip: 20 for a 20% margin, 25 for tax, 3 for growth, 4.3 for the
        risk-free rate, [10, 12, 14] for the grid. Each must be refused as "looks like a
        percentage". Each entry in the list is (where the field lives, the bad value); the inner
        loop walks down to the field and plants the value. Revenue growth is the exception -
        2.5 could honestly mean +250% - so there only the absurd (25 = +2,500%) is refused."""
        for path, val in ((("scenarios", 0, "ebit_margin"), 20), (("scenarios", 0, "tax_rate"), 25),
                          (("scenarios", 0, "terminal", "growth"), 3), (("discount_rate", "risk_free"), 4.3),
                          (("discount_rate", "equity_risk_premium"), 5), (("discount_rate", "grid"), [10, 12, 14])):
            raw = inputs("drivers")
            node = raw
            for p in path[:-1]:
                node = node[p]
            node[path[-1]] = val
            self.assertIn("percentage", self.problems(raw), path)
        raw = inputs("drivers")
        raw["scenarios"][0]["revenue"]["growth"] = [25, 20]
        self.assertIn("allowed maximum", self.problems(raw))

    def test_terminal_growth_must_clear_the_lowest_rate(self):
        """5.5% growth against a 6% rate leaves half a point under the perpetuity: refused."""
        raw = inputs("direct", discount_rate={"grid": [0.06, 0.08]})
        raw["scenarios"][0]["terminal"]["growth"] = 0.055
        self.assertIn("at least 1 point below", self.problems(raw))

    def test_slots_and_weights(self):
        """The rules for the scenarios as a set, broken one at a time: weights that add up to
        110%; two scenarios in the base slot; a weight on two of the three; a name used twice;
        a slot called "central"."""
        raw = inputs("direct")
        raw["scenarios"] = three(raw["scenarios"][0], weights=(0.3, 0.5, 0.3), scale_key="fcf")
        self.assertIn("weights sum to 1.1000", self.problems(raw))
        raw["scenarios"][2]["slot"] = "base"
        self.assertIn("more than one scenario is assigned to the 'base' slot", self.problems(raw))
        raw = inputs("direct")
        raw["scenarios"] = three(raw["scenarios"][0], scale_key="fcf")
        del raw["scenarios"][1]["weight"]
        self.assertIn("every slotted scenario or to none", self.problems(raw))
        raw = inputs("direct")
        raw["scenarios"] = three(raw["scenarios"][0], scale_key="fcf")
        raw["scenarios"][1]["name"] = "bear"
        self.assertIn("used more than once", self.problems(raw))
        raw = inputs("direct")
        raw["scenarios"][0]["slot"] = "central"
        self.assertIn("is not one of bear, base, bull", self.problems(raw))

    def test_mode_specific_requirements(self):
        """Each mode's own rules, broken one at a time: mode eps must state its basis;
        value_driver needs mode drivers, and a return on new capital above growth; fcf_margin
        must say whether SBC has been deducted; an SBC path belongs only with a non-GAAP margin,
        and a non-GAAP margin must have one; an exit multiple can only be applied to a line the
        mode models; mode direct has no fade."""
        raw = inputs("eps")
        del raw["model"]["basis"]
        self.assertIn("needs an explicit basis", self.problems(raw))
        raw = inputs("fcf_margin")
        raw["scenarios"][0]["terminal"] = {"method": "value_driver", "growth": 0.02, "ronic": 0.2}
        self.assertIn("only mode 'drivers' models", self.problems(raw))
        raw = inputs("drivers")
        raw["scenarios"][0]["terminal"] = {"method": "value_driver", "growth": 0.02, "ronic": 0.02}
        self.assertIn("must exceed terminal growth", self.problems(raw))
        raw = inputs("fcf_margin")
        del raw["scenarios"][0]["sbc_deducted"]
        self.assertIn("'sbc_deducted' must be stated", self.problems(raw))
        raw = inputs("drivers")
        raw["scenarios"][0]["sbc_pct_revenue"] = 0.05
        self.assertIn("only used when ebit_margin_basis is 'non_gaap'", self.problems(raw))
        raw = inputs("drivers")
        raw["scenarios"][0]["ebit_margin_basis"] = "non_gaap"
        self.assertIn("missing 'sbc_pct_revenue'", self.problems(raw))
        raw = inputs("drivers")
        raw["scenarios"][0]["terminal"] = {"growth": 0.02, "method": "exit_multiple", "exit_multiple": 10,
                                           "exit_metric": "eps"}
        self.assertIn("is not one of ebitda, ebit, nopat, fcf, revenue", self.problems(raw))
        raw = inputs("direct", model={"fade_years": 2})
        self.assertIn("not available in mode 'direct'", self.problems(raw))

    def test_structure_errors(self):
        """Malformed files, one defect each: a growth list of the wrong length; more levels than
        forecast years; no horizon; debt left out; a whole section missing; no scenarios; a date
        in the wrong format; a growth rate applied to a loss; a mode that does not exist."""
        raw = inputs("drivers")
        raw["scenarios"][0]["revenue"]["growth"] = [0.1]
        self.assertIn("expected 2 values", self.problems(raw))
        raw = inputs("drivers")
        raw["scenarios"][0]["revenue"] = {"base": 100.0, "levels": [110.0, 120.0, 130.0]}
        self.assertIn("'levels' has 3 values but the explicit period is 2 years", self.problems(raw))
        raw = inputs("drivers")
        del raw["model"]["explicit_years"]
        self.assertIn("explicit_years is not set", self.problems(raw))
        raw = inputs("drivers")
        del raw["bridge"]["debt"]
        self.assertIn("missing required number 'debt'", self.problems(raw))
        raw = inputs("drivers")
        del raw["shares"]
        self.assertIn("missing required section 'shares'", self.problems(raw))
        raw = inputs("drivers")
        raw["scenarios"] = []
        self.assertIn("non-empty list", self.problems(raw))
        raw = inputs("drivers")
        raw["meta"]["valuation_date"] = "11/11/2026"
        self.assertIn("not a YYYY-MM-DD date", self.problems(raw))
        raw = inputs("eps")
        raw["scenarios"][0]["eps"] = {"base": -1.0, "growth": [0.1, 0.1]}
        self.assertIn("non-positive starting level", self.problems(raw))
        raw = inputs("drivers")
        raw["model"]["mode"] = "dcf"
        self.assertIn("is not one of", self.problems(raw))

    def test_every_problem_is_reported_at_once(self):
        """Four unrelated mistakes in one file (a margin of 20, an unknown key, a beta of 9, no
        ticker) come back as four messages from a single run - not one per attempt."""
        raw = inputs("drivers")
        raw["scenarios"][0]["ebit_margin"] = 20
        raw["scenarios"][0]["capex"] = 1
        raw["discount_rate"]["beta"] = 9
        raw["meta"].pop("ticker")
        with self.assertRaises(dcf.InputError) as ctx:
            dcf.normalize(raw)
        self.assertEqual(len(ctx.exception.problems), 4, ctx.exception.problems)

    def test_eps_can_start_from_a_loss(self):
        """An EPS path may begin with losses (-2.00 last year, -0.50 next year) provided explicit
        levels carry it into profit before growth rates take over. It must then value and print
        normally, with the undefined growth rates shown as n/a."""
        raw = inputs("eps", model={"explicit_years": 4, "fade_years": 2})
        raw["scenarios"][0]["eps"] = {"base": -2.0, "levels": [-0.5, 1.0], "growth": [0.5, 0.3]}
        res = run(raw)
        self.assertGreater(res["results"][0]["values"][0.10]["value_per_share"], 0)
        dcf.render_markdown(res)


# ---------------------------------------------------------------------------
class Output(unittest.TestCase):
    """What the program hands back: the Markdown report, the JSON results file, and its
    behaviour as a command."""

    def full(self):
        """The drivers example from dcf.py's template with its "this is a template" marker
        removed: a complete file with three scenarios, a history, options and a convertible."""
        tpl = dcf.template("drivers")
        tpl.pop("_template")
        return tpl

    def test_markdown_carries_the_numbers_the_memo_needs(self):
        """The report must contain its main sections and the actual figures of the hand-off (the
        base value at r*, the bear value at r_hi, the PWV), plus the stub and terminal-year
        labels. And "nan" must appear nowhere: an undefined figure has to print as n/a. (The word
        "finance" is removed before that check because it happens to contain "nan".)"""
        res = run(self.full())
        md = dcf.render_markdown(res)
        ho = res["handoff"]
        for needle in ("## DCF value", "## 1. Discount rate", "## 3. Scenario values", "## 5. Sensitivity",
                       "## 6. Implied expectations", "## 7. Hand-off to the Entry & Exit Plan", "## 8. Model flags",
                       f"${ho['at_primary']['base']:,.2f}", f"${ho['at_sensitivity']['bear']:,.2f}",
                       f"PWV ${ho['pwv_primary']:,.2f}", "Ordering check: bear < base < bull at r\\* - holds",
                       "FY2027 (stub 0.63)", "Terminal year (FY2037)"):
            self.assertIn(needle, md)
        self.assertNotIn("nan", md.lower().replace("finance", ""))

    def test_results_json_is_complete_and_deterministic(self):
        """Two runs on the same inputs must give identical JSON, character for character: no
        timestamps, no randomness. The file must have all its sections, show its rates as text
        keys ("0.1000", ...), and carry the base case's ten yearly rows."""
        a = json.dumps(dcf.results_json(run(self.full())), sort_keys=True)
        b = json.dumps(dcf.results_json(run(self.full())), sort_keys=True)
        self.assertEqual(a, b)
        out = json.loads(a)
        for key in ("program", "conventions", "discount_rate", "scenarios", "sensitivity", "handoff", "quality",
                    "implied", "flags"):
            self.assertIn(key, out)
        self.assertEqual(out["program"]["version"], dcf.VERSION)
        self.assertEqual(set(out["scenarios"][0]["values"]), {"0.1000", "0.1200", "0.1400"})
        self.assertEqual(len(out["scenarios"][1]["rows"]), 10)

    def test_every_mode_renders(self):
        """All four modes, each with a market price and without one, must produce a report and a
        JSON file without error. Without a price the WACC has no market cap to weight by, so
        debt_to_capital is supplied instead."""
        for mode in dcf.MODES:
            tpl = dcf.template(mode)
            tpl.pop("_template")
            for price in (tpl["market"]["price"], None):
                t = copy.deepcopy(tpl)
                if price is None:
                    del t["market"]
                    t["discount_rate"]["debt_to_capital"] = 0.05
                res = run(t)
                md = dcf.render_markdown(res)
                self.assertIn("## 7. Hand-off", md)
                json.dumps(dcf.results_json(res))

    def test_cli(self):
        """The program run as a real command, in a temporary folder that is deleted afterwards.
        In order: `template` prints an example, which `check` then refuses (exit code 2); a good
        file passes `check`; `run` writes its two output files and prints the same report it
        saved; a bad file exits with 2, gives the reason on the error stream, prints no report
        and writes nothing; a missing file exits with 2; given one good file and one bad one,
        the good one is still processed; and `selftest` passes."""
        with tempfile.TemporaryDirectory() as tmp:
            # Two inputs files: a valid one, and the same with a margin typed as 23 instead of 0.23.
            good, bad, tpl = (os.path.join(tmp, n) for n in ("good.json", "bad.json", "tpl.json"))
            with open(good, "w") as fh:
                json.dump(self.full(), fh)
            broken = self.full()
            broken["scenarios"][1]["ebit_margin"] = 23
            with open(bad, "w") as fh:
                json.dump(broken, fh)

            def call(*args):
                """Run dcf.py as a separate process and capture what it prints and its exit code.
                -I is Python's isolated mode: ignore environment settings and the current folder,
                so the test exercises the script exactly as it is shipped."""
                return subprocess.run([sys.executable, "-I", DCF, *args], capture_output=True, text=True)

            p = call("template", "--mode", "eps")
            self.assertEqual(p.returncode, 0)
            self.assertTrue(json.loads(p.stdout)["_template"])
            with open(tpl, "w") as fh:
                fh.write(p.stdout)
            self.assertEqual(call("check", tpl).returncode, 2)

            p = call("check", good)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertIn("inputs are valid", p.stdout)

            out = os.path.join(tmp, "out")
            p = call("run", good, "--out-dir", out)
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertIn("# DCF - XMPL", p.stdout)
            with open(os.path.join(out, "XMPL-dcf-report.md"), encoding="utf-8") as fh:
                self.assertEqual(fh.read().strip(), p.stdout.strip())
            with open(os.path.join(out, "XMPL-dcf-results.json"), encoding="utf-8") as fh:
                self.assertEqual(json.load(fh)["meta"]["ticker"], "XMPL")

            p = call("run", bad)
            self.assertEqual(p.returncode, 2)
            self.assertIn("looks like a percentage", p.stderr)
            self.assertEqual(p.stdout, "")
            self.assertFalse(os.path.exists(os.path.join(tmp, "XMPL-dcf-report.md")))

            self.assertEqual(call("run", os.path.join(tmp, "missing.json")).returncode, 2)
            p = call("run", good, bad, "--quiet")                       # one bad file does not hide the good one
            self.assertEqual(p.returncode, 2)
            self.assertTrue(os.path.exists(os.path.join(tmp, "XMPL-dcf-report.md")))
            self.assertEqual(call("selftest").returncode, 0)


# Run as `python3 test_dcf.py`: find every test class above and run all of its test_... methods.
if __name__ == "__main__":
    unittest.main(verbosity=1)
