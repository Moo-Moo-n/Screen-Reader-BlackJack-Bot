# Blackjack Card-Counting Assistant

## Project Purpose
A desktop app that watches a blackjack table on screen, understands the dealt cards and hand states in real time, keeps an accurate running and true count, and provides bet and play advice with logs and exports.

## High-Level Modules
- **Capture Layer**: handles screen or window frame capture.
- **Vision Adapter**: converts captured frames into `CardObservations[]`.
- **Table Mapper**: translates calibrated seat and dealer zones.
- **Game State Tracker**: maintains round, hand, and deck state.
- **Counting Engine**: computes running and true counts using a profile.
- **Strategy Advisor**: surfaces basic strategy actions plus true-count deviations.
- **Bet Sizing Engine**: suggests hand count and unit size based on true count and bankroll.
- **UI Layer**: provides visualization, controls, and tooltips.
- **Persistence & Export**: produces CSV/JSON session logs.

## Repository Layout
```
/requirements.md
/contracts/
  card_observation.schema.json
  zones_config.schema.json
  count_profile.schema.json
  rules_config.schema.json
  risk_model.schema.json
  advice.schema.json
  capture_api.schema.json
  vision_api.schema.json
  game_state_api.schema.json
  strategy_api.schema.json
  bet_api.schema.json
  persistence_api.schema.json
/fixtures/
  stream_simple_round.json
  stream_split_double_round.json
  deck_drain_sequence.json
  strategy_flip_cases.json
  export_expected_summary.json
/QA.md
/ROADMAP.md
```

## Zero-Assumption Starter Tasks
1. **Contracts First**: load schemas from `/contracts`, generate typed stubs in the chosen language, and wire no-op adapters that echo fixtures end to end.
2. **Fixture Playback**: build a runner that feeds `/fixtures/stream_*.json` into the pipeline and produces `/tmp/advice.log` and `/tmp/export.json`.
3. **Acceptance Harness**: implement the checks described in `QA.md` against the runner output.
