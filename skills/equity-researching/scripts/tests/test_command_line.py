"""Running the program the way a user does."""

import json

import pytest

import dcf
from figures import ILLUSTRATION
from util import BOOK, changed


@pytest.fixture
def run(capsys):
    """Run dcf.py with some arguments; give back its exit code, output and errors."""
    def run_program(*arguments):
        code = dcf.main(list(arguments))
        out, err = capsys.readouterr()
        return code, out, err
    return run_program


@pytest.fixture
def save(tmp_path):
    """Write some inputs to a JSON file; give back its path."""
    def save_inputs(inputs):
        path = tmp_path / f"inputs-{len(list(tmp_path.iterdir()))}.json"
        path.write_text(json.dumps(inputs), encoding="utf-8")
        return str(path)
    return save_inputs


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
