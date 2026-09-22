# General market path (non-sport Kalshi / Polymarket)

Use this when the market has no sport model: economics releases, politics,
weather, awards, crypto thresholds, entertainment, or any event contract. The
discipline is the same. Build a probability from evidence, never from the
contract price.

## Process

1. **Define the resolution exactly.** Read what makes the contract resolve YES.
   The wording (threshold, date, source, rounding) is the whole game. Get it
   precise before estimating anything.

2. **Find the base rate.** How often has this kind of event happened in
   comparable past cases. This is the anchor. See `references/trend-analysis.md`
   for building a clean reference class and computing the historical hit rate.

3. **Gather current evidence.** Pull the live inputs specific to this event:
   - Economics (CPI, jobs, GDP, Fed): economist consensus surveys, nowcasts
     (e.g. Cleveland Fed, Atlanta Fed GDPNow), recent surprise history. Do not
     use fed-funds futures or any market-implied probability as an input.
   - Politics (elections, confirmations): polling averages, fundamentals
     (approval, economy, incumbency), historical base rates for the office. Do
     not use betting-market odds as an input.
   - Weather, crypto thresholds, scheduled events: the relevant forecast model,
     the current level vs the threshold, and time remaining.

4. **Clean and weight the evidence.** Apply `references/data-analysis.md`:
   source quality, recency weighting, context adjustment, and the data-quality
   gate. Do not let any market price leak in.

5. **Combine base rate and evidence.** Start from the base rate, then move toward
   the current evidence by how strongly it points. Treat the base rate as the
   prior and the fresh data as the update.

6. **Report the most-likely side** (YES or NO) with its probability, then apply
   the confidence calibration from SKILL.md. Honor the 80% ceiling and the
   suppression list. Basis line cites the base rate and the key current data.

## Notes
- Resolution wording errors are the most common mistake here. A contract that
  needs a value "above" a threshold is different from "at or above," and the
  source of record matters.
- With thin or no historical reference class, lean on current evidence and lower
  confidence a tier.
- Time to resolution matters: a level far from the threshold with little time
  left is near-certain; close with lots of time left is closer to a coin flip.
