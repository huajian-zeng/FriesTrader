#!/usr/bin/env python3
"""Evaluate Phase A Step 2's three signal criteria and the magnitude score
used to ration the news-search budget, per risk_rules.json/PHASE_A_TASK.md.

Why this is a script rather than model arithmetic: the Robinhood build
read `average_volume_30_days` straight off get_equity_fundamentals, so
the volume-spike test was a single division. The IBKR connector has no
such field, so the average has to be computed from the daily bars — new
arithmetic, and this project deliberately keeps arithmetic out of the
model.

Reads a JSON object on stdin. `get_price_history` returns COLUMNAR
parallel arrays, not a list of bar objects, so that response is accepted
verbatim — transposing parallel arrays by hand is exactly the kind of
step that silently misaligns a close with the wrong volume:

  {"history": {"time": [...], "close": [...], "volume": [...], ...},
   "high_52_weeks": 321.00,       optional, null if unavailable
   "low_52_weeks": 180.00,        optional, null if unavailable
   "current_price": 314.86}

A row-shaped `"bars": [{"close": ..., "volume": ...}, ...]` list (oldest
first) is also accepted, which is what the tests use.

A criterion whose inputs are missing simply does not qualify. It is never
a reason to substitute a value, and never suppresses the other two.
"""
import argparse
import json
import statistics
import sys


def to_bars(payload):
    """Normalise either input shape into oldest-first row dicts.

    get_price_history's arrays are index-aligned, so a length mismatch
    means the response is malformed and zipping them would pair a close
    with someone else's volume. Refuse rather than produce plausible
    nonsense.
    """
    if payload.get("bars") is not None:
        return payload["bars"]

    history = payload.get("history") or payload
    times, closes, volumes = history.get("time"), history.get("close"), history.get("volume")
    if closes is None:
        return []
    lengths = {len(x) for x in (times, closes, volumes) if x is not None}
    if len(lengths) > 1:
        raise ValueError(f"get_price_history arrays have mismatched lengths {sorted(lengths)} — "
                         f"refusing to zip misaligned columns")
    return [
        {
            "date": times[i] if times else None,
            "close": closes[i],
            "volume": volumes[i] if volumes else None,
        }
        for i in range(len(closes))
    ]


def pct_move(bars):
    """60-calendar-day price move, using the window the caller actually pulled."""
    if len(bars) < 2:
        return None
    first, last = bars[0], bars[-1]
    if not first.get("close"):
        return None
    return {
        "ratio": abs(last["close"] - first["close"]) / first["close"],
        "close_60d_ago": first["close"],
        "latest_close": last["close"],
        "bars_used": len(bars),
    }


def volume_spike(bars, lookback):
    """Latest session's volume against the mean of the prior `lookback` bars.

    The latest bar is excluded from its own baseline — including a genuine
    spike in the average it is measured against would damp the very signal
    this is meant to detect.
    """
    if len(bars) < 2:
        return None
    latest = bars[-1].get("volume")
    prior = [b["volume"] for b in bars[-(lookback + 1):-1] if b.get("volume")]
    if not latest or len(prior) < 2:
        return None
    average = statistics.fmean(prior)
    if average <= 0:
        return None
    return {
        "ratio": latest / average,
        "latest_volume": latest,
        "avg_volume": round(average, 2),
        "bars_averaged": len(prior),
    }


def near_extreme(current_price, high_52w, low_52w):
    """Distance to whichever 52-week extreme is closer, as a fraction."""
    candidates = []
    if high_52w:
        candidates.append(("near_52wk_high", (high_52w - current_price) / high_52w, high_52w))
    if low_52w:
        candidates.append(("near_52wk_low", (current_price - low_52w) / low_52w, low_52w))
    # A price above its 52-week high (or below its low) reads as a negative
    # distance; that is still "at the extreme", so clamp rather than discard.
    usable = [(name, max(ratio, 0.0), ref) for name, ratio, ref in candidates]
    if not usable:
        return None
    name, ratio, reference = min(usable, key=lambda x: x[1])
    return {"which": name, "ratio": ratio, "reference": reference,
            "current_price": current_price}


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--price-move-threshold", type=float, required=True,
                    help="signal_thresholds.price_move_60d_pct")
    p.add_argument("--volume-spike-threshold", type=float, required=True,
                    help="signal_thresholds.volume_spike_multiple")
    p.add_argument("--pct-from-52wk-threshold", type=float, required=True,
                    help="signal_thresholds.pct_from_52wk_extreme")
    p.add_argument("--volume-lookback-bars", type=int, default=30,
                    help="bars to average for the volume baseline (default 30)")
    args = p.parse_args()

    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(json.dumps({"error": f"could not parse stdin: {exc}"}), file=sys.stderr)
        sys.exit(1)

    try:
        bars = to_bars(payload)
    except ValueError as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        sys.exit(1)
    current_price = payload.get("current_price")
    if not current_price:
        print(json.dumps({"error": "current_price is required"}), file=sys.stderr)
        sys.exit(1)

    triggered = []
    parts = []
    scores = []

    move = pct_move(bars)
    if move:
        parts.append(f"price_move_60d: {move['ratio']:.4f} "
                     f"(close_60d_ago: {move['close_60d_ago']} -> "
                     f"latest_close: {move['latest_close']})")
        if move["ratio"] >= args.price_move_threshold:
            triggered.append("price_move_60d")
            scores.append(move["ratio"] / args.price_move_threshold)

    spike = volume_spike(bars, args.volume_lookback_bars)
    if spike:
        parts.append(f"volume_spike: {spike['ratio']:.2f}x "
                     f"(latest_volume: {spike['latest_volume']} / "
                     f"avg_volume_{spike['bars_averaged']}d: {spike['avg_volume']})")
        if spike["ratio"] >= args.volume_spike_threshold:
            triggered.append("volume_spike")
            scores.append(spike["ratio"] / args.volume_spike_threshold)

    extreme = near_extreme(current_price, payload.get("high_52_weeks"),
                           payload.get("low_52_weeks"))
    if extreme:
        parts.append(f"{extreme['which']}: {extreme['ratio']:.4f} "
                     f"(current_price: {extreme['current_price']} / "
                     f"{extreme['reference']})")
        if extreme["ratio"] <= args.pct_from_52wk_threshold:
            triggered.append(extreme["which"])
            # Inverted: smaller distance means closer to the extreme, so more
            # notable. A ratio of exactly 0 (at the extreme) is unbounded, so
            # it is floored to keep the score finite and comparable.
            scores.append(args.pct_from_52wk_threshold / max(extreme["ratio"], 1e-6))

    result = {
        "qualifies": bool(triggered),
        "triggered": triggered,
        "signal_check": "; ".join(parts) if parts else "none",
        "magnitude_score": round(max(scores), 4) if scores else None,
        "unevaluable": [name for name, value in
                        (("price_move_60d", move), ("volume_spike", spike),
                         ("pct_from_52wk_extreme", extreme)) if value is None],
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
