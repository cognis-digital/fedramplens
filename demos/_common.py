"""Shared helpers for the fedramplens demo scenarios.

Every scenario loads a *bundled* boundary fixture (the JSON packages under
``demos/NN-*/boundary.json``) and drives the real ``fedramplens`` API — there
is no fabricated data or stubbed output. All scenarios run fully offline; the
OSCAL-enrichment scenario points the data-feed cache at the trimmed NIST
800-53 rev5 fixture under ``tests/fixtures/feedcache`` so it never touches the
network.
"""
from __future__ import annotations

import os
import sys

# allow `python demos/NN_name.py` from anywhere
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fedramplens.core import Boundary, load_boundary  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMOS_DIR = os.path.join(REPO_ROOT, "demos")

# The trimmed-but-real NIST 800-53 rev5 OSCAL catalog cache shipped for tests;
# reused here so the enrichment scenario resolves control titles offline.
OFFLINE_FEED_CACHE = os.path.join(
    REPO_ROOT, "tests", "fixtures", "feedcache"
)

# Map of the bundled boundary fixtures the scenarios draw on.
FIXTURES = {
    "basic": "01-basic",
    "clean_low": "02-clean-low-saas",
    "boundary_creep": "03-boundary-creep",
    "overdue_poam": "04-overdue-poam-backlog",
    "dangling_flow": "05-dangling-flow-typo",
    "orphan": "06-orphan-component",
    "high_ready": "07-high-baseline-ready",
    "bad_poam_date": "08-bad-poam-date",
    "multi_external": "09-multi-external-deps",
    "oscal_enrichment": "10-oscal-enrichment",
}


def fixture_path(key: str) -> str:
    """Absolute path to a bundled boundary fixture by short key."""
    return os.path.join(DEMOS_DIR, FIXTURES[key], "boundary.json")


def load(key: str) -> Boundary:
    """Load a bundled boundary fixture into a real ``Boundary`` object."""
    return load_boundary(fixture_path(key))


def use_offline_feed_cache() -> None:
    """Point the data-feed layer at the bundled offline OSCAL cache.

    Lets the enrichment scenario resolve real NIST 800-53 rev5 titles with
    ``offline=True`` and no network access.
    """
    os.environ["COGNIS_FEEDS_CACHE"] = OFFLINE_FEED_CACHE
    # The title map is lru_cached on the offline flag; clear it so a fresh
    # process picks up the fixture cache regardless of import order.
    try:
        from fedramplens import controls
        controls.reset_cache()
    except Exception:  # pragma: no cover - controls always importable
        pass


def rule(title: str) -> None:
    print("\n" + "=" * 72)
    print(f"  {title}")
    print("=" * 72)


def bullet(text: str) -> None:
    print(f"   - {text}")


def boundary_to_mermaid(b: Boundary) -> str:
    """Render a real ``Boundary`` as a Mermaid flowchart.

    In-boundary components sit inside an ``Authorization Boundary`` subgraph;
    external dependencies sit outside it. Encrypted flows are solid edges,
    unencrypted flows are dotted and labelled — the same boundary-crossing
    signal the analyzer flags as SC-8 findings. This is a demo-side view built
    purely from the public boundary data (mirrors ``generate_dot``).
    """
    def nid(name: str) -> str:
        return "n_" + "".join(ch if ch.isalnum() else "_" for ch in str(name))

    declared = b.component_ids()
    in_b = [c for c in b.components if c.get("zone") != "external"]
    ext = [c for c in b.components if c.get("zone") == "external"]

    lines = ["flowchart LR"]
    lines.append('  subgraph AB["Authorization Boundary"]')
    for c in in_b:
        lbl = str(c.get("name", c["id"])).replace('"', "'")
        lines.append(f'    {nid(c["id"])}["{lbl}"]')
    lines.append("  end")
    for c in ext:
        lbl = str(c.get("name", c["id"])).replace('"', "'")
        lines.append(f'  {nid(c["id"])}(["{lbl}"])')
    # external-token endpoints referenced only in flows (e.g. "internet")
    for fl in b.flows:
        for end in (fl["from"], fl["to"]):
            if end not in declared:
                declared = declared | {end}
                lines.append(f'  {nid(end)}(["{end}"])')
    for fl in b.flows:
        data = str(fl.get("data", "")).replace('"', "'")
        if fl.get("encrypted"):
            lines.append(f'  {nid(fl["from"])} -->|{data}| {nid(fl["to"])}')
        else:
            lines.append(f'  {nid(fl["from"])} -.->|{data} UNENCRYPTED| {nid(fl["to"])}')
    return "\n".join(lines)
