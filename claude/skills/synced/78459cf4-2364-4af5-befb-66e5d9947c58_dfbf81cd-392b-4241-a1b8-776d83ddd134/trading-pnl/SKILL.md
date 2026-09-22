---
name: trading-pnl
description: >
  Refresh and rebuild Vincent's consolidated prediction-market P&L statement (Polymarket US + Kalshi).
  Trigger whenever Vincent says "update my pnl", "refresh my trading p&l", "pnl statement", "how am I
  doing on poly / kalshi", "rebuild my p&l sheet", "what's my trading profit", or asks for current
  combined profit/loss across his Polymarket US and Kalshi accounts. Pulls both accounts live via API,
  reconciles deposits/withdrawals/credits/open-positions, and writes a formatted multi-tab Excel workbook
  with charts. Never invents numbers — everything is pulled live and reconciled by identity.
---

# Trading P&L (Polymarket US + Kalshi)

This skill produces **Trading P&L Statement (auto).xlsx** — a consolidated, verified P&L across
Vincent's Polymarket US and Kalshi accounts.

## How to run it

The whole pipeline is one self-contained script. Run exactly:

```
cd "<POLY_KALSHI_FOLDER>/pnl-updater" && python3 update_pnl.py
```

`<POLY_KALSHI_FOLDER>` is Vincent's connected "Poly & Kalshi" directory (in the workspace shell it is
mounted under `/sessions/<id>/mnt/Poly & Kalshi/`). The `pnl-updater/` folder there holds the live copy
of `update_pnl.py`, `pull_poly.mjs`, `config.json`, the Kalshi private key, and the persistent
`trades_ledger.csv`.

The script:
1. Pulls Polymarket US live via its bundled SDK (`portfolio/activities`, `account/balances`, `portfolio/positions`).
2. Pulls Kalshi live via the saved RSA key (`deposits`, `withdrawals`, `settlements`, `balance`).
3. Recomputes every figure, rebuilds all dynamic tabs, recalculates in place, and writes the .xlsx.
4. Prints a final line starting with `SUMMARY |`.

If `cryptography` or `openpyxl` is missing: `pip install cryptography openpyxl --break-system-packages`.
If node says it can't find `polymarket-us`, just retry once (the script copies its puller into the SDK folder at runtime).

After it runs, **present the .xlsx with `present_files`** and relay the `SUMMARY |` line. Do not
re-derive numbers by hand — trust the script.

## The P&L methodology (do not change — these make the numbers correct)

- **Polymarket P&L** = (cash balance + open positions at cost basis + completed withdrawals) − deposits − promotional credits.
  Open positions MUST be valued at cost (the API's `assetNotional` is often 0 for sports and would wrongly drop deployed capital).
  Pending withdrawals stay inside the cash balance (they are reserved, not yet sent), so they are not added back.
- **Kalshi P&L** = balance + withdrawals − deposits − `kalshi_credit_usd`. The credit input (default $44.68)
  makes it match Kalshi's official profile profit (−$219.45). Do NOT sum per-settlement (payout − cost − fees):
  that double-counts gross cost basis from buy/sell/rebuy churn and overstates the loss (it gives ≈ −$775, which is wrong).
- **Past transactions are preserved** via `trades_ledger.csv` (append new fills, dedup by trade id, never drop old ones).
- **R&D / operating costs**: Claude tooling ($45 flat) + sports pick book ($15/week, auto-escalating via `TODAY()`).
- **Bank Account (cash in pocket)** = cashed out (total withdrawals) − pick book − Claude.

## Reconciliation invariants (sanity checks)

- Polymarket: deposits + credits + P&L = total equity (cash + open at cost). e.g. 130 + 125.19 + 568.21 = 823.40.
- Polymarket: equity − pending withdrawals = buying power. e.g. 823.40 − 327.80 = 495.60.
- Kalshi: deposits + credit − withdrawals − profit = ending balance. e.g. 236 + 44.68 − 61.22 − 219.45 ≈ 0.

If any invariant breaks, stop and investigate before presenting — usually it means a new open position,
a completed withdrawal, or a new deposit/credit the formula needs to account for.

## Config

`pnl-updater/config.json` holds the editable inputs (Claude cost, pick-book rate + start date, Kalshi
credit, file paths). The Kalshi private key lives next to it as `kalshi-private-key.pem` and stays in
Vincent's folder — it is intentionally NOT bundled in this skill. See `scripts/config.example.json` for the shape.
