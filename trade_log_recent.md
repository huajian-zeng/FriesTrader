# 2026-08-20

## ⚠ 2 instructions awaiting your approval in IBKR

Review them all at:
https://ndcdyn.interactivebrokers.com/sso/resolver?action=ACCT-MGMT-MAIN#/orders/instructions

- **SELL 0.0947 COHR** (stop-loss, 15.78% drawdown, ~$26.97 at the $284.80 bid) — expires **2026-08-27**
- **BUY 0.5199 CORT** ($119.12 ask, ~$61.93, medium conviction, new entry) — expires **2026-08-27**

**Neither has executed.** They are drafts sitting in IBKR's AI Instructions
queue and nothing reaches the market until you open the app and tap *Review &
Submit*. Left untouched they vanish on 2026-08-27.

Ran 08:35–08:41 Central on a Thursday, inside the 08:30–15:00 regular session.

---

## Resolved from earlier instructions

Nothing. The queue was empty at the start of the cycle, and every `instruction`
entry in the log was already resolved on 2026-08-17 (the four fills of
2026-08-14). Nothing was approved, declined, or expired since the last cycle —
and nothing expired unattended, because there was nothing in the queue to go
unread.

## Loss-limit check

- Daily realized: **$0.00 (0.00%)** against a 5% limit
- Weekly realized: **$0.00 (0.00%)** against a 10% limit
- **Entries not halted.**

No sale has ever executed in this account, so nothing is realized either way.
The 30-day window holds five equity BUY fills plus the 2026-08-12 AED→USD
conversion, which was dropped as a non-USD row (not trading P&L).

*Partial by construction:* the connector sees only the account it is connected
to, so this counts only what that one account realized.

## Held positions — stop-loss / take-profit

All four quotes came back **REALTIME (live)**.

| Symbol | Price | vs avg cost | Stop % used | Status |
|---|---|---|---|---|
| MSFT | $481.30 | −4.43% | 9.72% | holding |
| DELL | $435.00 | −12.48% | 13.49% | holding |
| ALAB | $288.28 | −11.00% | 15.00% (capped) | holding |
| **COHR** | **$285.12** | **−15.78%** | **15.00% (capped)** | **STOP TRIGGERED → sell queued** |

**COHR's stop-loss fired** — the first time any stop has triggered in this
account. Its 20-day stdev is 9.13%, so 2.5× that is 22.84%, clamped down to the
15.00% `max_stop_pct`; a 15.78% drawdown clears it. A full-position SELL of
0.0947 shares is now in your queue. A good thesis does not cancel a stop, so no
thesis review was applied and no loss-limit halt could have blocked it.

No take-profit tier has fired for any position this holding period — every
position is underwater.

> **Reminder:** there is no resting stop at the broker. This is a once-a-day
> evaluation, and even when it triggers the sell is only an instruction awaiting
> your tap. COHR can keep falling until you open the app.

## Candidates considered — 7

COHR's stop-loss freed exactly one slot: `open_slots = 4 max − 3 live − 0
pending = 1`. Ranked order was MSFT → DELL → CORT → ALAB → TSM → MRVL.

### ✅ Approved — CORT (medium, new entry) — $61.94 → 0.5199 shares

Corcept Therapeutics. Every disclosed figure re-verified against primary sources
this cycle and all four check out:

- Q2 2026 revenue **$256.1M, +32% YoY**
- Full-year 2026 guidance raised to **$1.1B–$1.2B** — the thesis's "as much as
  $1.2B" is correct. Worth flagging: this is the same figure that got an earlier
  CORT thesis **rejected on 2026-08-14**, when it quoted the superseded
  $950M–$1.05B Q1 range as the current raised outlook. That error is gone.
- Phase 3 **ROSELLA** at ASCO 2026: 35% reduction in risk of death (HR 0.65,
  p=0.0004), median OS **16.0 vs 11.9 months**
- Relacorilant NDA for Cushing's **resubmitted 17 June 2026** after a December
  2025 complete response letter; FDA action date **17 December 2026**, which
  matches the thesis's "around late 2026"

The thesis says relacorilant "is not approved in Cushing's" — correct, and
correctly scoped: it *is* approved and selling in platinum-resistant ovarian
cancer as LIFYORLI ($47.6M in Q2). Price −0.38% vs Phase A; no invalidation
criterion met. Cash after: $131.68 (25.5% buffer), 4 of 4 positions.

### Rejected — top-ups (3)

Every held thesis passed both the disclosed-fact re-check and the price
staleness check; the rejections are all sizing, not quality.

- **MSFT** — $209.65 held vs $103.23 target → already above target. FY26 Q4
  re-verified: revenue $90.0B (+18%), EPS $4.74 vs $4.24, Azure +43% and past
  $100B annual. Price −0.63% vs Phase A.
- **DELL** — headroom **$5.00**, just under the **$6.19** minimum → no order
  attempted. Q1 FY27 re-verified: revenue $43.84B (+88%), AI servers $16.1B,
  backlog $51.3B, FY27 guide $165–169B with ~$60B AI. Its −6.08% session on
  19 Aug is reported as profit-taking plus a Morgan Stanley IT-hardware sector
  downgrade — not a disclosure, and none of its invalidation criteria are met.
- **ALAB** — headroom $2.20, below the $5.00 minimum. Q2 2026 re-verified:
  revenue $392.4M (+104% YoY, +27% seq), Q3 guide $540–560M. Price −0.64%.

### Rejected — new entries (2), on scarcity

Both were fully re-verified before the cap closed; they lost the slot to CORT,
not on quality.

- **TSM** (low) — July 2026 revenue NT$467.58B, **+44.7% YoY**, 2026 USD growth
  guided slightly above 40%. Verified. Cap filled.
- **MRVL** (low, `dilution_risk`) — the 19 Aug disclosure verified: Google may
  buy up to **$12.2B** of stock, 58,970,907 shares at $206.58, vesting per
  $500M of chip procurement, exercisable to 18 Aug 2033. Cap filled.

### Dropped — COHR top-up

COHR was also a low-conviction top-up candidate. Dropped before ranking under
the **no same-cycle sell-then-buy** rule — its stop fired this cycle, and
queueing a BUY and a SELL for the same symbol side by side in your approval
queue is exactly what that rule prevents.

## Wash-sale notes

**Buy side (CORT):** clean on the connected account — `get_account_trades`
(DAYS_30) contains no CORT sell at all, let alone a loss sale in the 30-day
window.

**Sell side (COHR):** a stop-loss sell is a loss by definition, and COHR was
bought on 2026-08-14, inside the 30-day window — but this is a **full**-position
sell of the only lot, so nothing remains held for a disallowed loss to attach
to. That makes it an ordinary closed round-trip, **not** a wash sale, and it is
not flagged. It will be re-checked against `get_account_positions` at resolution
time if you approve it.

`YOUR_OTHER_ACCOUNT_ID_HERE` **could not be checked** — the IBKR connector
exposes only the account it is connected to. An account that could not be
checked is not an account that came back clean.

## ⚠ Still open — MSFT position-size breach

MSFT is **$209.65, or 40.6% of net liquidation**, against a 20%
`max_position_pct_of_account` cap. This dates from the 2026-08-14 duplicate fill
(two 0.2178 fills against one instruction).

**No mechanical rule forces a trim**: the cap governs the sizing of new buys,
and the only sell triggers are stop-loss and take-profit, neither of which fired
for MSFT. No sell instruction was created on this basis. **This is yours to
decide** — trim it manually in the IBKR app or leave it.

## Account fingerprint

Net liquidation **$516.15** (expected band $400–900 ✓), 4 positions: ALAB, COHR,
DELL, MSFT.

*Tripwire only, not an account verification* — no connector endpoint returns an
account identifier, so `risk_rules.json`'s `account_number` could not be and was
not checked. It cannot distinguish two accounts of similar size.

---

*Convenience view only. `trade_log.jsonl` is the source of truth; if the two
disagree, trust `trade_log.jsonl`.*
