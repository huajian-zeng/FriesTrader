# Phase A — Screening & Thesis Only (Automated Daily Task)

Automated subset of this pipeline (see `README.md`), run every weekday
4:30pm Central as a scheduled routine.

Performs **ONLY Steps 1–3**. **NEVER** Step 4 (re-verify), 5 (risk
enforcement), 6 (order instructions), or 7 (`trade_log.jsonl`) — those
belong to Phase B. Order tools (`create_order_instruction`,
`delete_order_instruction`) are hard-blocked at the connector level; do
not attempt them anyway.

## Broker access — the IBKR connector

All market and account data comes from the IBKR MCP connector. Two
mechanics differ from every other MCP you may have used, and both bite
immediately:

**1. Everything is keyed by `contract_id`, not by ticker.** Before any
price call, resolve the symbol with `search_contracts`, then use the
chosen row's `underlying_contract_id`. **Two conditions, both required:**

1. `symbol` matches the ticker **exactly** — a live search for "AAPL"
   also returns AAPU, AAPB, AAPD, AAPE, AAPW, AAPY and IOSX, and a
   near-match is a different instrument, not a close-enough one.
2. `country_code == "US"` — **exact symbol match alone is not enough.**
   That same live search returned **four** rows whose symbol is exactly
   "AAPL", on NASDAQ (US), MEXI (MX), EBS (CH) and TSE (CA, an
   "APPLE INC-CDR"). Without the country filter, picking "the exact
   match" can land on a Mexican listing or a Canadian depositary receipt.

Resolve each symbol once per run and reuse the id; do not re-resolve per
call. **If a symbol does not resolve to exactly one US exact match, drop
it** and log
`"reason": "no unique US contract match in search_contracts — excluded rather than guessing an instrument"`.
Rows carrying an `issuer` instead of an `underlying_contract_id` are
bonds; ignore them.

**2. Response keys are hyphenated where request names are underscored.**
Requesting `misc_statistics` returns `misc-statistics`; `avg_90d_usd_volume`
returns `avg-90d-usd-volume`; `bid_ask` returns `bid-ask`. Read values
from the hyphenated form. A lookup against the underscored name returns
nothing, which looks exactly like missing data — and missing data has
real consequences below, so do not confuse the two.

If a call fails or returns nothing usable, log what failed and drop that
candidate. Never substitute a value from a previous run, a plausible
estimate, or your own knowledge for data a failed call didn't return.

## Market-hours guard — check the clock, don't trust the schedule

Before Step 1, read the current time with
`TZ='America/Chicago' date +'%H:%M'` and **stop the run** unless it is
**15:00 Central or later** on a weekday. Write
`"stage": "summary", "halted": true, "reason": "ran at <HH:MM> Central, before the 15:00 close — the latest daily bar is incomplete and every 60-day signal would be computed against a partial session"`
to `pending_proposals.jsonl` and do nothing else.

Cloud cron fires on a fixed UTC expression while Central time shifts with
daylight saving, so a schedule that is 16:30 Central in summer becomes
15:30 in winter. That particular drift still lands after the close, but
the same mechanism can push a run into the session, where the newest daily
bar is a half-finished day and every 60-day move is computed against it.
This guard makes that visible instead of quietly poisoning the inputs.

## Step 1 — Build the watchlist

Pull symbols from every IBKR watchlist named in `universe.watchlist_names`
in `risk_rules.json` (read fresh each run — don't assume prior values or
hardcode the names). Call `get_watchlists` once, match each configured
name **exactly** against the returned `name` field, then call
`get_watchlist` on each matching id. Ignore watchlists not in the list.

**Union the results and drop duplicates by `contract_id_ex`** — a symbol
on two lists is one candidate, not two.

**If a configured name matches no watchlist, stop the run and log it.**
Do not proceed with the lists that did resolve: a typo would otherwise
silently shrink the candidate universe every cycle with nothing in the log
to show what went missing.

**Drop anything that isn't a US-listed stock**, before spending any call
on it. Watchlists are not restricted to equities — a live check found FX
pairs sitting alongside stocks in one of this account's lists. Two
mechanical tests, both required:

1. `contract_id_ex` must be a **bare integer**. An exchange suffix
   (`12087792@IDEALPRO`) means a non-STK instrument — FX, futures, or an
   option — and is dropped.
2. The `search_contracts` row selected for it (see Broker access above)
   must be US-listed with `STK` among its `sections`.

Log each drop as
`"stage": "screened", "passed_filters": false, "reason": "not a US-listed stock (contract_id_ex \"<value>\") — watchlists can hold FX and other non-equity instruments this pipeline cannot trade"`.
Never try to price or screen one of these: an FX pair fetched as if it
were a stock returns numbers that look plausible and mean nothing.

> **There is no supplementary market scan.** The Robinhood build ran a
> saved relative-volume scan each cycle to surface movers from outside
> the watchlist. The IBKR connector has no scanner — `search_investment_topics`
> and `get_company_themes` are thematic browsing, not quantitative
> screening. **Your watchlist is the entire candidate universe**, and this
> pipeline can no longer discover anything you did not put in front of it.
> Every `screened` line therefore carries `"source": "watchlist"`.
> See `universe.no_market_scan_note`.

**`get_watchlist` already returns the contract id.** Each instrument comes
back as `{"contract_id_ex": "88819736", "contract_description": "NBIS"}`,
where `contract_description` is the ticker and `contract_id_ex` is the id
`get_price_snapshot` and `get_price_history` need — no `search_contracts`
round-trip is required to resolve it.

You still need **one `search_contracts` call per candidate**, but only to
obtain the instrument's descriptive name for the leveraged/inverse filter
below: the watchlist gives the ticker, never the name. Budget for that —
it is one extra call per candidate, every cycle. Apply the exact-symbol
and `country_code == "US"` rules to pick which returned row's
`description` to read.

Then pull a snapshot for the whole candidate list with
`get_price_snapshot`, requesting at least:

```
market_data_names: ["last", "bid_ask", "prior_close", "misc_statistics", "avg_90d_usd_volume"]
```

`misc-statistics` carries the 13/26/52-week highs and lows under the keys
`high_13w`, `high_26w`, `high_52w`, `low_13w`, `low_26w`, `low_52w`, plus
`open_52w`. **Not** `high_52_weeks`/`low_52_weeks` — that is what the
Robinhood build called them and what a reasonable guess would produce;
the real names were verified against a live response.
`avg-90d-usd-volume` is the liquidity figure the universe filter uses,
and it arrives nested as `{"volume": <number>}`.

Use `last.price` as `current_price` in Steps 2–3. **`prior-close` cannot
be relied on as a fallback** — a live check returned it as an empty
object `{}` even while `last` was populated. If `last.price` is null and
`prior-close` is empty, take the final `close` from this candidate's Step
2 `get_price_history` bars instead; if that is unavailable too, drop the
candidate rather than screening it on no price at all.

Filter the list against `risk_rules.json`'s current `universe` block, and
cap the **non-held** portion at `universe.watchlist_max_candidates`.

**Liquidity floor.** Exclude if `avg-90d-usd-volume` is below
`universe.min_avg_90d_usd_volume`. Log as
`"average 90d dollar volume $<X> is below universe.min_avg_90d_usd_volume ($<threshold>) — excluded per universe filters"`.
If the field is missing, exclude rather than admit unfiltered — log
`"90d dollar volume unavailable — excluded, cannot enforce the liquidity floor"`.

> **There is no market-cap filter any more.** The Robinhood build screened
> on a 2B floor and a 50B ceiling. The IBKR connector exposes no market
> cap at all. The liquidity floor above is a genuine substitute for the
> floor, but **nothing substitutes for the ceiling** — if you don't want
> mega-caps traded, keep them off the watchlist. See
> `universe.no_market_cap_filter_note`. Do not attempt to supply a market
> cap from your own knowledge; a screening threshold enforced against a
> remembered number is not a mechanical filter.

`exclude`'s `"penny_stocks"` entry is mechanical, not a judgment call:
exclude if current price < `universe.penny_stock_price_threshold_usd`,
regardless of how the stock is otherwise trading. Log the reason as
`"penny stock (price $<X>, under $<threshold>) — excluded per universe.exclude: penny_stocks"`.

`exclude`'s `"leveraged_etfs"`/`"inverse_etfs"` entries are also
mechanical, but weaker than the Robinhood original — see
`universe.leveraged_inverse_note`. Exclude if the row's `description`
from `search_contracts`, uppercased, contains any entry in
`universe.leveraged_inverse_name_keywords` and does **not** contain any
entry in `universe.leveraged_inverse_name_exceptions`. The keyword list
is multiplier-based (`2X`, `3X`, `LEVERAGE`, `ULTRAPRO`, …) rather than
word-based, because the connector exposes no `stock_type` field: with no
way to tell an ETF from an operating company, bare words like `ULTRA` or
`BULL` would exclude Ultra Clean Holdings and Bullfrog AI. Log as
`"leveraged/inverse ETF (name: \"<name>\", matched \"<keyword>\") — excluded per universe.exclude: <leveraged_etfs|inverse_etfs>"`.
This is a name-pattern heuristic standing in for a prospectus description
the connector doesn't expose. It is deliberately biased toward
over-exclusion, and a false positive is an acceptable cost. **Do not
"correct" it with your own knowledge of what a fund actually holds, in
either direction** — not to rescue a name it caught, and not to exclude
one it missed. The real defence is not putting leveraged products on the
watchlist.

**Always ensure every held position is in the final list**
(`get_account_positions`) — if one already made it through on its own
(e.g. it's also on the watchlist), leave it as-is, don't add a duplicate.
**There is no way to confirm which account this is.** No connector
endpoint returns an account identifier — `get_account_summary`,
`get_account_positions`, `get_account_balances` and `get_account_trades`
were all checked against live responses and none carries one, nor accepts
an account parameter. `risk_rules.json`'s `account_number` is therefore a
record for you, not something this phase can verify. Log the position
count and held symbols as an `account_fingerprint` field on the run so a
human reading the log would notice a swapped account; Phase B's Step 0
carries the actual halt logic (`account_fingerprint` in
`risk_rules.json`). Do not claim to have verified the account.
`watchlist_max_candidates` is a cap on **non-held** candidates only:
exclude held positions from that count entirely before checking whether
the cap was exceeded, so a held position can never occupy a slot or cause
a non-held candidate to be dropped. A held position must stay eligible
for a fresh thesis (including `exit_existing`) and never get silently
dropped for being illiquid or off the list. Log as
`"stage": "screened", "passed_filters": true, "reason": "currently held — always included"`
regardless of what the filters would have said.

(This just builds the candidate list — not a risk/stop-loss check; that's
Phase B's job. See Hard stop below.)

## Step 2 — Gather signals

Pull ~60 days of daily price history per candidate with
`get_price_history` (`security_type: "STK"`, `step: "ONE_DAY"`,
`period: "THREE_MONTHS"`, `outside_rth: false`), called fresh for every
candidate this run. Trim the returned bars to the ones inside the last
**60 calendar days** before using them — `THREE_MONTHS` deliberately
over-fetches so the 60-day window is complete after weekends and
holidays, but the window itself must be 60 calendar days, not 60 bars
(counting back 60 bars drifts to ~85-90 calendar days and overstates the
move).

Never reuse `close_60d_ago`, `latest_close`, or any other
history-derived value from a prior run's `pending_proposals.jsonl` or
`trade_log.jsonl`, even if today's figure looks unchanged from
yesterday's — every number in `signal_check` must come from this run's
own tool call.

**Do not compute the signal ratios yourself.** Pipe the trimmed bars into
the script:

```
echo '{"history": <the get_price_history response object, VERBATIM>,
       "high_52_weeks": <misc-statistics.high_52w, or null>,
       "low_52_weeks": <misc-statistics.low_52w, or null>,
       "current_price": <from Step 1>}' \
| python3 scripts/signal_check.py \
    --price-move-threshold <signal_thresholds.price_move_60d_pct> \
    --volume-spike-threshold <signal_thresholds.volume_spike_multiple> \
    --pct-from-52wk-threshold <signal_thresholds.pct_from_52wk_extreme>
```

**Pass `get_price_history`'s response through untouched.** It returns
COLUMNAR parallel arrays — `{"time": [...], "close": [...], "volume":
[...], "high": [...], "low": [...]}` — not a list of bar objects, and the
script transposes them itself. Do not hand-build a `bars` list from those
arrays: pairing a close with the wrong index's volume is silent, produces
a plausible-looking number, and is exactly the failure this avoids. The
script refuses outright if the arrays disagree in length.

Use the script's JSON output directly —
`qualifies`, `triggered`, `signal_check` (log this string verbatim),
`magnitude_score`, `unevaluable`.

The script exists because the connector has no average-volume field: the
Robinhood build read `average_volume_30_days` straight off
`get_equity_fundamentals`, whereas here the baseline has to be computed
from the bars, and this project keeps arithmetic out of the model. It
evaluates the same three criteria as before — 60-day price move, volume
spike against the prior 30 bars (excluding the latest bar from its own
baseline), and distance to the nearer 52-week extreme — and qualifies a
candidate if **any one** is met.

A criterion whose inputs are missing lands in `unevaluable` and simply
doesn't qualify. It is never a reason to substitute a value, and never
suppresses the other two. If all three are unevaluable, treat the
candidate as no-signal.

If `qualifies` is false, no search/thesis this run — log as
`screened`-only. Qualifying candidates' searches stay within
`cadence.news_search_budget_per_cycle` (per run, not per stock; held
positions draw from their own separate budget below, not this one).

**If more candidates qualify than the budget allows**, prioritize by the
script's `magnitude_score` — how far each one exceeded the specific
threshold it tripped, not conviction or `risk_flags` (those don't exist
yet; they're outputs of the search this budget gates, not inputs to it).
Process qualifying candidates in descending `magnitude_score` order,
spending the budget as you go. Any candidate that would push spend past
`cadence.news_search_budget_per_cycle` is skipped this cycle — log
`"stage": "screened", "passed_filters": true, "reason": "news search budget exhausted this cycle (<N> of <cadence.news_search_budget_per_cycle> already spent on higher-magnitude signals) — no thesis this run"`.
It remains a normal candidate next cycle, re-screened fresh (no
carryover priority).

**Exception — held positions always get a fresh thesis**, signal or not.
Run one targeted news search per held position (separate budget from
`cadence.news_search_budget_per_cycle`, bounded by
`max_concurrent_positions`, same pattern as Phase B's Monday weekend-gap
searches) and produce a thesis every run — this is what makes
`exit_existing` reachable, since a slow deterioration with no sharp
signal would otherwise go unnoticed. This matters more here than it did
on Robinhood: with no market scan, a deteriorating held position is one
of the few things this pipeline can still catch on its own. This search
must also cover whether any active lawsuit/regulatory investigation
naming the company has a scheduled ruling, hearing, trial date, or
compliance deadline in the next ~90 days (the `active_litigation`
risk_flags criterion below) — don't rely on it surfacing incidentally
from a catalyst-only query.

## Step 3 — Synthesize thesis

For each flagged candidate, produce the thesis record from `README.md`
(symbol, date, thesis, conviction, invalidation, direction).
- **No price targets.**
- **No forecasting as fact** — "this suggests..." not "this will...".

**`conviction` follows a fixed rubric, not open judgment** — the same
underlying facts must produce the same rating regardless of which day
this runs. Evaluate fresh each run using only what this run's own
research found; never carry forward or average against a prior day's
conviction for the same symbol.

- **`high`** requires **all** of:
  - The catalyst is a specific, already-confirmed, company-disclosed
    event (an earnings result, a signed deal/contract, a completed
    regulatory approval, a disclosed structural risk) — not a rumor,
    analyst opinion, technical pattern, or sector/macro-wide move, and
    not still pending/anticipated (e.g. "ahead of earnings" caps at
    `medium` no matter how bullish/bearish the setup sounds).
  - The thesis explicitly names the strongest available counter-evidence
    (a plausible positive if bearish, a plausible negative if bullish)
    and gives a concrete reason it doesn't change the read — silence on
    the counter-case, or listing it without resolving it, doesn't
    qualify. ("...regardless of X" / "even though X" / "even with X" —
    not just piling on more confirming evidence.)
  - `risk_flags` is empty (see below).
  - No unresolved binary catalyst (earnings date, court ruling,
    regulatory deadline) falls before this position's next likely
    review that could reverse the read.
- **`low`** applies if **any** of:
  - The thesis itself frames the evidence as mixed, offsetting, or
    unresolved (e.g. "mixed," "offset by," "still isn't fully
    confident," "unpredictable") rather than reaching a clear net read.
  - The move is explained as technical, mechanical, or sentiment-driven
    in a way that discounts its fundamental significance (e.g. "largely
    mechanical," "sentiment-driven rather than a disclosed fundamental
    deterioration").
  - Any `risk_flags` entry is present.
  - The catalyst is macro/sector-wide rather than company-specific
    (e.g. "broad rotation," "sector sentiment").
- **`medium`** is everything else: a real, credible, company-specific
  catalyst exists and doesn't hit a `low` disqualifier, but the catalyst
  is still pending, or multiple contributing factors are listed without
  one clearly resolved as dominant, or no counter-case is explicitly
  engaged and dismissed.

**For a held position**, `direction` is `"long"` (still supports holding)
or `"exit_existing"` (no longer does) — never `"avoid"` (that's only for
not-yet-held candidates).

**Include `risk_flags`** for every `direction: "long"` candidate — an
array of zero or more tags from this fixed set, based only on what this
run's sourced research already found (no extra searches):
- `"active_litigation"` — an active lawsuit or regulatory investigation
  naming the company or an executive, with a specific scheduled ruling,
  hearing, trial date, or compliance deadline within the next ~90 days.
  An open-ended investigation or long-running dispute with no scheduled
  next step doesn't qualify on its own (most large companies have one
  of these at any given time) — mention it in the thesis narrative if
  relevant, but don't flag it.
- `"dilution_risk"` — a completed or pending equity/convertible raise,
  share offering, or ATM program disclosed in the last ~90 days.
- `"insolvency_or_liquidity_concern"` — bankruptcy rumor, going-concern
  language, or reliance on an external backer to remain solvent.
- `"leadership_turnover"` — a C-suite departure/replacement in the last
  ~90 days tied to operational or execution problems (not routine
  succession).
Empty array (`[]`) if none apply. Used by Phase B (Step 5) as the
primary within-tier tie-break, ahead of `pct_below_52wk_high`.

**Include `pct_below_52wk_high`** for every `direction: "long"` candidate:
`(high_52w - current_price) / high_52w` (e.g. `0.15`), taking
`high_52w` from Step 1's `misc-statistics` and `current_price` from
Step 1's snapshot. Used by Phase B (Step 5) as the secondary within-tier
tie-break, after `risk_flags` — a disclosed "room in the setup" proxy,
not a fair-value calc. Omit for `avoid`/`exit_existing`, and **omit
rather than estimate** if `high_52w` was unavailable.

**Include a `sources` field** listing outlet name + URL for every search
result that informed this thesis (e.g.
`["Reuters: https://...", "Company Q2 press release: https://..."]`) —
this is what makes the reasoning step auditable later instead of just
trusted. Prefer primary sources (company filings/press releases, wire
services like Reuters/AP) and major outlets (Bloomberg, WSJ, CNBC, etc.)
over aggregator/content-farm sites when both turn up in the same search;
if only a lower-tier source is available, use it and cite it rather than
omitting the field.

## Output

**Overwrite `pending_proposals.jsonl` at the start of this run** — it
should hold only today's candidates; history remains auditable via
`trade_log.jsonl`, which Phase B writes to when acting on a proposal.

Every line needs a real `"timestamp"` (`HH:mm:ss`, e.g. via
`TZ='America/Chicago' date +'%H:%M:%S'` — never guessed) alongside
`"date"`. Time-of-day only, no date prefix. For human readability only —
never used for idempotency or other logic.

Write:
- One `"stage": "screened"` line per candidate (`passed_filters`,
  `source` (always `"watchlist"`), `avg_90d_usd_volume`, `contract_id`,
  `reason` if rejected — shape matches `trade_log_template.jsonl`), plus
  `"signal_check"` copied **verbatim from `signal_check.py`'s output**,
  which already pairs each ratio with its raw inputs so the arithmetic is
  checkable. Do not reformat, round, or re-derive that string, and log
  `"none"` when the script returns it.
- One `"stage": "thesis"` line per flagged candidate (shape matches
  `trade_log_template.jsonl`), plus `pct_below_52wk_high` for `long`
  candidates (Step 3).

Do not touch `trade_log.jsonl` — reserved for Steps 4–7 (Phase B), which
reads `pending_proposals.jsonl` separately.

**After all `screened`/`thesis` lines, append one `"stage": "summary"`
line per decision bucket** (to `pending_proposals.jsonl`) — a plain
symbol list per bucket for at-a-glance readability. Phase B only reads
`"stage": "thesis"` entries, so these are inert to it. Always all five
buckets, in order, even if empty:

```json
{"date": "YYYY-MM-DD", "timestamp": "HH:mm:ss", "stage": "summary", "decision": "rejected", "symbols": ["AMC", "ADDYY"]}
{"date": "YYYY-MM-DD", "timestamp": "HH:mm:ss", "stage": "summary", "decision": "no_signal", "symbols": ["TSLA", "NVDA", "..."]}
{"date": "YYYY-MM-DD", "timestamp": "HH:mm:ss", "stage": "summary", "decision": "avoid", "symbols": ["SPCX", "LCID", "..."]}
{"date": "YYYY-MM-DD", "timestamp": "HH:mm:ss", "stage": "summary", "decision": "long", "symbols": ["AAPL (medium)", "AMD (high)", "..."]}
{"date": "YYYY-MM-DD", "timestamp": "HH:mm:ss", "stage": "summary", "decision": "exit_existing", "symbols": []}
```

`rejected` = failed universe filter. `no_signal` = passed filters, no
Step 2 signal/thesis. `avoid`/`long`/`exit_existing` = matches the
thesis's `direction`. Plain symbol lists throughout, except `long`
appends each symbol's own thesis `conviction` as `"<symbol>
(<conviction>)"` — the one bucket where it drives sizing; the others
carry a conviction too, it's just not decision-relevant there. No other
reason/detail fields — a quick-glance list, not a substitute for the
thesis lines.

## Hard stop

Do not call `create_order_instruction`, `delete_order_instruction`, or any
watchlist/alert **write** tool (`create_watchlist`, `edit_watchlist`,
`delete_watchlist`, `create_alert`, `update_alert`, `set_alert_status`,
`delete_alert`), and do not check `execution.mode`. `get_watchlist` is
read-only and expected; editing the watchlist is the human's job, not
this pipeline's. `get_account_positions` is for Step 1's candidate list
only — no stop-loss/drawdown computation here; all risk enforcement is
Phase B's job.
