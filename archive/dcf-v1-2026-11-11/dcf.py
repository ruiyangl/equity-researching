#!/usr/bin/env python3
"""
dcf.py - deterministic DCF and reverse-DCF engine for the equity-researching skill.

WHAT IT DOES
------------
The analyst supplies evidence and judgment in one JSON "inputs file": the balance
sheet, the share count, the discount-rate inputs, and a few scenarios for the
business (how fast it grows, what margin it earns, what it has to reinvest). This
program does every piece of arithmetic from there - the same way every time - and
reports the checks that failed. It makes no forecast of its own: run it twice on
the same inputs and the output is identical to the last digit.
Standard library only (Python 3.8+); nothing to install.

HOW TO RUN IT
-------------

    python3 dcf.py template [--mode drivers|fcf_margin|eps|direct] > XYZ-dcf-inputs.json
    python3 dcf.py check XYZ-dcf-inputs.json
    python3 dcf.py run   XYZ-dcf-inputs.json [--out-dir DIR]
    python3 dcf.py selftest

`run` prints a Markdown report and writes <TICKER>-dcf-report.md and
<TICKER>-dcf-results.json next to the inputs file (or into --out-dir).
Exit codes: 0 = valued (flags may be present), 2 = inputs rejected, 1 = internal error.

HOW THE PROGRAM FLOWS  (the sections of this file come in the same order)
-------------------------------------------------------------------------
    main()                      reads the command line
      run_file()                one inputs file in, one report out
        load_file()             read the JSON text
        normalize()             STEP 1  check every field; expand shorthand into year-by-year lists
        analyze()               STEP 2  all of the finance:
            compute_discount()      cost of equity (CAPM) -> WACC -> choose r* and r_hi
            project()               one scenario -> a cash flow per forecast year + a "terminal year"
            value_at()              discount those at one rate -> operating value -> equity -> per share
            scenario_flags()        sanity checks on that scenario
            ...then, inside analyze() itself: the sensitivity table, the reverse DCF
               (implied_block), the bear/base/bull hand-off and the robust/directional verdict
        render_markdown()       STEP 3  turn the results into the report you read
        results_json()                  and into the machine-readable copy saved beside it

FOUR IDEAS THAT EXPLAIN MOST OF THE CODE
----------------------------------------
1. Building cash flows and valuing them are separate jobs. project() never sees a
   discount rate; value_at() never sees how the cash flows were built. That is why one
   scenario can be valued at every rate on the grid, and why four different ways of
   building cash flows (the "modes") share a single valuation routine.
2. "What if" questions are asked with overrides, not copies. The sensitivity table and
   the reverse-DCF solvers call project() again with a small dict named `ov`
   ({"terminal_growth": 0.025}, {"constant_growth": 0.14}, ...) that replaces one
   assumption for that one call. The scenario itself is never modified.
3. Errors stop; flags inform. An input that makes the arithmetic meaningless (no share
   count, 12 typed where 0.12 was meant, a misspelt key) raises InputError and nothing is
   valued. An assumption that makes the answer fragile (terminal value is 80% of the
   total; growth falls off a cliff into perpetuity) still produces a value, with a WARN
   or NOTE attached that the memo has to fix or disclose.
4. Scenario values come from the business inputs, not from the market price. The price
   is used in three places only: the "% vs price" columns, the reverse-DCF block, and -
   unless discount_rate.debt_to_capital is given - the debt/equity weights inside the
   WACC. That last one is the only route by which the price can reach a value: it can
   tip r* from one grid rate to the next when the anchor sits near the midpoint.

GLOSSARY  (finance term, what it means here, and its name in the code)
----------------------------------------------------------------------
FCF (free cash flow)   Cash produced in a year after the business has reinvested in itself:
                       EBIT - cash tax + D&A - capex - increase in working capital.
                       "Unlevered" = before interest, so it belongs to lenders and
                       shareholders together. In the code: row["fcf"], proj["flows"].
EBIT                   Operating profit - here always AFTER stock-based compensation (SBC),
                       which is treated as a real cost.
NOPAT                  EBIT minus the tax on it (net operating profit after tax).
D&A, capex, NWC        Depreciation & amortisation (non-cash, so added back); capital
                       expenditure; net working capital (d_nwc = the cash absorbed when
                       working capital grows with revenue).
NOL                    Tax losses carried forward; they shelter later profits from tax.
Owner earnings         EPS x FCF-conversion: the part of reported earnings that becomes cash.
Operating value        Present value of the business's cash flows (= enterprise value).
Bridge                 The step from operating value to equity value: + cash and investments
                       - debt - preferred - minorities - other claims. bridge["net"].
Terminal value (TV)    The value, at the end of the forecast, of every year after it. tv_h.
g                      Terminal growth: the rate cash flow grows at for ever after the forecast.
r, r*, r_hi            A discount rate. r* (r_star) is the "primary rate" values are quoted
                       at; r_hi is the next step up, used to stress them.
Grid                   The menu of round hurdle rates (10/12/14% by default) r* is picked from.
CAPM, WACC, anchor     CAPM: cost of equity = risk-free + beta x equity risk premium.
                       WACC: the blend of that and the after-tax cost of debt. The "anchor"
                       is whichever of the two matches the cash flows, before it is rounded
                       to the grid.
RONIC                  Return on new invested capital. Growth has to be paid for:
                       growth = share of profit reinvested x RONIC.
Stub                   The fraction of forecast year 1 still to come at the valuation date.
Treasury-stock method  Options add shares only for their in-the-money value: n x (1 - strike/V).
If-converted           A convertible note counts as shares (and stops being debt) once a
                       share is worth more than its conversion price.
Slot                   bear / base / bull - the three scenarios the Entry & Exit Plan uses.
                       A scenario without a slot is "context": shown, never used.
PWV, PWR               Probability-weighted value = sum of weight x scenario value (the
                       skill's valuation framework calls this "fair value");
                       probability-weighted return = PWV / price - 1.
F1 ... F5              The reverse-DCF "framings" of the skill's implied-expectations module:
                       Gordon inversion, growth/margin solve, mid-cycle EPS at multiples,
                       the scenario table, and market-implied probability.

Names you will meet in almost every function: `inp` the validated inputs; `sc` one
scenario; `proj` a projection (that scenario's cash flows); `ov` overrides for one call;
`r` a discount rate; `g` terminal growth; `P` the collector of validation problems;
`res` everything analyze() returns; `disc` the discount-rate results; `u` the units label.

CONVENTIONS  (the method, in brief)
-----------------------------------
These are this program's own conventions. They are not guaranteed to match the valuation
framework under references/ at any given moment, so before quoting a figure from here in a
memo, check the two against each other - above all the required return, the timing of cash
flows and the fade.

* Cash-flow modes
    drivers     revenue -> EBIT (after SBC) -> cash taxes (loss carry-forward) -> + D&A - capex - dNWC
    fcf_margin  revenue x unlevered free-cash-flow margin (after SBC)
    eps         EPS x FCF-conversion = owner earnings per share
    direct      analyst-supplied cash flows from a bespoke model
* Basis. "firm": flows are before interest, the anchor rate is WACC, and the
  result is operating value, bridged to equity (+cash +non-operating assets
  -debt -preferred -minorities -other claims). "equity": flows are after
  interest, the anchor rate is the cost of equity, and no bridge is applied.
* Discount rate. CAPM and WACC anchor the choice; the value is struck at hurdle
  rates on a grid (default 10/12/14%). Primary rate r* = grid rate nearest the
  anchor (ties go up; the grid is extended upward if the anchor sits above it).
  Sensitivity rate r_hi = the next grid step. Every scenario is valued at every
  rate - scenarios differ in cash flows, never in discount rate.
* Timing. Mid-year discounting by default. If the first forecast year is partly
  elapsed at the valuation date, only the remaining fraction (the stub) of its
  cash flow is counted and every later flow is discounted from the valuation date.
* Terminal value. gordon: FCF(N+1)/(r-g) on a terminal year rebuilt at terminal
  ratios; value_driver: NOPAT(N+1) x (1 - g/RONIC)/(r-g); exit_multiple: metric(N) x multiple.
  The cross-implied multiple / growth / return on new capital is always reported.
* Share count. shares.count + options (treasury-stock method) + convertibles
  (if-converted, principal removed from debt), solved at the model's own value.
* The market price. No scenario's cash flows read it. It appears in the "% vs price"
  columns and the reverse-DCF block, and - unless debt_to_capital is given - in the
  market-value weights of the WACC, which is how it can influence r* (idea 4 above).

THE INPUTS FILE  (`python3 dcf.py template` prints a filled-in example to edit)
-------------------------------------------------------------------------------
Rules that hold everywhere:
  * Rates, margins and growth are decimals: 12% is 0.12. A 12 is rejected as "looks
    like a percentage" rather than silently valued at 1,200%.
  * Monetary totals AND share counts use one scale, meta.units (millions by default),
    so equity / shares comes out directly in dollars per share. Prices, EPS, option
    strikes and conversion prices are plain per-share currency.
  * A "path" - one value per forecast year - can be written three ways:
        0.21                                     the same value every year
        [0.20, 0.21, 0.22, 0.22, 0.22]           one value per explicit year
        {"from": 0.20, "to": 0.22, "years": 3}   a straight line over 3 years, flat after
  * A key starting with "_" is a comment. Any other key the program does not know is an
    error (with a "did you mean ...?"), so a typo cannot quietly leave a default in force.

Sections (required ones marked *):
  meta*            ticker*, company, valuation_date*, currency, units,
                   first_forecast_year_end + first_forecast_label (which fiscal year is
                   "year 1", and so how much of it is left - the stub), balance_sheet_date
  market           price, price_date. Optional: without a price you get forward values only.
  shares*          count* (basic + unvested RSUs + likely issuance), options [{count,
                   strike}], convertibles [{name, principal, conversion_price, shares}]
  bridge*          cash_and_investments*, debt* (incl. finance leases and the convertibles'
                   principal), non_operating_assets, preferred_equity, minority_interest,
                   other_claims
  discount_rate*   risk_free*, equity_risk_premium*, beta*, additional_premium,
                   pre_tax_cost_of_debt, tax_rate, debt_to_capital, grid,
                   primary_rate + primary_rate_reason (set r* yourself instead of by anchor)
  model*           mode*, basis (must be stated in mode eps), timing, explicit_years (required
                   except in mode direct, where it is the number of cash flows), fade_years,
                   terminal_growth_cap, cyclical + mid_cycle_ebit_margin / mid_cycle_fcf_margin /
                   mid_cycle_eps_at_horizon, mid_cycle_tolerance, mature_peer_multiple
  scenario_defaults  any scenario keys; used by every scenario that does not set its own
  scenarios*       a list. Every scenario: name*, slot, weight, label, narrative, reverse,
                   terminal* {method, growth*, optional terminal-year values}. Then by mode:
        drivers      revenue {base, levels, growth}, ebit_margin, ebit_margin_basis,
                     sbc_pct_revenue, tax_rate, nol_balance, nol_usage_limit,
                     da_pct_revenue, capex_pct_revenue, nwc_pct_incremental_revenue
        fcf_margin   revenue {...}, fcf_margin, sbc_deducted, sbc_pct_revenue
        eps          eps {base, levels, growth}, fcf_conversion
        direct       fcf [one cash flow per year], revenue [optional, display only]
  history          periods + revenue, ebit, da, capex, sbc, change_in_nwc, fcf, eps, roic.
                   Never enters a value; it is what the assumptions are checked against.
  implied          fcf_conversion, terminal_growth, eps_anchors {run_rate,
                   forward_consensus, all_time_peak, mid_cycle}, mid_cycle_multiples -
                   settings for the reverse-DCF block only.
  sources          {"which input": "where it came from, and when"}

"revenue" and "eps" share one shape: `base` is the last actual year; `levels` are
explicit forecasts for the first years (consensus, guidance); `growth` is a path of
growth rates for the remaining explicit years.
"""
from __future__ import annotations

import argparse
import copy
import difflib
import hashlib
import json
import math
import os
import re
import sys
from datetime import date

VERSION = "1.0.0"

# --- The vocabulary of the inputs file. A value outside these lists is rejected. -------------------
MODES = ("drivers", "fcf_margin", "eps", "direct")           # how a scenario's cash flows are built
BASES = ("firm", "equity")                                   # cash flows before interest / after interest
TIMINGS = ("mid_year", "end_year")                           # when in the year a cash flow is taken to arrive
SLOTS = ("bear", "base", "bull")                             # the three scenarios the Entry & Exit Plan uses
LABELS = ("consensus-anchored", "analyst construction")      # who authored a scenario's path
TERMINAL_METHODS = ("gordon", "value_driver", "exit_multiple")   # three ways to value "everything after"
# What an exit multiple may be applied to. A mode can only offer the lines it actually models:
# "fcf_margin" has no EBITDA, "eps" works per share, "direct" knows nothing but the cash flow.
EXIT_METRICS = {
    "drivers": ("ebitda", "ebit", "nopat", "fcf", "revenue"),
    "fcf_margin": ("fcf", "revenue"),
    "eps": ("eps", "owner_earnings"),
    "direct": ("fcf",),
}
UNITS = {"thousands": 1e3, "millions": 1e6, "billions": 1e9}   # scale of monetary totals and share counts

# --- Thresholds. The grid picks the discount rate; every other number here only decides when a flag
# --- is raised. None of them changes a cash flow or a value. ---------------------------------------
DEFAULT_GRID = [0.10, 0.12, 0.14]   # hurdle rates r* is chosen from, unless discount_rate.grid says otherwise
GRID_STEP = 0.02                 # spacing used to extend the grid upward and to find r_hi above its top
TV_SHARE_DIRECTIONAL = 0.75      # terminal value above this share of operating value => directional only
THIN_SPREAD = 0.04               # r* - g below this => terminal value hypersensitive
GROWTH_CLIFF = 0.05              # last modelled growth this far above terminal growth, no fade => cliff
RONIC_HIGH = 0.60                # implied return on new capital above this => reinvestment too light
RATE_SWING_DIRECTIONAL = 0.30    # value move for one grid step in the rate above this => directional
STALE_BALANCE_SHEET_DAYS = 140   # roughly a quarter plus a filing deadline: older than this, a newer 10-Q exists


# =============================================================================
# Input errors and small utilities
# =============================================================================
# Everything in this section exists to read ONE field from the inputs file and decide whether it
# is usable. The helpers share two arguments:
#     where   a human-readable location used in messages, e.g. "scenario 'Base'.terminal"
#     P       the Problems collector (below)
# A helper that finds something wrong records it in P and carries on with a harmless default,
# instead of stopping. That is deliberate: one run then reports every mistake in the file at once,
# rather than making you fix them one at a time.

class InputError(Exception):
    """Raised with a list of every problem found in the inputs file.

    main() catches it, prints the list and exits with code 2. Nothing is valued and no report is
    written, so a half-valid file can never produce a number that looks finished."""

    def __init__(self, problems):
        super().__init__("; ".join(problems))
        self.problems = list(problems)


class Problems:
    """A running list of validation messages. normalize() fills it while reading the whole file,
    then calls raise_if_any() once at the end to turn the list into a single InputError."""

    def __init__(self):
        self.items = []

    def add(self, where, msg):
        self.items.append(f"{where}: {msg}")

    def raise_if_any(self):
        if self.items:
            raise InputError(self.items)


def is_num(x):
    """True for a real, finite number. Booleans are excluded on purpose: Python counts True as 1,
    so `"debt": true` in the JSON would otherwise be accepted as a debt of 1."""
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def clean(d):
    """Drop comment keys (anything starting with '_')."""
    return {k: v for k, v in d.items() if not str(k).startswith("_")}


def check_keys(d, allowed, where, P):
    """Reject any key the program does not know.

    If "capex_pct" (missing "_revenue") were silently ignored, the scenario would run on a default
    and the memo would carry a wrong value with nothing to show for it. So a typo is an error, and
    difflib suggests the closest valid name."""
    for k in d:
        if k not in allowed:
            hint = difflib.get_close_matches(k, allowed, n=1)
            P.add(where, f"unknown key '{k}'" + (f" (did you mean '{hint[0]}'?)" if hint else ""))


def get_obj(raw, key, where, P, required=False):
    """Fetch one section of the file (a JSON object such as "meta" or "bridge") without its
    comment keys. Returns {} when the section is absent, so the caller can keep reading."""
    v = raw.get(key)
    if v is None:
        if required:
            P.add(where, f"missing required section '{key}'")
        return {}
    if not isinstance(v, dict):
        P.add(where, f"'{key}' must be an object")
        return {}
    return clean(v)


def get_num(d, key, where, P, required=False, default=None, lo=None, hi=None, frac=False):
    """Read one number, checking it on the way in.

    required   complain if it is missing
    default    what to return when it is missing or unusable
    lo, hi     the allowed range (inclusive); None = no limit on that side
    frac       True for anything that must be a decimal fraction (a rate, a margin). A value
               beyond +/-1.5 is taken to be a percentage typed as a whole number - 12 instead of
               0.12 - and is rejected, because valuing a company at a 1,200% margin is worse
               than stopping.
    """
    v = d.get(key)
    if v is None:
        if required:
            P.add(where, f"missing required number '{key}'")
        return default
    if not is_num(v):
        P.add(where, f"'{key}' must be a finite number, got {v!r}")
        return default
    v = float(v)
    if frac and abs(v) > 1.5:
        P.add(where, f"'{key}' = {v:g} looks like a percentage; write 12% as 0.12")
        return default
    if lo is not None and v < lo:
        P.add(where, f"'{key}' = {v:g} is below the allowed minimum {lo:g}")
        return default
    if hi is not None and v > hi:
        P.add(where, f"'{key}' = {v:g} is above the allowed maximum {hi:g}")
        return default
    return v


def get_str(d, key, where, P, required=False, default=None, choices=None):
    """Read one piece of text. `choices`, when given, is the closed list it must come from
    (e.g. MODES), so "mid-year" instead of "mid_year" is caught here rather than ignored."""
    v = d.get(key)
    if v is None:
        if required:
            P.add(where, f"missing required text '{key}'")
        return default
    if not isinstance(v, str) or not v.strip():
        P.add(where, f"'{key}' must be non-empty text")
        return default
    v = v.strip()
    if choices and v not in choices:
        P.add(where, f"'{key}' = '{v}' is not one of {', '.join(choices)}")
        return default
    return v


def get_date(d, key, where, P, required=False):
    """Read one date written as YYYY-MM-DD and return it as a `date`, so that two dates can be
    subtracted to count the days between them (used for the stub and the stale-balance-sheet check)."""
    v = d.get(key)
    if v is None:
        if required:
            P.add(where, f"missing required date '{key}' (YYYY-MM-DD)")
        return None
    try:
        return date.fromisoformat(str(v))
    except ValueError:
        P.add(where, f"'{key}' = {v!r} is not a YYYY-MM-DD date")
        return None


def resolve_path(spec, n, where, P, lo=None, hi=None, frac=True):
    """A per-year path given as a number (flat), a list of n values, or a ramp
    {"from": a, "to": b, "years": k} (linear a -> b over the first k years, flat after).

    Whatever the shorthand, the result is a plain list of n numbers, one per explicit forecast
    year, so the rest of the program only ever deals with lists. Returns None (after recording
    the problem) when the spec is unusable. Example with n = 5:
        0.2                                    -> [0.20, 0.20, 0.20, 0.20, 0.20]
        {"from": 0.34, "to": 0.36, "years": 3} -> [0.34, 0.35, 0.36, 0.36, 0.36]
    """
    if n <= 0:
        return []
    if is_num(spec):
        vals = [float(spec)] * n
    elif isinstance(spec, list):
        if len(spec) != n:
            P.add(where, f"expected {n} values (one per year), got {len(spec)}")
            return None
        if not all(is_num(x) for x in spec):
            P.add(where, "every value must be a finite number")
            return None
        vals = [float(x) for x in spec]
    elif isinstance(spec, dict):
        s = clean(spec)
        if set(s) != {"from", "to", "years"}:
            P.add(where, 'a ramp must be exactly {"from": a, "to": b, "years": k}')
            return None
        a, b, k = s["from"], s["to"], s["years"]
        if not (is_num(a) and is_num(b) and isinstance(k, int) and not isinstance(k, bool) and 1 <= k <= n):
            P.add(where, f"ramp needs numeric from/to and an integer years between 1 and {n}")
            return None
        # Year i (counting from 0) sits min(i, k-1)/(k-1) of the way from a to b: it starts at a,
        # arrives at b in year k, and min() holds it at b for every year after that.
        vals = [b if k == 1 else a + (b - a) * min(i, k - 1) / (k - 1) for i in range(n)]
    else:
        P.add(where, "expected a number, a list, or a ramp {from, to, years}")
        return None
    # The same sanity checks get_num applies to a single number, applied to every year of the path.
    for x in vals:
        if frac and abs(x) > 1.5:
            P.add(where, f"value {x:g} looks like a percentage; write 12% as 0.12")
            return None
        if lo is not None and x < lo:
            P.add(where, f"value {x:g} is below the allowed minimum {lo:g}")
            return None
        if hi is not None and x > hi:
            P.add(where, f"value {x:g} is above the allowed maximum {hi:g}")
            return None
    return vals


def deep_merge(defaults, override, merge_keys=("terminal", "revenue", "eps")):
    """Scenario = scenario_defaults overlaid by the scenario. Only the named
    sections merge key-by-key; every other value (including ramps) is replaced.

    This is what lets three scenarios share their common assumptions. With
        defaults  {"tax_rate": 0.19, "terminal": {"growth": 0.03, "capex_pct_revenue": 0.085}}
        scenario  {"ebit_margin": 0.22, "terminal": {"growth": 0.025}}
    the scenario runs on tax 0.19, margin 0.22 and terminal {growth 0.025, capex 0.085}: its
    "terminal" was merged into the default one, not swapped for it. A ramp, by contrast, is one
    value that happens to be written as a dict, so merging two ramps key by key would produce
    nonsense - which is why only the three structural sections are merged.
    """
    out = copy.deepcopy(clean(defaults))
    for k, v in clean(override).items():
        if k in merge_keys and isinstance(v, dict) and isinstance(out.get(k), dict):
            merged = clean(out[k])
            merged.update(clean(v))
            out[k] = merged
        else:
            out[k] = copy.deepcopy(v)
    return out


# =============================================================================
# Normalisation: raw JSON -> validated inputs
# =============================================================================
# STEP 1 of the program. normalize() (at the end of this section) turns the raw JSON into the
# `inp` dict that everything else works from. Each norm_* function handles one section and does
# four things: checks every field, fills in defaults, expands shorthand paths into year-by-year
# lists, and adds a few derived numbers (the stub, the net bridge, a convertible's share count).
# Once normalize() has returned, no other part of the program looks at the raw JSON again or has
# to ask "is this field present?" - which is why the finance code further down can stay short.
#
# The *_KEYS tuples below are the whitelist of key names per section, used by check_keys().
# They double as a compact reference of what the inputs file may contain.

TOP_KEYS = ("meta", "market", "shares", "bridge", "discount_rate", "model",
            "scenario_defaults", "scenarios", "history", "implied", "sources")
META_KEYS = ("ticker", "company", "valuation_date", "currency", "units",
             "first_forecast_year_end", "first_forecast_label", "balance_sheet_date", "fiscal_note")
MARKET_KEYS = ("price", "price_date")
SHARES_KEYS = ("count", "options", "convertibles", "note")
BRIDGE_KEYS = ("cash_and_investments", "non_operating_assets", "debt", "preferred_equity",
               "minority_interest", "other_claims", "note")
MODEL_KEYS = ("mode", "basis", "timing", "explicit_years", "fade_years", "terminal_growth_cap",
              "cyclical", "mid_cycle_ebit_margin", "mid_cycle_fcf_margin", "mid_cycle_eps_at_horizon",
              "mid_cycle_tolerance", "mature_peer_multiple")
DISCOUNT_KEYS = ("risk_free", "equity_risk_premium", "beta", "additional_premium",
                 "pre_tax_cost_of_debt", "tax_rate", "debt_to_capital", "grid",
                 "primary_rate", "primary_rate_reason", "note")
# A scenario's keys: those every scenario may carry, plus the ones its cash-flow mode needs.
SCENARIO_COMMON = ("name", "slot", "weight", "label", "narrative", "reverse",
                   "explicit_years", "fade_years", "terminal")
SCENARIO_KEYS = {
    "drivers": SCENARIO_COMMON + ("revenue", "ebit_margin", "ebit_margin_basis", "sbc_pct_revenue",
                                  "tax_rate", "nol_balance", "nol_usage_limit", "da_pct_revenue",
                                  "capex_pct_revenue", "nwc_pct_incremental_revenue"),
    "fcf_margin": SCENARIO_COMMON + ("revenue", "fcf_margin", "sbc_deducted", "sbc_pct_revenue"),
    "eps": SCENARIO_COMMON + ("eps", "fcf_conversion"),
    "direct": SCENARIO_COMMON + ("fcf", "revenue"),
}
# Inside a scenario's "terminal" block: the method, the growth rate, and - optionally - the value a
# ratio should take in the terminal year when that differs from the last forecast year.
TERMINAL_KEYS = {
    "drivers": ("method", "growth", "ebit_margin", "tax_rate", "da_pct_revenue", "capex_pct_revenue",
                "nwc_pct_incremental_revenue", "sbc_pct_revenue", "ronic", "exit_multiple", "exit_metric"),
    "fcf_margin": ("method", "growth", "fcf_margin", "sbc_pct_revenue", "exit_multiple", "exit_metric"),
    "eps": ("method", "growth", "fcf_conversion", "eps", "exit_multiple", "exit_metric"),
    "direct": ("method", "growth", "fcf", "exit_multiple", "exit_metric"),
}
LEVEL_KEYS = ("base", "levels", "growth")   # the one shape shared by "revenue" and "eps" (see norm_level)
HISTORY_KEYS = ("periods", "revenue", "ebit", "da", "capex", "sbc", "change_in_nwc", "fcf", "eps", "roic", "note")
IMPLIED_KEYS = ("fcf_conversion", "terminal_growth", "eps_anchors", "mid_cycle_multiples")
EPS_ANCHOR_KEYS = ("run_rate", "forward_consensus", "all_time_peak", "mid_cycle")


def norm_meta(raw, P):
    """Who and when: ticker, valuation date, units - and the stub, which is computed here."""
    m = get_obj(raw, "meta", "top level", P, required=True)
    check_keys(m, META_KEYS, "meta", P)
    out = {
        "ticker": get_str(m, "ticker", "meta", P, required=True),
        "company": get_str(m, "company", "meta", P),
        "valuation_date": get_date(m, "valuation_date", "meta", P, required=True),
        "currency": get_str(m, "currency", "meta", P, default="USD"),
        "units": get_str(m, "units", "meta", P, default="millions", choices=tuple(UNITS)),
        "first_forecast_year_end": get_date(m, "first_forecast_year_end", "meta", P),
        "first_forecast_label": get_str(m, "first_forecast_label", "meta", P),
        "balance_sheet_date": get_date(m, "balance_sheet_date", "meta", P),
        "fiscal_note": get_str(m, "fiscal_note", "meta", P),
    }
    # The stub: how much of forecast year 1 is still ahead of us on the valuation date.
    #   Valued on 2026-11-11 with FY2027 ending 2027-06-30: 231 days remain -> 231 / 365.25 = 0.63.
    #   Only 63% of FY2027's cash flow is still to come; the other 37% has been earned already and
    #   is sitting in the balance sheet's cash, so counting it again would double-count it.
    # Without the two fiscal dates, year 1 is simply "the next twelve months" and the stub is 1.
    # Getting this wrong is the classic way a model silently gains or loses a year of discounting.
    stub = 1.0
    vd, fye = out["valuation_date"], out["first_forecast_year_end"]
    if vd and fye:
        days = (fye - vd).days
        # Year 1 has to be the fiscal year in progress: one that already ended has no cash flow
        # left, and one ending more than a year out (372 = a year plus a week of slack for
        # 52/53-week calendars) would mean the year in between was skipped.
        if days <= 0:
            P.add("meta", f"first_forecast_year_end {fye} is not after valuation_date {vd}; "
                          "year 1 must be the fiscal year still in progress (or the next one)")
        elif days > 372:
            P.add("meta", f"first_forecast_year_end {fye} is more than 12 months after valuation_date {vd}; "
                          "year 1 must be the fiscal year in progress - add the missing year")
        else:
            stub = min(1.0, days / 365.25)
    out["stub"] = stub
    return out


def norm_market(raw, P):
    """The market price. Optional: scenario values are computed without it; it only switches on
    the "% vs price" columns and the reverse-DCF block (and, by default, weights the WACC)."""
    m = get_obj(raw, "market", "top level", P)
    check_keys(m, MARKET_KEYS, "market", P)
    return {"price": get_num(m, "price", "market", P, lo=1e-9),
            "price_date": get_date(m, "price_date", "market", P)}


def norm_shares(raw, P):
    """The share count, in three parts that dilute differently:

    count         shares that exist whatever the stock is worth (basic + unvested RSUs + issuance
                  already announced). Always in the denominator.
    options       add shares only when in the money, and only for the in-the-money part.
    convertibles  are debt below the conversion price and shares above it.

    The last two depend on what a share is worth, so they are only described here; the actual
    dilution is worked out later, at the model's own value, in per_share_value().
    """
    s = get_obj(raw, "shares", "top level", P, required=True)
    check_keys(s, SHARES_KEYS, "shares", P)
    out = {"count": get_num(s, "count", "shares", P, required=True, lo=1e-9),
           "options": [], "convertibles": [], "note": get_str(s, "note", "shares", P)}
    for i, o in enumerate(s.get("options") or []):
        w = f"shares.options[{i}]"
        if not isinstance(o, dict):
            P.add(w, "must be an object {count, strike}")
            continue
        o = clean(o)
        check_keys(o, ("count", "strike", "name"), w, P)
        c = get_num(o, "count", w, P, required=True, lo=0)
        k = get_num(o, "strike", w, P, required=True, lo=1e-9)
        if c is not None and k is not None:
            out["options"].append({"count": c, "strike": k, "name": o.get("name")})
    for i, c in enumerate(s.get("convertibles") or []):
        w = f"shares.convertibles[{i}]"
        if not isinstance(c, dict):
            P.add(w, "must be an object {principal, conversion_price}")
            continue
        c = clean(c)
        check_keys(c, ("name", "principal", "conversion_price", "shares"), w, P)
        pr = get_num(c, "principal", w, P, required=True, lo=1e-9)
        cp = get_num(c, "conversion_price", w, P, required=True, lo=1e-9)
        sh = get_num(c, "shares", w, P, lo=1e-9)
        if pr is not None and cp is not None:
            # Shares issued on conversion = principal / conversion price ($1,000M at $150 -> 6.67M
            # shares) unless the note's own figure is supplied in "shares".
            out["convertibles"].append({"name": c.get("name") or f"convertible {i + 1}",
                                        "principal": pr, "conversion_price": cp,
                                        "shares": sh if sh is not None else pr / cp})
    return out


def norm_model(raw, P):
    """The structural choices that apply to every scenario: how cash flows are built (mode),
    whether they are before or after interest (basis), when in the year they arrive (timing),
    how long the forecast runs (explicit_years + fade_years), and the settings for the checks
    (terminal-growth cap, cyclical mid-cycle anchors, a mature-peer multiple to compare against)."""
    m = get_obj(raw, "model", "top level", P, required=True)
    check_keys(m, MODEL_KEYS, "model", P)
    mode = get_str(m, "mode", "model", P, required=True, choices=MODES)
    basis = get_str(m, "basis", "model", P, choices=BASES)
    # An EPS path can be either kind: reported and consensus EPS are after interest ("equity"),
    # NOPAT per share is before it ("firm"). The program cannot tell which was typed in, and the
    # wrong guess either double-counts or drops the net cash, so in this mode it refuses to guess.
    if mode == "eps" and basis is None:
        P.add("model", "mode 'eps' needs an explicit basis: 'equity' if the EPS is after interest "
                       "(reported or consensus EPS), 'firm' if it is before interest (NOPAT per share)")
    if basis is None:
        basis = "firm"
    out = {
        "mode": mode, "basis": basis,
        "timing": get_str(m, "timing", "model", P, default="mid_year", choices=TIMINGS),
        "explicit_years": None, "fade_years": 0,
        "terminal_growth_cap": get_num(m, "terminal_growth_cap", "model", P, default=0.03, lo=0.0, hi=0.06, frac=True),
        "cyclical": bool(m.get("cyclical", False)),
        "mid_cycle_ebit_margin": get_num(m, "mid_cycle_ebit_margin", "model", P, lo=-1, hi=0.95, frac=True),
        "mid_cycle_fcf_margin": get_num(m, "mid_cycle_fcf_margin", "model", P, lo=-1, hi=0.95, frac=True),
        "mid_cycle_eps_at_horizon": get_num(m, "mid_cycle_eps_at_horizon", "model", P),
        "mid_cycle_tolerance": get_num(m, "mid_cycle_tolerance", "model", P, default=0.10, lo=0, hi=1, frac=True),
        "mature_peer_multiple": None,
    }
    if m.get("cyclical") is not None and not isinstance(m.get("cyclical"), bool):
        P.add("model", "'cyclical' must be true or false")
    # Year counts must be whole numbers. (bool is tested first because Python treats True as 1.)
    # explicit_years stays None if absent: each scenario may set its own, checked in norm_scenario.
    for key, lo, hi in (("explicit_years", 1, 30), ("fade_years", 0, 20)):
        v = m.get(key)
        if v is None:
            continue
        if isinstance(v, bool) or not isinstance(v, int) or not lo <= v <= hi:
            P.add("model", f"'{key}' must be an integer between {lo} and {hi}")
        else:
            out[key] = v
    # Optional yardstick, e.g. {"metric": "ebitda", "value": 14}: what mature peers trade at. Never
    # used to compute a value - only to flag a terminal value that implies a richer multiple.
    mp = m.get("mature_peer_multiple")
    if mp is not None:
        if not isinstance(mp, dict):
            P.add("model", "'mature_peer_multiple' must be an object {metric, value}")
        else:
            mp = clean(mp)
            check_keys(mp, ("metric", "value", "note"), "model.mature_peer_multiple", P)
            metric = get_str(mp, "metric", "model.mature_peer_multiple", P, required=True,
                             choices=EXIT_METRICS.get(mode, ()) if mode else None)
            value = get_num(mp, "value", "model.mature_peer_multiple", P, required=True, lo=0.1, hi=200)
            if metric and value:
                out["mature_peer_multiple"] = {"metric": metric, "value": value}
    return out


def norm_bridge(raw, model, P):
    """The bridge from operating value (what the business is worth) to equity value (what the
    shareholders' part is worth):

        net = cash and investments + non-operating assets
              - debt - preferred equity - minority interest - other claims

    On a firm basis cash and debt must be written out, even when zero: a figure that is simply
    missing must never be read as "no net debt". On an equity basis the cash flows are already
    after interest, so the bridge is not applied at all and the section may be left out.
    """
    firm = model["basis"] == "firm"
    b = get_obj(raw, "bridge", "top level", P, required=firm)
    check_keys(b, BRIDGE_KEYS, "bridge", P)
    out = {"note": get_str(b, "note", "bridge", P)}
    for key in ("cash_and_investments", "debt"):
        out[key] = get_num(b, key, "bridge", P, required=firm, default=0.0, lo=0)
    for key in ("non_operating_assets", "preferred_equity", "minority_interest", "other_claims"):
        out[key] = get_num(b, key, "bridge", P, default=0.0, lo=0)
    out["net"] = (out["cash_and_investments"] + out["non_operating_assets"] - out["debt"]
                  - out["preferred_equity"] - out["minority_interest"] - out["other_claims"])
    return out


def norm_discount(raw, P):
    """The raw ingredients of the discount rate. They are only checked here; the arithmetic
    (CAPM, WACC, choosing r* off the grid) happens in compute_discount().

    The allowed ranges are wide on purpose. They are there to catch typing mistakes - a beta of
    13, a risk-free rate of 4.3 - not to second-guess a judgment."""
    d = get_obj(raw, "discount_rate", "top level", P, required=True)
    check_keys(d, DISCOUNT_KEYS, "discount_rate", P)
    out = {
        "risk_free": get_num(d, "risk_free", "discount_rate", P, required=True, lo=0.0, hi=0.15, frac=True),
        "equity_risk_premium": get_num(d, "equity_risk_premium", "discount_rate", P, required=True, lo=0.02, hi=0.12, frac=True),
        "beta": get_num(d, "beta", "discount_rate", P, required=True, lo=0.1, hi=4.0),
        "additional_premium": get_num(d, "additional_premium", "discount_rate", P, default=0.0, lo=0.0, hi=0.15, frac=True),
        "pre_tax_cost_of_debt": get_num(d, "pre_tax_cost_of_debt", "discount_rate", P, lo=0.0, hi=0.40, frac=True),
        "tax_rate": get_num(d, "tax_rate", "discount_rate", P, lo=0.0, hi=0.60, frac=True),
        "debt_to_capital": get_num(d, "debt_to_capital", "discount_rate", P, lo=0.0, hi=0.95, frac=True),
        "primary_rate": get_num(d, "primary_rate", "discount_rate", P, lo=0.04, hi=0.40, frac=True),
        "primary_rate_reason": get_str(d, "primary_rate_reason", "discount_rate", P),
        "note": get_str(d, "note", "discount_rate", P),
    }
    grid = d.get("grid", DEFAULT_GRID)
    if not isinstance(grid, list) or not grid or not all(is_num(x) for x in grid):
        P.add("discount_rate", "'grid' must be a non-empty list of rates, e.g. [0.10, 0.12, 0.14]")
        grid = DEFAULT_GRID
    for x in grid:
        if x > 1.5:
            P.add("discount_rate", f"grid rate {x:g} looks like a percentage; write 12% as 0.12")
        elif not 0.04 <= x <= 0.40:
            P.add("discount_rate", f"grid rate {x:g} is outside 0.04-0.40")
    out["grid"] = sorted({round(float(x), 6) for x in grid})      # duplicates removed, lowest rate first
    # Setting r* by hand is allowed (a rule-based or investor-chosen required return, say), but it
    # replaces the rate the program would have derived, so it has to arrive with its justification.
    if out["primary_rate"] is not None and not out["primary_rate_reason"]:
        P.add("discount_rate", "'primary_rate' overrides the CAPM/WACC-anchored rate and needs 'primary_rate_reason'")
    return out


def norm_level(spec, n_exp, where, P, positive):
    """Revenue or EPS: {"base": last actual, "levels": [explicit forecasts], "growth": path for the rest}.

    The two-part shape mirrors how forecasts are usually known. The next year or two come as
    numbers (consensus, guidance) - those go in "levels". Beyond that the analyst has a view on
    growth rather than on a figure - that goes in "growth". With explicit_years = 5:
        {"base": 9000, "levels": [10600, 12200], "growth": [0.13, 0.11, 0.09]}
    means year 1 = 10,600, year 2 = 12,200, then +13%, +11%, +9% for years 3 to 5.
    "base" is the last actual year: it gives year 1 its growth rate and its working-capital change.

    positive   True for revenue (must be above zero). False for EPS, which may start from a loss.
    Returns {"base", "fixed" (the levels), "growth" (a list for the remaining years)}.
    """
    if not isinstance(spec, dict):
        P.add(where, 'must be an object {"base", "levels", "growth"}')
        return None
    s = clean(spec)
    check_keys(s, LEVEL_KEYS, where, P)
    base = get_num(s, "base", where, P, required=True, lo=1e-9 if positive else None)
    fixed = s.get("levels") or []
    if not isinstance(fixed, list) or not all(is_num(x) for x in fixed):
        P.add(where, "'levels' must be a list of numbers")
        return None
    fixed = [float(x) for x in fixed]
    if positive and any(x <= 0 for x in fixed):
        P.add(where, "'levels' must all be positive")
        return None
    k = len(fixed)
    if k > n_exp:
        P.add(where, f"'levels' has {k} values but the explicit period is {n_exp} years")
        return None
    growth = []
    if k < n_exp:
        if s.get("growth") is None:
            P.add(where, f"'growth' is required for the {n_exp - k} explicit year(s) not covered by 'levels'")
            return None
        growth = resolve_path(s["growth"], n_exp - k, f"{where}.growth", P, lo=-0.9, hi=10.0, frac=False)
        if growth is None:
            return None
        if any(g > 10 for g in growth):
            P.add(f"{where}.growth", "growth above 1000% - write 25% as 0.25")
        # A growth rate needs something positive to grow from: "+20%" applied to a loss of -1.00
        # gives -1.20. A company still losing money must be carried to profit with explicit levels.
        start = fixed[-1] if fixed else base
        if start is not None and start <= 0:
            P.add(where, "growth rates cannot be applied to a non-positive starting level; give explicit 'levels' "
                         "until the level is positive")
            return None
    elif s.get("growth") is not None:
        P.add(where, "'growth' is unused because 'levels' already covers every explicit year")
    if base is None:
        return None
    return {"base": base, "fixed": fixed, "growth": growth}


def norm_terminal(sc, mode, where, P):
    """A scenario's "terminal" block: how everything after the last forecast year is valued.

    method      gordon (default)   cash flow of the year after the forecast / (r - g)
                value_driver       the same, with reinvestment set by a stated return on new capital
                exit_multiple      a multiple of the last forecast year's EBITDA, EPS, ...
    growth      g, the perpetual growth rate. Required even with an exit multiple, because the
                fade and the reverse-DCF inversions still need it.
    overrides   terminal-year values for the ratios (margin, tax, D&A, capex, NWC, SBC,
                conversion) where the steady state should differ from the last forecast year -
                typically capex settling closer to D&A once growth has slowed.
    """
    t = sc.get("terminal")
    if not isinstance(t, dict):
        P.add(where, "missing 'terminal' object (at least {\"growth\": ...})")
        return None
    t = clean(t)
    check_keys(t, TERMINAL_KEYS[mode], f"{where}.terminal", P)
    w = f"{where}.terminal"
    method = get_str(t, "method", w, P, default="gordon", choices=TERMINAL_METHODS)
    out = {"method": method,
           "growth": get_num(t, "growth", w, P, required=True, lo=-0.05, hi=0.06, frac=True),
           "overrides": {}, "ronic": None, "exit_multiple": None, "exit_metric": None,
           "fcf": None, "eps": None}
    # Allowed range for each terminal-year override. Only those present in the file are kept; an
    # absent one means "same as the last forecast year" (resolved later, in full_path()).
    bounds = {"ebit_margin": (-5, 0.95), "tax_rate": (0, 0.6), "da_pct_revenue": (0, 1),
              "capex_pct_revenue": (0, 10), "nwc_pct_incremental_revenue": (-1.5, 1.5),
              "sbc_pct_revenue": (0, 1), "fcf_margin": (-5, 0.95), "fcf_conversion": (0.05, 1.5)}
    for key, (lo, hi) in bounds.items():
        if key in t and t[key] is not None:
            v = get_num(t, key, w, P, lo=lo, hi=hi, frac=key != "capex_pct_revenue")
            if v is not None:
                out["overrides"][key] = v
    if mode == "direct":
        out["fcf"] = get_num(t, "fcf", w, P)
    if mode == "eps":
        out["eps"] = get_num(t, "eps", w, P)
    if method == "value_driver":
        if mode != "drivers":
            P.add(w, "method 'value_driver' needs NOPAT, which only mode 'drivers' models")
        out["ronic"] = get_num(t, "ronic", w, P, required=True, lo=0.01, hi=2.0, frac=False)
        # The formula keeps (1 - g / RONIC) of profit as free cash flow. With RONIC at or below g
        # that share is zero or negative: the business would have to reinvest more than it earns
        # just to stand still.
        if out["ronic"] is not None and out["growth"] is not None and out["ronic"] <= out["growth"]:
            P.add(w, "'ronic' must exceed terminal growth")
    elif t.get("ronic") is not None:
        P.add(w, "'ronic' is only used with method 'value_driver'")
    if method == "exit_multiple":
        out["exit_multiple"] = get_num(t, "exit_multiple", w, P, required=True, lo=0.1, hi=200)
        out["exit_metric"] = get_str(t, "exit_metric", w, P, required=True, choices=EXIT_METRICS[mode])
    elif t.get("exit_multiple") is not None or t.get("exit_metric") is not None:
        P.add(w, "'exit_multiple' / 'exit_metric' are only used with method 'exit_multiple'")
    return out


def norm_scenario(raw_sc, model, idx, P):
    """One scenario from the file -> the tidy form project() works from (None if unusable).

    Whatever the mode, the result carries:
        name, slot, weight, label, narrative, reverse
        n_exp      number of explicit forecast years
        fade       number of fade years after them
        terminal   the terminal block (see norm_terminal)
    and then what its mode needs:
        level      revenue (drivers, fcf_margin) or EPS (eps): {"base", "fixed", "growth"}
        paths      {ratio name: [one value per explicit year]} - margins, tax, capex, ...
        fcf        the cash flows themselves (direct)
    `raw_sc` has already been overlaid on scenario_defaults by the caller.
    """
    mode = model["mode"]
    if not isinstance(raw_sc, dict):
        P.add(f"scenarios[{idx}]", "must be an object")
        return None
    sc = clean(raw_sc)
    name = sc.get("name") if isinstance(sc.get("name"), str) and sc.get("name").strip() else None
    # Messages refer to the scenario by name when it has one, by position when it does not.
    where = f"scenario '{name}'" if name else f"scenarios[{idx}]"
    if name is None:
        P.add(where, "missing 'name'")
    if mode is None:            # model.mode itself was invalid (already reported): nothing to check against
        return None
    check_keys(sc, SCENARIO_KEYS[mode], where, P)
    out = {
        "name": name or f"scenario {idx + 1}",
        "slot": get_str(sc, "slot", where, P, choices=SLOTS),
        "weight": get_num(sc, "weight", where, P, lo=0.0, hi=1.0),
        "label": get_str(sc, "label", where, P, choices=LABELS),
        "narrative": get_str(sc, "narrative", where, P),
        "reverse": bool(sc.get("reverse", False)),
        "fade": model["fade_years"], "n_exp": model["explicit_years"],
    }
    # A scenario may run on its own horizon (say a 5-year view shown beside a 10-year one); if it
    # does not say, it uses the model-wide explicit_years / fade_years copied in just above.
    for key, target, lo, hi in (("explicit_years", "n_exp", 1, 30), ("fade_years", "fade", 0, 20)):
        v = sc.get(key)
        if v is None:
            continue
        if isinstance(v, bool) or not isinstance(v, int) or not lo <= v <= hi:
            P.add(where, f"'{key}' must be an integer between {lo} and {hi}")
        else:
            out[target] = v

    terminal = norm_terminal(sc, mode, where, P)
    out["terminal"] = terminal

    # --- mode "direct": the analyst supplies the cash flows; there is nothing to build. -------------
    # The horizon is simply the number of cash flows given. A fade cannot be offered because the
    # program does not know what drives these numbers, so it has nothing to fade.
    if mode == "direct":
        fcf = sc.get("fcf")
        if not isinstance(fcf, list) or not fcf or not all(is_num(x) for x in fcf):
            P.add(where, "'fcf' must be a non-empty list of yearly cash flows")
            return None
        out["fcf"] = [float(x) for x in fcf]
        if out["n_exp"] is not None and out["n_exp"] != len(fcf):
            P.add(where, f"'fcf' has {len(fcf)} values but explicit_years is {out['n_exp']}")
        out["n_exp"] = len(fcf)
        if out["fade"]:
            P.add(where, "fade_years is not available in mode 'direct' - put the fade into the cash flows")
        rev = sc.get("revenue")
        if rev is not None:
            if not isinstance(rev, list) or len(rev) != len(fcf) or not all(is_num(x) for x in rev):
                P.add(where, "'revenue' (display only in mode 'direct') must be a list as long as 'fcf'")
                rev = None
        out["display_revenue"] = [float(x) for x in rev] if rev else None
        return out if terminal else None

    # --- the three modes the program builds itself ---------------------------------------------------
    n = out["n_exp"]
    if n is None:
        P.add(where, "explicit_years is not set (model.explicit_years or the scenario's own)")
        return None
    paths = {}

    def path(key, lo, hi, required=True, frac=True):
        """Expand one ratio (a number, a list or a ramp) into n yearly values and store it in `paths`.
        Defined inside norm_scenario so it can see sc, n, paths and where; each call below then
        needs only the ratio's name and its allowed range."""
        if sc.get(key) is None:
            if required:
                P.add(where, f"missing '{key}'")
            return
        paths[key] = resolve_path(sc[key], n, f"{where}.{key}", P, lo=lo, hi=hi, frac=frac)

    if mode in ("drivers", "fcf_margin"):
        if sc.get("revenue") is None:
            P.add(where, "missing 'revenue'")
            out["level"] = None
        else:
            out["level"] = norm_level(sc["revenue"], n, f"{where}.revenue", P, positive=True)
    if mode == "drivers":
        # The five ratios that turn revenue into free cash flow, each as a path over the explicit years:
        path("ebit_margin", -5, 0.95)                    # operating profit / revenue (may be negative)
        path("tax_rate", 0, 0.6)                         # cash tax as a share of operating profit
        path("da_pct_revenue", 0, 1)                     # depreciation & amortisation / revenue
        path("capex_pct_revenue", 0, 10, frac=False)     # capex / revenue; can top 100% in a heavy build-out,
        #                                                  hence the high ceiling and no "looks like a %" test
        path("nwc_pct_incremental_revenue", -1.5, 1.5)   # working capital tied up per dollar of NEW revenue
        #                                                  (negative when customers pay in advance)
        # SBC is a real cost. A GAAP operating margin already contains it. A non-GAAP ("adjusted")
        # margin leaves it out, so in that case the SBC path is required and is subtracted.
        out["margin_basis"] = get_str(sc, "ebit_margin_basis", where, P, default="gaap", choices=("gaap", "non_gaap"))
        if out["margin_basis"] == "non_gaap":
            path("sbc_pct_revenue", 0, 1)
        elif sc.get("sbc_pct_revenue") is not None:
            P.add(where, "'sbc_pct_revenue' is only used when ebit_margin_basis is 'non_gaap' "
                         "(a GAAP margin already carries SBC as an expense)")
        # Tax losses brought forward, and the share of any one year's profit they may shelter
        # (0.8 = the US rule that carried-forward losses can offset at most 80% of taxable income).
        out["nol_balance"] = get_num(sc, "nol_balance", where, P, default=0.0, lo=0)
        out["nol_usage_limit"] = get_num(sc, "nol_usage_limit", where, P, default=0.8, lo=0.0, hi=1.0)
    elif mode == "fcf_margin":
        path("fcf_margin", -5, 0.95)
        # "Free cash flow" as companies report it adds SBC back. The program needs it AFTER SBC and
        # will not guess which kind was typed in: the scenario has to say, and if SBC is still in
        # the margin it has to supply the SBC path so it can be taken out.
        if not isinstance(sc.get("sbc_deducted"), bool):
            P.add(where, "'sbc_deducted' must be stated: true if the FCF margin is already net of stock-based "
                         "compensation, false if it is not (then give sbc_pct_revenue)")
            out["sbc_deducted"] = True
        else:
            out["sbc_deducted"] = sc["sbc_deducted"]
        if not out["sbc_deducted"]:
            path("sbc_pct_revenue", 0, 1)
        elif sc.get("sbc_pct_revenue") is not None:
            P.add(where, "'sbc_pct_revenue' is only used when sbc_deducted is false")
    elif mode == "eps":
        if sc.get("eps") is None:
            P.add(where, "missing 'eps'")
            out["level"] = None
        else:
            out["level"] = norm_level(sc["eps"], n, f"{where}.eps", P, positive=False)
        path("fcf_conversion", 0.05, 1.5)                # share of EPS that turns into free cash flow
    out["paths"] = paths
    # If any piece failed, its problem is already recorded; returning None keeps a half-built
    # scenario away from the cross-checks in normalize().
    if terminal is None or out.get("level") is None or any(v is None for v in paths.values()):
        return None
    return out


def norm_history(raw, P):
    """The company's own record, oldest period first (optional).

    History never enters a valuation. It is the yardstick the assumptions are held against:
    flags such as "terminal margin above every year in history" or "year-1 margin jumps 9 points
    above the latest actual", and the history table printed beside the forecast. Each series is
    a list as long as `periods`; use null where a figure is not available."""
    h = raw.get("history")
    if h is None:
        return None
    if not isinstance(h, dict):
        P.add("history", "must be an object")
        return None
    h = clean(h)
    check_keys(h, HISTORY_KEYS, "history", P)
    periods = h.get("periods")
    if not isinstance(periods, list) or not periods:
        P.add("history", "'periods' must be a non-empty list of labels, oldest first")
        return None
    out = {"periods": [str(p) for p in periods], "note": h.get("note")}
    for key in HISTORY_KEYS:
        if key in ("periods", "note") or h.get(key) is None:
            continue
        v = h[key]
        if not isinstance(v, list) or len(v) != len(periods) or not all(x is None or is_num(x) for x in v):
            P.add("history", f"'{key}' must be a list of {len(periods)} numbers (null where unavailable)")
            continue
        out[key] = [None if x is None else float(x) for x in v]
    if "revenue" in out and any(x is not None and x <= 0 for x in out["revenue"]):
        P.add("history", "'revenue' values must be positive")
    return out


def norm_implied(raw, P):
    """Settings for the reverse-DCF block only (optional; sensible defaults otherwise).

    fcf_conversion, terminal_growth   the two assumptions of the Gordon inversion (framing F1)
    eps_anchors                       what the implied EPS is compared against: today's run-rate,
                                      forward consensus, the all-time peak, the mid-cycle level
    mid_cycle_multiples               the through-cycle P/E multiples used in framing F3
    """
    im = raw.get("implied")
    out = {"fcf_conversion": None, "terminal_growth": None, "eps_anchors": {},
           "mid_cycle_multiples": [10.0, 12.0, 14.0, 16.0]}
    if im is None:
        return out
    if not isinstance(im, dict):
        P.add("implied", "must be an object")
        return out
    im = clean(im)
    check_keys(im, IMPLIED_KEYS, "implied", P)
    out["fcf_conversion"] = get_num(im, "fcf_conversion", "implied", P, lo=0.05, hi=1.5)
    out["terminal_growth"] = get_num(im, "terminal_growth", "implied", P, lo=-0.05, hi=0.06, frac=True)
    anchors = im.get("eps_anchors")
    if anchors is not None:
        if not isinstance(anchors, dict):
            P.add("implied", "'eps_anchors' must be an object")
        else:
            anchors = clean(anchors)
            check_keys(anchors, EPS_ANCHOR_KEYS, "implied.eps_anchors", P)
            for k in EPS_ANCHOR_KEYS:
                v = get_num(anchors, k, "implied.eps_anchors", P)
                if v is not None:
                    out["eps_anchors"][k] = v
    mm = im.get("mid_cycle_multiples")
    if mm is not None:
        if not isinstance(mm, list) or not mm or not all(is_num(x) and x > 0 for x in mm):
            P.add("implied", "'mid_cycle_multiples' must be a list of positive numbers")
        else:
            out["mid_cycle_multiples"] = [float(x) for x in mm]
    return out


def normalize(raw):
    """Validate the raw JSON and return the inputs the engine works from.

    Reads the whole file before complaining: every norm_* call adds what it finds to P, and only
    the final P.raise_if_any() stops the run - with the complete list. The returned dict (`inp`
    everywhere else) has one key per section: meta, market, shares, bridge, model, discount,
    scenarios, history, implied, sources.
    """
    if not isinstance(raw, dict):
        raise InputError(["top level: the inputs file must be a JSON object"])
    # `dcf.py template` output is marked "_template": true and is full of invented numbers. Refusing
    # to run it is a speed bump against a made-up figure surviving into a real valuation.
    if raw.get("_template"):
        raise InputError(["top level: this is still the template - replace every value with sourced company "
                          "data, then delete the \"_template\" key"])
    raw = clean(raw)
    P = Problems()
    check_keys(raw, TOP_KEYS, "top level", P)
    meta = norm_meta(raw, P)
    market = norm_market(raw, P)
    shares = norm_shares(raw, P)
    model = norm_model(raw, P)
    bridge = norm_bridge(raw, model, P)
    disc = norm_discount(raw, P)
    defaults = raw.get("scenario_defaults") or {}
    if not isinstance(defaults, dict):
        P.add("scenario_defaults", "must be an object")
        defaults = {}
    raw_scenarios = raw.get("scenarios")
    scenarios = []
    if not isinstance(raw_scenarios, list) or not raw_scenarios:
        P.add("top level", "'scenarios' must be a non-empty list")
    elif model["mode"]:
        for i, s in enumerate(raw_scenarios):
            # Each scenario is laid over the shared defaults first, then checked as a whole.
            merged = deep_merge(defaults, s) if isinstance(s, dict) else s
            sc = norm_scenario(merged, model, i, P)
            if sc is not None:
                scenarios.append(sc)
    history = norm_history(raw, P)
    implied = norm_implied(raw, P)
    sources = raw.get("sources")
    if sources is not None and not isinstance(sources, dict):
        P.add("sources", "must be an object mapping an input (e.g. \"bridge.debt\") to its citation")
        sources = None

    # --- checks that involve more than one scenario --------------------------------------------------
    # Names must be unique (results are looked up by name); each of bear / base / bull can be held
    # by one scenario only; and weights are all-or-nothing and must add up to 100%, because the
    # probability-weighted value is meaningless otherwise.
    names = [s["name"] for s in scenarios]
    for n in set(names):
        if names.count(n) > 1:
            P.add("scenarios", f"scenario name '{n}' is used more than once")
    for slot in SLOTS:
        if sum(1 for s in scenarios if s["slot"] == slot) > 1:
            P.add("scenarios", f"more than one scenario is assigned to the '{slot}' slot")
    slotted = [s for s in scenarios if s["slot"]]
    weighted = [s for s in slotted if s["weight"] is not None]
    if weighted and len(weighted) != len(slotted):
        P.add("scenarios", "give a 'weight' to every slotted scenario or to none")
    if weighted and len(slotted) == 3 and abs(sum(s["weight"] for s in weighted) - 1.0) > 1e-6:
        P.add("scenarios", f"bear/base/bull weights sum to {sum(s['weight'] for s in weighted):.4f}, not 1")
    for s in scenarios:
        if s["weight"] is not None and not s["slot"]:
            P.add(f"scenario '{s['name']}'", "'weight' is only meaningful on a bear/base/bull slot")

    # The perpetuity formula divides by (r - g). As g approaches r the value runs off to infinity,
    # so terminal growth has to sit at least a full point under the lowest rate that will be used.
    min_rate = min(disc["grid"]) if disc["grid"] else 0.10
    if disc.get("primary_rate"):
        min_rate = min(min_rate, disc["primary_rate"])
    for s in scenarios:
        t = s.get("terminal")
        if t and t["growth"] is not None and t["growth"] > min_rate - 0.01:
            P.add(f"scenario '{s['name']}'",
                  f"terminal growth {t['growth']:.2%} must sit at least 1 point below the lowest discount rate {min_rate:.2%}")
    P.raise_if_any()
    return {"meta": meta, "market": market, "shares": shares, "bridge": bridge, "model": model,
            "discount": disc, "scenarios": scenarios, "history": history, "implied": implied,
            "sources": clean(sources) if sources else {}}


# =============================================================================
# Discount rate
# =============================================================================
# STEP 2 begins here. This section answers two questions:
#   "How many shares are there?"     diluted_at() and per_share_value()
#   "What rate do we discount at?"   compute_discount()
# The share-count helpers sit here because the WACC needs the market value of the equity
# (price x diluted shares) for its weights. value_at() reuses them later to turn equity value into
# value per share.

def diluted_at(v, shares, basis):
    """Share count, and convertible principal that turns into equity, if a share is worth v.

    Options - the treasury-stock method. Exercising brings cash into the company, and that cash
    could buy shares back, so only the difference dilutes. 10M options struck at $40 with the
    share at $100: holders pay 10M x $40 = $400M, which buys back 4M shares at $100, leaving
    6M net new shares = 10M x (1 - 40/100). Below the strike nobody exercises: no dilution.

    Convertibles - the if-converted method. Above the conversion price holders are better off
    converting, so the note's shares are added and its principal is handed back to the caller,
    who must stop counting it as debt. A note is debt or shares, never both. (Only on a firm
    basis: an equity-basis run has no debt bridge for the principal to come out of.)

    Returns (share count, converted principal).
    """
    n = shares["count"]
    for o in shares["options"]:
        if v > o["strike"]:
            n += o["count"] * (1.0 - o["strike"] / v)
    converted = 0.0
    if basis == "firm":
        for c in shares["convertibles"]:
            if v > c["conversion_price"]:
                n += c["shares"]
                converted += c["principal"]
    return n, converted


def per_share_value(equity_pre, shares, basis):
    """Solve value per share V = (equity + converted principal at V) / diluted shares at V.

    There is a circle here. How many shares there are depends on what a share is worth (more
    options are in the money and more notes convert as the value rises), and what a share is
    worth depends on how many there are. So instead of a formula the code searches for the one
    value that is consistent with itself.

    equity_pre   equity value with every convertible still counted as debt
    Returns (value per share, diluted share count, principal that converted). The value can be
    negative when debt exceeds operating value; value_at() floors it at zero for display.

    The search is bisection: keep a range [lo, hi] known to contain the answer, test the
    midpoint, discard the half that cannot contain it, repeat. If valuing the company with the
    dilution that applies at `mid` gives more than `mid`, the true value lies higher.
    """
    n0 = shares["count"]
    dilutive = shares["options"] or (basis == "firm" and shares["convertibles"])
    # Nothing to solve when there is nothing dilutive - or when equity is worthless, since then no
    # option is in the money and no note converts.
    if equity_pre <= 0 or not dilutive:
        return equity_pre / n0, n0, 0.0
    lo = 0.0
    # The value can never exceed "every note converted, no new shares issued": a safe ceiling.
    hi = (equity_pre + sum(c["principal"] for c in shares["convertibles"])) / n0
    for _ in range(200):      # each pass halves the range; 200 is far beyond floating-point precision
        mid = (lo + hi) / 2.0
        n, conv = diluted_at(mid, shares, basis)
        if (equity_pre + conv) / n > mid:
            lo = mid
        else:
            hi = mid
    v = (lo + hi) / 2.0
    n, conv = diluted_at(v, shares, basis)
    return v, n, conv


def compute_discount(inp, flags):
    """From the discount-rate inputs to the rates every scenario is valued at.

    1. Cost of equity by CAPM:  ke = risk-free + beta x equity risk premium (+ any extra premium).
           4.3% + 1.30 x 5.0% = 10.8%
    2. The anchor - the rate that matches the cash flows being discounted:
           equity basis  -> ke          (the cash flows belong to shareholders only)
           firm basis    -> WACC = E/(D+E) x ke  +  D/(D+E) x cost of debt x (1 - tax)
                                        (the cash flows belong to lenders and shareholders together)
    3. Round the anchor onto the grid of hurdle rates: r* = the nearest grid rate, a tie going to
       the higher one. 10.48% -> 10%; 11.0% -> 12%. The grid grows upward if the anchor is above it.
    4. r_hi = the next grid rate above r*: the rate the values are stress-tested at.

    Why round at all? A WACC quoted to two decimals claims a precision nobody has, and rounding
    to a small set of stated hurdle rates makes the choice visible. The exact anchor is still
    printed, and the base case is also valued at it for reference.

    Returns a dict; the entries the rest of the program uses are "primary_rate" (r*),
    "sensitivity_rate" (r_hi) and "rates" (every rate each scenario will be valued at).
    """
    d, basis = inp["discount"], inp["model"]["basis"]
    price = inp["market"]["price"]
    # 1. CAPM cost of equity.
    ke = d["risk_free"] + d["beta"] * d["equity_risk_premium"] + d["additional_premium"]
    out = {"risk_free": d["risk_free"], "equity_risk_premium": d["equity_risk_premium"], "beta": d["beta"],
           "additional_premium": d["additional_premium"], "cost_of_equity": ke,
           "pre_tax_cost_of_debt": d["pre_tax_cost_of_debt"], "tax_rate": d["tax_rate"],
           "wacc": None, "debt_weight": None, "weight_source": None,
           "market_cap": None, "debt_for_weights": None}
    # Market value of the equity and of the debt, for the WACC weights. A convertible that is in the
    # money at today's price is already equity in the market's eyes, so it moves from debt to shares.
    if price is not None:
        n, conv = diluted_at(price, inp["shares"], basis)
        out["market_cap"] = price * n
        out["debt_for_weights"] = max(inp["bridge"]["debt"] - conv, 0.0)
    # 2. The anchor.
    if basis == "equity":
        anchor, anchor_name = ke, "cost of equity"
    else:
        # wd = the weight of debt in the capital structure, from the first source available:
        if d["debt_to_capital"] is not None:
            wd, src = d["debt_to_capital"], "analyst input (debt_to_capital)"
        elif out["market_cap"] is not None:
            # NOTE: this branch is the only way the share price can reach a scenario value. A
            # different price changes the weights, so the WACC, and can tip r* onto the next grid
            # rate. Supplying debt_to_capital (or primary_rate) removes the dependence entirely.
            dv = out["debt_for_weights"]
            wd, src = dv / (dv + out["market_cap"]), "market values (debt / (debt + market cap))"
        elif inp["bridge"]["debt"] == 0:
            wd, src = 0.0, "no debt"
        else:
            raise InputError(["discount_rate: the WACC needs capital-structure weights - give market.price "
                              "or discount_rate.debt_to_capital"])
        if wd > 0 and (d["pre_tax_cost_of_debt"] is None or d["tax_rate"] is None):
            raise InputError(["discount_rate: the company carries debt, so 'pre_tax_cost_of_debt' and "
                              "'tax_rate' are required for the WACC"])
        # Interest is tax-deductible, so debt costs the company its coupon less the tax saved.
        # (`x or 0.0`: both inputs may be missing when there is no debt, and then wd is 0 anyway.)
        kd_after = (d["pre_tax_cost_of_debt"] or 0.0) * (1.0 - (d["tax_rate"] or 0.0))
        out["debt_weight"], out["weight_source"] = wd, src
        out["wacc"] = (1.0 - wd) * ke + wd * kd_after
        anchor, anchor_name = out["wacc"], "WACC"
    out["anchor"], out["anchor_name"] = anchor, anchor_name

    # 3. Round the anchor onto the grid.
    # First make sure the grid reaches high enough: while the anchor is at least as close to the
    # NEXT step above the top as to the top itself, add that step. A 16.5% anchor against
    # 10/12/14 adds 16%. Without this, a risky name's 17% would be "rounded" down to 14%.
    grid = list(d["grid"])
    extended = False
    while anchor >= grid[-1] + GRID_STEP / 2 - 1e-9:      # a tie at the top goes up, as it does inside the grid
        grid.append(round(grid[-1] + GRID_STEP, 6))
        extended = True
    if extended:
        flags.add("NOTE", "N-GRID-EXTENDED", None,
                  f"The {anchor_name} anchor ({anchor:.1%}) sits above the rate grid, so the grid was extended to "
                  f"{grid[-1]:.0%}; a hurdle rate is never rounded a full point below its anchor.")
    # The grid is NOT extended downward. A 7.5% anchor against a 10% floor stays at 10%: the grid
    # is a set of hurdle rates, and a low computed rate is not allowed to lower the hurdle by itself.
    if anchor < grid[0] - 0.01 - 1e-9:
        flags.add("NOTE", "N-GRID-FLOOR", None,
                  f"The {anchor_name} anchor ({anchor:.1%}) is below the grid floor ({grid[0]:.0%}); r* is held at "
                  "the floor as a hurdle rate. Add 0.08 to the grid only for a genuinely low-beta compounder, and say so.")
    if d["primary_rate"] is not None:
        r_star = round(d["primary_rate"], 6)
        flags.add("WARN", "W-RATE-OVERRIDE", None,
                  f"Primary rate overridden to {r_star:.1%} (anchor {anchor:.1%}). Reason given: "
                  f"{d['primary_rate_reason']}. The memo must state the override and the reason.")
    else:
        # "The grid rate nearest the anchor; on a tie, the higher one" in one line. Each rate is
        # scored by the pair (distance to the anchor, minus the rate) and the smallest pair wins:
        # the distance decides, and when two distances are equal the larger rate has the smaller
        # "minus the rate". round(.., 9) keeps floating-point dust (0.11 - 0.10 is not exactly
        # 0.12 - 0.11 in binary) from deciding a tie.
        r_star = min(grid, key=lambda x: (round(abs(x - anchor), 9), -x))
    # 4. r_hi: the next rate above r* - or one more step if r* is already the top of the grid.
    higher = [x for x in grid if x > r_star + 1e-9]
    r_hi = higher[0] if higher else round(r_star + GRID_STEP, 6)
    out["grid"] = grid
    out["primary_rate"], out["sensitivity_rate"] = r_star, r_hi
    # Every rate a scenario gets valued at: the whole grid, plus r* and r_hi in case an override or
    # a top-of-grid r* put them outside it.
    out["rates"] = sorted({round(x, 6) for x in grid + [r_star, r_hi]})
    out["override"] = d["primary_rate"] is not None
    return out


# =============================================================================
# Cash-flow projections
# =============================================================================
# A "projection" is one scenario turned into numbers: a cash flow for every forecast year, plus
# one extra "terminal year" that stands for everything afterwards. No discount rate appears
# anywhere in this section - that separation is what lets one projection be valued at every rate.
#
# A forecast has up to three stages:
#     explicit years   1 .. n_exp     the analyst's year-by-year view: levels, then growth rates
#     fade years       the next F     growth and ratios glide in a straight line towards their
#                                     terminal values, so nothing jumps on the forecast's last day
#     terminal year    N + 1          one year at terminal growth and terminal ratios; the
#                                     perpetuity is built on its cash flow

def build_levels(level, fade, g_term, ov):
    """Explicit levels, then growth, then a linear fade of growth towards terminal growth.

    Builds the revenue path (or the EPS path in mode "eps"). Returns (levels, growths), one
    entry per forecast year: explicit years first, fade years after.

    With base 100, levels [120], growth [0.20, 0.14], three fade years and terminal growth 2%:
        explicit   120 (+20% on the base), 144 (+20%), 164.2 (+14%)
        fade       growth steps evenly down from 14% towards 2%:  +11%, +8%, +5%
        terminal   built by the caller, one more equal step down: +2%
    The gap is cut into fade + 1 equal steps so that the terminal year lands exactly on terminal
    growth instead of repeating the last fade year's rate.

    ov["constant_growth"] (set by the reverse-DCF solver) replaces every growth rate of the
    explicit period with one number. Fixed levels - the consensus years - are left alone.
    """
    growth = level["growth"]
    if "constant_growth" in ov:
        growth = [ov["constant_growth"]] * len(growth)
    levels, growths = [], []
    prev = level["base"]
    # 1. Years given as explicit levels. Their growth rate is worked out only so it can be shown;
    #    from a zero or negative start (a loss) a growth rate is meaningless -> nan, printed as "n/a".
    for x in level["fixed"]:
        growths.append(x / prev - 1.0 if prev > 0 else float("nan"))
        levels.append(x)
        prev = x
    # 2. Years given as growth rates: compound from the previous year.
    for g in growth:
        prev *= 1.0 + g
        levels.append(prev)
        growths.append(g)
    # 3. Fade years. If the last growth rate is undefined (EPS has only just turned positive)
    #    there is nothing sensible to fade from, so grow at the terminal rate.
    g_last = growths[-1]
    if math.isnan(g_last):
        g_last = g_term
    for j in range(1, fade + 1):
        g = g_last + (g_term - g_last) * j / (fade + 1)
        prev *= 1.0 + g
        levels.append(prev)
        growths.append(g)
    return levels, growths


def full_path(explicit, terminal_value, fade):
    """Explicit path, then a linear fade to the terminal value (flat if none is given).

    The growth fade of build_levels(), applied to a ratio (a margin, capex as a share of
    revenue, ...). Returns (the path over every forecast year, the terminal-year value).
    Margin 10% in each explicit year, terminal value 18%, three fade years: the fade years are
    12%, 14%, 16% and the terminal year is 18%. Without a terminal value the ratio just stays
    where the explicit period left it.
    """
    last = explicit[-1]
    tv = last if terminal_value is None else terminal_value
    return explicit + [last + (tv - last) * j / (fade + 1) for j in range(1, fade + 1)], tv


def year_labels(meta, n):
    """Labels for years 1..n and the terminal year, e.g. FY2027, FY2028, ... from first_forecast_label."""
    label = meta.get("first_forecast_label")
    if label:
        # Find the last run of 2 or 4 digits (the "2027" in "FY2027E") and count up from it, keeping
        # whatever surrounds it. n + 1 labels are returned: the extra one names the terminal year.
        runs = [m for m in re.finditer(r"\d+", label) if len(m.group()) in (2, 4)]
        if runs:
            m = runs[-1]
            year, width = int(m.group()), len(m.group())
            return [label[: m.start()] + str(year + i).zfill(width)[-width:] + label[m.end():] for i in range(n + 1)]
    return [f"Y{i + 1}" for i in range(n + 1)]


def project(sc, inp, ov=None):
    """Build one scenario's yearly cash flows and its terminal year.

    sc    the scenario, as norm_scenario() left it
    ov    optional overrides for this one call - how every "what if" in the program is asked:
              terminal_growth   use this g instead of the scenario's            (sensitivity table)
              exit_multiple     use this multiple instead of the scenario's     (sensitivity table)
              constant_growth   one growth rate across the explicit period      (reverse DCF)
              margin_shift      add this many points to the margin every year   (reverse DCF)
              flow_scale        multiply every cash flow by this                (reverse DCF, direct)

    Returns `proj`, a dict:
        flows          the cash flow of each forecast year - the only thing value_at() discounts
        terminal_fcf   the terminal year's cash flow, on which the perpetuity is built
        g, method      terminal growth and terminal method
        rows           the same years line by line (revenue, EBIT, tax, ...), for the report
        terminal_row   the terminal year line by line
        metrics        the last forecast year's EBITDA / EBIT / EPS / ...: what an exit multiple
                       is applied to, and what the "implied terminal multiple" is measured against
        diag           by-products the checks need (implied return on new capital, last growth, ...)
        per_share      True in mode "eps", where every figure is already per share
        n              the number of forecast years (explicit + fade)

    There is one branch per mode. They differ only in how a year's cash flow is put together;
    all of them fill in the same `proj`.
    """
    ov = ov or {}
    mode = inp["model"]["mode"]
    t = sc["terminal"]
    g = ov.get("terminal_growth", t["growth"])
    O = t["overrides"]            # terminal-year values the scenario set explicitly ({} = none)
    fade = sc["fade"]
    proj = {"mode": mode, "per_share": mode == "eps", "g": g, "method": t["method"], "terminal_fcf": None,
            "rows": [], "flows": [], "diag": {}, "metrics": {}, "terminal_row": {}}

    # ---- mode "direct": the cash flows are supplied; nothing to build ---------------------------------
    if mode == "direct":
        scale = ov.get("flow_scale", 1.0)
        flows = [x * scale for x in sc["fcf"]]
        for i, f in enumerate(flows):
            row = {"fcf": f}
            if sc.get("display_revenue"):
                row["revenue"] = sc["display_revenue"][i]
            proj["rows"].append(row)
        proj["flows"] = flows
        # Terminal cash flow: the analyst's own normalised figure if one was given; otherwise the
        # last year's, grown one more year at g. (The program cannot rebuild a terminal year here -
        # it does not know what the cash flows are made of.)
        tf = t["fcf"] * scale if t["fcf"] is not None else flows[-1] * (1.0 + g)
        proj["terminal_fcf"] = tf
        proj["terminal_row"] = {"fcf": tf}
        proj["metrics"] = {"fcf": flows[-1]}
        proj["diag"]["terminal_basis"] = ("analyst-supplied terminal cash flow" if t["fcf"] is not None
                                          else "final-year cash flow grown at g")

    # ---- mode "eps": owner earnings per share = EPS x FCF conversion ----------------------------------
    elif mode == "eps":
        eps, gr = build_levels(sc["level"], fade, g, ov)
        conv, conv_t = full_path(sc["paths"]["fcf_conversion"], O.get("fcf_conversion"), fade)
        for i, e in enumerate(eps):
            oe = e * conv[i]      # the part of this year's EPS that reaches the owner as cash
            proj["rows"].append({"eps": e, "growth": gr[i], "conversion": conv[i], "fcf": oe})
            proj["flows"].append(oe)
        # Terminal-year EPS: a stated normalised figure (the mid-cycle level, for a cyclical caught
        # at a peak) or else the last year's EPS grown at g - times the terminal conversion.
        eps_t = t["eps"] if t["eps"] is not None else eps[-1] * (1.0 + g)
        proj["terminal_fcf"] = eps_t * conv_t
        proj["terminal_row"] = {"eps": eps_t, "conversion": conv_t, "fcf": eps_t * conv_t,
                                "growth": eps_t / eps[-1] - 1.0 if eps[-1] > 0 else float("nan")}
        proj["metrics"] = {"eps": eps[-1], "owner_earnings": proj["flows"][-1]}
        proj["diag"]["terminal_profit_metric"] = eps_t
        proj["diag"]["last_growth"] = gr[-1]

    # ---- modes "drivers" and "fcf_margin": both start from a revenue path ------------------------------
    else:
        rev, gr = build_levels(sc["level"], fade, g, ov)
        shift = ov.get("margin_shift", 0.0)     # reverse DCF: "what if every margin were this much higher?"
        prev = sc["level"]["base"]              # last year's revenue, for the change in working capital
        rev_t = rev[-1] * (1.0 + g)             # terminal-year revenue: the last forecast year grown at g
        P = sc["paths"]
        # "fcf_margin": the shortcut. Cash flow = revenue x free-cash-flow margin - less SBC when the
        # margin supplied was before SBC.
        if mode == "fcf_margin":
            margin, m_t = full_path(P["fcf_margin"], O.get("fcf_margin"), fade)
            if sc["sbc_deducted"]:
                sbc, sbc_t = [0.0] * len(margin), 0.0
            else:
                sbc, sbc_t = full_path(P["sbc_pct_revenue"], O.get("sbc_pct_revenue"), fade)
            for i, r in enumerate(rev):
                m = margin[i] + shift - sbc[i]
                proj["rows"].append({"revenue": r, "growth": gr[i], "fcf_margin": m, "fcf": r * m})
                proj["flows"].append(r * m)
            m_te = m_t + shift - sbc_t
            proj["terminal_fcf"] = rev_t * m_te
            proj["terminal_row"] = {"revenue": rev_t, "growth": g, "fcf_margin": m_te, "fcf": rev_t * m_te}
            proj["metrics"] = {"fcf": proj["flows"][-1], "revenue": rev[-1]}
            proj["diag"]["terminal_profit_metric"] = m_te
        # "drivers": the full build, line by line from revenue to free cash flow.
        else:
            # Each ratio as a path over all forecast years (explicit, then fade), plus the value it
            # takes in the terminal year (the *_t names).
            margin, m_t = full_path(P["ebit_margin"], O.get("ebit_margin"), fade)
            taxr, tax_t = full_path(P["tax_rate"], O.get("tax_rate"), fade)
            da, da_t = full_path(P["da_pct_revenue"], O.get("da_pct_revenue"), fade)
            capex, capex_t = full_path(P["capex_pct_revenue"], O.get("capex_pct_revenue"), fade)
            nwc, nwc_t = full_path(P["nwc_pct_incremental_revenue"], O.get("nwc_pct_incremental_revenue"), fade)
            if sc["margin_basis"] == "non_gaap":
                sbc, sbc_t = full_path(P["sbc_pct_revenue"], O.get("sbc_pct_revenue"), fade)
            else:
                sbc, sbc_t = [0.0] * len(margin), 0.0
            # One forecast year at a time (here `r` is that year's REVENUE, not a discount rate):
            #       EBIT             revenue x EBIT margin, after SBC
            #     - cash tax         on EBIT, after using any tax losses carried forward
            #     + D&A              a non-cash charge inside EBIT, so it is added back
            #     - capex            cash spent on fixed assets
            #     - change in NWC    working capital needed for THIS year's increase in revenue
            #     = free cash flow
            nol = sc["nol_balance"]             # running pool of tax losses carried forward
            for i, r in enumerate(rev):
                m = margin[i] + shift - sbc[i]
                ebit = r * m
                # A loss pays no tax and is added to the pool. A profit first draws on the pool -
                # up to the usage limit - and is taxed only on what is left.
                if ebit <= 0:
                    tax = 0.0
                    nol += -ebit
                else:
                    used = min(nol, sc["nol_usage_limit"] * ebit)
                    nol -= used
                    tax = taxr[i] * (ebit - used)
                d_amt, cx, dn = r * da[i], r * capex[i], nwc[i] * (r - prev)
                fcf = ebit - tax + d_amt - cx - dn
                proj["rows"].append({"revenue": r, "growth": gr[i], "ebit_margin": m, "ebit": ebit, "tax": tax,
                                     "nopat": ebit - tax, "da": d_amt, "capex": cx, "d_nwc": dn, "fcf": fcf,
                                     "fcf_margin": fcf / r, "nol_end": nol})
                proj["flows"].append(fcf)
                prev = r
            # ---- The terminal year (N + 1): rebuilt from terminal ratios, not copied from year N. ----
            # Year N's cash flow carries year N's reinvestment, which was sized for year N's growth.
            # Growing that by g and capitalising it would freeze the mismatch in for ever. So the
            # terminal year is built afresh: revenue up by g, terminal margin and tax, and
            # reinvestment sized for growth of g.
            m_te = m_t + shift - sbc_t
            ebit_t = rev_t * m_te
            tax_amt = max(ebit_t, 0.0) * tax_t      # full tax: a finite pool of losses cannot shelter a perpetuity
            nopat_t = ebit_t - tax_amt
            row = {"revenue": rev_t, "growth": g, "ebit_margin": m_te, "ebit": ebit_t, "tax": tax_amt, "nopat": nopat_t}
            if t["method"] == "value_driver":
                # Value-driver formula. To grow at g while earning RONIC on each new dollar invested,
                # the business must reinvest g / RONIC of its profit; the rest is free cash flow.
                # g 3% with RONIC 15%: reinvest 20%, keep 80%.
                rr = g / t["ronic"]
                fcf_t = nopat_t * (1.0 - rr)
                proj["diag"].update({"reinvestment_rate": rr, "implied_ronic": t["ronic"], "ronic_is_input": True})
            else:
                # Gordon: use the terminal ratios as given, then work BACKWARDS to the return on new
                # capital they imply, so it can be checked:
                #     reinvestment rate = (capex - D&A + change in NWC) / NOPAT
                #     implied RONIC     = g / reinvestment rate
                # A terminal year that grows without net reinvestment implies an infinite return;
                # scenario_flags() reports that, and an implausibly high one.
                da_amt, cx_amt, dn_amt = rev_t * da_t, rev_t * capex_t, nwc_t * (rev_t - rev[-1])
                fcf_t = nopat_t + da_amt - cx_amt - dn_amt
                row.update({"da": da_amt, "capex": cx_amt, "d_nwc": dn_amt})
                net_reinvestment = cx_amt - da_amt + dn_amt
                rr = net_reinvestment / nopat_t if nopat_t > 0 else None
                proj["diag"].update({"reinvestment_rate": rr, "ronic_is_input": False,
                                     "implied_ronic": (g / rr) if (rr is not None and rr > 0 and g > 0) else None,
                                     "terminal_capex_pct": capex_t})
            row["fcf"] = fcf_t
            row["fcf_margin"] = fcf_t / rev_t
            proj["terminal_fcf"] = fcf_t
            proj["terminal_row"] = row
            last = proj["rows"][-1]
            proj["metrics"] = {"ebitda": last["ebit"] + last["da"], "ebit": last["ebit"], "nopat": last["nopat"],
                               "fcf": last["fcf"], "revenue": last["revenue"]}
            proj["diag"]["terminal_profit_metric"] = m_te
            proj["diag"]["last_modelled_margin"] = proj["rows"][-1]["ebit_margin"]
            proj["diag"]["nol_left"] = nol
        proj["diag"]["last_growth"] = gr[-1]
        proj["diag"]["revenue_n"] = rev[-1]

    # With an exit multiple the terminal value is "last forecast year's metric x the multiple", so
    # note which metric, its value, and the multiple (or the sensitivity table's override of it).
    if t["method"] == "exit_multiple":
        proj["exit_metric"] = t["exit_metric"]
        proj["exit_multiple"] = ov.get("exit_multiple", t["exit_multiple"])
        proj["exit_metric_value"] = proj["metrics"][t["exit_metric"]]
    proj["n"] = len(proj["flows"])
    return proj


# =============================================================================
# Valuation
# =============================================================================
# The other half of the separation: take a projection and ONE discount rate, return a value.
#
#     operating value  =  PV of each forecast year's cash flow  +  PV of the terminal value
#     equity value     =  operating value + net bridge            (firm basis only)
#     value per share  =  equity value / diluted shares

def timing_table(n, stub, timing):
    """(weight, time in years) of each year's cash flow, and the horizon (end of year n).

    "Time" is how far from the valuation date a cash flow is taken to arrive: the exponent it
    is discounted by. "Weight" is how much of the year's cash flow counts: 1, except for a partly
    elapsed year 1, which counts only its remaining fraction (the stub).

    No stub (year 1 = the next twelve months), three years:
        end_year   times 1.0, 2.0, 3.0    cash treated as arriving on the last day of each year
        mid_year   times 0.5, 1.5, 2.5    cash arrives all through the year - on average, mid-year
    Stub 0.63 (63% of year 1 still to come), mid_year:
        year 1     weight 0.63, time 0.315    the middle of the stretch that remains
        year 2     weight 1,    time 1.13     0.63 to reach the end of year 1, plus half a year
        horizon    0.63 + 2 = 2.63            the end of year 3, where the terminal value sits
    Mid-year values run about half a year's return above end-year ones (roughly 5% at r = 10%).
    """
    mid = timing == "mid_year"
    out = []
    for t in range(1, n + 1):
        if t == 1:
            out.append((stub, stub / 2.0 if mid else stub))
        else:
            out.append((1.0, stub + (t - 1) - (0.5 if mid else 0.0)))
    return out, stub + n - 1


def value_at(proj, r, inp):
    """Value one projection at one discount rate.

    Four steps: (1) the present value of each forecast year's cash flow; (2) the terminal value
    at the end of the forecast, discounted back to today; (3) operating value -> equity value ->
    value per share; (4) diagnostics. Returns a dict: "value_per_share" is the headline, and
    everything else in it is there to explain that number.
    """
    model, bridge, shares = inp["model"], inp["bridge"], inp["shares"]
    # (1) Forecast years:  PV = weight x cash flow / (1 + r)^time, with the weights and times from
    #     timing_table(). `pvs` keeps each year's PV so the report can show it beside the cash flow.
    tt, horizon = timing_table(proj["n"], inp["meta"]["stub"], model["timing"])
    pvs = [w * f * (1.0 + r) ** (-tau) for (w, tau), f in zip(tt, proj["flows"])]
    pv_explicit = sum(pvs)
    # (2) Terminal value. `tv_h` is its value AT THE HORIZON - the end of the last forecast year.
    #       exit multiple   the last forecast year's metric x the multiple
    #       otherwise       a growing perpetuity: next year's cash flow / (r - g)
    #     The perpetuity formula assumes each cash flow arrives at a year-end. With mid-year timing
    #     they all arrive half a year sooner, which makes the stream worth (1 + r)^0.5 more.
    mid_adj = (1.0 + r) ** 0.5 if model["timing"] == "mid_year" else 1.0
    g = proj["g"]
    if proj["method"] == "exit_multiple":
        tv_h = proj["exit_metric_value"] * proj["exit_multiple"]
    else:
        tv_h = proj["terminal_fcf"] / (r - g) * mid_adj
    pv_tv = tv_h * (1.0 + r) ** (-horizon)      # ...and from the horizon back to today
    op_value = pv_explicit + pv_tv
    # (3) From the business to one share.
    firm = model["basis"] == "firm"
    if proj["per_share"]:
        # Mode "eps": every figure is per share already. On a firm basis net cash per share is
        # added; the share count is used as given (the EPS is taken to be on a diluted count).
        n = shares["count"]
        bridge_ps = bridge["net"] / n if firm else 0.0
        raw, converted = op_value + bridge_ps, 0.0
        equity = raw * n
    else:
        # Totals: add the net bridge to reach equity, then let per_share_value() settle how many
        # shares there are at that value (options, convertibles). Converted notes stop being debt,
        # so their principal comes back into equity.
        equity_pre = op_value + (bridge["net"] if firm else 0.0)
        raw, n, converted = per_share_value(equity_pre, shares, model["basis"])
        equity = equity_pre + converted

    # (4a) Peak cash burn. Walk through the years keeping a running total of cash flow; its lowest
    #      point is how much outside money the scenario needs before the business funds itself.
    cum, trough = 0.0, 0.0
    for (w, _), f in zip(tt, proj["flows"]):
        cum += w * f
        trough = min(trough, cum)

    # (4b) What the terminal value quietly assumes. An exit multiple hides a growth rate: solving
    #      TV = FCF x (1 + g) / (r - g) for g brings it into the open. And any terminal value can be
    #      restated as a multiple of the last forecast year's EBITDA / EPS / FCF.
    fcf_n = proj["flows"][-1]
    implied_g = None
    if proj["method"] == "exit_multiple" and fcf_n > 0 and tv_h > 0:
        implied_g = (tv_h * r - mid_adj * fcf_n) / (tv_h + mid_adj * fcf_n)
    implied_mult = {k: tv_h / v for k, v in proj["metrics"].items() if v and v > 0}
    # "value_per_share_raw" may be negative (debt above operating value). The solvers need that
    # unbroken number to search on; "value_per_share" floors it at zero, because a shareholder
    # cannot lose more than everything.
    return {"rate": r, "pv_explicit": pv_explicit, "tv_at_horizon": tv_h, "pv_terminal": pv_tv,
            "operating_value": op_value, "tv_share": pv_tv / op_value if op_value > 0 else None,
            "equity_value": equity, "diluted_shares": n, "converted_principal": converted,
            "value_per_share_raw": raw, "value_per_share": max(raw, 0.0),
            "pvs": pvs, "horizon": horizon, "funding_trough": -trough,
            "implied_perpetual_growth": implied_g, "implied_multiples": implied_mult}


def scenario_value(sc, r, inp, ov=None):
    """Project and value in one call. This is the form the sensitivity table and the reverse-DCF
    solvers use: each of their evaluations is a fresh projection with one assumption overridden."""
    return value_at(project(sc, inp, ov), r, inp)


# =============================================================================
# Flags
# =============================================================================
# A flag is the program saying "I computed this, but look here". A flag never changes a number.
#     WARN   the memo has to either fix the input or disclose the weakness
#     NOTE   information; nothing needs fixing
# Each flag has a short code (W-... or N-...) so it can be searched for, the scenario it concerns
# (None when it concerns the whole model), and a message written so it can go into the memo.
#
# Where flags are raised:
#     compute_discount()   about the rate: grid extended or floored, r* overridden
#     scenario_flags()     about one scenario: terminal value, growth, reinvestment, history
#     analyze()            about the model as a whole: slots, weights, units, sources, stale data

class Flags:
    """The flags raised in one run. sorted() lists warnings before notes and otherwise keeps the
    order in which they were raised (Python's sort leaves equal items in their original order)."""
    ORDER = {"WARN": 0, "NOTE": 1}

    def __init__(self):
        self.items = []

    def add(self, level, code, scenario, message):
        self.items.append({"level": level, "code": code, "scenario": scenario, "message": message})

    def sorted(self):
        return sorted(self.items, key=lambda f: self.ORDER[f["level"]])


def cyclical_check(sc, proj, model):
    """A cyclical's terminal economics must mean-revert to mid-cycle.

    The mistake this guards against is capitalising a boom: taking a cyclical's peak margin and
    carrying it into the perpetuity, where it is multiplied by ten or more. The skill's valuation
    framework calls such a scenario inadmissible. The test compares the scenario's terminal-year
    profitability with a mid-cycle anchor the analyst supplies:
        mode drivers      terminal EBIT margin   vs  model.mid_cycle_ebit_margin
        mode fcf_margin   terminal FCF margin    vs  model.mid_cycle_fcf_margin
        mode eps          terminal-year EPS      vs  model.mid_cycle_eps_at_horizon
    and passes when the terminal figure is no more than mid_cycle_tolerance (10%) above the anchor.

    Returns {"status", "detail"}, the status being one of:
        n/a            the company is not marked cyclical
        admissible     the terminal year is back at mid-cycle
        inadmissible   it is not: the scenario may be shown but must not feed the plan
        unverified     marked cyclical, but no anchor was supplied to test against
    """
    if not model["cyclical"]:
        return {"status": "n/a", "detail": "not flagged cyclical"}
    key = {"drivers": "mid_cycle_ebit_margin", "fcf_margin": "mid_cycle_fcf_margin",
           "eps": "mid_cycle_eps_at_horizon"}.get(model["mode"])
    anchor = model.get(key) if key else None
    metric = proj["diag"].get("terminal_profit_metric")
    if anchor is None or metric is None:
        return {"status": "unverified",
                "detail": f"no mid-cycle anchor supplied ({key or 'not available in mode direct'})"}
    # Allowed ceiling: the anchor plus the tolerance. (For a negative anchor "10% above" has no
    # clean meaning, so the anchor itself is the ceiling.)
    limit = anchor * (1.0 + model["mid_cycle_tolerance"]) if anchor >= 0 else anchor
    ok = metric <= limit + 1e-12
    # How to print the two figures: dollars for EPS, a percentage for a margin.
    fmt = (lambda x: f"${x:,.2f}") if model["mode"] == "eps" else (lambda x: f"{x:.1%}")
    return {"status": "admissible" if ok else "inadmissible",
            "detail": f"terminal {fmt(metric)} vs mid-cycle {fmt(anchor)} (tolerance {model['mid_cycle_tolerance']:.0%})"}


def scenario_flags(sc, proj, v_star, r_star, inp, flags, adm):
    """Every check that concerns ONE scenario. Nothing in here changes a value: each test either
    adds a flag or does nothing.

    v_star   this scenario's valuation at r*, from value_at()
    adm      the result of cyclical_check()

    The checks, in order:
        terminal value      growth above the cap; r* too close to g; a terminal cash flow that is
                            not positive; a terminal value that dominates the total
        the hand-over       growth falling off a cliff as the forecast ends
        reinvestment        (mode drivers) growth that is not paid for; an implausible return on
                            new capital; a margin that improves only in the terminal year
        terminal multiple   an exit multiple that implies too much growth; a terminal value
                            richer than mature peers trade at
        solvency            equity wiped out; a cash burn larger than the cash in hand
        cyclicality and the authorship label
        history             terminal margin, year-1 margin, capex and return on capital, each
                            against the company's own record
        typing              growth above 150% in a year - usually a percentage not divided by 100
    """
    name, model = sc["name"], inp["model"]
    g, t = proj["g"], sc["terminal"]
    is_base = sc["slot"] == "base"
    # --- terminal value ----------------------------------------------------------------------------
    # Nothing outgrows the economy for ever: a company growing 3.5% in a 3% economy ends up being it.
    if g > model["terminal_growth_cap"] + 1e-9:
        flags.add("WARN", "W-TG-CAP", name,
                  f"Terminal growth {g:.2%} exceeds the cap of {model['terminal_growth_cap']:.2%} (nominal GDP). "
                  "Lower it, or justify the exception in the memo.")
    if proj["method"] != "exit_multiple":
        # A perpetuity is worth cash flow / (r - g). With r - g at 3%, moving either input by a
        # quarter of a point moves the terminal value by nearly a tenth.
        if r_star - g < THIN_SPREAD:
            flags.add("WARN", "W-THIN-SPREAD", name,
                      f"r* minus terminal growth is {r_star - g:.1%}; below {THIN_SPREAD:.0%} the terminal value "
                      "swings violently with either input.")
        if proj["terminal_fcf"] <= 0:
            flags.add("WARN", "W-TERMINAL-NEGATIVE", name,
                      "Terminal-year cash flow is not positive, so the perpetuity is worth nothing or less. "
                      "The scenario never reaches self-funding; say so rather than reading the number.")
    # When most of the value lies beyond the forecast, the answer is mostly the terminal
    # assumptions - the part of the model with the least evidence behind it.
    if v_star["tv_share"] is not None and v_star["tv_share"] > TV_SHARE_DIRECTIONAL:
        flags.add("WARN", "W-TV-SHARE", name,
                  f"Terminal value is {v_star['tv_share']:.0%} of operating value at r* (threshold "
                  f"{TV_SHARE_DIRECTIONAL:.0%}); treat this scenario's value as directional.")
    # --- the hand-over from forecast to perpetuity ---------------------------------------------------
    # A business growing 20% in its last forecast year does not grow 3% the next morning, and its
    # margins and reinvestment in that last year belong to a 20%-growth company. A fade fixes both.
    last_g = proj["diag"].get("last_growth")
    if (last_g is not None and not math.isnan(last_g) and proj["mode"] != "direct"
            and last_g - g > GROWTH_CLIFF and sc["fade"] == 0):
        flags.add("WARN", "W-GROWTH-CLIFF", name,
                  f"Growth drops from {last_g:.1%} in the last modelled year to {g:.1%} in perpetuity with no fade. "
                  "Add fade_years (or lengthen the explicit period) so growth and reinvestment decline together.")
    # --- reinvestment in the terminal year (only mode "drivers" models it) ---------------------------
    # rr    = the share of terminal-year profit ploughed back (net capex + working capital) / NOPAT
    # ronic = the return that reinvestment has to earn to produce growth of g:  g / rr
    d = proj["diag"]
    if proj["mode"] == "drivers":
        rr, ronic = d.get("reinvestment_rate"), d.get("implied_ronic")
        if not d.get("ronic_is_input"):         # with value_driver the return is an input, not a by-product
            if g > 0 and rr is not None and rr <= 0:
                flags.add("WARN", "W-NO-REINVESTMENT", name,
                          f"The terminal year grows {g:.1%} with no net reinvestment (capex <= D&A and no "
                          "working-capital build), i.e. an infinite return on new capital. Raise terminal "
                          "capex/NWC or use value_driver.")
            elif ronic is not None and ronic > RONIC_HIGH:
                flags.add("WARN", "W-RONIC-HIGH", name,
                          f"Terminal reinvestment implies a {ronic:.0%} return on new invested capital "
                          f"(above {RONIC_HIGH:.0%}); terminal capex looks too light for {g:.1%} growth.")
        # Growth adds value only when new capital earns more than it costs. Below that, each extra
        # point of terminal growth makes the business worth LESS. Legitimate, so a note.
        if ronic is not None and ronic < r_star:
            flags.add("NOTE", "N-RONIC-BELOW-RATE", name,
                      f"Terminal return on new capital ({ronic:.1%}) is below r* ({r_star:.0%}): terminal growth "
                      "destroys value in this scenario.")
        if d.get("nol_left", 0) > 1e-9:
            flags.add("NOTE", "N-NOL-UNUSED", name,
                      "A loss carry-forward remains at the end of the forecast and is not valued.")
        # A margin that improves only in the terminal year adds value in the one place nobody can
        # inspect, and the perpetuity then multiplies it.
        step = d["terminal_profit_metric"] - d["last_modelled_margin"]
        if step > 0.01:
            flags.add("WARN", "W-TERMINAL-STEP-UP", name,
                      f"The terminal EBIT margin is {step * 100:.1f} points above the last modelled year. "
                      "Put the improvement in the forecast years, where it can be seen and challenged.")
    # --- the terminal value restated as a multiple, or the multiple restated as growth ---------------
    # An exit multiple and a perpetuity are two ways of writing the same number, so each is
    # checked in the other's terms: does the multiple imply growth above the cap, and does the
    # terminal value amount to a richer multiple than mature peers actually trade at?
    if proj["method"] == "exit_multiple":
        ig = v_star["implied_perpetual_growth"]
        if ig is not None and ig > model["terminal_growth_cap"] + 1e-9:
            flags.add("WARN", "W-EXIT-IMPLIED-GROWTH", name,
                      f"The exit multiple implies {ig:.1%} perpetual growth at r*, above the "
                      f"{model['terminal_growth_cap']:.1%} cap.")
    mp = model["mature_peer_multiple"]
    if mp:
        im = v_star["implied_multiples"].get(mp["metric"])
        if im is not None and im > mp["value"] * 1.0001:
            flags.add("WARN", "W-TERMINAL-MULTIPLE", name,
                      f"Terminal value is {im:.1f}x {mp['metric']} at the horizon, above the mature-peer "
                      f"{mp['value']:.1f}x. A terminal richer than mature peers needs a stated reason.")
    # --- solvency ------------------------------------------------------------------------------------
    if v_star["value_per_share_raw"] <= 0:
        flags.add("WARN", "W-EQUITY-WIPED", name,
                  "Claims senior to equity exceed operating value at r*: equity is worth zero in this scenario.")
    # A DCF values the cash flows as if the money to survive the lean years were simply there. If
    # the burn is bigger than the cash in hand, that money has to be raised, and the scenario
    # includes neither the dilution nor the interest. So its value is too high by an unknown amount.
    cash = inp["bridge"]["cash_and_investments"]
    if not proj["per_share"] and model["basis"] == "firm" and v_star["funding_trough"] > cash + 1e-9:
        flags.add("WARN", "W-FUNDING-GAP", name,
                  f"Cumulative cash burn peaks at {v_star['funding_trough']:,.0f} against {cash:,.0f} of cash. "
                  "The scenario needs outside capital that the model does not charge for (dilution or interest).")
    if adm["status"] == "inadmissible":
        flags.add("WARN", "W-CYCLICAL-INADMISSIBLE", name,
                  f"Carries above-mid-cycle economics into perpetuity ({adm['detail']}). Context only: not an "
                  "admissible value for the Entry & Exit Plan (valuation-framework Module 4, rule 6).")
    elif adm["status"] == "unverified" and sc["slot"]:
        flags.add("WARN", "W-CYCLICAL-UNVERIFIED", name,
                  f"Cyclical name, but mean reversion could not be checked: {adm['detail']}.")
    if not sc["label"]:
        flags.add("NOTE", "N-NO-LABEL", name,
                  "No authorship label; Module 4 rule 8 wants 'consensus-anchored' or 'analyst construction'.")
    # --- against the company's own record ------------------------------------------------------------
    # For the base case these are warnings. For bear and bull they are notes: a bull case is
    # SUPPOSED to go beyond the record, and it is enough that the reader is told it does.
    hist = inp["history"]
    if hist and proj["mode"] in ("drivers", "fcf_margin"):
        level = "WARN" if is_base else "NOTE"
        hm = history_ratio(hist, "ebit" if proj["mode"] == "drivers" else "fcf")     # margin in each past period
        if hm:
            peak = max(hm)
            if d["terminal_profit_metric"] > peak + 0.02:
                flags.add(level, "W-MARGIN-ABOVE-HISTORY" if is_base else "N-MARGIN-ABOVE-HISTORY", name,
                          f"Terminal margin {d['terminal_profit_metric']:.1%} is above every year supplied in "
                          f"history (best {peak:.1%}). State what structurally changes.")
            # Year 1 against the latest actual. A jump of more than five points is rarely a forecast
            # and usually the commonest input mistake there is: an "adjusted" margin, which leaves
            # SBC out, typed in as a GAAP one. Always a warning, whichever scenario it is in.
            first = proj["rows"][0]["ebit_margin" if proj["mode"] == "drivers" else "fcf_margin"]
            if first - hm[-1] > 0.05:
                flags.add("WARN", "W-MARGIN-JUMP", name,
                          f"Year-1 margin {first:.1%} is {(first - hm[-1]) * 100:.1f} points above the latest actual "
                          f"({hm[-1]:.1%}). Check the margin basis first - a non-GAAP margin entered as GAAP "
                          "overstates cash flow by the whole of SBC - then the evidence for the step.")
        hc = history_ratio(hist, "capex")
        if hc and proj["mode"] == "drivers" and d.get("terminal_capex_pct") is not None:
            avg = sum(hc) / len(hc)
            if avg > 0 and d["terminal_capex_pct"] < 0.5 * avg:
                flags.add(level, "W-CAPEX-BELOW-HISTORY" if is_base else "N-CAPEX-BELOW-HISTORY", name,
                          f"Terminal capex is {d['terminal_capex_pct']:.1%} of revenue, under half the historical "
                          f"average of {avg:.1%}.")
        # The return on new capital the terminal year implies, against the best the company has
        # ever earned. (Above RONIC_HIGH the blunter W-RONIC-HIGH has been raised already.)
        roic = [x for x in (hist.get("roic") or []) if x is not None]
        ronic = d.get("implied_ronic")
        if roic and ronic is not None and not d.get("ronic_is_input") and ronic > 1.5 * max(roic) and ronic <= RONIC_HIGH:
            flags.add(level, "W-RONIC-ABOVE-HISTORY" if is_base else "N-RONIC-ABOVE-HISTORY", name,
                      f"Implied terminal return on new capital {ronic:.0%} is more than 1.5x the best historical "
                      f"ROIC supplied ({max(roic):.0%}).")
    # --- typing ----------------------------------------------------------------------------------------
    # Growth above 150% can be real (a start-up tripling) but is more often 2.5 typed for 2.5%.
    # It cannot be rejected outright, so it is pointed out - once per scenario (hence the break).
    for i, row in enumerate(proj["rows"]):
        gr = row.get("growth")
        if gr is not None and not math.isnan(gr) and gr > 1.5:
            flags.add("NOTE", "N-HYPERGROWTH", name,
                      f"Year {i + 1} growth is {gr:.0%}. Confirm this is intended and not a percentage entered "
                      "without dividing by 100.")
            break


def history_ratio(hist, key):
    """One history series as a share of revenue, period by period - EBIT / revenue gives the
    margin record, capex / revenue the capital intensity. Periods where either figure is missing
    are skipped; the result is [] when the series was not supplied at all."""
    rev, num = hist.get("revenue"), hist.get(key)
    if not rev or not num:
        return []
    return [n / r for n, r in zip(num, rev) if n is not None and r]


# =============================================================================
# Reverse DCF / implied expectations
# =============================================================================
# A forward DCF asks "given these assumptions, what is the business worth?". A reverse DCF asks
# the opposite: "given the PRICE, what is the market assuming?". This is the only part of the
# program that needs market.price. It reads scenario values; it never changes one.
#
# Two kinds of inversion live here:
#   closed form   the Gordon formula turned round (F1), a division by a multiple (F3) and a
#                 two-point interpolation (F5): one line of arithmetic each
#   numerical     "what growth rate, or what margin, makes this scenario worth exactly the price?"
#                 (F2). No formula gives that, so solve_root() searches: it re-runs the forward
#                 model with an override, again and again, until the value matches the price.

def solve_root(fn, target, lo, hi, step):
    """Lowest x in [lo, hi] with fn(x) = target (grid scan, then bisection).

    fn       a function of one number, e.g. "value per share if growth were x"
    target   the value to hit: the market price

    Two stages. First a coarse scan: evaluate fn every `step` across the range. Where two
    neighbouring points fall on opposite sides of the target, the answer lies between them.
    Then bisection inside that interval: halve it 80 times, keeping whichever half still
    straddles the target.

    Why scan first instead of bisecting the whole range? Because value is not always a rising
    function of the input. Growth that costs more capital than it earns makes value FALL as
    growth rises, and sometimes there is no solution at all. The scan finds the lowest crossing
    when one exists; when none does it says so and reports how close the model can get. That is
    a finding ("no growth rate justifies this price"), not an error.

    Returns {"solved": True, "x": ...}, or {"solved": False, "reason": ..., and the best value}.
    """
    n = int(round((hi - lo) / step))
    xs = [lo + i * step for i in range(n + 1)]
    vals = []
    for x in xs:
        try:
            vals.append(fn(x))
        except (ZeroDivisionError, OverflowError, ValueError):
            vals.append(float("nan"))       # the model cannot be evaluated here; skip this point
    for i in range(len(xs) - 1):
        a, b = vals[i], vals[i + 1]
        if math.isnan(a) or math.isnan(b):
            continue
        if a == target:
            return {"solved": True, "x": xs[i]}
        # (a - target) and (b - target) have opposite signs: the target lies between these two points.
        if (a - target) * (b - target) < 0:
            x0, x1, f0 = xs[i], xs[i + 1], a - target
            for _ in range(80):
                xm = (x0 + x1) / 2.0
                fm = fn(xm) - target
                if f0 * fm <= 0:
                    x1 = xm
                else:
                    x0, f0 = xm, fm
            return {"solved": True, "x": (x0 + x1) / 2.0}
    # No crossing anywhere in the range. Say which side the price is on, and the nearest the model got.
    finite = [(v, x) for v, x in zip(vals, xs) if not math.isnan(v)]
    if not finite:
        return {"solved": False, "reason": "the model could not be evaluated over the search range"}
    best_v, best_x = max(finite)
    low_v, low_x = min(finite)
    if best_v < target:
        return {"solved": False, "reason": "price is above every value the model can reach",
                "max_value": best_v, "x_at_max": best_x}
    return {"solved": False, "reason": "price is below every value the model can reach",
            "min_value": low_v, "x_at_min": low_x}


def market_frame(inp, price):
    """What the market price implies for operating value, on the model's own basis.

    The forward model runs   operating value -> + net cash -> equity -> / shares -> per share.
    This runs the same road backwards, starting from the price:
        market cap        = price x diluted shares   (options and convertibles settled AT THE PRICE)
        operating value   = market cap - net cash    (firm basis)
    so that a market number can be set beside a model number of the same kind. On an equity
    basis there is no bridge, and the market's "operating value" is simply the market cap.
    """
    basis, bridge, shares = inp["model"]["basis"], inp["bridge"], inp["shares"]
    n, conv = diluted_at(price, shares, basis)
    mcap = price * n
    if basis == "firm":
        net = bridge["net"] + conv          # converted notes stop being debt
        return {"diluted_shares": n, "market_cap": mcap, "net_cash": net, "net_cash_per_share": net / n,
                "operating_value": mcap - net, "operating_value_per_share": price - net / n}
    return {"diluted_shares": n, "market_cap": mcap, "net_cash": 0.0, "net_cash_per_share": 0.0,
            "operating_value": mcap, "operating_value_per_share": price}


def reverse_scenario(sc, inp, rates, price, frame):
    """What must be true of this scenario's free variables for its value to equal the price.

    For each rate, up to four separate answers. Each one changes a single thing and leaves the
    rest of the scenario exactly as written:
        growth       the one constant growth rate - over the explicit years that are not pinned
                     to a level - at which the scenario is worth the price, with the revenue (or
                     EPS) that implies at the horizon, ready to be compared with the market's size
        margin       how many points every year's margin would have to move (modes with a margin)
        flow_scale   the multiple of every cash flow that would be needed (mode direct)
        terminal     with the forecast years' cash flows held fixed, the terminal cash flow - or
                     exit multiple - that would make up the difference. Closed form; no search.
    """
    mode = inp["model"]["mode"]
    out = {"scenario": sc["name"], "by_rate": {}}
    base_proj = project(sc, inp)
    # "Free" years are the explicit years written as growth rates. Years written as levels
    # (consensus, guidance) are evidence, not assumptions, so the solver leaves them alone.
    free_years = len(sc["level"]["growth"]) if mode != "direct" else 0
    out["free_growth_years"] = free_years
    if free_years:
        k = len(sc["level"]["fixed"])
        out["growth_window"] = (k + 1, sc["n_exp"])     # first and last free year, counting from 1
    for r in rates:
        row = {}
        if free_years:
            # Value per share as a function of growth alone, at this rate. `r=r` freezes the
            # current rate inside the function: without it Python would look `r` up only when the
            # function is called, by which time the loop may have moved on to the next rate.
            def at_growth(c, r=r):
                return scenario_value(sc, r, inp, {"constant_growth": c})["value_per_share_raw"]

            # Search from -50% to +200% a year, in steps of one point.
            res = solve_root(at_growth, price, -0.50, 2.00, 0.01)
            if res["solved"]:
                p2 = project(sc, inp, {"constant_growth": res["x"]})
                key = "eps" if mode == "eps" else "revenue"
                res["level_n"] = p2["rows"][-1][key]
                res["base_level_n"] = base_proj["rows"][-1][key]
                res["fcf_n"] = p2["flows"][-1]
                # Capital-hungry growth can lower value; then the "implied growth" is not a bar to clear.
                res["value_rises_with_growth"] = at_growth(res["x"] + 0.005) > at_growth(res["x"] - 0.005)
            row["growth"] = res
        if mode in ("drivers", "fcf_margin"):
            # The same question for margins: shift every year's margin by s points, from -60 to +60.
            res = solve_root(lambda s: scenario_value(sc, r, inp, {"margin_shift": s})["value_per_share_raw"],
                             price, -0.60, 0.60, 0.005)
            if res["solved"]:
                res["terminal_margin"] = base_proj["diag"]["terminal_profit_metric"] + res["x"]
                res["base_terminal_margin"] = base_proj["diag"]["terminal_profit_metric"]
            row["margin"] = res
        if mode == "direct":
            row["flow_scale"] = solve_root(
                lambda s: scenario_value(sc, r, inp, {"flow_scale": s})["value_per_share_raw"], price, 0.0, 20.0, 0.02)
        # The terminal requirement, by arithmetic rather than search. Whatever the market's operating
        # value is, the forecast years account for pv_explicit of it; the terminal value has to
        # supply the rest. Compound that gap forward to the horizon, then undo whichever terminal
        # formula the scenario uses to see what cash flow (or multiple) it would take.
        v = value_at(base_proj, r, inp)
        target_op = frame["operating_value_per_share"] if base_proj["per_share"] else frame["operating_value"]
        tv_needed = (target_op - v["pv_explicit"]) * (1.0 + r) ** v["horizon"]
        if base_proj["method"] == "exit_multiple":
            metric = base_proj["exit_metric_value"]
            row["terminal"] = {"kind": "exit_multiple", "required": tv_needed / metric if metric > 0 else None,
                               "modelled": base_proj["exit_multiple"], "metric": base_proj["exit_metric"]}
        else:
            mid_adj = (1.0 + r) ** 0.5 if inp["model"]["timing"] == "mid_year" else 1.0
            row["terminal"] = {"kind": "terminal_fcf", "required": tv_needed * (r - base_proj["g"]) / mid_adj,
                               "modelled": base_proj["terminal_fcf"]}
        out["by_rate"][r] = row
    return out


def implied_block(inp, results, disc, price):
    """Module 4 framings F1 (Gordon inversion), F2 (growth/margin solve), F3 (mid-cycle), F5 (probabilities).

    (F4 - the table of every scenario's value at every rate - needs no price; analyze() builds it.)

    F1  If the business simply earned a steadily growing stream for ever, how large would that
        stream have to be TODAY to be worth the price?
            implied EPS = operating value per share x (r - g) / (conversion x (1 + g))
        Set against run-rate, consensus, peak and mid-cycle EPS, it shows how much permanence
        the price is paying for.
    F2  reverse_scenario(): the growth, margin or terminal value the price demands of the base case.
    F3  operating value per share / a through-cycle multiple = the mid-cycle EPS the price implies.
    F5  Suppose the stock ends at either the bear value or the bull value. What probability of
        the bull makes the expected value equal the price?   p = (price - bear) / (bull - bear)
        Above 100% the price is beyond the bull case; below 0% it is beneath the bear.
    """
    rates = disc["rates"]
    frame = market_frame(inp, price)
    im = inp["implied"]
    by_slot = {s["slot"]: s for s in results if s["slot"]}
    base = by_slot.get("base") or results[0]
    out = {"price": price, "frame": frame, "base_scenario": base["name"]}

    # ---- F1: the two assumptions of the inversion --------------------------------------------------
    # Growth: the implied block's own figure if given, otherwise the base case's terminal growth.
    # Conversion: the stated figure, otherwise read off the base case's terminal year (its
    # conversion in mode eps; free cash flow / NOPAT in mode drivers). In the other two modes
    # there is nothing to read it from, and F1 is skipped with a message.
    g1 = im["terminal_growth"] if im["terminal_growth"] is not None else base["sc"]["terminal"]["growth"]
    conv, conv_src = im["fcf_conversion"], "implied.fcf_conversion"
    if conv is None:
        proj = base["proj"]
        if proj["mode"] == "eps":
            conv, conv_src = proj["terminal_row"]["conversion"], "base scenario terminal conversion"
        elif proj["mode"] == "drivers" and proj["terminal_row"].get("nopat", 0) > 0 and proj["terminal_fcf"] > 0:
            conv = proj["terminal_fcf"] / proj["terminal_row"]["nopat"]
            conv_src = "base scenario terminal FCF / NOPAT"
    ovps = frame["operating_value_per_share"]
    mid = inp["model"]["timing"] == "mid_year"

    def perpetuity_base(value, r):
        """Current-year cash flow which, growing at g1 forever, is worth `value` - on the model's own timing.

        The Gordon formula turned round. Forward:  value = CF x (1 + g) / (r - g), times (1 + r)^0.5
        when cash arrives mid-year. Solved for CF, the cash flow of the year just ended. Using the
        forward model's own timing matters: a stream priced by value_at() must imply itself back."""
        return value * (r - g1) / ((1.0 + g1) * ((1.0 + r) ** 0.5 if mid else 1.0))

    f1 = {"terminal_growth": g1, "conversion": conv, "conversion_source": conv_src if conv is not None else None,
          "rows": [], "anchors": im["eps_anchors"], "mid_year": mid}
    if conv is not None and ovps > 0:
        for r in rates:
            if r - g1 < 0.005:
                continue
            f1["rows"].append({"rate": r, "implied_eps": perpetuity_base(ovps, r) / conv})
    out["f1"] = f1
    # The same inversion in total dollars instead of per share: the perpetual free cash flow the
    # market's operating value requires, to set beside the base case's own first and last years.
    out["f1_firm"] = None
    if inp["model"]["basis"] == "firm" and frame["operating_value"] > 0:
        proj = base["proj"]
        if not proj["per_share"]:
            out["f1_firm"] = {"terminal_growth": g1, "year1_fcf": proj["flows"][0], "year_n_fcf": proj["flows"][-1],
                              "rows": [{"rate": r, "implied_fcf": perpetuity_base(frame["operating_value"], r)}
                                       for r in rates if r - g1 >= 0.005]}
    # ---- F3: what mid-cycle EPS is the price paying for, at 10x / 12x / 14x / 16x? -------------------
    out["f3"] = {"rows": [{"multiple": m, "implied_eps": ovps / m} for m in im["mid_cycle_multiples"]] if ovps > 0 else [],
                 "anchors": im["eps_anchors"]}

    # ---- F2: the numerical solves, on the base case and on any scenario marked "reverse": true ------
    targets = [base] + [s for s in results if s["sc"]["reverse"] and s is not base]
    out["f2"] = [reverse_scenario(s["sc"], inp, rates, price, frame) for s in targets]

    # ---- F5: the market-implied probability of the bull case, at each rate --------------------------
    f5 = {"rows": [], "available": "bear" in by_slot and "bull" in by_slot}
    if f5["available"]:
        for r in rates:
            pb = by_slot["bear"]["values"][r]["value_per_share"]
            pu = by_slot["bull"]["values"][r]["value_per_share"]
            every = [s["values"][r]["value_per_share"] for s in results]
            row = {"rate": r, "pv_bear": pb, "pv_bull": pu, "p_bull": None, "state": "ok",
                   "above_every_scenario": price > max(every), "below_every_scenario": price < min(every)}
            if pu <= pb:
                row["state"] = "bull PV is not above bear PV"
            else:
                row["p_bull"] = (price - pb) / (pu - pb)
                if row["p_bull"] > 1:
                    row["state"] = "price above the bull PV"
                elif row["p_bull"] < 0:
                    row["state"] = "price below the bear PV"
            f5["rows"].append(row)
    out["f5"] = f5
    return out


# =============================================================================
# Orchestration
# =============================================================================
# analyze() is the conductor. It calls everything above in order and gathers the results into
# one dict - `res` - which the two renderers further down turn into the report and the JSON file.
# It holds little arithmetic of its own: the sensitivity table, the hand-off, the quality verdict.

def analyze(inp):
    """Run the whole valuation on validated inputs and return everything the report needs.

    1. Discount rate     r*, r_hi and the full list of rates
    2. Each scenario     project it once, value it at every rate, run the checks on it
    3. Sensitivity       the base case re-valued across rates x terminal growth
    4. Hand-off          bear / base / bull at r* and at r_hi, the weights, PWV and PWR
    5. Quality           is the base-case value robust, or only directional?
    6. Reverse DCF       only if a market price was supplied
    7. Flags that concern the model as a whole
    """
    flags = Flags()
    # ---- 1. discount rate ---------------------------------------------------------------------------
    disc = compute_discount(inp, flags)
    rates, r_star, r_hi = disc["rates"], disc["primary_rate"], disc["sensitivity_rate"]
    model, meta, price = inp["model"], inp["meta"], inp["market"]["price"]

    # ---- 2. every scenario: one projection, valued at each rate -------------------------------------
    results = []
    for sc in inp["scenarios"]:
        proj = project(sc, inp)
        values = {r: value_at(proj, r, inp) for r in rates}     # {rate: the valuation at that rate}
        adm = cyclical_check(sc, proj, model)
        scenario_flags(sc, proj, values[r_star], r_star, inp, flags, adm)
        results.append({"name": sc["name"], "slot": sc["slot"], "weight": sc["weight"], "label": sc["label"],
                        "narrative": sc["narrative"], "sc": sc, "proj": proj, "values": values, "admissibility": adm})
    # The scenario the sensitivity table, the anchor-rate line and the reverse DCF are run on: the
    # one in the base slot - or simply the first scenario, when no slots have been assigned.
    by_slot = {s["slot"]: s for s in results if s["slot"]}
    base = by_slot.get("base") or results[0]

    # ---- 3. sensitivity -----------------------------------------------------------------------------
    # Sensitivity of the base case: rate x terminal growth (or x exit multiple).
    # Rows are the rates. Columns are terminal growth 1 point lower, half a point lower, as
    # modelled and half a point higher (or the exit multiple at 0.8x to 1.2x). Every cell is a
    # complete re-run of the base case with that one assumption overridden. A cell is left empty
    # where g would come within a point of the rate and the perpetuity would blow up.
    bsc = base["sc"]
    if bsc["terminal"]["method"] == "exit_multiple":
        m0 = bsc["terminal"]["exit_multiple"]
        cols = [round(m0 * k, 4) for k in (0.8, 0.9, 1.0, 1.1, 1.2)]
        axis, key = "exit multiple", "exit_multiple"
    else:
        g0 = bsc["terminal"]["growth"]
        cols = [round(g0 + dgr, 6) for dgr in (-0.01, -0.005, 0.0, 0.005)]
        axis, key = "terminal growth", "terminal_growth"
    sens = {"axis": axis, "columns": cols, "rows": [], "scenario": base["name"],
            "cap": model["terminal_growth_cap"] if key == "terminal_growth" else None}
    for r in rates:
        row = []
        for c in cols:
            if key == "terminal_growth" and r - c < 0.01:
                row.append(None)
            else:
                row.append(scenario_value(bsc, r, inp, {key: c})["value_per_share"])
        sens["rows"].append({"rate": r, "values": row})

    # Value at the un-rounded anchor rate, for reference only.
    # (Shows how much of the answer comes from rounding 10.48% to 10%. Never used downstream.)
    anchor_value = None
    if disc["anchor"] - bsc["terminal"]["growth"] >= 0.01:
        anchor_value = scenario_value(bsc, disc["anchor"], inp)["value_per_share"]

    # ---- 4. hand-off ----------------------------------------------------------------------------------
    # Hand-off to the Entry & Exit Plan.
    # The plan is built from exactly these numbers and nothing else:
    #     at_primary       {"bear", "base", "bull"} values per share at r*
    #     at_sensitivity   the same three at r_hi (the plan sizes positions on the bear value here)
    #     weights          the analyst's probabilities for the three
    #     pwv_primary      probability-weighted value = sum of weight x value, at r*
    #     pwr              PWV / price - 1: the expected return at today's price (needs a price)
    # It is "complete" only when all three slots are filled.
    handoff = {"complete": all(s in by_slot for s in SLOTS), "primary_rate": r_star, "sensitivity_rate": r_hi}
    if handoff["complete"]:
        for tag, r in (("at_primary", r_star), ("at_sensitivity", r_hi)):
            handoff[tag] = {s: by_slot[s]["values"][r]["value_per_share"] for s in SLOTS}
        handoff["names"] = {s: by_slot[s]["name"] for s in SLOTS}
        handoff["admissibility"] = {s: by_slot[s]["admissibility"]["status"] for s in SLOTS}
        # The three must come out bear < base < bull. If not, a scenario is sitting in the wrong
        # slot, or the "bear" is not actually worse than the "base".
        p = handoff["at_primary"]
        handoff["ordered"] = p["bear"] < p["base"] < p["bull"]
        if not handoff["ordered"]:
            flags.add("WARN", "W-SLOT-ORDER", None,
                      f"At r* the slots are not ordered bear < base < bull (${p['bear']:,.2f} / ${p['base']:,.2f} / "
                      f"${p['bull']:,.2f}). The scenario slots are mis-assigned or the scenarios do not span the debate.")
        weights = {s: by_slot[s]["weight"] for s in SLOTS}
        if all(w is not None for w in weights.values()):
            handoff["weights"] = weights
            handoff["pwv_primary"] = sum(weights[s] * handoff["at_primary"][s] for s in SLOTS)
            handoff["pwv_sensitivity"] = sum(weights[s] * handoff["at_sensitivity"][s] for s in SLOTS)
            if price is not None:
                handoff["pwr"] = handoff["pwv_primary"] / price - 1.0
        else:
            handoff["weights"] = None
            flags.add("WARN", "W-NO-WEIGHTS", None,
                      "Bear/base/bull weights are missing, so the probability-weighted value (PWV, the plan's exit "
                      "floor) was not computed. Add 'weight' to each slotted scenario.")
        if model["cyclical"] and handoff["admissibility"]["bull"] == "inadmissible":
            flags.add("WARN", "W-BULL-SLOT-INADMISSIBLE", None,
                      "The bull slot holds an inadmissible (non-mean-reverting) scenario. Move it to context and "
                      "put the highest-value admissible scenario in the bull slot.")
    else:
        missing = [s for s in SLOTS if s not in by_slot]
        flags.add("WARN", "W-NO-SLOTS", None,
                  f"No scenario is assigned to the {', '.join(missing)} slot(s), so the Entry & Exit hand-off is "
                  "incomplete. A full report needs bear, base and bull.")

    # ---- 5. quality -----------------------------------------------------------------------------------
    # DCF quality: robust or directional.
    # "Directional" means: trust the sign and the rough size, not the second digit. Any one of these
    # is enough - the value is mostly terminal; r* sits too close to g; one step in the rate moves
    # the value by more than 30%; the forecast years add nothing; or the terminal year contradicts
    # itself. With no reason found, the base-case value is called robust.
    reasons = []
    v_base = base["values"][r_star]
    if v_base["tv_share"] is not None and v_base["tv_share"] > TV_SHARE_DIRECTIONAL:
        reasons.append(f"terminal value is {v_base['tv_share']:.0%} of operating value")
    if bsc["terminal"]["method"] != "exit_multiple" and r_star - bsc["terminal"]["growth"] < THIN_SPREAD:
        reasons.append(f"r* minus terminal growth is only {r_star - bsc['terminal']['growth']:.1%}")
    v_hi = base["values"][r_hi]["value_per_share"]
    if v_base["value_per_share"] > 0:
        swing = abs(v_hi / v_base["value_per_share"] - 1.0)
        if swing > RATE_SWING_DIRECTIONAL:
            reasons.append(f"moving the rate from {r_star:.0%} to {r_hi:.0%} changes value by {swing:.0%}")
    if v_base["pv_explicit"] <= 0:
        reasons.append("the explicit period contributes no value - everything rests on the terminal")
    if any(f["code"] in ("W-GROWTH-CLIFF", "W-NO-REINVESTMENT", "W-RONIC-HIGH", "W-TERMINAL-STEP-UP")
           and f["scenario"] == base["name"] for f in flags.items):
        reasons.append("the terminal year is not internally consistent (see flags)")
    quality = {"label": "directional" if reasons else "robust", "reasons": reasons}

    # ---- 6. reverse DCF, and 7. model-wide flags ------------------------------------------------------
    implied = None
    if price is not None:
        implied = implied_block(inp, results, disc, price)
        # A value 20 times the price, or a twentieth of it, is not a view on the stock. It is revenue
        # in millions against shares in billions, or a price typed as a market cap.
        ratio = v_base["value_per_share"] / price if price else None
        if ratio is not None and (ratio > 20 or (0 < ratio < 0.05)):
            flags.add("WARN", "W-UNITS", None,
                      f"Base value is {ratio:.2f}x the price. Check that revenue, debt and share count are in the "
                      f"same units ({meta['units']}) and that the price is per share.")
        if (model["mode"] == "eps" and model["basis"] == "firm"
                and abs(implied["frame"]["net_cash_per_share"]) > 0.10 * price):
            flags.add("WARN", "W-EPS-BASIS", None,
                      "Mode 'eps' on a firm basis adds net cash (or deducts net debt) per share, which is only "
                      "right if the EPS path is before interest. Net cash/debt is more than 10% of the price here: "
                      "strip after-tax interest from the EPS path, switch basis to 'equity', or use mode 'drivers'.")
    else:
        flags.add("NOTE", "N-NO-PRICE", None,
                  "No market.price supplied: forward values only. The reverse-DCF block, '% vs price' and PWR need it.")
    if inp["history"] is None:
        flags.add("NOTE", "N-NO-HISTORY", None,
                  "No 'history' block: the assumptions were not benchmarked against the company's own record.")
    if not inp["sources"]:
        flags.add("WARN", "W-NO-SOURCES", None,
                  "No 'sources' recorded. Every input needs a source and date before it reaches the memo.")
    bs_date = meta["balance_sheet_date"]
    if bs_date and (meta["valuation_date"] - bs_date).days > STALE_BALANCE_SHEET_DAYS:
        flags.add("WARN", "W-STALE-BALANCE-SHEET", None,
                  f"The balance sheet ({bs_date}) is {(meta['valuation_date'] - bs_date).days} days older than the "
                  "valuation date. Use the latest filing, or adjust the bridge for raises, buybacks and deals since.")
    if model["basis"] == "equity" and (inp["bridge"]["cash_and_investments"] or inp["bridge"]["debt"]):
        flags.add("NOTE", "N-BRIDGE-IGNORED", None,
                  "Equity basis: cash and debt in 'bridge' are not applied, because after-interest cash flows "
                  "already reflect them.")
    if model["basis"] == "equity" and inp["shares"]["convertibles"]:
        flags.add("NOTE", "N-CONVERTS-IGNORED", None,
                  "Equity basis: convertibles are not converted by the engine; reflect them in the share count.")
    # `res`: everything the renderers need. "results" is the list of scenarios, each with its
    # projection ("proj") and its valuations by rate ("values"); "labels" names each scenario's years.
    return {"inp": inp, "discount": disc, "results": results, "base": base, "sensitivity": sens,
            "anchor_value": anchor_value, "handoff": handoff, "quality": quality, "implied": implied,
            "flags": flags.sorted(), "labels": {s["name"]: year_labels(meta, s["proj"]["n"]) for s in results}}


# =============================================================================
# Rendering - Markdown
# =============================================================================
# STEP 3. From here to the end of the file nothing is calculated: every number below was produced
# by analyze() and is only being laid out. If a figure in the report looks wrong, the cause is
# above this line; if it looks right but reads badly, it is below.
#
# First come the small formatters that turn a number into text, then the two functions that
# assemble the report: cashflow_table() for one scenario's year-by-year table, and
# render_markdown() for the whole document.

def pct(x, d=1):
    """0.1234 -> "12.3%" (d = decimals). A missing or undefined value prints as "n/a"."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "n/a"
    return f"{x * 100:.{d}f}%"


def rate_label(r):
    """A discount rate as a label: 0.10 -> "10%", 0.105 -> "10.5%" (no ".0" on round rates)."""
    return f"{r * 100:.1f}%".replace(".0%", "%")


def usd(x, d=2):
    """A per-share amount: 85.288 -> "$85.29", -3.5 -> "-$3.50"."""
    if x is None:
        return "n/a"
    return f"-${abs(x):,.{d}f}" if x < 0 else f"${x:,.{d}f}"


def tot(x, units):
    """A monetary total, input in `units`, shown with a magnitude suffix.

    The inputs file states totals in one scale (say millions). For reading, each figure is
    converted to plain dollars and then shown at whatever size suits it: 43190 (millions) ->
    "$43.19B", 500 -> "$500.0M". The suffix always tells you the scale, so nothing depends on
    remembering which units the file was written in.
    """
    if x is None:
        return "n/a"
    v = x * UNITS[units]
    a = abs(v)
    if a >= 1e12:
        s = f"{a / 1e12:,.2f}T"
    elif a >= 1e9:
        s = f"{a / 1e9:,.2f}B"
    elif a >= 1e6:
        s = f"{a / 1e6:,.1f}M"
    else:
        s = f"{a:,.0f}"
    return ("-$" if v < 0 else "$") + s


def count_fmt(x, units):
    """A share count, converted from the file's units: 506.37 (millions) -> "506.37M"."""
    v = x * UNITS[units]
    return f"{v / 1e9:,.3f}B" if v >= 1e9 else f"{v / 1e6:,.2f}M"


def vs_price(v, price):
    """How far a value sits from the market price: value 85, price 100 -> "-15%"."""
    return "n/a" if price is None else f"{(v / price - 1.0) * 100:+.0f}%"


def table(headers, rows, align=None):
    """Lay out a Markdown table. `align` gives "l" or "r" per column; by default the first column
    (the labels) is left-aligned and every other column (the numbers) right-aligned."""
    align = align or ["l"] + ["r"] * (len(headers) - 1)
    sep = ["---" if a == "l" else "---:" for a in align]
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(sep) + "|"]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


def cashflow_table(res, s, r):
    """One scenario's build, year by year, with each year's present value at rate r in the last
    column - the table to check the model against by hand. The final row is the terminal year
    (or the exit multiple), and its PV is the present value of the whole terminal value.

    s   one entry of res["results"]: the scenario with its projection and valuations
    """
    inp = res["inp"]
    u, proj, mode = inp["meta"]["units"], s["proj"], inp["model"]["mode"]
    labels = res["labels"][s["name"]]
    v = s["values"][r]
    stub = inp["meta"]["stub"]
    # Money is per share in mode "eps" and a total (with a B / M suffix) in every other mode.
    money = (lambda x: usd(x)) if proj["per_share"] else (lambda x: tot(x, u))
    # The columns to show for each mode, as (heading, key of the figure in a row, how to format it).
    cols = {
        "drivers": [("Revenue", "revenue", money), ("Growth", "growth", pct), ("EBIT margin", "ebit_margin", pct),
                    ("EBIT", "ebit", money), ("Cash tax", "tax", money), ("D&A", "da", money),
                    ("Capex", "capex", money), ("Change in NWC", "d_nwc", money), ("FCF", "fcf", money),
                    ("FCF margin", "fcf_margin", pct)],
        "fcf_margin": [("Revenue", "revenue", money), ("Growth", "growth", pct), ("FCF margin", "fcf_margin", pct),
                       ("FCF", "fcf", money)],
        "eps": [("EPS", "eps", money), ("Growth", "growth", pct), ("Conversion", "conversion", pct),
                ("Owner earnings/share", "fcf", money)],
        "direct": [("Revenue", "revenue", money), ("FCF", "fcf", money)],
    }[mode]
    if mode == "direct" and not s["sc"].get("display_revenue"):
        cols = cols[1:]
    headers = ["Year"] + [c[0] for c in cols] + [f"PV at {rate_label(r)}"]
    rows = []
    for i, row in enumerate(proj["rows"]):
        label = labels[i] + (f" (stub {stub:.2f})" if i == 0 and stub < 1 else "")
        rows.append([label] + [fn(row.get(k)) if row.get(k) is not None else "n/a" for _, k, fn in cols] + [money(v["pvs"][i])])
    if proj["method"] == "exit_multiple":
        rows.append([f"Terminal ({proj['exit_multiple']:g}x {proj['exit_metric']})"] + [""] * len(cols) + [money(v["pv_terminal"])])
    else:
        tr = proj["terminal_row"]
        rows.append([f"Terminal year ({labels[proj['n']]})"]
                    + [fn(tr.get(k)) if tr.get(k) is not None else "n/a" for _, k, fn in cols] + [money(v["pv_terminal"])])
    return table(headers, rows)


def render_markdown(res):
    """Turn the results of analyze() into the report, as one Markdown string.

    The report's sections, in the order the code below writes them:
        (title)                  what was valued, when, and under which conventions
        DCF value                the headline: base case at r*, the bear-to-bull range, PWV, quality
        1. Discount rate         CAPM -> WACC -> anchor -> r* and r_hi, with the arithmetic shown
        2. Equity bridge and share count
        3. Scenario values       every scenario at every rate (framing F4), then its diagnostics
        4. Cash-flow build       the year-by-year table for each scenario, and the history supplied
        5. Sensitivity           the base case across rates x terminal growth
        6. Implied expectations  the reverse DCF: F1, F2, F3, F5 (only when a price was given)
        7. Hand-off              the numbers the Entry & Exit Plan is built from
        8. Model flags           every WARN and NOTE
        9. Input sources

    How it is written: `L` is the list of lines, `add` is shorthand for "append a line to L", and
    the very last statement joins the lines. Much of the length below is `if` branches choosing
    which sentence fits the case (firm or equity basis, price or no price, solved or not).
    """
    inp, disc = res["inp"], res["discount"]
    meta, model, shares, bridge = inp["meta"], inp["model"], inp["shares"], inp["bridge"]
    u, price = meta["units"], inp["market"]["price"]
    r_star, r_hi, rates = disc["primary_rate"], disc["sensitivity_rate"], disc["rates"]
    base, results, ho = res["base"], res["results"], res["handoff"]
    firm = model["basis"] == "firm"
    per_share_mode = model["mode"] == "eps"
    money = (lambda x: usd(x)) if per_share_mode else (lambda x: tot(x, u))
    L = []
    add = L.append

    # ---- title block: what, when, and under which conventions --------------------------------------
    # The inputs' sha256 fingerprint ties this report to the exact file that produced it.
    title = f"# DCF - {meta['ticker']}" + (f" ({meta['company']})" if meta["company"] else "")
    add(title)
    add("")
    add(f"- Valuation date: {meta['valuation_date']} · program dcf.py v{VERSION} · inputs sha256 `{res.get('inputs_sha', 'n/a')}`")
    basis_txt = ("firm basis (cash flows before interest, discounted at a WACC-anchored rate, then bridged to equity)"
                 if firm else "equity basis (cash flows after interest, discounted at a cost-of-equity-anchored rate, no bridge)")
    add(f"- Method: mode `{model['mode']}` · {basis_txt} · "
        f"{'mid-year' if model['timing'] == 'mid_year' else 'end-of-year'} discounting · totals in "
        f"{meta['currency']} {u}, per-share figures in {meta['currency']}")
    if meta["stub"] < 1:
        add(f"- Fiscal mapping: year 1 = {res['labels'][base['name']][0]}, ending {meta['first_forecast_year_end']}; "
            f"{meta['stub']:.2f} of that year remains at the valuation date, so only that share of its cash flow is counted")
    else:
        add("- Fiscal mapping: year 1 = the twelve months following the valuation date (no stub)")
    if meta["fiscal_note"]:
        add(f"- Fiscal note: {meta['fiscal_note']}")
    add("")

    # ---- headline: the few lines someone reads if they read nothing else ----------------------------
    add("## DCF value")
    add("")
    vb = base["values"][r_star]
    line = f"- **Base case at r\\* = {rate_label(r_star)}: {usd(vb['value_per_share'])} per share** [{base['name']}]"
    if price is not None:
        line += f" · {vs_price(vb['value_per_share'], price)} vs price {usd(price)}"
    add(line)
    if ho["complete"]:
        p = ho["at_primary"]
        add(f"- Range at r\\*: bear {usd(p['bear'])} [{ho['names']['bear']}] / base {usd(p['base'])} / "
            f"bull {usd(p['bull'])} [{ho['names']['bull']}]")
        if ho.get("weights"):
            w = ho["weights"]
            pw = f"- Probability-weighted value (weights {w['bear']:.0%}/{w['base']:.0%}/{w['bull']:.0%}): {usd(ho['pwv_primary'])}"
            if "pwr" in ho:
                pw += f" · PWR {ho['pwr'] * 100:+.1f}%"
            add(pw)
    q = res["quality"]
    add(f"- Quality: **{q['label']}**" + (" - " + "; ".join(q["reasons"]) if q["reasons"] else
                                         " - no structural warning on the base case"))
    nwarn = sum(1 for f in res["flags"] if f["level"] == "WARN")
    add(f"- Model flags: {nwarn} warning(s), {len(res['flags']) - nwarn} note(s) - see the last section; "
        "every warning is fixed in the inputs or disclosed in the memo")
    add("")

    # ---- 1. discount rate: every step of compute_discount(), with its arithmetic written out ---------
    add("## 1. Discount rate")
    add("")
    ke_line = (f"- Cost of equity (CAPM) = {pct(disc['risk_free'], 2)} + {disc['beta']:.2f} x "
               f"{pct(disc['equity_risk_premium'], 2)}")
    if disc["additional_premium"]:
        ke_line += f" + {pct(disc['additional_premium'], 2)}"
    add(ke_line + f" = **{pct(disc['cost_of_equity'], 2)}**")
    if firm:
        wd = disc["debt_weight"]
        if wd > 0:
            add(f"- After-tax cost of debt = {pct(disc['pre_tax_cost_of_debt'], 2)} x (1 - {pct(disc['tax_rate'], 0)}) = "
                f"{pct(disc['pre_tax_cost_of_debt'] * (1 - disc['tax_rate']), 2)}")
        add(f"- Weights: equity {pct(1 - wd)} / debt {pct(wd)} - {disc['weight_source']}"
            + (f" (market cap {tot(disc['market_cap'], u)}, debt {tot(disc['debt_for_weights'], u)})"
               if disc["market_cap"] is not None and "market" in disc["weight_source"] else ""))
        add(f"- WACC = **{pct(disc['wacc'], 2)}**")
    add(f"- Anchor: {disc['anchor_name']} {pct(disc['anchor'], 2)} -> primary rate **r\\* = {rate_label(r_star)}**"
        + (" (analyst override)" if disc["override"] else " (nearest grid rate; ties go up)")
        + f" · sensitivity rate **r_hi = {rate_label(r_hi)}** · grid {' / '.join(rate_label(x) for x in disc['grid'])}")
    if res["anchor_value"] is not None and abs(disc["anchor"] - r_star) > 1e-9:
        add(f"- Reference only: the base case at the un-rounded anchor rate is {usd(res['anchor_value'])}. "
            "The memo and the Entry & Exit Plan use r\\*.")
    add("")

    # ---- 2. bridge and shares: how operating value becomes value per share ---------------------------
    # (Bridge lines that are zero are left out of the table; the total is always shown.)
    add("## 2. Equity bridge and share count")
    add("")
    if firm:
        rows = [["Cash and investments", tot(bridge["cash_and_investments"], u)],
                ["Non-operating assets", tot(bridge["non_operating_assets"], u)],
                ["Debt (incl. finance leases and convertible principal)", tot(-bridge["debt"], u)],
                ["Preferred equity", tot(-bridge["preferred_equity"], u)],
                ["Minority interest", tot(-bridge["minority_interest"], u)],
                ["Other claims", tot(-bridge["other_claims"], u)],
                ["**Net bridge (added to operating value)**", f"**{tot(bridge['net'], u)}**"]]
        add(table(["Bridge item", "Amount"], [r for r in rows if r[1] not in ("$0", "-$0") or r[0].startswith("**")]))
    else:
        add("Equity basis: no bridge is applied.")
    add("")
    add(f"- Share count before options and convertibles: {count_fmt(shares['count'], u)}"
        + (f" ({shares['note']})" if shares["note"] else ""))
    for o in shares["options"]:
        add(f"- Options: {count_fmt(o['count'], u)} at {usd(o['strike'])} strike - treasury-stock method at the model's value")
    for c in shares["convertibles"]:
        add(f"- {c['name']}: {tot(c['principal'], u)} principal, converts at {usd(c['conversion_price'])} into "
            f"{count_fmt(c['shares'], u)} shares - if-converted when the model's value is above the conversion price")
    if not per_share_mode:
        add(f"- Base case at r\\*: equity value {tot(vb['equity_value'], u)} over {count_fmt(vb['diluted_shares'], u)} "
            f"diluted shares" + (f" (convertible principal treated as equity: {tot(vb['converted_principal'], u)})"
                                 if vb["converted_principal"] else ""))
    add("")

    # ---- 3. scenario values: one row per scenario, one column per rate; then a diagnostics table ------
    # The first table's columns depend on the run: "vs price" appears only when a price was given,
    # "Mean-reverts?" only for a cyclical. The second table explains each value: how much of it is
    # terminal, what the terminal value amounts to as a multiple, what return on new capital it implies.
    add("## 3. Scenario values (Module 4 framing F4)")
    add("")
    headers = ["Scenario", "Slot", "Authorship"] + [f"Value at {rate_label(r)}" + (" (r\\*)" if r == r_star else "") for r in rates]
    if price is not None:
        headers.append(f"vs {usd(price)} at r\\*")
    headers += ["TV share at r\\*"]
    if model["cyclical"]:
        headers.append("Mean-reverts?")
    rows = []
    for s in results:
        row = [s["name"], s["slot"] or "context", s["label"] or "unlabelled"]
        row += [usd(s["values"][r]["value_per_share"]) for r in rates]
        if price is not None:
            row.append(vs_price(s["values"][r_star]["value_per_share"], price))
        row.append(pct(s["values"][r_star]["tv_share"], 0))
        if model["cyclical"]:
            row.append(s["admissibility"]["status"])
        rows.append(row)
    add(table(headers, rows, ["l", "l", "l"] + ["r"] * (len(headers) - 3)))
    add("")
    for s in results:
        if s["narrative"]:
            add(f"- **{s['name']}**: {s['narrative']}")
    add("")
    add("Scenario diagnostics at r\\*:")
    add("")
    dh = ["Scenario", "Operating value", "PV explicit", "PV terminal", "Terminal method", "Terminal growth",
          "Horizon " + ("EPS" if per_share_mode else "revenue"), "Horizon FCF", "Implied terminal multiple",
          "Return on new capital", "Peak cash burn"]
    drows = []
    for s in results:
        v, proj = s["values"][r_star], s["proj"]
        if proj["method"] == "exit_multiple":
            tg = f"implied {pct(v['implied_perpetual_growth'])}"
            mult = f"{proj['exit_multiple']:g}x {proj['exit_metric']} (input)"
        else:
            tg = pct(proj["g"], 2)
            pref = "ebitda" if "ebitda" in v["implied_multiples"] else ("eps" if "eps" in v["implied_multiples"] else "fcf")
            mult = f"{v['implied_multiples'][pref]:.1f}x {pref}" if pref in v["implied_multiples"] else "n/a"
        d = proj["diag"]
        if model["mode"] != "drivers":
            ronic = "n/a"
        elif d.get("ronic_is_input"):
            ronic = f"{pct(d['implied_ronic'], 0)} (input)"
        elif d.get("implied_ronic") is not None:
            ronic = f"{pct(d['implied_ronic'], 0)} implied"
        else:
            ronic = "no net reinvestment" if (d.get("reinvestment_rate") is not None and d["reinvestment_rate"] <= 0) else "n/a"
        horizon_level = proj["rows"][-1].get("eps" if per_share_mode else "revenue")
        drows.append([s["name"], money(v["operating_value"]), money(v["pv_explicit"]), money(v["pv_terminal"]),
                      proj["method"], tg, money(horizon_level) if horizon_level is not None else "n/a",
                      money(proj["flows"][-1]), mult, ronic,
                      money(v["funding_trough"]) if v["funding_trough"] > 0 else "none"])
    add(table(dh, drows, ["l"] + ["r"] * 3 + ["l", "r", "r", "r", "r", "r", "r"]))
    add("")

    # ---- 4. cash-flow build: the base case first, then the others; then the history, if supplied ------
    add("## 4. Cash-flow build")
    add("")
    ordered = [base] + [s for s in results if s is not base]
    for s in ordered:
        add(f"### {s['name']}" + (f" ({s['slot']})" if s["slot"] else " (context)"))
        add("")
        add(cashflow_table(res, s, r_star))
        add("")
    if inp["history"]:
        add("### History supplied (benchmark for the assumptions above)")
        add("")
        h = inp["history"]
        hrows = []
        rev = h.get("revenue")
        if rev:
            hrows.append(["Revenue"] + [tot(x, u) if x is not None else "n/a" for x in rev])
            hrows.append(["Revenue growth", "n/a"] + [pct(rev[i] / rev[i - 1] - 1) if rev[i] and rev[i - 1] else "n/a"
                                                     for i in range(1, len(rev))])
            for key, name in (("ebit", "EBIT margin"), ("da", "D&A / revenue"), ("capex", "Capex / revenue"),
                              ("sbc", "SBC / revenue"), ("fcf", "FCF margin")):
                if h.get(key):
                    hrows.append([name] + [pct(n / r) if n is not None and r else "n/a" for n, r in zip(h[key], rev)])
            if h.get("change_in_nwc"):
                hrows.append(["Change in NWC / change in revenue", "n/a"]
                             + [pct(h["change_in_nwc"][i] / (rev[i] - rev[i - 1]))
                                if h["change_in_nwc"][i] is not None and rev[i] and rev[i - 1] and rev[i] != rev[i - 1]
                                else "n/a" for i in range(1, len(rev))])
        if h.get("roic"):
            hrows.append(["ROIC"] + [pct(x) if x is not None else "n/a" for x in h["roic"]])
        if h.get("eps"):
            hrows.append(["EPS"] + [usd(x) if x is not None else "n/a" for x in h["eps"]])
        add(table(["Metric"] + h["periods"], hrows))
        add("")

    # ---- 5. sensitivity: the grid built in analyze(); a dagger marks growth columns above the cap -----
    sens = res["sensitivity"]
    add(f"## 5. Sensitivity - {sens['scenario']}, value per share")
    add("")
    if sens["axis"] == "terminal growth":
        heads = ["Discount rate"] + [pct(c, 2) + (" †" if c > sens["cap"] + 1e-9 else "") for c in sens["columns"]]
    else:
        heads = ["Discount rate"] + [f"{c:g}x" for c in sens["columns"]]
    add(table(heads, [[rate_label(row["rate"]) + (" (r\\*)" if row["rate"] == r_star else "")]
                      + [usd(x) if x is not None else "n/a" for x in row["values"]] for row in sens["rows"]]))
    add("")
    add(f"Columns: {sens['axis']}." + (" † above the terminal-growth cap - shown for sensitivity only, never as a case."
                                       if sens["axis"] == "terminal growth" and any(c > sens["cap"] + 1e-9 for c in sens["columns"]) else ""))
    add("")

    # ---- 6. implied expectations: the results of implied_block(), one framing after another -----------
    # The longest stretch of this function, because each framing has to cope with the cases where
    # it could not be computed (no price, no conversion factor, no bear/bull slots, no solution).
    add("## 6. Implied expectations (reverse DCF)")
    add("")
    im = res["implied"]
    if im is None:
        add("Not run: no `market.price` in the inputs.")
        add("")
    else:
        fr = im["frame"]
        add(f"Price {usd(price)} x {count_fmt(fr['diluted_shares'], u)} diluted shares = market cap {tot(fr['market_cap'], u)}; "
            + (f"net cash {tot(fr['net_cash'], u)} ({usd(fr['net_cash_per_share'])} per share) -> "
               f"operating value {tot(fr['operating_value'], u)} ({usd(fr['operating_value_per_share'])} per share)."
               if firm else "equity basis, so operating value per share = price."))
        add("")
        f1 = im["f1"]
        add("**F1 - implied perpetual owner earnings (Gordon inversion).** "
            "Implied sustainable EPS = operating value per share x (r - g) / (conversion x (1 + g)"
            + (" x (1 + r)^0.5); the last factor matches the model's mid-year discounting." if f1["mid_year"] else ")."))
        add("")
        if f1["rows"]:
            anchors = f1["anchors"]
            names = {"run_rate": "vs run-rate", "forward_consensus": "vs forward consensus",
                     "all_time_peak": "vs all-time peak", "mid_cycle": "vs mid-cycle"}
            hd = ["Discount rate", "Implied sustainable EPS"] + [f"{names[k]} {usd(anchors[k])}" for k in EPS_ANCHOR_KEYS if k in anchors]
            add(table(hd, [[rate_label(x["rate"]), usd(x["implied_eps"])]
                           + [f"{x['implied_eps'] / anchors[k]:.2f}x" if anchors[k] > 0 else "n/a"
                              for k in EPS_ANCHOR_KEYS if k in anchors] for x in f1["rows"]]))
            add("")
            add(f"g = {pct(f1['terminal_growth'], 2)}, conversion = {pct(f1['conversion'], 0)} ({f1['conversion_source']})."
                + ("" if anchors else " No EPS anchors supplied (`implied.eps_anchors`), so the comparison columns are missing.")
                + (" On a firm basis the implied figure is EPS before interest." if firm else ""))
        else:
            add("Not computed: needs `implied.fcf_conversion` (or a base scenario the conversion can be read from) and a "
                "positive operating value.")
        add("")
        if im["f1_firm"]:
            f = im["f1_firm"]
            add("Same inversion on total cash flow: perpetual unlevered FCF the operating value requires, against the "
                f"base case's year-1 FCF of {tot(f['year1_fcf'], u)} and horizon FCF of {tot(f['year_n_fcf'], u)}:")
            add("")
            add(table(["Discount rate", "Required perpetual FCF", "vs base year 1", "vs base horizon"],
                      [[rate_label(x["rate"]), tot(x["implied_fcf"], u),
                        f"{x['implied_fcf'] / f['year1_fcf']:.2f}x" if f["year1_fcf"] > 0 else "n/a",
                        f"{x['implied_fcf'] / f['year_n_fcf']:.2f}x" if f["year_n_fcf"] > 0 else "n/a"] for x in f["rows"]]))
            add("")
        for f2 in im["f2"]:
            add(f"**F2 - what the price requires of '{f2['scenario']}'** (every other assumption held at the scenario's values).")
            add("")
            labels = res["labels"][f2["scenario"]]
            level_word = "EPS" if per_share_mode else "revenue"
            hd, rows = ["Discount rate"], []
            has_growth = bool(f2["free_growth_years"])
            has_margin = model["mode"] in ("drivers", "fcf_margin")
            has_scale = model["mode"] == "direct"
            if has_growth:
                a, b = f2["growth_window"]
                hd += [f"Implied {level_word} CAGR {labels[a - 1]}-{labels[b - 1]}", f"Horizon {level_word} required", "vs scenario"]
            if has_margin:
                hd += ["Implied terminal margin", "vs scenario"]
            if has_scale:
                hd += ["Implied multiple of every cash flow"]
            hd += ["Terminal requirement (explicit flows fixed)", "vs modelled"]
            any_perverse = False
            for r in rates:
                x = f2["by_rate"][r]
                row = [rate_label(r) + (" (r\\*)" if r == r_star else "")]
                if has_growth:
                    gsol = x["growth"]
                    if gsol["solved"]:
                        perverse = not gsol["value_rises_with_growth"]
                        any_perverse = any_perverse or perverse
                        row += [pct(gsol["x"]) + (" ‡" if perverse else ""), money(gsol["level_n"]),
                                f"{gsol['level_n'] / gsol['base_level_n']:.2f}x"]
                    else:
                        row += [f"none - {gsol['reason']}", "n/a", "n/a"]
                if has_margin:
                    msol = x["margin"]
                    if msol["solved"]:
                        row += [pct(msol["terminal_margin"]), f"{msol['x'] * 100:+.1f} pts"]
                    else:
                        row += [f"none - {msol['reason']}", "n/a"]
                if has_scale:
                    ssol = x["flow_scale"]
                    row += [f"{ssol['x']:.2f}x" if ssol["solved"] else f"none - {ssol['reason']}"]
                tr = x["terminal"]
                if tr["kind"] == "exit_multiple":
                    row += [f"{tr['required']:.1f}x {tr['metric']}" if tr["required"] is not None else "n/a",
                            f"{tr['required'] / tr['modelled']:.2f}x" if tr["required"] is not None else "n/a"]
                else:
                    row += [money(tr["required"]) + " terminal FCF",
                            f"{tr['required'] / tr['modelled']:.2f}x" if tr["modelled"] > 0 else "n/a"]
                rows.append(row)
            add(table(hd, rows))
            add("")
            if has_growth:
                a, b = f2["growth_window"]
                add(f"The growth solve replaces growth in {labels[a - 1]}-{labels[b - 1]} with one constant rate"
                    + (f" (the {a - 1} explicit level(s) before it stay fixed)" if a > 1 else "")
                    + "; margins, reinvestment, fade and terminal assumptions stay as modelled. "
                      "\"None\" is a finding, not an error: at these unit economics no growth rate reaches the price.")
                if any_perverse:
                    add("")
                    add("‡ At this point value falls as growth rises (growth consumes more capital than it earns), so "
                        "the figure is the growth at which value has dropped to the price, not a bar to clear. "
                        "The margin solve is the meaningful inversion here.")
                add("")
        f3 = im["f3"]
        add("**F3 - implied mid-cycle EPS at through-cycle multiples.** Operating value per share / multiple.")
        add("")
        if f3["rows"]:
            anchors = f3["anchors"]
            hd = ["Multiple", "Implied mid-cycle EPS"] + [f"vs {k.replace('_', ' ')} {usd(anchors[k])}" for k in ("mid_cycle", "all_time_peak") if k in anchors]
            add(table(hd, [[f"{x['multiple']:g}x", usd(x["implied_eps"])]
                           + [f"{x['implied_eps'] / anchors[k]:.2f}x" if anchors[k] > 0 else "n/a"
                              for k in ("mid_cycle", "all_time_peak") if k in anchors] for x in f3["rows"]]))
        else:
            add("Not computed: operating value per share is not positive.")
        add("")
        f5 = im["f5"]
        add("**F5 - market-implied probability.** P(bull) = (price - PV bear) / (PV bull - PV bear).")
        add("")
        if f5["available"]:
            rows = []
            for x in f5["rows"]:
                if x["p_bull"] is None:
                    ptxt = "n/a"
                elif x["state"] == "ok":
                    ptxt = pct(x["p_bull"], 0)
                else:
                    ptxt = f"{pct(x['p_bull'], 0)} - degenerate: {x['state']}"
                note = ("price exceeds every scenario PV" if x["above_every_scenario"]
                        else "price is below every scenario PV" if x["below_every_scenario"] else "")
                rows.append([rate_label(x["rate"]) + (" (r\\*)" if x["rate"] == r_star else ""),
                             usd(x["pv_bear"]), usd(x["pv_bull"]), ptxt, note])
            add(table(["Discount rate", "PV bear", "PV bull", "Implied P(bull)", "Note"], rows, ["l", "r", "r", "r", "l"]))
            if any(x["above_every_scenario"] for x in f5["rows"]):
                add("")
                add("Where the price exceeds every scenario PV, say so plainly and name the likeliest explanation: a lower "
                    "discount rate than the grid, or value a DCF does not capture (strategic scarcity, a backstop, option "
                    "value, flows).")
        else:
            add("Not computed: needs scenarios in the bear and bull slots.")
        add("")

    # ---- 7. hand-off: the handful of numbers the Entry & Exit Plan takes from this valuation ----------
    add("## 7. Hand-off to the Entry & Exit Plan")
    add("")
    if ho["complete"]:
        p, h2 = ho["at_primary"], ho["at_sensitivity"]
        add(f"- Primary rate r\\* = {rate_label(r_star)} · sensitivity rate r_hi = {rate_label(r_hi)}")
        add(f"- Scenario values at r\\*: bear {usd(p['bear'])} [{ho['names']['bear']}] / base {usd(p['base'])} "
            f"[{ho['names']['base']}] / bull {usd(p['bull'])} [{ho['names']['bull']}]")
        add(f"- At r_hi: {usd(h2['bear'])} / {usd(h2['base'])} / {usd(h2['bull'])}")
        if ho.get("weights"):
            w = ho["weights"]
            add(f"- Analyst weights {w['bear']:.0%} / {w['base']:.0%} / {w['bull']:.0%} -> PWV {usd(ho['pwv_primary'])} at r\\* "
                f"({usd(ho['pwv_sensitivity'])} at r_hi)"
                + (f" · PWR {ho['pwr'] * 100:+.1f}% vs {usd(price)}" if "pwr" in ho else " · PWR needs market.price"))
        else:
            add("- PWV: not computed - scenario weights missing")
        add(f"- Ordering check: bear < base < bull at r\\* - {'holds' if ho['ordered'] else 'FAILS (fix the slots)'}")
        if model["cyclical"]:
            a = ho["admissibility"]
            add(f"- Cyclical mean-reversion check: bear {a['bear']} / base {a['base']} / bull {a['bull']}")
        add("- Sizing bear for the plan = the bear value at r_hi. Levels, sizing and tranches are derived in "
            "`references/entry-exit-framework.md` from exactly these numbers.")
    else:
        add("Incomplete: assign scenarios to the bear, base and bull slots.")
    add("")

    # ---- 8. flags: warnings first, then notes, each with its code and the scenario it concerns --------
    add("## 8. Model flags")
    add("")
    if res["flags"]:
        for f in res["flags"]:
            scope = f" [{f['scenario']}]" if f["scenario"] else ""
            add(f"- **{f['level']}** `{f['code']}`{scope}: {f['message']}")
    else:
        add("None.")
    add("")

    # ---- 9. sources: the "sources" section of the inputs file, echoed so the report stands alone -------
    add("## 9. Input sources")
    add("")
    if inp["sources"]:
        for k, v in inp["sources"].items():
            add(f"- `{k}`: {v}")
    else:
        add("None recorded.")
    add("")
    return "\n".join(L)


# =============================================================================
# Rendering - JSON
# =============================================================================
# The same results as the Markdown report in machine-readable form, saved beside it. It serves as
# an audit trail (every intermediate figure, not only those the report prints) and as something a
# later run or another program can read without parsing prose.

def jsonable(x):
    """Make a results structure storable as JSON, which is stricter than Python: keys must be
    text (a rate used as a key, 0.10, becomes "0.1000"), there are no date objects (-> "2026-11-11")
    and no NaN or infinity (an undefined growth rate -> null). Works through nested dicts and lists."""
    if isinstance(x, dict):
        return {(f"{k:.4f}" if isinstance(k, float) else str(k)): jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [jsonable(v) for v in x]
    if isinstance(x, date):
        return x.isoformat()
    if isinstance(x, float) and not math.isfinite(x):
        return None
    return x


def results_json(res):
    """Everything analyze() produced, arranged for the results file: the conventions used, the
    discount-rate build, each scenario (its year-by-year rows, terminal year, diagnostics and its
    valuation at every rate), the sensitivity grid, the hand-off, the reverse DCF and the flags.
    Only the per-year present values ("pvs") are left out; they follow from the rows and the rate."""
    inp, disc = res["inp"], res["discount"]
    scenarios = []
    for s in res["results"]:
        proj = s["proj"]
        scenarios.append({
            "name": s["name"], "slot": s["slot"], "weight": s["weight"], "label": s["label"],
            "narrative": s["narrative"], "admissibility": s["admissibility"],
            "year_labels": res["labels"][s["name"]], "rows": proj["rows"], "terminal_row": proj["terminal_row"],
            "terminal": {"method": proj["method"], "growth": proj["g"], "cash_flow": proj["terminal_fcf"],
                         "exit_multiple": proj.get("exit_multiple"), "exit_metric": proj.get("exit_metric")},
            "diagnostics": proj["diag"],
            "values": {r: {k: v for k, v in val.items() if k != "pvs"} for r, val in s["values"].items()},
        })
    implied = res["implied"]
    if implied is not None:
        implied = copy.deepcopy(implied)
    return jsonable({
        "program": {"name": "dcf.py", "version": VERSION},
        "inputs_sha256": res.get("inputs_sha"),
        "meta": inp["meta"], "market": inp["market"],
        "conventions": {"mode": inp["model"]["mode"], "basis": inp["model"]["basis"],
                        "timing": inp["model"]["timing"], "stub": inp["meta"]["stub"], "units": inp["meta"]["units"]},
        "discount_rate": disc, "bridge": inp["bridge"], "shares": inp["shares"],
        "base_scenario": res["base"]["name"], "scenarios": scenarios, "sensitivity": res["sensitivity"],
        "anchor_rate_value": res["anchor_value"], "handoff": res["handoff"], "quality": res["quality"],
        "implied": implied, "flags": res["flags"], "sources": inp["sources"],
    })


# =============================================================================
# Template
# =============================================================================
# `python3 dcf.py template` prints what this function returns: a complete inputs file for an
# invented company, to be overwritten field by field. It is also the easiest way to see what a
# valid file looks like, and each example is tuned to run without a single warning (a test keeps
# it that way), so it shows what a clean model looks like too.

def template(mode="drivers"):
    """A complete, runnable example for a fictitious company. Every number is invented.

    The "_template": True marker makes normalize() refuse the file until it has been removed -
    a deliberate obstacle between an invented number and a real valuation. All four modes share
    the company-level sections; they differ in "model", "history" and the scenarios themselves.
    """
    # ---- the sections every mode shares ---------------------------------------------------------------
    t = {
        "_template": True,
        "_help": ("FICTITIOUS EXAMPLE. Replace every value with sourced company data, then delete the "
                  "\"_template\" key. Keys starting with '_' are comments and are ignored. Rates, margins and "
                  "growth are decimals (12% = 0.12). Monetary totals AND share counts use meta.units; prices, "
                  "EPS, strikes and conversion prices are plain currency per share. A per-year path may be a "
                  "number (flat), a list with one value per explicit year, or a ramp "
                  "{\"from\": a, \"to\": b, \"years\": k}. Field guide: the header comment of dcf.py."),
        "meta": {
            "ticker": "XMPL", "company": "Example Corp",
            "valuation_date": "2026-11-11", "currency": "USD", "units": "millions",
            "_help_fiscal": ("first_forecast_year_end = end of forecast year 1, which must be the fiscal year in "
                             "progress (or the next one). Omit both fields to make year 1 the next twelve months."),
            "first_forecast_year_end": "2027-06-30", "first_forecast_label": "FY2027",
            "balance_sheet_date": "2026-09-30",
            "fiscal_note": "Fiscal year ends June 30; FY2027 = July 2026 to June 2027.",
        },
        "market": {"price": 100.00, "price_date": "2026-11-10"},
        "shares": {
            "_help": ("count = basic shares + unvested RSUs/PSUs + announced or highly likely issuance. Do NOT "
                      "include options or convertibles listed below; the engine adds them at the model's value."),
            "count": 500.0,
            "options": [{"count": 12.0, "strike": 40.00}],
            "convertibles": [{"name": "2030 convertible notes", "principal": 1000.0, "conversion_price": 150.00}],
            "note": "498.2M basic (10-Q cover, 2026-10-30) + 1.8M unvested RSUs",
        },
        "bridge": {
            "_help": ("debt includes finance leases and the full principal of the convertibles above. Leave "
                      "operating-lease liabilities out when lease cost is inside EBIT. Haircut illiquid or "
                      "trapped assets yourself and say so in the note."),
            "cash_and_investments": 6000.0, "non_operating_assets": 500.0, "debt": 3000.0,
            "preferred_equity": 0.0, "minority_interest": 0.0, "other_claims": 0.0,
            "note": "Balance sheet 2026-09-30; equity stake carried at a 30% haircut",
        },
        "discount_rate": {
            "risk_free": 0.043, "equity_risk_premium": 0.05, "beta": 1.30, "additional_premium": 0.0,
            "pre_tax_cost_of_debt": 0.065, "tax_rate": 0.21, "grid": [0.10, 0.12, 0.14],
            "note": "10-year Treasury 4.30% on 2026-11-10; 5-year monthly beta 1.30; cost of debt = weighted coupon",
        },
        "implied": {
            "fcf_conversion": 0.80,
            "eps_anchors": {"run_rate": 4.10, "forward_consensus": 5.00, "all_time_peak": 4.40, "mid_cycle": 3.20},
        },
        "sources": {
            "market.price": "Exchange close 2026-11-10",
            "shares": "10-Q cover page (2026-10-30); equity note for options and RSUs",
            "bridge": "10-Q balance sheet and debt note, period ended 2026-09-30",
            "discount_rate": "Treasury.gov 10-year yield 2026-11-10; vendor beta, retrieved 2026-11-11",
            "history": "10-K FY2024-FY2026",
            "scenarios": "Management guidance (FQ1 call 2026-10-29); consensus via aggregator, retrieved 2026-11-11",
        },
    }
    # ---- the three scenarios' descriptions: (name, slot, weight, authorship, narrative) -------------------
    # The same three stories in every mode. Only the numbers that express them change, and those are
    # the `specs` lists below: one entry per scenario, in the same bear / base / bull order. Each
    # mode's last statement zips the descriptions with the numbers to build the scenario dicts.
    slots = [("Share loss", "bear", 0.25, "analyst construction",
              "Largest customer dual-sources; growth halves and margins give back the last two years of gains."),
             ("Guided path", "base", 0.50, "consensus-anchored",
              "FY2027-28 at consensus, then growth fades as the product cycle matures; margins hold near today's."),
             ("Platform win", "bull", 0.25, "analyst construction",
              "Second product line reaches scale; growth stays in the high teens and margins expand with mix.")]
    if mode == "drivers":
        t["model"] = {"mode": "drivers", "basis": "firm", "timing": "mid_year", "explicit_years": 5, "fade_years": 5,
                      "terminal_growth_cap": 0.03, "cyclical": False,
                      "mature_peer_multiple": {"metric": "ebitda", "value": 14.0}}
        t["history"] = {
            "periods": ["FY2024", "FY2025", "FY2026"],
            "revenue": [6200.0, 7400.0, 9000.0], "ebit": [1050.0, 1400.0, 1890.0], "da": [370.0, 450.0, 540.0],
            "capex": [500.0, 610.0, 760.0], "sbc": [430.0, 520.0, 630.0], "change_in_nwc": [None, 130.0, 170.0],
            "roic": [0.17, 0.19, 0.21],
            "note": "EBIT is GAAP operating income (after SBC)",
        }
        t["scenario_defaults"] = {
            "_help": "Applied to every scenario unless the scenario overrides the key.",
            "ebit_margin_basis": "gaap", "tax_rate": 0.19, "da_pct_revenue": 0.06,
            "nwc_pct_incremental_revenue": 0.10,
            "terminal": {"method": "gordon", "growth": 0.03, "capex_pct_revenue": 0.085},
        }
        # Per scenario: (revenue, EBIT-margin path, capex as a share of revenue). The base and bull
        # pin their first two years to "consensus" levels; the bear is written as growth rates only.
        specs = [({"base": 9000.0, "growth": [0.08, 0.06, 0.05, 0.04, 0.04]}, {"from": 0.20, "to": 0.17, "years": 3}, 0.080),
                 ({"base": 9000.0, "levels": [10600.0, 12200.0], "growth": [0.13, 0.11, 0.09]}, {"from": 0.215, "to": 0.225, "years": 5}, 0.085),
                 ({"base": 9000.0, "levels": [10900.0, 13100.0], "growth": [0.18, 0.16, 0.14]}, {"from": 0.22, "to": 0.27, "years": 5}, 0.090)]
        t["scenarios"] = [{"name": n, "slot": s, "weight": w, "label": lab, "narrative": nar,
                           "revenue": rev, "ebit_margin": m, "capex_pct_revenue": cx}
                          for (n, s, w, lab, nar), (rev, m, cx) in zip(slots, specs)]
    elif mode == "fcf_margin":
        t["model"] = {"mode": "fcf_margin", "basis": "firm", "timing": "mid_year", "explicit_years": 5, "fade_years": 5,
                      "terminal_growth_cap": 0.03, "cyclical": False}
        t["history"] = {"periods": ["FY2024", "FY2025", "FY2026"], "revenue": [6200.0, 7400.0, 9000.0],
                        "fcf": [560.0, 780.0, 1060.0], "sbc": [430.0, 520.0, 630.0],
                        "note": "fcf = unlevered free cash flow after SBC"}
        t["scenario_defaults"] = {"sbc_deducted": True, "terminal": {"method": "gordon", "growth": 0.03}}
        # Per scenario: (revenue, free-cash-flow margin path).
        specs = [({"base": 9000.0, "growth": [0.08, 0.06, 0.05, 0.04, 0.04]}, {"from": 0.11, "to": 0.10, "years": 3}),
                 ({"base": 9000.0, "levels": [10600.0, 12200.0], "growth": [0.13, 0.11, 0.09]}, {"from": 0.12, "to": 0.135, "years": 5}),
                 ({"base": 9000.0, "levels": [10900.0, 13100.0], "growth": [0.18, 0.16, 0.14]}, {"from": 0.125, "to": 0.17, "years": 5})]
        t["scenarios"] = [{"name": n, "slot": s, "weight": w, "label": lab, "narrative": nar,
                           "revenue": rev, "fcf_margin": m}
                          for (n, s, w, lab, nar), (rev, m) in zip(slots, specs)]
    elif mode == "eps":
        t["model"] = {"mode": "eps", "basis": "equity", "timing": "mid_year", "explicit_years": 5, "fade_years": 5,
                      "terminal_growth_cap": 0.03, "cyclical": False}
        t["history"] = {"periods": ["FY2024", "FY2025", "FY2026"], "eps": [2.60, 3.30, 4.10]}
        t["scenario_defaults"] = {"terminal": {"method": "gordon", "growth": 0.03, "fcf_conversion": 0.85}}
        # Per scenario: (EPS, FCF-conversion path). Equity basis, because consensus EPS is after interest.
        specs = [({"base": 4.10, "growth": [0.04, 0.03, 0.03, 0.03, 0.03]}, 0.70),
                 ({"base": 4.10, "levels": [5.00, 5.90], "growth": [0.12, 0.09, 0.06]}, {"from": 0.72, "to": 0.80, "years": 5}),
                 ({"base": 4.10, "levels": [5.30, 6.70], "growth": [0.18, 0.14, 0.10]}, {"from": 0.75, "to": 0.85, "years": 5})]
        t["scenarios"] = [{"name": n, "slot": s, "weight": w, "label": lab, "narrative": nar,
                           "eps": eps, "fcf_conversion": conv}
                          for (n, s, w, lab, nar), (eps, conv) in zip(slots, specs)]
    else:
        t["model"] = {"mode": "direct", "basis": "firm", "timing": "mid_year", "terminal_growth_cap": 0.03, "cyclical": False}
        t["scenario_defaults"] = {"terminal": {"method": "gordon", "growth": 0.03}}
        # Per scenario: ten years of cash flow, as they would come out of the analyst's own model.
        specs = [[900.0, 960.0, 1010.0, 1050.0, 1090.0, 1125.0, 1160.0, 1195.0, 1230.0, 1265.0],
                 [1150.0, 1420.0, 1700.0, 1980.0, 2240.0, 2470.0, 2670.0, 2840.0, 2980.0, 3100.0],
                 [1300.0, 1750.0, 2300.0, 2900.0, 3500.0, 4060.0, 4550.0, 4960.0, 5310.0, 5580.0]]
        t["scenarios"] = [{"name": n, "slot": s, "weight": w, "label": lab, "narrative": nar, "fcf": fcf}
                          for (n, s, w, lab, nar), fcf in zip(slots, specs)]
    return t


# =============================================================================
# Command line
# =============================================================================
# What happens when the file is run from a shell. main() at the bottom reads the command;
# run_file() is the whole pipeline for one inputs file; selftest() is a built-in health check.

def load_file(path):
    """Read an inputs file. Returns the parsed JSON and a 16-character fingerprint (SHA-256) of the
    file's exact bytes. The fingerprint is printed on the report, so a report can always be matched
    to the precise inputs that produced it - change one digit and the fingerprint changes."""
    with open(path, "rb") as fh:
        data = fh.read()
    try:
        raw = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InputError([f"{path}: not valid JSON ({exc})"])
    return raw, hashlib.sha256(data).hexdigest()[:16]


def run_file(path, out_dir=None, quiet=False):
    """The whole pipeline for one inputs file - the three steps named at the top of this file:
    load and validate, analyze, render. Writes <TICKER>-dcf-report.md and <TICKER>-dcf-results.json
    (next to the inputs unless out_dir says otherwise) and prints the report.

    If the inputs are rejected, normalize() raises InputError before anything is written, so a
    stale report from an earlier run is never mistaken for the result of this one."""
    raw, sha = load_file(path)
    inp = normalize(raw)                # STEP 1: validate
    res = analyze(inp)                  # STEP 2: value
    res["inputs_sha"] = sha
    md = render_markdown(res)           # STEP 3: present
    out_dir = out_dir or os.path.dirname(os.path.abspath(path))
    os.makedirs(out_dir, exist_ok=True)
    stem = inp["meta"]["ticker"].replace("/", "-").replace(" ", "-")
    md_path = os.path.join(out_dir, f"{stem}-dcf-report.md")
    json_path = os.path.join(out_dir, f"{stem}-dcf-results.json")
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write(md + "\n")
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(results_json(res), fh, indent=2)
        fh.write("\n")
    if not quiet:
        print(md)
    # The "wrote ..." lines go to stderr, so that what arrives on stdout is the report and nothing else.
    print(f"\n[dcf.py] wrote {md_path}\n[dcf.py] wrote {json_path}", file=sys.stderr)
    return res


def selftest():
    """Closed-form identities the engine must satisfy; a broken install fails here.

    `python3 dcf.py selftest` needs no inputs file and takes a second. It checks a handful of
    results whose right answer is known in advance - cases where finance gives an exact formula,
    or where the skill's own documents print a worked example. If someone edits this file and
    breaks the arithmetic, this is the quickest way to find out. The full suite is test_dcf.py.
    """
    checks = []

    def check(name, got, want, tol=1e-9):
        """Record one comparison. Passes when got and want agree to about nine significant digits."""
        ok = abs(got - want) <= tol * max(1.0, abs(want))
        checks.append((name, ok, got, want))

    def base_inputs(timing, levels, growth, n, **term):
        """The smallest valid inputs file: revenue 100 with a 20% free-cash-flow margin, no cash,
        no debt, 10 shares. Each check below varies only the timing, the revenue path and n."""
        return {"meta": {"ticker": "T", "valuation_date": "2026-01-01"}, "shares": {"count": 10},
                "bridge": {"cash_and_investments": 0, "debt": 0},
                "discount_rate": {"risk_free": 0.04, "equity_risk_premium": 0.05, "beta": 1.2},
                "model": {"mode": "fcf_margin", "timing": timing, "explicit_years": n},
                "scenarios": [{"name": "s", "slot": "base", "sbc_deducted": True, "fcf_margin": 0.2,
                               "revenue": {"base": 100.0, "levels": levels, "growth": growth},
                               "terminal": dict({"growth": 0.03}, **term)}]}

    # 1. A cash flow growing 3% forever is worth FCF1/(r-g), however the horizon is cut.
    #    Revenue grows 3% a year in the forecast AND in perpetuity, so the split between "forecast
    #    years" and "terminal value" is arbitrary: 1, 5 or 12 explicit years must all give
    #    100 x 1.03 x 20% / (10% - 3%) = 294.29. This one identity exercises the projection, the
    #    discounting and the terminal value together. Mid-year timing is worth (1.10)^0.5 more.
    for n in (1, 5, 12):
        inp = normalize(base_inputs("end_year", [], 0.03, n))
        v = scenario_value(inp["scenarios"][0], 0.10, inp)["operating_value"]
        check(f"growing perpetuity, end-year, n={n}", v, 100 * 1.03 * 0.2 / 0.07)
        inp = normalize(base_inputs("mid_year", [], 0.03, n))
        v = scenario_value(inp["scenarios"][0], 0.10, inp)["operating_value"]
        check(f"growing perpetuity, mid-year, n={n}", v, 100 * 1.03 * 0.2 / 0.07 * 1.10 ** 0.5)
    # 2. Treasury-stock and if-converted dilution against hand arithmetic.
    sh = {"count": 100.0, "options": [{"count": 10.0, "strike": 5.0}],
          "convertibles": [{"principal": 200.0, "conversion_price": 8.0, "shares": 25.0}]}
    v, n, conv = per_share_value(1000.0, sh, "firm")
    check("dilution fixed point", v, (1000.0 + conv) / n)
    check("dilution converts in the money", conv, 200.0)
    check("dilution share count", n, 100.0 + 10.0 * (1 - 5.0 / v) + 25.0)
    # 3. The growth solve recovers the growth that produced the price.
    #    Value a scenario built on 17% growth, call that value "the price", then ask the solver what
    #    growth the price implies. It has to answer 17%.
    inp = normalize(base_inputs("mid_year", [110.0], 0.17, 6))
    sc = inp["scenarios"][0]
    target = scenario_value(sc, 0.12, inp)["value_per_share_raw"]
    sol = solve_root(lambda c: scenario_value(sc, 0.12, inp, {"constant_growth": c})["value_per_share_raw"],
                     target, -0.5, 2.0, 0.01)
    check("reverse growth round trip", sol["x"], 0.17, 1e-7)
    # 4. The frameworks' worked examples, through the engine (end-of-year timing, as written there).
    def worked(basis, cash):
        """A one-year model whose values can be set by hand. Each scenario pays EPS x at the end of
        year 1 and is then sold for 9 x that EPS, so at 12% it is worth 10x / 1.12. Choosing
        x = 6.16, 16.8 and 29.12 gives exactly $55, $150 and $260 - the three scenario values of
        the entry-exit framework's worked example, whose 20/50/30 weights give a PWV of $164."""
        return {"meta": {"ticker": "T", "valuation_date": "2026-01-01"}, "market": {"price": 930.0 if cash else 100.0},
                "shares": {"count": 1.0}, "bridge": {"cash_and_investments": cash, "debt": 0.0},
                "discount_rate": {"risk_free": 0.04, "equity_risk_premium": 0.05, "beta": 1.6},
                "model": {"mode": "eps", "basis": basis, "timing": "end_year", "explicit_years": 1},
                "implied": {"fcf_conversion": 0.75, "terminal_growth": 0.03},
                "scenarios": [{"name": nm, "slot": slot, "weight": w, "fcf_conversion": 1.0,
                               "eps": {"base": 1.0, "levels": [x]},
                               "terminal": {"method": "exit_multiple", "exit_multiple": 9.0, "exit_metric": "eps",
                                            "growth": 0.03}}
                              for nm, slot, w, x in (("a", "bear", 0.2, 6.16), ("b", "base", 0.5, 16.8),
                                                     ("c", "bull", 0.3, 29.12))]}

    res = analyze(normalize(worked("firm", 18.0)))
    f1 = {row["rate"]: row["implied_eps"] for row in res["implied"]["f1"]["rows"]}
    check("F1 worked example: $930, $18 net cash, 12%, g 3%, conv 75%", f1[0.12], 912 * 0.09 / 0.7725)
    res = analyze(normalize(worked("equity", 0.0)))
    ho = res["handoff"]
    check("hand-off worked example: bear PV", ho["at_primary"]["bear"], 55.0)
    check("hand-off worked example: PWV 20/50/30 of 55/150/260", ho["pwv_primary"], 164.0)
    check("hand-off worked example: PWR at $100", ho["pwr"], 0.64)
    # 5. Every template runs end to end.
    for mode in MODES:
        tpl = template(mode)
        tpl.pop("_template")
        res = analyze(normalize(tpl))
        ho = res["handoff"]
        checks.append((f"template '{mode}' runs and orders bear < base < bull", bool(ho.get("ordered")), None, None))
        render_markdown(res)
        json.dumps(results_json(res))
    failed = [c for c in checks if not c[1]]
    for name, ok, got, want in checks:
        detail = "" if got is None else f"  got {got:.6f}  want {want:.6f}"
        print(f"{'ok  ' if ok else 'FAIL'}  {name}{detail}")
    print(f"\n{len(checks) - len(failed)}/{len(checks)} checks passed")
    return 1 if failed else 0


def main(argv=None):
    """Read the command line and do what it asks: run, check, template or selftest.

    Returns the exit code: 0 when everything ran, 2 when at least one inputs file was rejected or
    missing. With several files, a bad one does not stop the others from being processed."""
    # The report uses a few non-ASCII characters (the middle dot, the dagger); make sure they print
    # whatever the terminal's default encoding is.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(prog="dcf.py", description="Deterministic DCF and reverse-DCF engine "
                                                            "(equity-researching skill). The header comment of "
                                                            "dcf.py documents the inputs and the method.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("run", help="value one or more inputs files; print and save the report")
    p.add_argument("inputs", nargs="+")
    p.add_argument("--out-dir", help="where to write <TICKER>-dcf-report.md and -results.json (default: next to the inputs)")
    p.add_argument("--quiet", action="store_true", help="write the files but do not print the report")
    p = sub.add_parser("check", help="validate inputs files without valuing them")
    p.add_argument("inputs", nargs="+")
    p = sub.add_parser("template", help="print a runnable example inputs file (fictitious numbers)")
    p.add_argument("--mode", choices=MODES, default="drivers")
    sub.add_parser("selftest", help="verify the engine against closed-form identities")
    args = ap.parse_args(argv)

    if args.cmd == "template":
        print(json.dumps(template(args.mode), indent=2))
        return 0
    if args.cmd == "selftest":
        return selftest()
    status = 0
    for path in args.inputs:
        try:
            if args.cmd == "check":
                raw, _ = load_file(path)
                inp = normalize(raw)
                # Also run the discount-rate step: two input problems (debt with no cost of debt, a
                # WACC with nothing to weight it by) can only be detected there.
                compute_discount(inp, Flags())
                print(f"{path}: inputs are valid ({len(inp['scenarios'])} scenario(s), mode {inp['model']['mode']})")
            else:
                run_file(path, args.out_dir, args.quiet)
        except InputError as exc:
            status = 2
            print(f"\n{path}: inputs rejected - fix these and run again:", file=sys.stderr)
            for prob in exc.problems:
                print(f"  - {prob}", file=sys.stderr)
        except FileNotFoundError:
            status = 2
            print(f"{path}: file not found", file=sys.stderr)
    return status


if __name__ == "__main__":
    sys.exit(main())
