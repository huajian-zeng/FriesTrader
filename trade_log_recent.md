# 2026-08-24 (Monday)

## ✅ 0 instructions awaiting your approval in IBKR

The queue is empty. Nothing was created this cycle and nothing is waiting for
your tap.

---

## Resolved since the last run — you approved both

Both drafts from Friday 2026-08-21 were approved in the IBKR app and filled on
2026-08-21 at 14:02 UTC, well before their 2026-08-28 expiry. Neither was
declined and neither expired unread.

- **BUY 0.329 CORT** (top-up) filled at **$122.77**, commission $0.40
- **BUY 0.1131 ALAB** (top-up) filled at **$289.61**, commission $0.33

Both are buys, so no realized P&L and no wash-sale question.

---

## Loss limits — reset for the new week

| Window | Realized | % of $542.44 | Limit | Halted? |
|---|---|---|---|---|
| Today | $0.00 | 0.00% | 5% | no |
| This week (from Mon 2026-08-24) | $0.00 | 0.00% | 10% | no |

A new trading week started today, so last week's **-$5.22 COHR stop-loss loss
has rolled out of the weekly window**. New entries and top-ups are not halted.

*Partial by construction: the connector sees only the account it is attached
to, so hand trades in another account are invisible here.*

---

## Held positions — stop-loss / take-profit

Nothing triggered and no take-profit tier fired. All four quotes were live
(REALTIME).

| Symbol | Qty | Avg cost | Fresh price | Drawdown | Stop used | Status |
|---|---|---|---|---|---|---|
| MSFT | 0.4356 | $503.62 | $484.04 | 3.89% | 9.76% | holding |
| CORT | 0.8489 | $121.75 | $120.99 | 0.62% | 15.00% | holding |
| ALAB | 0.2129 | $307.23 | $273.15 | 11.09% | 15.00% | holding |
| DELL | 0.1309 | $497.02 | $436.00 | **12.28%** | 13.43% | holding — closest to its stop |

**DELL is 1.15 points of drawdown away from its stop**, and reports Q2 FY2027
on 1 September. Remember there is no resting stop at the broker: this is
evaluated once a day, and even a trigger only produces a draft awaiting your
tap.

---

## New-entry candidates — all skipped on capacity

The account holds 4 of 4 allowed positions and no sell freed a slot, so all
nine new candidates were short-circuited **without** a staleness re-check.
This is scarcity, not a verdict on any thesis.

COHR, SNDK, GLW, AAOI, NBIS, MU, AMD, SPCX, TSM.

Note on **COHR**: beyond the capacity block, it still carries an unresolved
sell re-entry lock from the 2026-08-20 stop-loss sell at $286.25 — any future
COHR buy needs a fresh price at or below that.

---

## Top-up candidates — considered, all rejected on sizing

Weekend news searches (Sat/Sun) turned up nothing contradicting any thesis, and
all four theses were re-verified against the companies' own disclosures — MSFT
FY26 Q4, ALAB Q2 2026 and its $540–560M Q3 guide, CORT Q2 2026 and the raised
$1.1–1.2B guide, DELL Q1 FY2027. **No thesis was contradicted.**

- **MSFT** (high) — already above target ($210.84 held vs $102.67 target). No top-up.
- **CORT** (high) — already at target ($102.71 vs $102.67). No top-up.
- **DELL** (medium) — $4.53 of headroom, below the $6.16 minimum top-up. No order attempted.
- **ALAB** (low) — already above target ($58.15 vs $30.80). No top-up.

**ALAB gapped -4.33%** from Friday's close. Checked against its invalidation
criteria and it does not meet them: a sector-wide AI/semiconductor selloff and
continued valuation de-rating, with no company disclosure behind it. Q3 is not
yet reported.

---

## Standing flags for you

- **MSFT is 41.1% of net liquidation against a 20% cap** — a legacy of the
  2026-08-14 duplicate approval tap that filled the same instruction twice. No
  mechanical rule forces a trim, so the pipeline will not act on it.
- **Account identity is not verified.** No connector endpoint returns an
  account id. The fingerprint (net liquidation $513.33, inside the
  [400, 900] band; 4 positions) is a tripwire only and cannot tell two
  similarly-sized accounts apart.
- **Wash-sale guard is incomplete.** Linked account
  `YOUR_OTHER_ACCOUNT_ID_HERE` is unreachable through this connector and was
  **not** checked. Unchecked is not clean.

---

*Convenience view only. `trade_log.jsonl` is the source of truth; if the two
disagree, trust the log.*
