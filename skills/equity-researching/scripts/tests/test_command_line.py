"""Running the program the way a user does. The run and save fixtures are in
conftest.py."""

import json

import pytest

from figures import ILLUSTRATION
from util import BOOK, changed


def test_the_example_runs_and_gives_the_spreadsheets_answer(run, save):
    code, example, _ = run("--example")
    assert code == 0
    code, text, _ = run(save(json.loads(example)))
    assert code == 0
    assert "**Market-implied forecast period: 8 years** at a share price of 418.00" in text
    assert "**DCF value per share: 458.29** with a 10-year forecast period" in text
    assert "Value per share is 417.71 with 8 and 437.84 with 9." in text


def test_the_report_shows_the_books_illustration(run, save):
    code, text, _ = run(save(ILLUSTRATION))
    assert code == 0
    assert "**DCF value per share: 257.07** with a 5-year forecast period" in text
    assert "| 5 | 47.44 | 209.63 | 257.07 | 257.07 | 257.07 | your forecast period |" in text


@pytest.mark.parametrize("line", [
    "| 1 | 110.00 | 16.50 | 4.13 | 12.38 | 1.50 | 1.00 | 9.88 | 9.14 |",
    "| 2 | 121.00 | 18.15 | 4.54 | 13.61 | 1.65 | 1.10 | 10.86 | 9.31 |",
    "| 3 | 133.10 | 19.97 | 4.99 | 14.97 | 1.82 | 1.21 | 11.95 | 9.49 |",
    "| 4 | 146.41 | 21.96 | 5.49 | 16.47 | 2.00 | 1.33 | 13.14 | 9.66 |",
    "| 5 | 161.05 | 24.16 | 6.04 | 18.12 | 2.20 | 1.46 | 14.46 | 9.84 |",
])
def test_the_report_prints_table_2_1_to_the_cent(run, save, line):
    # Sales, operating profit, cash taxes, NOPAT, fixed-capital investment,
    # working-capital investment, free cash flow and its present value,
    # exactly as printed in the book. Halves round up: 4.125 prints as 4.13.
    _, text, _ = run(save(ILLUSTRATION))
    assert line in text


def test_json_output_holds_the_same_numbers(run, save):
    code, text, _ = run(save(ILLUSTRATION), "--json")
    assert code == 0
    result = json.loads(text)
    assert result["dcf"]["value_per_share"] == pytest.approx(257.07, abs=BOOK)
    assert len(result["rows"]) == 25


def test_rejected_inputs_exit_with_code_2_and_say_why(run, save):
    code, out, err = run(save(changed(ILLUSTRATION, cost_of_capital=8)))
    assert (code, out) == (2, "")
    assert "Inputs rejected:" in err
    assert "'cost_of_capital' is 8" in err


def test_a_missing_file_exits_with_code_2(run):
    code, _, err = run("no-such-file.json")
    assert code == 2
    assert "Cannot read no-such-file.json" in err


# --- Logging, on stderr -------------------------------------------------------

def test_by_default_a_normal_run_logs_nothing(run, save):
    code, _, err = run(save(ILLUSTRATION))
    assert (code, err) == (0, "")


def test_info_logs_the_answers(run, save):
    code, _, err = run(save(dict(ILLUSTRATION, share_price=250)), "--log-level", "INFO")
    assert code == 0
    assert "INFO: DCF value per share 257.0" in err
    assert "INFO: market-implied forecast period: 4 years at a share price of 250" in err


def test_debug_logs_every_row(run, save):
    code, _, err = run(save(ILLUSTRATION), "--log-level", "DEBUG")
    assert code == 0
    assert sum(line.startswith("DEBUG: year ") for line in err.splitlines()) == 25


def test_the_log_never_mixes_into_the_json(run, save):
    code, out, err = run(save(ILLUSTRATION), "--json", "--log-level", "DEBUG")
    assert code == 0 and err
    assert json.loads(out)["dcf"]["value_per_share"] == pytest.approx(257.07, abs=BOOK)


def test_a_warning_when_no_forecast_period_reaches_the_price(run, save):
    code, _, err = run(save(dict(ILLUSTRATION, share_price=100000)))
    assert code == 0
    assert "WARNING: no market-implied forecast period at a share price of 100000" in err


def test_a_warning_when_value_per_share_is_negative(run, save):
    code, _, err = run(save(dict(ILLUSTRATION, debt=1000)))
    assert code == 0
    assert "WARNING: value per share is negative" in err


def test_errors_are_logged_even_at_the_quietest_level(run):
    code, _, err = run("no-such-file.json", "--log-level", "ERROR")
    assert code == 2
    assert "ERROR: Cannot read no-such-file.json" in err
