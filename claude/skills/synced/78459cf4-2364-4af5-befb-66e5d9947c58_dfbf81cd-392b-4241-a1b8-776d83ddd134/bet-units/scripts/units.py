#!/usr/bin/env python3
"""
Bet unit converter.

Converts between a dollar bankroll and "units" (U), the standard way bettors
normalize stake size. Works in both directions:
  - balance -> dollars-per-unit (given a unit rule)
  - a slip of picks expressed in U -> dollar stakes + total risk
  - a dollar amount -> units

It also runs a sanity check on the unit rule, because the whole reason units
exist is to keep one bad day from emptying the bankroll. If the configured
unit is a large fraction of the bankroll, or a whole slip risks more than the
bankroll holds, the script says so loudly.

Usage examples:
  # Define 1U as "5 units total in the bankroll", show $/unit:
  python units.py --bankroll 150 --total-units 5

  # Define 1U as 2% of bankroll:
  python units.py --bankroll 150 --pct 2

  # Define 1U as a flat $3:
  python units.py --bankroll 150 --flat 3

  # Convert a slip (units risked per pick) into dollars. Pass --slip once per pick,
  # or pipe the raw slip text via --slip-file / stdin and let the regex pull the U values:
  python units.py --bankroll 150 --total-units 5 --slip 1.4 --slip 1.1 --slip 1.2 --slip 1.4

  # Convert dollars back to units:
  python units.py --bankroll 150 --total-units 5 --to-units 42
"""
import argparse
import re
import sys


def unit_value(bankroll, total_units=None, pct=None, flat=None):
    """Return dollars-per-unit under exactly one rule."""
    provided = [x for x in (total_units, pct, flat) if x is not None]
    if len(provided) != 1:
        raise ValueError("Provide exactly one of --total-units, --pct, --flat.")
    if total_units is not None:
        if total_units <= 0:
            raise ValueError("--total-units must be positive.")
        return bankroll / total_units
    if pct is not None:
        if pct <= 0:
            raise ValueError("--pct must be positive.")
        return bankroll * pct / 100.0
    if flat <= 0:
        raise ValueError("--flat must be positive.")
    return float(flat)


def parse_slip_text(text):
    """Pull every '1.4U' style number out of raw pasted slip text."""
    return [float(m) for m in re.findall(r"(\d+(?:\.\d+)?)\s*[uU]\b", text)]


def sanity_notes(bankroll, uv, total_slip_units=None):
    notes = []
    pct = uv / bankroll * 100 if bankroll else 0
    implied_total = bankroll / uv if uv else 0
    notes.append(f"1U = ${uv:,.2f}  ({pct:.1f}% of bankroll; bankroll = {implied_total:.1f}U)")

    if pct > 5:
        notes.append(
            f"WARNING: 1U is {pct:.1f}% of your bankroll. Standard staking is 1-2% so a "
            f"cold streak can't bust you. At this size you have only ~{implied_total:.0f} units "
            f"of runway; pros run 50-100."
        )
    elif pct > 2:
        notes.append(
            f"CAUTION: 1U is {pct:.1f}% of bankroll. Above the 1-2% norm. Workable if your edge "
            f"is real and tested, risky if not."
        )

    if total_slip_units is not None:
        total_dollars = total_slip_units * uv
        notes.append(
            f"Slip total: {total_slip_units:.2f}U = ${total_dollars:,.2f} "
            f"({total_dollars / bankroll * 100:.1f}% of bankroll)"
        )
        if total_dollars > bankroll:
            notes.append(
                f"HARD STOP: this slip risks ${total_dollars:,.2f} but your bankroll is "
                f"${bankroll:,.2f}. You cannot place it. Cut picks or shrink unit size."
            )
        elif total_dollars > bankroll * 0.25:
            notes.append(
                f"WARNING: this single slip risks {total_dollars / bankroll * 100:.0f}% of your "
                f"bankroll. One bad day does serious damage. Spread exposure across days."
            )
    return notes


def main():
    p = argparse.ArgumentParser(description="Convert bankroll <-> betting units.")
    p.add_argument("--bankroll", type=float, required=True, help="Current bankroll in dollars.")
    g = p.add_argument_group("unit rule (pick one)")
    g.add_argument("--total-units", type=float, help="Bankroll = this many units. 1U = bankroll/N.")
    g.add_argument("--pct", type=float, help="1U = this %% of bankroll.")
    g.add_argument("--flat", type=float, help="1U = this flat dollar amount.")
    p.add_argument("--slip", type=float, action="append", default=[],
                   help="Units risked on a pick. Repeat for each pick.")
    p.add_argument("--slip-file", help="File of raw slip text; U values are auto-extracted.")
    p.add_argument("--slip-stdin", action="store_true",
                   help="Read raw slip text from stdin and auto-extract U values.")
    p.add_argument("--to-units", type=float, help="Convert this dollar amount into units.")
    args = p.parse_args()

    uv = unit_value(args.bankroll, args.total_units, args.pct, args.flat)

    slip = list(args.slip)
    if args.slip_file:
        with open(args.slip_file) as f:
            slip += parse_slip_text(f.read())
    if args.slip_stdin:
        slip += parse_slip_text(sys.stdin.read())

    print("=" * 56)
    total = sum(slip) if slip else None
    for note in sanity_notes(args.bankroll, uv, total):
        print(note)
    print("=" * 56)

    if slip:
        print("Per-pick stakes:")
        for i, u in enumerate(slip, 1):
            print(f"  Pick {i}: {u:.2f}U  ->  ${u * uv:,.2f}")
        print("=" * 56)

    if args.to_units is not None:
        print(f"${args.to_units:,.2f}  ->  {args.to_units / uv:.2f}U")
        print("=" * 56)


if __name__ == "__main__":
    main()
