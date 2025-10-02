# Product and Engineering Requirements

## 1. Outcomes (Definition of Done)
1. User selects a screen or window region to watch and the configuration persists.
2. Cards appearing in the region are surfaced as observations with `{zoneId, rank, (optional suit), confidence}` and assigned to seats plus dealer in near real time.
3. Running count and true count update deterministically using a selected count profile; decks remaining is adjustable and/or inferred.
4. Strategy panel shows basic action and deviation (when true-count thresholds are met) with concise tooltip text.
5. Bet panel recommends hand count (1 or 2) and unit size, obeying bankroll constraints and table limits via a pluggable risk model.
6. Operator can begin rounds, mark outcomes (win/loss/push/blackjack/insurance), override a misread card, and toggle which seats are "mine" with minimal friction.
7. Session stats (hands per hour, wagers, net, EV estimate, variance) and full logs export to CSV and JSON.
8. Alerts surface when penetration is shallow, FPS is low, confidence is low, or a table change should be considered.

## 2. Non-Functional Requirements
- **Latency**: ≤ 500 ms from observation to updated advice.
- **Accuracy**: 95%+ rank accuracy on clean, in-focus frames (validated via fixtures and human overrides).
- **Resilience**: Overrides never corrupt state; every mutation is timestamped and auditable.
- **Portability**: No hard dependency on a particular CV or GUI toolkit. Adapters must be replaceable.
- **Privacy**: Default local processing and storage.

## 3. Rules Support (Initial)
- 8-deck shoe, Blackjack 3:2, S17 default, DAS true, surrender none (configurable via `rules_config`).
- Two-hand player support; counting uses all observed cards.

## 4. UX Essentials
- Always visible: running count, true count, shoe depth, bet advice.
- Quick tooltips on deviations (e.g., `16 vs 10 → Stand at TC ≥ 0; else Hit`).
- Hotkeys for: start/next hand, mark outcomes, toggle two-hand, add/remove card, pause capture.

## 5. Extensibility
- Profiles: counting (tag weights, rounding rules), risk models (JSON driven), strategy tables (data driven).
- Adapters: capture, vision, strategy, bets, persistence defined by minimal interfaces in `/contracts`.
