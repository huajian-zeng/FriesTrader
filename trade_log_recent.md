# 2026-09-02

## ⚠ 1 instruction awaiting your approval in IBKR
Review it at: https://ndcdyn.interactivebrokers.com/sso/resolver?action=ACCT-MGMT-MAIN#/orders/instructions
- **SELL 0.2129 ALAB** (stop-loss, 10.5% drawdown vs an 8.4% stop) — expires 2026-09-09

Nothing below has executed. An instruction is a draft that sits in IBKR's AI
Instructions queue until you open the app and tap *Review & Submit*. Left
untouched it disappears on its own after 7 days.

## Resolved since the last cycle
- **NVDA BUY 0.4782 @ $216.87** — you approved instruction 100 on 2026-09-01
  and it filled at 13:55:46Z, well before its 2026-09-08 expiry. Commission
  $1.00. Nothing declined, nothing expired unread — the queue was empty, not
  ignored.

## Loss limits — no halt
Daily realized $0.00 (0.00%), weekly realized **-$8.36 (-1.54%)** against
$542.44 starting capital; limits are 5% daily / 10% weekly. One trade in the
week's bucket (the CORT stop-loss you approved on 2026-08-31). New entries and
top-ups were **not** halted. Source is `get_account_trades`, so hand-made sells
count too — but it only ever sees the one account the connector is attached to.

## Held positions
| Symbol | Qty | Avg cost | Now | Stop % used | Drawdown / gain | Outcome |
|---|---|---|---|---|---|---|
| ALAB | 0.2129 | $307.23 | $275.00 | 8.38% | **-10.49%** | **STOP TRIGGERED → sell queued** |
| DELL | 0.1309 | $497.02 | $459.00 | 10.29% | -7.65% | hold |
| MSFT | 0.4356 | $503.62 | $496.14 | 5.00% | -1.48% | hold |
| NVDA | 0.4782 | $218.96 | $219.28 | n/a (gain) | +0.15% | hold |

No take-profit tier is anywhere near firing — the first tier is +15% and every
position is at or below cost. No tier has ever fired on any of these holdings.

**ALAB is the one that needs you.** Its 10.49% drawdown from average cost
cleared the 8.38% volatility-scaled stop (2.5 × a 3.35% 20-day stdev). The
sell is a full exit of the position, and it is only a draft — there is no
resting stop at the broker, so ALAB stays held, gap risk and all, until you
approve it.

## Candidates considered (8 long theses from Phase A)
Every thesis was re-verified against the company's own disclosures this cycle,
not just against price. All eight facts checked out — no thesis was
contradicted. All eight were still rejected on mechanical grounds:

- **ALAB** (low, top-up) — rejected: its stop-loss fired this same cycle, so
  it can't be topped up in the same breath as being sold.
- **CORT** (medium, new) — rejected: **sell re-entry lock**. Sold at $113.03 on
  2026-08-31; it's $114.09 now, above that. Independently blocked by the
  wash-sale guard too (loss sale inside the 30-day window). The FDA approval of
  Lifyorli and the $950M–$1,050M 2026 guidance both check out — the gate is
  mechanical, and a good thesis doesn't override one.
- **LITE** (high, new) — rejected: a $103.20 entry would leave cash at -$28.90,
  under the $51.60 (10%) buffer. The Aug 12 beat-and-raise verified ($1.01B rev
  vs $987.7M est, $3.23 adj EPS, Q1 guide $1.225–1.275B).
- **DELL** (high, top-up) — rejected: $43.12 of headroom, but the buy would
  leave $31.18 cash, under the $51.60 buffer. The Sept 1 print verified: record
  $47.0B revenue, $7.04 adj EPS, FY27 raised $25B to $192B and EPS to $25.50.
- **MSFT** (high, top-up) — rejected: already $216.12 vs a $103.20 target, over
  size by $112.92. FQ4 verified (Azure +43%, $4.74 vs $4.24 est).
- **NVDA** (high, top-up) — rejected: $104.86 vs a $103.20 target, already at
  size. FQ2 beat and the AWS 2-million-GPU/Vera commitment verified.
- **AAOI** (low, new) — rejected: cash buffer. Q2 verified ($191.9M rev +86%,
  $0.06 EPS, Q3 guide $255–290M).
- **AMD** (low, new) — rejected: cash buffer. Data center +107% verified; the
  160M-share OpenAI warrant is real and dates to October 2025.

**The binding constraint this cycle was cash, not conviction.** $74.30 of cash
against a $51.60 minimum buffer leaves $22.70 to spend — less than any
candidate's size. If the ALAB sell is approved it frees roughly $58, which
would change that picture next cycle.

## Caveats that apply every cycle
- The account itself **cannot be verified**. No connector endpoint returns an
  account identifier. The fingerprint (net liq $516, inside the $400–900 band;
  4 positions: ALAB, DELL, MSFT, NVDA) is a tripwire, not a guarantee — it
  can't tell two accounts of similar size apart.
- The **wash-sale guard is incomplete**. `YOUR_OTHER_ACCOUNT_ID_HERE` is not
  reachable through this connector and was not checked. An account that can't
  be checked is not one that came back clean.
- **No intraday stop protection.** Stops are evaluated once a day, here, and
  the result is a draft awaiting your tap.

*`trade_log.jsonl` is the source of truth. If this file and it ever disagree,
trust `trade_log.jsonl`.*
