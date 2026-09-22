#!/usr/bin/env python3
"""
Scout slip -> Kalshi + Polymarket tickets.

Takes a tipster slip (the kind "The Scout" posts: a side, American odds, and a
risk in units) plus Vincent's live usable cash on each platform, and produces
ready-to-enter limit-order tickets: side, limit price in cents, contract/share
count, and dollar cost. It runs the bankroll safety check and DOES NOT and CANNOT
place any orders -- it only computes what to enter. Vincent places every trade.

Unit rules (Vincent's, fixed):
  - Kalshi:     bankroll = 10U, so 1U = usable_cash / 10
  - Polymarket: 75% of bankroll = 10U, so 1U = 0.075 * usable_cash

"Usable cash" means free cash only, NOT cash + open positions. On Kalshi that is
the balance endpoint (positions are deducted from it). On Polymarket that is
buyingPower (currentBalance bundles open-position collateral and would double-count).

Polymarket cash is pulled LIVE by default via the polymarket-us SDK in the bot
folder (config key polymarket_sdk_dir). If the live pull fails for any reason
(dead key, missing node, timeout) it degrades to the last cached buyingPower from
poly_dump.json, tagged with its age, then to a --poly-cash override. The output
header always reports the true source: "live", "cached Nh old", or "override".

Usage:
  # Live pull both platforms, size a pasted slip:
  python ticket.py --slip-file slip.txt
  echo "England ML (-140) Risk: 1.4U" | python ticket.py --slip-stdin

  # Force the cached Poly path (skip the live SDK pull):
  python ticket.py --slip-file slip.txt --no-live-poly

  # Override a balance (type the number from the app):
  python ticket.py --slip-file slip.txt --poly-cash 75.32
  python ticket.py --slip-file slip.txt --kalshi-cash 100.01

  # Single platform:
  python ticket.py --slip-file slip.txt --only kalshi
"""
import argparse, glob, json, os, re, sys, time, base64, urllib.request, subprocess, shutil

# ---- locate the pnl-updater folder that holds the API keys/config ----
# The folder lives at ~/Documents/Poly & Kalshi/pnl-updater on Vincent's Mac.
# When this runs inside a sandbox it is mounted under /sessions/<id>/mnt/...,
# and the <id> changes every session -- so never hardcode one. Glob for it.
def _candidate_dirs():
    cands = [os.path.expanduser("~/Documents/Poly & Kalshi/pnl-updater")]
    cands += sorted(glob.glob("/sessions/*/mnt/Poly & Kalshi/pnl-updater"))
    cands += sorted(glob.glob("/sessions/*/mnt/*/pnl-updater"))  # folder renamed
    return cands

def find_pnl_dir(explicit=None):
    seen = set()
    for d in ([explicit] if explicit else []) + _candidate_dirs():
        if not d or d in seen:
            continue
        seen.add(d)
        if os.path.exists(os.path.join(d, "config.json")):
            return d
    return None

# ---- odds math ----
def american_to_prob(o):
    """American odds -> implied probability (also the break-even limit price)."""
    o = float(o)
    if o < 0:
        return -o / (-o + 100.0)
    return 100.0 / (o + 100.0)

# ---- slip parsing ----
def parse_slip(text):
    """Return list of picks: {desc, odds, prob, units}. One pick per non-empty line
    that carries a risk in U. Robust to the Scout's format and minor variants."""
    picks = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        um = re.search(r"(\d+(?:\.\d+)?)\s*[uU]\b", line)
        if not um:
            continue
        units = float(um.group(1))
        om = re.search(r"\(\s*([+-]\d+)\s*\)", line)
        odds = int(om.group(1)) if om else None
        # description = everything before the odds (or before Risk:), cleaned of emoji
        cut = line[:om.start()] if om else re.split(r"[Rr]isk", line)[0]
        desc = re.sub(r"[^\x00-\x7F]+", "", cut).strip(" -–\t")
        prob = american_to_prob(odds) if odds is not None else None
        picks.append({"desc": desc, "odds": odds, "prob": prob, "units": units})
    return picks

# ---- balance pulls ----
def kalshi_cash(pnl_dir):
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    cfg = json.load(open(os.path.join(pnl_dir, "config.json")))
    kid = cfg["kalshi_key_id"]
    key = serialization.load_pem_private_key(
        open(os.path.join(pnl_dir, cfg["kalshi_key_file"]), "rb").read(), password=None)
    base, pfx = "https://api.elections.kalshi.com", "/trade-api/v2"
    ts = str(int(time.time() * 1000))
    fp = pfx + "/portfolio/balance"
    sig = base64.b64encode(key.sign((ts + "GET" + fp).encode(),
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH),
        hashes.SHA256())).decode()
    req = urllib.request.Request(base + pfx + "/portfolio/balance")
    for k, v in {"KALSHI-ACCESS-KEY": kid, "KALSHI-ACCESS-SIGNATURE": sig,
                 "KALSHI-ACCESS-TIMESTAMP": ts}.items():
        req.add_header(k, v)
    with urllib.request.urlopen(req, timeout=25) as r:
        d = json.loads(r.read())
    return float(d["balance_dollars"]), float(d.get("portfolio_value", 0)), "live"

# Node module (fed to `node --input-type=module` via stdin) that reads the bot
# folder's .env at runtime and prints "BP:<buyingPower>". The secret never leaves
# that .env -- it is not written to disk, the bundle, or any output.
_POLY_LIVE_JS = r'''import { PolymarketUS } from "polymarket-us";
import fs from "fs";
function envFrom(p){const o={};if(!fs.existsSync(p))return o;for(const l of fs.readFileSync(p,"utf8").split("\n")){const m=l.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$/i);if(!m)continue;let v=m[2].trim();if((v.startsWith('"')&&v.endsWith('"'))||(v.startsWith("'")&&v.endsWith("'")))v=v.slice(1,-1);o[m[1]]=v;}return o;}
const e=envFrom(process.cwd()+"/.env");
const c=new PolymarketUS({keyId:e.POLYMARKET_KEY_ID,secretKey:e.POLYMARKET_SECRET_KEY});
const b=await c.account.balances();
const bp=(b&&b.balances&&b.balances[0])?b.balances[0].buyingPower:null;
if(bp==null){process.stderr.write("no buyingPower in balances response");process.exit(2);}
process.stdout.write("BP:"+bp+"\n");
'''

def poly_cash_live(pnl_dir):
    """LIVE buyingPower via the polymarket-us SDK in the bot folder. Shells out to
    node with cwd=bot so bare imports resolve to bot/node_modules and the .env is
    read in-place. Returns a float, or raises on any failure (caller falls back)."""
    cfg = json.load(open(os.path.join(pnl_dir, "config.json")))
    sdk_rel = cfg.get("polymarket_sdk_dir")
    if not sdk_rel:
        raise RuntimeError("no polymarket_sdk_dir in config.json")
    bot_dir = os.path.normpath(os.path.join(pnl_dir, sdk_rel))
    if not os.path.isfile(os.path.join(bot_dir, ".env")):
        raise RuntimeError("no .env in bot dir %s" % bot_dir)
    node = shutil.which("node") or "node"
    proc = subprocess.run([node, "--input-type=module"],
                          input=_POLY_LIVE_JS, cwd=bot_dir,
                          capture_output=True, text=True, timeout=45)
    if proc.returncode != 0:
        tail = (proc.stderr or "").strip().splitlines()
        raise RuntimeError("node pull rc=%d %s" % (proc.returncode, tail[-1] if tail else ""))
    m = re.search(r"BP:([0-9]+(?:\.[0-9]+)?)", proc.stdout)
    if not m:
        raise RuntimeError("no BP in node output")
    return float(m.group(1))

def poly_cash_cached(pnl_dir):
    """Last-known buyingPower from poly_dump.json with an age-based tag. This is a
    CACHE: only as good as the last pnl-updater pull. Returns (value, 'cached Nh old')."""
    dump = os.path.join(pnl_dir, "poly_dump.json")
    if not os.path.exists(dump):
        return None, "missing"
    P = json.load(open(dump))
    bp = (P.get("balances", {}).get("balances", [{}]) or [{}])[0].get("buyingPower")
    if bp is None:
        return None, "missing"
    tag = "cached"
    pulled = P.get("pulledAt")
    if pulled:
        try:
            from datetime import datetime, timezone
            t = datetime.fromisoformat(pulled.replace("Z", "+00:00"))
            secs = (datetime.now(timezone.utc) - t).total_seconds()
            tag = "cached " + (f"{secs/3600:.0f}h old" if secs >= 3600
                               else f"{secs/60:.0f}m old")
        except Exception:
            pass
    return float(bp), tag

def poly_cash(pnl_dir, allow_live=True):
    """Live first (default), then cache. Returns (value_or_None, source_tag)."""
    if allow_live:
        try:
            return poly_cash_live(pnl_dir), "live"
        except Exception:
            pass  # degrade silently to the cache; source tag stays honest
    return poly_cash_cached(pnl_dir)

# ---- ticketing ----
def tickets(picks, unit_value, platform):
    """unit_value = $/U on this platform. Returns rows + total cost."""
    rows, total = [], 0.0
    unit_name = "contracts" if platform == "kalshi" else "shares"
    for p in picks:
        stake = round(p["units"] * unit_value, 2)
        if p["prob"] is None:
            rows.append({"desc": p["desc"], "limit": None, "qty": None,
                         "cost": None, "stake": stake, "note": "no odds parsed"})
            continue
        price = round(p["prob"], 2)            # dollars per $1 contract/share
        price = min(max(price, 0.01), 0.99)
        qty = int(round(stake / price))
        cost = round(qty * price, 2)
        total += cost
        rows.append({"desc": p["desc"], "limit_cents": int(round(price * 100)),
                     "qty": qty, "qty_name": unit_name, "cost": cost,
                     "stake": stake, "odds": p["odds"]})
    return rows, round(total, 2)

def safety(cash, unit_value, total_risk, label):
    out = []
    pct_u = unit_value / cash * 100 if cash else 0
    pct_slip = total_risk / cash * 100 if cash else 0
    out.append(f"  1U = ${unit_value:,.2f} ({pct_u:.1f}% of {label} cash); slip risks "
               f"${total_risk:,.2f} ({pct_slip:.0f}% of cash)")
    if pct_u > 5:
        out.append(f"  WARNING: 1U is {pct_u:.0f}% of bankroll. Survival sizing is 1-2%. "
                   f"At this size a normal cold streak can bust the roll.")
    if total_risk > cash:
        out.append(f"  HARD STOP: slip risk ${total_risk:,.2f} exceeds usable cash "
                   f"${cash:,.2f}. Cannot place. Cut picks or shrink unit.")
    elif pct_slip > 25:
        out.append(f"  WARNING: this one slip risks {pct_slip:.0f}% of the roll. "
                   f"One bad day does serious damage. Spread across days.")
    return out

def render(label, cash, src, unit_value, rows, total, warns):
    print(f"\n=== {label.upper()}  (usable cash ${cash:,.2f}, {src}) ===")
    if src.startswith("cached"):
        print(f"  !! Poly balance is CACHED ({src}); the live SDK pull did not succeed")
        print("     this run. It is only as accurate as the last pnl-updater pull.")
        print("     Verify in-app, or rerun with --poly-cash <number from the app>.")
    hdr_qty = rows[0]["qty_name"] if rows and rows[0].get("qty_name") else "qty"
    print(f"  {'Pick':<34}{'Limit':>7}{hdr_qty:>11}{'Cost':>9}")
    for r in rows:
        if r.get("limit_cents") is None:
            print(f"  {r['desc'][:33]:<34}{'--':>7}{'--':>11}{'--':>9}  ({r.get('note','')})")
        else:
            print(f"  {r['desc'][:33]:<34}{str(r['limit_cents'])+'c':>7}"
                  f"{r['qty']:>11}{'$'+format(r['cost'],'.2f'):>9}")
    print(f"  {'TOTAL RISK':<34}{'':>7}{'':>11}{'$'+format(total,'.2f'):>9}")
    for w in warns:
        print(w)

def main():
    ap = argparse.ArgumentParser(description="Scout slip -> Kalshi/Poly tickets. Never places orders.")
    ap.add_argument("--slip-file")
    ap.add_argument("--slip-stdin", action="store_true")
    ap.add_argument("--kalshi-cash", type=float, help="Override Kalshi usable cash.")
    ap.add_argument("--poly-cash", type=float, help="Override Poly usable cash.")
    ap.add_argument("--no-live-poly", action="store_true",
                    help="Skip the live SDK pull and use the cached Poly balance.")
    ap.add_argument("--only", choices=["kalshi", "poly"], help="Limit to one platform.")
    ap.add_argument("--pnl-dir", help="Path to the pnl-updater folder with API keys.")
    args = ap.parse_args()

    text = ""
    if args.slip_file:
        text = open(args.slip_file).read()
    if args.slip_stdin:
        text += sys.stdin.read()
    if not text.strip():
        sys.exit("No slip provided. Use --slip-file or --slip-stdin.")
    picks = parse_slip(text)
    if not picks:
        sys.exit("No picks with a U risk found in the slip.")

    pnl_dir = find_pnl_dir(args.pnl_dir)
    print("SCOUT TICKETS  -  I size and price. You place every order. I never submit.")
    print(f"Parsed {len(picks)} pick(s): " + "; ".join(
        f"{p['desc']} {('('+format(p['odds'],'+d')+')') if p['odds'] is not None else '(no odds)'} {p['units']}U"
        for p in picks))

    do_k = args.only in (None, "kalshi")
    do_p = args.only in (None, "poly")

    if do_k:
        if args.kalshi_cash is not None:
            kc, src = args.kalshi_cash, "override"
        elif pnl_dir:
            try:
                kc, _pv, src = kalshi_cash(pnl_dir)
            except Exception as e:
                kc, src = None, f"FAILED ({type(e).__name__})"
        else:
            kc, src = None, "no key dir"
        if kc is None:
            print(f"\n=== KALSHI === pull {src}; pass --kalshi-cash to size.")
        else:
            uv = kc / 10.0                       # rule: bankroll = 10U
            rows, total = tickets(picks, uv, "kalshi")
            render("kalshi", kc, src, uv, rows, total, safety(kc, uv, total, "Kalshi"))

    if do_p:
        if args.poly_cash is not None:
            pc, src = args.poly_cash, "override"
        elif pnl_dir:
            pc, src = poly_cash(pnl_dir, allow_live=not args.no_live_poly)
        else:
            pc, src = None, "no key dir"
        if pc is None:
            print(f"\n=== POLYMARKET === balance {src}; pass --poly-cash to size.")
        else:
            uv = 0.075 * pc                      # rule: 75% of bankroll = 10U
            rows, total = tickets(picks, uv, "poly")
            render("polymarket", pc, src, uv, rows, total, safety(pc, uv, total, "Poly"))

    print("\nReminder: these are targets off the Scout's odds, not live order books. "
          "Confirm each market exists and the limit is reachable. You enter the orders.")

if __name__ == "__main__":
    main()
