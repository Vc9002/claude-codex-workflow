#!/usr/bin/env python3
"""
HOI4 Mod Doctor — optimize load order and bugcheck Paradox launcher playlists.

Reads launcher-v2.sqlite, sorts each playlist into the standard HOI4 load-order
hierarchy (overhauls on top, cosmetics on the bottom so they win conflicts),
and scans for the problems that actually break HOI4: missing/broken enabled
mods, two total-conversions stacked in one list, and version drift.

Safe by default: writes nothing unless --optimize is passed, and always makes a
timestamped backup of the database before writing. Never removes or disables a
mod — it only changes load-order `position` values.

Usage:
    python3 hoi4_doctor.py --db /path/launcher-v2.sqlite --report report.md
    python3 hoi4_doctor.py --db /path/launcher-v2.sqlite --optimize --report report.md

Edit the OVERHAULS / SUBMODS / keyword lists below to teach it new mods.
"""
import argparse, os, sqlite3, sys, shutil, glob, time

# ---- Tunable knowledge base (edit these to extend) -------------------------

# Steam workshop IDs of total-conversion / overhaul BASE mods (tier 0).
OVERHAULS = {
    "820260968":   "The Road to 56",
    "2828712151":  "Eight Years' War of Resistance",
    "2438003901":  "The New Order: Last Days of Europe",
    "3256452254":  "TNO: Long and Arduous Road",
    "2777392649":  "Millennium Dawn",
    "3350890356":  "The Fire Rises",
    "2149567872":  "World Ablaze",
    "3365515312":  "The Great War Redux",
    "2419469750":  "Fields of Anime",
    # add your own: "<steamId>": "Name",
}
# Submods / official expansions that belong directly under their base (tier 1).
SUBMODS = {
    "3506850939","3565915572","3441455702","3226205718","2129060088",   # RT56 family
    "3306973445","3350747146","3583339918","2980739000","3535686157",   # TNO family
    "3458558897","3350892196","3480142041","3561017215","3604257135",   # TFR family
    "3660997335","3453884475","3573532989",
}
# Compatibility patches that should sit at the very bottom (tier 7).
PATCH_KW = ["compatibility patch", "compat patch", "patch for", "submod patch"]
# Cosmetic / visual override mods (tier 6 — load last so they win).
COSMETIC_KW = ["colou", "color", "uncensored", "realistic & immersive", "coats of arms",
    "flag", "emblem", "portrait", "icon", "anime", "propaganda", "party names",
    "faction names", "insignia", "puppet flags", "enhanced", "war flags", "abwehr"]
# UI / HUD / QoL (tier 5).
UI_KW = ["stats expanded", "topbar", "battle plans", "combat view", "theater box",
    "fog of war", "focus filter", "rename factions", "host tool", "tension suggestion",
    "super events", "spy reminder", "speeches", "news headlines", "advertisement",
    "minimalistic", "large combat", "larger theater", "decisions", "medal", "授勋"]
# Map / performance / graphics overhauls (tier 4).
MAP_KW = ["smooth iron", "fps map", "spot optimization", "texture overhaul",
    "border overhaul", "makeshift bridge", "visible railroad"]
# Mechanics suites that conflict with big overhauls (for the MEDIUM warning).
MECHANICS_KW = ["better mechanics"]
# Known add-on -> base ordering fixes (addon steamId must load after base steamId).
ADDON_AFTER_BASE = {"2698816291": "2690450515"}  # AIGFX Supply Map Mode after base

# ---------------------------------------------------------------------------

def find_db():
    home = os.path.expanduser("~")
    cands = [
        os.path.join(home, "Documents", "Paradox Interactive", "Hearts of Iron IV", "launcher-v2.sqlite"),
        os.path.join(home, ".local", "share", "Paradox Interactive", "Hearts of Iron IV", "launcher-v2.sqlite"),
    ]
    cands += glob.glob(os.path.join(home, "**", "Hearts of Iron IV", "launcher-v2.sqlite"), recursive=True)
    live = [c for c in cands if os.path.exists(c)]
    return max(live, key=os.path.getmtime) if live else None

def tier(steam, name):
    s = str(steam); n = (name or "").lower()
    if s in OVERHAULS: return 0
    if s in SUBMODS: return 1
    if any(k in n for k in PATCH_KW): return 7
    if any(k in n for k in COSMETIC_KW): return 6
    if any(k in n for k in UI_KW): return 5
    if any(k in n for k in MAP_KW): return 4
    return 3  # gameplay default

def sort_key(idx, steam, name):
    s = str(steam)
    base_pull = 0
    sub = 0
    if s in ADDON_AFTER_BASE:      # addon: push just after its base, keep tier
        sub = 1
    elif s in ADDON_AFTER_BASE.values():
        sub = -1
    return (tier(s, name), idx, sub)

def ver_tuple(v):
    """Return (major, minor) or None. Returns None for wildcard/broad-compat
    versions like '1.*' or '*' so they aren't flagged as drifting."""
    if not v: return None
    segs = str(v).split(".")
    if len(segs) < 2 or "*" in segs[0] or "*" in segs[1]:
        return None
    try:
        return (int(segs[0]), int(segs[1]))
    except ValueError:
        return None

def load(db):
    con = sqlite3.connect(db); cur = con.cursor()
    mods = {}
    for mid,name,dname,steam,req,tags,status in cur.execute(
        "SELECT id,name,displayName,steamId,requiredVersion,tags,status FROM mods").fetchall():
        mods[mid] = {"name": dname or name, "steam": steam, "req": req,
                     "tags": tags, "status": status}
    playsets = []
    for pid,pname,active in cur.execute(
        "SELECT id,name,isActive FROM playsets WHERE isRemoved=0").fetchall():
        rows = cur.execute(
            "SELECT modId,enabled,position FROM playsets_mods WHERE playsetId=? ORDER BY position",
            (pid,)).fetchall()
        items = []
        for modId,en,pos in rows:
            m = mods.get(modId, {"name": "??missing "+str(modId), "steam": None,
                                 "req": None, "tags": None, "status": "missing_in_db"})
            items.append({"id": modId, "en": en, "pos": pos, **m})
        playsets.append({"id": pid, "name": pname, "active": active, "mods": items})
    con.close()
    return playsets

def optimize(db, playsets):
    ts = time.strftime("%Y%m%d_%H%M%S")
    backup = os.path.join(os.path.dirname(db), f"launcher-v2_backup_preLoadOrder_{ts}.sqlite")
    shutil.copy2(db, backup)
    con = sqlite3.connect(db); cur = con.cursor()
    for ps in playsets:
        ordered = sorted(enumerate(ps["mods"]),
                         key=lambda t: sort_key(t[0], t[1]["steam"], t[1]["name"]))
        for newpos, (_, m) in enumerate(ordered):
            cur.execute("UPDATE playsets_mods SET position=? WHERE playsetId=? AND modId=?",
                        (newpos, ps["id"], m["id"]))
    con.commit(); con.close()
    return backup

def bugcheck(playsets):
    findings = {}
    for ps in playsets:
        f = {"broken": [], "overhauls": [], "mechanics_over_overhaul": False,
             "incoherent": False, "version": [], "dupes": []}
        enabled = [m for m in ps["mods"] if m["en"]]
        # broken enabled
        f["broken"] = [(m["name"], m["status"]) for m in enabled
                       if m["status"] not in ("ready_to_play",)]
        # stacked overhauls (enabled)
        f["overhauls"] = [m["name"] for m in enabled if str(m["steam"]) in OVERHAULS]
        # mechanics over overhaul
        has_overhaul = bool(f["overhauls"])
        has_mech = any(any(k in (m["name"] or "").lower() for k in MECHANICS_KW) for m in enabled)
        f["mechanics_over_overhaul"] = has_overhaul and has_mech
        # incoherent: overhaul present in list but disabled, or <25% enabled
        base_present = [m for m in ps["mods"] if str(m["steam"]) in OVERHAULS]
        base_disabled = base_present and not any(m["en"] for m in base_present)
        mostly_off = len(ps["mods"]) >= 8 and len(enabled) < 0.25*len(ps["mods"])
        f["incoherent"] = bool(base_disabled or mostly_off)
        # version drift among enabled gameplay mods
        vers = [ver_tuple(m["req"]) for m in enabled if ver_tuple(m["req"])]
        if vers:
            newest = max(vers)
            for m in enabled:
                vt = ver_tuple(m["req"])
                n = (m["name"] or "").lower()
                is_cos = any(k in n for k in COSMETIC_KW)
                if vt and not is_cos and (newest[0]-vt[0])*100+(newest[1]-vt[1]) >= 5:
                    f["version"].append((m["name"], m["req"]))
        # duplicates
        seen = {}
        for m in enabled:
            seen.setdefault(m["steam"], []).append(m["name"])
        f["dupes"] = [v for k,v in seen.items() if len(v) > 1 and k]
        findings[ps["name"]] = f
    return findings

SEV = {"broken":"CRITICAL","overhauls":"CRITICAL","mechanics_over_overhaul":"MEDIUM",
       "incoherent":"MEDIUM","version":"LOW","dupes":"MEDIUM"}

def report(playsets, findings, backup=None):
    L = []
    L.append("# HOI4 Playlist Optimization & Compatibility Report")
    L.append(f"_Generated {time.strftime('%Y-%m-%d %H:%M')} · {len(playsets)} playlists_\n")
    if backup:
        L.append("## What I changed")
        L.append("Reordered every playlist into the standard load-order hierarchy "
                 "(overhauls on top, cosmetics on the bottom). **Nothing removed or disabled.**")
        L.append(f"\nBackup: `{os.path.basename(backup)}` — restore by renaming it to "
                 "`launcher-v2.sqlite` if needed.\n")
        L.append("> Close the Paradox launcher before launching, then reopen it, or it may "
                 "overwrite the new order.\n")
    # severity buckets
    crit, med, low = [], [], []
    for name, f in findings.items():
        if f["overhauls"] and len(f["overhauls"]) > 1:
            crit.append(f"**{name}** — {len(f['overhauls'])} total-conversions enabled at once "
                        f"({', '.join(f['overhauls'])}). Pick one; stacking overhauls conflicts/crashes.")
        if f["broken"]:
            crit.append(f"**{name}** — {len(f['broken'])} enabled mod(s) won't load "
                        f"(missing/invalid): " + ", ".join(f"{n} [{s}]" for n,s in f["broken"][:8])
                        + (" …" if len(f["broken"])>8 else ""))
        if f["mechanics_over_overhaul"]:
            med.append(f"**{name}** — mechanics suite (e.g. Better Mechanics) runs on top of a "
                       "total-conversion; they edit the same core files. Test combat/AI; last-loaded wins.")
        if f["incoherent"]:
            med.append(f"**{name}** — incoherent playlist (base disabled or almost everything off). "
                       "Looks like a scratch copy; rebuild or delete.")
        for d in f["dupes"]:
            med.append(f"**{name}** — duplicate mod enabled twice: {d}")
        if f["version"]:
            low.append(f"**{name}** — gameplay mods well behind the newest in the list: "
                       + ", ".join(f"{n} ({v})" for n,v in f["version"][:6]))
    L.append("## Honest assessment first")
    L.append("Load order matters a lot for overhaul stacks and barely at all for cosmetic-only "
             "lists. For those, the real fixes are the broken-mod and stacked-overhaul findings below.\n")
    for title, bucket in [("CRITICAL — fix before playing", crit),
                          ("MEDIUM — likely conflicts, test these", med),
                          ("LOW — version drift", low)]:
        L.append(f"## {title}")
        if bucket:
            L += [f"- {x}" for x in bucket]
        else:
            L.append("- none found")
        L.append("")
    # table
    L.append("## Per-playlist status")
    L.append("| Playlist | Enabled | Broken | Verdict |")
    L.append("|---|---|---|---|")
    for ps in playsets:
        f = findings[ps["name"]]
        en = sum(1 for m in ps["mods"] if m["en"])
        broken = len(f["broken"])
        if broken and f["overhauls"] and any("missing" in s or "unsub" in s for _,s in f["broken"]):
            verdict = "Broken — missing content"
        elif len(f["overhauls"]) > 1:
            verdict = "Two overhauls — pick one"
        elif broken:
            verdict = f"Clean up {broken} missing"
        elif f["mechanics_over_overhaul"]:
            verdict = "Test mechanics vs overhaul"
        elif f["incoherent"]:
            verdict = "Incoherent — rebuild"
        else:
            verdict = "Clean"
        active = " (active)" if ps["active"] else ""
        L.append(f"| {ps['name']}{active} | {en} | {broken} | {verdict} |")
    L.append("\n_Re-subscribing or disabling mods is left to you — it changes what you actually play._")
    return "\n".join(L)

def main():
    ap = argparse.ArgumentParser(description="HOI4 Mod Doctor")
    ap.add_argument("--db", help="path to launcher-v2.sqlite (auto-located if omitted)")
    ap.add_argument("--optimize", action="store_true", help="write optimized load order (makes a backup)")
    ap.add_argument("--report", default="hoi4_report.md", help="output report path")
    args = ap.parse_args()
    db = args.db or find_db()
    if not db or not os.path.exists(db):
        sys.exit("Could not find launcher-v2.sqlite. Pass --db with the full path.")
    print(f"Database: {db}")
    playsets = load(db)
    print(f"Found {len(playsets)} playlists.")
    backup = optimize(db, playsets) if args.optimize else None
    if backup:
        print(f"Backup written: {backup}")
        playsets = load(db)  # reload post-write
    findings = bugcheck(playsets)
    rep = report(playsets, findings, backup)
    with open(args.report, "w", encoding="utf-8") as fh:
        fh.write(rep)
    print(f"Report written: {args.report}")
    # console summary
    for name, f in findings.items():
        if f["broken"] or len(f["overhauls"])>1:
            print(f"  ! {name}: {len(f['broken'])} broken, "
                  f"{len(f['overhauls'])} overhauls enabled")

if __name__ == "__main__":
    main()
