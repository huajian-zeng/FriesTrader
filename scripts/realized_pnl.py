#!/usr/bin/env python3
"""Sum IBKR realized P&L into the daily and weekly figures pnl_pct.py
expects, per PHASE_B_TASK.md Step 5.

Reads a `get_account_trades` response on stdin verbatim — the whole
object, `{"trades": [...]}`, not a hand-extracted subset — and buckets
each trade's `realized_pnl` by trading day.

Two things this exists to get right, neither of which belongs in the
model:

  * **Timezone.** `trade_time` is UTC; the loss limits are defined on
    America/Chicago trading days. An extended-hours fill at 01:30Z is
    20:30 the *previous* Chicago day, so bucketing on the raw UTC date
    would push it into the wrong day and mis-state both limits.
  * **Week start.** The week runs Monday through today, so a Monday run
    has daily and weekly equal.

Trades with `realized_pnl` of 0 (every buy, and any flat close) are
counted but contribute nothing; trades missing the field entirely are
skipped and reported in `skipped_no_pnl` rather than silently dropped.
"""
import argparse
import json
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

CHICAGO = ZoneInfo("America/Chicago")


def to_trading_day(trade_time):
    """UTC ISO-8601 timestamp -> the America/Chicago calendar date it fell on."""
    text = trade_time.replace("Z", "+00:00")
    moment = datetime.fromisoformat(text)
    if moment.tzinfo is None:
        raise ValueError(f"trade_time has no timezone: {trade_time!r}")
    return moment.astimezone(CHICAGO).date()


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--today", required=True,
                    help="YYYY-MM-DD in America/Chicago, from "
                         "`TZ='America/Chicago' date +%%F` — never guessed")
    p.add_argument("--currency", default="USD",
                    help="only count trades in this currency (default USD); FX conversion "
                         "trades in the account base currency are not realized trading P&L")
    args = p.parse_args()

    try:
        today = datetime.strptime(args.today, "%Y-%m-%d").date()
    except ValueError:
        print(json.dumps({"error": f"--today must be YYYY-MM-DD, got {args.today!r}"}),
              file=sys.stderr)
        sys.exit(1)

    week_start = today - timedelta(days=today.weekday())

    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(json.dumps({"error": f"could not parse get_account_trades response: {exc}"}),
              file=sys.stderr)
        sys.exit(1)

    trades = payload.get("trades")
    if trades is None:
        print(json.dumps({"error": "expected a get_account_trades response with a 'trades' key"}),
              file=sys.stderr)
        sys.exit(1)

    daily = 0.0
    weekly = 0.0
    counted = []
    skipped_no_pnl = []
    skipped_other_currency = 0

    for trade in trades:
        symbol = trade.get("symbol")
        if trade.get("currency") and trade["currency"] != args.currency:
            skipped_other_currency += 1
            continue
        if "realized_pnl" not in trade or trade["realized_pnl"] is None:
            skipped_no_pnl.append(symbol)
            continue
        if not trade.get("trade_time"):
            print(json.dumps({"error": f"trade for {symbol} has no trade_time — cannot bucket it "
                                        f"by trading day, refusing to guess"}), file=sys.stderr)
            sys.exit(1)
        try:
            day = to_trading_day(trade["trade_time"])
        except ValueError as exc:
            print(json.dumps({"error": str(exc)}), file=sys.stderr)
            sys.exit(1)

        if day > today or day < week_start:
            continue

        amount = float(trade["realized_pnl"])
        weekly += amount
        if day == today:
            daily += amount
        if amount:
            counted.append({"date": day.isoformat(), "symbol": symbol,
                            "realized_pnl": round(amount, 6)})

    result = {
        "today": args.today,
        "week_start": week_start.isoformat(),
        "daily_realized_usd": round(daily, 2),
        "weekly_realized_usd": round(weekly, 2),
        "trades_in_week": len(counted),
        "entries_counted": counted,
    }
    if skipped_no_pnl:
        result["skipped_no_pnl"] = skipped_no_pnl
    if skipped_other_currency:
        result["skipped_other_currency"] = skipped_other_currency
    print(json.dumps(result))


if __name__ == "__main__":
    main()
