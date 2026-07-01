"""Scenario 8 - control-coverage report vs the FedRAMP baseline.

Audience: control owners / compliance analysts.

Coverage against the applicable baseline is the headline metric in a readiness
review. This scenario reports implemented-vs-baseline counts per impact level,
lists the distinct controls a system implements with their official NIST
800-53 rev5 titles (resolved offline), and shows how coverage differs across
low/moderate/high baselines for the same control set.
"""
from _common import load, rule, bullet, use_offline_feed_cache
from fedramplens.core import analyze_boundary, BASELINE_CONTROL_COUNTS
from fedramplens import controls


def main() -> None:
    rule("CONTROL COVERAGE  -  implemented vs FedRAMP baseline")
    use_offline_feed_cache()

    b = load("basic")
    s = analyze_boundary(b, resolve_titles=True, offline=True)
    print(f"\nSystem: {s['system_name']} ({s['system_id']}), "
          f"{s['impact'].upper()} impact")
    bullet(f"controls implemented : {s['controls_implemented']}")
    bullet(f"baseline controls    : {s['baseline_controls']}")
    bullet(f"coverage             : {s['coverage_pct']}% of baseline")

    # Distinct implemented controls with their real titles.
    implemented = sorted({c for comp in b.components
                          for c in comp.get("controls", [])})
    rule("IMPLEMENTED CONTROLS (with NIST 800-53 rev5 titles)")
    for cid in implemented:
        title = controls.control_title(cid, offline=True) or "(title unresolved)"
        bullet(f"{cid:8} {title}")

    # Same control set, different baselines -> different coverage.
    rule("COVERAGE ACROSS BASELINES (same implemented set)")
    n = s["controls_implemented"]
    for impact, total in BASELINE_CONTROL_COUNTS.items():
        pct = round(100.0 * n / total, 1)
        bullet(f"{impact:9} baseline = {total:3} controls -> {pct}% covered")

    print("\nThis is the coverage snapshot a control owner brings to a gap review.")


if __name__ == "__main__":
    main()
