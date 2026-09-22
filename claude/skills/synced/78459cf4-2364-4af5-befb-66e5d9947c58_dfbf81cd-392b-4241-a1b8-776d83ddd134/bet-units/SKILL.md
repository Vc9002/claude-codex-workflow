---
name: bet-units
description: Convert Vincent's betting bankroll to and from units (U). Trigger whenever he gives a dollar balance and a unit rule and wants to know what 1U is worth, pastes a betting slip with picks sized in U (like "England ML 1.4U" or "NRFI Risk 1.4U") and wants the dollar stakes, or asks "convert my balance to U", "how much is X units", "what should I bet", "size my slip", "how many units is $X". Use it for any sports-betting stake-sizing question where units and dollars need to be translated. Always runs a bankroll-safety check so reckless sizing gets flagged, not silently obeyed.
---

# Bet Units Converter

Translate between a dollar bankroll and **units (U)**, the standard way bettors normalize stake size so a plan stays consistent as the balance grows or shrinks. This skill answers three questions: what is 1U worth, what does a slip of picks cost in real dollars, and how many units is a given dollar amount.

## Why units exist (the point you must protect)

A unit is a fixed fraction of bankroll. The reason serious bettors size in units instead of dollars is **survival**: if every bet is a small, fixed slice of the roll, a losing streak can't wipe you out, and you never have to redo the math when the balance changes. The standard slice is **1-2% of bankroll**, which gives 50-100 units of runway. The further above that you go, the faster variance can bust you. So this skill never just spits out a number — it always reports what 1U is as a percentage of bankroll and flags sizing that undermines the whole point.

## The unit rule (always pin this down first)

Vincent sets the rule each time. There are three ways to express it, and you must use exactly one:

- **Total units**: "I want 5U" / "split my roll into 5" means the whole bankroll equals N units, so 1U = bankroll / N. (This is what he means by phrasings like "I have 150 and want 5U".)
- **Percent**: "1U is 2%" means 1U = bankroll x %.
- **Flat**: "1U is $3" means 1U is a fixed dollar amount regardless of balance.

If he gives a bankroll and a slip but no rule, ask which one — don't guess, because the dollar answer depends entirely on it.

## How to run it

Use the bundled script `scripts/units.py`. It does the arithmetic, prints $/unit, converts slips, converts dollars-to-units, and runs the safety check. Run it rather than doing mental math so the numbers are exact and the warnings are consistent.

```
# What is 1U worth, total-units rule:
python scripts/units.py --bankroll 150 --total-units 5

# Percent rule:
python scripts/units.py --bankroll 150 --pct 2

# Flat rule:
python scripts/units.py --bankroll 150 --flat 3

# Size a slip (units risked per pick), any rule:
python scripts/units.py --bankroll 150 --total-units 5 --slip 1.4 --slip 1.1 --slip 1.2 --slip 1.4

# Dollars back to units:
python scripts/units.py --bankroll 150 --total-units 5 --to-units 42
```

When Vincent pastes raw slip text (the kind from a Discord pick post, e.g. "England ML (-140) Risk: 1.4U"), save it to a file and pass `--slip-file`, or pipe it in with `--slip-stdin`. The script pulls every `1.4U`-style number out automatically, so you don't have to retype each stake. (Stdin is only read when `--slip-stdin` is set, so the script never hangs waiting for input.)

```
python scripts/units.py --bankroll 150 --total-units 5 --slip-file slip.txt
echo "England 1.4U, Over 1.1U, NRFI 1.4U" | python scripts/units.py --bankroll 150 --total-units 5 --slip-stdin
```

## Reading the output

The script reports 1U in dollars and as a percent of bankroll, per-pick dollar stakes, the slip total in both U and dollars, and any warnings. Relay those plainly. Note that in betting "Risk: 1.4U" means the amount **staked**, not the amount won — at negative odds you risk more than you stand to win, so the risk figure is the right one to convert.

## Don't suppress the warnings

The safety notes are the most valuable part of this skill, not noise to strip out. If 1U exceeds ~5% of bankroll, or a slip risks more than 25% of the roll, or a slip exceeds the bankroll entirely, surface that clearly and tell him why it matters. He has explicitly asked to be told when he's making a mistake rather than coddled, so when the sizing is reckless, say so directly and give the fix (smaller unit, fewer picks, or a bigger roll) instead of just running the conversion.
