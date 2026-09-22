# Tennis model — data-adaptive

The model fits the data you can actually pull. Try for the richest tier first;
if the inputs aren't there, drop to the next tier automatically and lower the
confidence ceiling with it. Never fabricate serve splits to stay in a higher
tier — degrade honestly and say which tier you used in the Method line.

Run the tier-selection first, then the math for that tier, then the live overlay
if the match is in progress, then the calibration cap.

## Tier selection (pick the highest tier the data supports)

| Tier | Data you could fetch (surface-specific, last ~12mo + last 10) | Method | Confidence ceiling |
|------|---------------------------------------------------------------|--------|-------------------|
| A — Serve-structural | Service & return points won %, hold/break %, 1st/2nd-serve %, ace/DF, on this surface | Full serve model + rating prior | up to ~75% |
| B — Rating-driven | Surface Elo/Glicko, games won-lost, form last 10 (quality-adj), H2H | Rating model on games | up to ~65% |
| C — Ranking/base-rate | Current ranking, recent W/L, surface record only | Ranking-gap prior + base rate | up to ~58% |

Most ATP/WTA main-draw and top-100 players reach Tier A. Sub-#150 players,
qualifiers, and Challenger fields usually bottom out at Tier B or C — that is
the expected case, not a failure. State the tier; do not pretend to Tier A
precision on Tier C data.

## Tier A — serve-structural (preferred)

1. Clean the inputs: surface-specific, exponentially recency-weighted, and
   **opponent-adjusted** (regress serve-points-won against the return quality of
   opponents actually faced, not raw tour average). Shrink thin samples toward
   the surface/tour prior.
2. Barnett-Clarke serve adjustment for player i serving to opponent j:
   `f_ij = f_t + (f_i − f_av) − (g_j − g_av)`
   where f_t = tournament avg serve-points-won, f_i = i's serve rate, f_av =
   tour avg serve, g_j = j's return-points-won, g_av = tour avg return. Compute
   for both players → each player's point-win-on-serve p_s.
3. Propagate p_s point → game → set → match (iid-points assumption) to a match
   win probability. This is the structural number.
4. Blend with the rating prior (Tier B output) ~70/30 structural/prior; shade
   toward the prior when the serve sample is thin.

## Tier B — rating-driven (fallback when serve splits are missing)

1. Use surface-weighted Glicko-2 if available (it carries a rating deviation =
   built-in uncertainty), else surface-weighted Elo. Rate on **games** won/lost,
   not just match W/L, to extract more signal per match.
2. Blended rating `R = 0.8 × overall + 0.2 × surface` as the floor; go
   surface-heavier for extreme style/surface mismatches (clay grinder on grass).
3. Win prob: `P_A = 1 / (1 + 10^((R_B − R_A)/400))`.
4. Widen the implied error (lower the reported confidence) when either player's
   rating deviation / data recency is poor.

## Tier C — ranking/base-rate (last resort)

1. Convert the ranking gap to a rough prior win probability (bigger gap → higher
   prior, but compress hard: ranking is a noisy proxy and qualifying compresses
   the field).
2. Anchor to the trend-analysis base rate for "favorite of this ranking-gap size
   on this surface/round."
3. Cap at ~58%. If the gap is small or the data is stale, this is a Pass.

## Live overlay (any tier, in-progress match)

The pre-match tier sets the prior; the live score updates it.
1. Start from the tier's pre-match win probability.
2. Bayesian-update each player's p_s (Tier A) or rating (Tier B/C) with the
   points/games actually observed this match — partial pooling, so a hot set
   nudges the prior without replacing it. Avoid overreacting to one break.
3. Recompute the match win probability from the **current exact score** and who
   serves next. In a deciding set, score and server dominate the profiles.
4. State the single flip condition (e.g. "if returner breaks for 3-1, flip").

Note: Wimbledon and most Slams play a 10-point tiebreak at 6-6 in the final set;
at 6-6 the match collapses to a near-coin-flip breaker where the bigger server
and steadier nerves get a small edge.

## Reconcile, adjust, calibrate

1. If the structural (A) and rating (B) numbers disagree sharply, trust the
   serve model on fast/serve-dominant surfaces (grass, indoor hard) and the
   rating model on slow surfaces (clay); drop one confidence tier for the
   disagreement.
2. Adjust for fatigue and injury, which ratings lag badly — a player off a long
   five-setter or deep run is overrated until results catch up.
3. Calibrate against history: track Brier score / log-loss on resolved calls
   (the `log` skill) and trust the tier whose past calls were best calibrated.
   A confident number that isn't calibration-checked is just an assertion.

## Ceilings

Roughly 70% overall, up to ~75% for clear top-player mismatches with full Tier A
data. Never output tennis confidence above the high 70s. Each tier down lowers
the ceiling per the table — that is the model fitting the data, by design.
