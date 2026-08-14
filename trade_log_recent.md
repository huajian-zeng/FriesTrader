# 2026-08-14

## ⚠ 4 instructions awaiting your approval in IBKR

Review them all at:
<https://ndcdyn.interactivebrokers.com/sso/resolver?action=ACCT-MGMT-MAIN#/orders/instructions>

- **BUY 0.2178 MSFT** ($498.10 ask, $108.49, high conviction) — expires 2026-08-21
- **BUY 0.1309 DELL** ($496.99 ask, $65.06, medium conviction) — expires 2026-08-21
- **BUY 0.0998 ALAB** ($325.88 ask, $32.52, low conviction) — expires 2026-08-21
- **BUY 0.0947 COHR** ($343.50 ask, $32.53, low conviction) — expires 2026-08-21

**Nothing has executed.** These are drafts sitting in IBKR's AI Instructions
queue. No money moves until you open the app and tap *Review & Submit* on each
one. If you leave them, they disappear on their own on **2026-08-21** — and an
expiry is not a decision, it just means the queue went unread.

That link is the queue page, the same for all four — not a deep link to any one
instruction.

This is the first cycle that has ever put anything in your queue.
`execution.mode` went to `live` on 2026-08-13 and yesterday's dry run satisfied
`dry_run_min_cycles_before_live` (1 of 1), so the gate opened today.

## Instruction queue reconciliation

Queue was empty at the start of the cycle. Yesterday's four `instruction`
entries were all `dry_run` with `created: false` — `create_order_instruction`
was never called for them, so they never reached IBKR and there was nothing to
resolve. **No approval, decline, or expiry was inferred**, and no equity fills
appeared in the 7-day trade history.

## Account

Net liquidation **$542.44**, inside the `[400, 900]` fingerprint band. **0** open
positions, **$542.00** USD cash (plus AED 1.62). The fingerprint is a tripwire,
not an account check — no connector endpoint returns an account identifier, so
`account_number` was **not** verified and cannot be.

## Loss-limit check

Daily realized **$0.00 (0.00%)**, weekly realized **$0.00 (0.00%)**, 0 trades in
the week. **Entries not halted.** The only trade in the 30-day window is the
2026-08-12 AED→USD conversion, dropped as a non-USD row.

## Stop-loss / take-profit

No open positions, so neither check had anything to evaluate this cycle.

## Candidates considered (6 long proposals from Phase A's 2026-08-13 run)

All six returned live REALTIME quotes; today is Friday, so the Monday-only
weekend-gap search did not run.

**Queued (4) — cap filled in ranked priority order:**

| Symbol | Conviction | Size | Fresh price | Shares |
|---|---|---|---|---|
| MSFT | high | $108.49 | $498.20 | 0.2178 |
| DELL | medium | $65.09 | $496.04 | 0.1309 |
| ALAB | low | $32.55 | $324.65 | 0.0998 |
| COHR | low | $32.55 | $343.29 | 0.0947 |

Cash after all four would be **$303.76** (56.0% buffer, well clear of the 10%
floor); `max_concurrent_positions` (4) exactly filled.

**Dropped on the fact check (1) — CORT.** See below.

**Rejected on slots (1) — AMD.** Carries the sizing script's own
`concurrent_positions_after (5) exceeds max_concurrent_positions (4) — cap
filled by higher-priority candidates this cycle`. Scarcity, not quality.

## Why CORT was dropped

Phase A's thesis rests on "a raised 2026 revenue outlook of **$950M–$1.05B**".
That range is real, but it is the **superseded** guidance Corcept raised to back
at Q1 (up from $900M–$1B). The Q2 release the thesis is actually built on raised
full-year 2026 guidance **again, to $1.1B–$1.2B**. The thesis quotes a stale
range as the current outlook and anchors its own invalidation trigger ("revenue
tracking below the $950M low end of company guidance") to a floor the company no
longer guides to.

Everything else in that thesis checked out — Q2 revenue $256.1M (+32%),
relacorilant already approved in platinum-resistant ovarian cancer and selling as
LIFYORLI ($47.6M in the quarter), the Cushing's decision set for Dec 17, 2026.

Note the error runs in Corcept's *favour*: guidance is higher than the thesis
claims. It was dropped anyway. The fact check turns on whether a disclosed figure
the thesis rests on is contradicted, not on which direction the error points —
the same rule that would have caught the Cerebras miss-called-a-beat. CORT is not
blocked; it re-enters normally through Phase A's screening.

## Worth your eye before you tap

- **Concentration, again.** Three of the four queued names are AI infrastructure
  (MSFT cloud/AI, ALAB AI interconnect, COHR AI optical), and DELL is AI servers.
  That is effectively four expressions of one trade. `risk_rules.json`
  deliberately has no correlation limit and expects this to be caught at your
  approval tap. You do not have to approve all four.
- **COHR gapped +3.9%** overnight (330.40 → 343.29) and **AMD +3.5%**
  (485.00 → 502.17). Both were re-checked against their theses' stated
  invalidation criteria; neither has triggered, since both hinge on a next
  quarterly report that has not landed. COHR's move traces to a reported FCC
  proposal to ban Chinese optical transceiver imports plus sector strength after
  Lumentum; AMD's to post-Q2 optimism and a Baird target raise — sentiment and
  analyst opinion, not new disclosure.
- **COHR's print is now quantified.** Phase A's thesis said no source it read
  gave the headline figures. This run found them: FQ4 revenue $2.05B against a
  ~$1.99B consensus, non-GAAP EPS $1.74 against ~$1.61, and FQ1 guided to
  $2.2–2.4B against a ~$2.14B consensus. That supports the thesis's qualitative
  read rather than contradicting it — but it is a low-conviction name whose
  thesis was written without the numbers in hand.
- **No intraday stop protection exists** on this route. The connector has no stop
  order type, stops are evaluated once per day here, and even a triggered stop
  only becomes another instruction waiting for your tap. Anything you approve
  today can gap down tomorrow morning and stay held until you next open the app.

## Guard coverage — read this as partial

- **Wash-sale guard is incomplete.** `YOUR_OTHER_ACCOUNT_ID_HERE` is not
  reachable through the IBKR connector and was not checked. An account that could
  not be checked is not an account that came back clean. On the connected
  account, no loss sale of any candidate symbol appeared in the 30-day window.
- **Loss limits see one account only**, for the same reason.

---
`trade_log.jsonl` is the source of truth. If this file and it ever disagree,
trust `trade_log.jsonl`.
