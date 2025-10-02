# Acceptance and Verification Plan

## A. Count Consistency
- **Input**: `deck_drain_sequence.json`
- **Check**: Running and true counts match `expectedSnapshots` (respecting rounding rules).

## B. Strategy Flip Determinism
- **Input**: `strategy_flip_cases.json`
- **Check**: For each case, `advise()` returns `below` when TC < threshold and `atOrAbove` when TC ≥ threshold, including the `deviationTag`.

## C. Fixture Playback Integrity
- **Input**: `stream_simple_round.json`
- **Check**: Events flow through adapters and `finalizeRound` produces export values within tolerance of `export_expected_summary.json`.

## D. Splits and Doubles State Machine
- **Input**: `stream_split_double_round.json`
- **Check**: Multiple hands are tracked, doubles adjust bet accounting, and the round closes with separate outcomes.

## E. Performance Budget
- **Check**: Observation to updated advice occurs within 500 ms (95th percentile measured via timestamps in logs).

## F. Operator Overrides
- **Check**: Inject three incorrect observations; user overrides within 5 seconds total; no corrupted state; audit log shows both original and corrected entries.
