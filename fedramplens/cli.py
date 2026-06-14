"""Command-line interface for FEDRAMPLENS."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from . import TOOL_NAME, TOOL_VERSION
from .core import (
    BoundaryError,
    load_boundary,
    analyze_boundary,
    generate_dot,
    generate_ssp,
    generate_poam,
)


def _print_analysis_table(summary: dict) -> None:
    print(f"System : {summary['system_name']} ({summary['system_id']})")
    print(f"Impact : {summary['impact'].upper()}")
    print(
        f"Controls: {summary['controls_implemented']}/"
        f"{summary['baseline_controls']} "
        f"({summary['coverage_pct']}% of baseline)"
    )
    print(
        f"Boundary: {summary['components_in_boundary']} components, "
        f"{summary['flows']} flows, "
        f"{len(summary['external_dependencies'])} external deps"
    )
    print(
        f"POA&M  : {summary['poam_open']} open, "
        f"{len(summary['poam_overdue'])} overdue, "
        f"risk score {summary['poam_risk_score']}"
    )
    counts = summary["finding_counts"]
    cnt_str = ", ".join(f"{k}={v}" for k, v in sorted(counts.items())) or "none"
    print(f"Findings: {cnt_str}")
    for f in summary["findings"]:
        ctl = f" [{f['control']}]" if f.get("control") else ""
        print(f"  - ({f['severity']}) {f['type']}{ctl}: {f['detail']}")
    ready = "YES" if summary["authorization_ready"] else "NO"
    print(f"Authorization-ready (no high/critical findings): {ready}")


def _emit(obj, fmt: str) -> None:
    if fmt == "json":
        print(json.dumps(obj, indent=2))


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog=TOOL_NAME,
        description="FedRAMP boundary visualizer & OSCAL SSP/POA&M generator.",
    )
    parser.add_argument(
        "--version", action="version",
        version=f"{TOOL_NAME} {TOOL_VERSION}",
    )
    parser.add_argument(
        "--format", choices=("table", "json"), default="table",
        help="output format (default: table; ignored for dot/ssp/poam)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_an = sub.add_parser("analyze", help="analyze boundary integrity & coverage")
    p_an.add_argument("boundary", help="path to boundary JSON file")

    p_dot = sub.add_parser("diagram", help="emit Graphviz DOT for the boundary")
    p_dot.add_argument("boundary", help="path to boundary JSON file")

    p_ssp = sub.add_parser("ssp", help="generate OSCAL-style SSP (JSON)")
    p_ssp.add_argument("boundary", help="path to boundary JSON file")

    p_poam = sub.add_parser("poam", help="generate OSCAL-style POA&M (JSON)")
    p_poam.add_argument("boundary", help="path to boundary JSON file")

    args = parser.parse_args(argv)

    try:
        b = load_boundary(args.boundary)
    except FileNotFoundError:
        print(f"error: file not found: {args.boundary}", file=sys.stderr)
        return 2
    except IsADirectoryError:
        print(
            f"error: path is a directory, not a file: {args.boundary}",
            file=sys.stderr,
        )
        return 2
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON in {args.boundary!r}: {exc}", file=sys.stderr)
        return 2
    except UnicodeDecodeError as exc:
        print(f"error: file is not valid UTF-8: {exc}", file=sys.stderr)
        return 2
    except BoundaryError as exc:
        print(f"error: invalid boundary: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"error: cannot read {args.boundary!r}: {exc}", file=sys.stderr)
        return 2

    if args.command == "analyze":
        summary = analyze_boundary(b)
        if args.format == "json":
            _emit(summary, "json")
        else:
            _print_analysis_table(summary)
        # Non-zero exit if not authorization-ready.
        return 0 if summary["authorization_ready"] else 1

    if args.command == "diagram":
        print(generate_dot(b))
        return 0

    if args.command == "ssp":
        print(json.dumps(generate_ssp(b), indent=2))
        return 0

    if args.command == "poam":
        print(json.dumps(generate_poam(b), indent=2))
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
