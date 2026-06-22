"""controls — resolve NIST SP 800-53 rev5 control titles from the real OSCAL catalog.

FEDRAMPLENS emits control ids (AC-2, SC-8, SC-13, ...) in its findings, SSP, and
POA&M. On their own those ids are opaque. This module loads the **authoritative**
NIST SP 800-53 rev5 catalog — distributed by NIST as native OSCAL JSON
(https://github.com/usnistgov/oscal-content) and bundled here as the
``oscal-800-53-rev5-catalog`` data feed — and builds an id -> title map so the
tool can say *what each control actually is*.

Edge / air-gap: the catalog is fetched once, cached to disk, and re-served
``offline``. If neither a cache nor the network is available the resolver simply
degrades to returning ids unchanged — analysis never hard-fails on a missing feed.

Defensive / authorized-use only.
"""
from __future__ import annotations

import re
from functools import lru_cache
from typing import Any, Dict, Optional

from . import datafeeds

# The single feed this compliance tool consumes.
FEED_ID = "oscal-800-53-rev5-catalog"
RELEVANT_FEED_IDS = (FEED_ID,)

_CTL_RE = re.compile(r"^[a-z]{2}-\d+(?:\.\d+)?$")


def _walk_controls(node: Dict[str, Any], out: Dict[str, str]) -> None:
    """Recursively collect id->title for controls and their enhancements."""
    cid = node.get("id")
    title = node.get("title")
    if cid and title:
        out[cid.lower()] = title
    for sub in node.get("controls", []) or []:
        _walk_controls(sub, out)


def build_title_map(catalog_json: Dict[str, Any]) -> Dict[str, str]:
    """Flatten an OSCAL 800-53 catalog into {control-id: title}.

    Control ids are normalized lower-case (``ac-2``, ``ac-2.1``) to match OSCAL.
    """
    out: Dict[str, str] = {}
    cat = catalog_json.get("catalog", catalog_json)
    for group in cat.get("groups", []) or []:
        # A group title is useful as a family label too (e.g. "ac" -> family).
        for ctl in group.get("controls", []) or []:
            _walk_controls(ctl, out)
    return out


@lru_cache(maxsize=4)
def _title_map(offline: bool) -> Dict[str, str]:
    """Load + cache the title map. Returns {} on any failure (graceful degrade)."""
    try:
        catalog = datafeeds.get(FEED_ID, offline=offline)
    except (FileNotFoundError, KeyError, ConnectionError, ValueError):
        return {}
    if not isinstance(catalog, dict):
        return {}
    return build_title_map(catalog)


def control_title(control_id: str, *, offline: bool = False) -> Optional[str]:
    """Return the official 800-53 title for a control id, or None if unknown.

    An enhancement (``AC-2(1)`` / ``AC-2.1``) falls back to its base control
    title when the enhancement itself is not present in the loaded catalog.
    """
    if not control_id:
        return None
    cid = _normalize(control_id)
    titles = _title_map(offline)
    if cid in titles:
        return titles[cid]
    base = cid.split(".", 1)[0]
    return titles.get(base)


def enrich_controls(
    control_ids, *, offline: bool = False
) -> Dict[str, Optional[str]]:
    """Map a list of control ids to their 800-53 titles (None if unresolved)."""
    return {c: control_title(c, offline=offline) for c in control_ids}


def _normalize(control_id: str) -> str:
    """Normalize ``AC-2(1)`` / ``AC-2.1`` / ``ac-2`` to OSCAL form ``ac-2.1``."""
    s = str(control_id).strip().lower()
    # AC-2(1) -> ac-2.1
    s = re.sub(r"\((\d+)\)", r".\1", s)
    return s


def reset_cache() -> None:
    """Clear the in-process title-map cache (used by tests)."""
    _title_map.cache_clear()
