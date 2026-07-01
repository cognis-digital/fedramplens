"""Scenario 9 - POA&M tracker: overdue, risk, and closure planning.

Audience: ISSOs running POA&M remediation.

The POA&M is a living backlog. This scenario drives the analyzer over a system
with an overdue backlog and a system with a malformed date, then renders the
POA&M the way an ISSO tracks it: open vs closed, overdue items to escalate,
the weighted risk score, and any data-quality problems (bad dates) that would
bounce a package back from the PMO.
"""
from _common import load, rule, bullet
from fedramplens.core import analyze_boundary, generate_poam


def _report(key):
    b = load(key)
    s = analyze_boundary(b)
    poam = generate_poam(b)["plan-of-action-and-milestones"]
    print(f"\n  {s['system_name']} ({s['system_id']})")
    bullet(f"open items    : {s['poam_open']}")
    bullet(f"overdue       : {', '.join(s['poam_overdue']) or 'none'}")
    bullet(f"risk score    : {s['poam_risk_score']}")
    bad = [f for f in s["findings"] if f["type"] == "bad_poam_date"]
    bullet(f"bad dates     : {len(bad)}")
    for f in bad:
        bullet(f"  -> {f['detail']}")
    print("    OSCAL POA&M items:")
    for it in poam["poam-items"]:
        props = {p["name"]: p["value"] for p in it["props"]}
        print(f"      - {it['title']:7} [{props['severity']:8}/"
              f"{props['status']:10}] due={props['scheduled-completion'] or '-'}")


def main() -> None:
    rule("POA&M TRACKER  -  overdue, risk, and closure planning")
    for key in ("overdue_poam", "bad_poam_date"):
        _report(key)
    rule("ESCALATION")
    bullet("Overdue items go to the AO with a revised milestone date.")
    bullet("Bad-date findings are fixed before the package returns to the PMO.")


if __name__ == "__main__":
    main()
