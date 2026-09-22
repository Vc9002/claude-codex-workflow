# Trend analysis (historical base rates)

Turn "how often does this actually happen" into a number the model can use. This
is the empirical backbone of the forecast. Count how often a line has hit in a
clean, comparable sample, and use that frequency as a prior. It never reads a
market price and never sizes a bet.

A trend is only evidence if the reference class is honest. Most bad betting
"trends" are cherry-picked samples ("5 of last 6 overs") with no predictive
value. The job here is to build a clean sample and resist that trap.

## Step 1 — Define the reference class

State precisely what you are counting before you count it. A good reference
class is specific enough to be relevant and broad enough to have a sample.
- The exact line or event (Over 2.5, −7.5 favorite, NRFI, YES on a threshold).
- The conditions that must match (same surface, same park, similar pace,
  similar team strength tier, home/away, indoor/outdoor).
- The window (this season, trailing 12 months, last N matchups). State it.

Write the reference class in one sentence. If you cannot, it is too vague.

## Step 2 — Gather the sample

Pull the actual past cases that fit the class. Record:
- Sample size N (how many qualifying past events).
- Number of hits k (how many resolved YES / over / cover).
- The dates, so you can judge staleness and regime change.

Prefer a larger, slightly looser class over a tiny, perfectly-matched one. Ten
games is noise. Aim for 30+ where possible; below 20, treat the rate as weak.

## Step 3 — Compute the empirical hit rate with a confidence interval

- Point estimate: `p_hat = k / N`.
- Wilson score interval (better than normal approximation for betting-size
  samples) for a 95% band. Report the width. A wide band means low trust.
- Example: 19 of 30 overs → p_hat = 0.63, Wilson 95% ≈ [0.45, 0.78]. The true
  rate could plausibly be anywhere in that band, so this is a lean, not a lock.

## Step 4 — Shrink small samples toward a prior

Do not trust a raw rate from a small sample. Pull it toward a sensible prior
(league average for that line, or 50%) using a Beta-binomial shrink:
- `p_shrunk = (k + a) / (N + a + b)` where `(a, b)` encode the prior. A weak
  prior of `a = b = 5` (prior mean 50%, worth 10 pseudo-games) is a reasonable
  default; use the league base rate instead of 50% when you know it.
- With N = 30, k = 19: `p_shrunk = (19 + 5)/(30 + 10) = 24/40 = 0.60`. The raw
  0.63 shrinks to 0.60 because 30 games is still modest.

Bigger samples barely move; tiny samples move a lot. That is the point.

## Step 5 — Test the trend for spuriousness

Before using it, sanity-check that the trend is real, not an artifact:
- **Cherry-picking:** would the trend survive if you moved the window by a few
  games? "5 of last 6" that becomes "5 of last 11" is noise.
- **Confounding:** is the trend really about the variable you think, or a hidden
  one (a soft schedule, a now-injured player, a since-changed lineup)?
- **Regime change:** did something structural change inside the window (new
  coach, trade, rule change, park reconfiguration)? Cut the sample at the break.
- **Multiple comparisons:** if you searched many possible trends and kept the
  striking one, discount it heavily.

If a trend fails these, drop it or widen the class and recompute.

## Step 6 — Hand the base rate to the model

The shrunk, interval-aware hit rate is the prior `p_base`. The sport model's
output is the situational update. Combine them: start at `p_base`, move toward
the model's number in proportion to how much current information (lineups,
weather, matchup) the model adds beyond what the base rate already captures.
When the model and the base rate agree, confidence rises. When they diverge,
confidence falls and the basis line should name the disagreement.

## What to put in the basis line

When a trend materially drove the call, cite it concretely: the rate, the sample
size, and the class. "Over hit 19/30 (63%) in this league's top-6 home matchups
this season" is evidence. "Trending over" is not.
