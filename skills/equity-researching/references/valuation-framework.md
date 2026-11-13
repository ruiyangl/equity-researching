# Valuation Framework

Read this for **every full report** — the Entry & Exit Plan is cut from the Value Lock this file produces — and whenever the request is about valuation, fair value, upside/downside, price targets, scenario analysis, **or what the current price implies ("what's priced in", implied expectations, "is this priced for perfection", reverse DCF)**.

## The rules this file is built around

**Value is worked out without the price. The price is only ever compared against it.**

The valuation exists to fix, in advance, the prices at which to act. That works only if the value stays put while the price moves — and only if the value is one a real price can reach. Three consequences run through everything below.

1. **A one-way firewall.** Part A builds the value from facts about the business and never touches the share price or anything computed from it. Part B reads the market against that value. Nothing flows back.
2. **Value the normal year, not the next one.** Most of a business's value sits in what it earns in a normal year several years out. Next year's estimates are a bridge to that year, and forecast growth beyond the market's own rate gets half credit until it has been delivered. This is what keeps long-term levels steady from one earnings report to the next.
3. **Caution is applied once.** The values in the lock are *central* estimates — what the evidence most likely implies, at a fair required return. The margin of safety is applied openly, in one place: the plan's buy and sell levels. Caution stacked in the discount rate, the base case, the bear case and the entry rule all at once produces levels that no real price ever reaches, and a plan that cannot be executed is as useless as one that moves.

| | Part A — Intrinsic value | Part B — Market read |
|---|---|---|
| Modules | 1 Normal-year scenario DCF · 2 Sector adaptation | 3 Relative valuation and Street reconciliation · 4 Reverse DCF / implied expectations |
| Uses the share price? | **Never** | Yes — that is its job |
| Output | The **Value Lock**: required return, bear / base / bull values, weights, fair value | Multiples, the gap to consensus targets explained, market-implied expectations, valuation labels |
| Feeds | The Entry & Exit Plan's levels and sizes | The verdict narrative and the plan's status line |
| Changes when | The company reports, or its estimates move materially (1.9) | The price moves |

Do Part A first and finish it before starting Part B.

## Contents

Part A — Intrinsic value (price-blind)
- Module 1. Normal-year scenario DCF → the Value Lock
  1.1 Admissible inputs · 1.2 Order of work · 1.3 Visibility class · 1.4 Required return · 1.5 Conventions · 1.6 The three scenarios · 1.7 Weights · 1.8 The Value Lock block · 1.9 When the lock changes · 1.10 Price-invariance test · 1.11 Worked example
- Module 2. Sector adaptation

Part B — Market read (price-dependent)
- Module 3. Relative valuation and Street reconciliation
- Module 4. Reverse DCF / Implied Expectations
- Conclusion labels
- Margin-of-safety discipline

---

## Part A — Intrinsic value (price-blind)

### Module 1. Normal-year scenario DCF → the Value Lock

Runs for every ticker in every full report. It produces three per-share values — bear, base, bull — at a required return, with weights, from facts about the business alone.

#### 1.1 Admissible inputs

Every number that enters Module 1 comes from the left column. The right column is banned from Part A in any form, including as a "cross-check" that then nudges an assumption.

| Admissible — facts about the business | Inadmissible — facts about the stock |
|---|---|
| Reported financials and segment data | The share price, market cap or enterprise value — today's, recent or historical |
| Guidance, published long-term model, backlog / RPO, contracted capacity | Any trading multiple of the subject (P/E, EV/EBITDA, P/S, FCF yield, PEG), spot, forward or its own historical range |
| Consensus **operating** estimates (revenue, margins, EPS, FCF) | Peers' trading multiples, spot or forward |
| Independent multi-year forecasts of the competed market; market shares; pricing and cycle data | Consensus **price targets**, ratings, "upside to target" |
| Customers' budgets: their revenue, cash flow and spending intensity | Price history: returns, 52-week range, drawdown, momentum, any technical indicator |
| The company's and peers' **operating** record: growth, margins, returns, cash conversion, peak-to-trough episodes | Options-implied moves or volatility, short interest, fund flows |
| Balance sheet, debt and convertible terms, share counts as filed, announced issuance | Beta or any return-based risk measure as the source of the required return |
| Base rates for growth persistence and margin mean-reversion; tax, capex plans, regulatory and contractual facts | Any Module 3 or Module 4 output, and how the stock reacted to an event |

Consensus operating estimates are admissible because they forecast the business. Price targets are not: they forecast the stock, and they track the quote.

#### 1.2 Order of work

Build Module 1 from the playbook's Pass A data (facts about the business) and write the Value Lock **before** the quote, the market cap or any multiple is used for anything. The quote has usually been glimpsed by then — it sits beside the financials on most data pages. That is why the rule is structural rather than a matter of willpower: every input cites an admissible source, every value is arithmetic on those inputs, the rate, the spread and the weights come from rubrics, a lock is carried rather than rebuilt between reports (1.9), and the invariance test (1.10) is run before leaving Part A.

#### 1.3 Visibility class

Decide once, from the cash-flow record — never from where the stock trades.

- **Standard** — owner earnings positive in at least 3 of the last 5 fiscal years (or in each of the last 2 for a company with a shorter record), and guidance or consensus operating estimates exist for the next 2 years.
- **Low-visibility** — anything else: pre-profit, a turnaround with negative trailing and next-year earnings, under 2 years of relevant operating history, or data confidence Low. The method is the same; the values are tagged `[low-visibility]`, the widest spread is used (1.6), and the Entry & Exit Plan sets its buy levels deeper and haircuts its sizing bear.

A DCF on an unpredictable business launders guesswork into false precision; the tag is how the memo stays honest about that without retreating to a price-based method. There is no multiples-based fallback: a "fair-value range" built from trading multiples is a restatement of the market's price, not a value.

#### 1.4 Required return r\*

r\* is a fair return for owning this kind of business — roughly what the wider market offers for comparable risk. It is set by what the business is, so it does not float with the stock's beta or the tape. It is deliberately not a punitive hurdle: business risk is carried by the three scenarios, and caution by the plan's buy levels. Asking the rate to carry them a second time is how values end up far below anything the market will ever offer.

Count the risk flags, each decided from filings:

| Flag | Raised when |
|---|---|
| Earnings durability | Owner earnings negative over the last twelve months, or positive in fewer than 3 of the last 5 fiscal years |
| Deep cyclicality | Within the last 10 years, annual revenue fell more than 20% peak-to-trough or operating margin fell more than 10 points |
| Concentration | Top customer ≥ 25% of revenue, top three ≥ 50%, or one product line or end market ≥ 70% |
| Balance sheet | Net debt / EBITDA above 3×, interest coverage below 4×, or the plan needs external capital within 24 months (use the sector's own solvency tests where EBITDA leverage is not meaningful) |
| Scale | Annual revenue under $1B |

| Flags raised | r\* | r_hi |
|---|---|---|
| 0 | 8% | 10% |
| 1 | 9% | 11% |
| 2 | 10% | 12% |
| 3–4 | 12% | 14% |
| 5, or earnings durability and balance sheet together | 14% | 16% |

A user control line `hurdle: r*=—%` overrides the rubric — the required return is the investor's to set — and is echoed in the lock. It is the single most powerful setting in the method: one point of required return moves every value by roughly 12–15%.

**r_hi = r\* + 2 points** is the stress rate. Every value is reported at both; the plan sizes on the bear value at r_hi, prints its sensitivity line there, and uses the pair to state the expected return at each level.

**CAPM is a cross-check, not the source.** Print `rf + beta × ~4.5–5% ERP` beside r\* and say what beta implies. If it lands a full step or more above r\*, say so in one line; r\* stands, and r_hi already prices that step. Beta is a statistic of the price path — letting it set r\* would move every level whenever the stock has a volatile month.

r\* changes only when a flag changes on reported evidence.

#### 1.5 Conventions

1. **Owner earnings, not reported EPS.** Cash stream = EPS (or NOPAT per share) × an explicit **FCF-conversion** factor, with stock-based compensation treated as a real cost: conversion = (FCF − SBC) ÷ net income. Bridge years use the company's own trailing three-year average (show the arithmetic). The normal year uses the maturity level for its asset intensity: 50–65% for a business still in a heavy build, 70–85% mature, 90–100% asset-light. Straight-line between the two. State every factor.
2. **Share count from filings, not from the quote.** Latest reported diluted count plus announced or contracted issuance, held flat. Buybacks are not modelled: cash returned at fair value is value-neutral, and assuming repurchases at today's quote would make per-share value a function of the price. Convertibles count as shares when the conversion price is below the base value and as debt otherwise. Equity needed to fund a scenario's path is issued at that scenario's own per-share value (one iteration is enough).
3. **Operating value plus net cash.** PV the owner-earnings stream, then add net cash per share (subtract net debt). Count marketable equity stakes at carrying value and say so.
4. **Terminal honesty.** Gordon growth at g = 2.5% in all three scenarios (2–3% with a stated reason; lower for a business in structural decline). State the terminal multiple this implies as a sanity read. A market multiple — the subject's or its peers', spot or forward — is never a terminal input: it imports today's prices into the value.
5. **Horizon and timing.** Year 1 is the fiscal year in progress on the valuation date; `f` is the fraction of it already elapsed. Year 5 is the normal year. Years 6–10 fade to g. Discount from the valuation date and count only the unelapsed part of year 1:

   ```
   PV = Σ(k=1..10) w_k · OE_k / (1+r)^(k−f)  +  TV / (1+r)^(10−f)  +  net cash per share
        w_1 = 1 − f,  w_k = 1 for k ≥ 2;   TV = OE_10 · (1+g) / (r − g)
        OE_k = EPS_k × conversion_k for k ≤ 5;   OE_k = OE_(k−1) × (1 + g_k) for k = 6..10,
        g_k = g_a + (g − g_a) · (k − 5) / 5      (g_a = growth at the normal year; g_10 = g)
   ```

   State the fiscal calendar once and map scenario years to it — sloppy year-mapping quietly shifts a full year of discounting. With this convention a lock rolls forward smoothly through the year instead of jumping at year-end.
6. **Label authorship.** Each path is `consensus-anchored`, `guidance-anchored` or `analyst construction`.

#### 1.6 The three scenarios

Exactly three scenarios feed the lock. They share the bridge and differ in one thing: what the business earns in the normal year.

- **Bridge — years 1 and 2.** Consensus operating estimates, revenue and EPS; guidance where consensus is missing or visibly stale against newer guidance. The same bridge serves all three scenarios. Use an earnings measure that expenses stock compensation.
- **Normal year — year 5.** A base, a bear and a bull normal-year EPS, built as below. This is where most of the value sits.
- **Years 3 and 4.** Straight-line in EPS from year 2 to the normal-year EPS; conversion straight-line from the bridge level to the normal-year level.
- **Years 6–10.** Owner earnings grow at a rate that fades linearly to g (formula in 1.5), starting from `g_a` = the market's growth rate `g_n` capped at 8% in the base, g in the bear, and `g_n` in the bull.

**Base — the central case.** What the evidence most likely implies, with no caution added:

```
base normal-year revenue = ½ · [ R1 · (1 + g_n)^4  +  R2 · (1 + g_n)^3 ]
base normal-year EPS     = that revenue × normal margin × (1 − tax rate) ÷ diluted shares
```

| Input | Rule |
|---|---|
| `R1`, `R2` | bridge revenue in years 1 and 2 |
| `g_n` — growth from the bridge to the normal year | the competed market's long-run growth rate per independent multi-year forecasts (the median of those available), capped at 10%; where no independent forecast exists, the lower of the bridge's own growth rate and 6% |
| Normal margin | average operating margin of the last five fiscal years — the last three when the business has been transformed (a segment that was under half of revenue five years ago is now over three-quarters) — or the midpoint of a published long-term model. A deep cyclical that has not been transformed uses the full cycle (ten years where the record allows). One-off charges are excluded |
| Tax rate, shares | the guided or normal rate; diluted shares per 1.5. Interest on net cash is left out — net cash is added once, at the end |

The formula carries each bridge year forward to year 5 at the market's growth rate and averages the two. When the company grows in line with its market, the two halves agree and the base simply follows consensus. When consensus has the company outgrowing — or undershooting — its market in year 2, **that excess gets half credit**: forecasts of abnormal growth regress toward the mean, and half is the neutral prior until the growth is delivered. Once year 2 becomes year 1 it counts in full.

**Bear and bull — the one-in-four cases on either side.** Their distance from the base is measured from the company's own record, not judged:

```
d = the largest peak-to-trough fall in annual operating income in the ten-year record
    (one-offs excluded), bounded to 20%–60%
bear normal-year EPS = base × (1 − d)          bull normal-year EPS = base × (1 + d)
```

Use d = 60% for a low-visibility name or a record shorter than five years. A business whose profits have halved before can halve again; one whose worst year was a 15% dip earns a narrow range. Each scenario still names its mechanism — the leading item in the memo's Risks for the bear, the leading Catalyst for the bull — so the reader knows what would have to happen. The mechanism explains the scenario; the record sizes it.

Rules:

- **Central, not cautious.** The base takes consensus and the company's own recent margins as they are. Do not shade it "to be prudent" — the plan applies the margin of safety, once. Equally, do not lift it to meet a hot quarter: the half-credit rule already says how much of a forecast jump counts.
- **Cyclicals mean-revert.** For a business at a cyclical high or low the normal margin is the full-cycle average, so the base path bends back to mid-cycle economics by year 5. A scenario that carries peak-year economics into perpetuity is inadmissible.
- **Independent means independent.** `g_n` comes from forecasters with no stake in the answer. The company's own market-size claims, and those of its suppliers and bankers, are not sources for it.
- **Bound the bull.** Check it against base rates (sustained 20%+ earnings growth for a decade is achieved by a single-digit percentage of large caps; 30–45% a year is reserved for generational outliers) and against Module 4's physical-world anchors (implied share of a competitive market above 30–40%, earnings above the closest mega-peer's profit pool). If it fails, cap the bull at the bound and say so.
- **Stress case — shown, not locked.** When the bear's named mechanism can be sized on its own arithmetic — customers' spending falling back to its through-cycle share of their cash flow, the loss of a named customer — and that arithmetic lands below the bear, print it beneath the table as `[stress case — not in the lock]`. It informs the Invalidation Triggers and the plan's Rule 2 audit; it moves no level. A blue-sky case may be shown the same way.

#### 1.7 Weights

Start at **25 / 50 / 25** (bear / base / bull). Move 5 points from one tail to the other for each condition below that the memo has evidenced; net the two lists; cap the result at 35/50/15 and 15/50/35. The base weight stays 50.

Toward the bear (+5 bear, −5 bull each):
- moat trend weakening or unproven
- growth classified narrative-driven, or cyclical with current margins above the five-year average
- float dynamics a structural headwind, or the plan needs external equity within 24 months
- the balance-sheet distress lens is flagged
- data confidence Low

Toward the bull (+5 bull, −5 bear each):
- moat trend strengthening, with the evidence named
- backlog, RPO or contracted volume already covers the bridge's next four quarters
- net cash with a shrinking share count

Print the tilts applied. Nothing else moves a weight — not the market-implied probability from Module 4, not recent stock performance, not sentiment, not a sense that the default "feels wrong" at this price.

**Fair value** is the probability-weighted value: `FV = p_bear·PV_bear + p_base·PV_base + p_bull·PV_bull` at r\*. At that price the probability-weighted return on the stock equals r\* a year.

#### 1.8 The Value Lock block

Module 1's output is one block, emitted in the memo's Valuation section and reused verbatim by the Entry & Exit Plan:

> **Value Lock — TICKER — as of YYYY-MM-DD** · evidence through [latest filing or print, date]
> - Visibility: Standard / Low-visibility ([criteria met])
> - Required return: r\* = —% (flags raised: … | `hurdle:` override) · r_hi = —% · CAPM cross-check —% (context only)
> - Weights —/—/— (start 25/50/25; tilts applied: …)
> - Values at r\*: bear $— / base $— / bull $— → **fair value $—** · at r_hi: $— / $— / $— → $—
> - Change vs prior lock: [first lock] / [carried verbatim] / [recomputed — attribution below] / [recomputed, step capped — evidence fair value $—, locked $—, remainder ±—% pending]

| | Bear — [mechanism] | Base — central case | Bull — [mechanism] | Source |
|---|---|---|---|---|
| Bridge revenue and EPS, years 1–2 [fiscal years] | | | | consensus / guidance, date |
| Growth to the normal year `g_n` | | | | independent forecasts, dates |
| Base normal-year revenue = ½·[R1·(1+g_n)⁴ + R2·(1+g_n)³] | | | | arithmetic shown |
| Normal margin → base normal-year EPS | | | | margin record |
| Spread d → bear / bull normal-year EPS | | | | operating-income record |
| Conversion (bridge → normal year) | | | | cash-flow record |
| Growth after the normal year → g | | | | |
| Diluted shares · net cash per share · f | | | | filing, date |
| **Value per share at r\*** | $— | $— | $— | |
| **Value per share at r_hi** | $— | $— | $— | |
| Authorship | | | | |

The block contains no share price, no market cap, no multiple of the quote and no "% vs price" column — those belong to Part B and to the plan's Status block. The plan takes from it: the three values and the fair value at r\* and at r_hi, the weights, the visibility class, the date, and any pending remainder. Nothing from Part B.

#### 1.9 When the lock changes — and when it does not

**Between reports the lock is carried verbatim** — same date, same numbers. It is recomputed only when one of these fires:

1. The subject reports a quarter, pre-announces or changes guidance.
2. Consensus operating estimates for either bridge year have moved 10% or more from the figures in the lock.
3. The diluted share count has moved 3% or more, or net cash per share materially.
4. The business itself has changed — M&A, a divestiture, a restructuring — or an Invalidation Trigger has fired (the plan's Rule 1 then governs, and a fresh memo sets a new lock).
5. An error is found in the lock: fix it, label it `[model correction]`, name the error.

**At a trigger, recompute the whole lock** from the evidence then available — bridge, `g_n`, normal margin, d, the flags behind r\*, the weights — exactly as for a first lock. Call the result the *evidence values*. Then apply the step cap.

**Step cap — no single report moves any of the three values by more than 15%, up or down.** For each of the bear, base and bull values: if the evidence value is within 15% of the locked one it becomes the lock; if it is further away, the locked value moves exactly 15% toward it (apply the same factor to that scenario's value at r_hi). Fair value and all five levels therefore move by at most 15% in any one report. Record what is left as pending: `evidence fair value $—, locked $—, remainder ±—% pending`. The next trigger repeats the step. A change that large has to show up twice before the plan acts on all of it — the same confirmation standard the plan applies to exits. While a remainder is pending, the plan acts at half strength in the direction the stale levels would favour (entry-exit framework, section 3): no new tranche opens while the remainder is downward; an exit is taken as a trim while it is upward. A first lock has no cap.

Print the attribution whenever the lock changes:

| Lock item | Prior | New | Evidence (source, date) |
|---|---|---|---|
| Bridge year-2 revenue / EPS | | | |
| Fair value at r\* | | | follows from the rows above |

Every changed input needs a row, and the evidence column names a fact about the business.

**Never a reason to change the lock:** the share price moved, by any amount in either direction; the price reached or crossed a level; the stock gapped on a print (the print is evidence, the gap is not); a price target or rating changed; the stock looks "obviously" cheap or expensive against the lock; a new report is being written. If the price sits far outside the bear–bull range, report that as a finding in Part B. Below the bear value the plan's Rule 2 orders a search for missed *evidence* — and if the search finds none, the lock stands.

A fresh full report on a name that already has a lock follows the same rule: if no trigger has fired, the lock is carried.

#### 1.10 Price-invariance test

Before leaving Part A, and again at the pre-emit checklist: suppose the stock were quoted at half today's price, then at double, with every fact about the business unchanged. Read the Value Lock line by line — every number must survive both. A line that would move is a defect: trace it to the input that carried the price in (a multiple, a beta, a target, a scenario pitched to bracket the quote, a weight shaded by the mood of the tape) and replace it with an admissible one.

#### 1.11 Worked example (format to replicate)

> Hypothetical. Valuation date one quarter into FY1 (f = 0.25). 100M diluted shares, net cash $5.00 per share, tax 15%. Flags: deep cyclicality, concentration, balance sheet → r\* = 12%, r_hi = 14%. Bridge (consensus): revenue $3.20B / $3.60B and EPS $6.00 / $7.00 in FY1 / FY2. Independent forecasts put the market's long-run growth at 6% → `g_n` = 6%. Conversion 70% (three-year average) → 80% (mature manufacturer). g = 2.5%.
>
> Base normal-year revenue = ½ · [3.20 × 1.06⁴ + 3.60 × 1.06³] = ½ · [4.040 + 4.288] = **$4.164B**. Consensus has year 2 growing 12.5% against a 6% market; the half-credit rule counts half of that excess. Normal margin 22% (five-year average) → base normal-year EPS = 4.164B × 22% × 0.85 ÷ 100M = **$7.79**.
> Spread: operating income fell 40% peak to trough in the worst episode of the last ten years → d = 40% → bear **$4.67** [mechanism: the largest customer digests inventory], bull **$10.90** [mechanism: the new fab ramps on schedule].
>
> | | Bear | Base | Bull |
> |---|---|---|---|
> | Normal-year EPS | $4.67 | $7.79 | $10.90 |
> | Growth after the normal year | 2.5% | 6% → 2.5% | 6% → 2.5% |
> | **Value at r\* 12%** | **$43.71** | **$64.97** | **$84.72** |
> | **Value at r_hi 14%** | $37.37 | $54.01 | $69.52 |
>
> Base arithmetic: owner earnings $4.20, $4.90, $5.33, $5.77, $6.23 in years 1–5 (EPS 6.00, 7.00, 7.26, 7.52, 7.79 × conversion 70%, 70%, 73.3%, 76.7%, 80%), fading to $7.54 in year 10; discounted per 1.5 with f = 0.25, plus $5.00 net cash = $64.97.
> Weights 25/50/25 (no tilt) → **fair value = 10.93 + 32.48 + 21.18 = $64.59** at r\*; $53.73 at r_hi.
> No price appears above. A quarter later the company reports and consensus for FY2 rises 4%: the lock is recomputed and fair value rises about 3% — an ordinary step. Had the new evidence called for +24% (evidence values $54.10 / $80.40 / $104.90, fair value $79.95), the step cap would move each locked value 15% — to $50.27 / $74.72 / $97.43, fair value $74.28 — and record the remaining +7.6% as pending for the next report.

### Module 2. Sector adaptation

How Module 1's cash stream, normal year and terminal form change by sector. All of it stays price-free.

- **Banks / insurers:** residual-income form — value = book value per share × (ROE − g) / (r − g) on through-cycle ROE; the bear and bull apply the spread d to sustainable ROE. Capital adequacy and credit quality name the bear's mechanism.
- **Cyclicals:** the normal year *is* mid-cycle — full-cycle average margin on the base normal-year revenue; the bridge may sit far above or below it.
- **Suppliers of capital goods (chips, equipment, infrastructure):** the natural stress case is customers' spending falling back to what they can fund — their operating cash flow in the last completed fiscal year, grown at the lower of its own trend and 10% a year, times the average share of it they spent on this category over their last five completed years. An order book is a bridge fact; customers' budgets bound the normal year.
- **REITs:** AFFO per share as owner earnings, payout coverage as the constraint; an NAV cross-check may use private-market cap rates, never the REIT's own or its peers' trading multiples.
- **High-growth software:** FCF-transition logic — when margins have not reached steady state by year 5, push the normal year out to the first steady-state year (no later than year 10) and straight-line to it; SBC is a cost throughout.
- **Capital-intensive transitions (miners, infrastructure, AI build-out):** fund the gap inside each path — the debt, or the dilution at the scenario's own value, that it takes to finish the build.

The same lens tells Module 3 which multiples are meaningful (P/B and ROE for banks, P/FFO for REITs, EV/revenue for early software).

---

## Part B — Market read (price-dependent)

Start here only after the Value Lock is written. Everything in Part B describes how the market is pricing the business today. None of it is an input to value.

### Module 3. Relative valuation and Street reconciliation

Use when earnings, EBITDA, book value, or revenue are usable.
Core tools: P/E, forward P/E, EV/EBITDA, P/S, PEG, P/B (when sector-appropriate), FCF yield.

Compare against:
- peers
- the company's own 3-5 year history when available

A relative read answers "how is the market pricing this against its neighbours and its own past". It fills the memo's multiples table and the playbook's valuation score. It does not produce a fair value: peer multiples ride the same tape as the subject, so a value built from them moves with the price.

**Street reconciliation** — whenever consensus price targets are available, explain the gap between them and the lock instead of leaving two sets of numbers side by side. A price target is a twelve-month price forecast, usually next year's earnings times a market multiple; the lock is what the business is worth to an owner who requires r\* a year. Three lines:

1. **The target as a multiple:** mean target ÷ bridge year-2 EPS = —×; the lock's fair value ÷ the same EPS = —×.
2. **The required return the target implies:** the discount rate at which the lock's fair value would equal the mean target (re-run the fair value at lower rates, or extrapolate from the r\* / r_hi pair).
3. **What the rest of the gap is:** the credit given to forecast growth beyond the market's rate (the lock gives half), the margin assumed in the normal year, or a multiple the cash flows do not support.

Also say where the lowest and highest published targets sit against the lock's bear and bull. The lowest sell-side target is not a bear case — it is the least optimistic price forecast — and a stock trading below it is information about the targets, not about the lock. The lock is never moved toward a target.

### Module 4. Reverse DCF / Implied Expectations

The expectations-investing module (Rappaport/Mauboussin lineage). Hold the **price** fixed, solve for the assumptions required to justify it, and set those market-implied assumptions beside the locked scenarios from Module 1. The output is a set of falsifiable market expectations and a statement of the gap — a diagnostic. It consumes the Value Lock and never changes it.

**When mandatory:** the request asks what's priced in / implied expectations / whether the price is justified; the name trades at an extreme forward multiple in either direction vs. sector norms; a cyclical is at a boom/bust extreme; a turnaround or pre-profit story carries a large market cap; or a price-target debate needs adjudication. When run, its outputs populate the memo's **Valuation Justification Check** section (see memo-standard). Whether it runs changes nothing in the lock or the plan.

#### Non-negotiable discipline rules

1. **Invert, don't forecast.** Price is the input; required assumptions are the output. The forward values already exist in the lock: build no new scenario here, and never let an implied figure flow back into Module 1.
2. **Same conventions as Module 1.** Owner earnings with explicit conversion factors, SBC as a cost, the filed share count, terminal growth ≤ nominal GDP, the same fiscal-year mapping. An inversion run on different conventions cannot be compared with the lock.
3. **Operate on operating value.** Implied-value math runs on market cap adjusted for net cash/debt (add net cash per share back at the end, or subtract net debt).
4. **Discount-rate honesty grid.** Never a single rate: invert at r\*, r_hi and one step below r\*. Smuggling optimism through a low discount rate is the #1 reverse-DCF sin; the second is a too-rich terminal.
5. **Cyclicals get mid-cycle framing.** Never invert a spot boom/trough year alone; always include F3.

#### The five framings

Run **at least three**; run all five when data permits. Each answers the same question from a different angle — convergence is the signal.

**F1 — Implied perpetual owner earnings (Gordon inversion).**
`Implied sustainable EPS = OperatingValue/share × (r − g) / (conversion × (1 + g))`
Report at each grid rate. Benchmark the implied EPS against four anchors: current run-rate, forward consensus, the company's all-time peak, and the lock's base normal-year EPS. One sentence translating it ("the price pays for FY-next earnings becoming permanent, with zero real growth").

**F2 — Implied growth solve (classic reverse DCF).**
Given a base-year owner-earnings figure, solve the growth rate over 5y and 10y horizons (with the stated terminal) that makes PV = price. Judge the result against **base rates**, not vibes: sustained 20%+ EPS growth for a decade is historically rare (single-digit percentage of large caps achieve it); 30-45%/yr for a decade is reserved for generational outliers. High implied growth is not automatically "overvalued" — a long reinvestment runway at high incremental returns can grow into it — but the burden of proof scales with the implied rate.

**F3 — Implied mid-cycle earnings at through-cycle multiples** (mandatory for cyclicals).
`Implied mid-cycle EPS = OperatingValue/share ÷ M` for M ∈ {10x, 12x, 14x, 16x}.
Compare against the lock's base normal-year EPS and the current peak/trough — this states, in one row, how much structural repricing of the cycle the market believes in.

**F4 — Scenario gap table.**
Set the price beside the three locked values and the fair value from Module 1, at r\* and at r_hi, with each value's % distance from the price. This is a comparison, not a construction: the scenarios are the lock's, unchanged. If the price sits outside the whole bear–bull range, that is the finding — not a reason to add a scenario or move one.

**F5 — Market-implied probabilities.**
Solve the mixture weight between the locked bear and bull values that reproduces the current price: `P(bull) = (Price − PV_bear) / (PV_bull − PV_bear)`, at each rate, and set it beside the lock's own weights; the difference is the disagreement with the market. It is never a reason to move the lock's weights. Report degenerate cases explicitly — if the price **exceeds every scenario value**, say so plainly: the market is either using a lower discount rate or pricing non-DCF value (strategic scarcity, government backstop, real-option value, index/momentum flows). Name which explanation is most plausible rather than hiding the overflow.

#### Sanity-anchor table (mandatory)

Reduce the implied expectations to physical-world comparisons; a reader should be able to reject or accept them without a model. Include every anchor that applies:

| Anchor | Test |
|---|---|
| Company history | Implied earnings vs. all-time peak (x multiple of best year ever) |
| Peer profit pools | Implied earnings vs. the actual profits of the closest mega-peer ("requires TSMC-scale FCF") |
| Market share | Revenue implied by (implied earnings ÷ plausible margin) vs. TAM → implied share; flag if >30-40% of a competitive market |
| Balance-sheet floor | Book value / replacement cost today and on the forward path (cyclicals: trough-multiple × forward book as the moving floor) |
| Street cross-check | Module 3's Street reconciliation, carried here in one line |

The same physical-world tests bound the lock's bull scenario (1.6); there they are applied to the scenario's own path, never to the price.

#### Expectations-gap verdict (the output that matters)

Conclude the module with:
- **Market-implied expectation** in one sentence (what future the price requires).
- **Locked central case** in one sentence, with the lock's weights.
- **Gap verdict:** `Expectations too low / roughly fair / too high`, read off the plan's level map so the two can never disagree — too low at or below the Accumulate ceiling, roughly fair between the Accumulate ceiling and the Trim floor, too high at or above the Trim floor (below the Floor: `too low — evidence audit due`). The framings explain *what* the market is assuming; the levels decide *whether* that is a gap worth acting on.
- **Bull/bear asymmetry line:** downside to the locked bear value vs upside to the locked bull value at the current price, and the expected annual return at the current price (entry-exit framework, section 10).
- Map the verdict into the Attractive / Watchlist / Caution label (below), which then feeds the memo verdict as usual.

#### Falsifiability hooks

Every implied expectation must map to **≥2 observable signposts** with thresholds and dates (price prints, backlog/RPO disclosures, margin levels, customer-commitment announcements, capex responses). Wire these directly into the memo's **Invalidation Triggers** section — an implied expectation that can't be monitored is a story, not an analysis.

#### Failure modes (check before emitting)

- An implied figure used to adjust a locked scenario; a scenario added or re-pitched because the price fell outside the range; weights moved toward the market-implied probability; the lock nudged toward a consensus price target.
- Smuggled optimism in "fixed" inputs (low r, rich terminal) making implied growth look conservative.
- Reading high implied growth as automatically overvalued (runway matters) — or low implied growth as automatically cheap (melting-ice-cube businesses deserve low expectations).
- Reported EPS instead of owner earnings; ignoring SBC; ignoring the capex cycle in conversion.
- Trailing/stale diluted share count when dilution is announced or structural.
- Single-point outputs — every output appears as a grid or range.
- Inverting one spot year of a cyclical.
- Stopping at the number: the implied rate is the *start*; it must be interrogated against history, base rates, and reinvestment capacity.

#### Compact worked example (format to replicate)

> Lock (r\* 12%, built before the quote): bear $330 / base $550 / bull $770 (d = 40%), weights 25/50/25 → fair value $550; base normal-year EPS $60. Then the price: $930, net cash $18/sh → op value $912. F1 at r=12%, g=2.5%, conv 75%: implied sustained EPS = 912 × 0.095 / 0.769 ≈ **$113** (≈ FY-next consensus; almost twice the lock's base normal-year EPS). F3: at 12–14x → implied mid-cycle EPS **$65–76**. F4: the price is +182% vs bear, +69% vs base, +21% vs bull — above every locked value. F5: P(bull) = (930 − 330) / (770 − 330) = 136% → degenerate: no weighting of the locked scenarios reaches the price; the market is capitalising next year's earnings as permanent. Street: mean target $1,050 = 9.3× FY-next EPS against the lock's 4.9×; the target needs a required return near 8% and full credit for next year's jump. Gap verdict: above the Exit floor ($770) → expectations **too high** → **Caution**; bear −65% / bull −17% from here. The lock is unchanged by any of this.

---

## Conclusion labels

The valuation work concludes with one of **Attractive / Watchlist / Caution**, and the memo's Valuation section with **Cheap / Fair / Expensive**. Both are *status*: they compare today's price with the lock, so they change when the price does — and they are read off the plan's level map rather than judged afresh.

| Price sits | Zone | Label | Verdict |
|---|---|---|---|
| below the Floor | Floor-break | Attractive — evidence audit due | Cheap — audit due |
| Floor to Accumulate ceiling | Accumulate | Attractive | Cheap |
| Accumulate ceiling to fair value | Starter | Attractive | Fair — below fair value |
| fair value to Trim floor | Hold | Watchlist | Fair — above fair value |
| at or above the Trim floor | Trim / Exit | Caution | Expensive |

This is the valuation-specific read; it feeds — but does not replace — the memo's outputs. The label informs (alongside quality, balance sheet, and growth) the overall Bullish/Neutral/Bearish verdict and the score. A great business can be Caution on valuation and still score well; a cheap weak business can be Attractive and still be Bearish overall.

## Margin-of-safety discipline

Define a fair-value **range** — the lock's bear-to-bull span around fair value — not a fake point estimate with unwarranted precision. The width of that range is measured from the company's own record, and the plan's levels sit inside it: the first tranche opens at fair value, the full position builds halfway down to the bear, trimming starts halfway up to the bull. A steadier business therefore gets a narrower range and closer levels; a volatile or low-visibility one gets a wider range and deeper buy levels. That is the whole margin of safety, applied once.

Do not add a second margin by shading the base case, the required return or the weights. And do not remove it by moving a level toward the price: the margin of safety is created by waiting for the price to come to the level, never by moving the level to the price.
