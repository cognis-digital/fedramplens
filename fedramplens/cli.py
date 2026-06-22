"""Command-line interface for FEDRAMPLENS."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from . import TOOL_NAME, TOOL_VERSION
from . import datafeeds
from .controls import RELEVANT_FEED_IDS
from .core import (
    BoundaryError,
    load_boundary,
    analyze_boundary,
    generate_dot,
    generate_ssp,
    generate_poam,
    to_sarif,
)


# --------------------------------------------------------------------------- #
# data-feed layer (edge / air-gap deployable)
# --------------------------------------------------------------------------- #
def _relevant_feeds() -> list:
    """Catalog entries this compliance tool consumes (OSCAL 800-53 only)."""
    catalog = datafeeds.load_catalog()
    return [f for f in catalog.get("feeds", []) if f["id"] in RELEVANT_FEED_IDS]


def _cmd_feeds(args) -> int:
    """`fedramplens feeds list|update|get <id>` — the data-feed layer."""
    relevant_ids = {f["id"] for f in _relevant_feeds()}

    if args.feeds_cmd == "list":
        for f in _relevant_feeds():
            age = datafeeds.cached_age_hours(f["id"])
            fresh = "uncached" if age is None else f"{age:.1f}h old"
            print(f"  {f['id']:30} {f.get('domain',''):11} [{fresh}]  {f['name']}")
            print(f"      {f.get('url','')}")
        return 0

    fid = getattr(args, "feed_id", None)
    if fid not in relevant_ids:
        print(
            f"error: {fid!r} is not a feed for {TOOL_NAME}; "
            f"relevant feeds: {', '.join(sorted(relevant_ids))}",
            file=sys.stderr,
        )
        return 2

    if args.feeds_cmd == "update":
        try:
            path = datafeeds.update(fid)
        except (KeyError, ConnectionError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        print(f"updated {fid} -> {path} ({path.stat().st_size} bytes)")
        return 0

    if args.feeds_cmd == "get":
        try:
            data = datafeeds.get(fid, offline=args.offline)
        except (KeyError, FileNotFoundError, ConnectionError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        text = (
            json.dumps(data, indent=2)
            if isinstance(data, (dict, list))
            else str(data)
        )
        print(text[:4000])
        return 0

    print("error: feeds subcommand required (list|update|get)", file=sys.stderr)
    return 2


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
        ctl = ""
        if f.get("control"):
            title = f.get("control_title")
            ctl = f" [{f['control']}: {title}]" if title else f" [{f['control']}]"
        print(f"  - ({f['severity']}) {f['type']}{ctl}: {f['detail']}")
    if summary.get("control_titles"):
        src = "cache" if not summary.get("feed_available", True) else "OSCAL 800-53 rev5"
        print(f"Control titles resolved from NIST {src}:")
        for cid, title in sorted(summary["control_titles"].items()):
            print(f"  {cid.upper():10} {title}")
    ready = "YES" if summary["authorization_ready"] else "NO"
    print(f"Authorization-ready (no high/critical findings): {ready}")


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
        "--format", choices=("table", "json", "sarif"), default="table",
        help="output format for analyze: table | json | sarif 2.1.0 "
             "(default: table; ignored for dot/ssp/poam)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_an = sub.add_parser("analyze", help="analyze boundary integrity & coverage")
    p_an.add_argument("boundary", help="path to boundary JSON file")
    p_an.add_argument(
        "--enrich", action="store_true",
        help="resolve NIST 800-53 rev5 control titles from the OSCAL data feed",
    )
    p_an.add_argument(
        "--offline", action="store_true",
        help="serve the OSCAL feed from the on-disk cache only (air-gap mode)",
    )

    p_dot = sub.add_parser("diagram", help="emit Graphviz DOT for the boundary")
    p_dot.add_argument("boundary", help="path to boundary JSON file")

    p_ssp = sub.add_parser("ssp", help="generate OSCAL-style SSP (JSON)")
    p_ssp.add_argument("boundary", help="path to boundary JSON file")
    p_ssp.add_argument(
        "--enrich", action="store_true",
        help="annotate implemented controls with their 800-53 titles",
    )
    p_ssp.add_argument(
        "--offline", action="store_true",
        help="serve the OSCAL feed from cache only (air-gap mode)",
    )

    p_poam = sub.add_parser("poam", help="generate OSCAL-style POA&M (JSON)")
    p_poam.add_argument("boundary", help="path to boundary JSON file")

    # feeds: edge/air-gap data-feed ingestion layer
    p_feeds = sub.add_parser(
        "feeds",
        help="manage the NIST 800-53 OSCAL data feed (list|update|get)",
    )
    fsub = p_feeds.add_subparsers(dest="feeds_cmd", required=True)
    fsub.add_parser("list", help="list the feeds relevant to this tool")
    f_up = fsub.add_parser("update", help="fetch + cache a feed by id")
    f_up.add_argument("feed_id", help="feed id (e.g. oscal-800-53-rev5-catalog)")
    f_get = fsub.add_parser("get", help="print a cached/fetched feed by id")
    f_get.add_argument("feed_id", help="feed id (e.g. oscal-800-53-rev5-catalog)")
    f_get.add_argument(
        "--offline", action="store_true",
        help="serve from the on-disk cache only (never touch the network)",
    )

    args = parser.parse_args(argv)

    # feeds command does not need a boundary file
    if args.command == "feeds":
        return _cmd_feeds(args)

    try:
        b = load_boundary(args.boundary)
    except FileNotFoundError:
        print(f"error: file not found: {args.boundary}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON: {exc}", file=sys.stderr)
        return 2
    except BoundaryError as exc:
        print(f"error: invalid boundary: {exc}", file=sys.stderr)
        return 2

    if args.command == "analyze":
        summary = analyze_boundary(
            b, resolve_titles=args.enrich, offline=args.offline
        )
        if args.format == "json":
            print(json.dumps(summary, indent=2))
        elif args.format == "sarif":
            print(json.dumps(to_sarif(summary), indent=2))
        else:
            _print_analysis_table(summary)
        # Non-zero exit if not authorization-ready.
        return 0 if summary["authorization_ready"] else 1

    if args.command == "diagram":
        print(generate_dot(b))
        return 0

    if args.command == "ssp":
        print(json.dumps(
            generate_ssp(b, resolve_titles=args.enrich, offline=args.offline),
            indent=2,
        ))
        return 0

    if args.command == "poam":
        print(json.dumps(generate_poam(b), indent=2))
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
