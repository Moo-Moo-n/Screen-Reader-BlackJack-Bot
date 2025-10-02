"""Typed protocol definitions for the starter blackjack pipeline."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Literal, Optional, Protocol, Sequence, TypedDict


class CardObservation(TypedDict, total=False):
    timestamp: float
    zoneId: str
    rank: Literal["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
    suit: Optional[Literal["S", "H", "D", "C"]]
    confidence: float
    bbox: Sequence[float]


class CountSnapshot(TypedDict):
    running: float
    true: float
    decksRemaining: float


class StrategyAdvice(TypedDict, total=False):
    seatId: str
    handIndex: int
    basicAction: str
    deviationAction: Optional[str]
    deviationTag: Optional[str]
    trueCount: float


class BetAdvice(TypedDict):
    seatId: str
    hands: int
    unitSize: float
    totalWager: float


class RoundExport(TypedDict, total=False):
    hands: int
    wins: int
    losses: int
    pushes: int
    blackjacks: int
    avgBet: float
    net: float
    stdev: float
    penDepth: float


@dataclass
class ObservationEvent:
    timestamp: float
    observation: CardObservation


@dataclass
class CommandEvent:
    timestamp: float
    command: str
    payload: dict


PipelineEvent = ObservationEvent | CommandEvent


class CaptureAdapter(Protocol):
    """Produces raw frames or fixture events."""

    def stream(self) -> Iterable[PipelineEvent]:  # pragma: no cover - protocol
        ...


class VisionAdapter(Protocol):
    """Transforms capture output into card observations."""

    def process(self, events: Iterable[PipelineEvent]) -> Iterable[PipelineEvent]:  # pragma: no cover
        ...


class GameStateTracker(Protocol):
    """Maintains round state based on observations."""

    def ingest(self, events: Iterable[PipelineEvent]) -> Iterable[PipelineEvent]:  # pragma: no cover
        ...


class StrategyAdvisor(Protocol):
    """Calculates play advice for each seat/hand."""

    def advise(self, state_events: Iterable[PipelineEvent]) -> List[StrategyAdvice]:  # pragma: no cover
        ...


class BetSizingEngine(Protocol):
    """Derives bet recommendations from true count and bankroll."""

    def recommend(self, state_events: Iterable[PipelineEvent]) -> List[BetAdvice]:  # pragma: no cover
        ...


class PersistenceAdapter(Protocol):
    """Persists key events and exports session summaries."""

    def save_round(self, events: Iterable[PipelineEvent], advice: List[StrategyAdvice], bets: List[BetAdvice]) -> RoundExport:  # pragma: no cover
        ...

