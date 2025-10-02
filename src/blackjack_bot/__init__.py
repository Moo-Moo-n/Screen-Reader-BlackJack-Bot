"""Blackjack card-counting assistant skeleton package."""

from .schemas import load_all_schemas, SchemaRegistry
from .acceptance import AcceptanceHarness, CheckResult, run_acceptance_checks
from .adapters import (
    CaptureAdapter,
    VisionAdapter,
    GameStateTracker,
    StrategyAdvisor,
    BetSizingEngine,
    PersistenceAdapter,
    NoOpCaptureAdapter,
    NoOpVisionAdapter,
    NoOpGameStateTracker,
    NoOpStrategyAdvisor,
    NoOpBetSizingEngine,
    InMemoryPersistenceAdapter,
)
from .counting import CountingEngine, CountProfileConfig
from .state import RoundStateTracker
from .zones import (
    Region,
    Zone,
    ZonesConfig,
    ZonesConfigStore,
    PlaceholderRenderer,
    generate_default_zones,
)
__all__ = [
    "load_all_schemas",
    "SchemaRegistry",
    "CaptureAdapter",
    "VisionAdapter",
    "GameStateTracker",
    "StrategyAdvisor",
    "BetSizingEngine",
    "PersistenceAdapter",
    "NoOpCaptureAdapter",
    "NoOpVisionAdapter",
    "NoOpGameStateTracker",
    "NoOpStrategyAdvisor",
    "NoOpBetSizingEngine",
    "InMemoryPersistenceAdapter",
    "CountingEngine",
    "CountProfileConfig",
    "RoundStateTracker",
    "AcceptanceHarness",
    "CheckResult",
    "run_acceptance_checks",
    "Region",
    "Zone",
    "ZonesConfig",
    "ZonesConfigStore",
    "PlaceholderRenderer",
    "generate_default_zones",
]
