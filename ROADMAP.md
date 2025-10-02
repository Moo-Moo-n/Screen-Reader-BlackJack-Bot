# Implementation Roadmap

## M1 — Contracts & Skeleton (Day 1–2)
- Load schemas.
- Generate typed interfaces.
- Create no-op adapters that pass fixtures through.
- Build a CLI runner that replays `/fixtures/*` to the console.

## M2 — Zones & Calibration (Day 2–3)
- Implement region selection persistence.
- Load and save `zones_config`.
- Render seat and dealer boxes in a placeholder UI.

## M3 — Round Engine (Day 3–4)
- Implement `beginRound`, `commitObservation`, and `finalizeRound` with multi-hand support for splits and doubles.
- Add a counting engine with profile loading and manual decks-remaining control.

## M4 — Advice Engines (Day 4–5)
- Strategy advisor: basic table plus deviation thresholds driven by data.
- Bet sizing: load risk model; enforce table limits and bankroll.

## M5 — Fixture Green (Day 5–6)
- Ensure all QA cases pass on fixture playback.

## M6 — Capture & Vision Adapters (Day 6–8)
- Wire real capture sources.
- Plug a provisional vision adapter that returns `CardObservations[]`.
- Add override UI and hotkeys.

## M7 — Export & Polish (Day 8–9)
- CSV and JSON export, session summaries, penetration warnings, tooltips, and status bar improvements.
