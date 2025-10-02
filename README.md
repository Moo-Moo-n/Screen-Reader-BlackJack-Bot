# Blackjack Card‑Counting Assistant — Starter Pack for Codex

This pack gives Codex everything needed to scaffold a fresh implementation without prescribing specific libraries or ML models. It includes:

- `requirements.md` (product & engineering requirements)
- `/contracts` (method‑agnostic JSON schemas/interfaces)
- `/fixtures` (golden test cases and sample observation streams)
- `QA.md` (acceptance tests & verification)
- `ROADMAP.md` (milestones)
- `README.md` (folder layout & first tasks)

---

## README.md

### Project Purpose
A desktop app that watches a blackjack table on screen, understands the dealt cards/hand states in real time, keeps an accurate running & true count, and provides bet/play advice with logs and exports.

### High‑Level Modules (all pluggable)
- **Capture Layer** (screen/window frames)
- **Vision Adapter** (frame → CardObservations[])
- **Table Mapper** (calibrated seat/dealer zones)
- **Game State Tracker** (round/hand/deck state)
- **Counting Engine** (running/true count; profile‑based)
- **Strategy Advisor** (basic strategy + TC deviations)
- **Bet Sizing Engine** (TC + bankroll → bet advice)
- **UI Layer** (visualization, controls, tooltips)
- **Persistence & Export** (CSV/JSON session logs)

### Repository Layout (proposed)
```
/requirements.md
/contracts/
  card_observation.schema.json
  count_profile.schema.json
  rules_config.schema.json
  advice.schema.json
  risk_model.schema.json
  zones_config.schema.json
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

### Zero‑Assumption Starter Tasks
1. **Contracts First**: Load schemas from `/contracts`, generate typed stubs in the chosen language, and wire no‑op adapters that echo fixtures end‑to‑end.
2. **Fixture Playback**: Build a small runner that feeds `/fixtures/stream_*.json` into the pipeline and produces `/tmp/advice.log` and `/tmp/export.json`.
3. **Acceptance Harness**: Implement the checks described in `QA.md` against the runner output.

---

## requirements.md

### 1) Outcomes (Definition of Done)
1. User selects a screen/window region to watch; configuration persists.
2. Cards appearing in the region are surfaced as **observations** with {zoneId, rank, (optional suit), confidence} and assigned to seats + dealer in near‑real‑time.
3. Running count and true count update deterministically using a selected **count profile**; decks‑remaining is adjustable and/or inferred.
4. Strategy panel shows **basic action** and **deviation** (when TC thresholds are met) with concise tooltip.
5. Bet panel recommends **hand count** (1 or 2) and **unit size**, obeying bankroll constraints and table limits via a pluggable **risk model**.
6. Operator can quickly: begin round, mark outcomes (win/loss/push/blackjack/insurance), override a misread card, toggle which seats are "mine".
7. Session stats (hands/hour, wagers, net, EV estimate, variance) and full logs export to CSV/JSON.
8. Alerts: penetration shallow, low FPS, low confidence, consider table change.

### 2) Non‑Functional
- **Latency**: ≤ 500 ms from observation to updated advice.
- **Accuracy Target (vision‑agnostic)**: 95%+ rank accuracy on clean, in‑focus frames (validated via fixtures & human overrides).
- **Resilience**: Overrides never corrupt state; every mutation is timestamped and auditable.
- **Portability**: No hard dependency on a particular CV/GUI toolkit. Adapters must be replaceable.
- **Privacy**: Default local processing & storage.

### 3) Rules Support (initial)
- 8‑deck shoe, Blackjack 3:2, S17 default, DAS true, surrender none (configurable via `rules_config`).
- Two‑hand player support; counting uses all observed cards.

### 4) UX Essentials
- Always‑visible: Running count, True count, Shoe depth, Bet advice.
- Quick tooltips on deviations (e.g., `16 vs 10 → Stand at TC ≥ 0; else Hit`).
- Hotkeys for: Start/Next hand, mark outcomes, toggle two‑hand, add/remove card, pause capture.

### 5) Extensibility
- **Profiles**: Counting (tag weights, rounding rules), Risk models (JSON driven), Strategy tables (data driven).
- **Adapters**: Capture, Vision, Strategy, Bets, Persistence defined by minimal interfaces in `/contracts`.

---

## /contracts (JSON Schemas & Adapter Contracts)

### card_observation.schema.json
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "card_observation.schema.json",
  "type": "object",
  "required": ["timestamp", "zoneId", "rank", "confidence"],
  "properties": {
    "timestamp": {"type": "number", "description": "Unix seconds with fraction"},
    "zoneId": {"type": "string", "description": "seat_1..seat_7 or dealer"},
    "rank": {"type": "string", "enum": ["A","2","3","4","5","6","7","8","9","10","J","Q","K"]},
    "suit": {"type": ["string","null"], "enum": ["S","H","D","C", null]},
    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    "bbox": {"type": "array", "items": {"type": "number"}, "minItems": 4, "maxItems": 4}
  }
}
```

### zones_config.schema.json
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "zones_config.schema.json",
  "type": "object",
  "required": ["region", "zones"],
  "properties": {
    "region": {"type": "object", "properties": {"x": {"type": "number"}, "y": {"type": "number"}, "w": {"type": "number"}, "h": {"type": "number"}}, "required": ["x","y","w","h"]},
    "zones": {
      "type": "array",
      "items": {"type": "object", "required": ["id","polygon"],
        "properties": {
          "id": {"type": "string"},
          "polygon": {"type": "array", "items": {"type": "array", "items": {"type": "number"}, "minItems": 2, "maxItems": 2}}
        }
      }
    }
  }
}
```

### count_profile.schema.json
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "count_profile.schema.json",
  "type": "object",
  "required": ["name","tags"],
  "properties": {
    "name": {"type": "string"},
    "tags": {"type": "object", "additionalProperties": {"type": "number"}},
    "roundDownTrueCount": {"type": "boolean", "default": true}
  }
}
```

### rules_config.schema.json
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "rules_config.schema.json",
  "type": "object",
  "required": ["decks","blackjackPays","dealerHitsSoft17"],
  "properties": {
    "decks": {"type": "integer", "minimum": 1},
    "blackjackPays": {"type": "string", "enum": ["3:2","6:5"]},
    "dealerHitsSoft17": {"type": "boolean"},
    "doubleAfterSplit": {"type": "boolean", "default": true},
    "splitAcesOnce": {"type": "boolean", "default": true},
    "surrender": {"type": "string", "enum": ["none","late","early"], "default": "none"}
  }
}
```

### risk_model.schema.json
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "risk_model.schema.json",
  "type": "object",
  "required": ["name","unitBase","maxUnit","kellyFraction"],
  "properties": {
    "name": {"type": "string"},
    "unitBase": {"type": "number", "minimum": 0},
    "maxUnit": {"type": "number", "minimum": 0},
    "twoHandThresholdTC": {"type": "number"},
    "kellyFraction": {"type": "number", "minimum": 0},
    "minEnterTC": {"type": "number", "default": 1}
  }
}
```

### advice.schema.json
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "advice.schema.json",
  "type": "object",
  "properties": {
    "bet": {
      "type": "object",
      "required": ["handCount","unitSize","rationale"],
      "properties": {
        "handCount": {"type": "integer", "enum": [1,2]},
        "unitSize": {"type": "number"},
        "rationale": {"type": "string"}
      }
    },
    "play": {
      "type": "object",
      "required": ["action"],
      "properties": {
        "action": {"type": "string", "enum": ["Hit","Stand","Double","Split","Surrender","Insurance"]},
        "deviationTag": {"type": ["string","null"]},
        "tooltip": {"type": ["string","null"]}
      }
    }
  }
}
```

### capture_api.schema.json (Adapter Contract)
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "capture_api.schema.json",
  "type": "object",
  "properties": {
    "methods": {
      "type": "array",
      "items": {"type": "string", "enum": ["start","stop","onFrame","setRegion","listSources"]}
    }
  },
  "description": "Capture adapter must expose start(sourceId, region), stop(), onFrame(cb(bitmap,timestamp)), setRegion(region), listSources()"
}
```

### vision_api.schema.json (Adapter Contract)
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "vision_api.schema.json",
  "type": "object",
  "properties": {
    "methods": {
      "type": "array",
      "items": {"type": "string", "enum": ["analyzeFrame","setTableZones","warmup","teardown"]}
    },
    "analyzeFrame_return": {
      "type": "array",
      "items": {"$ref": "card_observation.schema.json"}
    }
  }
}
```

### game_state_api.schema.json (Adapter Contract)
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "game_state_api.schema.json",
  "type": "object",
  "properties": {
    "methods": {
      "type": "array",
      "items": {"type": "string", "enum": ["beginRound","commitObservation","overrideCard","finalizeRound","resetShoe","onEvent"]}
    }
  }
}
```

### strategy_api.schema.json (Adapter Contract)
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "strategy_api.schema.json",
  "type": "object",
  "properties": {
    "methods": {
      "type": "array",
      "items": {"type": "string", "enum": ["advise","loadTables"]}
    },
    "advise_return": {"$ref": "advice.schema.json"}
  }
}
```

### bet_api.schema.json (Adapter Contract)
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "bet_api.schema.json",
  "type": "object",
  "properties": {
    "methods": {
      "type": "array",
      "items": {"type": "string", "enum": ["suggest","loadRiskModel"]}
    },
    "suggest_return": {"type": "object", "properties": {"bet": {"$ref": "advice.schema.json#/properties/bet"}}}
  }
}
```

### persistence_api.schema.json (Adapter Contract)
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "persistence_api.schema.json",
  "type": "object",
  "properties": {
    "methods": {
      "type": "array",
      "items": {"type": "string", "enum": ["saveSession","loadSession","exportCSV","exportJSON","appendLog"]}
    }
  }
}
```

---

## /fixtures (Golden Cases & Streams)

### stream_simple_round.json
A short stream illustrating one round with 3 player seats, no splits/doubles.
```json
{
  "zonesConfig": {"region": {"x": 100, "y": 100, "w": 1280, "h": 720}, "zones": [{"id":"dealer","polygon":[[0.45,0.05],[0.55,0.05],[0.55,0.15],[0.45,0.15]]},{"id":"seat_1","polygon":[[0.10,0.60],[0.20,0.60],[0.20,0.85],[0.10,0.85]]},{"id":"seat_2","polygon":[[0.30,0.60],[0.40,0.60],[0.40,0.85],[0.30,0.85]]},{"id":"seat_3","polygon":[[0.50,0.60],[0.60,0.60],[0.60,0.85],[0.50,0.85]]}]},
  "rules": {"decks": 8, "blackjackPays": "3:2", "dealerHitsSoft17": false, "doubleAfterSplit": true, "splitAcesOnce": true, "surrender": "none"},
  "countProfile": {"name": "WongHalvesLike", "tags": {"2": 0.5, "3": 1, "4": 1, "5": 1.5, "6": 1, "7": 0.5, "8": 0, "9": -0.5, "10": -1, "J": -1, "Q": -1, "K": -1, "A": -1}, "roundDownTrueCount": true},
  "riskModel": {"name": "ConservativeKelly", "unitBase": 5, "maxUnit": 150, "twoHandThresholdTC": 3, "kellyFraction": 0.033, "minEnterTC": 1},
  "events": [
    {"t": 0.10, "obs": {"zoneId": "seat_1", "rank": "10", "confidence": 0.97}},
    {"t": 0.12, "obs": {"zoneId": "seat_2", "rank": "5",  "confidence": 0.96}},
    {"t": 0.15, "obs": {"zoneId": "seat_3", "rank": "9",  "confidence": 0.95}},
    {"t": 0.20, "obs": {"zoneId": "dealer", "rank": "6",  "confidence": 0.98}},
    {"t": 0.40, "obs": {"zoneId": "seat_1", "rank": "A",  "confidence": 0.96}},
    {"t": 0.45, "obs": {"zoneId": "seat_2", "rank": "K",  "confidence": 0.95}},
    {"t": 0.50, "obs": {"zoneId": "seat_3", "rank": "7",  "confidence": 0.94}},
    {"t": 0.80, "command": "finalizeRound", "outcomes": [{"seatId":"seat_1","result":"blackjack"},{"seatId":"seat_2","result":"loss"},{"seatId":"seat_3","result":"win"}]}]
}
```

### stream_split_double_round.json
Demonstrates splits and doubles, ensuring state machine covers multi‑hand seats.
```json
{
  "zonesConfig": {"region": {"x": 0, "y": 0, "w": 1920, "h": 1080}, "zones": [{"id":"dealer","polygon":[[0.46,0.08],[0.54,0.08],[0.54,0.16],[0.46,0.16]]},{"id":"seat_2","polygon":[[0.30,0.62],[0.40,0.62],[0.40,0.88],[0.30,0.88]]}]},
  "rules": {"decks": 8, "blackjackPays": "3:2", "dealerHitsSoft17": false},
  "countProfile": {"name": "AltCount", "tags": {"2":1, "3":1, "4":1, "5":1, "6":1, "7":0, "8":0, "9":0, "10":-1, "J":-1, "Q":-1, "K":-1, "A":-1}},
  "events": [
    {"t":0.10, "obs": {"zoneId":"seat_2","rank":"8","confidence":0.97}},
    {"t":0.14, "obs": {"zoneId":"seat_2","rank":"8","confidence":0.95}},
    {"t":0.18, "command":"split", "seatId":"seat_2"},
    {"t":0.20, "obs": {"zoneId":"seat_2","rank":"3","confidence":0.95}},
    {"t":0.23, "obs": {"zoneId":"seat_2","rank":"2","confidence":0.94}},
    {"t":0.30, "command":"double", "seatId":"seat_2","handIndex":0},
    {"t":0.35, "obs": {"zoneId":"dealer","rank":"10","confidence":0.98}},
    {"t":0.80, "command":"finalizeRound","outcomes":[{"seatId":"seat_2","result":"win","handIndex":0},{"seatId":"seat_2","result":"loss","handIndex":1}]}
  ]
}
```

### deck_drain_sequence.json
A deterministic sequence to validate running/true count parity with a profile.
```json
{
  "countProfile": {"name":"TestProfile","tags":{"2":0.5,"3":1,"4":1,"5":1.5,"6":1,"7":0.5,"8":0,"9":-0.5,"10":-1,"J":-1,"Q":-1,"K":-1,"A":-1}, "roundDownTrueCount": true},
  "decks": 1,
  "cards": ["2","3","4","5","6","7","8","9","10","J","Q","K","A","2","2","2","9","9","9","A","A","A"],
  "expectedSnapshots": [
    {"index": 4,  "running": 5.0,  "true": 5.0},
    {"index": 12, "running": 1.0,  "true": 1.0},
    {"index": 20, "running": 2.5,  "true": 3.0}
  ]
}
```

### strategy_flip_cases.json
Cases where advice must flip at specific TC thresholds.
```json
[
  {"player":"16","dealer":"10","thresholdTC":0,  "below":"Hit","atOrAbove":"Stand", "tag":"16v10@TC>=0"},
  {"player":"12","dealer":"3", "thresholdTC":2,  "below":"Hit","atOrAbove":"Stand", "tag":"12v3@TC>=2"},
  {"player":"9","dealer":"2",  "thresholdTC":1,  "below":"Hit","atOrAbove":"Double", "tag":"9v2@TC>=1"}
]
```

### export_expected_summary.json
Expected aggregated stats for the simple stream.
```json
{
  "hands": 3,
  "wins": 2,
  "losses": 1,
  "pushes": 0,
  "blackjacks": 1,
  "avgBet": 15,
  "net": 17.5,
  "stdev": 1.2,
  "penDepth": 0.12
}
```

---

## QA.md (Acceptance & Verification)

### A. Count Consistency
- **Input**: `deck_drain_sequence.json`
- **Check**: Running & true count match `expectedSnapshots` (within rounding rules).

### B. Strategy Flip Determinism
- **Input**: `strategy_flip_cases.json`
- **Check**: For each case, `advise()` returns `below` when TC < threshold; `atOrAbove` when TC ≥ threshold; includes `deviationTag`.

### C. Fixture Playback Integrity
- **Input**: `stream_simple_round.json`
- **Check**: Events flow through adapters; `finalizeRound` produces export with values within tolerance of `export_expected_summary.json`.

### D. Splits/Doubles State Machine
- **Input**: `stream_split_double_round.json`
- **Check**: Multiple hands tracked; doubles adjust bet accounting; round closes cleanly with separate outcomes.

### E. Performance Budget
- **Check**: Observation → updated advice ≤ 500 ms (measured with timestamps in logs for 95th percentile).

### F. Operator Overrides
- **Check**: Inject three incorrect observations; user override within 5s total; no corrupted state; audit log shows both original and corrected entries.

---

## ROADMAP.md (Milestones for a Fresh Build)

### M1 — Contracts & Skeleton (Day 1–2)
- Load schemas; generate typed interfaces; create no‑op adapters that pass fixtures through.
- CLI runner that replays `/fixtures/*` to console.

### M2 — Zones & Calibration (Day 2–3)
- Implement region selection persistence; load/save `zones_config`.
- Render seat/dealer boxes in UI placeholder.

### M3 — Round Engine (Day 3–4)
- `beginRound`/`commitObservation`/`finalizeRound`; multi‑hand (split/double) support.
- Counting Engine with profile load; manual decks‑remaining control.

### M4 — Advice Engines (Day 4–5)
- Strategy Advisor: basic table + deviation thresholds via data.
- Bet Sizing: load risk model; enforce table limits & bankroll.

### M5 — Fixture Green (Day 5–6)
- All QA cases pass on fixture playback.

### M6 — Capture & Vision Adapters (Day 6–8)
- Wire real capture; plug a provisional vision adapter (any method) returning `CardObservations[]`.
- Add override UI and hotkeys.

### M7 — Export & Polish (Day 8–9)
- CSV/JSON export, session summaries, penetration warnings, tooltips, status bar.

---

## Notes to Implementers
- Keep **Strategy** and **Bet Sizing** entirely **data‑driven** (JSON lookups + thresholds), not hardcoded logic.
- Use **events** for state changes: `onCardAdded`, `onRoundComplete`, `onShoeDepthChanged`, `onWarning`.
- Vision adapter should surface **uncertainty** (low confidence) so UI can request confirmation rather than guessing.
- All timestamps should be monotonic and included in logs for post‑hoc analysis.

