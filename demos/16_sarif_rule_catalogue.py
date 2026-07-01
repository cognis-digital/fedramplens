"""Scenario 16 - the SARIF rule catalogue explained.

Audience: security-tooling engineers integrating the SARIF output.

Every finding type fedramplens can emit becomes a SARIF rule with a stable id,
a remediation description, and a default level. This scenario aggregates
findings across the whole demo corpus, then prints the resulting rule
catalogue -- id, PascalCase name, default level, and the fix guidance -- so an
integrator knows exactly what rules their code-scanning dashboard will show.
"""
from _common import load, rule, bullet, FIXTURES
from fedramplens.core import analyze_boundary, to_sarif


def main() -> None:
    rule("SARIF RULE CATALOGUE  -  every finding type as a scanning rule")

    # Merge findings from all fixtures so each rule type appears at least once.
    merged = []
    for key in FIXTURES:
        merged.extend(analyze_boundary(load(key))["findings"])
    sarif = to_sarif({"system_id": "CORPUS", "system_name": "Demo Corpus",
                      "findings": merged})
    rules = sarif["runs"][0]["tool"]["driver"]["rules"]

    print(f"\n{len(rules)} distinct rule(s) across the demo corpus "
          f"({len(merged)} findings total):\n")
    for r in rules:
        lvl = r["defaultConfiguration"]["level"]
        print(f"  - id={r['id']}")
        print(f"      name  : {r['name']}")
        print(f"      level : {lvl}")
        print(f"      fix   : {r['fullDescription']['text']}")

    rule("LEVEL DISTRIBUTION ACROSS RESULTS")
    levels = {}
    for res in sarif["runs"][0]["results"]:
        levels[res["level"]] = levels.get(res["level"], 0) + 1
    for lvl in ("error", "warning", "note"):
        bullet(f"{lvl:8} = {levels.get(lvl, 0)} result(s)")

    print("\nThese are the exact rules your code-scanning dashboard renders.")


if __name__ == "__main__":
    main()
