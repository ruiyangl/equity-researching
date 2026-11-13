# Fundamental Playbook
 
The primary analysis engine. Single source of truth for sourcing, data collection, screening, scoring, and decision rules.
 
## Contents
1. Input parse
2. Ticker disambiguation gate
3. Source hierarchy and data collection
4. Data quality scorecard
5. Quick screen
6. Scoring framework (100 points)
7. Rating bands and tie-breakers
8. Sector adjustments
9. Hard decision rules

## 1. Input parse
 
Extract:
- ticker(s) or scope (portfolio / watchlist)
- region (default US)
- style: value / quality / growth / blend (default blend)
- horizon: short / medium / long
- sector-outlook time frame (default 12 months unless the user specifies otherwise)
- must-avoid constraints, if given
- required return, if given as a control line (`hurdle: r*=10%`); otherwise the valuation framework's risk-flag rubric sets it
- risk budget for the Entry & Exit Plan, if given as a control line (`risk_budget: L=2%, L_top=3%, cluster=10%, cap=10%, adv=5%, drawdown=10%/15%`); otherwise the framework defaults apply and the memo says so
- position state, if given (cost basis, size as % NAV, tranches taken) — from the request or the configured portfolio file; otherwise the plan is written for new money and a generic holder
- for portfolio reports: book NAV and high-water mark from the portfolio file, for the drawdown guard; otherwise `[not provided — drawdown guard not evaluated]`
- whether an event trade is requested (a tactical position around a named dated event); only then does the plan carry an event-trade line

## 2. Ticker disambiguation gate
 
For each symbol, resolve legal company name, primary exchange, and country. If a symbol is materially ambiguous across markets, ask one clarification question and stop — every downstream number depends on having the right entity.
 
## 3. Source hierarchy and data collection
 
### Source hierarchy
 
- **Tier 0**: the most recent earnings report or annual report.
- **Tier 1**: official filings, investor relations pages, SEC/company filings.
- **Tier 2**: reputable sell-side research, Seeking Alpha analyst reports, recent 13F filings, direct management quotes from earnings calls or official communications, credible insider blog posts/podcasts/interviews.
- **Tier 3**: reputable aggregators (Stock Analysis, Yahoo Finance, Koyfin-style public pages, Finviz). Use for fast metric retrieval and cross-checks.
- News/media: catalysts and context only — never the sole basis for a core metric.
Cross-check anomalous core metrics against a second source. If a required metric is unavailable or conflicting, mark it `NA`/`[Data unavailable]` and say why.
 
### Currency standardization (USD)
 
All monetary figures in the output are expressed in **USD**, regardless of the company's reporting currency. This makes foreign names directly comparable to US peers and to each other — a memo that mixes JPY, EUR, and USD line items cannot be scanned or ranked.
 
**Convert at collection time, not at the end.** As soon as a non-USD reporter is identified, fetch the USD rate and convert each figure as it is gathered. Deferring conversion to the drafting stage is how local-currency numbers leak into the final memo. Working notes and the memo itself should both be in USD.
 
Rules:
- Identify the reporting currency from the filings. If it is not USD, convert every monetary figure (revenue, income, cash, debt, FCF, market cap, etc.) to USD.
- For flow items (revenue, income, CFO, FCF), use the average FX rate over the reporting period when practical; for balance-sheet items and market cap, use a recent spot rate. If only one rate is practical, use a recent spot rate consistently and say so.
- State the conversion explicitly once in the memo header (e.g., `FX: reported in JPY; converted at 1 USD = 155 JPY, spot 2026-06-10`). Do not re-derive or re-label the rate on every line.
- Ratios, margins, growth rates, and multiples (P/E, EV/EBITDA, FCF margin, YoY %) are currency-neutral — compute them in the reporting currency and present as-is; never "convert" a percentage.
- YoY comparisons of converted absolute figures can be distorted by FX moves. When the FX swing is material (roughly >5% over the period), note whether growth differs meaningfully in constant currency, and prefer the company's constant-currency growth disclosure when available.
- For a key anchor figure or two (e.g., TTM revenue), it's fine to show the original currency in parentheses; everywhere else, USD only.
- If a usable FX rate cannot be obtained, do not guess — present the figure in local currency tagged `[Local currency: FX unavailable]` and lower confidence accordingly.
### Freshness rules
 
Prefer latest annual plus latest quarter.
- Core data stale (>12 months old) → label the work `STALE-DATA ANALYSIS` and cap confidence at Medium.
- Stale data AND source conflicts together → cap confidence at Low.
### Two-pass collection — the business first, the stock second

Collect in two passes and keep them apart in the working notes.

- **Pass A — facts about the business.** Everything the valuation is allowed to use. Finish it, build the Value Lock from it (valuation-framework Module 1), and only then use Pass B.
- **Pass B — facts about the stock.** The quote and everything computed from it. Used for the multiples table, the valuation score, the reverse DCF and the plan's Status block — never for the value or the levels.

The quote will usually be seen during Pass A; it sits beside the financials on most data pages. Seeing it is unavoidable; using it is the defect. No Pass B figure may appear in, or shape, a Value Lock input.

### Minimum data set (when available)

**Pass A — the business**
- Core business: every major product/service, % of total revenue each contributes, per-segment profitability where disclosed
- Competed market: exact market definition, TAM size, major competitors and their approximate shares
- Independent multi-year forecasts of the competed market (two or more where they exist, each with its date and any revision in the past twelve months); the company's own long-range market claims, kept separate
- Customers' budgets where the product is a capital good: their cash flow or revenue and what they have spent on this category over the last five years
- Revenue, operating income, net income
- Gross / operating / net margin — five fiscal years, ten where the record allows (the normal-year margin averages need them)
- ROE / ROIC or best available return metric
- Debt, cash, net debt, interest coverage
- CFO, capex, FCF, FCF margin, stock-based compensation
- Share-count trend / dilution or buybacks; diluted share count as filed; announced or contracted issuance; convertible terms
- Customer and product concentration (top customer, top three, largest product line as % of revenue)
- Consensus **operating** estimates for the next two fiscal years (revenue, EPS), with the date; guidance and any published long-term model
- Latest quarter / annual trends
- Multi-year growth signals: 3Y/5Y revenue growth, EPS trend, segment growth, management guidance, likely next 2-3 year drivers
- The cycle record: the worst peak-to-trough revenue and margin episodes of the last 10–15 years, and how long recovery took
- Moat evidence: market share, switching costs, scale, IP/process advantage, brand/distribution, ecosystem lock-in, cost advantage, or regulatory positioning where relevant
- Entry & Exit Plan inputs (collect now, not at drafting): the subject's next two confirmed or expected earnings dates; dated events of the Peer Map's key customers and suppliers; lockup expiries and known ATM/secondary windows; the one dated catalyst the thesis most depends on (the plan's time-stop state); for cyclicals, the 2–4 observable cycle-turn signals (contract pricing direction, inventory days, customer capex revisions, capacity additions) with sources

**Pass B — the stock**
- Share price and its date; market cap; enterprise value
- Valuation multiples: P/E, forward P/E, EV/EBITDA, P/S, PEG, FCF yield — trailing and forward where available; peer multiples
- Float dynamics that are market data: free float, insider + institutional ownership %, short interest where available
- Consensus price targets and ratings — for the Street reconciliation in the market read; never an input to value
- The options-implied move for the next print (ATM straddle) or, failing that, the last four post-earnings absolute moves; 20-day average dollar volume; beta (for the CAPM cross-check line only)
### Sector context (collect alongside company fundamentals)
 
- Define the exact competed market and subsector precisely enough to avoid fuzzy comparisons — exact market definitions over broad buzzword sectors.
- Key demand drivers, pricing dynamics, cycle position.
- Estimated size of the relevant market / served market / TAM, whichever is most supportable.
- Sector outlook over the chosen time frame, with an explicit YoY growth number for that market when available; if unavailable, say so and give a directional estimate with stated confidence.
- How much of the company's revenue, profit, or strategic narrative is actually exposed to that market — and whether the company is a pure-play, major participant, or partial-exposure vehicle.
- The company's approximate market share within that market when supportable; label estimates as approximate.

### Market-share triangulation (when shares are not directly published)
 
Market share is core to the sector verdict, so "estimates unavailable" after one search is not an acceptable stopping point. When no source publishes shares directly, derive them:
 
1. List the major competitors in the defined market.
2. For each competitor, pull the most relevant revenue figure — segment revenue from its filings/IR where the segment maps to this market, or product-line figures from earnings calls, news, or analyst coverage.
3. Convert to USD and divide by the estimated market size to get an approximate share per competitor.
4. Do the same for the subject company; show the arithmetic (revenue figure, source, market size, resulting %).
5. Label everything derived this way as an estimate, note where a competitor's segment is broader/narrower than the defined market, and state confidence.
6. Only after this attempt, if specific inputs genuinely cannot be found, mark those competitors `[Data unavailable: <which input was missing>]` — a partial triangulation with 4 of 7 competitors estimated is far more useful than a blanket "unavailable."
This is extra search effort, deliberately: a sector section without share estimates fails its purpose.
 
The distinction matters: a market can be attractive while the ticker has only token exposure to it. Always separate "the market is good" from "this company captures it."
 
### Peer relationship mapping (run for every report)

A list of competitors with share estimates is not enough. Companies in the same space — especially tangled ones like photonics, semis, biotech, payments, cloud infrastructure — are routinely confused with one another, and an investor cannot place the subject without knowing how each near-neighbor actually relates to it. So for every report, map the peer batch as *relationships*, not just rivals. This is core to placing the subject, not optional color.

1. **Identify the batch.** List the companies an investor would naturally group with, or confuse for, the subject — direct competitors plus the names that recur in the same ETFs, screens, analyst baskets, and "X vs Y" comparisons. Aim for the 3–6 that genuinely matter.
2. **Place each on the value chain.** State where each peer sits relative to the subject: upstream supplier (its output is an input to the subject), downstream customer/integrator (the subject's output feeds it), same-layer competitor (substitutable products to the same buyers), or adjacent (related market, not directly overlapping).
3. **Name the business-model distinction.** Pure-play vs diversified; component vs module/system vs platform; vertically integrated vs outsourced; merchant vs captive. This is what separates two names that "do the same thing" at a buzzword level.
4. **Classify the relationship type.** Competitor / supplier / customer / partner / co-opetition (simultaneously a supplier-or-partner *and* a competitor). Cooperative and supply-chain links matter as much as rivalry — a peer can be supplier, customer, and competitor at once, and that shapes the subject's pricing power, concentration risk, and defensibility.
5. **State the one-line distinction per peer:** why the subject is differentiated — better or worse — versus that specific peer. This is the takeaway the reader remembers.

Do the research to support it: pull each peer's product scope and supply/customer relationships from filings, IR, earnings calls, and news — never assert a supplier/customer/partner link you have not seen evidenced; label inferred links `[Inference, unverified]`. Worked example of the distinction between confusingly-similar names (COHR vs LITE vs AAOI in AI-datacenter optics): see the photonics example in memo-standard's "Peer Map & Relationships" section. That section owns the output format; this owns the process.

### 13F / ownership workflow (minimum standard when ownership is discussed)
 
Prefer direct/primary sources first (SEC filings, manager filings, official filer pages). If direct holder-change data are not efficiently accessible, use `https://whalewisdom.com/` as the fallback — and always label which source type the conclusion came from.
 
1. State the **reporting quarter** and remind the reader that 13F data are delayed.
2. Capture the **source type**: direct filer / SEC-derived aggregator / WhaleWisdom fallback / unavailable.
3. Record **institution count** and **total institutional shares** when an accessible aggregator provides them.
4. Record the **top 3-5 holders** by name when available.
5. Record **specific adds / trims / new positions / exits** from the latest accessible quarter. If the latest quarter is incomplete because filings are still arriving, say so and fall back to the most recently complete quarter.
6. Separate **broad passive ownership** (Vanguard, BlackRock, State Street) from **thesis-relevant active moves** (specialist growth funds, event-driven funds, concentrated managers, notable new positions, sharp trims).
7. End with a one-line interpretation: **ownership supports / is neutral to / challenges** the thesis.
Practical source order for fast desk work:
- Direct SEC filer pages or primary filer disclosures when easily accessible
- SEC-derived ownership aggregators (Fintel, 13f.info) for holder counts / top holders
- WhaleWisdom for holder-change summaries when direct holder-delta work is inefficient
- HedgeFollow / MarketBeat / similar only as supporting context for specific fund moves, never as sole ownership evidence
## 4. Data quality scorecard
 
Before the final verdict, state:
- Coverage % = available core metrics / required core metrics
- Conflicts count = materially conflicting core metrics
- Freshness = TTM+latest quarter / annual+quarter / stale
Confidence caps:
- Coverage <70% → Low
- Conflicts ≥3 → Low
- Heavy dependence on lower-quality (Tier 3 / context) sources → at most Medium
## 5. Quick screen
 
Pass/fail checks:
1. Size: market cap > $2B in US unless there is a good reason otherwise
2. Liquidity: current or quick ratio acceptable for the sector
3. Debt: leverage and interest coverage acceptable for the sector
4. Earnings trend: positive and reasonably stable over time
5. Cash flow trend: FCF positive or credibly inflecting
6. Return quality: ROE/ROIC respectable for the sector
7. Growth trajectory: multi-year drivers durable enough to matter, not one-quarter noise
8. Valuation: not absurd relative to peers and own history
Interpretation: 7-8 pass = strong candidate; 5-6 = selective / mixed; 0-4 = weak, highlight concerns prominently.
 
Checks 1 and 8 use Pass B data and are run after the Value Lock is written; the other six are Pass A.
 
## 6. Scoring framework (100 points)
 
Default style = blend.
 
### A. Business Quality + Moat + Sector Position (30)
- Margin quality + trend (6)
- ROE / ROIC quality (6)
- EPS quality + stability (5)
- Moat strength and durability (7)
- Sector position / relevance / exposure quality (6)
### B. Balance Sheet + Solvency (25)
- Liquidity (8)
- Leverage safety (10)
- Distress resilience / coverage (7)
### C. Cash-Flow Strength + Growth Trajectory + Sector Outlook (20)
- CFO / FCF trend (7)
- FCF margin + conversion (3)
- Growth trajectory quality and durability (6)
- Sector outlook supportiveness over the chosen horizon (4)
### D. Valuation (20)
- Multiples vs peers (12)
- Growth-adjusted value / FCF yield reasonableness (8)
### E. Capital Allocation (5)
- Buybacks vs dilution, SBC burden, red flags (5)
### Business score (price-free)
Section D is the only part of the score that uses the share price, so the total score moves when the price does. The **business score** = A + B + C + E after modifiers (maximum 80) does not. Report it beside the total. The Entry & Exit Plan's top-conviction test uses the business score (≥ 68 of 80, with confidence High), never the total or the valuation label, so that the target position size does not depend on the quote.
### Modifiers after base score
- Missing/conflicting data: -3 to -8
- Cyclical peak earnings distortion: -2 to -5
- One-off accounting noise: -2 to -5
- Excellent consistency and cross-check quality: +1 to +5
## 7. Rating bands and tie-breakers
 
- 85-100: Exceptional
- 75-84: Strong
- 65-74: Acceptable
- 50-64: Weak
- <50: Avoid
Tie-breakers for close peer rankings, in order:
1. Higher FCF durability
2. Better balance-sheet resilience
3. Less dilution / better capital allocation
4. Cheaper valuation for similar quality
5. Higher confidence
## 8. Sector adjustments
 
### Banks / insurers
Emphasize capital adequacy, reserves, asset quality, ROE stability. Ignore EV/EBITDA.
 
### Utilities / telecom
Emphasize interest coverage, debt maturity profile, regulated cash-flow visibility.
 
### High-growth software
Emphasize gross margin durability, FCF inflection, dilution/SBC discipline, retention if available. Do not over-anchor on P/E in low-profit phases.
 
### Cyclicals / commodities / autos
Use mid-cycle margins and through-cycle FCF. Do not trust spot-year P/E in distorted peak/trough conditions.
 
### REITs
Use FFO/AFFO, payout coverage, leverage, occupancy, lease rollover. Do not use EPS P/E as the primary anchor.
 
### Capital-intensive transitions (miners, infra, AI buildout)
Emphasize funding runway, unit economics, capex discipline, dilution path.
 
## 9. Hard decision rules
 
- Never conclude from one metric or one article alone.
- Keep these dimensions separate in the analysis: sector outlook, sector exposure, moat, growth trajectory, quality, balance-sheet safety, valuation.
- Prefer cash-flow truth over cosmetic EPS.
- Moat claims must be tied to evidence (share position, cost advantage, switching costs, ecosystem lock-in, IP/process edge, brand, regulation, distribution).
- Competitive-position claims (about the subject OR its competitors) must each carry a concrete supporting fact: a named customer/design win, a revenue or capacity figure, a documented cost/process edge, a specific switching-cost mechanism. Strings of generic attributes ("scale, lock-in, manufacturing depth") with nothing attached are banned as findings — the reader cannot tell evidenced shorthand from hallucination, so unsupported claims are either cut or explicitly tagged `[Inference, unverified]`.
- Size/share characterizations ("subscale", "low single-digit share", "market leader") must show their arithmetic: the subject's relevant USD revenue vs the market size, with sources.
- Every report maps the peer batch as relationships, not just a competitor list: each near-neighbor is placed on the value chain (upstream / downstream / same-layer / adjacent), given its business-model distinction, and classified as competitor / supplier / customer / partner / co-opetition, with a one-line "why the subject differs" takeaway. Cooperative and supply links count as much as rivalry; confusable names get an explicit distinction. See the peer relationship mapping process above and memo-standard's Peer Map section.
- Growth claims must distinguish cyclical rebound vs secular growth vs acquisition-driven growth vs true compounding.
- Value before price. The intrinsic values (bear / base / bull), the fair value, the required return and the scenario weights are built from Pass A data only and locked before the quote is used. The share price, market cap, trading multiples (the subject's or its peers'), price targets, beta and price history never enter them. A value or a level that would come out differently if the stock were quoted 50% higher or lower, with no new fact about the business, is a defect.
- Value the normal year, centrally. Each scenario is built on what the business earns in a normal year five years out, with the next two years of consensus as a bridge to it; forecast growth beyond the market's own rate gets half credit until delivered, and the bear and bull are set by the spread in the company's own operating record. The values are central estimates at a fair required return — caution is applied once, in the plan's levels, never stacked into the base case, the rate and the bear as well. No value moves by more than 15% in one earnings report, so long-term levels hold steady from one report to the next.
- Levels must be reachable. The first tranche opens at fair value and the full position builds halfway to the bear value; a holding at fair value is kept, not sold. A plan whose buy levels sit far below anything the stock has traded at while the business kept compounding is a sign of stacked caution in the lock, to be fixed there.
- Every full report ends its analysis with a pre-committed Entry & Exit Plan whose price levels are derived from the memo's Value Lock, never from round numbers, chart levels, consensus price targets, cost basis or the current price; whose exit rules each carry a state and a date or threshold; and whose event calendar is dated. The plan is carried verbatim from report to report and re-cut only when the lock is recomputed — when the company reports or its estimates move materially — with every change attributed — a rising price never raises a level, a falling price never lowers one, and reaching a level is the cue to act on it. Only the plan's Status block reads the current price. Process and derivations: `references/valuation-framework.md` (the lock) and `references/entry-exit-framework.md` (the plan); output format: memo-standard.
- 13F claims must distinguish delayed ownership disclosure from current real-time conviction.
- Market size, YoY growth outlook, and market share are stated when supportable; if not supportable, say so explicitly and use directional language.
- If something cannot be determined, say so. Every qualitative claim gets supporting metric values inline when possible. State assumptions explicitly.