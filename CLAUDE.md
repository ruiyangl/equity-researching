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
      util.py                       shared tolerances (BOOK, SHEET, CLOSE) and changed()
      figures.py                    the published numbers the tests compare against
archive/dcf-v1-2026-11-11/          superseded DCF engine, kept for reference only
```

When `SKILL.md` and a reference disagree, the reference owns its domain, as `SKILL.md` states.

The documents cite each other by section number (for example "valuation-framework 1.9", "valuation-framework Module 4", "memo-standard section 9"). If you renumber or move a section, grep for its old number and update every reference to it.

The `description` in `plugin.json` is the `SKILL.md` frontmatter description cut off at 500 characters. If you change the frontmatter description, update `plugin.json` to match.

## The DCF script

`scripts/dcf.py` implements the DCF and reverse DCF of *Expectations Investing* (Rappaport and Mauboussin, revised edition). It uses the Python standard library only.

- The comment at the top of `dcf.py` explains the method and every input.
- Example inputs: `python3 dcf.py --example`
- Report: `python3 dcf.py inputs.json` (add `--json` for machine-readable output)
- Tests use pytest, from `skills/equity-researching/scripts/`: `python3 -B -m pytest tests`
- One file: `python3 -B -m pytest tests/test_reverse_dcf.py` (files: `test_book_table_2_1`, `test_continuing_value`, `test_authors_spreadsheet`, `test_reverse_dcf`, `test_inputs`, `test_command_line`); by name: `-k reverse`
- Where pytest is not installed (many system Pythons refuse pip installs), run it through uv: `uv run --no-project --with pytest python -B -m pytest tests`
- A new test goes in the file for its group; numbers from the book or the spreadsheet go in `tests/figures.py`.

The tests reproduce three sources exactly:
- the book's chapter 2 Summary Illustration (table 2.1);
- the four continuing value examples in the chapter 2 appendix;
- the authors' Domino's Pizza spreadsheet (Online Tutorial 8 on expectationsinvesting.com).

Every change must keep them passing.

Rules for the script:
- **Keep it small and faithful to the book.** A larger general-purpose engine was rejected as too complex; it is the one in `archive/`. Do not add modes, options or diagnostics nobody asked for, and do not build on the archived code.
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
