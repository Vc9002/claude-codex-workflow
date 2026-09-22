# Forecasting core (calibration and conversion)

Cross-sport rules that keep the confidence number honest. Read this whenever
setting a confidence tier or converting a projected margin to a probability.

## Margin-to-probability conversion

For spread and winner markets, model the final margin as a normal variable
centered on the projected margin, with the sport's empirical margin standard
deviation. Then the win probability is the chance the margin clears zero.

| Sport | Margin SD around a projection |
|-------|-------------------------------|
| NFL | about 13.5 points (13.45 to 13.86 in the literature) |
| College football | about 15 to 16 points |
| NBA | about 11 to 12 points |
| College basketball | about 10 to 11 points |

`P(side wins) = 1 − NORMDIST(0, projected_margin_for_side, SD, TRUE)`.

The size of these SDs is the discipline. A three-point NFL edge is only a small
probability tilt, not a lock, because 13.5 points of noise swamp it. Never let a
modest projected edge become a high-confidence call.

## Empirical accuracy ceilings

These are the realistic upper bounds that good public models reach. They are why
the SKILL.md hard ceiling is 80% and why most honest calls sit in the 55 to 70
range. If a forecast wants to print above these, the data overfit or a market
price leaked in.

| Sport / market | Realistic ceiling |
|----------------|-------------------|
| Soccer match result (xG models) | around 65% |
| Tennis match winner (Elo / serve models) | around 70%, up to ~75% for top-player mismatches |
| NBA / NFL sides and totals | high 60s to low 70s on a single game |
| MLB single-game total | mid 60s, baseball is high variance |

A pick can sit above the base rate of its market and still be correct, but a
single-game confidence in the 80s is almost always a modeling error.

## Combining the base rate and the model

The historical base rate from `trend-analysis.md` is the prior. The sport model
is the situational update. Start at the base rate and move toward the model in
proportion to how much current, confirmed information the model adds beyond what
the base rate already captures.
- Model and base rate agree → confidence up a notch.
- They diverge → confidence down, and name the disagreement in the basis line.
- Data thin, stale, or a volatile input unconfirmed → confidence down a tier per
  the data-quality gate, or Pass.

## The one thing that overrides the model

Confirmed personnel and conditions news (lineups, starting pitcher, QB status,
star rest, extreme weather) moves probabilities more than any modeling
refinement. A clean model on stale personnel data is wrong. Confirm the volatile
inputs as close to event time as possible, and treat any forecast built on
unconfirmed inputs as provisional with reduced confidence.
