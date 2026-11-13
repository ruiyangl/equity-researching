"""Helpers and tolerances shared by the tests of dcf.py."""

import logging

# The tests' log. Nothing shows unless asked for (see conftest.py):
#   DEBUG    what goes in: inputs files, commands, amounts derived from a filing
#   INFO     each result against its published figure
#   WARNING  a result that passes with less than a fifth of its tolerance left
#   ERROR    a result outside its tolerance (the assert after it fails)
log = logging.getLogger("dcf_tests")

# The share of a tolerance a result may use before it is logged as a warning.
NEAR_THE_EDGE = 0.8

# The book prints two decimals, so a result matches a printed figure when it is
# within half a cent of it (plus a hair for floating-point arithmetic).
BOOK = 0.00501

# The authors' spreadsheet figures are matched to five decimal places.
SHEET = 0.000005

# Two numbers that should be equal, up to floating-point rounding.
CLOSE = 0.0000001

# Relative: a published spreadsheet's cached value, matched to full precision.
# The same arithmetic in a different order differs only in the last digits.
EXACT = 1e-12


def log_comparison(label, value, expected, allowed, should_match=True):
    """Log a result against its published figure, at a level that says how
    close it is. allowed is the tolerance, as an absolute amount. With
    should_match=False the result is meant to miss (a wrong convention), and
    missing is the normal case."""
    off = value - expected
    text = f"{label}: {value:,.4f} against {expected:,.4f}, off {off:+,.4f} (allowed {allowed:,.4f})"
    if not should_match:
        level = logging.INFO if abs(off) > allowed else logging.ERROR
        text += ", meant to miss"
    elif abs(off) > allowed:
        level = logging.ERROR
    elif abs(off) > NEAR_THE_EDGE * allowed:
        level = logging.WARNING
    else:
        level = logging.INFO
    log.log(level, text)


def growth_after(growth):
    """The book's continuing value method for a bank's perpetuity growth rate."""
    if growth > 0:
        return {"continuing_value_method": "perpetuity_with_inflation", "inflation": growth}
    if growth < 0:
        return {"continuing_value_method": "perpetuity_with_decline", "decline_rate": -growth}
    return {"continuing_value_method": "perpetuity"}


def changed(base, **changes):
    """A copy of some inputs with a few of them changed. None removes a key."""
    inputs = dict(base)
    for key, value in changes.items():
        if value is None:
            inputs.pop(key, None)
        else:
            inputs[key] = value
    return inputs
