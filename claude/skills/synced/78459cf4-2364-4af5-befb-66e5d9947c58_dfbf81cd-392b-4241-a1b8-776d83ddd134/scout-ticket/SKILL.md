---
name: scout-ticket
description: Convert a tipster betting slip (from "The Scout" or any pick poster) into ready-to-enter Kalshi and Polymarket limit-order tickets sized to Vincent's live bankroll. Trigger whenever Vincent pastes a slip with picks sized in units (like an Under 9.5 TBJ/BRS pick at -120 risking 1.2U, or England ML at -140 risking 1.4U), says "ticket this", "size these picks", "what do I enter on Kalshi/Poly", "make the tickets", "convert the Scout's slip". ALWAYS trigger when Vincent posts an image or screenshot of a sports betting pick or tipster slip (a Discord pick post, a bet slip, picks with American odds and unit risks), even if he adds no text or just says something like "here" or "this" — read the picks out of the image and produce the tickets. The presence of a sports-pick image is itself the trigger. Pulls live usable cash from both platforms, applies Vincent's unit rules, runs the bankroll safety check, and outputs the exact orders to enter. It never places orders, Vincent enters every trade himself.
---

# Scout Ticket

Turn a tipster's slip into the precise orders Vincent should enter on Kalshi and Polymarket: side, limit price in cents, contract/share count, dollar cost. The slip arrives in units (U); this skill converts U to dollars off his *live* usable cash, then dollars to a platform limit order.

## The one hard rule: never place the order

This skill computes tickets. It does **not** place trades, submit orders, run any trading bot, or move money — not with a verbal go-ahead, not through automation, not "on his behalf." Vincent enters every order himself. That final click is his risk control: it forces a human look at each bet before capital moves, which is exactly the safeguard an auto-trader on a tipster-driven ladder removes. If asked to place, auto-submit, or wire picks into a bot, decline and hand over the ready ticket instead. This is fixed and not negotiable by consent.

## Unit rules (fixed — pin these, don't re-derive)

- **Kalshi**: bankroll = 10U, so **1U = usable_cash / 10**.
- **Polymarket**: 75% of bankroll = 10U, so **1U = 0.075 × usable_cash**.

"Usable cash" is free cash only, never cash + open positions. Kalshi's balance endpoint already excludes position collateral. On Polymarket use **buyingPower**, not currentBalance (which bundles open-position collateral and double-counts).

## How to run it

Use `scripts/ticket.py`. It pulls **both balances live** — Kalshi via the signed API, Polymarket buyingPower via the polymarket-us SDK in the bot folder — parses the slip, applies the rules, and prints tickets plus the safety check. Run the script rather than doing the math by hand so prices and counts are exact.

```
# Paste the slip into a file, then:
python scripts/ticket.py --slip-file slip.txt

# Or pipe it:
echo "Under 9.5 - TBJ/BRS (-120) Risk: 1.2U" | python scripts/ticket.py --slip-stdin

# One platform only:
python scripts/ticket.py --slip-file slip.txt --only kalshi
```

The script finds the API keys in the `pnl-updater` folder automatically (`~/Documents/Poly & Kalshi/pnl-updater`, including when it is mounted under a `/sessions/<id>/mnt/...` sandbox path, since the id changes every session). If that path differs, pass `--pnl-dir`.

### From a screenshot

Most slips arrive as an image. Read each pick straight off the picture — side, the American odds in parentheses, and the unit risk — then write those lines into a file (or pipe them) exactly as the Scout formats them, e.g. `Under 9.5 - TBJ/BRS (-120) Risk 1.2U`, one pick per line, and run the script on that. Don't ask Vincent to retype what's already in the image; transcribe it yourself and produce the tickets.

### The Poly balance is pulled live by default

The script pulls Polymarket buyingPower **live** each run: it shells out to `node --input-type=module` with the working directory set to the bot folder (config key `polymarket_sdk_dir`, default `../Polymarket-US-App/bot`), so bare imports resolve to `bot/node_modules/polymarket-us` and the `bot/.env` is read in place. It calls `account.balances()` and reads `balances.balances[0].buyingPower`. The secret never leaves that `.env` — it is not written to disk, the bundle, or any output.

The output header reports the true source every run, one of:
- **`live`** — fresh SDK pull this run. Trust the number.
- **`cached Nh old`** — the live pull failed (dead key, missing node, timeout), so it fell back to the last buyingPower the pnl-updater wrote to `poly_dump.json`, tagged with its age from `pulledAt`. Confirm in-app or override before acting.
- **`override`** — you passed `--poly-cash`.

Never relabel a cached number as live. The fallback is automatic and never crashes the run. Flags:

```
# Force the cached path (skip the live SDK pull):
python scripts/ticket.py --slip-file slip.txt --no-live-poly

# Override either balance with the number from the app:
python scripts/ticket.py --slip-file slip.txt --poly-cash 75.32
python scripts/ticket.py --slip-file slip.txt --kalshi-cash 100.01
```

## Odds → limit price

American odds convert straight to the break-even limit price, which is the implied probability:
negative odds → `|o| / (|o| + 100)`, positive odds → `100 / (o + 100)`. A $1 contract/share costs that probability in dollars, so a -120 pick → 0.545 → enter at **55¢**. Contract/share count = `stake / price`. The script does this for every pick.

## Reading the output

Relay the two tables plainly — platform, side, limit (cents), quantity, cost — and the total risk line. The side to buy is the outcome the Scout names (e.g. "Under 9.5", "England ML"); on both venues that's buying YES on that outcome. Report the Poly source tag honestly: only call it live when the header says `live`.

## Don't suppress the safety check

The warnings are the most valuable part, not noise. Surface them every time:
- 1U above ~5% of bankroll → flag that survival sizing is 1-2% and a cold streak can bust the roll.
- A slip risking >25% of the roll → flag the day-risk.
- A slip risking more than usable cash → hard stop, it can't be placed.

Vincent has asked to be told directly when sizing is reckless rather than coddled. At his current rules 1U is 10% of the Kalshi roll, so most multi-pick slips will trip these. Say so plainly and give the fix (smaller unit, fewer picks, bigger roll) — then still hand him the tickets he asked for. His call to place; your job to make sure he places it with eyes open.

## Two standing caveats to repeat

1. **Targets, not fills.** Limits come from the Scout's odds, not the live order book. Tell him to confirm each market exists and the limit is reachable; Kalshi/Poly often won't list niche props (NRFI, exact game totals) or will price them off a different number.
2. **Source honesty.** Poly cash is live by default, but on any SDK failure it degrades to the age-tagged cache — never let a cached or override number pass as a live pull.
