# Soccer model

Goal markets use a Dixon-Coles model, which is a bivariate Poisson with a
low-score correction. Corners use negative binomial. Result markets use the
Dixon-Coles scoreline grid collapsed to win/draw/loss. This is the standard
academic and professional approach and it beats plain Poisson on two fronts at
once, low-scoring accuracy and adaptation speed.

## Why Dixon-Coles, not plain Poisson

Plain independent Poisson under-predicts the four low scores 0-0, 1-0, 0-1, and
1-1, which are exactly the results that decide unders, no-BTTS, and draws.
Dixon-Coles adds a dependence parameter (rho, typically small, in the rough
0.05 to 0.15 magnitude range) that lifts those four cells. Always apply this
correction. It is the single most cost-effective improvement over Poisson.

## Data to fetch first

For each team, recent matches in the relevant competition (see the recency
weighting note below for how far back):
- xG for and xG against per match. Use xG over raw goals. Shots-over-expected and
  xG are more stable team signals than goals-over-expected, so xG predicts future
  goals better than past goals do. If a league has no xG, fall back to
  opponent-adjusted goals and drop confidence one tier.
- Shots, shots on target, big chances, set-piece threat (needed for corners and
  totals)
- Home and away splits, kept separate. Home advantage is real and is modeled as
  its own parameter, not folded into form.
- Confirmed starting XI, key injuries and suspensions, rotation risk
- Rest days and travel
- Weather if outdoor and extreme, match importance (dead rubber, must-win, cup)

## Recency weighting

Weight recent matches more with exponential time decay, the Dixon-Coles xi
parameter. For in-season prediction use a half-life of roughly three to six
months, shorter than the one-to-three-year half-life the original paper used for
multi-season fitting. Do not discard the whole season for a hot streak, and do
not weight a six-month-old match equally with last week.

## Dixon-Coles scoreline model (goals, totals, BTTS, result)

1. League baseline: average home and away goals per team in this competition this
   season, `Lh` and `La`.
2. Team attack = team xG per game / league average. Team defense = team xG
   conceded per game / league average. Use time-decayed, home/away-split figures.
3. Expected goals:
   - `xG_home = home_attack × away_defense × Lh`
   - `xG_away = away_attack × home_defense × La`
   Adjust for confirmed lineup, injuries, rest. Apply the separate home-advantage
   term to the home side.
4. Build the scoreline grid for 0..6 each side as the product of two Poissons,
   then apply the Dixon-Coles rho correction to the four low-score cells.
5. Collapse to the market:
   - Over/Under 2.5: cells with i + j >= 3 vs <= 2
   - BTTS yes: cells with i >= 1 and j >= 1
   - Result: i > j (home), i = j (draw), i < j (away)
6. The larger side is the pick. Report its grid probability, then apply the
   SKILL.md confidence calibration.

## Corners (negative binomial)

Corner counts are overdispersed, variance exceeds the mean, so negative binomial
fits better than Poisson and a Poisson here understates the spread of outcomes.
1. Fetch corners for and against per game, time-decayed, last 6 to 10 matches.
2. Expected corners each side via the same strength-ratio method as goals, with
   shots volume as a supporting input (high-shot sides generate more corners off
   blocks and deflections).
3. Total expected corners = both sides, adjusted for game state and style (a team
   chasing takes more corners, a low block concedes territory and corners).
4. Model the total negative binomial and read Over/Under the line. Calibrate
   expectations: good public corner models still carry average error near 1.9 to
   2.1 corners per game, so corner confidence should rarely reach the top tier.

## Notes
- Confirm the XI before any goals call. A first-choice striker or keeper out
  moves totals more than any ratings tweak.
- Live markets are dominated by game state and red cards. Weight current
  scoreline and the man-advantage above pre-match ratings.
- Empirical ceiling: even strong xG-based outcome models land around 65% match
  result accuracy, so do not output match-result confidence above the high 70s.
