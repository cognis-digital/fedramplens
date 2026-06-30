"""Scenario 2 - SARIF export for the assessor's toolchain.

Audience: 3PAOs / independent assessors.

An assessor wants findings in a format their tooling already speaks, with the
NIST control and FedRAMP severity preserved — not a PDF to retype. This
scenario analyzes a boundary that is *not* authorization-ready and renders the
findings as a SARIF 2.1.0 log: the same artifact GitHub code-scanning, Azure
DevOps, and any SARIF viewer ingest. It walks the rule catalogue and result
levels so an assessor can see exactly how FedRAMP severities map to SARIF.
"""
import json

from _common import load, rule, bullet
from fedramplens.core import analyze_boundary, to_sarif


def main() -> None:
    rule("ASSESSOR SARIF REVIEW  -  findings in the assessor's toolchain")

    b = load("boundary_creep")
    summary = analyze_boundary(b)
    sarif = to_sarif(summary)
    run = sarif["runs"][0]
    driver = run["tool"]["driver"]

    print(f"\nSystem under assessment: {summary['system_name']} "
          f"({summary['system_id']})")
    print(f"SARIF schema : {sarif['$schema']}")
    print(f"SARIF version: {sarif['version']}")
    print(f"Tool driver  : {driver['name']} {driver['version']}")

    # Run-level properties give the assessor the package posture at a glance.
    props = run["properties"]
    print("\nRun properties (package posture):")
    bullet(f"impact              = {props['impact']}")
    bullet(f"coverage-pct        = {props['coverage-pct']}")
    bullet(f"poam-risk-score     = {props['poam-risk-score']}")
    bullet(f"authorization-ready = {props['authorization-ready']}")

    print("\nRule catalogue emitted (FedRAMP -> SARIF level):")
    for r in driver["rules"]:
        lvl = r["defaultConfiguration"]["level"]
        print(f"  - {r['id']:32} level={lvl:8} {r['fullDescription']['text']}")

    print(f"\n{len(run['results'])} result(s) an assessor would triage:")
    for res in run["results"]:
        p = res["properties"]
        ctl = p.get("nist-control", "-")
        print(f"  - [{res['level']:7}] {res['ruleId']:32} "
              f"control={ctl:6} fedramp={p['fedramp-severity']}")
        print(f"            {res['message']['text']}")

    # Show that the artifact is real, valid JSON the way a pipeline consumes it.
    blob = json.dumps(sarif)
    print(f"\nSerialized SARIF log is {len(blob)} bytes of valid JSON "
          "ready to upload to code-scanning.")
    assert json.loads(blob)["version"] == "2.1.0"
    print("Round-trips cleanly (json.loads verified).")


if __name__ == "__main__":
    main()
