---
name: flat-call
description: >
  This skill should be used when Vincent wants the single most-likely outcome of
  a game or a Kalshi/Polymarket market, framed as a flat call rather than a
  betting-value analysis. Trigger when he says "flat call", "what's most likely",
  "what's going to happen", "give me the call", "the read on this game", "what
  should I bet on X", "who wins", "is the over hitting", pastes a matchup, a
  Kalshi/Polymarket contract, a screenshot of a slate, or names two teams or a
  player and a line. Produces exactly one pick, one confidence number, and a
  one-line data basis, followed by a short "read under the number" analysis. It
  never reads market price as a model input and never outputs EV, edge, sizing,
  or "not worth it" language.
metadata:
  version: "0.4.1"
---

# flat-call

Give Vincent the single most-likely outcome, backed by real model data, in a
fixed package: a boxed pick line, then a short read.

This skill answers one question only: what is most likely to happen. It is a
forecaster, not a value-betting advisor. Build an honest probability from real
data, then state the most-likely side. Do not talk about expected value, edge,
price, fees, staking, Kelly, bankroll, or whether a bet is "worth it." Vincent
has separate plugins for that and does not want to hear it here.

## The two rules that define this skill

**Rule 1 — Build the probability independently. Never input the market price.**
The market price is not an input to the forecast. Do not look up the Kalshi or
Polymarket price, the sportsbook odds, the live win-probability % shown on a
betting app, or any implied probability and let it shape the number. Markets
carry information but anchoring to them biases the model toward the book's
number and defeats the purpose. Build the probability from team and player data
only. If a price or a live % is visible in something Vincent pasted, ignore it
for modeling. The only place price is allowed is naming which contract or side
he is asking about.

**Rule 2 — The answer must be backed by real, fetched data, pulled through the
market-specific submodel.**
Never produce a confidence number from memory or vibes. Before stating a pick,
load the submodel that owns this market and gather the actual inputs it needs
(see Workflow step 2). The basis line must cite real numbers that were just
pulled. If the data cannot be found or is stale, say so and lower the confidence
accordingly, or declare Pass. A confident number with no data under it is a
failure of this skill.

## Execution requirement (mandatory — do not skip)

A flat call is not a guess dressed in a number. Every call MUST actually run the
pipeline, not substitute judgment for it. Specifically, before stating any
probability you must have:

1. **Run the market submodel** (step 2/5) and produced a model probability.
2. **Built a base rate** via trend-analysis (step 4) from a defined reference
   class — a counted hit rate, not a recalled trend.
3. **Cleaned the inputs** via data-analysis (step 3) with dates attached.

The final number is the model probability reconciled with the base rate. Show
both as distinct inputs in the read (e.g. "base rate 54%, serve model 61%,
settled at 58%"). A number with no model and no base rate behind it is not a
flat call and must not be delivered as one.

**Data-adaptive rule:** the model fits the data you can actually pull. Each
submodel defines data tiers (A = full structural data, B = rating-driven,
C = ranking/base-rate only); auto-select the highest tier the fetched data
supports, run that tier, and cap confidence at that tier's ceiling. Dropping a
tier because the data isn't there is correct behavior, not a failure — never
fabricate inputs to stay in a higher tier. Name the tier used in the Method
line (see `references/tennis.md` for the worked example).

**The only exception is a live, point-by-point decider** (a tennis fifth set, a
final-minutes lead, a bottom-of-the-9th) where the formal pre-match model lags
the current state and adds little. In that case you may give a state-anchored
**Estimate**, but you MUST label it as such in the Method line and say why the
full model was not run. You may not silently pass off an estimate as a model
run. When in doubt, or when there is lead time before the event, run the full
pipeline — option (a), not (b).

## Workflow

1. **Identify the market.** Determine the sport and the exact thing being asked
   (match winner, total, BTTS, corners, spread, player prop, or a non-sport
   Kalshi/Poly event). If two outcomes are plausible candidates, pick the one
   the question is about, or the single most-likely across all outcomes if the
   question is open ("who wins", "what happens").

2. **Invoke the market-specific submodel skill as the data/forecasting engine.**
   This is a required tool call, not a reference read. Actually call the Skill
   tool to load and run the submodel that owns this market — for tennis that
   means invoking `edge-analyst:tennis` (and `edge-analyst:edge-core` /
   `edge-analyst:trend-analysis` as it directs) — then strip its betting-value
   layer (see suppression rule below). Do not settle for a bare web search, and
   do not skip the submodel and reason from the bundled reference files: those
   (`references/tennis.md`, etc.) are the math fallback ONLY when the submodel
   skill is unavailable. If the submodel skill exists, you must call it.

   Routing:
   - Tennis → `edge-analyst:tennis` (serve/return hierarchical + surface Elo),
     plus `sports-leader` for live state and H2H
   - Football (NFL/CFB) → `edge-analyst:football`
   - Basketball (NBA/CBB) → `edge-analyst:basketball`
   - Soccer → `edge-analyst:soccer` (Dixon-Coles)
   - Macro / econ releases → `edge-analyst:macro`
   - Politics / elections → `edge-analyst:politics`
   - World Cup soccer → `edge-analyst:world-cup-predict`
   - Anything else with no sport model → `references/general-market.md`

   Three references apply to every call regardless of sport:
   `references/data-analysis.md` (how to source, clean, and weight every input),
   `references/trend-analysis.md` and `edge-analyst:trend-analysis` (how to build
   the historical base rate), and `references/forecasting-core.md`
   (margin-to-probability conversion, empirical accuracy ceilings, and how to
   combine the base rate with the model). The bundled per-sport reference files
   (`references/tennis.md`, etc.) are the fallback math when a submodel is not
   available.

3. **Gather and clean the data.** Pull the inputs the submodel lists, using
   `sports-leader` for live game state/injuries/lineups and web search to
   confirm rankings, form, and surface splits. Verify rankings from a primary
   source (ATP/ESPN), not the betting feed — the on-screen feed rankings have
   been wrong. Run `references/data-analysis.md`: source hierarchy, recency
   weighting, opponent/venue/rest adjustment, and the data-quality gate. Note
   the date of everything. Do not pass raw, unadjusted, or stale numbers into
   the model.

4. **Pull the base rate.** Build a clean reference class and compute the
   historical hit rate for this line, with a confidence interval and small-
   sample shrink. This empirical base rate is the prior the model updates from.
   Reject cherry-picked "last 5 games" trends.

5. **Compute the probability.** Run the submodel, anchored to the base rate from
   step 4 and fed the cleaned data from step 3. Produce a probability for the
   most-likely side. Keep market price and live % out of it.

6. **Set confidence from data quality and state.** Confidence is the model
   probability, adjusted down when the data is thin, stale, or unconfirmed, or
   when the base rate and the model disagree. See the calibration table below.
   Apply the live-state rule. Do not report a tier higher than the data supports.

7. **Output the package.** Use the fixed shape below — boxed pick line, then the
   read. Stop there.

## Live-state rule

For an in-progress game, the current score moves probability more than the
profiles do. In a deciding set or late game, weight it heavily:
- On-serve / no break, level score → the profile-based baseline edge holds.
- A confirmed break or lead → compress or flip the call immediately.
Always state the single condition that would flip the pick (e.g. "if Kym breaks
for 3-1, flip to Kym").

## Output contract

Always exactly this shape. First, the boxed pick line in a fenced code block:

```
<Pick> — <confidence %> (<tier>)
Basis: <2 to 4 real data points that produced the number>
Method: <Full model run | Estimate (live decider — reason)> · Tier <A|B|C> · base rate <x%>, model <y%>
```

The Method line is mandatory. State whether this was a full model run or a
state-anchored estimate, and show the base rate and the model probability as the
two distinct inputs that produced the final number. If Estimate, give the reason
in the parentheses.

Then, immediately below the box, a short **"the read under the number"**
paragraph (3 to 6 sentences, prose, no lists): the core case for the pick, the
one or two things capping the confidence, and the single swing factor that would
flip it. Close on the flip condition or forward momentum, never a question.

Then a **Sources:** line with markdown links to the data actually pulled.

Example:

```
Over 2.5 goals — 61% (Lean)
Basis: Arsenal 2.1 xGF / Spurs 1.6 xGA last 6, both scored in 5 of 6 H2H, full-strength XIs.
Method: Full model run · Tier A · base rate 57% (over hit 16/28 comparable fixtures), Dixon-Coles 63%
```

The read under the number: Arsenal's attack has been generating chances well
above this line and Spurs concede at a rate that compounds it, with the H2H
backing the pattern. What caps it at 61 rather than higher is that one cagey
1-0 flips the under, and late-window game state on a lead can kill the tempo.
The swing factor is an early goal: get one inside 20 minutes and this pushes
toward 70; a goalless half-hour and I'd be shading back toward even.

Rules for the output:
- The boxed pick line appears every time, first, in a code block.
- One pick. Not two, not a hedge, not "lean" as the pick.
- Confidence is a whole-number percent with a tier label in parentheses.
- Basis is one line of actual data, not reasoning filler. Numbers, not adjectives.
- The read is mandatory and always includes the flip condition.
- Never append EV, price, the live %, edge, "value", "worth it", stake size, or
  a units call.

If Vincent pastes a multi-game slate, output one boxed line per game; the read
can be one or two sentences per game to keep it tight.

## Confidence calibration

Confidence reflects both the model and the quality of the data behind it. Anchor
to these tiers and do not exceed what the data supports.

| Tier | Confidence | Use when |
|------|-----------|----------|
| Strong | 65-80% | Clear model signal, current confirmed data, no major unknowns |
| Lean | 55-64% | Real edge in the model, data current but a variable or two unconfirmed |
| Thin | 50-54% | Model barely separates the sides, or data is stale/partial |
| Pass | report as Pass | Coin flip, or required data could not be found |

Never report above 80%. Real sporting outcomes carry irreducible variance, and a
number above 80% almost always means the market price leaked into the model or
the data was overfit. The per-sport empirical ceilings in
`references/forecasting-core.md` are tighter than 80% for most markets (soccer
result ~65%, tennis ~70%, NBA/NFL sides high 60s to low 70s, MLB totals mid 60s),
so anchor to those, not to the 80% hard cap. If the honest read is a coin flip or
the data is missing, output "Pass — <reason>" in the box rather than forcing a side.

## Hard suppression list

Use the `edge-analyst` / `polymarket-edge` submodels purely as the
probability/data engine. They natively emit a betting-value layer — strip it.
Do not output any of the following in this skill, even if asked to justify the
pick: expected value, EV, edge, implied probability, fair price, the market or
book price, the live win-probability %, "value", "+EV", "-EV", "not worth it",
"no value", vig, fees, Kelly, units, stake size, bankroll percentage, or a
recommended bet amount. If Vincent wants those, that is the edge-analyst or
polymarket-edge plugin, and you can say so in one line, but do not produce them
here.
