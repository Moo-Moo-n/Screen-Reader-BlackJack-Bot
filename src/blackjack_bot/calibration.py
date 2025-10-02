"""Command line helpers for configuring the capture region and zones."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

from .zones import PlaceholderRenderer, Region, ZonesConfig, ZonesConfigStore


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Optional path to a zones_config.json file (defaults to project root).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    set_region = subparsers.add_parser(
        "set-region", help="Persist a new capture region (x, y, width, height)."
    )
    set_region.add_argument("x", type=float)
    set_region.add_argument("y", type=float)
    set_region.add_argument("width", type=float)
    set_region.add_argument("height", type=float)
    set_region.add_argument(
        "--reset-zones",
        action="store_true",
        help="Regenerate seat polygons instead of scaling existing ones.",
    )

    subparsers.add_parser("show", help="Print the stored configuration as JSON.")

    render = subparsers.add_parser(
        "render", help="Display an ASCII preview of the current zone layout."
    )
    render.add_argument("--width", type=int, default=60)
    render.add_argument("--height", type=int, default=20)

    reset = subparsers.add_parser(
        "reset", help="Restore the configuration to the default layout."
    )
    reset.add_argument(
        "--seat-count",
        type=int,
        default=7,
        help="Number of player seats to generate in the default layout.",
    )
    return parser


def _resolve_store(path: Path | None) -> ZonesConfigStore:
    return ZonesConfigStore(path)


def _handle_set_region(args: argparse.Namespace) -> int:
    store = _resolve_store(args.config)
    region = Region(x=args.x, y=args.y, w=args.width, h=args.height)
    updated = store.set_region(region, preserve_zones=not args.reset_zones)
    print(
        "Capture region updated to "
        f"x={updated.region.x:.0f}, y={updated.region.y:.0f}, "
        f"w={updated.region.w:.0f}, h={updated.region.h:.0f}."
    )
    print(f"Configuration saved to {store.path}.")
    return 0


def _handle_show(args: argparse.Namespace) -> int:
    store = _resolve_store(args.config)
    config = store.load()
    print(json.dumps(config.to_dict(), indent=2, sort_keys=True))
    return 0


def _handle_render(args: argparse.Namespace) -> int:
    store = _resolve_store(args.config)
    config = store.load()
    renderer = PlaceholderRenderer(config, width=args.width, height=args.height)
    print(renderer.render())
    return 0


def _handle_reset(args: argparse.Namespace) -> int:
    store = _resolve_store(args.config)
    config = ZonesConfig.default(seat_count=args.seat_count)
    store.save(config)
    print(f"Configuration reset with {args.seat_count} seats at {store.path}.")
    return 0


def main(argv: List[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    if args.command == "set-region":
        return _handle_set_region(args)
    if args.command == "show":
        return _handle_show(args)
    if args.command == "render":
        return _handle_render(args)
    if args.command == "reset":
        return _handle_reset(args)
    parser.error(f"Unsupported command: {args.command}")
    return 1


if __name__ == "__main__":  # pragma: no cover - CLI behaviour
    raise SystemExit(main())

