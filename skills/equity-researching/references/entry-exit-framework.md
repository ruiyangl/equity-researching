# Entry & Exit Framework

Owns the method behind the memo's **Entry & Exit Plan** section: how price levels are derived, how a position is sized and built in tranches, how dated events are handled, and the pre-committed rules that govern exits. Read it before drafting that section — the section is mandatory in every full report, and its status line is mandatory in every update report. Output format lives in memo-standard; this file owns the derivations and the rules.

## The invariant: the plan does not know the price

The plan exists so that when the stock reaches a level, the action at that level is already decided. That requires the levels to stay put while the price moves toward them — and to sit where a real price can reach them.

- **The Plan** — the five levels, the target and tranche sizes, the tranche gates, the event calendar and the exit rules — is derived entirely from the Value Lock (valuation-framework Module 1, built without the share price) plus the risk budget. No formula in sections 3–9 takes the current price as an input. Written with the stock at $52, $70 or $90, the plan comes out identical, line for line (section 12 shows it).
- **The Status** — the reference price, the zone it falls in, the distance to each level, the expected return at that price, and which pre-written action is live today — is the only place the quote appears (section 10). It is recomputed in every report and feeds back into nothing.

| | Plan | Status |
|---|---|---|
| Built from | Value Lock + risk budget | Plan + market data |
| Changes when | the Value Lock changes on evidence (section 10) | the price moves |
| A ±30% price move with no news | leaves it untouched | changes the zone and the live action |

A plan that shifts when the price shifts is a commentary on the price, not a plan: the level being waited for retreats as the stock approaches it.

## Contents
1. Lineage — what the method borrows and why it fits
2. Inputs
3. Level map — derivation
4. Position sizing
5. Tranche plan (staged entry)
6. Event calendar and the event-sizing rule
7. Exit hierarchy (pre-committed kill criteria)
8. What does not trigger an exit, and what does not move a level
9. Re-entry rules
10. Status block, update-mode status line, and when the plan changes
11. Failure modes
12. Compact worked example

---

## 1. Lineage — what the method borrows and why it fits

The method is **expectations-gap investing with pre-committed, rule-based entries and exits**. Each piece comes from how elite discretionary managers actually operate:

- **The quote is an offer, not information about value** (Graham's Mr. Market; Buffett; Klarman). The market's price is there to be accepted or declined against an appraisal worked out independently; an appraisal that drifts with the quote has stopped being one. Hence the invariant above: the value is locked before the price is consulted, and the levels move only when evidence about the business does.
- **Levels come from value, never from charts or round numbers** (Rappaport/Mauboussin expectations investing; Klarman; Marks). The thesis lives in the gap between market-implied expectations and the analyst's own scenarios, so the buy/sell levels are solved from the memo's own values. Klarman rejects percentage targets fixed at purchase and calls stop-loss orders irrational; the margin of safety shrinks as price converges to value, and that convergence — not a round number — is what drives trimming.
- **A fair price is enough to start; a discount is needed to build** (Buffett/Munger: a wonderful business at a fair price; the playbook's own default stance). At fair value the stock offers its required return, which is a reason to own some of it. The margin of safety governs how much: the full position is built only where the price has fallen halfway to the bear value. Because the bear-to-bull range is measured from each company's own record, the margin is narrow for steady earners and wide for volatile ones — the same idea as scaling a margin of safety to uncertainty.
- **Caution is applied once.** A punitive discount rate, a cautious base case, a catastrophic bear and a demanding entry rule each look prudent alone; stacked, they put the buy levels where no real price ever goes, and the plan never executes. The lock is central; the levels carry the caution.
- **Entries are staged and pressed only when earned** (Cadence Capital builds 1% → 5% in five adds as a position proves itself; Druckenmiller presses when a trade is working and he has a cushion; Lynch and Tudor Jones forbid averaging down into deteriorating fundamentals).
- **Exits are the weakest link, so they are rules tied to information, not to price salience.** Akepanidtaworn, Di Mascio, Imas and Schmidt (*Journal of Finance*, 2023) found institutional PMs' buys beat random by roughly 120 bp/yr while their sells lost roughly 80 bp/yr to random selling, driven by salience (extreme past returns) — and that selling improved sharply around earnings announcements, when PMs thought deliberately. Marks allows two legitimate reasons to sell (the thesis has weakened; a better opportunity exists) plus size-based trimming. Druckenmiller exits the moment the reason for the position is gone, regardless of P&L. Annie Duke's "kill criteria" (a *state* and a *date*, written before the position exists) supply the pre-commitment mechanic. Alpha Theory's data across ~200 hedge-fund clients: holding only positions with positive probability-weighted return added about 3% CAGR; systematic sizing on top added about 6.7%.
- **A stock at fair value is a hold, not a sale.** Fair value is discounted at the required return, so a holder at that price still expects to earn that return. Selling there gives up a fair return and pays tax for the privilege. Trimming starts only when the price is halfway to the bull value, and the position is closed when the price pays for the bull case in full.
- **Hard risk budgets replace the risk manager.** Multi-manager platforms stop PMs at 3–5% mark-to-market drawdowns (capital halved) and 7.5–10% (out). The retail analog has two parts: a maximum *model* loss per position measured to the bear-case value, with a cap on correlated-cluster exposure — essential when every name in a book rides the same factor — and a *mark-to-market* drawdown guard at the book level, applied in portfolio reports.

Why this fits a concentrated, thesis-driven, catalyst-aware book run without an external risk manager: pre-commitment does the risk manager's job; the levels are arithmetic on the Value Lock the memo already produces, so the method adds a section, not a model; the event calendar and event-sizing rule make tactical trades around prints explicit instead of accidental; and the cluster cap addresses the real portfolio risk — one factor expressed eleven ways.

Cautionary case the rules are built to prevent: Pabrai sold Micron in September 2023 on a single supply-side datapoint (a Samsung production increase) and missed the HBM upcycle — a thesis-break exit without a stated threshold or a confirming second datapoint. Rule 1's confirmation standard, Rule 4's two-signal requirement and the lock's step cap exist because of trades like that. The opposite failure — trimming a compounder because it has "gone up" — is what the wide Hold zone and Rule 7's deliberately high threshold prevent.

## 2. Inputs

Collect during data gathering (playbook minimum data set), not at drafting time. They fall in two groups, and only the first builds the plan.

**Plan inputs — all price-free:**

- **The Value Lock** (valuation-framework 1.8): `PV_bear`, `PV_base`, `PV_bull` and the fair value `FV` at the required return r\* and at the stress rate `r_hi`; the weights; the visibility class; the lock's date; any pending remainder from the step cap. The plan uses exactly these and re-derives none of them. `PV_bear(r_hi)` is the sizing bear.
- **Dated events**: the subject's next two earnings dates; the dated events of the Peer Map's key customers and suppliers (hyperscaler capex guidance, a key customer's print, a supplier's capacity decision); every dated item in the Catalysts section; lockup expiries, ATM/secondary windows where known; scheduled macro events (FOMC, tariff or export-control decisions) **only** where the thesis names them as a driver.
- **The dated thesis state** for Rule 5: the one catalyst or signpost the thesis most depends on, with the date by which it must be observed. Catalysts must carry at least one dated item for this purpose; if none exists, name one from the Invalidation Triggers' signposts, or write `[n/a: no dated thesis state — <reason>]`.
- **Cycle-turn signals** (cyclicals only): the two to four observable signals that mark the subject's cycle turning (contract price direction, inventory days, customer capex revisions, utilization or capacity additions), each with its source.
- **The business score and confidence** for the top-conviction test (section 4): playbook sections A + B + C + E after modifiers (maximum 80 — the valuation section D is left out because it moves with the price), and the data-confidence grade.
- **Risk-budget parameters**: defaults in section 4; the user overrides with a control line, e.g. `risk_budget: L=2%, L_top=3%, cluster=10%, cap=10%, adv=5%, drawdown=10%/15%`.

**Status inputs — market data, used only in section 10's Status block and in the event and liquidity checks:**

- **Reference price** P and its date — the memo's data snapshot, in USD.
- **Options-implied earnings move** M — from the at-the-money straddle for the expiry just after the print. If no options data are accessible, use 1.5× the mean absolute post-earnings move of the last four prints and label it `[proxy: 1.5× 4-print mean]`.
- **20-day average dollar volume** (ADV) for the liquidity check.
- **Position state** when the portfolio file or the request supplies it: cost basis, current size (% NAV), tranches already taken. Otherwise the status is written for new money and for a generic existing holder.
- **Book NAV and high-water mark** (portfolio reports, from the portfolio file) for the drawdown guard; otherwise `[not provided — drawdown guard not evaluated]`.

## 3. Level map — derivation

Everything comes from the Value Lock at the required return r\*. No price appears in any formula. Show the arithmetic in the memo — a level without its derivation is a round number in disguise.

```
FV                 = p_bear·PV_bear + p_base·PV_base + p_bull·PV_bull     fair value
Floor              = PV_bear
Accumulate ceiling = (FV + PV_bear) / 2      upside to fair value equals downside to the bear
Starter ceiling    = FV                      the probability-weighted return equals r*
Trim floor         = (FV + PV_bull) / 2      halfway from fair value to the bull
Exit floor         = PV_bull                 the price pays for the bull case in full
```

| Level | Standard lock | `[low-visibility]` lock | Meaning |
|---|---|---|---|
| Floor | `PV_bear` | `PV_bear` | below it the market is pricing worse than the bear case |
| Accumulate ceiling `P_acc` | `(FV + PV_bear) / 2` | `(FV + 2·PV_bear) / 3` | the full target can be built at or below |
| Starter ceiling `P_start` | `FV` | `(FV + PV_bear) / 2` | the first tranche can be bought at or below |
| Trim floor | `(FV + PV_bull) / 2` | same | the margin has gone and half the distance to the bull is paid for |
| Exit floor | `PV_bull` | same | nothing is left but the bull case |

`Floor < P_acc < P_start < Trim floor < Exit floor` holds by construction whenever bear < base < bull; print the values anyway, and if they are out of order the scenario slots were mis-assigned — fix the lock, not the formula.

**What each level pays.** Beside each level print the expected annual return it offers — the discount rate at which fair value would equal that price — from the lock's two rates:

```
expected return at price p  ≈  r* + (r_hi − r*) · ln(FV / p) / ln(FV / FV_hi)        FV_hi = fair value at r_hi
```

At the Starter ceiling it is r\* by construction; it is higher at the Accumulate ceiling and the Floor, lower at the Trim and Exit floors. It turns each level into a plain statement — "below $— this stock offers more than —% a year on these scenarios" — and it is a property of the lock, not of the quote.

**Zones and actions** — standing instructions: each row is an action the reader can take on the day the price gets there, without waiting for a new report.

| Zone | Band | New money | Existing holder |
|---|---|---|---|
| Floor-break | `P < Floor` | no buying on price alone; the Rule 2 evidence audit runs first, and adds reopen only through a fundamental confirmation gate | Rule 2 |
| Accumulate | `Floor ≤ P ≤ P_acc` | build toward target in tranches (T1; T2/T3 per section 5 gates) | add per tranche gates, up to target |
| Starter | `P_acc < P ≤ P_start` | T1 only (⅓ of target) | hold; add only on a confirmation gate |
| Hold | `P_start < P < Trim floor` | no new money — wait | hold, no adds |
| Trim | `Trim floor ≤ P < Exit floor` | no entry | trim to a runner ≤ 50% of target |
| Exit | `P ≥ Exit floor` | no entry | exit; the only permitted holding is a token ≤ 10% of target with a named non-DCF value explanation (strategic scarcity, real-option value) or an explicit tax/liquidity note, labeled as such |

Add one sensitivity line: the Accumulate ceiling, Starter ceiling, Trim floor and Exit floor at `r_hi`. In the five sessions before a binary event (section 6), the event-sizing rule overrides the zone action.

**Pending remainder.** When the lock's step cap has left part of a change pending (valuation-framework 1.9), the levels are known to lag the evidence, so the plan acts at half strength on the side the lag would favour: while the remainder is **downward**, no new tranche opens; while it is **upward**, an Exit is taken as a Trim. Everything else stands.

Rules:
- **Levels are derived, never asserted.** No round numbers, no chart support/resistance, no consensus price targets, no cost basis. A liquidity or price-action read may appear as a one-line *timing comment* in the Status block (Druckenmiller's split: valuation says how far a move can go, liquidity and technicals say when) — it never moves a boundary.
- **Levels are locked, never drifted.** They move only when the Value Lock moves, and the lock moves only when the company reports or its estimates move materially (valuation-framework 1.9) — and no level moves by more than 15% in any one report. A rising price never raises a level and a falling price never lowers one. As the business executes, each report rolls the values forward and the zones move up; that is the only mechanism by which a winner is allowed to run.
- **Reaching a level is the signal to act on it, not to re-derive it.**
- **The levels must be reachable.** If the Starter ceiling sits at a price the stock has not traded at in years while the business has kept compounding, check the lock for stacked caution — a shaded base case, a rate above the rubric, a bear sized by hand instead of by the record — before concluding the market is wrong.

## 4. Position sizing

Defaults, all as % of portfolio NAV; the user's `risk_budget:` control line overrides and the memo prints the values actually used. Like the levels, the sizes are part of the locked plan: nothing here takes the current price as an input.

- **Loss budget per position** `L = 2%` standard; `L_top = 3%` for top-conviction names: business score (playbook A + B + C + E after modifiers) ≥ 68 of 80 **and** confidence High. Valuation is deliberately not part of the test — cheapness is already enforced by the levels, and a budget that flipped with the valuation label would make the target size a function of the quote. **L is a loss to model value — what the position loses if the stock goes to the bear-case value — not a mark-to-market drawdown limit.** The drawdown guard below is the mark-to-market control.
- **Sizing price**: always the Starter ceiling `P_start` — the highest price at which the plan ever buys. Sizing there means the loss budget holds at every permitted fill (a lower fill loses less than budgeted), and the target does not depend on where the stock happens to trade when the report is written.
- **Sizing bear**: `PV_bear(r_hi)` — the bear value at the stress rate (× 0.9 for a `[low-visibility]` lock). The bear case is the most model-dependent number in the memo, so sizing takes a haircut the level map does not.
- **Target size** `D_size = 1 − sizing bear / P_start`; `S_full = L / D_size`; hard cap `10%` NAV. `S_full` changes only when the lock or the risk budget changes. "Target" everywhere in the plan means this number.
- **Tranche** = `S_full / 3`.
- **Correlated-cluster cap.** Name the subject's dominant factor cluster (e.g. *AI datacenter capex*, *memory cycle*, *US power build-out*). Require `Σ_cluster (size_i × D_size,i) ≤ 10%` NAV — the sum of bear-case losses across the cluster, i.e. what the book loses if the shared factor breaks and every name in it goes to its (haircut) bear value at once. Because `S_full = L / D_size`, a full-target position contributes exactly `L` when no cap binds (less when the 10%, ADV or half-Kelly cap does), so the default budget admits five full-target names per factor at L = 2% (fewer when L_top names are present; ten at half target). The sum is taken over *actual* sizes, so held names count at what they are — a Rule 3 runner at 0.5·L, a name drifted to 1.5× target at 1.5·L. The cap is enforced at sizing and at every portfolio-report re-sizing; Rule 7's cluster clause handles drift between reports. A book that expresses one thesis through more names than that is not diversified; it is one position with eleven tickers, and the cap is what says so. Always report the subject's own contribution `S_full × D_size`; when the portfolio is known, report cluster usage before and after; otherwise write `[portfolio not provided — cluster usage computed in the portfolio report]`.
- **Exit rule for size**: at or above the Exit floor the target size is zero; the only permitted holding is the Exit-zone token described in section 3.
- **Half-Kelly cross-check** (optional, one line). Evaluate it at the Accumulate ceiling, the price at which the full position may be built: with scenario returns `R_i = PV_i(r*) / P_acc − 1` and weights `p_i`, solve numerically for the `f*` that maximizes `Σ p_i · ln(1 + f·R_i)`; report `½·f*`. If `S_full > ½·f*`, the loss budget is too loose for this payoff distribution — cap at `½·f*`. It is a cap, never a target. If not run, write `[half-Kelly not run: <reason>]`.
- **Liquidity check — an execution check, not part of the derivation.** `S_full × NAV ÷ ADV ≤ 5%` (the position can be exited in one session at modest participation). ADV is market data, so evaluate it in the Status block and again at execution. If NAV is unknown, print the dollar position size at which the cap binds. If it binds, it caps the tranche being executed and the memo says so; it never changes a level.
- **Event-exposure constraint** — section 6 — can lower the size allowed into a print.
- **Book drawdown guard (portfolio reports only — a watchlist has no book).** Mark-to-market drawdown of the whole book from its high-water mark `> 10%` → no new tranches on any name until every held name has had its Rule 2-style evidence audit; `> 15%` → cut every position to half target. Defaults, overridable via `drawdown=` in the control line. This is the pod-shop stop in retail form; it belongs to the portfolio report, not the single-ticker memo, because it is a statement about the book. It is the one book-level, price-driven rule: its thresholds are fixed in advance, it changes no level and no lock, and it sits between Rules 2 and 3 in priority — it never overrides a thesis-break or floor-break exit, and it cuts names in Accumulate with no trigger fired, deliberately, because a 15% book drawdown in a one-factor book means the factor is being tested, whatever each memo says.

Sizing is illustrative arithmetic at the stated budget. The reader's own risk budget governs; the memo never presents a size as personalized advice.

## 5. Tranche plan (staged entry)

Three tranches, each with a gate written as a **state + date**, a zone condition, and what cancels it. Every gate is a level from section 3 plus facts about the business — none refers to the price at which the report was written or to the holder's cost. Every tranche is cancelled by any fired Invalidation Trigger, by the five-session pre-event blackout (section 6), and by a downward pending remainder in the lock (section 3).

- **T1 — starter (⅓ of target).** State: `Floor ≤ price ≤ P_start`, no Invalidation Trigger fired, data confidence ≥ Medium. Date: valid until the subject's next print, when the lock is recomputed and the gate is re-stated on the new levels. At Low confidence, T1 is the maximum until confidence improves — T2 and T3 are what Low confidence cancels, not T1.
- **T2 (⅓).** Zone condition: `Floor ≤ price ≤ P_start`. Gate, one of:
  (a) *fundamental confirmation* — a named catalyst or event (section 6 table) resolves at or above its stated threshold by its date; or
  (b) *price confirmation of value* — price at or below the Accumulate ceiling and at or above the Floor, with a clean news check: no trigger fired, and the decline does not trace to a thesis datapoint (contract loss, guidance cut, a cycle-turn signal).
- **T3 (⅓).** Zone condition: `Floor ≤ price ≤ P_start`. Gate: both of (i) the thesis is working — the first confirmation still stands and fair value in the current lock is not below its value when T1 was taken — and (ii) a second, independent confirmation has arrived by its date. Press when the position has earned it, not before.

Rules:
- **Below the Floor nothing opens on price.** A price under the bear value is either maximum margin of safety or a bear case that was too kind; the Rule 2 evidence audit decides which. After a clean audit, adds reopen only through the fundamental gates — T2(a) or T3.
- **Averaging down** happens only through the T2(b) / T3 gates: never below the Floor, never when the drop traces to a thesis datapoint. Those belong to exit Rules 1, 2 and 4 — a cheaper price is not a reason to add to a position whose reason is eroding.
- **Missed it.** If a confirmation gaps the price above `P_start`, there is no chase. Hold what is owned; the next add waits for the next confirmation or a retreat.
- Each tranche row states its trigger, its zone condition, its size, and what cancels it.

## 6. Event calendar and the event-sizing rule

**Binary event** = every subject earnings print, plus any dated catalyst row that carries a stated threshold. These rows get the blackout, the exposure check, and the post-event lock check; other rows (a peer's print, a lockup) are watch items with stated actions.

Every full report carries a dated table (format in memo-standard) with, at minimum: the subject's next two earnings dates; at least one dated event from a Peer Map customer or supplier; every dated Catalyst; known lockup / ATM / secondary windows; and a scheduled macro event only if the thesis names it as a driver. Each row says what metric is watched, at what threshold, the stance going in, and the action on a favorable versus unfavorable outcome. Unscheduled watch items (export-control action, M&A, an offering) are listed below the table with the signal that would surface them.

**Event-sizing rule.** Exposure into a binary event `E = size × M` (M = implied move or proxy). Require `E ≤ L` — the rule deliberately borrows the model-loss budget L as the budget for a one-day mark-to-market gap, since a print is the one place the two coincide. If it fails, trim to `size = L / M` before the event and print the number; rebuild through the tranche gates afterwards. No adds in the 5 trading days before a binary event (from `print − 5 sessions`, inclusive) unless the user asked for an event trade. In those five sessions the event rule overrides the zone action. M is market data: the rule is fixed in the plan, the check is run in the Status block.

**Event trade line** — only when the request names a tactical trade around an event: entry level, its own maximum loss (not borrowed from the thesis position's budget), and an exit by date (event + N sessions) or level, whichever comes first. Event trades close on their date regardless of P&L — a tactical trade that becomes a "long-term hold" after it loses is the classic failure.

**Post-event.** Within 5 trading days of every subject print, recompute the lock from the evidence the print supplied (valuation-framework 1.9), apply the step cap, re-cut the level map, print the attribution, and apply the tranche, trim and exit rules to the result. What the print said about the business is the input; how far the stock gapped on it is not. Selling decisions made deliberately around information events are the ones the evidence says are good; make the plan's decisions there.

## 7. Exit hierarchy (pre-committed kill criteria)

Priority order, not time order: the highest-priority rule whose state is met governs the action, and every rule continues to apply to whatever remains after a trim. Every rule carries a **state** and a **date or threshold**; a rule that says "monitor closely" is a defect. Written for the existing holder.

1. **Thesis-break exit (hard).** Any Invalidation Trigger fires on its stated threshold → exit 100% within 5 trading days, regardless of P&L or zone; no averaging down; re-entry only through a fresh full memo. *Confirmation standard:* a supply-side or competitor datapoint (a capacity announcement, a rival's price cut) fires only with a second confirming datapoint (contract pricing, inventory, utilization) unless the trigger was deliberately written as single-datapoint.
2. **Floor-break evidence audit (hard).** Price closes below the Floor `PV_bear(r*)` for 3 consecutive sessions → an evidence audit within 5 trading days: (i) confirm the status of every Invalidation Trigger; (ii) sweep for information about the business dated after the lock — filings, guidance, customer and supplier disclosures, cycle signals; (iii) test the bear scenario and any printed stress case against what the sweep found. **Exit** if a trigger has fired (Rule 1 governs). If the sweep found new evidence, recompute the lock on it and apply the ordinary rules to the new levels; if it lowered the bear value, cut confidence one notch and cap the position at its current size. **Otherwise hold**, with no adds until a fundamental confirmation gate. If the sweep finds nothing new, the lock stands exactly as written: the price being below the Floor is not itself evidence, and a re-run that "finds" a lower bear case without a new datapoint is anchoring, not analysis. This is a forced-deliberation stop in place of a mechanical one.
3. **Valuation trim / exit.** `P ≥ Trim floor` → trim to ≤ 50% of target. `P ≥ Exit floor` → exit (a trim only, while an upward remainder is pending in the lock). The levels are the current lock's; they rise only when a report raises the values on evidence about the business — a higher price is never that evidence. For cyclicals the values are the mean-reverting ones, so this rule already embeds the cycle. Between fair value and the Trim floor the position is simply held: it is still expected to earn close to its required return.
4. **Cycle-turn exit (cyclicals only).** Two or more of the memo's named cycle-turn signals confirm → cut to ≤ ⅓ of target and set a one-quarter date for full exit unless the signals reverse. Write `[n/a: not cyclical]` otherwise.
5. **Time stop.** The dated thesis state (section 2) has not appeared by its date → cut to ⅓ and set one final date a quarter out; a second miss is an exit. A thesis whose deadline keeps moving is a hope. `[n/a: no dated thesis state — <reason>]` is permitted only when the Catalysts and Invalidation Triggers carry no date at all, and that absence is itself noted as a weakness.
6. **Opportunity-cost rotation.** A fresh memo shows another name whose expected annual return at its current price is at least 4 points higher, and that name sits in a different factor cluster, or in the same cluster with `Σ size × D_size` still within the cap after the swap, and the subject sits in Hold or above → rotate; the memo documents the comparison. (Marks's second legitimate reason.) Expected return is a status figure — each name's lock against its own price — so this rule is evaluated when the comparison memo is written.
7. **Concentration trim.** Size ≥ the 10% NAV cap → trim to the cap, always. Size ≥ 1.5 × target and the name is not top-conviction → trim to target. Top-conviction names run to the cap. Cluster clause (portfolio reports): `Σ_cluster size × D_size ≥ 1.5 × cluster cap` → trim the largest contributor to target, repeat until within the cap. Appreciation below these thresholds never trims — value convergence is Rule 3's job, and a position built to target that has simply risen is a winner, not a concentration problem.

## 8. What does not trigger an exit, and what does not move a level

**Does not trigger an exit:**

- A price drop while `P > Floor` and no trigger has fired.
- The price standing at or somewhat above fair value. Fair value is where the stock earns its required return; it is the middle of the Hold zone's reasoning, not a target.
- A single sell-side downgrade or price-target cut.
- A macro headline the thesis did not name as a driver.
- One competitor or supply-side datapoint without confirmation (the Micron lesson).
- The stock being "up a lot" — salience is precisely what the evidence says destroys exit value.
- A missed quarter that stays inside the thesis's stated threshold.
- Size drifting above target through appreciation, below Rule 7's thresholds.

The one exception is book-level, not name-level: the drawdown guard (section 4) in portfolio reports, which cuts names regardless of their own zone when the whole book has drawn down past its thresholds.

**Does not move a level, a size or a gate:**

- A price move of any size, in either direction — including a gap on a print.
- The price reaching or crossing a level. That is the cue to act.
- A price-target change, a rating change, or the stock looking "obviously" cheap or expensive.
- A new report being written. Absent a lock trigger, the plan is carried verbatim.
- The part of a change that exceeds the lock's 15% step cap. It is recorded as pending and waits for the next report.

## 9. Re-entry rules

- After Rule 1 or a Rule 2 exit: a fresh full memo is required before any re-entry.
- After Rule 3: re-enter when price falls to or below `P_start` of the **then-current** lock — never on levels from a superseded one.
- After Rule 4: only when the cycle-turn signals have reversed and price ≤ then-current `P_start`.
- After Rule 5: only once the delayed state has actually been observed.
- After Rule 6: when the rotation target's expected-return advantage has closed below 4 points, or the subject returns to the Starter zone on the current lock.
- After an event trade closes: a new event trade needs its own line; it does not inherit the old one.

## 10. Status block, update-mode status line, and when the plan changes

### Status block — the only price-dependent part of the section

Computed last, from the finished plan and the reference price P. It reports; it never feeds back.

```
Zone            = the band of section 3 that P falls in
Distances       = % from P to the nearest level below and the nearest level above
To fair value   = FV / P − 1
To the bear     = PV_bear / P − 1
Skew K          = (FV − P) / (P − PV_bear)        upside to fair value ÷ downside to the bear; only for Floor < P < FV
Expected return = r* + (r_hi − r*) · ln(FV / P) / ln(FV / FV_hi)     a year, at this price, on the lock's scenarios
```

K is "skew to fair value" and is labeled that way; it is not the Valuation Justification Check's bull/bear asymmetry line, which uses PV_bull. If the price is below the Floor, write `Floor-break — Rule 2 evidence audit due` instead of K; at or above fair value write `n/a — price above fair value`.

The block then states the **live action**: for new money, which tranche (if any) is executable today and at what size, or the level to wait for; for a holder, hold / trim / exit or the rule that is due. It closes with the checks that need market data — the event-exposure check when a binary event is near, the liquidity check — and an optional one-line timing comment.

If the status looks strange — the price far outside the bear–bull range — that is a finding to report (and, below the Floor, a Rule 2 audit). It is never a reason to revisit the lock.

### When the plan changes

The plan changes only when the Value Lock does, on the triggers in valuation-framework 1.9: the subject reports or changes guidance; consensus operating estimates for a bridge year move 10% or more; the share count or net cash moves materially; the business itself changes; an error is corrected. At a trigger the lock is recomputed and the levels and `S_full` are re-cut from it — no value, and so no level, moving more than 15% in one report, with any remainder recorded as pending.

Otherwise the plan is **carried verbatim**: same lock date, same five levels, same `S_full`. A price move, a level being crossed, a Rule 2 audit that found nothing, or the mere fact of a new report changes nothing. Whenever the plan does change, the memo prints the lock's attribution table and the old → new levels, and "the price moved" may not appear in the evidence column. A plan whose lock is more than 100 days old is tagged `[Stale]` and is due a recompute.

### Update-mode status line

Every update report carries, per ticker: the zone now versus the prior report; levels reached or crossed since the prior report, with dates, and the action each one called for; rules fired (none / which, and the action due); tranche eligibility (which gates are open); the next dated event and days to it; if a binary event falls within 10 trading days, the event-exposure check `E` versus `L`; the expected annual return at the current price; and the plan's provenance — `carried verbatim (lock YYYY-MM-DD)` or `recomputed` with the trigger, the attribution, the old → new levels and any pending remainder.

## 11. Failure modes (check before emitting)

- **Any value, level, size or gate that would change if the quote changed with no new fact about the business.** Run the half-and-double test: at half the price and at double, the Plan must read the same.
- **Stacked caution.** A base case shaded "to be prudent", a required return above the rubric, a bear sized by hand below the record's spread, weights tilted without a listed condition — each makes the levels unreachable and none belongs in the lock. Caution is the distance between the Starter and Accumulate ceilings, and nothing else.
- Scenario values pitched to bracket the price, or nudged toward a consensus price target.
- Levels re-derived because a boundary was crossed, the price gapped, or a new report was being written. A lock changed without an attribution row, or with the price in the evidence column. A value or level moved more than 15% in one report.
- Selling at fair value. Fair value is the top of the Starter zone and the bottom of the Hold zone — a place to stop buying, not a place to sell.
- Levels taken from round numbers, chart levels, consensus price targets, or the holder's cost basis instead of the Value Lock.
- Sizing at the reference price instead of the Starter ceiling; a top-conviction budget keyed to the valuation label; sizing off the unhaircut bear.
- A gate that refers to the holder's cost basis or to the price at the time of writing.
- Averaging down into a fired trigger, or sizing an add by how far the stock has fallen; opening a tranche while a downward remainder is pending.
- An exit rule without a state and a date; "monitor closely" as a rule.
- Trimming a winner for having risen, below Rule 7's thresholds.
- A price below the Floor handled by quietly lowering the bear case, or an exit below the Floor without the Rule 2 audit having found a fired trigger.
- An event trade left open past its date.
- The cluster cap ignored because each position passes on its own; the drawdown guard omitted from a portfolio report.
- Default budgets presented as advice; the `risk_budget:` or `hurdle:` override not honored or not echoed.
- Status figures (zone, K, expected return at the price, distances) mixed into the plan lines or the plan summary.

## 12. Compact worked example (format to replicate)

> Hypothetical — the lock from valuation-framework 1.11. **Value Lock** (as of 2026-11-02; r\* = 12%, r_hi = 14%; Standard visibility): bear **$43.71** [largest customer digests inventory] / base **$64.97** / bull **$84.72** [new fab ramps on schedule]; weights 25/50/25 → fair value = 10.93 + 32.48 + 21.18 = **$64.59**. At 14%: $37.37 / $54.01 / $69.52 → $53.73. No pending remainder.
>
> **Plan — no price used anywhere:**
>
> | Level | Derivation | Price | Expected return a year at that price |
> |---|---|---|---|
> | Floor | PV_bear | **$43.71** | ≈ 16.2% |
> | Accumulate ceiling | (64.59 + 43.71) / 2 | **$54.15** | ≈ 13.9% |
> | Starter ceiling | fair value | **$64.59** | 12.0% (= r\*) |
> | Trim floor | (64.59 + 84.72) / 2 | **$74.66** | ≈ 10.4% |
> | Exit floor | PV_bull | **$84.72** | ≈ 9.1% |
>
> Ordering check 43.71 < 54.15 < 64.59 < 74.66 < 84.72. Expected return, e.g. at the Accumulate ceiling: 12% + 2% × ln(64.59 / 54.15) / ln(64.59 / 53.73) = 12% + 2% × 0.176 / 0.184 = 13.9%. Sensitivity at 14%: Accumulate ceiling $45.55, Starter ceiling $53.73, Trim floor $61.62, Exit floor $69.52.
> Sizing (at the Starter ceiling $64.59; sizing bear = PV_bear at 14% = $37.37): D_size = 1 − 37.37 / 64.59 = 42.1%; L = 2% → **S_full = 4.7% NAV**, tranche **1.6%**. Cluster "AI datacenter capex": subject contribution 4.7% × 42.1% = 2.0% of the 10% budget `[portfolio not provided]`. Half-Kelly at the Accumulate ceiling $54.15 (returns −19% / +20% / +56%, weights 25/50/25): f\* ≈ 3.0 → ½f\* ≈ 150% ≫ 4.7%, no cap binds.
> Tranches: T1 1.6% at $43.71–$64.59, valid until the FQ2 print 2026-12-17; T2 1.6% on (a) FQ2 datacenter revenue ≥ $— by 2026-12-17 with price $43.71–$64.59, or (b) price $43.71–$54.15 with a clean news check; T3 1.6% once the first confirmation stands and fair value ≥ $64.59, plus a second confirmation (named customer capex guide ≥ $— by 2027-01-30), price $43.71–$64.59.
> Next binary event: FQ2 print 2026-12-17; no adds from 2026-12-10. Hard kill: datacenter segment revenue growth < 20% YoY for two consecutive quarters (prints of 2026-12-17 and 2027-03-18) → exit 100% within 5 sessions. Time stop: the customer capex guide (dated thesis state) by 2027-01-30.
> **Plan summary:** Floor $43.71 · Accumulate ≤ $54.15 · Starter ≤ $64.59 (fair value) · Trim ≥ $74.66 · Exit ≥ $84.72 (r\* 12%; at 14%: Starter ≤ $53.73 / Exit ≥ $69.52) · target 4.7% NAV in 3 × 1.6% · next event FQ2 print 2026-12-17 (no adds from 12-10) · hard kill DC growth < 20% YoY ×2 by 2027-03-18.
>
> **Status — the same plan read against four different quotes:**
>
> | Quote | Zone | Distance to next level | To fair value · skew K · expected return | Live action |
> |---|---|---|---|---|
> | $52 | Accumulate | −15.9% to Floor $43.71 · +4.1% to Accumulate ceiling $54.15 | +24% · 1.5:1 · ≈ 14.4% a year | T1 executable now (1.6%); T2(b) open on a clean news check |
> | $60 | Starter | −9.7% to Accumulate ceiling $54.15 · +7.7% to Starter ceiling $64.59 | +8% · 0.3:1 · ≈ 12.8% | T1 executable now (1.6%); further adds need a confirmation gate or ≤ $54.15 |
> | $70 | Hold | −7.7% to Starter ceiling $64.59 · +6.7% to Trim floor $74.66 | −8% · n/a · ≈ 11.1% | no new money; holders hold |
> | $90 | Exit | −5.9% to Exit floor $84.72 | −28% · n/a · ≈ 8.4% | no entry; holders exit (Rule 3) |
>
> Every line of the plan is identical in the four cases; only the status row differs. A report written at $90 and one written at $52 must print the same levels, the same target and the same gates. Event check at $60 with an 18% implied move: E at full target = 4.7% × 18% = 0.85% ≤ L = 2% → within budget.
>
> **Carried through time.** After the FQ2 print consensus for FY2 rises 4%: the lock is recomputed, fair value and the levels rise about 3%, and the attribution names that estimate change. Had the print instead called for +24%, the step cap would move each value and every level 15% (fair value to $74.28), record the remaining +7.6% as pending, and — the remainder being upward — downgrade any Exit to a Trim until the next report. Had the stock fallen 25% with no report and no estimate change, the plan would be carried verbatim — same lock date, same five levels — and only the status row would change.
