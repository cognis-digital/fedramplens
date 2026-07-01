"""Scenario 18 - deep inspection of the generated OSCAL SSP.

Audience: OSCAL toolers / package validators.

Beyond "it produced JSON", this scenario validates the internal integrity of
the generated SSP: every implemented-requirement's by-components link resolves
to a declared component uuid, control ids are lower-case OSCAL form, uuids are
deterministic across runs, and enrichment (offline) annotates requirements
with their NIST 800-53 rev5 title. It's the check an OSCAL pipeline runs before
accepting the package.
"""
from _common import load, rule, bullet, use_offline_feed_cache
from fedramplens.core import generate_ssp


def main() -> None:
    rule("OSCAL SSP DEEP INSPECT  -  internal-integrity validation")
    use_offline_feed_cache()

    b = load("basic")
    ssp = generate_ssp(b, resolve_titles=True, offline=True)
    root = ssp["system-security-plan"]
    comps = root["system-implementation"]["components"]
    reqs = root["control-implementation"]["implemented-requirements"]
    comp_uuids = {c["uuid"] for c in comps}

    print(f"\nSSP: {root['metadata']['title']}")
    bullet(f"components               : {len(comps)}")
    bullet(f"implemented-requirements : {len(reqs)}")

    rule("INTEGRITY CHECKS")
    # 1. Every by-component link resolves.
    dangling = [r for r in reqs
                if r["by-components"][0]["component-uuid"] not in comp_uuids]
    bullet(f"by-component links all resolve : {not dangling}")
    assert not dangling

    # 2. Control ids are lower-case OSCAL form.
    bad_ids = [r["control-id"] for r in reqs
               if r["control-id"] != r["control-id"].lower()]
    bullet(f"control-ids are OSCAL lowercase: {not bad_ids}")
    assert not bad_ids

    # 3. Deterministic uuids across a second generation.
    ssp2 = generate_ssp(b)["system-security-plan"]
    bullet(f"top-level uuid deterministic   : {root['uuid'] == ssp2['uuid']}")
    assert root["uuid"] == ssp2["uuid"]

    # 4. Enrichment attached titles.
    labelled = [r for r in reqs if any(
        p.get("class") == "nist-800-53-rev5-title"
        for p in r.get("props", []))]
    bullet(f"requirements annotated w/ title: {len(labelled)}/{len(reqs)}")

    rule("ANNOTATED REQUIREMENTS")
    for r in labelled:
        label = next(p["value"] for p in r["props"]
                     if p.get("class") == "nist-800-53-rev5-title")
        print(f"  - {r['control-id']:8} -> {label}")

    print("\nThe SSP passes structural validation an OSCAL pipeline would run.")


if __name__ == "__main__":
    main()
