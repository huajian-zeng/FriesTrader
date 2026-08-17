# 2026-08-17

## ✅ 0 instructions awaiting your approval in IBKR
The queue is empty. Nothing was created this cycle, and nothing is waiting for a tap.

---

## ⚠ Needs your attention: MSFT filled twice, position is double size

All four instructions from Friday were approved and filled — but **MSFT executed twice against a single instruction**:

| | |
|---|---|
| Instruction created | 1 × BUY 0.2178 MSFT (id 100) |
| Fills received | 2 × 0.2178 @ $499.18 and $498.87, five seconds apart |
| Resulting position | 0.4356 shares, avg cost $503.62 |
| Position size | **$213.75 = 39.8% of net liquidation, against a 20% cap** |

Most likely a double tap on *Review & Submit* in the IBKR app. It was not produced by any pipeline rule, and **no mechanical rule forces a trim**: `max_position_pct_of_account` governs the sizing of new buys, and the only sell triggers are stop-loss and take-profit, neither of which fired for MSFT. So no sell instruction was created. **Whether to trim MSFT back toward $107 (20%) is your call** — the pipeline will not do it on its own, and it will keep MSFT excluded from top-ups while it sits above target.

The extra fill also cost an extra ~$1.00 commission and consumed ~$108 of cash that the sizing script had not authorised.

## Approved and filled since Friday

All four resolved well before their 2026-08-21 expiry. None expired, none was declined.

| Symbol | Instr | Filled | Price | Commission |
|---|---|---|---|---|
| MSFT | 100 | 0.2178 | $499.18 | $1.00 |
| MSFT | *(none)* | 0.2178 | $498.87 | $1.00 |
| DELL | 101 | 0.1309 | $492.10 | $0.64 |
| ALAB | 102 | 0.0998 | $320.71 | $0.32 |
| COHR | 103 | 0.0947 | $335.18 | $0.32 |

This was the first end-to-end test of the approve → fill → reconcile path that `execution.went_live_note` flagged as unverified. It worked — the one thing it surfaced is the duplicate-fill case above, which the log now records as a resolution plus a separate unattributed fill rather than pretending one instruction produced two fills.

## Loss limits — no halt

Daily and weekly realized P&L are both **$0.00 (0.0%)** against $542.44 starting capital. No sale has ever been made from this account, so nothing is realized either way. Week starts today (Monday), so daily and weekly are identical.

*Partial by construction: the connector sees only the account it is connected to. The wash-sale guard could not check `YOUR_OTHER_ACCOUNT_ID_HERE` — an account that cannot be checked is not an account that came back clean.*

## Held positions — all holding, nothing triggered

Stops are volatility-scaled and recomputed fresh each cycle.

| Symbol | Qty | Avg cost | Price | Gain/loss | Stop % | Status |
|---|---|---|---|---|---|---|
| ALAB | 0.0998 | $323.92 | $336.86 | **+4.00%** | n/a (gain) | holding |
| COHR | 0.0947 | $338.53 | $335.50 | −0.90% | 15.0% | holding |
| MSFT | 0.4356 | $503.62 | $490.71 | −2.56% | 9.85% | holding |
| DELL | 0.1309 | $497.02 | $481.17 | −3.19% | 13.8% | holding |

No stop-loss triggered and no take-profit tier fired — no position is near its 15% first tier.

> Reminder: there is no resting stop at the broker. This is a once-a-day check, and even when it triggers the sell is only an instruction awaiting your tap.

## Candidates considered — none queued

**Account is full: 4 of 4 concurrent positions, queue empty → 0 open slots.**

New entries — skipped on slot scarcity, not on quality. Per spec these were *not* re-checked for staleness or weekend news:

- **CORT** (high conviction) — no open slots
- **RKLB** (low) — no open slots
- **GLW** (low) — no open slots

Top-ups — evaluated in full (Monday weekend-gap search, fact check, fresh live quote), then all rejected by the sizing script:

- **ALAB** — at/above target ($33.62 vs $32.22 target, headroom −$1.40)
- **COHR** — headroom only $0.45, below the $5.00 minimum top-up
- **MSFT** — far above target ($213.75 vs $32.22, headroom −$181.53)
- **DELL** — above target ($62.99 vs $32.22, headroom −$30.76)

Monday weekend-gap searches turned up nothing that contradicts any of the four theses, and each thesis's disclosed figures were re-verified against source reporting with no contradiction found. MSFT declared a $0.91 dividend, ex-date 2026-08-20 — noted, not thesis-relevant.

---

*`trade_log.jsonl` is the source of truth; this file is a convenience view. If the two disagree, trust the log.*
