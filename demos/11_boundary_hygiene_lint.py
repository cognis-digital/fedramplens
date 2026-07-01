"""Scenario 11 - boundary hygiene lint (dangling flows + orphans).

Audience: engineers maintaining the boundary-as-code file.

Before a boundary definition reaches an assessor it should be internally
consistent: no flow should reference a component that doesn't exist, and no
in-boundary component should be stranded with zero data flows. This scenario
runs those structural lints over the typo and orphan fixtures and prints a
tidy pass/fail lint report an engineer fixes in the JSON.
"""
from _common import load, rule, bullet
from fedramplens.core import analyze_boundary

LINTS = {
    "dangling_flow": "flow references an undefined component",
    "orphan_component": "in-boundary component has no data flows",
    "bad_poam_date": "POA&M scheduled date is not ISO-8601",
}


def _lint(key):
    s = analyze_boundary(load(key))
    hits = {}
    for f in s["findings"]:
        if f["type"] in LINTS:
            hits.setdefault(f["type"], []).append(f["detail"])
    return s, hits


def main() -> None:
    rule("BOUNDARY HYGIENE LINT  -  structural consistency checks")

    for key in ("dangling_flow", "orphan", "clean_low"):
        s, hits = _lint(key)
        status = "FAIL" if hits else "PASS"
        print(f"\n  [{status}] {s['system_name']} ({s['system_id']})")
        if not hits:
            bullet("clean -- no structural issues")
        for lint, details in hits.items():
            bullet(f"{lint}: {LINTS[lint]} ({len(details)} hit(s))")
            for d in details:
                print(f"        - {d}")

    rule("LINT RULES CHECKED")
    for lint, desc in LINTS.items():
        bullet(f"{lint:22} {desc}")
    print("\nRun this as a pre-commit hook on the boundary-as-code file.")


if __name__ == "__main__":
    main()
