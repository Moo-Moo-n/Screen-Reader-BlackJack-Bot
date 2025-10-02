"""Utilities for loading JSON schema contracts."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable
import json


@dataclass
class SchemaRegistry:
    """Holds loaded JSON schemas keyed by filename."""

    root: Path
    schemas: Dict[str, dict]

    def get(self, name: str) -> dict:
        """Return a schema by file stem or filename."""
        key = name
        if not key.endswith(".json"):
            key = f"{key}.json"
        schema = self.schemas.get(key)
        if schema is None:
            raise KeyError(f"Schema '{name}' not found. Available: {sorted(self.schemas)}")
        return schema

    def items(self) -> Iterable[tuple[str, dict]]:
        return self.schemas.items()


def load_all_schemas(contracts_dir: Path | None = None) -> SchemaRegistry:
    """Load every JSON schema from the contracts directory."""
    if contracts_dir is None:
        module_path = Path(__file__).resolve()
        search_roots = [
            module_path.parents[1] / "contracts",
            module_path.parents[2] / "contracts",
            Path.cwd() / "contracts",
        ]
        for candidate in search_roots:
            if candidate.exists():
                contracts_dir = candidate
                break
        else:
            raise FileNotFoundError("Could not locate contracts directory.")
    schemas: Dict[str, dict] = {}
    for path in sorted(contracts_dir.glob("*.json")):
        with path.open("r", encoding="utf-8") as handle:
            schemas[path.name] = json.load(handle)
    return SchemaRegistry(root=contracts_dir, schemas=schemas)
