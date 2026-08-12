# Phase B — Re-verify, Risk Enforcement, Order Instructions, and Logging (Automated Daily Task)

Automated second half of this pipeline (see `README.md`), run every
weekday 8:35am Central (5 min after 9:30am ET open) as a scheduled
routine. Performs **Steps 4–7**, consuming candidates from Phase A's
`pending_proposals.jsonl`.

**This phase cannot execute a trade.** The IBKR connector's
`create_order_instruction` produces a **draft** that sits in IBKR's AI
Instructions queue until the human opens the IBKR app and taps *Review &
Submit*. Nothing here reaches the market on its own. Read
`execution.mode_semantics_note` before assuming `"live"` means what it
meant on Robinhood — here it means "instructions reach the queue".

That changes what the gates are for, but not whether they apply. Every
mechanical rule below still runs in full, and a candidate that fails one
must never reach `create_order_instruction` — the human's tap is a second
check on top of the rules, never a substitute for them. Do not add,
remove, or loosen any gate condition on your own judgment.

## Broker access — the IBKR connector

Same two mechanics as Phase A, both of which bite immediately:

**1. Everything is keyed by `contract_id`.** Resolve each symbol once per
run with `search_contracts`. Two conditions, **both** required: `symbol`
matches the ticker exactly, **and** `country_code == "US"`. Exact symbol
match alone is not enough — a live search for "AAPL" returned four rows
whose symbol is exactly "AAPL" (NASDAQ/US, MEXI/MX, EBS/CH, and a
Canadian CDR), alongside look-alikes AAPU/AAPB/AAPD. Reuse the id across
calls, and drop any symbol that doesn't resolve to exactly one US match.

**2. Response keys are hyphenated where request names are underscored.**
`misc_statistics` → `misc-statistics`, `bid_ask` → `bid-ask`. Reading the
underscored form returns nothing, which is indistinguishable from missing
data — and missing data triggers fail-safe behaviour below, so do not
confuse the two.

If a call fails or returns nothing usable, that is a failure. Where this
spec says to fail safe, that is exactly the condition meant.

## Step 0 — Load state (do this first, every run)

1. Read `risk_rules.json` **fresh** — never cache across runs. Use its
   `account_number`, not a hardcoded value.
2. **Preflight.** Call `get_account_summary`. If it fails, the connector
   is not available (a scheduled/headless run may not have it — see
   `README.md`). Log a `cycle_summary` noting the failure and stop.
   **Create nothing.**

   **Account identity cannot be verified — use the fingerprint instead.**
   No connector endpoint returns an account identifier: `get_account_summary`,
   `get_account_positions`, `get_account_balances` and `get_account_trades`
   were each checked against live responses and none carries one, nor
   takes an account parameter. Watchlists are no help either — they are
   user-level and stay byte-identical across an account switch. So
   `risk_rules.json`'s `account_number` is a record for the human, not a
   check this phase can perform. **Never state or log that the account was
   verified.**

   When `account_fingerprint.enabled` is true, apply it as a tripwire:
   - Halt the cycle if `net_liquidation` falls outside
     `account_fingerprint.expected_net_liquidation_usd`.
   - Halt if `account_fingerprint.expected_symbols` is non-empty and
     `get_account_positions` holds none of them.
   - Either way, log
     `"stage": "account_fingerprint", "net_liquidation": <X>, "position_count": <N>, "symbols": [...]`
     **every cycle**, halt or not, so a swapped account is visible in the
     log even when the band is set wide.

   This cannot distinguish two accounts of similar size. It is a
   tripwire, not a guarantee, and must be described that way.

   **A zero-value account is normal, not an error.** An unfunded account
   returns `net_liquidation: 0`, `positions: []` and `trades: []`. Every
   check below runs; `position_sizing.py` rejects every candidate with
   "account total_value is $0.00" and the cycle logs a clean no-op.
3. Determine today's day of week mechanically (e.g.
   `TZ='America/Chicago' date +'%A'`) — don't infer it from the date
   string. Needed for Step 4's weekend-gap check.

   **Market-hours guard — check the clock, don't trust the schedule.**
   Read the current time with `TZ='America/Chicago' date +'%H:%M'` and
   **stop the run** unless it falls between **08:30 and 15:00** Central,
   on a weekday. Log
   `"stage": "cycle_summary", "halted": true, "reason": "ran at <HH:MM> Central, outside the 08:30-15:00 regular session — Phase B requires live opening-session quotes"`
   and create nothing.

   This exists because the schedule cannot be trusted to stay correct.
   Cloud cron fires on a fixed UTC expression while Central time shifts
   with daylight saving: a `35 13 * * 1-5` cron is 08:35 Central in summer
   and **07:35 Central in winter — 55 minutes before the market opens**.
   Nothing else in this pipeline would notice. Quotes would come back
   pre-market, the `data_type` check would reject every candidate, and the
   cycle would log a clean-looking no-op every single day until someone
   thought to look. Fix the cron when the guard starts firing; the guard
   is what makes that failure visible instead of silent.
4. **Reconcile the instruction queue (do this before anything else
   reads a position).** Instructions this pipeline created on earlier
   cycles may since have been approved, declined, or left sitting. Call
   `get_order_instructions` and `get_account_trades` (period `DAYS_7`),
   and for every `"stage": "instruction"` entry in `trade_log.jsonl` not
   yet resolved, decide which of three happened:

   - **Still listed in `get_order_instructions`** → still pending. Leave
     it for the staleness rules in Step 6. Log nothing new.
   - **Gone from the queue, and a matching fill appears in
     `get_account_trades`** → the human approved it and it executed.
     Append `"stage": "order", "resolved_from_instruction": true,
     "placed": true`, copying the fill's `price`, `size`, `commission`,
     `trade_time` and **`realized_pnl` straight from `get_account_trades`**.

     IBKR returns a per-trade `realized_pnl` (0 on buys, the real figure
     on sells) — verified against live responses, **despite that field
     being absent from the connector's own tool description**. Do not
     compute it from average cost; the broker's number is authoritative
     and already nets commission.
   - **Gone from the queue with no matching fill** → it was either
     declined or it expired, and **these are different events that must
     not be logged as one**. Instructions expire 7 days after creation, so
     compare today against the `expiration` recorded on the instruction
     entry:
     - **Past `expiration`** → it timed out unattended. Append
       `"stage": "order", "resolved_from_instruction": true, "placed":
       false, "reason": "instruction expired unapproved after 7 days"`.
       This is not a decision the human made; it means the queue went
       unread. Surface it prominently in the recap.
     - **Before `expiration`** → the human actively declined it. Append
       `"reason": "instruction removed from the queue before expiry —
       declined by the human"`.

     **Do not re-propose either case this cycle on that basis alone.** A
     decline is a deliberate human override of a mechanical rule (see
     `execution.declined_instruction_note`); the candidate re-enters
     normally through Phase A's screening, nothing more.

   Do this before Step 4 and Step 5 so they see the real current position
   rather than one this log still claims exists. Apply the wash-sale flag
   rules (Step 5) to any resolved sells here too — a loss realized on an
   approval you tapped yesterday is still a loss that may be disallowed.
5. Read `pending_proposals.jsonl` (overwritten each Phase A run, holds only
   the latest run — use its `"stage": "thesis"` entries directly as
   today's candidates). If missing or empty, log a `cycle_summary` noting
   nothing to process and stop — don't error. Step 0's reconciliation
   above still counts as work done and must be written first.
6. Read `trade_log.jsonl` (if present):
   - **Idempotency — key off the proposal's own `date`, not today's.**
     Skip a candidate if `trade_log.jsonl` already has a `risk_check`/
     `instruction`/`order` entry for that symbol with a matching
     `proposal_date` (not the entry's top-level `date`, which reflects
     when the decision was made and changes daily even for a stale
     proposal). This matters because if Phase A ever fails to run, an
     un-refreshed proposal would otherwise look "new" every day and could
     be re-proposed repeatedly; keying off `proposal_date` means it's
     decided once. `stop_loss`/`take_profit` are exempt — always run fresh.
   - **Dry-run cycle count**: number of **distinct dates** with a
     `cycle_summary` entry where `mode: dry_run` — not raw entry count
     (same-day reruns count once). This represents validated days, not
     executions, and must be
     `>= execution.dry_run_min_cycles_before_live` before Step 6's
     instruction gate can open.

## Step 4 — Re-verify proposals against fresh opening data

**Resolve sells and classify candidates (do this first):**
1. Run Step 5's stop-loss and take-profit checks now (pull
   `get_account_positions` and fresh `get_price_snapshot` quotes, resolve
   any triggered sells) — needed before knowing current slot occupancy.
2. Process any `direction: "exit_existing"` candidates now too (through
   the staleness check below, then to Step 6 as a sell) — selling is
   never gated.
3. Split remaining `direction: "long"` candidates:
   - **new**: not a live open position — a genuine new entry, the only
     kind that consumes a slot.
   - **held**: already a live open position — a potential top-up (Step 5).
     Top-ups never consume a slot and are always considered regardless of
     account fullness.
4. `open_slots = max_concurrent_positions - (live positions per
   get_account_positions, excluding sells just resolved)`. Only **new**
   candidates consume a slot; fixed for the cycle unless one gets
   approved in Step 5.

   **Count a pending unapproved BUY instruction as an occupied slot.** It
   represents exposure you have already committed to and may approve at
   any moment; treating it as free would let the pipeline queue up more
   new entries than `max_concurrent_positions` permits, and approving them
   all would breach the cap with no rule ever having been violated on
   paper.
5. **If `open_slots <= 0`**: no **new** candidate can be approved this
   cycle. Skip the weekend-gap search, staleness check, and Step 5 work
   for every **new**-group candidate — log instead:
   `"stage": "risk_check", "passed": false, "proposal_date": "<candidate's date from pending_proposals.jsonl>", "reason": "no open slots this cycle (X of Y max already held/pending/approved) — skipped without staleness re-check"`.
   **held** group is unaffected.
6. **If `open_slots > 0`**: **new** group continues normally (slots may
   still run out mid-Step-5 via ordinary per-candidate concurrency check).

For every **new** candidate not short-circuited by 5, and every **held**
candidate (always):

### Weekend gap (Monday runs only)

A Friday proposal is staler than an overnight one — 2.5 days vs ~16
hours. **If today is Monday**:

1. Before the price-staleness check, run **one additional targeted search
   per pending proposal** covering Saturday/Sunday (earnings, M&A,
   guidance, macro) — separate from and not counted against
   `cadence.news_search_budget_per_cycle`. Same sourcing rules as Phase
   A's thesis `sources` field (prefer primary/major-outlet sources; cite
   whatever you used).
2. If anything materially contradicts the thesis/invalidation criteria,
   drop it — log
   `"stage": "risk_check", "passed": false, "proposal_date": "<candidate's date from pending_proposals.jsonl>", "reason": "weekend news invalidated thesis: <what you found>", "sources": ["Outlet Name: https://..."]`
   — don't process further.
3. If nothing turns up, proceed to the price-based check.

Other weekdays: skip straight to the price-based check.

### Price-based staleness check (every day)

Pull a fresh quote (`get_price_snapshot`, `market_data_names: ["last",
"bid_ask", "prior_close"]`) — re-verify against this morning's open, not
Phase A's prior-close price. If the price gapped significantly, re-check
against the thesis's `invalidation` criteria — same sourcing rules as
above, cite whatever explains the gap in a `"sources"` field on the
resulting log line; if the gap plausibly invalidates it, drop it as above.

**If no `last` or bid/ask comes back**, drop the candidate with
`"reason": "no live quote available — cannot re-verify against a fresh open price"`
rather than falling back to `prior_close`. Phase A may use the prior
close because it runs after the bell; this phase exists specifically to
re-check against a *fresh* price, and substituting yesterday's close here
would defeat the entire step.

## Step 5 — Mechanical risk enforcement

**Stop-loss check (always runs, independent of new candidates):** Pull
current `get_account_positions` and fresh `get_price_snapshot` quotes for
every open position.

**`get_account_positions` field names are not the obvious ones** —
verified against a live response. Average cost is **`average_price`**,
not `average_cost`. The ticker is **`contract_description`** (its value
is the symbol, e.g. `"ALAB"`, despite the name suggesting prose), not
`symbol`. Quantity is **`position`**, and it can be fractional
(`1.721`) on a fractional-enabled account. Also present: `contract_id`,
`market_price`, `market_value`, `unrealized_pnl`, `daily_pnl`,
`asset_class`. Feed `average_price` to `stop_loss.py --average-cost`.

> **Know what this check is and isn't.** `create_order_instruction`
> supports MARKET and LIMIT only — **there is no stop order type** — so no
> resting stop sits at the broker. This is a once-a-day evaluation, and
> even when it triggers, the resulting sell is only an *instruction*
> awaiting your tap. A position can gap down hard at 10am and stay held
> until you next open the app. See `stop_loss.no_intraday_protection_note`.

**Gather inputs, then let the script decide — do not hand-compute the
reference price, drawdown, stdev, or clamp.** For each position:
- Check `trade_log.jsonl` for whether any `take_profit` tier has fired
  for this position's current holding period (same "since quantity
  last reached zero" scope as the take-profit check below).
- If a tier has fired, pull daily `high` bars via `get_price_history`
  (`step: "ONE_DAY"`) from the holding period's entry date (the buy that
  started it from zero) through yesterday, for `--daily-highs`.
- If `risk_rules.json`'s `stop_loss.mode` is `"volatility_scaled"` and
  the position is not currently showing a gain on average cost, pull the
  last `stop_loss.volatility_lookback_trading_days` trading days of daily
  closes via `get_price_history` (`step: "ONE_DAY"`, `period:
  "ONE_MONTH"` to cover weekends/holidays), oldest first through
  yesterday, for `--daily-closes`. Skip this pull on a gain — the script
  itself also skips the computation in that case, since a non-positive
  drawdown can never meet a positive `stop_pct`.

Run:
`python3 scripts/stop_loss.py --average-cost <avg cost> --current-price <fresh quote> --mode <stop_loss.mode> --hard-stop-pct <stop_loss.hard_stop_pct> --volatility-multiplier <stop_loss.volatility_stdev_multiplier> --min-stop-pct <stop_loss.min_stop_pct> --max-stop-pct <stop_loss.max_stop_pct> --fallback-stop-pct <stop_loss.fallback_stop_pct> --min-bars 10 [--daily-closes <comma-separated closes>] [--take-profit-tier-fired --daily-highs <comma-separated highs> --trailing-high-since <entry date>]`
and use its JSON output directly (`stop_reference_basis`,
`stop_reference_price`, `drawdown_pct`, `stop_pct_used`, `stdev_20d`
when computed, `fallback_reason` when the fallback applied,
`triggered`, `action`) rather than recomputing any of it. This only
changes what the stop protects — it does not affect the take-profit
gain calculation below, which always measures gain from average cost
regardless of `stop_reference_basis`.

**If the script fails to run**, do not guess a result: treat this
position as if a loss-limit breach applied this cycle (`entries_halted
= true` for new entries/top-ups, this position itself excluded from
any sell decision) and log `"stage": "stop_loss"` with
`"stop_pct_used": null, "triggered": false, "action":
"halt_entries_check_manually", "notes": "stop_loss.py failed to run —
verify this position's stop manually before next cycle"`. Do not fall
back to manual computation.

If `triggered` is true: immediate full-position sell instruction — no
thesis review, never blocked by a loss-limit halt. Log `"stage":
"stop_loss"` with the script's `stop_pct_used`, `stop_reference_basis`,
and `stop_reference_price` (plus, when trailing, `trailing_high_since`);
when `stop_pct_used` is null, log the script's own `"notes": "gain, stop
not computed"` as-is. Include `stdev_20d`/`fallback_reason` when present.
If triggered, treat as a Step 6 sell candidate. A good thesis never
cancels a stop-loss — see `risk_rules.json`'s note.

**Take-profit check (always runs, independent of new candidates, tiered
partial sells)**: Using the same pull as the stop-loss check (no need to
call again — average cost, quantity, and fresh price as they stood at
the start of Step 5), check `trade_log.jsonl` for `"stage":
"take_profit"` entries for this symbol at each tier's exact `gain_pct`,
logged since the position's quantity last reached zero (a full exit) —
collect the `gain_pct` values already fired this holding period.

**A tier counts as fired when its instruction is created, whether or not
the human approves it** (see `take_profit.tier_fires_once_note`). This is
deliberate: re-firing a declined tier every cycle would override a
decision the human already made, and this pipeline does not get to
overrule an explicit human decline by repetition.

Run:
`python3 scripts/take_profit.py --average-cost <avg cost> --current-price <fresh quote> --quantity <quantity> --tiers <risk_rules.json take_profit.tiers as "gain_pct:sell_fraction" pairs, e.g. "0.15:0.25,0.30:0.25,0.50:0.25"> [--already-fired <comma-separated gain_pct values already fired this holding period>]`
and use its JSON output directly (`gain_pct`, `tiers_status`,
`fired_this_cycle`, `triggered`, `action`) rather than recomputing any
of it — the script already handles the ascending-order,
cascading-quantity logic for **when a single cycle's gain has jumped
past more than one not-yet-fired tier at once**.

**If the script fails to run**, treat it like a stop-loss script
failure: `entries_halted = true` for new entries/top-ups this cycle,
exclude this position from any sell decision, and log `"stage":
"take_profit"` with `"triggered": false, "action":
"halt_entries_check_manually", "notes": "take_profit.py failed to run
— verify this position's tiers manually before next cycle"`. Do not
fall back to manual computation.

If `fired_this_cycle` is non-empty: log one line per entry in it
(already in ascending order) — `"stage": "take_profit",
"tier_gain_pct"`, `"sell_fraction"`, `"quantity_before"`,
`"quantity_sold"` straight from that entry, plus the script's
top-level `"gain_pct"` and `"tiers_status"`, `"triggered": true,
"action": "sell_partial_position"` — and treat each as its own Step 6
sell candidate. No thesis review, never blocked by a loss-limit halt
(it's an exit, not a new entry). If `fired_this_cycle` is empty, log
one line with the script's `gain_pct` and `tiers_status`, `"triggered":
false, "action": "hold_monitor"`. Once all three tiers have fired, the
remaining quantity is held long indefinitely — only the stop-loss
check above still applies to it. Tiers become eligible again only
after the position is fully closed to zero shares and a new entry is
later opened (a genuinely new holding period, not a top-up).

**No same-cycle sell-then-buy**: if a symbol's stop-loss fired or any
take-profit tier fired earlier in this same cycle, it is not eligible
for a top-up this same cycle, regardless of thesis or conviction — drop
it from the **held** group before the merged priority order below,
logging
`"stage": "risk_check", "passed": false, "position_action": "top_up", "reason": "stop-loss/take-profit fired this cycle — not eligible for a same-cycle top-up"`.
This applies unconditionally (dry_run or live) since it's about not
producing a self-contradictory sell-and-buy pair in one cycle — which
would be doubly confusing here, where both would land in your approval
queue side by side. It's a normal top-up candidate again starting next
cycle (subject to the sell re-entry lock below).

**Sell re-entry lock — price-gated, not time-gated, any sell type**:
check `trade_log.jsonl` for this symbol's most recent `"stage": "order"`
entry whose `reason` is any sell (`stop_loss`, `take_profit`, or
`exit_existing`). This lock only applies if that sell **actually
executed** — i.e. an `order` entry with `"placed": true` resolved from an
approved instruction, confirmed against `get_account_positions` showing a
genuinely lower quantity than before it. A `dry_run` entry, or an
instruction the human never approved, never reduced anything and so never
arms the lock; the symbol should be evaluated normally, not dropped. When
the sell did execute and no later `order` entry for that symbol shows a
buy since, the symbol is locked out of any new buy (new entry or top-up)
— including later in this same cycle — until a fresh quote is **at or
below** the price it was sold at (that entry's `fill_price`), no matter
how many cycles or days have passed, and regardless of thesis quality or
conviction. This exists to prevent buying back into a symbol at a worse
price than you just sold it at, whatever the reason for that sell —
averaging up right after trimming or exiting undermines the whole point
of it. Before ranking, pull a fresh quote for any candidate with an
unresolved (actually-executed) sell lock and drop it from the merged
priority order below if the fresh price is above that sell price — log it
as its own line rather than silently omitting it:
`"stage": "risk_check", "passed": false, "proposal_date": "<candidate's date from pending_proposals.jsonl>", "reason": "sell re-entry lock — current price <X> is above the <Y> it was sold at on <date> (reason: <stop_loss|take_profit|exit_existing>)"`.
Once the fresh price is at or below that sell price, the lock clears and
it's eligible again as a normal candidate through Phase A's usual
screening — no separate time-based cooldown on top of this.

**Wash-sale guard (buys only) — cross-account, calendar-gated, separate
from the price-gated lock above:** if `risk_rules.json`'s
`wash_sale_avoidance.enabled` is `false`, skip this guard entirely and
proceed as if it doesn't exist. If `true`: before approving any
**new**-group or **held**-group (top-up) candidate, check for a closing
sale of that symbol realizing a loss within the last
`lookback_window_days` days. Source this from `trade_log.jsonl`'s own
`get_account_trades` (period `DAYS_30`), filtered to that symbol, for any
`SELL` with a negative `realized_pnl` inside the window. Source it from
the broker rather than this pipeline's log, so a loss sale the human made
by hand still arms the guard. If a matching loss sale turns up, drop the candidate before
ranking — log
`"stage": "risk_check", "passed": false, "reason": "wash sale guard -- <symbol> was sold at a loss on <date>, within the <lookback_window_days>-day wash-sale window"`
(add `"position_action": "top_up"` if it's a top-up candidate).

**One hard limit on this guard, which must be logged every cycle, never
silently tolerated** (see `wash_sale_avoidance.linked_accounts_note`):
the IBKR connector exposes only the account it is connected to —
`get_account_trades` and `get_account_positions` take no account
parameter. For every entry in `linked_accounts` other than the connected
one, log
`"wash_sale_guard_incomplete": true, "unchecked_accounts": [...], "notes": "these linked accounts are not reachable through the IBKR connector and could not be checked — the wash-sale guard is incomplete this cycle"`.
**An account that cannot be checked is not an account that came back
clean.** Do not treat it as one, and do not let the log imply a
cross-account check that did not happen.

This guard never applies to stop_loss/take_profit/exit_existing sells —
selling is never gated by tax considerations, only buying is (see the
flag-only check just below for the sell side).

**Wash-sale flag on sells (informational only, never blocks a sell):**
whenever a stop-loss triggers, a take-profit tier fires, an
`exit_existing` sell is processed, or Step 0 resolved an approved sell,
and that specific sale realizes a loss (a stop-loss sell is always a loss
by definition; check the others case by case against
that trade's own `realized_pnl` from `get_account_trades`), check for a purchase of that
symbol within `lookback_window_days` days before today.

A qualifying purchase alone is not enough to flag — the wash-sale rule
disallows the loss by rolling it into the cost basis of stock you still
hold, so if nothing of that symbol remains held after this sale, there is
no replacement position for a disallowed loss to attach to and it is not
a wash sale, whatever the calendar gap. Concretely: a single purchase
fully closed out by this same sale is an ordinary closed round-trip, not
a wash sale — do not flag it. Before adding the flag, call
`get_account_positions` and confirm a nonzero quantity of the symbol
still remains after this sale, sourced from a purchase inside the
lookback window (a genuine surviving replacement lot, not the shares this
sale just closed out). Only then add
`"wash_sale_flag": true, "wash_sale_note": "possible wash sale -- <symbol> was bought on <date>, within <lookback_window_days> days of this sale, and a replacement position remains held -- this loss may be disallowed for tax purposes"`
to that sell's `order` log entry. Purely informational for the human's
own tax reconciliation — it never blocks, delays, or resizes the sell
itself, and it does not require `wash_sale_avoidance.enabled` to be
`true` (the flag is a record of what happened, not a guard against future
action, so it stays on even if the buy-side guard is toggled off). Note
the asymmetry this can't fix: a sell logged clean today can still become
a wash sale later if any account you control buys the same symbol
afterward — outside this pipeline's visibility, and now more so, since it
can only see one account at all.

**Loss-limit halt check (always runs, gates all new entries and top-ups):**
Call `get_account_trades` (period `DAYS_30`) and pipe the response
**verbatim** into the summing script — the whole `{"trades": [...]}`
object, not a hand-extracted subset:

```
echo '<the get_account_trades response, VERBATIM>' \
| python3 scripts/realized_pnl.py --today <TZ='America/Chicago' date +%F>
```

The script converts each `trade_time` from UTC to America/Chicago before
bucketing. **This matters and is not optional**: an extended-hours fill
at 01:30Z is 20:30 the *previous* Chicago day, so bucketing on the raw
UTC date would put it in the wrong day and mis-state both limits. It also
drops non-USD rows (FX conversion trades are not trading P&L) and reports
anything it skipped.

Then feed its two totals to the limit check — **do not hand-compute the
percentages**:

```
python3 scripts/pnl_pct.py \
  --daily-realized-usd <daily_realized_usd> \
  --weekly-realized-usd <weekly_realized_usd> \
  --starting-capital-usd <risk_rules.json starting_capital_usd> \
  --daily-limit-pct <loss_limits.daily_loss_limit_pct_of_account> \
  --weekly-limit-pct <loss_limits.weekly_loss_limit_pct_of_account>
```

and use its JSON output (`daily_pnl_pct`, `weekly_pnl_pct`,
`entries_halted`, `halt_reason`) directly. **If either script fails to
run, fail safe: treat as breached** (`entries_halted = true`) rather than
falling back to manual computation. Halts both new entries and top-ups (a
top-up still spends cash/exposure, even though it skips the concurrency
check). Log as `"stage": "loss_limit_check"`, including
`"source": "get_account_trades"` and the script's `trades_in_week`, so
the figure is traceable.

Because the broker is the source rather than this pipeline's own log,
**sells the human made by hand in the IBKR app count toward these limits
too**. That is correct and deliberate: a realized loss constrains further
risk-taking regardless of who initiated it.

**Candidate priority order — new entries and top-ups compete equally
(decide before any per-candidate check):**
Merge **new** and **held** groups from Step 4 (excluding new-group
candidates already rejected by Step 4's capacity short-circuit) into
one list. **Do not hand-sort or hand-compute any of this — gather the
inputs below and let the scripts decide.**

**Gather, for every candidate in the merged list:** `symbol`,
`conviction`, `risk_flags` (omit the key entirely if the thesis
disclosed none — an omitted key and an empty array mean different
things to the ranking script below), `pct_below_52wk_high` (omit if
not available), `group` (`"new"` or `"held"`), and — for **held**
candidates only — `current_position_value` (quantity from
`get_account_positions` × fresh price). Also gather live `total_value`
and `cash` from `get_account_summary` / `get_account_balances`
(NetLiquidation and total cash; `cash` is the starting `cash_remaining`),
and `concurrent_positions_start` (the live open position count per Step
4's `open_slots` calc, **including pending unapproved buy instructions**,
before this cycle's approvals).

Rank the candidates, then size them — pipe the candidate list (a JSON
array) through both scripts in sequence (directly chainable):
`python3 scripts/rank_candidates.py | python3 scripts/position_sizing.py --total-value <total_value> --cash-start <cash> --concurrent-positions-start <concurrent_positions_start> [--entries-halted] --max-position-pct <position_sizing.max_position_pct_of_account> --max-concurrent-positions <position_sizing.max_concurrent_positions> --min-cash-buffer-pct <position_sizing.min_cash_buffer_pct> --min-top-up-usd <position_sizing.min_top_up_usd> --min-top-up-pct-of-target <position_sizing.min_top_up_pct_of_target> --conviction-pct "high:0.20,medium:0.12,low:0.06"`
`rank_candidates.py` sorts by conviction tier first (`high` before
`medium` before `low`), then `risk_flags` count ascending within a
tier (a missing `risk_flags` field sorts last, treated as worst
case), then `pct_below_52wk_high` descending (a missing field sorts
last in its tier) — a high-conviction top-up can end up ranked ahead
of a lower-conviction new entry and vice versa.
`position_sizing.py` then processes strictly in that ranked order,
compounding the running cash/concurrency totals as each candidate is
approved. Pass `--entries-halted` whenever the loss-limit check above
(or a stop-loss/take-profit script failure) halted entries this cycle
— the sizing script then rejects every candidate uniformly with the
standard halt reason and leaves the totals unchanged.

**Log `risk_flags` and `pct_below_52wk_high` as structured fields on
every risk_check entry from this sort — winners and rejections alike**
(the only place this survives, since `pending_proposals.jsonl` is
overwritten daily).

Use the final script's JSON output directly — its `results` array (one
entry per candidate, in ranked order, each carrying `passed`, and
depending on outcome: `reason`, `position_action: "top_up"`,
`dollar_amount`, `current_position_value`, `target_size`, `headroom`,
`concurrent_positions_after`, `cash_remaining_after`,
`cash_buffer_after_pct`) plus `cash_remaining_final` and
`concurrent_positions_after_final` — rather than recomputing any of
it. A **new**-group candidate rejected purely for lack of slots
carries the script's own `"concurrent_positions_after (N) exceeds
max_concurrent_positions (M) — cap filled by higher-priority
candidates this cycle"` wording, to show it's scarcity, not quality.

**If either script fails to run**, do not guess a result: reject every
still-pending candidate this cycle — log `"stage": "risk_check",
"passed": false, "reason": "rank_candidates.py/position_sizing.py
failed to run — no instructions created this cycle, verify manually"`
for each — rather than falling back to manual computation.

For each candidate, log `"stage": "risk_check"` with that candidate's
`results` entry fields verbatim.

Every `risk_check` entry must include `proposal_date` (copied from the
candidate's `"date"` in `pending_proposals.jsonl` — Step 0's idempotency
key) and, for `direction: "long"`, `risk_flags` and `pct_below_52wk_high`
(for auditing the priority sort). Top-up entries must also include
`"position_action": "top_up"`.

`direction: "avoid"` candidates aren't processed further (already logged
in Phase A). `direction: "exit_existing"` candidates for a held symbol
skip all the checks above (selling reduces risk — not blocked by
position/concurrency/cash-buffer/loss-limit checks) and go straight to
Step 6 as a sell.

## Step 6 — Create order instructions (and the instruction gate)

For every candidate that passed Step 5 (stop-loss, take-profit,
exit_existing sells, and approved top-ups):

**1. Convert the dollar amount to shares.** `create_order_instruction`
takes `quantity` in shares; `position_sizing.py` speaks in dollars. Do
not divide by hand:

```
python3 scripts/dollars_to_shares.py \
  --dollar-amount <dollar_amount from position_sizing.py> \
  --reference-price <fresh ask for a BUY, fresh bid for a SELL> \
  [--fractional]
```

Pass `--fractional` if and only if `execution.fractional_shares` is
`true`. If the script returns `"action": "skip"`, log its `reason` as a
rejected `order` entry and move on — never round up to reach one share,
and never fall back to a dollar-denominated order, which this broker does
not accept. Log its `quantity`, `actual_notional`, and `unspent_usd`; the
last one shows how much of the approved size whole-share flooring left
behind, so the log doesn't imply the full amount was ordered.

For sells, quantity comes from the stop-loss (full position) or
take-profit (`quantity_sold`) result directly — no dollar conversion.

**2. Check the queue before adding to it** (see `instruction_queue.note`).
Call `get_order_instructions`. Each queued instruction comes back as —
verified against a live response:

```json
{"id": "100", "contract_id_ex": "787273575", "contract_id": 787273575,
 "side": "BUY", "quantity": 1, "order_type": "MARKET", "tif": "DAY",
 "creation_time": "2026-08-12T11:07:26.283Z",
 "expiration": "2026-08-19T11:07:26.283Z",
 "is_new": true, "symbol": "RKLB"}
```

**Instructions expire on their own, exactly 7 days after creation.**
`expiration` is always `creation_time + 7 days`. Nothing in this pipeline
sets or extends it. Record `expiration` on every `instruction` entry —
Step 0 needs it to tell a decline from an expiry, and without it the two
are indistinguishable.

`symbol` is returned directly, so matching by symbol needs no
`contract_id` lookup. `is_new` was `true` on a freshly created
instruction; its exact meaning is not documented and was not observed
changing, so **do not build any logic on it** — log it if useful, but
never gate a decision on a field whose semantics are a guess.

If a pending instruction already exists for this symbol:
- If `instruction_queue.replace_stale_instructions` is `true` and it is
  older than `instruction_queue.max_instruction_age_cycles`, it was
  priced against a stale quote and sized against a stale balance. Call
  `delete_order_instruction` on it, log `"stage": "instruction", "action":
  "deleted_stale"` with its id and age, then create the fresh one.
- Otherwise leave it and **do not create a duplicate** — log
  `"stage": "instruction", "action": "skipped_duplicate", "reason":
  "an unapproved instruction for this symbol is already queued"`.
  Two instructions for the same symbol sitting in your queue is a way to
  accidentally double a position with two taps.

**3. There is no pre-trade preview.** Robinhood's `review_equity_order`
returned blocking alerts before placement; the IBKR connector has no
equivalent (`whatIfOrder` exists in the TWS API, not here). What replaces
it is the instruction itself — it does not execute — plus **your own
review at approval time**. Before creating a buy instruction, sanity-check
`get_account_balances` shows cash at least equal to `actual_notional`; if
not, log a rejected `order` entry rather than queueing something that
would fail on approval.

**4. Branch on `execution.mode`** (fresh from Step 0) and the dry-run
cycle count:

**Instruction gate — ALL must be true:**
- `execution.mode == "live"`
- dry-run cycle count `>= execution.dry_run_min_cycles_before_live`
- no unapproved duplicate instruction for this symbol (step 2 above)

- **Gate open**: call `create_order_instruction` with `side`
  (`BUY`/`SELL`), the `contract_id_ex` for this symbol (stringified
  `underlying_contract_id` from `search_contracts`), `quantity`,
  `order_type: "MARKET"`, and `time_in_force: "DAY"`.

  **The response is `{"id": "100", "url": "..."}`** — verified against a
  live round-trip. Two things to get right:
  - The field is **`url`**, not `review_url`.
  - **That URL is a generic link to the instructions queue page, identical
    for every instruction.** It is *not* a deep link to this particular
    one. Never present it as "the link to this order" — there is one
    queue, and the human reads it as a list.

  Log `"stage": "instruction", "action": "created", "mode": "live",
  "instruction_id": "<id, a STRING like \"100\">", "expiration":
  "<from get_order_instructions, see below>", "side"`, `"quantity"`,
  `"reference_price"`, `"actual_notional"`, and —
  **for sells** — `"average_cost_at_instruction": <the position's
  `average_price` from get_account_positions, BEFORE this sell>`. Realized
  P&L no longer depends on it (IBKR supplies that directly at resolution),
  but record it anyway: it is the only surviving trace of what the
  position looked like at the moment the decision was made, and without it
  a resolved fill cannot be audited against the reasoning that produced it.

  **Nothing has executed at this point.** Do not log `"placed": true`, do
  not treat the position as changed, and do not report the trade as done.
- `execution.mode == "dry_run"`: log
  `"stage": "instruction", "mode": "dry_run", "would_create": true` and
  stop. **Never call `create_order_instruction` here.**
- `execution.mode == "live"` but cycle count still under threshold: do
  **not** create. Log
  `"stage": "instruction", "mode": "live_blocked_insufficient_cycles", "would_create": true, "created": false`
  with current vs. required count.

Never change `execution.mode` yourself. Never invent/guess a field value —
if a tool call fails, log the failure and skip that candidate. Every
`instruction` entry must carry `proposal_date` (same as Step 5) — Step 0's
idempotency check matches against `risk_check`, `instruction`, or `order`
entries.

## Step 7 — Logging

Append every decision to `trade_log.jsonl` — one JSON line each:
`stop_loss`, `take_profit`, `loss_limit_check`, `risk_check` (pass/fail,
including Step 4's weekend-gap/price-gap rejections and Step 5's top-up
evaluations), `instruction` (created/skipped/deleted this cycle), and
`order` (resolutions of earlier instructions, from Step 0) stages,
matching the shape already in
`trade_log.jsonl`/`trade_log_template.jsonl`. Top-up entries must include
`"position_action": "top_up"`.

Keep `instruction` and `order` distinct and never collapse them.
`instruction` means "queued, awaiting a human"; `order` means "actually
executed, confirmed against a fill". Conflating them would make the log
claim trades that never happened.

**Every line — including the final `cycle_summary` — needs a real
`"timestamp"`** (`HH:mm:ss`, e.g. via `TZ='America/Chicago' date +'%H:%M:%S'`
— never guessed), no date prefix. Separate from `"date"`/`"proposal_date"`
— for readability only, never used for idempotency, dry-run count, or
other logic; only `date` and `proposal_date` are mechanical.

**Always append exactly one final line per run**, even if nothing else
happened:
```json
{"date": "YYYY-MM-DD", "timestamp": "HH:mm:ss", "stage": "cycle_summary", "mode": "dry_run|live", "candidates_considered": N, "instructions_created": N, "instructions_pending_total": N, "instructions_resolved": N}
```
Load-bearing — Step 0's dry-run cycle count depends on this line existing
every run, keyed off `"date"` (distinct dates), not `"timestamp"`.
`instructions_pending_total` is the full queue depth per
`get_order_instructions` after this cycle, not just what this cycle added.

**After appending, regenerate `trade_log_recent.md`** (full overwrite,
not append) — a short, plain-English recap for a quick mobile/GitHub read.

**Lead with what needs your action.** Unlike the Robinhood build, this
cycle's decisions do nothing until you approve them, so the recap's first
line must be the pending count and what is waiting, with the review link
for each:

```
# 2026-07-10

## ⚠ 2 instructions awaiting your approval in IBKR
Review them all at: <the `url` from any create_order_instruction response>
- SELL 3 EXAMPLE (stop-loss, 7.5% drawdown) — expires 2026-07-17
- BUY 2 OTHER ($56.80, medium conviction) — expires 2026-07-17
```

**One link, not one per instruction** — the returned `url` is the queue
page and is identical for every instruction. Give each line its
`expiration` date instead: that is the actionable per-item fact, since an
instruction left untouched for 7 days disappears on its own.

Then, below that, the usual sections covering only what actually happened
this cycle (skip anything empty): anything Step 0 resolved from earlier
instructions (approved and filled, or declined); the loss-limit check
result; each held position's stop-loss/take-profit status (symbol,
`stop_pct` used, gain/drawdown, and whether it triggered, fired a tier, or
is just holding); and each new-entry/top-up candidate considered with its
outcome in one line. This is a readable render of what this cycle already
decided — no new research, no re-deciding anything. Convenience view only,
not a second audit trail: `trade_log.jsonl` is still the source of truth,
and if the two ever disagree, trust `trade_log.jsonl`.

## Hard rules

- Never change `execution.mode` or any `risk_rules.json` value.
- Never call `create_order_instruction` unless Step 6's instruction gate
  is open at that moment.
- **Never report an instruction as an executed trade.** It is a draft
  awaiting a human tap, and every summary, log line, and recap must say
  so.
- A "high conviction" thesis never overrides a failed mechanical check.
  The human's approval tap is a check **on top of** the rules, never a
  substitute for one — a candidate that fails a rule must never be
  queued "to let the human decide".
- If required data can't be retrieved (account, positions, P&L history),
  fail safe — treat the check as failed/halt new entries — and log exactly
  what failed.
- Never re-propose an instruction the human declined, on that basis
  alone. A decline is a deliberate override; treat it as one.
- The wash-sale guard (Step 5) only ever blocks a buy. It must never
  block, delay, or resize a stop_loss/take_profit/exit_existing sell —
  a tax outcome never overrides risk management.
- The wash-sale guard and the loss limits are both partial here: the
  connector sees one account, and realized P&L only covers sells this
  pipeline originated. Log that partiality every cycle; never let it read
  as a complete check.
