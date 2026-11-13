# CLAUDE.md

Guidance for Claude Code when working in this repository.

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
    test_dcf.py                     tests against the book's own numbers
archive/dcf-v1-2026-11-11/          superseded DCF engine, kept for reference only
```

When `SKILL.md` and a reference disagree, the reference owns its domain, as `SKILL.md` states.

## The DCF script

`scripts/dcf.py` implements the DCF and reverse DCF of *Expectations Investing* (Rappaport and Mauboussin, revised edition). It uses the Python standard library only.

- The comment at the top of `dcf.py` explains the method and every input.
- Example inputs: `python3 dcf.py --example`
- Report: `python3 dcf.py inputs.json` (add `--json` for machine-readable output)
- Tests, from `skills/equity-researching/scripts/`: `python3 -m unittest -v test_dcf`

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
