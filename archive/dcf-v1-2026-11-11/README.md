# Archived: first DCF script

Archived on 2026-11-12 at the user's request ("far too complex for what I need"). Kept for reference only; nothing uses it.

- `dcf.py` (3,350 lines) and `test_dcf.py` (1,767 lines, 106 tests), written 2026-11-11: a general DCF engine with four cash-flow modes, a CAPM/WACC hurdle-rate grid, mid-year discounting, several reverse-DCF framings and warning flags.
- Replaced by `skills/equity-researching/scripts/dcf.py`, which implements only the DCF and reverse DCF from *Expectations Investing* (Rappaport and Mauboussin).
- The skill's documents never referenced this script.

To run its tests from this folder: `python3 -m unittest test_dcf`
