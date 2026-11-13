"""pytest setup for the tests of dcf.py. pytest reads this file first.

The tests check dcf.py against numbers published by its source. Each file
holds one group:

    test_book_table_2_1.py       the Summary Illustration in chapter 2 (table 2.1)
    test_continuing_value.py     the four worked examples in the chapter 2 appendix
    test_authors_spreadsheet.py  the authors' Domino's Pizza spreadsheet
                                 (expectationsinvesting.com, Online Tutorial 8)
    test_reverse_dcf.py          the answers the reverse DCF can give
    test_inputs.py               lists, named parts, and rejected inputs
    test_command_line.py         running the program as a user would

figures.py holds the published numbers; util.py holds the helpers and
tolerances the tests share.

HOW TO RUN (from the scripts folder, the one holding dcf.py)
    python3 -B -m pytest tests                          every test
    python3 -B -m pytest tests/test_inputs.py           one file
    python3 -B -m pytest tests -k reverse               tests whose name has "reverse"
Where pytest is not installed, put "uv run --no-project --with pytest" in
front of each command, with "python" in place of "python3".
"""

import os
import sys

# dcf.py sits in the folder above this one.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
