"""Scenario 4 - generate the OSCAL SSP + POA&M package.

Audience: ISSOs / package authors.

An ISSO has to produce the System Security Plan and the Plan of Action &
Milestones in OSCAL — the machine-readable format FedRAMP is standardizing on.
This scenario takes a bundled boundary and emits both real OSCAL artifacts via
the public API, then inspects their structure: SSP metadata + OSCAL version,
component inventory, implemented-requirements, and the POA&M item roll-up the
ISSO tracks to closure.
"""
from _common import load, rule, bullet
from fedramplens.core import generate_ssp, generate_poam


def main() -> None:
    rule("OSCAL PACKAGE  -  SSP + POA&M for an ISSO")

    b = load("overdue_poam")
    ssp = generate_ssp(b)
    poam = generate_poam(b)

    root = ssp["system-security-plan"]
    meta = root["metadata"]
    sc = root["system-characteristics"]
    comps = root["system-implementation"]["components"]
    reqs = root["control-implementation"]["implemented-requirements"]

    print(f"\nSystem Security Plan: {meta['title']}")
    bullet(f"OSCAL version   : {meta['oscal-version']}")
    bullet(f"SSP version     : {meta['version']}")
    bullet(f"system id       : {sc['system-ids'][0]['id']}")
    bullet(f"sensitivity     : {sc['security-sensitivity-level']}")
    bullet(f"import-profile  : {root['import-profile']['href']}")
    bullet(f"components       : {len(comps)}")
    bullet(f"implemented reqs : {len(reqs)} control implementations")

    print("\n  Component inventory (uuid is deterministic for stable diffs):")
    for c in comps:
        zone = next((p["value"] for p in c["props"] if p["name"] == "zone"), "?")
        print(f"    - {c['title']:32} type={c['type']:9} zone={zone:9} "
              f"{c['uuid']}")

    # Show a couple of implemented-requirements as the AO/3PAO would read them.
    print("\n  Sample implemented-requirements:")
    for r in reqs[:4]:
        by = r["by-components"][0]["description"]
        print(f"    - control {r['control-id']:8} : {by}")

    rule("OSCAL POA&M  -  open items the ISSO tracks to closure")
    proot = poam["plan-of-action-and-milestones"]
    items = proot["poam-items"]
    print(f"\n{proot['metadata']['title']}  "
          f"(OSCAL {proot['metadata']['oscal-version']}, "
          f"system {proot['system-id']['id']})")
    print(f"{len(items)} POA&M item(s):")
    for it in items:
        props = {p["name"]: p["value"] for p in it["props"]}
        print(f"  - {it['title']:7} [{props['severity']:8} / {props['status']:9}] "
              f"control={props['control'] or '-':6} "
              f"due={props['scheduled-completion'] or '-'}")
        print(f"            {it['description']}")

    print("\nBoth artifacts are valid OSCAL-shaped JSON the ISSO drops straight")
    print("into a FedRAMP package — no manual reformatting.")


if __name__ == "__main__":
    main()
