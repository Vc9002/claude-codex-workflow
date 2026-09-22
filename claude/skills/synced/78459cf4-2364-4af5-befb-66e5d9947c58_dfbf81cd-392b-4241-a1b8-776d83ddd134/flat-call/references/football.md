# Football model (NFL / CFB)

Winner, spread, total, and props use efficiency (EPA per play, success rate) plus
situation, then a normal margin distribution for win probability. Football has
small samples and high variance, so weight opponent-adjusted efficiency over raw
record.

## Use EPA, and weight offense over defense

EPA per play is one of the strongest available predictors because it is modeled
directly on points. Two findings shape how to use it:
- Weighted EPA predicts future team performance better than point differential
  and better than DVOA. Make EPA the spine of the power rating.
- Offensive EPA is "stickier" (more stable across windows) than defensive EPA, so
  trust a team's offensive EPA more than its defensive EPA, and regress defensive
  EPA harder toward the mean, especially early in a season.

## Data to fetch first

- Offensive and defensive EPA per play, pass and rush split, opponent-adjusted
- Success rate, explosive-play rate, red-zone and third-down efficiency
- Confirmed QB status. QB injury is the single largest line mover. Also key skill
  and offensive-line injuries.
- Pace and plays per game (drives totals)
- Weather: wind above ~15 mph suppresses passing and totals, plus precipitation
  and cold
- Rest: bye, short week, Thursday game, travel and time-zone change
- Home-field advantage (about 1.5 to 2.5 points NFL, larger in college)
- Props: target share, snap share, route participation, usage trend, matchup vs
  the defender or scheme

## Model

1. Net efficiency edge = (team A off EPA − team B def EPA) against the reverse,
   with defensive EPA regressed toward the mean. Translate the per-play edge to
   expected points over expected plays.
2. Build each team's expected points. The difference is the projected margin, the
   sum is the projected total. Apply home-field and weather adjustments.
3. Convert projected margin to win probability with a normal distribution. The
   NFL margin-of-victory standard deviation around a projection is about 13.5
   points (commonly 13.45 to 13.86 in the literature), so
   `P(A win) = 1 − NORMDIST(0, margin_A, 13.5, TRUE)`. College football is more
   variable, use a wider SD near 15 to 16.
4. Total vs the line gives Over/Under, larger side is the pick.
5. Props: project the stat from usage × efficiency × game script (a trailing team
   throws more, a blowout cuts a back's fourth-quarter carries), then read the
   line.

## Notes
- Confirm the QB before producing any number. A backup rewrites the forecast.
- Wind is the most underweighted total variable. Confirm it for outdoor games.
- Early-season samples are noisy. Shrink efficiency toward priors and drop
  confidence a tier through about the first quarter of the season.
- The 13.5-point NFL SD means even a clean three-point projected edge is only a
  small win-probability tilt. Keep single-game confidence honest, rarely above
  the low 70s for a side.
