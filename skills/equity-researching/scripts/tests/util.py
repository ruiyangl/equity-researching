"""Helpers and tolerances shared by the tests of dcf.py."""

# The book prints two decimals, so a result matches a printed figure when it is
# within half a cent of it (plus a hair for floating-point arithmetic).
BOOK = 0.00501

# The authors' spreadsheet figures are matched to five decimal places.
SHEET = 0.000005

# Two numbers that should be equal, up to floating-point rounding.
CLOSE = 0.0000001


def changed(base, **changes):
    """A copy of some inputs with a few of them changed. None removes a key."""
    inputs = dict(base)
    for key, value in changes.items():
        if value is None:
            inputs.pop(key, None)
        else:
            inputs[key] = value
    return inputs
