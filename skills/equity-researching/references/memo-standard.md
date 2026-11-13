# Memo Standard

Single source of truth for output format. Use this for all final outputs.

## Contents
1. Which template to use
2. Completeness contract (full mode)
3. Canonical section list (full mode)
4. Update report template
5. Full report template (single ticker)
6. Multi-ticker addendum
7. Style notes
8. Pre-emit checklist
9. Review mode format (`report_mode: review`)

## 1. Which template to use

- `report_mode: update` (the default) → Update report template (section 4). Updates are deltas: shorter is fine, shallow is not.
- `report_mode: full`, or an update with no prior report → Full report template (section 5), governed by the completeness contract below.
- `report_mode: review` → Review mode format (section 9). Review annotates an existing commented report in place; it never produces a new report file.

## 2. Completeness contract (full mode)

Every section in the canonical list is mandatory for every ticker. The reader treats a missing section as a defect, not a simplification — a silent gap is indistinguishable from a forgotten check.

1. Emit every section heading, in order, for every ticker.
2. No data? Keep the heading and write `[Data unavailable: <reason — e.g. not disclosed, paywalled, source blocked, stale beyond 90 days>]` plus any defensible directional comment. Never delete the heading.
3. Never fabricate numbers. `[Data unavailable]` always beats a guess.
4. Label every number with its source/date inline or in the Sources block. Older than 90 days → tag `[Stale]`.
5. Confidence must reflect coverage: more than 4 `[Data unavailable]` sections → Confidence = Low, plus a "Data coverage warning" line at the top of that ticker's block.
6. Multi-ticker memos repeat the full per-ticker template for each ticker; the peer-ranking block is in addition to, never instead of, the per-ticker sections.
7. Before emitting, run the pre-emit checklist (section 8) per ticker.

## 3. Canonical section list (full mode, in order)

1. Header block — resolved entity, verdict, score, confidence, data snapshot date, data quality line
2. AI Stack Role / Business Role — "AI Stack Role" only when the request is AI/tech-themed or the ticker is plausibly AI-adjacent; otherwise a 2–4 line "Business Role" paragraph
3. Core Business Breakdown — every major product/service, % of total revenue each contributes, and per-segment profitability where disclosed
4. Sector Analysis — exact competed market, market/TAM size, outlook with time frame, YoY market growth, major competitors with **estimated TAM share for each** (triangulated, not skipped — see Sector Analysis rules in the template), the subject's exposure and approximate market share **with supporting evidence**, and competitive advantages running both directions (subject over competitors, competitors over subject), each tied to specific evidence
5. Peer Map & Relationships — the 3–6 companies an investor groups with or confuses for the subject, each placed on the value chain (upstream supplier / downstream customer / same-layer competitor / adjacent), given its business-model distinction (pure-play vs integrated, component vs module/system vs platform), and classified by relationship type (competitor / supplier / customer / partner / co-opetition), with a one-line "why the subject differs" per peer and a synthesis paragraph. Cooperative and supply-chain links count as much as rivalry
6. Moat — competitive position, why customers stay, moat trend
7. Growth Trajectory
8. Quality — revenue/EPS quality, margins, returns, cash-flow quality
9. Financials Snapshot table
10. Balance Sheet
11. Cash Flow
12. Float & Share Dynamics — shares outstanding trend, dilution rate, SBC, offerings/ATM activity, free float, insider/institutional ownership, short interest
13. Valuation — first the **Value Lock** (the price-blind intrinsic value from valuation-framework Module 1: required return, bridge, base normal-year earnings, the measured bear / bull spread, the three values and the fair value at r* and r_hi, weights, change vs the prior lock), then the market read: multiples table, the Street reconciliation explaining any gap to consensus price targets, and the Cheap/Fair/Expensive verdict read off the level map
14. Catalysts (numbered, minimum 3, at least one dated)
15. Risks — top 3 (numbered)
16. Valuation Justification Check
17. Invalidation Triggers — explicit, observable, thresholded, time-bound where possible
18. Entry & Exit Plan — in two parts. **The Plan**, which contains no share price and reads the same whatever the stock is quoted at: the Value Lock reference; the derived level map (Floor / Accumulate / Starter / Hold / Trim / Exit, arithmetic shown, with the expected annual return each level offers); sizing at the stated loss budget with the correlated-cluster cap; a three-tranche plan with state-and-date gates; a dated event calendar; the seven-rule exit hierarchy, each rule carrying a state and a date or threshold; the does-not-trigger / does-not-move-a-level list; re-entry rules; and a one-line plan summary. **The Status**, the only price-dependent part: reference price, zone, distance to the next levels, distance to fair value, expected annual return at that price, the live action for new money and for a holder, and the event-exposure and liquidity checks. Method and derivations: `references/entry-exit-framework.md`
19. Final Impression (4–6 lines, decisive, consistent with the plan summary and the status line)
20. 13F / Ownership Signals
21. Latest Relevant News (last 7–60 days, minimum 2 items with link or source)
22. Glossary — every acronym or niche term used in the memo (e.g., NRE, FWA, SBC, FV, r*), one line each
23. Sources

## 4. Update report template (`report_mode: update`)

```markdown
# [Portfolio / WatchList / Ticker] Update Report — YYYY-MM-DD

- Report mode: update
- Compared against prior report: [path/date/type]
- Data snapshot: YYYY-MM-DD
- Scope: [Portfolio / WatchList / ticker list]
- Data quality: [coverage, conflicts, stale items]

## Executive Update
- Biggest positive change:
- Biggest negative change:
- Most important risk change:
- Recommendation changes:
- Entry/exit rules fired since prior report (exits, trims, tranche gates opened, floor-break evidence audits due):
- Value Locks recomputed since prior report (ticker: trigger, evidence, fair value old → new, any pending remainder) — all others carried verbatim:
- Names requiring full re-underwrite:

## Change Log Since Prior Report
| Ticker | Prior verdict/score | Current verdict/score | What changed | Action implication |
|---|---:|---:|---|---|
|  |  |  |  |  |

## Portfolio / WatchList Risk Updates
- Concentration/correlation changes:
- New downside risks:
- Risks that improved:
- Liquidity / balance-sheet risk changes:

## Per-Ticker Updates

### [TICKER] — Update
- Prior report: [path/date]
- Prior verdict / score / confidence:
- Current verdict / score / confidence:
- Price / valuation change since prior report:
- New earnings / filings / guidance:
- Analyst revisions / PT changes:
- Latest relevant news:
- 13F / ownership changes:
- Float / share dynamics change (dilution, offerings, SBC trend, buybacks, short interest):
- Peer-relationship change (new supplier/customer/partner link, M&A among peers, a name entering or leaving the batch, value-chain shift):
- Thesis change:
- Risk change:
- Catalyst update:
- Invalidation trigger status:
- Entry/exit plan status: zone now vs prior · levels reached or crossed since prior report (with dates) and the action each called for · rules fired (none / which → action due) · tranche gates open · expected annual return at the current price · next binary event (days to it) · event-exposure check E vs L if a binary event is within 10 trading days · plan provenance: [carried verbatim — lock YYYY-MM-DD → Floor / Accumulate / Starter / Trim / Exit $—/$—/$—/$—/$— unchanged] | [recomputed — trigger: subject printed / guidance changed / consensus operating estimates moved ≥ 10% / share count or net cash moved / business changed → attribution: input old → new (source, date) → fair value and levels old → new; step cap applied? remainder ±—% pending]. A price move or a level being crossed is never a reason to change the plan:
- Recommendation / next action:
- Sources:

## Recommendations
1.
2.
3.

## Watch Next
- [ticker/event/date]

## Sources
- Prior report:
- Market/price data:
- Filings/IR:
- News/analyst/ownership sources:
```

If a ticker has no meaningful change, write `No material thesis-changing update since prior report.` — but still include data freshness and any price/valuation movement, so the reader knows the name was actually checked rather than skipped.

Update reports focus on delta, evidence, and action implication. They may be shorter than full reports; they may not be shallow.

## 5. Full report template (single ticker)

```markdown
## [TICKER] — Fundamental Verdict

- Resolved entity: [Legal Company Name] ([Exchange]: [Ticker], [Country])
- Verdict: Bullish / Neutral / Bearish
- Score: X/100
- Confidence: High / Medium / Low
- Data snapshot: YYYY-MM-DD
- Data quality: Coverage X% | Conflicts X | Freshness: [TTM+latest quarter / annual+quarter / stale]
- FX: [USD-reported / reported in XXX, converted at 1 USD = N XXX, rate type + date]

### AI Stack Role / Business Role
[AI Stack Role for AI/tech-themed requests or AI-adjacent tickers; otherwise a 2–4 line Business Role paragraph: what the company does and how it makes money.]

### Core Business Breakdown
- Major products/services, with the % of total revenue each contributes:
- Per-segment profitability (where disclosed):

### Sector Analysis
- Exact competed market / subsector definition:
- Estimated market / TAM size:
- Sector outlook ([time frame]): bullish / neutral / bearish
- Expected market growth (YoY):
- Key sector drivers:
- Major competitors, with estimated TAM share for each:
- Subject's exposure to this market (% of revenue / segment / strategic):
- Subject's approximate market share, with the evidence behind the estimate:
- Subject's competitive advantage over competitors (evidence-tied):
- Competitors' advantages over the subject (evidence-tied):

Rules for this section — it is one of the most-read sections of the memo, so it cannot stop at "unavailable":
- **Competitor share estimates: triangulate, don't punt.** If shares are not directly published, look into each listed competitor: pull their relevant segment revenue from filings/IR, recent news, or analyst coverage, and divide by the market size to derive approximate shares. Label these as estimates with the inputs shown (e.g., "Broadcom optical interconnect revenue ~$X B per FY25 10-K vs ~$Y B market → ~Z% share, approximate"). Only write `[Data unavailable]` after this triangulation has been attempted and the inputs genuinely cannot be found — and then say which inputs were missing.
- **Subject share claims need shown work.** A claim like "subscale / low single-digit share" must come with its arithmetic: subject's relevant revenue vs the market size, in USD, with sources. If the evidence only supports a direction, say "directional estimate" and show what it rests on.
- **Competitive-advantage claims must be specific and evidenced.** "Scale, customer lock-in, manufacturing depth" with nothing attached is boilerplate that could describe any incumbent — it reads as filler whether or not it happens to be true, and the reader cannot distinguish it from hallucination. Each advantage named must be tied to a concrete fact: a named customer or design win, a capacity/capex figure, a revenue-scale comparison, a patent/process specifics, a switching-cost mechanism. If no concrete support exists for an advantage, drop it or explicitly label it `[Inference, unverified]` — never present generic attributes as findings.

### Peer Map & Relationships
The companies an investor naturally groups with — or confuses for — the subject, and how each actually relates to it. A flat competitor list is not enough: place each near-neighbor, name the distinction, and classify the relationship. Build this from the playbook's peer relationship mapping process.

- Peer batch (3–6 names): direct competitors plus the names that share the subject's ETFs, screens, and "X vs Y" comparisons.
- One table row per peer (below).
- Synthesis paragraph (3–6 lines): place the subject within the batch — who is upstream vs downstream, who supplies whom, where the subject is the more (or less) defensible position, and the one distinction a reader should remember.

| Peer | Value-chain layer vs subject | Business model / distinction | Relationship type | Why the subject differs (one line) |
|---|---|---|---|---|
| TICKER | upstream supplier / downstream customer / same-layer competitor / adjacent | pure-play vs integrated; component vs module/system vs platform | competitor / supplier / customer / partner / co-opetition | … |

Rules:
- **Map relationships, not just rivalry.** A peer can be supplier, customer, and competitor at once (co-opetition). Cooperative and supply-chain links are required, not optional — they drive pricing power and concentration risk.
- **Evidence the links.** Supplier/customer/partner relationships come from filings, IR, earnings calls, or news — cite them. An unverified link is labeled `[Inference, unverified]`, never stated as fact.
- **Disambiguate confusable names.** If two names "do the same thing" at a buzzword level, the distinction line must say what actually separates them (component supplier vs module integrator; merchant vs captive; pure-play vs vertically integrated).

Worked example — subject **AAOI (Applied Optoelectronics)**, AI-datacenter optical basket:

| Peer | Value-chain layer vs AAOI | Business model / distinction | Relationship type | Why AAOI differs |
|---|---|---|---|---|
| COHR (Coherent) | same-layer competitor, also reaches further up the chain | vertically integrated platform — owns InP EML dies, silicon photonics, GaAs VCSELs, SiC substrates, packaging | competitor (+ NVIDIA partner via the Mar-2026 $2B deal) | AAOI is a smaller pure-play 800G transceiver maker; COHR captures far more of the value chain |
| LITE (Lumentum) | upstream component supplier to module makers | merchant laser-chip / EML maker, with some module exposure | co-opetition — supplies EMLs that flow into modules, also competes in modules | AAOI sources lasers rather than owning a merchant EML franchise at LITE's scale |
| FN (Fabrinet) | contract-manufacturing partner | outsourced optical assembly for OEMs | partner / supplier, not a brand competitor | AAOI manufactures more in-house; FN assembles rather than sells competing modules |
| MRVL / AVGO | upstream DSP / silicon supplier | merchant DSP & co-packaged-optics silicon | supplier (+ long-run substitution risk via CPO) | AAOI integrates third-party DSPs; these vendors could disintermediate discrete transceivers over time |
| NVDA | downstream customer | compute/networking platform buying optical infrastructure | customer | AAOI demand is derivative of hyperscaler / NVIDIA optical spend |

Synthesis: Unlike LITE — an upstream laser-chip/EML supplier whose components flow into the modules — and unlike COHR — the downstream, fully vertically integrated module integrator that assembles EMLs, silicon photonics, DSPs, and packaging into finished products and now anchors NVIDIA's optical roadmap via the March 2026 $2B partnership — AAOI is a smaller pure-play 800G transceiver maker. It rides the same transceiver ramp but owns less of the value chain than COHR and lacks LITE's merchant component franchise, so within the basket AAOI is the higher-beta, less-defensible expression of the AI-optical thesis: more torque if 800G/1.6T demand outruns supply, more fragility on pricing, sourcing, and customer concentration.

### Moat
- Competitive position:
- Why customers stay / why competitors struggle:
- Moat trend: strengthening / stable / weakening / unproven

### Growth Trajectory
- Historical growth shape:
- Next 2-3 year growth drivers:
- Growth quality: organic / cyclical / acquisition-driven / narrative-driven

### Quality
- Revenue/EPS quality:
- Margins and returns (gross / op / net margin, ROE / ROIC):
- Cash-flow quality:

### Financials Snapshot
All figures in USD (converted per the FX header line for non-USD reporters).

| Metric (USD) | Latest | YoY | Notes |
|---|---|---|---|
| Revenue (TTM) | | | |
| Operating income | | | |
| Net income | | | |
| Gross margin | | | |
| Operating margin | | | |
| Net margin | | | |
| Diluted EPS | | | |
| CFO | | | |
| Capex | | | |
| FCF | | | |
| FCF margin | | | |
| Share count trend | | | dilution / buyback |

If a row's data is unavailable, write `[Data unavailable]` in the cell — do not delete the row.

### Balance Sheet
- Cash & equivalents:
- Total debt:
- Net debt:
- Interest coverage:
- Liquidity:
- Distress lens:

### Cash Flow
- CFO trend:
- Capex intensity:
- FCF / FCF conversion:
- Capital allocation (buybacks / dividends / M&A / dilution):

### Float & Share Dynamics
- Shares outstanding trend (3Y / 1Y / latest quarter):
- Annualized dilution or buyback rate:
- SBC as % of revenue and trend:
- Recent or pending offerings / ATM programs / convertibles / warrants:
- Free float and insider + institutional ownership %:
- Short interest (% of float) and trend, where available:
- Read: is the share count a tailwind, neutral, or a structural headwind to per-share value?

### Valuation

**Value Lock (price-blind).** Built per valuation-framework Module 1 from facts about the business, before the quote was used; the Entry & Exit Plan reuses it verbatim. This block contains no share price, market cap, trading multiple or "% vs price". The values are central estimates — no caution is added here; the plan's levels carry the margin of safety.

- Value Lock — [TICKER] — as of YYYY-MM-DD · evidence through [latest filing or print, date]
- Visibility: Standard / Low-visibility ([criteria met])
- Required return: r* = —% (risk flags raised: … | `hurdle:` override) · r_hi = —% · CAPM cross-check —% (context only; does not set r*)
- Weights (bear / base / bull): —/—/— (start 25/50/25; tilts applied: …)
- Values at r*: bear $— / base $— / bull $— → **fair value $—** · at r_hi: $— / $— / $— → $—
- Change vs prior lock: [first lock] / [carried verbatim] / [recomputed — attribution below] / [recomputed, step capped at 15% — evidence fair value $—, locked $—, remainder ±—% pending]

| | Bear — [mechanism] | Base — central case | Bull — [mechanism] | Source |
|---|---|---|---|---|
| Bridge revenue and EPS, years 1–2 [fiscal years] | | | | consensus / guidance, date |
| Growth to the normal year g_n | | | | independent forecasts, dates |
| Base normal-year revenue = ½·[R1·(1+g_n)⁴ + R2·(1+g_n)³] | | | | arithmetic shown |
| Normal margin → base normal-year EPS | | | | margin record |
| Spread d → bear / bull normal-year EPS | | | | operating-income record |
| Conversion (bridge → normal year) | | | | cash-flow record |
| Growth after the normal year → g | | | | |
| Diluted shares · net cash per share · f | | | | filing, date |
| **Value per share at r*** | $— | $— | $— | |
| **Value per share at r_hi** | $— | $— | $— | |
| Authorship | | | | consensus-anchored / guidance-anchored / analyst construction |

- Stress case (optional; not in the lock): [the bear's mechanism sized on its own arithmetic → $—] 

Attribution (only when the lock changed; the evidence column names a fact about the business, never the price):

| Lock item | Prior | New | Evidence (source, date) |
|---|---|---|---|
| | | | |

- Price-invariance test: [passed — at half and at double the quote every line above is unchanged]

**Market read (price-dependent).** Reference price $— (YYYY-MM-DD).

| Multiple | Trailing | Forward | Peer median | Read |
|---|---|---|---|---|
| P/E | | | | |
| EV/EBITDA | | | | |
| P/S | | | | |
| PEG | | | | |
| FCF yield | | | | |

- Relative multiples vs peers:
- Street reconciliation (when consensus price targets are available): mean target $— = —× bridge year-2 EPS vs the lock's fair value at —× · the target implies a required return of about —% against r* —% · the rest of the gap is [credit for forecast growth beyond the market's rate / normal-year margin / a multiple the cash flows do not support] · lowest / highest published target $— / $— vs the lock's bear / bull $— / $— · the lock is not moved toward a target
- Cheap / Fair / Expensive verdict (read off the level map: Cheap at or below the Accumulate ceiling · Fair between the Accumulate ceiling and the Trim floor · Expensive at or above the Trim floor):

### Catalysts
At least one catalyst carries a date — it is the Entry & Exit Plan's dated thesis state (Rule 5).
1.
2.
3.

### Risks (top 3)
1.
2.
3.

### Valuation Justification Check
**What must happen for current valuation to be justified:**
-
-

**What would break the thesis fastest:**
-
-

**Implied Expectations block** — required here whenever valuation-framework Module 4 (Reverse DCF / Implied Expectations) is in scope; omit only when Module 4 was not triggered. It reads the market against the Value Lock and changes nothing in it:
- Price basis, operating value per share (net cash/debt adjustment), diluted share count
- Framings run (≥3 of F1–F5) with the discount-rate grid (10/12/14% minimum) and stated FCF-conversion factors
- Scenario gap table (the three locked values from the Valuation section, at r* and r_hi, each with its % distance from the price — no new scenarios)
- Market-implied probability line set beside the lock's own weights (or the explicit degenerate-case statement if price exceeds all locked values)
- Sanity-anchor table (company peak, peer profit pool, implied market share, book/replacement floor, Street cross-check)
- Expectations-gap verdict: market-implied expectation in one sentence, locked base case in one sentence, `too low / roughly fair / too high` read off the level map, and the bull/bear asymmetry line
- Signposts wired into Invalidation Triggers (≥2 observable, thresholded)

### Invalidation Triggers
- Explicit, observable conditions that would force a downgrade, with thresholds and time frames (e.g., "DC revenue growth <20% YoY for two consecutive quarters").

### Entry & Exit Plan
Pre-committed levels, sizing, tranches, events, and exit rules — all derived from this memo's Value Lock per `references/entry-exit-framework.md`. Illustrative arithmetic at the stated risk budget; the reader's own budget governs. Every level shows its derivation; every exit rule carries a state and a date or threshold.

The section has two parts. **The Plan** contains no share price and must read the same whatever the stock is quoted at — at half today's price or at double. **The Status**, at the end, is the only place the quote appears.

#### The Plan (locked — independent of the current price)

- Source: Value Lock above — as of YYYY-MM-DD · r* = —% · r_hi = —% · [Standard / `[low-visibility]`] · pending remainder: [none / +—% / −—%]
- Values at r*: bear $— [mechanism] / base $— / bull $— [mechanism] · weights —/—/— → fair value $— · at r_hi: $— / $— / $— → $—
- Plan provenance: [first plan] / [carried verbatim from the prior report] / [re-cut — lock recomputed on (trigger): levels old → new, attribution in the Valuation section]

**Level map** (arithmetic per the framework; a `[low-visibility]` lock sets the Starter ceiling at (FV + bear) / 2 and the Accumulate ceiling at (FV + 2·bear) / 3)

| Zone | Price band (USD) | Level and its derivation | Expected return a year at that level | New money | Existing holder |
|---|---|---|---|---|---|
| Floor-break | < $— | Floor = PV_bear = $— | ≈ —% | no buying on price alone; Rule 2 evidence audit first; adds reopen only through a fundamental gate | Rule 2 |
| Accumulate | $— to $— | Accumulate ceiling = (FV + PV_bear) / 2 = … | ≈ —% | build to target in tranches | add per tranche gates, up to target |
| Starter | $— to $— | Starter ceiling = fair value = … | —% (= r*) | T1 only (⅓ target) | hold; add only on a confirmation gate |
| Hold | $— to $— | up to the Trim floor | | wait | hold, no adds |
| Trim | $— to $— | Trim floor = (FV + PV_bull) / 2 = … | ≈ —% | no entry | trim to ≤ 50% of target |
| Exit | ≥ $— | Exit floor = PV_bull = $— | ≈ —% | no entry | exit; token ≤ 10% of target only with a named non-DCF value explanation or an explicit tax/liquidity note, labeled as such |

- Expected return at a level p ≈ r* + (r_hi − r*) · ln(FV / p) / ln(FV / FV_hi), from the lock's two rates
- Ordering print: Floor $— < Accumulate $— < Starter $— < Trim $— < Exit $— (out of order ⇒ scenario slots mis-assigned; fix the lock)
- Sensitivity at r_hi = —%: Accumulate ceiling $— / Starter ceiling $— / Trim floor $— / Exit floor $—
- Precedence: in the 5 sessions before a binary event the event-sizing rule overrides the zone action; while the lock carries a pending remainder, no new tranche opens if it is downward and an Exit is taken as a Trim if it is upward
- These levels move only when the lock is recomputed — when the company reports or its estimates move materially — and none by more than 15% in one report. Reaching a level is the signal to act on it.

**Sizing** (defaults L = 2% NAV, L_top = 3%, cluster cap 10%, position cap 10%, ADV cap 5%; `risk_budget:` override echoed here if given; L is a loss to model value, not a drawdown limit)
- Loss budget applied: L = —% ([standard / top-conviction — business score A+B+C+E —/80 ≥ 68 and confidence High])
- Sizing price = Starter ceiling $— (always; never the reference price) · sizing bear = PV_bear at r_hi = $— (`[low-visibility]`: × 0.9)
- D_size = 1 − sizing bear / Starter ceiling = —% → target S_full = L / D_size = —% NAV (cap 10%) · tranche = S_full / 3 = —% NAV
- Factor cluster: [name] · subject contribution S_full × D_size = —% NAV · cluster usage before / after: —% / —% of 10% (or `[portfolio not provided — computed in the portfolio report]`)
- Half-Kelly cross-check (returns at r* values vs the Accumulate ceiling): f* = — → ½f* = —% → [S_full within cap / capped at —%] (or `[half-Kelly not run: reason]`)
- At or above the Exit floor $— the target size is zero

**Tranche plan** (all tranches are cancelled by a fired Invalidation Trigger, by the 5-session pre-event blackout and by a downward pending remainder; nothing opens below the Floor on price alone)

| Tranche | Size (% NAV) | Gate (state + date) | Zone condition | Cancelled by |
|---|---|---|---|---|
| T1 — starter | — (⅓ target) | no trigger fired; confidence ≥ Medium · valid until [next subject print, date], then re-stated on the new levels | Floor $— ≤ price ≤ Starter ceiling $— | trigger fired; pre-event blackout from [date] |
| T2 | — (⅓ target) | (a) [named catalyst] resolves ≥ [threshold] by [date] — or — (b) price at or below the Accumulate ceiling $— with a clean news check (no trigger fired; the decline does not trace to a thesis datapoint) | Floor $— ≤ price ≤ Starter ceiling $— | trigger fired; confidence falls to Low (T1 is then the maximum); pre-event blackout |
| T3 | — (⅓ target) | thesis working (first confirmation still stands; fair value not below $—, its value when T1 was taken) **and** second independent confirmation: [named event, threshold, by date] | Floor $— ≤ price ≤ Starter ceiling $— | trigger fired; first confirmation reversed; confidence falls to Low; pre-event blackout |

- Averaging-down rule as applied here: [permitted only via T2(b)/T3 gates, never below the Floor $—, never on a thesis datapoint]
- Missed-it rule: no chase above the Starter ceiling

**Event calendar** (minimum: subject's next two prints; ≥ 1 Peer-Map customer/supplier event; every dated Catalyst. Binary events = subject prints + any dated catalyst with a stated threshold; they carry the blackout, the E ≤ L check and the post-event lock check)

| Date / window | Event | Binary? | Thesis link (Catalyst / Trigger #) | Watch metric & threshold | Pre-event stance | If favorable → | If unfavorable → |
|---|---|---|---|---|---|---|---|
| YYYY-MM-DD | [subject FQn print] | yes | … | … | hold / no adds from [date] | T2 gate opens; lock recomputed within 5 sessions | Rule — check; lock recomputed |
| YYYY-MM-DD | [key customer / supplier event] | no | … | … | … | … | … |
| YYYY-MM-DD | [dated catalyst] | yes/no | … | … | … | … | … |

- Event-sizing rule: exposure E = size × implied move M must be ≤ L; else trim to L / M before the event and rebuild via the tranche gates after · no adds from [date = event − 5 sessions, inclusive]
- Post-event: each subject print recomputes the lock (no value moves more than 15% per report); the stock's reaction to the print is not an input
- Unscheduled watch items: [item — monitoring signal]; [item — signal]
- Event trade (only if the request names one): entry $— · own max loss —% NAV · exit by [date = event + N sessions] or at $— · closed on date regardless of P&L

**Exit hierarchy** — priority order: the highest-priority rule whose state is met governs; every rule keeps applying to whatever remains; written for the existing holder
1. Thesis-break (hard): [Invalidation Trigger(s), thresholds, confirmation standard — single-datapoint or needs a second confirming datapoint] → exit 100% within 5 sessions; re-entry only via a fresh full memo
2. Floor-break evidence audit (hard): close < Floor $— for 3 consecutive sessions → audit within 5 sessions (trigger status; sweep for information about the business dated after the lock; test the bear and any stress case against it) → exit if a trigger fired; if the sweep found new evidence, recompute the lock on it and apply the ordinary rules; else hold, no adds until a fundamental gate; if the evidence lowered the bear value, confidence −1 notch and size capped at current; if the sweep finds nothing new, the lock stands — the price is not evidence
3. Valuation: ≥ $— (Trim floor) trim to ≤ 50% of target; ≥ $— (Exit floor) exit — a trim only while an upward remainder is pending. Between fair value $— and the Trim floor the position is held: it still earns close to its required return. Levels rise only when a report raises the lock
4. Cycle-turn (cyclicals only): ≥ 2 of [named signals with sources] confirm → cut to ⅓ of target, full exit by [date] unless reversed — or `[n/a: not cyclical]`
5. Time stop: [dated thesis state] by [date] else cut to ⅓ of target with final date [date + 1 quarter]; second miss = exit — or `[n/a: no dated thesis state — reason]` (noted as a weakness)
6. Opportunity-cost: rotate if a fresh memo shows another name with an expected annual return at least 4 points higher, in a different factor cluster or in the same cluster with Σ size × D_size still ≤ cap after the swap, and the subject is in Hold or above
7. Concentration: size ≥ 10% NAV cap → trim to cap; size ≥ 1.5 × target (—% NAV) and not top-conviction → trim to target; top-conviction runs to the cap; portfolio reports: cluster Σ size × D_size ≥ 15% NAV → trim the largest contributor to target; appreciation below these thresholds never trims

- Does NOT trigger an exit: price drop with P > Floor and no trigger fired; the price standing at or somewhat above fair value; single downgrade / PT cut; unnamed macro headline; one competitor or supply-side datapoint without confirmation; "up a lot"; a miss inside the stated threshold; size drift above target below Rule 7's thresholds. Sole book-level exception: the drawdown guard in portfolio reports (priority between Rules 2 and 3)
- Does NOT move a level, a size or a gate: a price move of any size, including a gap on a print; the price reaching or crossing a level; a PT or rating change; a new report being written; the part of a change beyond the 15% step cap (pending until the next report)
- Re-entry: after Rule 1 or a Rule 2 exit → fresh full memo; after Rule 3 → price ≤ then-current Starter ceiling; after Rule 4 → signals reversed and price ≤ then-current Starter ceiling; after Rule 5 → only once the delayed state is observed; after Rule 6 → the expected-return advantage closes below 4 points or the subject returns to the Starter zone

**Plan summary (one line, no price in it):** Floor $— · Accumulate ≤ $— · Starter ≤ $— (fair value) · Trim ≥ $— · Exit ≥ $— (r* —%; at r_hi —%: Starter ≤ $— / Exit ≥ $—) · target —% NAV in 3 × —% · next binary event: [event, date] (no adds from [date]) · hard kill: [trigger, threshold, date]

#### Status at the reference price (the only price-dependent part)

- Reference price: $— (YYYY-MM-DD)
- Current zone: — · distance to the next level: −—% (to [level] $—) / +—% (to [level] $—)
- To fair value: +/−—% · to the bear: −—% · skew to fair value K = —:1 (`Floor-break — Rule 2 audit due` below the Floor; `n/a — price above fair value` at or above it) · expected return at this price ≈ —% a year (r* —%)
- Position state: [new money only / holder: cost $—, size —% NAV, tranches taken —] (from portfolio file or request; else `[not provided]`)
- Live action — new money: [T— executable now at —% NAV / wait for ≤ $—] · holder: [hold / add per T— / trim to —% / exit / Rule — due by date]
- Event-sizing check (next binary event, [event, date]): implied move M = —% [straddle / `[proxy: 1.5× 4-print mean]`] → exposure E = size —% × M = —% NAV vs L = —% → [within budget / trim to L / M = —% NAV before the event]
- Liquidity: S_full × NAV vs 20-day ADV $— → [≤ 5%, no cap / binds above a $— account / tranche capped to —% NAV]
- Timing comment (optional; never moves a level): [liquidity / price-action read]

**Status line:** at $— (YYYY-MM-DD): [zone] → [live action]; expected return ≈ —% a year; next level below $— (−—%) / above $— (+—%)

### Final Impression
Write 4-6 lines. Be decisive. Say what you would do and why — at the levels and on the dates the Entry & Exit Plan sets; the Final Impression, the plan summary and the status line must agree.

### 13F / Ownership Signals
- Source type: direct filings / SEC-derived aggregator / WhaleWisdom fallback / unavailable
- Reporting quarter:
- Recent notable 13F changes:
- What high-signal holders appear to be doing:
- Caution: 13F data are delayed and should not be treated as real-time conviction

### Latest Relevant News (last 7-60 days)
- Headline — why it matters — direct link
- Headline — why it matters — direct link

### Glossary
One line per acronym or niche term used anywhere in this memo, so a non-specialist reader never has to leave the document. Examples of the kind of terms to cover: NRE (non-recurring engineering — one-off customer-funded development revenue), FWA (fixed wireless access), SBC, ATM, FFO, AFFO, design win, tape-out. Include only terms actually used in the memo. Common investing terms a generalist already knows (P/E, EPS, FCF) may be skipped.

### Sources
- Official filings / IR:
- Aggregator pages:
- 13F / ownership sources:
- Other data sources used:
```

## 6. Multi-ticker addendum

Append after the individual per-ticker memos:

```markdown
## Cross-Ticker Relationship Map
How the analyzed names relate to one another — not just who scores higher. When the batch *is* the requested tickers, their inter-relationships must be explicit so the ranking is read in context (e.g., #1 may be a supplier to #3, making them complements rather than substitutes).
- Value-chain order of the batch (upstream → downstream):
- Supplier / customer / partnership links among these tickers:
- Which pairs are true head-to-head substitutes vs adjacent or complementary:
- Confusable pair(s) and the one-line distinction for each:

## Peer Ranking

1. TICKER_A — X/100 — why #1
2. TICKER_B — Y/100 — key gap vs #1
3. TICKER_C — Z/100 — why lower

### Best Pick
- Selected: [ticker]
- Why this wins:
- Invalidation triggers:

### Runner-Up
- What would need to change for #2 to become #1:

## Deployment Order & Cluster Budget
Ranking says which business is best; this says where new money goes *now*. It is a status table: each ticker's plan — its levels and target — is fixed by its own Value Lock, and this table only reads today's prices against those plans. A name moving up or down the order changes nothing in its plan.

| Ticker | Current zone | To fair value | Expected return a year at ref. price | Distance to the next buy level | Target (% NAV) | Next binary event | Tranche open now? |
|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |

- Deployment order (names in Accumulate first, then Starter, by expected annual return; Hold/Trim/Exit names listed as "no new money"):
- Correlated-cluster budget: cluster(s) named · Σ over held names of actual size × D_size = —% NAV, plus L per new full-target name (2% standard / 3% top-conviction; less where a cap binds) · fill new names in deployment order until Σ reaches the 10% cap; names beyond it keep their plan but are queued — listed as `budget-constrained`, no tranche opens until budget frees up · [fits: Σ = —% / constrained: —, — queued] · Σ ≥ 15% → Rule 7 cluster clause: trim largest contributor(s) to target
- Book drawdown guard (portfolio reports only; defaults 10% / 15% from high-water mark, `drawdown=` override; needs book NAV and HWM from the portfolio file, else `[not provided — drawdown guard not evaluated]`): current drawdown —% → [no action / tranche freeze until every held name has had its evidence audit / every position cut to half target]
- Exit/trim actions due now on any name in the batch:
```

## 7. Style notes

- Tie each conclusion to evidence — supporting metric values inline where possible.
- **No unevidenced boilerplate.** Generic descriptors ("scale advantages", "strong customer relationships", "deep manufacturing expertise") presented without a concrete supporting fact are indistinguishable from hallucination to the reader. Attach the fact or cut the claim (or, rarely, label it `[Inference, unverified]`).
- Define every acronym on first use and again in the Glossary.
- All monetary figures in USD per the playbook's currency standardization rules.
- Avoid fluffy company descriptions.
- Do not bury risks.
- Prefer crisp bullets over bloated prose.
- **Every price level shows its derivation.** A level in the Entry & Exit Plan without its formula and inputs is a round number in disguise; a level sourced from chart support, a consensus price target, or a cost basis is a defect.
- **No value or level depends on the quote.** The Value Lock and the Plan are written so that they would read the same at half or at double today's price. The share price, anything computed from it, and words like "at current levels" appear only in the market-read part of Valuation, the Valuation Justification Check, the plan's Status block and the Final Impression.
- Never output machine-readable JSON in the user-facing memo.

## 8. Pre-emit checklist (run for EACH ticker before returning)

Walk the canonical section list (section 3) and confirm all 23 sections are present and non-empty. Then verify:

- [ ] Catalysts ≥ 3, Risks = top 3, News ≥ 2 items with source
- [ ] Sector Analysis: competitor shares triangulated (not punted), subject share claim shows its arithmetic, every competitive-advantage claim has a concrete fact attached or is cut/labeled
- [ ] Peer Map & Relationships: 3–6 peers, each placed on the value chain with a business-model distinction and a relationship type (competitor / supplier / customer / partner / co-opetition); cooperative & supply links included, not just rivals; confusable names disambiguated; synthesis paragraph present; any unverified link labeled `[Inference, unverified]`
- [ ] Float & Share Dynamics present with a stated read (tailwind / neutral / headwind)
- [ ] **Currency scan**: search the drafted memo for non-USD currency codes and symbols (SEK, NOK, DKK, EUR, GBP, JPY, CNY, KRW, TWD, CHF, kr, €, £, ¥, ₩). Any hit outside the FX header line or an explicitly permitted parenthetical anchor figure is a defect — convert it to USD before emitting. FX line present in header for non-USD reporters.
- [ ] Glossary covers every acronym used
- [ ] Final Impression is 4-6 lines, actually decisive, and agrees with the Entry & Exit Plan's summary line and status line (same zone call, same levels)
- [ ] Invalidation Triggers are observable and thresholded
- [ ] **Value Lock** (Valuation section): built before the quote was used; every input cites an admissible source (no price, market cap, trading multiple, price target, beta-as-source, price history or Module 3/4 output); required return from the risk-flag rubric (or the `hurdle:` override) with the CAPM line as context only; one bridge shared by three scenarios; base normal-year revenue from the half-credit formula with its arithmetic shown, normal margin from the record; bear and bull set by the measured spread d (not by hand), each with a named mechanism; weights from the tilt rubric with the tilts printed; values and fair value at r* and r_hi; no price and no "% vs price" anywhere in the block. **No stacked caution**: the base is not shaded, the rate is not above the rubric, the bear is not deeper than d. If a prior lock exists: carried verbatim, or recomputed only on a listed trigger, with an attribution row for every changed input, no mention of price in the evidence column, and no value moved by more than 15% (any remainder recorded as pending)
- [ ] **Price-invariance test**: re-read the Value Lock and the Plan as if the stock were quoted at half today's price, then at double. Every value, level, size and gate is unchanged; only the Status block would differ. Anything that would move is a defect — fix the input that carried the price in
- [ ] **Street reconciliation** (when consensus price targets exist): the gap between the mean target and the lock's fair value is explained in terms of the required return, the credit given to forecast growth and the normal-year margin; the lock was not moved toward the target
- [ ] **Entry & Exit Plan — the Plan**: values, fair value, weights, r* and r_hi transcribed from the lock, not re-derived; five levels each with its formula, inputs and the expected annual return it offers — none from round numbers, chart levels, consensus PTs, cost basis or the current price; Starter ceiling at fair value (deeper for a low-visibility lock); Floor-break row present; ordering print and sensitivity line at r_hi present; event precedence and pending-remainder lines present; sizing is at the Starter ceiling with the haircut sizing bear and states S_full, tranche and cluster contribution, uses the business score (not the valuation label) for the top-conviction test, and echoes the budget actually used; three tranche rows each with a state-and-date gate, a zone condition and a cancel condition, none referring to the holder's cost or the price at the time of writing; event calendar has ≥ 3 dated rows including the next two prints and ≥ 1 Peer-Map customer/supplier event, binary events flagged, with the blackout start date; all seven exit rules present with a state and a date/threshold (Rule 2 is an evidence audit; Rule 3 trims at the Trim floor and exits at the Exit floor, never at fair value; Rule 4 written or `[n/a: not cyclical]`; Rule 5 names the dated thesis state or `[n/a]` with reason; Rule 7 fires only at the cap or 1.5 × target); does-not-trigger / does-not-move-a-level list and re-entry rules present; plan summary line present and free of any price-dependent figure. A plan whose levels are not derived, or whose exit rules say "monitor closely," is incomplete
- [ ] **Entry & Exit Plan — the Status**: reference price dated; current zone and distances to the next level below and above; distance to fair value and the expected annual return at that price; live action for new money and for a holder; event-sizing check E vs L for the next binary event; liquidity check; status line present. Nothing in the Status feeds back into the Plan
- [ ] Catalysts: at least one carries a date (the Rule 5 thesis state); Valuation section carries the Value Lock with its three-point fair-value range, ahead of the multiples table
- [ ] If valuation-framework Module 4 was triggered: Implied Expectations block present in Valuation Justification Check with ≥3 framings, the discount-rate grid, the scenario gap table built on the locked values (no new scenarios), sanity anchors, and an explicit expectations-gap verdict read off the level map — a reverse DCF that ends without a `too low / roughly fair / too high` call is incomplete, and one that changed a locked value is a defect
- [ ] Every quantitative gap reads `[Data unavailable]` with a reason — no silent blanks
- [ ] Anything older than 90 days tagged `[Stale]`
- [ ] >4 `[Data unavailable]` sections → Confidence = Low + "Data coverage warning" at top of block
- [ ] Multi-ticker: checklist passes per ticker, and the cross-ticker relationship map, the peer-ranking / best-pick block, and the Deployment Order & Cluster Budget table (with the fill-in-order cluster allocation and, for portfolio reports, the book drawdown guard) are present in addition
- [ ] Update mode: every per-ticker block carries the Entry/exit plan status line (zone vs prior, levels reached or crossed and the action each called for, rules fired, gates open, expected annual return at the current price, next binary event, E vs L when one is within 10 trading days, plan provenance); the prior Value Lock and plan were carried verbatim unless a trigger in valuation-framework 1.9 fired (subject reported or changed guidance; consensus operating estimates moved ≥ 10%; share count or net cash moved; the business changed; model correction), and any recompute shows its attribution, the old → new levels, the 15% step cap and any pending remainder; no level changed because the price moved or a level was crossed; the Executive Update lists rules fired and locks recomputed since the prior report

## 9. Review mode format (`report_mode: review`)

Review mode annotates an existing report (full or update) that the user has commented on. It changes the file in exactly four ways: (1) normalized user comment blocks, (2) analyst response blocks, (3) marked body corrections, (4) the review log plus one header review line. Everything else in the file stays untouched — nothing deleted, nothing reflowed, verdict/score/confidence never edited.

### Comment blocks (the user's words)

Normalize each detected user comment, at the exact place it was written, into a blockquote attributed with the commenter's name (here, Rick):

```markdown
> 💬 **Rick:** Isn't the FCF margin here overstated? TODO: check it against the latest 10-Q.
```

Rules:
- **Proofreading only.** Fix spelling, grammar, and markdown formatting. The comment's meaning, stance, and content are inviolable — never soften, strengthen, summarize, or extend it. If a fix could shift meaning, keep the user's original wording verbatim.
- One block per comment, at its original location. Never merge, split, reorder, or drop comments.
- Multi-line comments stay a single blockquote (every line prefixed `>`).
- Comments found inside a table cell: clean a short one in place and put its response block directly below the table quoting the row; move a long one to a comment block directly below the table noting the row/column it came from, leaving `→ see comment below` in the cell.

### Response blocks (the analyst's answer)

Directly beneath each comment block:

```markdown
> 💬 **Rick:** Isn't the FCF margin here overstated? TODO: check it against the latest 10-Q.

**↳ Response (2026-07-12) — claim: Partly right · TODO: done.** TTM FCF margin recomputes to 18.9% vs the memo's 21.4%: CFO of $4.02B was right (Q3-26 10-Q p. 5) but capex used a single quarter ($0.61B) instead of TTM ($1.02B). Corrected in the Financials Snapshot below. Thesis impact: minor — quality read unchanged; the FCF-yield row moves 3.5% → 3.1%. Sources: FY25 10-K; Q3-26 10-Q (retrieved 2026-07-12).
```

Rules:
- Every response opens with `**↳ Response (YYYY-MM-DD) — <type>: <resolution>.**`, type ∈ TODO / question / claim / judgment / meta. A comment that mixes types (a claim plus a TODO, as above) lists each type with its own resolution.
- Claim verdict vocabulary: **Confirmed / Partly right / Incorrect / Unverifiable** — verified against primary sources per the playbook's hierarchy, never against the report being reviewed (a memo cannot corroborate itself).
- Responses meet the same evidence bar as memo text: numbers inline, sources and retrieval dates named, USD only, `[Stale]` tags past 90 days, `[Data unavailable: <reason>]` when research dead-ends.
- Every response states thesis impact: none / minor / material. Material ⇒ recommend a fresh `update` or `full` run, in the response and in the review log.
- Judgment comments get a real evaluation — agree or disagree with arithmetic and evidence. Reflexive agreement is a defect.
- Threading: user text appearing beneath an existing response is a new comment — normalize it and respond beneath it, in order. A comment block with a response beneath it and no newer user text under that response is resolved; later passes leave it alone.

### Body corrections

Only when a comment or a fact-check proves a specific body statement wrong:

- Fix the wrong fact in place and mark it: `18.9% [Corrected 2026-07-12: was 21.4%]`. In tight table cells the marker may go in that row's notes column instead.
- Correct only the proven-wrong fact — no opportunistic rewrites, reformatting, or deletions around it.
- Every correction is listed in the review log. An unmarked or unlogged body edit is a defect.
- The header verdict / score / confidence lines are off-limits in review mode: responses flag, research runs re-score.

### Review log (appended at the end of the report)

One dated section per review pass, appended after everything else (after Sources and after any earlier review logs):

```markdown
## Comment Review — 2026-07-12

- Comments addressed: 7/7
  1. Financials Snapshot — claim + TODO — Partly right; FCF margin corrected 21.4% → 18.9%
  2. Valuation — question — answered (peer-median source cited)
  3. Risks — judgment — pushed back: customer concentration stays top-3 by revenue math
  …
- Fact-check verdicts: 2 Confirmed · 1 Partly right · 1 Incorrect · 0 Unverifiable
- Body corrections: FCF margin (Financials Snapshot); FCF yield (Valuation)
- Thesis impact: [none material — no re-run needed] / [material on <topic> — recommend `report_mode: update`]
- New sources used:
- Open items: [anything requested that could not be completed, with the reason]
```

Also add one line to the report's header block: `- Last comment review: 2026-07-12 (7 comments)`. Add it once; on later passes update it in place. For multi-ticker reports, the per-comment list names the ticker/section each comment sits in.

### Review pre-emit checklist (run before returning)

- [ ] Every enumerated open comment has exactly one response block; the count matches the review log
- [ ] Each normalized comment re-read against the user's original: meaning, stance, and content unchanged — formatting/grammar fixes only
- [ ] Every claim has a verdict backed by sources independent of this report
- [ ] Every body correction is marked in place and listed in the log; zero unmarked body edits; verdict/score/confidence untouched
- [ ] All new figures: USD, sourced, dated; `[Stale]` past 90 days; no fabricated numbers
- [ ] Review log appended; header review line added or updated
- [ ] Apart from the four permitted change types, the original file content is untouched — nothing deleted or reflowed
