# 2026-08-18

## ✅ 0 instructions awaiting your approval in IBKR

The IBKR AI Instructions queue is empty. Nothing was created this cycle, and
nothing from an earlier cycle is sitting unapproved. There is nothing to tap.

**Nothing has executed. No order was placed today.**

## Resolved from earlier instructions

Nothing to resolve. The four instructions from 2026-08-14 (MSFT, DELL, ALAB,
COHR) were already recorded as approved-and-filled on 2026-08-17, and no fill
has hit the account since 2026-08-14 14:29 UTC. No instruction was declined and
none expired unread — the queue was empty, not ignored.

## ⚠ Still open: MSFT is oversized (39.6% vs a 20% cap)

From the 2026-08-14 duplicate fill (two 0.2178-share fills against one
instruction), MSFT is 0.4356 shares worth **$209.33 — 39.6% of a $528.06
account**, against `max_position_pct_of_account` of 20%.

No mechanical rule forces a trim: the position cap governs the sizing of *new*
buys, and the only sell triggers are stop-loss and take-profit, neither of which
fired. **This is yours to decide** — if you want it back at 20%, trim about
$103 of MSFT by hand in the app.

## Loss limits

| | Realized | % of $542.44 | Limit |
|---|---|---|---|
| Today | $0.00 | 0.0% | 5% |
| This week (from Mon 2026-08-17) | $0.00 | 0.0% | 10% |

**Entries not halted.** No sale has ever been made from this account, so nothing
is realized either way. Partial by construction — the connector sees only the
account it is connected to.

## Held positions — stop-loss and take-profit

All four quotes came back live (REALTIME). Every position is modestly underwater
and every one is a hold: no stop triggered, no take-profit tier fired.

| Symbol | Price | Avg cost | P&L | Stop % used | Status |
|---|---|---|---|---|---|
| MSFT | $480.55 | $503.62 | −4.58% | 10.07% | hold |
| COHR | $323.00 | $338.53 | −4.59% | 15.00% (clamped) | hold |
| ALAB | $306.92 | $323.92 | −5.25% | 15.00% (clamped) | hold |
| DELL | $483.67 | $497.02 | −2.69% | 13.71% | hold |

Reminder: there is no resting stop at the broker. This is evaluated once a day,
and even a trigger would only produce an instruction awaiting your tap.

## Candidates considered — 9, none approved

**New entries (5) — all skipped, account is full at 4 of 4 positions.** No sell
freed a slot, so per the spec these were not evaluated on quality and no quote
was pulled: CORT (high), LITE (high), MU (low), SNDK (low), SPCX (low).

**Top-ups (4) — all four theses survived re-verification, all four rejected on
size.**

- **MSFT** — facts re-verified (FQ4 revenue $90.01B +18%, EPS $4.74, Azure +43%
  and past $100B annual). Already $209.33 against a $105.61 target — no top-up.
- **DELL** — facts re-verified (Q1 FY27 revenue $43.8B +88%, AI servers $16.1B
  +757%, $51.3B backlog, FY27 outlook $165–169B; next print 2026-09-03).
  Headroom is $0.06 against a $6.34 minimum — no order.
- **ALAB** — gapped −4.2%, explained by giving back Monday's +7.1% Northland
  upgrade pop; Q3 isn't reported, so the invalidation criterion can't be met.
  Facts re-verified (Q2 revenue $392.4M +104%, EPS $0.80 vs ~$0.69; Q3 guided
  $540–560M, EPS $1.16–1.21). Headroom $1.05 vs a $5.00 minimum — no order.
- **COHR** — gapped −8.3%, the biggest move of the cycle, explained by the
  unwind of Monday's ~8% rally on the 300mm SiC substrate sampling
  announcement; no new disclosure, and neither invalidation criterion is met.
  Facts re-verified (FQ4 revenue $2.046B +33.8%, non-GAAP EPS $1.74, FY26
  $7.118B +22.5%, $3B/quarter target by end of FY27, FQ1 guided $2.2–2.4B).
  One correction of record, unchanged: the release is dated 2026-08-12, not
  2026-08-13 as the thesis says — a publication date, not a figure the thesis
  rests on. Headroom $1.09 vs a $5.00 minimum — no order.

## Wash-sale guard

Enabled, 30-day window. No sale of any kind exists on the connected account, so
nothing was blocked and no sell needed a flag. **Incomplete this cycle:**
`YOUR_OTHER_ACCOUNT_ID_HERE` is not reachable through the IBKR connector and was
not checked. An account that could not be checked is not an account that came
back clean.

---
*Convenience view only. `trade_log.jsonl` is the source of truth; if the two
disagree, trust `trade_log.jsonl`.*
