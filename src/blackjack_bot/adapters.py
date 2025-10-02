"""Simple no-op adapter implementations used for fixture playback."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, List
import json

from .interfaces import (
    BetAdvice,
    BetSizingEngine,
    CaptureAdapter,
    CommandEvent,
    GameStateTracker,
    ObservationEvent,
    PersistenceAdapter,
    PipelineEvent,
    StrategyAdvice,
    StrategyAdvisor,
    VisionAdapter,
)


@dataclass
class NoOpCaptureAdapter(CaptureAdapter):
    """Loads pre-recorded events from a fixture file."""

    fixture_path: Path

    def stream(self) -> Iterator[PipelineEvent]:
        with self.fixture_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        for item in payload.get("events", []):
            timestamp = float(item.get("t", 0.0))
            if "obs" in item:
                yield ObservationEvent(timestamp=timestamp, observation=item["obs"])
            else:
                command = item.get("command", "unknown")
                payload = {
                    key: value
                    for key, value in item.items()
                    if key not in {"t", "command"}
                }
                yield CommandEvent(timestamp=timestamp, command=command, payload=payload)


@dataclass
class NoOpVisionAdapter(VisionAdapter):
    """Passes through observation events unchanged."""

    def process(self, events: Iterable[PipelineEvent]) -> Iterable[PipelineEvent]:
        return list(events)


@dataclass
class NoOpGameStateTracker(GameStateTracker):
    """For now, just echoes events to downstream consumers."""

    def ingest(self, events: Iterable[PipelineEvent]) -> Iterable[PipelineEvent]:
        return list(events)


@dataclass
class NoOpStrategyAdvisor(StrategyAdvisor):
    """Produces placeholder advice for every observation seat."""

    default_action: str = "Stand"

    def advise(self, state_events: Iterable[PipelineEvent]) -> List[StrategyAdvice]:
        advice: List[StrategyAdvice] = []
        for event in state_events:
            if isinstance(event, ObservationEvent):
                advice.append(
                    StrategyAdvice(
                        seatId=event.observation.get("zoneId", "seat"),
                        handIndex=0,
                        basicAction=self.default_action,
                        deviationAction=None,
                        deviationTag=None,
                        trueCount=0.0,
                    )
                )
        return advice


@dataclass
class NoOpBetSizingEngine(BetSizingEngine):
    """Returns a constant bet recommendation."""

    unit_size: float = 10.0

    def recommend(self, state_events: Iterable[PipelineEvent]) -> List[BetAdvice]:
        bets: List[BetAdvice] = []
        seen_seats = set()
        for event in state_events:
            if isinstance(event, ObservationEvent):
                seat = event.observation.get("zoneId", "seat")
                if seat not in seen_seats and seat.startswith("seat"):
                    seen_seats.add(seat)
                    bets.append(
                        BetAdvice(
                            seatId=seat,
                            hands=1,
                            unitSize=self.unit_size,
                            totalWager=self.unit_size,
                        )
                    )
        return bets


@dataclass
class InMemoryPersistenceAdapter(PersistenceAdapter):
    """Collects events into a simple export dictionary."""

    def save_round(
        self,
        events: Iterable[PipelineEvent],
        advice: List[StrategyAdvice],
        bets: List[BetAdvice],
    ) -> dict:
        event_count = sum(1 for _ in events)
        return {
            "events": event_count,
            "adviceCount": len(advice),
            "betCount": len(bets),
        }

