"""Scenario 15 - enrichment contract: enriched vs graceful-degrade.

Audience: integrators relying on control-title enrichment.

Enrichment must never turn a working analysis into a crash. This scenario runs
the SAME boundary two ways -- against the bundled OSCAL cache (titles resolve)
and against an empty cache (titles unresolved) -- and shows the analysis
summary is structurally identical either way, only the control_titles map and
feed_available flag differ. That is the degrade contract downstream code leans
on.
"""
import os
import tempfile

from _common import load, rule, bullet, use_offline_feed_cache
from fedramplens import controls
from fedramplens.core import analyze_boundary


def _summary(key):
    return analyze_boundary(load(key), resolve_titles=True, offline=True)


def main() -> None:
    rule("ENRICHMENT CONTRACT  -  enriched vs graceful degrade")

    # Enriched path.
    use_offline_feed_cache()
    enriched = _summary("oscal_enrichment")
    print("\nWith the bundled OSCAL cache:")
    bullet(f"feed_available   : {enriched['feed_available']}")
    bullet(f"titles resolved  : {len(enriched['control_titles'])}")
    bullet(f"findings         : {len(enriched['findings'])}")

    # Degraded path: empty cache.
    empty = tempfile.mkdtemp(prefix="fedramplens_degrade_")
    os.environ["COGNIS_FEEDS_CACHE"] = empty
    controls.reset_cache()
    degraded = _summary("oscal_enrichment")
    print("\nWith an empty cache (no network):")
    bullet(f"feed_available   : {degraded['feed_available']}")
    bullet(f"titles resolved  : {len(degraded['control_titles'])}")
    bullet(f"findings         : {len(degraded['findings'])}")

    rule("CONTRACT CHECK")
    # Same structural analysis both ways.
    same_findings = len(enriched["findings"]) == len(degraded["findings"])
    same_coverage = enriched["coverage_pct"] == degraded["coverage_pct"]
    same_ready = enriched["authorization_ready"] == degraded["authorization_ready"]
    bullet(f"identical finding count : {same_findings}")
    bullet(f"identical coverage      : {same_coverage}")
    bullet(f"identical ready verdict : {same_ready}")
    assert same_findings and same_coverage and same_ready
    bullet("only control_titles + feed_available differ -> contract holds")

    use_offline_feed_cache()
    print("\nEnrichment is purely additive: it never changes the verdict.")


if __name__ == "__main__":
    main()
