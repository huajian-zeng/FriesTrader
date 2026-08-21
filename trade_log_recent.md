# 2026-08-21

## ⚠ 2 instructions awaiting your approval in IBKR

Review them all at: https://ndcdyn.interactivebrokers.com/sso/resolver?action=ACCT-MGMT-MAIN#/orders/instructions

- **BUY 0.329 CORT** (top-up, $122.50 ref, ~$40.30, high conviction) — expires **2026-08-28**
- **BUY 0.1131 ALAB** (top-up, $292.72 ref, ~$33.11, medium conviction) — expires **2026-08-28**

**Neither has executed.** They are drafts sitting in IBKR's AI Instructions queue. Nothing reaches the market until you open the app and tap *Review & Submit*. If you leave them untouched they vanish on 2026-08-28.

---

## Resolved from yesterday's queue — you approved both

This is the first cycle where an approved instruction came back and was reconciled end to end. Both of yesterday's instructions were gone from the queue and both had matching fills.

- **COHR — SELL 0.0947 @ $286.25** (stop-loss), filled 2026-08-20 13:42:53Z. Realized **−$5.22** after commission. Position fully closed.
  - *Not flagged as a wash sale.* The loss is real and COHR was bought 2026-08-14 (inside the 30-day window), but zero COHR remains held, so there is no replacement position for a disallowed loss to attach to — an ordinary closed round-trip.
- **CORT — BUY 0.5199 @ $119.13** (new entry), filled 2026-08-20 13:42:47Z. Commission $0.62.

Neither was declined and neither expired.

---

## Loss limits — not halted

| | Realized | % of $542.44 starting capital | Limit |
|---|---|---|---|
| Today | $0.00 | 0.00% | 5% |
| This week (from 2026-08-17) | −$5.22 | −0.96% | 10% |

The COHR stop-loss is this account's first realized loss. Well inside both limits, so new entries and top-ups were **not** halted.

> **Partial by construction.** Source is `get_account_trades` on the one account this connector is attached to. Linked account `YOUR_OTHER_ACCOUNT_ID_HERE` is unreachable here and was **not** checked — the wash-sale guard is incomplete this cycle. An account that can't be checked is not an account that came back clean.

---

## Held positions — stop-loss and take-profit

All four quotes came back REALTIME. Nothing triggered; nothing to sell.

| Symbol | Price | vs avg cost | Stop used | Status |
|---|---|---|---|---|
| MSFT | $483.05 | −4.08% | 9.76% | holding |
| CORT | $122.00 | **+1.40%** | — (gain, not computed) | holding |
| ALAB | $292.00 | −9.85% | 15.00% (clamped) | holding |
| DELL | $437.24 | −12.03% | 13.49% | holding |

DELL is the closest to its stop — 12.03% drawdown against a 13.49% trigger. No take-profit tier has fired on any position this holding period.

> **No intraday protection.** These stops are evaluated once a day, here, and even when one triggers the result is only an instruction awaiting your tap. A position can gap down hard mid-session and stay held until you next open the app.

---

## New entries — all four blocked on capacity

The account holds 4 positions against a max of 4, and no sell freed a slot this cycle. Per the spec these were short-circuited **without** a staleness re-check — this is scarcity, not a verdict on the theses.

- AAOI (medium) — no open slots
- MRVL (medium) — no open slots
- AMD (low) — no open slots
- TSM (low) — no open slots

---

## Top-ups considered — 2 queued, 2 rejected

Every thesis was re-checked against the company's own disclosures before sizing. **All four were confirmed; none was contradicted.**

- **CORT — queued, $40.31.** Q2 2026 (Jul 29) confirmed: record revenue $256.1M, +32% y/y, full-year guidance **raised** to $1.1–1.2B, Lifyorli $47.6M in its first quarter. Position $63.43 vs $103.74 target.
- **ALAB — queued, $33.11.** Q2 2026 (Aug 4) confirmed: record revenue $392.4M, +27% q/q and +104% y/y, adj EPS $0.80 vs $0.69, Q3 guided $540–560M, Scorpio X in volume production. Position $29.14 vs $62.25 target.
- **DELL — rejected.** FQ1 2027 confirmed ($43.8B revenue +88%, EPS $4.86, FY guide raised to $165–169B, $60B AI-server expectation; FQ2 report confirmed for Sep 1). But headroom is only $5.02 against a $6.22 minimum top-up — too small to be worth an order. **FQ2 earnings land Sep 1, eleven days out.**
- **MSFT — rejected.** FY26 Q4 confirmed: revenue $90.01B vs $87.62B, EPS $4.74 vs $4.24, Azure +43% accelerating from 40%, Azure past $100B annually. Already **over** target at $210.42 vs $103.74 — the double approval tap on 2026-08-14 left this position roughly twice its intended size.

Price gaps against Phase A's reference closes were all under 1% (MSFT +0.4%, CORT +0.8%, ALAB +0.5%, DELL +0.6%) — no invalidation criteria re-triggered. No sell re-entry lock is armed on any of these.

---

*Convenience view only. `trade_log.jsonl` is the source of truth; if the two disagree, trust the log.*
