"""Scenario 20 - end-to-end package pipeline for one system.

Audience: package leads running the whole flow.

This capstone runs a single boundary through every stage of the fedramplens
pipeline in order: analyze -> SARIF -> boundary diagram -> OSCAL SSP -> OSCAL
POA&M, with offline control-title enrichment throughout. It's the full journey
from a boundary-as-code file to a submission-ready, machine-readable package,
narrated stage by stage.
"""
from _common import load, rule, bullet, use_offline_feed_cache
from fedramplens.core import (
    analyze_boundary, generate_dot, generate_poam, generate_ssp, to_sarif,
)


def main() -> None:
    rule("FULL PACKAGE PIPELINE  -  boundary-as-code to OSCAL package")
    use_offline_feed_cache()

    b = load("basic")
    print(f"\nInput: {b.system_name} ({b.system_id}), {b.impact.upper()} impact\n")

    rule("STAGE 1  -  analyze (enriched, offline)")
    s = analyze_boundary(b, resolve_titles=True, offline=True)
    bullet(f"coverage            : {s['coverage_pct']}% of baseline")
    bullet(f"findings            : {len(s['findings'])}")
    bullet(f"control titles       : {len(s['control_titles'])} resolved")
    bullet(f"authorization-ready  : {s['authorization_ready']}")

    rule("STAGE 2  -  SARIF export")
    sarif = to_sarif(s)
    bullet(f"schema  : {sarif['version']}")
    bullet(f"rules   : {len(sarif['runs'][0]['tool']['driver']['rules'])}")
    bullet(f"results : {len(sarif['runs'][0]['results'])}")

    rule("STAGE 3  -  boundary diagram (DOT)")
    dot = generate_dot(b)
    bullet(f"DOT lines: {len(dot.splitlines())}")
    bullet(f"boundary cluster present: {'cluster_boundary' in dot}")

    rule("STAGE 4  -  OSCAL SSP")
    ssp = generate_ssp(b, resolve_titles=True, offline=True)["system-security-plan"]
    bullet(f"oscal-version : {ssp['metadata']['oscal-version']}")
    bullet(f"components     : "
           f"{len(ssp['system-implementation']['components'])}")
    bullet(f"implemented req: "
           f"{len(ssp['control-implementation']['implemented-requirements'])}")

    rule("STAGE 5  -  OSCAL POA&M")
    poam = generate_poam(b)["plan-of-action-and-milestones"]
    bullet(f"oscal-version : {poam['metadata']['oscal-version']}")
    bullet(f"poam-items     : {len(poam['poam-items'])}")

    rule("PIPELINE COMPLETE")
    bullet("analyze -> SARIF -> diagram -> SSP -> POA&M, all offline")
    print("\nOne boundary file produced the full machine-readable package.")


if __name__ == "__main__":
    main()
