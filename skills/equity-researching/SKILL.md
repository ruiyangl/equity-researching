---
name: equity-researching
description: "Deep, buy-side-quality fundamental analysis of public equities: single-ticker memos, multi-ticker peer comparisons with a ranked best pick, portfolio/watchlist update reports, and valuation work. Use this skill whenever the user mentions a stock ticker, asks whether a company is a good investment, asks to analyze/compare/rank equities, requests a portfolio or watchlist review or refresh, asks about valuation or fair value of a public company, asks what is priced into a stock (implied expectations, reverse DCF, 'priced for perfection', whether the current price is justified), asks where to buy, add, trim or sell a stock (entry/exit levels, position sizing, when to take profit, whether to hold through earnings), or sets up a recurring finance check — even if they don't say 'research memo'. Every full report ends with an Entry & Exit Plan (levels fixed by a price-blind valuation, tranches, dated events, exit rules). Supports report_mode: full and report_mode: update (default: update)."
---

# Equity Researching

Produce equity research at the standard of an experienced fundamental analyst: evidence-tied, decisive, bear-case-aware, and honest about data quality. Never casual ticker hype — every verdict comes with a thesis, a bear case, and explicit conditions that would prove it wrong.

## Reference files — read in this order

1. `references/fundamental-playbook.md` — **read before starting any analysis.** Owns the source hierarchy, data-collection rules, 13F workflow, quick screen, 100-point scoring framework, sector adjustments, and decision rules.
2. `references/memo-standard.md` — **read before drafting output.** Owns the canonical section list, both report templates (full and update), the completeness contract, and the pre-emit checklist. It is the single source of truth for what a finished memo must contain.
3. `references/valuation-framework.md` — **read for every full report**, and whenever the request centers on valuation, fair value, upside/downside, price targets, or scenario analysis. Its Module 1 builds the **Value Lock** — bear / base / bull values, a fair value, the required return and the weights, worked out from facts about the business with no share price in them — which is the only input of the Entry & Exit Plan. Its Module 3 explains any gap between that fair value and consensus price targets. Any "what's priced in" / implied-expectations / reverse-DCF question additionally triggers Module 4 and its Implied Expectations output block, which reads the market against the lock and never changes it.
4. `references/entry-exit-framework.md` — **read before drafting the Entry & Exit Plan section of any full report, and before writing the entry/exit status line of any update report.** Owns the method (levels derived from the Value Lock, loss-budget sizing with a correlated-cluster cap, three-tranche staged entry, dated event calendar with an event-sizing rule, a seven-rule pre-committed exit hierarchy, and the Status block that reads the current price against the fixed plan), the derivations, the defaults, and the failure modes.

**The rule that binds valuation and plan together: value is worked out without the price; the price is only ever compared against it.** Levels exist so that the action is already decided when the stock gets there, so they must not move when the stock moves. The Value Lock and the Plan read the same at half or at double today's quote; they change only when the company reports or its estimates move materially, no level moves more than 15% in one report, and every change is attributed. Only the plan's Status block depends on the current price.

**And the value has to be one a real price can reach.** The lock holds central estimates at a fair required return; caution is applied once, in the plan's buy and sell levels — the first tranche opens at fair value, the full position builds halfway down to the bear value, trimming starts halfway up to the bull. A cautious base case on top of a punitive rate on top of a catastrophic bear on top of a demanding entry rule produces levels that never trade, and a plan that cannot be executed is as useless as one that moves.

When SKILL.md and a reference seem to disagree, the reference owns its domain (playbook owns research process; memo-standard owns output format; valuation-framework owns value estimation; entry-exit-framework owns how value becomes levels, sizes, tranches, events and exit rules).

## Report modes

Two report modes, plus a review pass (below). The user may state a mode in plain English or as a control line (`report_mode: full` / `report_mode: update`).

- **`update` (default)** — for "refresh", "update", recurring/cron runs, weekly/monthly checks, or when no mode is given. Update reports are deltas against the most recent prior report: succinct and dense, focused on what changed and what to do about it, but built with the same sourcing and cross-checking discipline as full reports. Use the update template in memo-standard. An update carries the prior report's Value Lock and plan forward verbatim and re-cuts them only when one of the evidence triggers in valuation-framework 1.9 has fired; it never changes a value or a level because the price moved or a level was reached.
- **`full`** — when explicitly requested, or when an update is requested but no prior report exists. Full mode is bound by the completeness contract in memo-standard: every canonical section, for every ticker, no silent omissions. That includes the **Value Lock** and the **Entry & Exit Plan** — a full report that stops at a verdict without a price-blind valuation, derived levels, sizing, tranches, a dated event calendar and pre-committed exit rules is incomplete. If an earlier report already holds a Value Lock for the ticker, a new full report starts from it rather than from a blank page.

Optional control lines for the plan: `hurdle: r*=10%` (the investor's required return, overriding the valuation framework's risk-flag rubric); `risk_budget: L=2%, L_top=3%, cluster=10%, cap=10%, adv=5%, drawdown=10%/15%` (loss budget per position, top-conviction budget, correlated-cluster cap, single-position cap, liquidity cap as % of 20-day ADV, book drawdown freeze/cut thresholds — framework defaults shown); `position: cost=$—, size=—%, tranches=—` for an existing holding; `event_trade: <event, date>` when a tactical trade around a dated event is wanted. Absent these, the plan uses the defaults, says so, and is written for new money and a generic holder.

The review pass, `report_mode: review`, annotates an existing report in place with responses to the user's comments (memo-standard section 9); it produces no new report and no new plan.

### Finding the prior report (update mode)

1. Use the output directory configured by the task/agent setup if one is supplied.
2. Otherwise use the default reports directory `reports/finance/` under the agent workspace (e.g. `~/.openclaw/workspace/reports/finance/`).
3. Search dated subdirectories newest-to-oldest. Full or update reports both count as valid priors.
4. Prefer a prior report with matching scope (Portfolio vs WatchList vs single ticker). If only a partial-scope match exists, use the closest one and state the limitation in the header.
5. If no prior report exists, fall back to full mode and state: `No prior report found; falling back to full report.`

Run the same search before any full report: if an earlier report holds a Value Lock for the ticker, that lock is the starting point (valuation-framework 1.9).

### Resolving scope

The request may carry explicit tickers (`tickers: AAPL, MSFT, GOOGL`), a scope line (`scope: my portfolio`), or plain English. If no tickers are specified, default to the user's portfolio: read it from the configured portfolio file or the most recent portfolio report in the reports directory. If no portfolio definition can be found anywhere, ask the user for the ticker list rather than guessing — analyzing the wrong universe wastes an entire run.

## Workflow

### 1) Resolve every security first
Identify legal company name, ticker, primary exchange, and country. If a symbol is materially ambiguous across markets (e.g. same ticker on multiple exchanges), ask one clarification question and stop. Everything downstream is wrong if this step is wrong.

If the company reports in a non-USD currency (e.g. a Swedish name reporting in SEK), look up the current USD exchange rate **now**, before collecting any financials, and convert every monetary figure to USD as it is collected. All output is USD-denominated — never emit a local-currency number in the memo body. Full rules are in the playbook's currency standardization section.

### 2) Gather data with source discipline — the business first, the stock second
Follow the source hierarchy, minimum data set, sector-context rules, and 13F workflow in `references/fundamental-playbook.md`, in its two passes: **Pass A** collects facts about the business (filings, guidance, consensus operating estimates, independent market forecasts, customers' budgets, the operating record, dated events); **Pass B** collects facts about the stock (quote, market cap, multiples, price targets, options-implied move, volume). Cross-check anomalous numbers against a second source. Missing or conflicting data is never hidden — it is labeled and it lowers confidence, per the playbook's data-quality scorecard.

### 3) Lock the value before the price is used
Build the Value Lock per `references/valuation-framework.md` Module 1 from Pass A alone: required return from the risk-flag rubric; a two-year consensus bridge shared by three scenarios; a base normal-year EPS from the half-credit formula and the company's own normal margin; bear and bull set by the spread measured from its operating record; weights from the tilt rubric. Keep the values central — add no caution here. If a prior report holds a lock for the ticker, carry it verbatim unless a trigger has fired; when one has, recompute it, move no value by more than 15% in one report, and attribute every change to a fact about the business. Then run the price-invariance test — at half or at double today's quote, with nothing about the business changed, every number in the lock must be the same. Only now bring in Pass B.

### 4) Score like a fundamental investor
Apply the playbook's quick screen, then the 100-point scoring framework with sector-aware adjustments. Default stance: prefer quality compounding at a fair price over statistically cheap weak businesses; favor durable FCF, strong balance sheets, sane capital allocation. Explicitly classify growth (organic / cyclical / acquisition-driven / narrative-driven), moat trend (strengthening / stable / weakening / unproven), and float dynamics (dilution, SBC, offerings — tailwind / neutral / headwind). Watch for cyclical peak earnings, dilution, one-off accounting noise, and leverage-hidden fragility.

Evidence discipline applies to every qualitative claim: competitive-advantage and market-share statements must carry concrete supporting facts and shown arithmetic per the playbook — generic unevidenced attributes are cut, not emitted. All monetary figures convert to USD per the playbook's currency rules.

### 5) Draft output to the memo standard
Use the matching template from `references/memo-standard.md`. For multi-ticker requests: analyze each company individually first, then add the peer-ranking and best-pick block — the ranking supplements, never replaces, the per-ticker memos. If the batch is so large that full per-ticker memos are impractical, confirm scope with the user before abbreviating.

### 6) Derive the Entry & Exit Plan from the lock, then add the status (full mode: every ticker; update mode: the status line)
Convert the valuation into action per `references/entry-exit-framework.md`. **The Plan** takes only the Value Lock (the three values and the fair value at r* and r_hi, the weights, any pending remainder), the risk budget and the dated events from step 2: derive the level map (Floor / Accumulate / Starter / Hold / Trim / Exit) with the arithmetic shown and the expected annual return each level offers; size at the Starter ceiling with the stated loss budget and the correlated-cluster cap; write the three tranche gates as state + date; fill the event calendar; write all seven exit rules with a state and a date or threshold; end with the one-line plan summary. No formula in the Plan takes the current price, so it comes out the same whatever the stock trades at. **The Status** comes last and is the only price-dependent part: the zone the reference price falls in, the distance to the next levels and to fair value, the expected annual return at that price, the live action, and the event-exposure check for the next print. When consensus price targets exist, the market read explains the gap to them (the Street reconciliation) rather than leaving two sets of numbers side by side. Levels never come from round numbers, chart levels, consensus price targets, cost basis or the current price, and they change only when the lock changes on evidence — reaching a level is the cue to act on it, not to re-derive it. The Valuation labels (Cheap / Fair / Expensive, Attractive / Watchlist / Caution) are read off the level map, and the Final Impression must agree with the plan summary and status line. For multi-ticker reports, add the Deployment Order & Cluster Budget table after the peer ranking.

### 7) Self-check before emitting
Run memo-standard's pre-emit checklist for each ticker, including the price-invariance test on the Value Lock and the Plan. Any section without data still appears, containing `[Data unavailable: <reason>]` plus whatever directional judgment is still defensible. Brevity is fine; absence is not — the reader treats a missing section as a defect, and a silent gap is indistinguishable from "the analyst forgot to check."

## Constraints

- Educational/informational analysis only — not personalized investment advice. The Entry & Exit Plan's sizes are illustrative arithmetic at a stated risk budget, and its levels are the analyst's derived values, not predictions; the reader's own budget and judgment govern.
- The current share price never enters the valuation or the plan. It appears only where the market is being read against them: the multiples table, the Valuation Justification Check, the plan's Status block and the verdict. A value or level that would come out differently at a different quote, with no new fact about the business, is a defect.
- Never fabricate metrics. `[Data unavailable]` always beats a guess, because a wrong number silently corrupts the score and the verdict.
- If source access is constrained (paywall, blocked, stale), say so explicitly.
- Data quality caps confidence; the caps live in the playbook's scorecard. Poor data → Low confidence, stated up front.
