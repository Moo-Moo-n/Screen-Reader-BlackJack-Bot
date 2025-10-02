"""Acceptance harness implementing the QA plan checks."""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Dict, List, Optional

from .runner import Pipeline


@dataclass
class CheckResult:
    """Represents the outcome of a single acceptance check."""

    name: str
    passed: bool
    details: str
    data: Optional[Dict[str, object]] = None


class AcceptanceHarness:
    """Runs the acceptance checks described in QA.md."""

    def __init__(self, project_root: Optional[Path] = None) -> None:
        if project_root is None:
            project_root = Path(__file__).resolve().parents[2]
        self.project_root = project_root
        self.fixtures_dir = self.project_root / "fixtures"
        self.contracts_dir = self.project_root / "contracts"

    # -- Public API -----------------------------------------------------
    def run_all(self) -> List[CheckResult]:
        """Execute all checks in QA.md order."""

        return [
            self.check_count_consistency(),
            self.check_strategy_flip_determinism(),
            self.check_fixture_playback_integrity(),
            self.check_splits_and_doubles_state_machine(),
            self.check_performance_budget(),
            self.check_operator_overrides(),
        ]

    # -- Individual checks ----------------------------------------------
    def check_count_consistency(self) -> CheckResult:
        """Placeholder for count consistency validation (QA section A)."""

        fixture = self.fixtures_dir / "deck_drain_sequence.json"
        if not fixture.exists():
            return CheckResult(
                name="A. Count Consistency",
                passed=False,
                details="Fixture deck_drain_sequence.json is missing.",
            )

        return CheckResult(
            name="A. Count Consistency",
            passed=False,
            details=(
                "Pending implementation: counting engine is not available "
                "to verify running/true count snapshots."
            ),
        )

    def check_strategy_flip_determinism(self) -> CheckResult:
        """Placeholder for strategy flip validation (QA section B)."""

        fixture = self.fixtures_dir / "strategy_flip_cases.json"
        if not fixture.exists():
            return CheckResult(
                name="B. Strategy Flip Determinism",
                passed=False,
                details="Fixture strategy_flip_cases.json is missing.",
            )

        return CheckResult(
            name="B. Strategy Flip Determinism",
            passed=False,
            details=(
                "Pending implementation: strategy advisor does not yet "
                "apply deviation thresholds."
            ),
        )

    def check_fixture_playback_integrity(self) -> CheckResult:
        """Runs the simple stream through the pipeline and compares exports."""

        expected_path = self.fixtures_dir / "export_expected_summary.json"
        fixture_path = self.fixtures_dir / "stream_simple_round.json"
        missing_files: List[str] = [
            str(path.name)
            for path in (expected_path, fixture_path)
            if not path.exists()
        ]
        if missing_files:
            return CheckResult(
                name="C. Fixture Playback Integrity",
                passed=False,
                details=f"Missing required fixture files: {', '.join(missing_files)}.",
            )

        expected_summary = self._load_json(expected_path)
        pipeline_output = self._run_pipeline(fixture_path)
        export = pipeline_output.get("export", {})

        discrepancies: Dict[str, object] = {}
        tolerance = 1e-6
        for key, expected in expected_summary.items():
            actual = export.get(key)
            if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
                if not math.isclose(float(actual), float(expected), rel_tol=0.05, abs_tol=0.05):
                    discrepancies[key] = {"expected": expected, "actual": actual}
            elif actual != expected:
                discrepancies[key] = {"expected": expected, "actual": actual}

        passed = not discrepancies
        detail = (
            "Export matches expected summary within tolerance."
            if passed
            else "Export differs from expected summary."
        )

        return CheckResult(
            name="C. Fixture Playback Integrity",
            passed=passed,
            details=detail,
            data={
                "discrepancies": discrepancies,
                "observed_export": export,
                "pipeline_events": pipeline_output.get("events", []),
            },
        )

    def check_splits_and_doubles_state_machine(self) -> CheckResult:
        """Placeholder for split/double validation (QA section D)."""

        fixture = self.fixtures_dir / "stream_split_double_round.json"
        if not fixture.exists():
            return CheckResult(
                name="D. Splits and Doubles State Machine",
                passed=False,
                details="Fixture stream_split_double_round.json is missing.",
            )

        return CheckResult(
            name="D. Splits and Doubles State Machine",
            passed=False,
            details=(
                "Pending implementation: game state tracker lacks split/"
                "double handling."
            ),
        )

    def check_performance_budget(self) -> CheckResult:
        """Placeholder for performance timing validation (QA section E)."""

        return CheckResult(
            name="E. Performance Budget",
            passed=False,
            details=(
                "Pending implementation: pipeline does not emit timing "
                "metrics to validate latency."
            ),
        )

    def check_operator_overrides(self) -> CheckResult:
        """Placeholder for override audit validation (QA section F)."""

        return CheckResult(
            name="F. Operator Overrides",
            passed=False,
            details=(
                "Pending implementation: override workflow and audit log "
                "are not yet available."
            ),
        )

    # -- Internal helpers ------------------------------------------------
    def _run_pipeline(self, fixture_path: Path) -> Dict[str, object]:
        pipeline = Pipeline(fixture_path)
        return pipeline.run()

    def _load_json(self, path: Path) -> Dict[str, object]:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)


def run_acceptance_checks() -> List[CheckResult]:
    """Convenience function for programmatic access."""

    return AcceptanceHarness().run_all()


def main() -> int:
    """CLI entrypoint mirroring `python -m blackjack_bot.acceptance`."""

    results = run_acceptance_checks()
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"[{status}] {result.name}: {result.details}")
        if result.data:
            print(json.dumps(result.data, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI behaviour
    raise SystemExit(main())
