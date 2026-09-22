# Baseball / MLB model

Totals and run markets use a run-projection model driven by starting pitching,
bullpen, park, weather, and lineup handedness, then a negative binomial run
distribution. Result markets collapse the two expected-run figures to a win
probability.

## Pick the right pitcher metric

For projecting a starter's true talent, predictive value ranks SIERA slightly
ahead of xFIP, both well ahead of FIP, and all three ahead of ERA. The catch
that matters for game forecasting: the estimators' edge is largest at small
samples (around 100 innings) and essentially disappears by about 400 innings. So
for a current-season starter with limited innings, lean on SIERA or xFIP and the
projection systems. For a veteran with a long track record, the metrics converge
and you can blend them. Never forecast off raw ERA alone, since it is the least
predictive of the set.

## Data to fetch first

- Both starters: SIERA / xFIP / FIP, K%, BB%, expected workload (pitch count,
  likely innings), platoon splits vs LHB and RHB
- Bullpen: ERA/FIP, recent usage and fatigue (back-to-backs, blown innings),
  availability of high-leverage arms
- Lineups: confirmed orders, wOBA/OPS vs the opposing handedness, key bats in/out
- Park factor for runs and home runs at the venue
- Weather: temperature, wind speed and direction, humidity, roof status
- Umpire strike-zone tendency (run-suppressing vs hitter-friendly) if available
- Team defense (OAA)

Confirm the listed starters are actually starting. A late scratch rewrites the
forecast.

## Weather, quantified

Weather is often the most important situational variable for totals.
- Temperature: roughly a 1% change in home-run probability per 1 degree
  Fahrenheit (about 2% per degree Celsius). Hotter air is thinner and the ball
  carries. For scale, high heat-index games have averaged about 10.0 runs per
  game versus about 7.5 in cold, low-index games.
- Wind out 10+ mph adds carry and runs. Wind in 10+ mph kills fly balls. At 15+
  mph the effect can move the expected total by 1 to 2 runs.
- Wind is directional. "12 mph" is meaningless without direction relative to the
  field, so always get the direction, not just the speed.

## Run-projection model (totals)

1. Project each starter's expected runs allowed over likely innings from their
   rate stats applied to the opposing lineup's quality and handedness mix.
2. Project the bullpen's expected runs over the remaining innings, adjusted for
   fatigue and quality.
3. Sum to each team's expected runs scored. Apply park factor and the weather
   multiplier from above.
4. Expected total = home expected runs + away expected runs.
5. Model the total with a negative binomial, not Poisson. Team runs per game are
   overdispersed (variance > mean), the modal team total is 3 runs even though
   the mean is above 4, and Poisson misses both. Note that even negative binomial
   underestimates shutouts, so nudge low-scoring tails up slightly (zero-inflation
   intuition) when a dominant starter faces a weak lineup.
6. Read Over/Under the line. The larger side is the pick.

## Result (moneyline)

Convert the two expected-run figures to a win probability with a log5 or
Pythagorean-style estimate (more runs scored vs allowed raises win prob). Add a
bullpen edge in expected-close games. Report the favored side.

## Notes
- Starting pitching and weather are the two biggest levers on totals. Get both
  current.
- A tired bullpen on a back-to-back quietly pushes overs.
- Baseball is high variance at the single-game level. Confidence on a single MLB
  total should rarely exceed the mid 60s.
