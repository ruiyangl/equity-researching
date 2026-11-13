"""pytest setup for the tests of dcf.py. pytest reads this file first.

The tests check dcf.py against numbers published by its source. Each file
holds one group:

    test_book_table_2_1.py       the Summary Illustration in chapter 2 (table 2.1)
    test_continuing_value.py     the four worked examples in the chapter 2 appendix
    test_authors_spreadsheet.py  the authors' own spreadsheets: Domino's Pizza
                                 (Online Tutorial 8) and Gateway (first edition)
    test_reverse_dcf.py          the answers the reverse DCF can give
    test_inputs.py               lists, named parts, and rejected inputs
    test_command_line.py         running the program as a user would
    test_published_models.py     DCF models published online (Wall Street Prep,
                                 Edward Bodmer), year-end and both mid-year options,
                                 matched to full precision
    test_real_companies.py       end to end: real companies' projections in, the
                                 values their banks published (SEC merger filings) out
    test_real_companies_mid_year.py  the same with mid-year discounting, which most
                                 banks use (the book discounts at year end)

figures.py holds the published numbers; util.py holds the helpers and
tolerances the tests share; the run and save fixtures below run dcf.py from
the command line.

HOW TO RUN (from the scripts folder, the one holding dcf.py)
    python3 -B -m pytest tests                          every test
    python3 -B -m pytest tests/test_inputs.py           one file
    python3 -B -m pytest tests -k reverse               tests whose name has "reverse"
Where pytest is not installed, put "uv run --no-project --with pytest" in
front of each command, with "python" in place of "python3".

LOGGING (levels in util.py)
    --log-cli-level=INFO       each result against its published figure, live
    --log-cli-level=DEBUG      the inputs and commands too
    --log-cli-level=WARNING    only results close to, or outside, their tolerance
    --log-level=DEBUG          everything, but shown only for tests that fail
Without these, a failing test shows its warnings and errors. dcf.py's own log
(logger "dcf": its rows at DEBUG, its answers at INFO) shows the same way.
"""

import json
import os
import sys

import pytest

# dcf.py sits in the folder above this one.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import dcf  # noqa: E402  (needs the line above)
from util import log  # noqa: E402


@pytest.fixture
def run(capsys):
    """Run dcf.py with some arguments; give back its exit code, output and errors."""
    def run_program(*arguments):
        log.debug("dcf.py %s", " ".join(arguments))
        code = dcf.main(list(arguments))
        out, err = capsys.readouterr()
        log.debug("exit code %s%s", code, f"; errors: {err.strip()}" if err else "")
        return code, out, err
    return run_program


@pytest.fixture
def save(tmp_path):
    """Write some inputs to a JSON file; give back its path."""
    def save_inputs(inputs):
        path = tmp_path / f"inputs-{len(list(tmp_path.iterdir()))}.json"
        path.write_text(json.dumps(inputs), encoding="utf-8")
        log.debug("%s: %s", path.name, json.dumps(inputs))
        return str(path)
    return save_inputs
