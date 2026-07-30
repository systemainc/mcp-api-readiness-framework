"""
CLI entry point: python -m framework.cli scan --config <path> --target <dir>

Commands:
  scan      Run the full scorer against a target directory.
  validate  Validate a config file without scanning.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from .config import load_config
from .scanner import run_scan


_LEVEL_LABELS = {
    1: "Not Ready",
    2: "Partial",
    3: "Capable",
    4: "Robust",
}

_DIM_DISPLAY_ORDER = [
    "write_safety",
    "boundary_enforcement",
    "consent_auth",
    "forensics",
    "interface_legibility",
    "operational_containment",
]


def _print_scorecard(scorecard) -> None:
    label = _LEVEL_LABELS.get(scorecard.overall_level, "?")
    print(f"\n{'='*60}")
    print(f"  MCP API Readiness: {scorecard.target}")
    print(f"  Overall Level: {scorecard.overall_level}/4 — {label}")
    print(f"{'='*60}\n")

    ordered = sorted(
        scorecard.dimensions,
        key=lambda d: _DIM_DISPLAY_ORDER.index(d.id) if d.id in _DIM_DISPLAY_ORDER else 99,
    )
    for dim in ordered:
        label = _LEVEL_LABELS.get(dim.level, "?")
        flag = " [insufficient data]" if dim.insufficient_data else ""
        passed = sum(1 for check in dim.check_results if check.passed)
        total = len(dim.check_results)
        print(f"  {dim.name}{flag}")
        print(f"    Level {dim.level}/4 — {label} (weighted score)   Checks passed: {passed}/{total}")
        for check in dim.check_results:
            label = "PASS" if check.passed else "FAIL"
            print(f"         [{label}] {check.description}")
            print(f"           {check.evidence}")
        if dim.legibility_note:
            print(f"\n         [Legibility assessment]")
            print(f"         {dim.legibility_note}")
        print()

    if scorecard.scan_errors:
        print("Scan warnings:")
        for err in scorecard.scan_errors:
            print(f"  ! {err}")
        print()


def _write_dashboard_data(scorecard, path: str) -> None:
    """Emit window.MCP_READINESS_DATA = {...}; for docs/dashboard.html to pick up.

    Same shape as the --output JSON (asdict(scorecard)), just wrapped as a JS
    assignment so it can be loaded via <script src="..."> from a file:// page
    with no build step or fetch/CORS concerns.
    """
    payload = json.dumps(asdict(scorecard), indent=2)
    Path(path).write_text(f"window.MCP_READINESS_DATA = {payload};\n")


def cmd_scan(args: argparse.Namespace) -> int:
    target = args.target or str(Path(args.config).parent)
    scorecard = run_scan(args.config, target)
    _print_scorecard(scorecard)
    if args.output:
        Path(args.output).write_text(json.dumps(asdict(scorecard), indent=2))
        print(f"Scorecard written to {args.output}")
    if args.dashboard_data:
        _write_dashboard_data(scorecard, args.dashboard_data)
        print(f"Dashboard data written to {args.dashboard_data}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    try:
        config = load_config(args.config)
        print(f"Config valid: {len(config.dimensions)} dimensions configured for '{config.target_name}'")
        return 0
    except Exception as e:
        print(f"Config invalid: {e}", file=sys.stderr)
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(prog="python -m framework.cli")
    sub = parser.add_subparsers(dest="command")

    scan_p = sub.add_parser("scan", help="Score a target codebase")
    scan_p.add_argument("--config", required=True, help="Path to config YAML")
    scan_p.add_argument("--target", default=None, help="Path to target codebase (default: config dir)")
    scan_p.add_argument("--output", default=None, help="Write JSON scorecard to this path")
    scan_p.add_argument(
        "--dashboard-data",
        default=None,
        help="Write a window.MCP_READINESS_DATA=...; JS file to this path, "
        "for docs/dashboard.html to load in place of its sample data",
    )

    val_p = sub.add_parser("validate", help="Validate config without scanning")
    val_p.add_argument("--config", required=True)

    args = parser.parse_args()
    if args.command == "scan":
        return cmd_scan(args)
    elif args.command == "validate":
        return cmd_validate(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
