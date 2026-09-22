# Basketball model

Winner, spread, and total use pace and efficiency, with the Four Factors as the
diagnostic underneath the efficiency numbers. The identity is points =
possessions × points per possession, so model pace and offensive/defensive
efficiency separately, then convert margin to a win probability through a normal
distribution.

## The Four Factors (what drives efficiency)

When a forecast hinges on why a team scores efficiently, decompose it with Dean
Oliver's Four Factors and their weights:
- Effective field-goal % (eFG%) — about 40% of winning, the dominant factor
- Turnover rate — about 25%
- Offensive rebound rate — about 20%
- Free-throw rate — about 15%

Regression studies that predict win totals put even more weight on shooting and
turnovers (roughly 46% eFG, 35% TOV, 12% OREB, 7% FT). Either way, shooting and
turnovers are where games are won, so weight matchups in those two first. eFG% is
also the most volatile factor game to game (3-point variance), which is the main
reason single games are noisy.

## Data to fetch first

- Offensive and defensive rating (points per 100 possessions), season and last 10
- Pace (possessions per 48) for both teams
- Four Factors for and against, to locate the matchup edge
- Confirmed injuries, rest, load management. Star availability is the single
  biggest swing on both spread and total.
- Back-to-back status and travel (second night drops efficiency)
- Home-court advantage (about 2 to 3 points NBA, larger in college)
- For college: tempo-free (KenPom/Torvik) ratings and larger home edges

## Model

1. Expected pace `P` = average of the two paces, pulled toward the slower team if
   styles clash.
2. Expected efficiency:
   - `home_pts = (home_ORtg × away_DRtg / lg_avg) × P / 100`
   - `away_pts = (away_ORtg × home_DRtg / lg_avg) × P / 100`
   Adjust for confirmed injuries and rest. Add home-court points to the home side.
3. Total = home_pts + away_pts → Over/Under the line.
4. Margin = home_pts − away_pts → spread and winner.
5. Convert projected margin to win probability with a normal distribution.
   Empirical NBA game-margin standard deviation around a good projection is
   roughly 11 to 12 points, so `P(home win) = NORMDIST(0, −margin, 11.5, TRUE)`
   in effect (probability the margin clears zero). College basketball margins are
   tighter to project per-possession but use a wider game SD near 10 to 11.
6. The favored side is the pick.

## Notes
- Star injury and rest news dominates everything else. Confirm the report and its
  timing before calling.
- Pace mismatches usually land between the two teams' paces, not at the faster
  one. Do not assume the up-tempo team imposes its pace fully.
- College has far more variance and bigger home edges than the NBA. Widen the
  confidence band.
- Single-game ceiling is real. NBA totals and spreads rarely deserve confidence
  above the high 60s given the 11-to-12-point margin noise.
