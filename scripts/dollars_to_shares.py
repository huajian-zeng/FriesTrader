#!/usr/bin/env python3
"""Convert position_sizing.py's dollar amount into a share count for
create_order_instruction, per PHASE_B_TASK.md Step 6.

Robinhood accepted dollar-denominated orders directly, so this step did
not exist. IBKR's create_order_instruction takes `quantity` in shares,
which puts a division between the sizing decision and the order — and
that division has to be mechanical, not something the model does in its
head, for the same reason every other calculation here lives in a script.

Both modes floor rather than round, so the resulting order can only ever
be smaller than what position_sizing.py approved, never larger. Rounding
to the nearest tick would overshoot about half the time — small in
dollars, but it would mean placing an order the sizing script never
authorised, and the cash-buffer check upstream was computed against the
authorised figure. When the amount cannot buy even one share the result
is `skip`, never a rounded-to-zero order.
"""
import argparse
import json
import math
import sys


def floor_to(value, decimals):
    """Truncate toward zero at `decimals` places — never rounds up."""
    scale = 10 ** decimals
    return math.floor(value * scale) / scale


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dollar-amount", type=float, required=True,
                    help="position_sizing.py's approved dollar_amount for this candidate")
    p.add_argument("--reference-price", type=float, required=True,
                    help="the fresh ask for a BUY, or bid for a SELL, from get_price_snapshot")
    p.add_argument("--fractional", action="store_true",
                    help="set only if this IBKR account is actually enabled for fractional "
                         "trading; without it the result is floored to whole shares")
    p.add_argument("--fractional-decimals", type=int, default=4,
                    help="decimal places to round fractional quantities to (default 4)")
    p.add_argument("--min-fractional-usd", type=float, default=1.00,
                    help="IBKR's minimum order value in fractional mode (default 1.00)")

    args = p.parse_args()

    if args.reference_price <= 0:
        print(json.dumps({"error": "--reference-price must be positive"}), file=sys.stderr)
        sys.exit(1)
    if args.dollar_amount <= 0:
        print(json.dumps({"error": "--dollar-amount must be positive"}), file=sys.stderr)
        sys.exit(1)

    raw = args.dollar_amount / args.reference_price

    if args.fractional:
        quantity = floor_to(raw, args.fractional_decimals)
        if quantity * args.reference_price < args.min_fractional_usd:
            print(json.dumps({
                "quantity": None,
                "action": "skip",
                "reason": f"${args.dollar_amount:.2f} at {args.reference_price:.2f} is "
                          f"{quantity} shares, under IBKR's ${args.min_fractional_usd:.2f} "
                          f"fractional-order minimum",
            }))
            return
    else:
        quantity = math.floor(raw)
        if quantity < 1:
            print(json.dumps({
                "quantity": None,
                "action": "skip",
                "reason": f"${args.dollar_amount:.2f} buys {raw:.4f} shares at "
                          f"{args.reference_price:.2f} — less than one whole share, and this "
                          f"account is not in fractional mode",
            }))
            return

    notional = round(quantity * args.reference_price, 2)
    result = {
        "quantity": quantity,
        "action": "order",
        "reference_price": args.reference_price,
        "requested_dollar_amount": round(args.dollar_amount, 2),
        "actual_notional": notional,
        # Whole-share flooring can leave a real gap between what was sized and
        # what gets ordered. Surfaced so the log shows the difference rather
        # than implying the approved amount was what actually went in.
        "unspent_usd": round(args.dollar_amount - notional, 2),
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
