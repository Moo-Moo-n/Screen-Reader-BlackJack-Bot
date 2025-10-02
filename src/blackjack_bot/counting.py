"""Counting engine used by the round state tracker."""
from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Dict

from .interfaces import CountSnapshot


RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]


@dataclass
class CountProfileConfig:
    """Simple container describing a count profile."""

    name: str = "Neutral"
    tags: Dict[str, float] = field(default_factory=dict)
    round_down_true_count: bool = False


class CountingEngine:
    """Tracks running and true counts as cards are observed."""

    def __init__(self, decks: float = 6.0) -> None:
        self._profile = CountProfileConfig()
        self._running_count = 0.0
        self._cards_seen = 0
        self._decks_total = float(decks)
        self._manual_decks_remaining: float | None = None

    # -- Configuration -------------------------------------------------
    def configure_profile(self, payload: Dict[str, object]) -> None:
        name = str(payload.get("name", "Neutral"))
        tags = {
            rank: float(payload.get("tags", {}).get(rank, 0.0))
            for rank in RANKS
        }
        round_down = bool(payload.get("roundDownTrueCount", False))
        self._profile = CountProfileConfig(name=name, tags=tags, round_down_true_count=round_down)

    def configure_decks(self, decks: float) -> None:
        if decks <= 0:
            raise ValueError("Deck count must be positive")
        self._decks_total = float(decks)
        self._manual_decks_remaining = None

    def set_decks_remaining(self, decks_remaining: float | None) -> None:
        if decks_remaining is None:
            self._manual_decks_remaining = None
            return
        if decks_remaining <= 0:
            raise ValueError("Decks remaining must be positive")
        self._manual_decks_remaining = float(decks_remaining)

    # -- Runtime -------------------------------------------------------
    def reset_round(self) -> None:
        """Currently a no-op but reserved for future per-round bookkeeping."""

    def observe_card(self, rank: str) -> CountSnapshot:
        weight = self._profile.tags.get(rank, 0.0)
        self._running_count += weight
        self._cards_seen += 1
        return self.snapshot()

    def snapshot(self) -> CountSnapshot:
        decks_remaining = self._compute_decks_remaining()
        true_count = self._compute_true_count(decks_remaining)
        return CountSnapshot(
            running=self._running_count,
            true=true_count,
            decksRemaining=decks_remaining,
        )

    # -- Internal helpers ---------------------------------------------
    def _compute_decks_remaining(self) -> float:
        if self._manual_decks_remaining is not None:
            return max(self._manual_decks_remaining, 0.25)
        decks_consumed = self._cards_seen / 52.0
        remaining = max(self._decks_total - decks_consumed, 0.0)
        return max(remaining, 0.25)

    def _compute_true_count(self, decks_remaining: float) -> float:
        if decks_remaining <= 0:
            return self._running_count
        raw_true = self._running_count / decks_remaining
        if not self._profile.round_down_true_count:
            return raw_true
        if raw_true >= 0:
            return math.floor(raw_true)
        return math.ceil(raw_true)

