"""Scenario 5 - resolve NIST 800-53 titles offline (air-gap).

Audience: ISSOs / assessors working in a disconnected enclave.

Findings and SSPs carry control ids like SC-8 — opaque on their own. This
scenario enriches an analysis with the *official* NIST SP 800-53 rev5 control
titles, served entirely from the bundled OSCAL catalog cache with
``offline=True`` (no network). It also shows the graceful-degrade contract: the
same call against an empty cache keeps the analysis working with ids unchanged.
"""
import os
import tempfile

from _common import load, rule, bullet, use_offline_feed_cache
from fedramplens import controls
from fedramplens.core import analyze_boundary, generate_ssp


def main() -> None:
    rule("OFFLINE OSCAL ENRICHMENT  -  real NIST 800-53 rev5 titles, air-gapped")

    use_offline_feed_cache()  # point the feed layer at the bundled cache
    b = load("oscal_enrichment")

    # Enriched analysis: control ids gain their authoritative titles, offline.
    s = analyze_boundary(b, resolve_titles=True, offline=True)
    print(f"\nSystem: {s['system_name']} ({s['system_id']})")
    print(f"Feed available (served from cache, offline): {s['feed_available']}")

    print("\nResolved control titles (NIST SP 800-53 rev5 OSCAL catalog):")
    for cid, title in sorted(s["control_titles"].items()):
        bullet(f"{cid.upper():8} {title}")

    print("\nFindings now carry the control's real name:")
    for f in s["findings"]:
        if f.get("control"):
            t = f.get("control_title", "(unresolved)")
            bullet(f"({f['severity']}) {f['type']} [{f['control']}: {t}]")

    # Same enrichment flows into the OSCAL SSP as labelled props.
    ssp = generate_ssp(b, resolve_titles=True, offline=True)
    reqs = ssp["system-security-plan"]["control-implementation"][
        "implemented-requirements"]
    labelled = [r for r in reqs if any(
        p.get("class") == "nist-800-53-rev5-title"
        for p in r.get("props", []))]
    print(f"\nSSP implemented-requirements annotated with 800-53 titles: "
          f"{len(labelled)}/{len(reqs)}")
    for r in labelled[:3]:
        label = next(p["value"] for p in r["props"]
                     if p.get("class") == "nist-800-53-rev5-title")
        bullet(f"{r['control-id']:8} -> {label}")

    # Direct title lookup + the documented enhancement fallback (AC-2(1) -> AC-2).
    rule("DIRECT LOOKUP + ENHANCEMENT FALLBACK")
    for cid in ("SC-8", "AC-2", "AC-2(1)"):
        print(f"  control_title({cid!r}, offline=True) = "
              f"{controls.control_title(cid, offline=True)!r}")

    # Graceful degrade: empty cache + offline -> titles unresolved, no crash.
    rule("GRACEFUL DEGRADE  -  empty cache, still works")
    empty = tempfile.mkdtemp(prefix="fedramplens_empty_")
    os.environ["COGNIS_FEEDS_CACHE"] = empty
    controls.reset_cache()
    s2 = analyze_boundary(b, resolve_titles=True, offline=True)
    print(f"\n  feed_available with empty cache: {s2['feed_available']}")
    print(f"  control_titles resolved        : {len(s2['control_titles'])}")
    print("  analysis still completed — ids kept as-is, nothing hard-failed.")

    # Restore the working cache for any later demo in the same process.
    use_offline_feed_cache()


if __name__ == "__main__":
    main()
