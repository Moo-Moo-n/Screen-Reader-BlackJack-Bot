"""Utilities for managing the calibrated table region and seat zones."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple
import json


Point = Tuple[float, float]


@dataclass
class Region:
    """Represents the calibrated capture region on screen."""

    x: float
    y: float
    w: float
    h: float

    def to_dict(self) -> dict:
        return {"x": self.x, "y": self.y, "w": self.w, "h": self.h}

    @classmethod
    def from_dict(cls, payload: dict) -> "Region":
        return cls(
            x=float(payload.get("x", 0.0)),
            y=float(payload.get("y", 0.0)),
            w=float(payload.get("w", 0.0)),
            h=float(payload.get("h", 0.0)),
        )

    def normalize(self, point: Point) -> Point:
        """Convert an absolute point into the region's 0-1 coordinate space."""

        if self.w == 0 or self.h == 0:
            return 0.0, 0.0
        px, py = point
        nx = (px - self.x) / self.w
        ny = (py - self.y) / self.h
        return nx, ny

    def denormalize(self, point: Point) -> Point:
        """Convert a 0-1 point back into absolute coordinates."""

        px, py = point
        return self.x + px * self.w, self.y + py * self.h


@dataclass
class Zone:
    """Individual seat or dealer polygon."""

    id: str
    polygon: List[Point] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "polygon": [[float(x), float(y)] for x, y in self.polygon],
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "Zone":
        polygon_payload: Iterable[Sequence[float]] = payload.get("polygon", [])
        polygon: List[Point] = [
            (float(point[0]), float(point[1]))
            for point in polygon_payload
            if len(point) >= 2
        ]
        return cls(id=str(payload.get("id", "")), polygon=polygon)

    def centroid(self) -> Point:
        if not self.polygon:
            return 0.0, 0.0
        xs = [point[0] for point in self.polygon]
        ys = [point[1] for point in self.polygon]
        return sum(xs) / len(xs), sum(ys) / len(ys)

    def bounds(self) -> Tuple[Point, Point]:
        if not self.polygon:
            return (0.0, 0.0), (0.0, 0.0)
        xs = [point[0] for point in self.polygon]
        ys = [point[1] for point in self.polygon]
        return (min(xs), min(ys)), (max(xs), max(ys))

    def rescale(self, old_region: Region, new_region: Region) -> "Zone":
        """Return a new zone with polygon scaled into the new region."""

        if not self.polygon:
            return Zone(id=self.id, polygon=[])
        scaled: List[Point] = []
        for point in self.polygon:
            if old_region.w == 0 or old_region.h == 0:
                scaled.append(new_region.denormalize((0.0, 0.0)))
                continue
            nx, ny = old_region.normalize(point)
            scaled.append(new_region.denormalize((nx, ny)))
        return Zone(id=self.id, polygon=scaled)


@dataclass
class ZonesConfig:
    """Collection of seat zones scoped to a capture region."""

    region: Region
    zones: List[Zone]

    def to_dict(self) -> dict:
        return {
            "region": self.region.to_dict(),
            "zones": [zone.to_dict() for zone in self.zones],
        }

    @classmethod
    def from_dict(cls, payload: dict) -> "ZonesConfig":
        region_payload = payload.get("region", {})
        zones_payload = payload.get("zones", [])
        region = Region.from_dict(region_payload)
        zones = [Zone.from_dict(item) for item in zones_payload]
        return cls(region=region, zones=zones)

    @classmethod
    def default(cls, region: Region | None = None, seat_count: int = 7) -> "ZonesConfig":
        if region is None:
            region = Region(x=0.0, y=0.0, w=1280.0, h=720.0)
        zones = generate_default_zones(region, seat_count=seat_count)
        return cls(region=region, zones=zones)

    def rescaled(self, new_region: Region) -> "ZonesConfig":
        scaled_zones = [zone.rescale(self.region, new_region) for zone in self.zones]
        return ZonesConfig(region=new_region, zones=scaled_zones)


def generate_default_zones(region: Region, seat_count: int = 7) -> List[Zone]:
    """Produce a simple rectangular layout for seats and dealer."""

    zones: List[Zone] = []
    if seat_count <= 0:
        seat_count = 1

    horizontal_margin = region.w * 0.05
    vertical_margin = region.h * 0.1
    usable_width = max(region.w - 2 * horizontal_margin, 1.0)
    seat_stride = usable_width / seat_count
    seat_width = seat_stride * 0.75
    seat_height = max(region.h * 0.18, 1.0)
    base_y = region.y + region.h - vertical_margin - seat_height

    for index in range(seat_count):
        left = region.x + horizontal_margin + index * seat_stride
        right = left + seat_width
        top = base_y
        bottom = base_y + seat_height
        polygon = [(left, top), (right, top), (right, bottom), (left, bottom)]
        zones.append(Zone(id=f"seat_{index + 1}", polygon=polygon))

    dealer_width = max(region.w * 0.2, seat_width)
    dealer_height = max(region.h * 0.15, 1.0)
    dealer_left = region.x + (region.w - dealer_width) / 2
    dealer_top = region.y + vertical_margin
    dealer_polygon = [
        (dealer_left, dealer_top),
        (dealer_left + dealer_width, dealer_top),
        (dealer_left + dealer_width, dealer_top + dealer_height),
        (dealer_left, dealer_top + dealer_height),
    ]
    zones.append(Zone(id="dealer", polygon=dealer_polygon))
    return zones


class ZonesConfigStore:
    """Persist zones configuration alongside the project."""

    def __init__(self, path: Path | None = None) -> None:
        if path is None:
            path = Path(__file__).resolve().parents[2] / "zones_config.json"
        self.path = path

    def load(self) -> ZonesConfig:
        if not self.path.exists():
            return ZonesConfig.default()
        with self.path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        return ZonesConfig.from_dict(payload)

    def save(self, config: ZonesConfig) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(config.to_dict(), handle, indent=2, sort_keys=True)

    def set_region(self, region: Region, preserve_zones: bool = True) -> ZonesConfig:
        current = self.load()
        if preserve_zones and current.zones:
            updated = current.rescaled(region)
        else:
            updated = ZonesConfig.default(region=region)
        self.save(updated)
        return updated


class PlaceholderRenderer:
    """Renders a coarse ASCII preview of the configured zones."""

    def __init__(self, config: ZonesConfig, width: int = 60, height: int = 20) -> None:
        self.config = config
        self.width = max(width, 10)
        self.height = max(height, 10)

    def render(self) -> str:
        canvas = [[" " for _ in range(self.width)] for _ in range(self.height)]
        self._draw_border(canvas)

        label_map: dict[str, str] = {}
        for zone in self.config.zones:
            label = self._label_for(zone, label_map)
            self._draw_zone(canvas, zone, label)
            label_map[zone.id] = label

        lines = ["".join(row) for row in canvas]
        legend = ["", "Legend:"]
        for zone in self.config.zones:
            label = label_map.get(zone.id, "?")
            (min_x, min_y), (max_x, max_y) = zone.bounds()
            legend.append(
                f"  {label}: {zone.id} (x={min_x:.0f}–{max_x:.0f}, y={min_y:.0f}–{max_y:.0f})"
            )
        return "\n".join(lines + legend)

    def _draw_border(self, canvas: List[List[str]]) -> None:
        last_row = self.height - 1
        last_col = self.width - 1
        for col in range(self.width):
            canvas[0][col] = "-"
            canvas[last_row][col] = "-"
        for row in range(self.height):
            canvas[row][0] = "|"
            canvas[row][last_col] = "|"
        canvas[0][0] = "+"
        canvas[0][last_col] = "+"
        canvas[last_row][0] = "+"
        canvas[last_row][last_col] = "+"

    def _draw_zone(self, canvas: List[List[str]], zone: Zone, label: str) -> None:
        if not zone.polygon:
            return
        region = self.config.region
        xs = [point[0] for point in zone.polygon]
        ys = [point[1] for point in zone.polygon]
        min_col, max_col = self._project_bounds(xs, region.w, region.x, self.width)
        min_row, max_row = self._project_bounds(ys, region.h, region.y, self.height)

        for col in range(min_col, max_col + 1):
            canvas[min_row][col] = "#"
            canvas[max_row][col] = "#"
        for row in range(min_row, max_row + 1):
            canvas[row][min_col] = "#"
            canvas[row][max_col] = "#"

        cx, cy = zone.centroid()
        col, row = self._project_point(cx, cy, region)
        self._write_label(canvas, row, col, label)

    def _project_bounds(
        self, values: List[float], span: float, offset: float, size: int
    ) -> Tuple[int, int]:
        if not values or span == 0:
            return 1, max(1, size - 2)
        min_v = min(values)
        max_v = max(values)
        min_norm = (min_v - offset) / span
        max_norm = (max_v - offset) / span
        min_idx = max(1, min(size - 2, int(min_norm * (size - 1))))
        max_idx = max(1, min(size - 2, int(max_norm * (size - 1))))
        if min_idx > max_idx:
            min_idx, max_idx = max_idx, min_idx
        return min_idx, max_idx

    def _project_point(self, x: float, y: float, region: Region) -> Tuple[int, int]:
        if region.w == 0 or region.h == 0:
            return self.width // 2, self.height // 2
        norm_x = (x - region.x) / region.w
        norm_y = (y - region.y) / region.h
        col = int(round(norm_x * (self.width - 1)))
        row = int(round(norm_y * (self.height - 1)))
        col = max(1, min(self.width - 2, col))
        row = max(1, min(self.height - 2, row))
        return col, row

    def _write_label(self, canvas: List[List[str]], row: int, col: int, label: str) -> None:
        for index, char in enumerate(label):
            target_col = col + index
            if target_col >= self.width - 1:
                break
            canvas[row][target_col] = char

    def _label_for(self, zone: Zone, existing: dict[str, str]) -> str:
        if zone.id.startswith("seat_"):
            suffix = zone.id.split("_", 1)[1]
            label = suffix[:2]
        else:
            label = zone.id[:2].upper()

        attempt = label
        counter = 1
        while attempt in existing.values():
            counter += 1
            attempt = f"{label}{counter}"
        return attempt


__all__ = [
    "Region",
    "Zone",
    "ZonesConfig",
    "ZonesConfigStore",
    "PlaceholderRenderer",
    "generate_default_zones",
]

