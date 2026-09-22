---
name: hoi4-mod-doctor
description: Diagnose and fix Hearts of Iron IV (HOI4) mod playlists. Use this skill whenever the user wants to optimize mod load order, bugcheck a playlist for compatibility problems, find broken/missing mods, detect conflicting overhauls, or clean up their Paradox launcher setup. Trigger on phrases like "optimize my HOI4 load order", "bugcheck my playlist", "why do my HOI4 mods crash", "check my mod compatibility", "fix my Paradox launcher", "look over my playlists", or any mention of HOI4 mods, playsets, the Road to 56 / Kaiserreich / TNO / Millennium Dawn stacks, or the launcher-v2.sqlite database. Use it even if the user only says "look at my mods" in a HOI4 context.
---

# HOI4 Mod Doctor

Reads the Paradox launcher database, reorders mods into a sane load order, and scans every playlist for the things that actually break HOI4: missing mods, stacked total-conversions, and version drift. It never deletes or disables mods unless explicitly asked — it only reorders and reports.

## Where the data lives

The launcher stores everything in a SQLite file, **not** in loose text files:

- Windows: `Documents/Paradox Interactive/Hearts of Iron IV/launcher-v2.sqlite`
- macOS: `~/Documents/Paradox Interactive/Hearts of Iron IV/launcher-v2.sqlite`
- Linux: `~/.local/share/Paradox Interactive/Hearts of Iron IV/launcher-v2.sqlite`

If you also see `launcher-v2_openbeta.sqlite`, check both — the live one is whichever was **modified most recently** and has the most playsets. The 2021-era openbeta file is usually stale; don't write to it. `dlc_load.json` is the file the *game* reads, but the launcher regenerates it from the active playset, so you fix order in the database, not there.

Relevant tables: `playsets` (id, name, isActive, isRemoved), `playsets_mods` (playsetId, modId, enabled, position — **lower position = loaded first**), `mods` (id, displayName, steamId, requiredVersion, tags, status).

## Workflow

1. **Locate the database.** Ask for or request access to the HOI4 folder if you don't have it. Confirm which `.sqlite` is live (most recent mtime, most playsets, has an `isActive=1` playset).
2. **Run the engine.** Use `scripts/hoi4_doctor.py`. It always produces a report. It only writes load-order changes when you pass `--optimize`, and it always makes a timestamped backup first.
3. **Bugcheck before reorder.** The compatibility findings are the high-value output. Load order barely matters for cosmetic-only stacks; it matters a lot for overhaul stacks. Say so honestly rather than overselling the reorder.
4. **Warn about the launcher.** If the Paradox launcher is running when you write, it can overwrite your changes on close. Always tell the user to close it first, then reopen to verify.

### Running the engine

```bash
# Report only (safe, no writes) — always start here
python3 scripts/hoi4_doctor.py --db "<path>/launcher-v2.sqlite" --report report.md

# Apply optimized load order (makes a backup, writes positions, then reports)
python3 scripts/hoi4_doctor.py --db "<path>/launcher-v2.sqlite" --optimize --report report.md
```

The script self-locates the DB if `--db` is omitted and a HOI4 folder is on a standard path, but passing it explicitly is more reliable.

## Load-order hierarchy (top → bottom)

HOI4 rule: **a mod lower in the list overrides a mod higher up.** So big foundational content goes on top and targeted overrides go on the bottom. The engine sorts each playlist into these tiers, preserving the user's relative order *within* a tier:

1. Total-conversion / overhaul **base** (RT56, Kaiserreich, TNO, Millennium Dawn, The Fire Rises, World Ablaze, Great War Redux, Old World Blues, etc.)
2. Official **submods / expansions** of that overhaul
3. **Gameplay / mechanics** mods
4. **Map, performance, graphics overhauls**
5. **UI / HUD / QoL**
6. **Cosmetic** — icons, flags, portraits, country names (last, so they win as intended)
7. **Compatibility patches** (very bottom — they exist to override everything they touch)

It also fixes known add-on/base ordering (e.g. the `{AIGFX} Visible Railroads: Supply Map Mode` add-on must load after its base mod).

To extend the overhaul list or tier rules, edit the dictionaries at the top of `scripts/hoi4_doctor.py` — they're written to be edited.

## What the bugcheck flags

- **CRITICAL — broken enabled mods:** any mod that is `enabled` but whose `status` is not `ready_to_play` (`unsubscribed` = not downloaded, `invalid_mod` = incompatible/dead). These silently don't load; the playlist isn't what it looks like. If the *base overhaul* is among them, the whole playlist is broken.
- **CRITICAL — stacked overhauls:** two or more total-conversion mods enabled in one playlist almost always conflict or crash (e.g. TNO base + a separate standalone like "Long and Arduous Road"). Flag and tell the user to pick one.
- **MEDIUM — mechanics mods over an overhaul:** suites like "Better Mechanics" edit the same core combat/AI/production files a big overhaul does. They can coexist, but last-loaded wins — call out which is overriding which.
- **MEDIUM — incoherent playlist:** the named base is disabled while leftovers are enabled, or nearly everything is off (often a scratch "Clone of…" copy).
- **LOW — version drift:** gameplay mods whose `requiredVersion` is several minor versions below the newest mod in the list are the first suspects for errors. Cosmetic/flag/icon mods almost always survive version bumps, so don't over-flag them.
- **Duplicates:** the same Steam ID enabled twice in one playlist.

## Report structure

Lead with an honest assessment, then severity-ordered findings, then a per-playlist status table:

```
# HOI4 Playlist Optimization & Compatibility Report
## What I changed            (only if --optimize; name the backup file)
## Honest assessment first   (where order matters vs. where it doesn't)
## CRITICAL                  (broken playlists, stacked overhauls)
## MEDIUM                    (likely conflicts to test)
## LOW                       (version drift)
## Per-playlist status table (Playlist | Enabled | Broken | Verdict)
```

Leave re-subscribing or disabling mods to the user — that changes what content they actually play, so it's their call, not an automatic edit.
