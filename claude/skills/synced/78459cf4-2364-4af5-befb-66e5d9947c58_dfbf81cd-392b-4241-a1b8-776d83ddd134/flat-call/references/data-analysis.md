# Data analysis (gathering, cleaning, weighting)

Garbage in, garbage out. A simple model on clean, current, correctly-weighted
data beats a fancy model on stale or biased data. This file governs how to
source and treat the inputs before they ever reach a model. Every flat-call
forecast passes through this discipline.

## 1 — Source quality and hierarchy

Prefer primary, structured stats over secondary commentary.
- Tier 1: dedicated stats sources for the sport (FBref/Understat for soccer xG,
  Baseball Savant/FanGraphs for MLB, KenPom/Bart Torvik for CBB, official league
  stats, weather services for conditions).
- Tier 2: reputable aggregators and beat reporters for lineups and injuries.
- Tier 3: general sports media. Use for leads, not as the number of record.
Never use a betting/prediction market price or any implied probability as a data
input. That is the no-market-bias rule and it is absolute.

When two sources disagree, prefer the more primary one and note the conflict by
lowering confidence.

## 2 — Recency and weighting

Recent data is more predictive but noisier; old data is stable but stale. Weight
deliberately rather than averaging blindly.
- Use exponential or linear recency weighting: the last 5 to 6 games carry more
  weight than games from months ago, but do not discard the season entirely or
  you overfit a hot or cold streak.
- Separate home and away, and surface or park, before averaging. Pooling them
  hides real splits.
- For early-season samples, shrink toward last season or league priors (see the
  Beta-binomial shrink in trend-analysis.md). Do not trust 4-game rate stats.

## 3 — Adjust for context, do not use raw numbers

Raw stats are confounded. Adjust before modeling.
- **Opponent strength:** 2.0 xG against bottom sides is not 2.0 against the top.
  Use opponent-adjusted figures where available, or adjust manually.
- **Schedule and rest:** back-to-backs, short weeks, deep prior-round runs all
  depress output. Flag and discount.
- **Personnel:** a stat line built with a now-injured key player is a different
  team. Re-weight or discard pre-injury data when the lineup has changed.
- **Venue and conditions:** park factors, altitude, indoor/outdoor, weather. Apply
  the multiplier; do not bury it.

## 4 — Confirm the volatile inputs

Some inputs move probabilities far more than any modeling choice. Confirm these
as close to event time as possible, and treat the forecast as provisional until
they are confirmed:
- Starting lineups / starting pitcher / confirmed QB
- Injury and rest/load-management status
- Weather for outdoor events
- Any late news (suspension, personal absence, motivation/dead rubber)
If a volatile input is unconfirmed, say so and lower confidence a tier.

## 5 — Data-quality gate before output

Run this checklist before producing any pick. If it fails, lower confidence or
return Pass rather than guessing.
- Is the core data current (this season, recent games), not from memory?
- Are lineups / pitcher / QB / weather confirmed where they matter?
- Is the sample big enough, or has it been shrunk toward a prior?
- Have raw numbers been adjusted for opponent, venue, and rest?
- Do independent sources agree, or has the conflict been priced into confidence?
- Did any market price leak into the inputs? (It must not.)

## 6 — Combine into the forecast

Hand the cleaned, weighted, adjusted inputs to the sport model and the base rate
from trend-analysis.md. The model produces the situational probability; the base
rate anchors it; data quality sets how far confidence can go. The basis line in
the output must cite the actual cleaned numbers used, with their recency, so the
call is auditable. Numbers and dates, not adjectives.
