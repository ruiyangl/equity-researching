# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

A single agent skill, `equity-researching`, packaged as a plugin. An agent loads it to write buy-side equity research: single-ticker memos, peer comparisons, and portfolio or watchlist updates.

The Markdown files are **instructions the agent follows**, not documentation. Editing them changes how reports are written and how stocks are valued. The local checkout may also be the live copy an agent loads, so a change takes effect on its next run.

## Layout

```
.claude-plugin/plugin.json          plugin manifest (name, description)
skills/equity-researching/
  SKILL.md                          entry point: workflow, report modes, reading order
  references/
    fundamental-playbook.md         research process, sources, scoring
    memo-standard.md                report templates, completeness contract, pre-emit checklist
    valuation-framework.md          Value Lock (price-blind) and the market read (reverse DCF)
    entry-exit-framework.md         buy and sell levels, sizing, tranches, exit rules
  scripts/
    dcf.py                          DCF and reverse DCF from "Expectations Investing"
    tests/                          pytest tests against the book's own numbers, one file per group
      conftest.py                   pytest setup: makes dcf importable; lists the groups
      util.py                       shared tolerances, helpers, and the tests' log
      figures.py                    the published numbers the tests compare against
archive/dcf-v1-2026-11-11/          superseded DCF engine, kept for reference only
```

When `SKILL.md` and a reference disagree, the reference owns its domain, as `SKILL.md` states.

The documents cite each other by section number (for example "valuation-framework 1.9", "valuation-framework Module 4", "memo-standard section 9"). If you renumber or move a section, grep for its old number and update every reference to it.

The `description` in `plugin.json` is the `SKILL.md` frontmatter description cut off at 500 characters. If you change the frontmatter description, update `plugin.json` to match.

## The DCF script

`scripts/dcf.py` implements the DCF and reverse DCF of *Expectations Investing* (Rappaport and Mauboussin, revised edition). It uses the Python standard library only.

- The comment at the top of `dcf.py` explains the method and every input.
- **The forecast is in amounts.** Each of the five lines (sales, operating profit, cash taxes, fixed- and working-capital investment) takes yearly amounts, a rate (the book's value driver), or both. `projection()` builds the amounts: a given amount wins for its year; any other year comes from the line's rate by the book's arithmetic. `build_rows()`, the valuation, reads only the amounts. Pass a source's projections as amounts; never convert them into rates (the old `projection_inputs` did, and was removed). A line with amounts and no rate ends the table at its last amount.
- Example inputs: `python3 dcf.py --example`
- Report: `python3 dcf.py inputs.json` (add `--json` for machine-readable output)
- Logging, on stderr: `--log-level DEBUG|INFO|WARNING|ERROR` (default WARNING). DEBUG logs every row, INFO the answers, WARNING a negative value per share or no market-implied forecast period, ERROR an unreadable or rejected inputs file. stdout carries only the report or JSON. Logger name `dcf`, so tests see it through pytest's `--log-cli-level`.
- Tests use pytest, from `skills/equity-researching/scripts/`: `python3 -B -m pytest tests`
- One file: `python3 -B -m pytest tests/test_reverse_dcf.py` (files: `test_book_table_2_1`, `test_continuing_value`, `test_authors_spreadsheet`, `test_reverse_dcf`, `test_inputs`, `test_command_line`, `test_published_models`, `test_real_companies`, `test_real_companies_mid_year`); by name: `-k reverse`
- Where pytest is not installed (many system Pythons refuse pip installs), run it through uv: `uv run --no-project --with pytest python -B -m pytest tests`
- A new test goes in the file for its group; numbers from the book or the spreadsheet go in `tests/figures.py`.
- Test logging (levels in `tests/util.py`): `--log-cli-level=INFO` shows each result against its published figure, `DEBUG` adds the inputs and commands, `WARNING` shows only results close to or outside their tolerance. Use `log` / `log_comparison` from `util.py` rather than `print`, which the tests' output capture swallows or mixes into the program's JSON.

The tests reproduce these sources exactly:
- the book's chapter 2 Summary Illustration (table 2.1);
- the four continuing value examples in the chapter 2 appendix;
- the authors' Domino's Pizza spreadsheet (Online Tutorial 8 on expectationsinvesting.com);
- the authors' first-edition Gateway spreadsheet (every cell, and its market-implied forecast period of 7 years);
- three DCF models published online, to full precision (`test_published_models`): Wall Street Prep's Quick Lesson (year end, with a share count), Wall Street Prep's Terminal Growth Rate template (`mid_year`) and Edward Bodmer's Proof of Timing (`year_end` and `mid_year_including_continuing_value`).

The spreadsheet cases compare against cached cell values with a relative tolerance of 1e-12 (`EXACT` in `util.py`). Only the numbers are copied into `figures.py`, with their URLs; the files themselves are not committed.

`test_real_companies` runs end to end on real companies. Management's projections from two SEC merger filings (NIC 2021, Pre-Paid Legal 2011) go in as amounts through the command line, and the values per share their banks published come out. Both banks discount at year end from a fiscal year end, as the book does. Their continuing value starts from free cash flow where the book's starts from NOPAT, so the tests take that difference off before comparing exactly, and separately check that the book's own value is within 1% of the bank's. Filings with stub periods or exit-multiple terminal values cannot be reproduced and were left out.

**Mid-year discounting** is the one option not from the book, added at the owner's request because most banks use it. The `discounting` input is `year_end` (the book, the default), `mid_year` (free cash flow at mid-year, continuing value at year end) or `mid_year_including_continuing_value`. Every test except `test_real_companies_mid_year` uses the default. That file checks `mid_year_including_continuing_value` end to end on Cornerstone Building Brands 2022: Centerview's own debt, cash and its one printed share count (133.7) for all nine prices of its grid. Eight are within their $0.25 rounding; all nine are within that plus the most the inputs' $1mm rounding can move a price ($0.071, worked out in `figures.py`). $20.50 ($0.154 out) is a strict xfail of the $0.25-only check. The other conventions miss every price by more than both. `mid_year` is checked exactly by Wall Street Prep's template in `test_published_models`.

**The share count is an input, never calculated.** `shares_outstanding` is one number taken from a filing: the diluted weighted average shares from the latest 10-Q or 10-K (the company has already counted its options there), or in a loss year the cover-page count plus restricted stock units. The owner decided against a share calculation module (treasury stock method) in `dcf.py` or the tests. Options must not also go into `debt`, or they count twice.

**Share counts are never fitted in a test.** Every count comes from the source and is entered as a number: disclosed (NIC, Pre-Paid Legal, Quick Lesson, Gateway) or, for Cornerstone, the board book's printed 133.7 for every price. Tests do no share arithmetic. Sources that stop at enterprise value (Wall Street Prep's Terminal Growth Rate, Bodmer) are compared at enterprise value. Ultratech 2017 was dropped: BofA did not disclose its count and a single count from one end of its range misses the other end by more than the rounding.

Every change must keep them passing.

Rules for the script:
- **Keep it small and faithful to the book.** A larger general-purpose engine was rejected as too complex; it is the one in `archive/`. Do not add modes, options or diagnostics nobody asked for, and do not build on the archived code. The `discounting` option is the one exception, asked for by the owner; the default stays the book's.
- New behaviour follows the book's formulas and gets a test taken from a worked example in the book or the authors' tutorials.

**Status:** the skill's documents do not reference `dcf.py` yet. Wiring it into the workflow (gathering its inputs, and using it for the Value Lock and/or the reverse DCF) is an open decision for the owner. Do not make that change without asking.

## Rules for the skill's method

- **Value is worked out without the share price.** The Value Lock and the buy and sell levels must not move when the quote moves, and should stay roughly constant from one earnings period to the next. The price is only ever compared against the value; the reverse DCF is the one place that starts from it.
- **Levels must be reachable.** Values are central estimates; do not stack conservatism until the levels never trigger.
- **Explain gaps to the Street.** Where the value differs from consensus targets, the report says why.
- **Test method changes on real data, point in time.** Walk forward on a real ticker at several past earnings dates, using only what was known at each date. Synthetic cases are not enough.

## Working here

- This repository is **public**. Do not commit portfolio holdings, account details, credentials, reports about the owner's positions, or local paths.
- Commit and push only when asked.
- Python cache files are ignored (`.gitignore`); run scripts with `python3 -B` to avoid creating them.
