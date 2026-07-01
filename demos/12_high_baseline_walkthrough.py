"""Scenario 12 - high-baseline package walkthrough.

Audience: teams pursuing a FedRAMP High ATO.

High-impact systems are held to the 410-control High baseline. This scenario
takes a high-impact, SIEM-integrated boundary that is authorization-ready,
walks its posture end to end (coverage against the High baseline, boundary
crossings, POA&M, findings), and then emits its OSCAL SSP header so the team
sees the machine-readable package it would submit.
"""
from _common import load, rule, bullet
from fedramplens.core import analyze_boundary, generate_ssp


def main() -> None:
    rule("HIGH BASELINE WALKTHROUGH  -  a ready High-impact package")

    b = load("high_ready")
    s = analyze_boundary(b)

    print(f"\nSystem: {s['system_name']} ({s['system_id']})")
    bullet(f"impact              : {s['impact'].upper()} "
           f"(baseline {s['baseline_controls']} controls)")
    bullet(f"coverage            : {s['coverage_pct']}% "
           f"({s['controls_implemented']} controls)")
    bullet(f"components in bound. : {s['components_in_boundary']}")
    bullet(f"external deps        : {len(s['external_dependencies'])}")
    bullet(f"data flows           : {s['flows']}")
    bullet(f"POA&M open / overdue : {s['poam_open']} / {len(s['poam_overdue'])}")
    bullet(f"authorization-ready  : {s['authorization_ready']}")

    counts = s["finding_counts"]
    rule("FINDINGS")
    if s["findings"]:
        for f in s["findings"]:
            bullet(f"({f['severity']}) {f['type']}: {f['detail']}")
    else:
        bullet("none -- no structural or crossing issues")
    print(f"\n  severity counts: "
          f"{', '.join(f'{k}={v}' for k, v in sorted(counts.items())) or 'none'}")

    rule("OSCAL SSP HEADER (submission artifact)")
    ssp = generate_ssp(b)["system-security-plan"]
    meta = ssp["metadata"]
    bullet(f"title          : {meta['title']}")
    bullet(f"oscal-version  : {meta['oscal-version']}")
    bullet(f"import-profile : {ssp['import-profile']['href']}")
    bullet(f"components      : "
           f"{len(ssp['system-implementation']['components'])}")
    bullet(f"implemented reqs: "
           f"{len(ssp['control-implementation']['implemented-requirements'])}")
    print("\nA ready High package: coverage documented, crossings encrypted.")


if __name__ == "__main__":
    main()
