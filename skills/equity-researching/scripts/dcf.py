#!/usr/bin/env python3
"""DCF and reverse DCF from "Expectations Investing" (Rappaport and Mauboussin,
revised edition).

SOURCES
    Chapter 2, "Summary Illustration" (table 2.1)           the DCF
    Chapter 2 appendix, "Estimating Continuing Value"       equations 2.6 to 2.9
    The authors' price-implied expectations spreadsheet     the reverse DCF
      (expectationsinvesting.com, Online Tutorial 8)
    The tests in tests/ check this program against the numbers printed in all three.

THE IDEA
    The forecast period is the number of years a company is expected to keep
    investing at returns above its cost of capital. This program builds one
    table with a row per year. Each row answers one question: what is the
    company worth if the forecast period ends in this year?

    DCF          You choose the forecast period. That year's row gives the
                 shareholder value per share.
    Reverse DCF  The share price chooses it. The number of years before value
                 per share first rises above the price is the market-implied
                 forecast period: how many years of this forecast the price
                 already pays for.

THE FORECAST (each year, in amounts)
    Five lines: sales, operating profit, cash taxes, fixed-capital investment
    and working-capital investment. Give a line's yearly amounts where you
    have them, for example management's projections; any year without an
    amount is worked out from that line's rate (its value driver), as in the
    book:
    sales                       = last year's sales x (1 + sales growth rate)
    operating profit            = sales x operating profit margin
    cash taxes                  = operating profit x cash tax rate
    fixed-capital investment    = change in sales x incremental fixed-capital rate
    working-capital investment  = change in sales x incremental working-capital rate
    The valuation itself only ever sees the amounts.

THE ARITHMETIC (each year)
    NOPAT                       = operating profit - cash taxes
    free cash flow              = NOPAT - both investments
    present value               = free cash flow / (1 + cost of capital) ^ year
                                  (^ (year - 0.5) with mid-year discounting, below)

THE VALUE (if the forecast period ends in that year)
    continuing value   = NOPAT x (1 + growth) / (cost of capital - growth)
    corporate value    = cumulative present value of free cash flow
                         + continuing value / (1 + cost of capital) ^ year
    shareholder value  = corporate value + nonoperating assets - debt
    value per share    = shareholder value / shares outstanding

    "growth" is how fast NOPAT grows after the forecast period. The book's
    four continuing value methods differ only in that one number:
      perpetuity                          0
      perpetuity_with_inflation           inflation
      perpetuity_with_partial_inflation   inflation x inflation_recouped
      perpetuity_with_decline             minus decline_rate
    The book finds partial inflation the best fit for most companies. To
    assume growth above inflation, which it says to do very sparingly, enter
    that growth rate as the inflation rate.

DISCOUNTING (not from the book)
    The book discounts each year's cash flow from the end of that year. Banks
    usually assume cash comes in through the year, so on average at mid-year,
    which makes each year's cash flow worth (1 + cost of capital) ^ 0.5 more.
    They differ on the continuing value, so there are two mid-year choices:
      year_end                             the book: every amount at a year end (default)
      mid_year                             free cash flow at mid-year; continuing
                                           value at the end of the forecast period
      mid_year_including_continuing_value  the continuing value half a year
                                           earlier too, as if it were mid-year
                                           cash flows as well
    Mid-year adds about 1% (mid_year) to 4% (including continuing value) to the
    value, and so shortens the market-implied forecast period.

HOW TO RUN IT
    python3 dcf.py inputs.json           print the report
    python3 dcf.py inputs.json --json    print the same results as JSON
    python3 dcf.py --example             print an example inputs file
    --log-level DEBUG|INFO|WARNING|ERROR how much to log to stderr (default WARNING):
                                           DEBUG    every row as it is worked out
                                           INFO     the answers, and the inputs file read
                                           WARNING  results worth a second look: a
                                                    negative value per share, or no
                                                    market-implied forecast period
                                           ERROR    an inputs file that cannot be read
                                                    or is rejected (always shown)

THE INPUTS FILE (JSON)
    Rates are decimals: write 7% as 0.07. Money amounts and the share count
    use one unit, for example $ millions and millions of shares.

    The forecast: for each line, its amounts, its rate, or both (amounts for
    the years they cover, the rate after that).
      amounts (a list, year 1 first)   rate
      sales                            sales_growth_rate
      operating_profit                 operating_profit_margin (operating profit / sales)
      cash_taxes                       cash_tax_rate (cash taxes / operating profit)
      fixed_capital_investment         incremental_fixed_capital_rate (per $1 of added sales)
      working_capital_investment       incremental_working_capital_rate (per $1 of added sales)
    starting_sales                     sales of the last full year (year 0); needed
                                       when year 1 of sales or an investment
                                       comes from a rate
    cost_of_capital                    the discount rate
    continuing_value_method            one of the four names above
    inflation                          needed by the two inflation methods
    inflation_recouped                 share of inflation the company can pass on,
                                       0 to 1 (partial-inflation method only)
    decline_rate                       yearly decline (decline method only)
    nonoperating_assets                for example excess cash and securities
    debt                               debt and other liabilities
    shares_outstanding                 the latest diluted share count a
                                       filing discloses (see below)
    forecast_years                     your forecast period: gives the DCF
    share_price                        today's price: gives the reverse DCF
    company, ticker, base_year         labels, optional (base_year is year 0)
    max_years                          how far the table runs, default 25; a line
                                       given in amounts with no rate ends it at
                                       its last amount
    discounting                        year_end (default), mid_year, or
                                       mid_year_including_continuing_value

    Give forecast_years, share_price, or both.
    The five rates (growth, margin, tax rate and the two investment rates)
    are one number each, held constant as in the book, or a list of yearly
    numbers whose last entry repeats for every later year.
    nonoperating_assets and debt are one number each, or named parts that the
    program adds up, for example {"bonds": 4000, "leases": 170}.
    shares_outstanding: use the diluted weighted average shares from the
    latest 10-Q or 10-K income statement; the company has already counted its
    options and share units there. In a loss year that count leaves them out,
    so use the cover page's shares outstanding plus restricted stock units.
    Do not also put the options in debt (the book's other way, which values
    them instead), or they count twice.
    Any key that starts with "_" is ignored, so notes and sources can live in
    the file.
"""

import argparse
import json
import logging
import sys
from decimal import ROUND_HALF_UP, Decimal

MAX_YEARS = 25  # the authors' spreadsheet runs 25 years

# The program's log, on stderr. main() sets its level from --log-level; when
# another program imports this one, that program's logging settings apply.
log = logging.getLogger("dcf")

# The five lines of the forecast, each with the rate (value driver) that works
# it out in a year with no amount given. A rate is one number or a list of
# yearly numbers; amounts are a list.
LINES = {
    "sales": "sales_growth_rate",
    "operating_profit": "operating_profit_margin",
    "cash_taxes": "cash_tax_rate",
    "fixed_capital_investment": "incremental_fixed_capital_rate",
    "working_capital_investment": "incremental_working_capital_rate",
}
DRIVERS = list(LINES.values())

# The continuing value methods and the extra inputs each one needs.
METHODS = {
    "perpetuity": [],
    "perpetuity_with_inflation": ["inflation"],
    "perpetuity_with_partial_inflation": ["inflation", "inflation_recouped"],
    "perpetuity_with_decline": ["decline_rate"],
}

REQUIRED = ["cost_of_capital", "continuing_value_method", "nonoperating_assets", "debt", "shares_outstanding"]
OPTIONAL = list(LINES) + DRIVERS + [
    "starting_sales", "inflation", "inflation_recouped", "decline_rate",
    "forecast_years", "share_price",
    "company", "ticker", "base_year", "max_years", "discounting",
]

# How many years earlier than the year end each amount is discounted:
# (free cash flow, continuing value).
DISCOUNTING = {
    "year_end": (0.0, 0.0),
    "mid_year": (0.5, 0.0),
    "mid_year_including_continuing_value": (0.5, 0.5),
}

# The allowed range of each rate. Rates are decimals, so a number such as 7 or
# 17.5 is almost always a percentage typed by mistake, and is rejected.
LIMITS = {
    "sales_growth_rate": (-0.99, 5),
    "operating_profit_margin": (-1, 1),
    "cash_tax_rate": (0, 1),
    "incremental_fixed_capital_rate": (-5, 5),
    "incremental_working_capital_rate": (-5, 5),
    "cost_of_capital": (0.001, 1),
    "inflation": (-0.2, 0.5),
    "inflation_recouped": (0, 1),
    "decline_rate": (0, 0.9),
}

# The example is the authors' Domino's Pizza case (September 2020, $ millions),
# from their spreadsheet. forecast_years is not from the book: it is there only
# to show the DCF beside the reverse DCF.
EXAMPLE = {
    "company": "Domino's Pizza",
    "ticker": "DPZ",
    "base_year": 2019,
    "starting_sales": 3618.8,
    "sales_growth_rate": 0.07,
    "operating_profit_margin": 0.175,
    "cash_tax_rate": 0.165,
    "incremental_fixed_capital_rate": 0.15,
    "incremental_working_capital_rate": 0.10,
    "cost_of_capital": 0.05357,
    "continuing_value_method": "perpetuity_with_inflation",
    "inflation": 0.016,
    "nonoperating_assets": 391.9,
    "debt": 4170.0,
    "shares_outstanding": 39.35,
    "forecast_years": 10,
    "share_price": 418.0,
}


class InputError(Exception):
    """The inputs are missing something or hold a number that cannot be right."""

    def __init__(self, problems):
        super().__init__("; ".join(problems))
        self.problems = problems


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def is_number(value):
    """True for 3 or 0.07. False for text, lists, and true/false."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def is_whole_number(value):
    return isinstance(value, int) and not isinstance(value, bool)


def for_year(driver, year):
    """The value of a driver in a given year.

    One number applies to every year. A list gives year 1, year 2, and so on,
    and its last entry repeats for every later year.
    """
    if isinstance(driver, list):
        return driver[min(year, len(driver)) - 1]
    return driver


def total(amount):
    """One number, or the sum of named parts such as {"bonds": 4000, "leases": 170}."""
    if isinstance(amount, dict):
        return sum(amount.values())
    return amount


def years_text(count):
    return f"{count} year" + ("" if count == 1 else "s")


# ---------------------------------------------------------------------------
# Checking the inputs
# ---------------------------------------------------------------------------

def check_inputs(raw):
    """Return the inputs without their "_" notes, or raise InputError.

    Every problem is collected first, so one run reports all of them.
    """
    if not isinstance(raw, dict):
        raise InputError(["the inputs file must hold one JSON object: { ... }"])
    inp = {key: value for key, value in raw.items() if not key.startswith("_")}
    problems = [f"'{key}' is not an input this program knows"
                for key in inp if key not in REQUIRED + OPTIONAL]

    method = inp.get("continuing_value_method")
    if "continuing_value_method" in inp and (not isinstance(method, str) or method not in METHODS):
        problems.append("'continuing_value_method' must be one of: " + ", ".join(METHODS))
        method = None
    needed = REQUIRED + METHODS.get(method, [])
    problems += [f"'{key}' is missing" for key in needed if key not in inp]

    def check(name, value, low=None, high=None, positive=False):
        """Note a problem unless value is a number inside its allowed range."""
        if not is_number(value):
            problems.append(f"{name} must be a number")
        elif positive and value <= 0:
            problems.append(f"{name} must be greater than 0")
        elif (low is not None and value < low) or (high is not None and value > high):
            problems.append(f"{name} is {value}, outside the allowed {low} to {high}"
                            " (rates are decimals: write 7% as 0.07)")

    for key, (low, high) in LIMITS.items():
        if key not in inp:
            continue
        if key in DRIVERS and isinstance(inp[key], list):
            if not inp[key]:
                problems.append(f"'{key}' is an empty list")
            for position, item in enumerate(inp[key], 1):
                check(f"'{key}' year {position}", item, low, high)
        else:
            check(f"'{key}'", inp[key], low, high)

    lines_ok = True
    for line, driver in LINES.items():
        if line not in inp and driver not in inp:
            problems.append(f"give '{line}' (yearly amounts) or '{driver}' (a rate)")
            lines_ok = False
        elif line in inp:
            if not isinstance(inp[line], list) or not inp[line]:
                problems.append(f"'{line}' must be a list of yearly amounts, year 1 first")
                lines_ok = False
            else:
                for position, amount in enumerate(inp[line], 1):
                    check(f"'{line}' year {position}", amount, positive=(line == "sales"))
    year_1_from_a_rate = [line for line in ("sales", "fixed_capital_investment", "working_capital_investment")
                          if not isinstance(inp.get(line), list) or not inp[line]]
    if year_1_from_a_rate and "starting_sales" not in inp:
        problems.append("'starting_sales' is missing: year 1 of " + ", ".join(
            f"'{line}'" for line in year_1_from_a_rate) + " comes from a rate")

    for key in ("nonoperating_assets", "debt"):
        if isinstance(inp.get(key), dict):
            for part, amount in inp[key].items():
                check(f"'{key}' part '{part}'", amount)
        elif key in inp:
            check(f"'{key}'", inp[key])

    for key in ("starting_sales", "shares_outstanding", "share_price"):
        if key in inp:
            check(f"'{key}'", inp[key], positive=True)

    if inp.setdefault("discounting", "year_end") not in DISCOUNTING:
        problems.append("'discounting' must be one of: " + ", ".join(DISCOUNTING))

    max_years = inp.setdefault("max_years", MAX_YEARS)
    if not is_whole_number(max_years) or not 1 <= max_years <= 100:
        problems.append("'max_years' must be a whole number from 1 to 100")
        inp["max_years"] = MAX_YEARS
    table = table_years(inp) if lines_ok else inp["max_years"]
    if "forecast_years" in inp:
        years = inp["forecast_years"]
        if not is_whole_number(years) or not 1 <= years <= table:
            problems.append(f"'forecast_years' must be a whole number from 1 to {table}")
    if "base_year" in inp and not is_whole_number(inp["base_year"]):
        problems.append("'base_year' must be a whole number such as 2025")
    if "forecast_years" not in inp and "share_price" not in inp:
        problems.append("give 'forecast_years' (for the DCF), 'share_price'"
                        " (for the reverse DCF), or both")

    if not problems and inp["cost_of_capital"] <= growth_after_forecast_period(inp):
        problems.append("'cost_of_capital' must be higher than the growth assumed after"
                        " the forecast period, or the continuing value has no meaning")
    if problems:
        raise InputError(problems)
    log.debug("inputs checked: %s", inp)
    return inp


# ---------------------------------------------------------------------------
# The valuation
# ---------------------------------------------------------------------------

def growth_after_forecast_period(inp):
    """How fast NOPAT grows after the forecast period, under the chosen method."""
    method = inp["continuing_value_method"]
    if method == "perpetuity":
        return 0.0                                          # level forever
    if method == "perpetuity_with_inflation":
        return inp["inflation"]                             # keeps up with inflation
    if method == "perpetuity_with_partial_inflation":
        return inp["inflation"] * inp["inflation_recouped"]  # keeps up with part of it
    return -inp["decline_rate"]                             # perpetuity_with_decline


def continuing_value(nopat, cost_of_capital, growth):
    """Value, at the end of the forecast period, of everything that comes after.

    The appendix's equations 2.6 to 2.9 in one line. NOPAT is the last forecast
    year's. With growth of 0 this is NOPAT / cost of capital.
    """
    return nopat * (1 + growth) / (cost_of_capital - growth)


def table_years(inp):
    """How many years the table runs: max_years, or fewer when a line has
    amounts and no rate to carry it past them."""
    years = inp["max_years"]
    for line, driver in LINES.items():
        if driver not in inp:
            years = min(years, len(inp[line]))
    return years


def projection(inp):
    """The forecast in amounts, one dict per year: sales, operating profit,
    cash taxes and the two investments.

    A year's amount is the one given, if there is one. Otherwise it is worked
    out from the line's rate by the book's arithmetic (THE FORECAST above).
    """
    def given(line, year):
        amounts = inp.get(line)
        return amounts[year - 1] if amounts is not None and year <= len(amounts) else None

    def amount(line, year, from_rate):
        value = given(line, year)
        return value if value is not None else from_rate(for_year(inp[LINES[line]], year))

    forecast = []
    last_sales = inp.get("starting_sales")
    for year in range(1, table_years(inp) + 1):
        sales = amount("sales", year, lambda growth: last_sales * (1 + growth))
        operating_profit = amount("operating_profit", year, lambda margin: sales * margin)
        cash_taxes = amount("cash_taxes", year, lambda tax_rate: operating_profit * tax_rate)
        fixed = amount("fixed_capital_investment", year, lambda rate: (sales - last_sales) * rate)
        working = amount("working_capital_investment", year, lambda rate: (sales - last_sales) * rate)
        forecast.append({
            "year": year,
            "sales": sales,
            "operating_profit": operating_profit,
            "cash_taxes": cash_taxes,
            "fixed_capital_investment": fixed,
            "working_capital_investment": working,
        })
        last_sales = sales
    return forecast


def build_rows(inp, forecast):
    """One row per year of the forecast, in the order of the book's table 2.1.

    Uses the forecast's amounts only, never the rates. The value columns in a
    row (continuing value onwards) assume the forecast period ends in that
    row's year.
    """
    cost_of_capital = inp["cost_of_capital"]
    growth = growth_after_forecast_period(inp)
    log.debug("cost of capital %s, growth after the forecast period %s, discounting %s",
              cost_of_capital, growth, inp["discounting"])
    nonoperating_assets = total(inp["nonoperating_assets"])
    debt = total(inp["debt"])
    cash_flow_shift, continuing_value_shift = DISCOUNTING[inp["discounting"]]

    rows = []
    cumulative_pv = 0.0
    for line in forecast:
        year, sales = line["year"], line["sales"]
        operating_profit, cash_taxes = line["operating_profit"], line["cash_taxes"]
        fixed, working = line["fixed_capital_investment"], line["working_capital_investment"]
        nopat = operating_profit - cash_taxes
        free_cash_flow = nopat - fixed - working

        # The book: cash arrives at each year end. Mid-year: half a year sooner.
        pv_free_cash_flow = free_cash_flow / (1 + cost_of_capital) ** (year - cash_flow_shift)
        cumulative_pv += pv_free_cash_flow
        pv_continuing_value = (continuing_value(nopat, cost_of_capital, growth)
                               / (1 + cost_of_capital) ** (year - continuing_value_shift))

        corporate_value = cumulative_pv + pv_continuing_value
        shareholder_value = corporate_value + nonoperating_assets - debt
        rows.append({
            "year": year,
            "sales": sales,
            "operating_profit": operating_profit,
            "cash_taxes": cash_taxes,
            "nopat": nopat,
            "fixed_capital_investment": fixed,
            "working_capital_investment": working,
            "free_cash_flow": free_cash_flow,
            "pv_free_cash_flow": pv_free_cash_flow,
            "cumulative_pv_free_cash_flow": cumulative_pv,
            "pv_continuing_value": pv_continuing_value,
            "corporate_value": corporate_value,
            "shareholder_value": shareholder_value,
            "value_per_share": shareholder_value / inp["shares_outstanding"],
        })
        log.debug("year %d: sales %.4f, NOPAT %.4f, free cash flow %.4f, PV %.4f, PV of continuing"
                  " value %.4f, corporate value %.4f, value per share %.4f", year, sales, nopat,
                  free_cash_flow, pv_free_cash_flow, pv_continuing_value, corporate_value,
                  rows[-1]["value_per_share"])
    return rows


def market_implied_forecast_period(rows, share_price):
    """Reverse DCF: how many years of the forecast the share price pays for.

    The rule of the authors' spreadsheet: count the years before value per
    share first rises above the price.
      found           a whole number of years
      less_than_1     even a one-year forecast period is worth more than the price
      more_than_max   the price is still higher at the end of the table
      none            value per share never reaches the price and is falling
                      as the forecast period lengthens: with these drivers
                      growth costs more than it earns
    """
    values = [row["value_per_share"] for row in rows]
    years = 0
    while years < len(values) and values[years] <= share_price:
        years += 1

    if years == 0:
        status, label = "less_than_1", "less than 1 year"
    elif years < len(values) or values[-1] == share_price:
        status, label = "found", years_text(years)
    elif len(values) == 1 or values[-1] > values[-2]:
        status, label = "more_than_max", "more than " + years_text(len(values))
    else:
        status, label = "none", "none"
    if status == "found":
        log.info("market-implied forecast period: %s at a share price of %s", label, share_price)
    else:
        log.warning("no market-implied forecast period at a share price of %s: %s", share_price, {
            "less_than_1": "even a one-year forecast period is worth more than the price",
            "more_than_max": f"the price is still higher after {len(values)} years",
            "none": "value per share never reaches the price and falls as the forecast period"
                    " lengthens (growth costs more than it earns)",
        }[status])
    return {
        "share_price": share_price,
        "status": status,
        "years": years if status == "found" else None,
        "label": label,
    }


def analyse(raw):
    """Check the inputs, build the table, and read the two answers off it."""
    inp = check_inputs(raw)
    rows = build_rows(inp, projection(inp))
    result = {
        "inputs": inp,
        "growth_after_forecast_period": growth_after_forecast_period(inp),
        "dcf": None,
        "reverse_dcf": None,
        "rows": rows,
    }
    if "forecast_years" in inp:
        row = rows[inp["forecast_years"] - 1]
        result["dcf"] = {
            "forecast_years": inp["forecast_years"],
            "corporate_value": row["corporate_value"],
            "shareholder_value": row["shareholder_value"],
            "value_per_share": row["value_per_share"],
        }
        log.info("DCF value per share %.4f with a %d-year forecast period", row["value_per_share"],
                 inp["forecast_years"])
        if row["value_per_share"] < 0:
            log.warning("value per share is negative (%.4f): debt is more than the company is worth"
                        " with a %d-year forecast period", row["value_per_share"], inp["forecast_years"])
    if "share_price" in inp:
        result["reverse_dcf"] = market_implied_forecast_period(rows, inp["share_price"])
    return result


# ---------------------------------------------------------------------------
# The report
# ---------------------------------------------------------------------------

def money(value):
    """Two decimals, with halves rounded up as in the book's tables (4.125 -> 4.13).

    The value is first rounded to nine decimals so that arithmetic noise such
    as 9.874999999999998 still counts as 9.875.
    """
    cents = Decimal(f"{value:.9f}").quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{cents:,.2f}"


def rate(value):
    """0.05357 -> '5.357%', 0.07 -> '7%'."""
    return f"{value * 100:.3f}".rstrip("0").rstrip(".") + "%"


def driver_text(driver):
    if isinstance(driver, list):
        return ", ".join(rate(item) for item in driver) + " (last one repeats)"
    return rate(driver)


def amount_text(amount):
    if isinstance(amount, dict):
        parts = ", ".join(f"{name} {money(value)}" for name, value in amount.items())
        return f"{money(total(amount))} ({parts})"
    return money(amount)


def method_text(inp, growth):
    method = inp["continuing_value_method"]
    if method == "perpetuity":
        return "perpetuity (NOPAT stays level after the forecast period)"
    if method == "perpetuity_with_inflation":
        return f"perpetuity with inflation (NOPAT grows {rate(growth)} a year)"
    if method == "perpetuity_with_partial_inflation":
        return (f"perpetuity with partial inflation ({rate(inp['inflation_recouped'])} of"
                f" {rate(inp['inflation'])} inflation: NOPAT grows {rate(growth)} a year)")
    return f"perpetuity with decline (NOPAT falls {rate(inp['decline_rate'])} a year)"


# How the report names each line: as amounts, and as a rate.
LINE_LABELS = {
    "sales": ("Sales", "Sales growth rate"),
    "operating_profit": ("Operating profit", "Operating profit margin"),
    "cash_taxes": ("Cash taxes", "Cash tax rate"),
    "fixed_capital_investment": ("Fixed-capital investment", "Incremental fixed-capital investment rate"),
    "working_capital_investment": ("Working-capital investment", "Incremental working-capital investment rate"),
}

DISCOUNTING_TEXT = {
    "year_end": "year end (the book)",
    "mid_year": "mid-year for free cash flow; continuing value at year end",
    "mid_year_including_continuing_value": "mid-year, continuing value included",
}


def markdown_table(headers, rows):
    lines = ["| " + " | ".join(headers) + " |",
             "|" + "|".join("---:" for _ in headers) + "|"]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join(lines)


def report(result):
    """The results as a short Markdown report."""
    inp, rows = result["inputs"], result["rows"]
    dcf, reverse = result["dcf"], result["reverse_dcf"]
    base_year = inp.get("base_year")

    def year_text(year):
        return f"{year} ({base_year + year})" if base_year is not None else str(year)

    name = " ".join(filter(None, [str(inp.get("company", "")),
                                  f"({inp['ticker']})" if inp.get("ticker") else ""]))
    out = [f"# {name + ': ' if name else ''}DCF and reverse DCF", "",
           "Method: Expectations Investing (Rappaport and Mauboussin)."
           + (f" Year 0 is {base_year}." if base_year is not None else ""), ""]

    # --- Inputs ---
    lines = [("Starting sales", money(inp["starting_sales"]))] if "starting_sales" in inp else []
    for line, driver in LINES.items():
        amount_label, rate_label = LINE_LABELS[line]
        if line in inp:
            text = ", ".join(money(amount) for amount in inp[line])
            if driver in inp:
                text += f"; then {rate_label[0].lower() + rate_label[1:]} {driver_text(inp[driver])}"
            lines.append((amount_label, text))
        else:
            lines.append((rate_label, driver_text(inp[driver])))
    lines += [
        ("Cost of capital", rate(inp["cost_of_capital"])),
        ("Continuing value", method_text(inp, result["growth_after_forecast_period"])),
        ("Discounting", DISCOUNTING_TEXT[inp["discounting"]]),
        ("Nonoperating assets", amount_text(inp["nonoperating_assets"])),
        ("Debt and other liabilities", amount_text(inp["debt"])),
        ("Shares outstanding", f"{inp['shares_outstanding']:,.2f}"),
    ]
    if dcf:
        lines.append(("Forecast period", years_text(dcf["forecast_years"])))
    if reverse:
        lines.append(("Share price", money(reverse["share_price"])))
    out += ["## Inputs", "", "| Input | Value |", "|---|---:|"]
    out += [f"| {label} | {value} |" for label, value in lines]

    # --- Results ---
    out += ["", "## Results", ""]
    if dcf:
        out.append(f"- **DCF value per share: {money(dcf['value_per_share'])}** with a"
                   f" {dcf['forecast_years']}-year forecast period (shareholder value"
                   f" {money(dcf['shareholder_value'])}).")
    if reverse:
        price, status, years = money(reverse["share_price"]), reverse["status"], reverse["years"]
        headline = f"- **Market-implied forecast period: {reverse['label']}** at a share price of {price}."
        if status == "found" and years < len(rows):
            detail = (f" Value per share is {money(rows[years - 1]['value_per_share'])} with {years}"
                      f" and {money(rows[years]['value_per_share'])} with {years + 1}.")
        elif status == "found":
            detail = f" Value per share is {money(rows[-1]['value_per_share'])} with {years}."
        elif status == "less_than_1":
            detail = (f" Even a one-year forecast period is worth"
                      f" {money(rows[0]['value_per_share'])} a share.")
        elif status == "more_than_max":
            detail = (f" After {len(rows)} years value per share is only"
                      f" {money(rows[-1]['value_per_share'])}.")
        else:
            best = max(rows, key=lambda row: row["value_per_share"])
            detail = (f" No forecast period reaches the price: value per share peaks at"
                      f" {money(best['value_per_share'])} ({best['year']}-year forecast period) and falls"
                      f" after that, because with these drivers growth costs more than it earns.")
        out.append(headline + detail)
    if dcf and reverse:
        gap = dcf["value_per_share"] / reverse["share_price"] - 1
        out.append(f"- The DCF value is {abs(gap) * 100:.1f}% {'above' if gap >= 0 else 'below'}"
                   " the share price.")

    # --- Tables: show as far as the later of the two answers, plus one year ---
    last = max(5, dcf["forecast_years"] if dcf else 0,
               (reverse["years"] or 0) + 1 if reverse else 0)
    if reverse and reverse["status"] == "more_than_max":
        last = len(rows)
    shown = rows[:min(last, len(rows))]

    out += ["", "## Free cash flow", "", markdown_table(
        ["Year", "Sales", "Operating profit", "Cash taxes", "NOPAT",
         "Fixed-capital investment", "Working-capital investment", "Free cash flow",
         "PV of free cash flow"],
        [[year_text(row["year"])] + [money(row[key]) for key in (
            "sales", "operating_profit", "cash_taxes", "nopat", "fixed_capital_investment",
            "working_capital_investment", "free_cash_flow", "pv_free_cash_flow")]
         for row in shown])]

    def mark(row):
        notes = []
        if dcf and row["year"] == dcf["forecast_years"]:
            notes.append("your forecast period")
        if reverse and row["year"] == reverse["years"]:
            notes.append("market-implied")
        return ", ".join(notes)

    out += ["", "## Value by forecast period", "",
            "Each row is the value if the forecast period ends in that year.", "",
            markdown_table(
                ["Year", "Cumulative PV of free cash flow", "PV of continuing value",
                 "Corporate value", "Shareholder value", "Value per share", ""],
                [[year_text(row["year"])] + [money(row[key]) for key in (
                    "cumulative_pv_free_cash_flow", "pv_continuing_value", "corporate_value",
                    "shareholder_value", "value_per_share")] + [mark(row)]
                 for row in shown])]
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="DCF and reverse DCF from Expectations Investing. "
                    "The comment at the top of dcf.py explains the inputs.")
    parser.add_argument("inputs", nargs="?", help="JSON file with the inputs")
    parser.add_argument("--json", action="store_true", help="print the results as JSON")
    parser.add_argument("--example", action="store_true", help="print an example inputs file")
    parser.add_argument("--log-level", default="WARNING", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        help="how much to log to stderr (default WARNING)")
    args = parser.parse_args(argv)

    # Log to stderr, so the report or JSON on stdout is never mixed with it.
    # --log-level sets what this handler prints. The logger lets through
    # anything either it or the caller's logging (a test runner, say) wants.
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    handler.setLevel(args.log_level)
    level = log.level
    log.addHandler(handler)
    log.setLevel(min(getattr(logging, args.log_level), logging.getLogger().getEffectiveLevel()))
    try:
        return run(args, parser)
    finally:
        log.removeHandler(handler)
        log.setLevel(level)


def run(args, parser):

    if args.example:
        print(json.dumps(EXAMPLE, indent=2))
        return 0
    if not args.inputs:
        parser.error("give an inputs file, or --example")
    try:
        with open(args.inputs, encoding="utf-8") as handle:
            raw = json.load(handle)
    except (OSError, ValueError) as error:      # no such file, or not valid JSON
        log.error("Cannot read %s: %s", args.inputs, error)
        return 2
    log.info("read %s", args.inputs)
    try:
        result = analyse(raw)
    except InputError as error:
        log.error("Inputs rejected:\n- %s", "\n- ".join(error.problems))
        return 2
    print(json.dumps(result, indent=2) if args.json else report(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
