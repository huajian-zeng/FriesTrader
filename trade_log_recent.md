# 2026-08-31

## ⚠ 1 instruction awaiting your approval in IBKR
Review it at: https://ndcdyn.interactivebrokers.com/sso/resolver?action=ACCT-MGMT-MAIN#/orders/instructions

- **SELL 0.8489 CORT** (stop-loss, 6.63% drawdown vs a 5.37% stop) — expires **2026-09-07**

Nothing here has executed. This is a draft sitting in IBKR's AI Instructions
queue; it only becomes a real order when you open the app and tap *Review &
Submit*. If you leave it, it disappears on its own on 2026-09-07 — and an
expiry is not a decision, it just means the queue went unread.

## Resolved from earlier instructions
Nothing. The queue was empty at the start of the cycle and `get_account_trades`
(7 days) returned no trades at all, so nothing was approved, declined or
expired since Friday. Every earlier instruction was already resolved on a
previous cycle.

## Loss limits
No realized P&L today or this week (Monday, so the two are the same figure).
Daily 0.00% against a 5% limit, weekly 0.00% against 10%. **Entries not
halted.**

Partial by construction: the connector only sees the account it is connected
to, so realized P&L in any other linked account is invisible to these limits.

## Held positions — stop-loss / take-profit

| Symbol | Avg cost | Price now | Drawdown / gain | Stop used | Outcome |
|---|---|---|---|---|---|
| **CORT** | 121.75 | 113.67 | **−6.63%** | 5.37% | **STOP TRIGGERED — full-position sell queued** |
| DELL | 497.02 | 466.46 | −6.15% | 10.84% | holding |
| ALAB | 307.23 | 295.00 | −3.98% | 12.76% | holding |
| MSFT | 503.62 | 509.75 | +1.22% | n/a (in gain) | holding |

No take-profit tier fired anywhere — every position is well below the first
15% tier.

Worth remembering: there is **no resting stop at the broker**. The connector
has no stop order type, so this check runs once a day and even when it fires
the result is only an instruction waiting for you. A position can gap down at
10am and stay held until you next open the app.

## Candidates considered (proposals from Phase A, 2026-08-28)

Rejected before ranking:

- **NBIS** — thesis contradicted by disclosed facts. It treats a *proposed*
  $4.5B convertible note offering as an open question; Nebius disclosed on
  2026-08-24 that the offering **closed and was upsized to ~$5.75B**. A
  completed raise described as pending, and $1.25B larger than the thesis
  weighed. The price gap alone (−2.1%) would have waved this through.
- **CORT** — its stop-loss fired this cycle, so it is not eligible for a
  same-cycle top-up. Queueing a buy next to the sell would be
  self-contradictory.
- **COHR** — wash-sale guard: sold at a loss on 2026-08-20, inside the 30-day
  window. Note its *price-gated* re-entry lock had actually cleared (276.28 is
  below the 286.25 it was sold at); it was the calendar guard that blocked it.

Rejected by position sizing (in priority order):

- **NVDA** (high) — $105.57 target would leave cash at −$21.55, below the
  $52.79 cash-buffer floor.
- **MSFT** (high, top-up) — already above target size ($222.05 vs $105.57).
- **DELL** (medium, top-up) — headroom of $2.28 is below the $6.33 minimum
  top-up.
- **ALAB** (low, top-up) — already above target size ($62.81 vs $31.67).
- **SPCX, SNDK, MRVL, AMD** (low) — each would leave cash at $52.35, just
  under the $52.79 buffer floor.

**No buy instructions were created this cycle.** Cash is $84.02 against a
$52.79 minimum buffer, which leaves too little room for even a low-conviction
entry.

The 7 `avoid` theses (GLW, RKLB, ASTS, INTC, AAOI, MU, CBRS) were not
processed further.

## Checks run this cycle
- Market-hours guard: 08:37 Central on a Monday — inside the 08:30–15:00
  regular session.
- Account fingerprint: net liquidation $527.87, inside the [400, 900] band; 4
  positions (ALAB, CORT, DELL, MSFT). **This is a tripwire, not an account
  verification** — no connector endpoint returns an account identifier, so
  which account is connected cannot be confirmed, and this cannot distinguish
  two accounts of similar size.
- Every quote used was `REALTIME`. No prior-close fallback was accepted.
- Monday weekend-gap search plus a disclosed-facts check on all 10 candidates
  that reached Step 4. MSFT, NVDA, DELL, ALAB, COHR, MRVL, SNDK, SPCX and AMD
  all had their headline figures confirmed against primary or major-outlet
  sources; only NBIS failed.
- **Wash-sale guard is incomplete.** `YOUR_OTHER_ACCOUNT_ID_HERE` is not
  reachable through this connector and could not be checked. An account that
  cannot be checked is not an account that came back clean.

---
`trade_log.jsonl` is the source of truth. This file is a convenience view; if
the two ever disagree, trust the log.
