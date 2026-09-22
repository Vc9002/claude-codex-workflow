---
name: sports-leader
description: >-
  Live and historical sports data for Vincent via the locally-installed
  sports-leader MCP server (ESPN-backed, free, no API key). Trigger whenever
  Vincent asks about live scores, in-game state, play-by-play, box scores,
  standings, rosters, player stats, injuries, betting odds, or sports news for
  any game or league. ALSO trigger automatically as a data source when any
  edge-analyst or polymarket-edge skill is pricing a live or upcoming game and
  needs current game state, injuries, or lineups. Covers 17 sports and 139
  leagues (NFL, NBA, WNBA, MLB, NHL, NCAA, Premier League, La Liga, Serie A,
  Bundesliga, Ligue 1, MLS, UFC, PGA Tour, F1, and more).
---

# Sports Leader MCP

Vincent has the `sports-leader` MCP server installed locally on his Mac. It is
free, ESPN-backed, needs no API key, and has no rate limits. Tool names are
prefixed `mcp__sports-leader__` (or appear under the `sports-leader` server).

## When to use

- Direct questions: "what NBA games are live", "score of the Yankees game",
  "is the over live", "who's injured for the Lakers", "F1 standings".
- As a silent data feed for the edge-analyst / polymarket-edge models when they
  need live game state, injuries, lineups, or odds for a market Vincent is
  pricing. Pull the data, then hand it to the relevant submodel.

## Latency caveat

This is a polling feed (ESPN endpoints), so "live" means roughly 15-30s lag, not
tick-by-tick. Fine for reading game state and modeling. Do NOT treat it as a
low-latency scalping feed for fast-moving live lines — flag the lag to Vincent if
he's sizing real money against an in-play number.

## Core workflow

1. `list_sports_and_leagues` — get valid sport/league slugs if unsure.
2. `get_scoreboard` — live and scheduled games; this is the entry point and
   returns the `eventId` you need for game-level tools.
3. Drill into a game with the eventId:
   - `get_game_summary` — boxscore, leaders, broadcasts, win probability
   - `get_game_plays` — full play-by-play (in-game state)
   - `get_game_probabilities` — win probability timeline
   - `get_game_odds` — spread, moneyline, total by sportsbook

## Tool reference (20 tools)

Discovery: `list_sports_and_leagues`, `search`, `espn_fetch` (escape hatch for
any ESPN URL).

Games: `get_scoreboard`, `get_game_summary`, `get_game_plays`, `get_game_odds`,
`get_game_probabilities`.

Teams: `get_teams`, `get_team` (roster, schedule, record, depth chart, injuries,
transactions, history, news, leaders), `get_team_injuries`.

Athletes: `get_athlete_overview`, `get_athlete_stats`, `get_athlete_gamelog`,
`get_athlete_splits`.

League-wide: `get_standings`, `get_league_leaders`, `get_injuries`,
`get_transactions`, `get_news`.

## Betting-odds providers

`get_game_odds` returns lines from DraftKings, FanDuel, Caesars, BetMGM, and
ESPN BET. Use ESPN BET / consensus as a sanity check, never as the model's
probability input — the edge-analyst no-market-bias rule still applies.

## If the tools are missing

The server may not have loaded. Confirm Claude Desktop was fully quit (Cmd+Q)
and reopened after install. The config entry lives at
`~/Library/Application Support/Claude/claude_desktop_config.json` under
`mcpServers.sports-leader`, pointing at
`/Users/vincentc9002/sports-leader-mcp/dist/index.js` run with
`/usr/local/bin/node`. Rebuild with `npm run build` in
`~/sports-leader-mcp` if `dist/index.js` is gone.
