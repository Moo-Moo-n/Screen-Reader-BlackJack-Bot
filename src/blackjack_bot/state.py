"""Round state management for fixture playback and counting."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List

from .counting import CountingEngine
from .interfaces import CommandEvent, GameStateTracker, ObservationEvent, PipelineEvent


PLAYER_ZONE_PREFIX = "seat_"


@dataclass
class HandState:
    """Represents a single blackjack hand."""

    hand_index: int
    cards: List[str] = field(default_factory=list)
    doubled: bool = False

    def to_dict(self) -> Dict[str, object]:
        return {
            "handIndex": self.hand_index,
            "cards": list(self.cards),
            "doubled": self.doubled,
        }


@dataclass
class SeatState:
    """Tracks all hands for a single seat."""

    seat_id: str
    hands: List[HandState] = field(default_factory=lambda: [HandState(hand_index=0)])

    def ensure_hand(self, index: int) -> HandState:
        while len(self.hands) <= index:
            self.hands.append(HandState(hand_index=len(self.hands)))
        return self.hands[index]

    def to_dict(self) -> Dict[str, object]:
        return {"seatId": self.seat_id, "hands": [hand.to_dict() for hand in self.hands]}


class RoundStateTracker(GameStateTracker):
    """Consumes events, maintains round state, and emits derived commands."""

    def __init__(self) -> None:
        self._counting = CountingEngine()
        self._round_index = 0
        self._round_active = False
        self._seats: Dict[str, SeatState] = {}
        self._dealer = HandState(hand_index=0)

    # -- GameStateTracker API -----------------------------------------
    def ingest(self, events: Iterable[PipelineEvent]) -> Iterable[PipelineEvent]:
        output: List[PipelineEvent] = []
        for event in events:
            output.append(event)
            if isinstance(event, ObservationEvent):
                derived = self._handle_observation(event)
                output.extend(derived)
            elif isinstance(event, CommandEvent):
                derived = self._handle_command(event)
                output.extend(derived)
        return output

    # -- Internal handlers --------------------------------------------
    def _handle_command(self, event: CommandEvent) -> List[PipelineEvent]:
        command = event.command
        payload = event.payload or {}
        derived: List[PipelineEvent] = []
        if command == "configureCountProfile" and "countProfile" in payload:
            self._counting.configure_profile(payload["countProfile"])
        elif command == "configureRules" and "rules" in payload:
            decks = payload["rules"].get("decks")
            if decks:
                self._counting.configure_decks(float(decks))
        elif command == "setDecksRemaining":
            self._counting.set_decks_remaining(payload.get("value"))
            derived.append(
                CommandEvent(
                    timestamp=event.timestamp,
                    command="countSnapshot",
                    payload=dict(self._counting.snapshot()),
                )
            )
        elif command == "beginRound":
            self._begin_round()
            derived.append(self._round_state_event(event.timestamp, "roundStarted"))
        elif command == "split":
            seat_id = payload.get("seatId")
            if seat_id:
                self._apply_split(seat_id)
                derived.append(self._round_state_event(event.timestamp, "handSplit", seat_id=seat_id))
        elif command == "double":
            seat_id = payload.get("seatId")
            hand_index = int(payload.get("handIndex", 0))
            if seat_id:
                seat = self._ensure_seat(seat_id)
                hand = seat.ensure_hand(hand_index)
                hand.doubled = True
                derived.append(
                    self._round_state_event(
                        event.timestamp, "handDoubled", seat_id=seat_id, hand_index=hand_index
                    )
                )
        elif command == "finalizeRound":
            summary_payload = payload.copy()
            summary_payload.update(self._build_round_snapshot())
            derived.append(
                CommandEvent(
                    timestamp=event.timestamp,
                    command="roundSummary",
                    payload=summary_payload,
                )
            )
            self._end_round()
        return derived

    def _handle_observation(self, event: ObservationEvent) -> List[PipelineEvent]:
        if not self._round_active:
            self._begin_round()
        zone_id = event.observation.get("zoneId", "")
        rank = event.observation.get("rank")
        derived: List[PipelineEvent] = []

        if not rank:
            return derived

        if zone_id.startswith(PLAYER_ZONE_PREFIX):
            seat = self._ensure_seat(zone_id)
            hand = self._select_hand_for_card(seat)
            hand.cards.append(rank)
            derived.append(
                self._round_state_event(
                    event.timestamp,
                    "cardAdded",
                    seat_id=zone_id,
                    hand_index=hand.hand_index,
                    rank=rank,
                )
            )
        else:
            self._dealer.cards.append(rank)
            derived.append(
                self._round_state_event(
                    event.timestamp,
                    "dealerCardAdded",
                    seat_id="dealer",
                    hand_index=0,
                    rank=rank,
                )
            )

        snapshot = self._counting.observe_card(rank)
        derived.append(
            CommandEvent(
                timestamp=event.timestamp,
                command="countSnapshot",
                payload=dict(snapshot),
            )
        )
        return derived

    # -- Helpers -------------------------------------------------------
    def _begin_round(self) -> None:
        self._round_index += 1
        self._round_active = True
        self._seats = {}
        self._dealer = HandState(hand_index=0)
        self._counting.reset_round()

    def _end_round(self) -> None:
        self._round_active = False

    def _ensure_seat(self, seat_id: str) -> SeatState:
        if seat_id not in self._seats:
            self._seats[seat_id] = SeatState(seat_id=seat_id)
        return self._seats[seat_id]

    def _apply_split(self, seat_id: str) -> None:
        seat = self._ensure_seat(seat_id)
        hand = seat.ensure_hand(0)
        if len(hand.cards) < 2:
            return
        first_card, second_card = hand.cards[0], hand.cards[1]
        hand.cards = [first_card]
        new_hand = HandState(hand_index=len(seat.hands), cards=[second_card])
        seat.hands.append(new_hand)

    def _select_hand_for_card(self, seat: SeatState) -> HandState:
        hand = min(seat.hands, key=lambda h: (len(h.cards), h.hand_index))
        return hand

    def _build_round_snapshot(self) -> Dict[str, object]:
        return {
            "round": self._round_index,
            "dealer": self._dealer.to_dict(),
            "seats": [seat.to_dict() for seat in sorted(self._seats.values(), key=lambda s: s.seat_id)],
            "count": dict(self._counting.snapshot()),
        }

    def _round_state_event(self, timestamp: float, command: str, **payload: object) -> CommandEvent:
        data = self._build_round_snapshot()
        data.update(payload)
        return CommandEvent(
            timestamp=timestamp,
            command=command,
            payload=data,
        )

