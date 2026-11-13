"""The continuing value examples in the chapter 2 appendix: NOPAT of $1.00
and an 8% cost of capital."""

import pytest

import dcf
from figures import ILLUSTRATION
from util import BOOK, CLOSE, changed


def value(method, **extra):
    growth = dcf.growth_after_forecast_period(dict(extra, continuing_value_method=method))
    return dcf.continuing_value(1.00, 0.08, growth)


def test_perpetuity_is_12_50():
    # 1.00 / 0.08
    assert value("perpetuity") == pytest.approx(12.50, abs=CLOSE)


def test_perpetuity_with_inflation_is_17_00():
    # 1.02 / (0.08 - 0.02)
    assert value("perpetuity_with_inflation", inflation=0.02) == pytest.approx(17.00, abs=CLOSE)


def test_perpetuity_with_partial_inflation_is_14_43():
    # Half of 2% inflation recouped: 1.01 / (0.08 - 0.01)
    result = value("perpetuity_with_partial_inflation", inflation=0.02, inflation_recouped=0.5)
    assert result == pytest.approx(14.43, abs=BOOK)


def test_perpetuity_with_decline_is_9_80():
    # 0.98 / (0.08 + 0.02)
    assert value("perpetuity_with_decline", decline_rate=0.02) == pytest.approx(9.80, abs=CLOSE)


def test_the_method_changes_the_dcf_value():
    # More continuing value means a higher DCF value, in the appendix's order.
    values = [
        dcf.analyse(changed(ILLUSTRATION, continuing_value_method=method, **extra))["dcf"]["value_per_share"]
        for method, extra in [
            ("perpetuity_with_decline", {"decline_rate": 0.02}),
            ("perpetuity", {}),
            ("perpetuity_with_partial_inflation", {"inflation_recouped": 0.5}),
            ("perpetuity_with_inflation", {}),
        ]
    ]
    assert values == sorted(values)
    assert len(set(values)) == 4
