"""CLI runner that replays fixture streams through the no-op pipeline."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from .adapters import (
    InMemoryPersistenceAdapter,
    NoOpBetSizingEngine,
    NoOpCaptureAdapter,
    NoOpStrategyAdvisor,
    NoOpVisionAdapter,
)
from .state import RoundStateTracker
from .schemas import load_all_schemas


class Pipeline:
    """Lightweight container composing the starter adapters."""

    def __init__(self, fixture_path: Path) -> None:
        self.fixture_path = fixture_path
        self.capture = NoOpCaptureAdapter(fixture_path)
        self.vision = NoOpVisionAdapter()
        self.state_tracker = RoundStateTracker()
        self.strategy = NoOpStrategyAdvisor()
        self.bets = NoOpBetSizingEngine()
        self.persistence = InMemoryPersistenceAdapter()

    def run(self) -> dict:
        events = list(self.capture.stream())
        vision_events = list(self.vision.process(events))
        state_events = list(self.state_tracker.ingest(vision_events))
        strategy_advice = self.strategy.advise(state_events)
        bet_advice = self.bets.recommend(state_events)
        export = self.persistence.save_round(state_events, strategy_advice, bet_advice)
        return {
            "fixture": self.fixture_path.name,
            "events": [event.__dict__ for event in events],
            "advice": strategy_advice,
            "bets": bet_advice,
            "export": export,
        }


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "fixture",
        help="Path to a fixture JSON file from the fixtures directory.",
    )
    parser.add_argument(
        "--contracts",
        type=Path,
        default=None,
        help="Optional path to the contracts directory for validation purposes.",
    )
    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    fixture_path = Path(args.fixture).expanduser().resolve()
    if not fixture_path.exists():
        raise SystemExit(f"Fixture '{fixture_path}' does not exist.")

    registry = load_all_schemas(args.contracts)
    print(f"Loaded {len(list(registry.items()))} JSON schemas from {registry.root}.")

    pipeline = Pipeline(fixture_path)
    output = pipeline.run()
    print(f"Replay complete for fixture: {output['fixture']}")
    print(f"Observed {len(output['events'])} events → {len(output['advice'])} advice entries, {len(output['bets'])} bet entries.")
    print("Export summary:")
    for key, value in output["export"].items():
        print(f"  {key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
