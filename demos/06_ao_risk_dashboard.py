"""Scenario 6 - authorizing-official risk dashboard.

Audience: Authorizing Officials (AOs) / risk executives.

An AO signs the ATO and owns the residual risk. This scenario ranks the
portfolio by POA&M risk score and blocking-finding count, so the AO sees --
at a glance -- where the risk concentrates and which systems need a
conditional ATO or a remediation deadline before signature.
"""
from _common import load, rule, bullet
from fedramplens.core import analyze_boundary

PORTFOLIO = ["clean_low", "basic", "overdue_poam", "high_ready",
             "boundary_creep", "multi_external"]


def main() -> None:
    rule("AO RISK DASHBOARD  -  residual-risk ranking for signature")

    rows = []
    for key in PORTFOLIO:
        s = analyze_boundary(load(key))
        counts = s["finding_counts"]
        blocking = counts.get("high", 0) + counts.get("critical", 0)
        rows.append((s, blocking))

    # Highest risk first: blocking findings, then POA&M risk score.
    rows.sort(key=lambda r: (r[1], r[0]["poam_risk_score"]), reverse=True)

    print("\n  rank  system                         risk  blk  overdue  ready")
    print("  " + "-" * 66)
    for i, (s, blocking) in enumerate(rows, 1):
        print(f"  {i:>4}  {s['system_name'][:28]:28}  "
              f"{s['poam_risk_score']:>4}  {blocking:>3}  "
              f"{len(s['poam_overdue']):>7}  "
              f"{'YES' if s['authorization_ready'] else 'NO':>5}")

    rule("SIGNATURE GUIDANCE")
    ready = [s for s, _ in rows if s["authorization_ready"]]
    blocked = [s for s, _ in rows if not s["authorization_ready"]]
    bullet(f"Clear to sign now      : {len(ready)} system(s)")
    bullet(f"Needs remediation first: {len(blocked)} system(s)")
    top = rows[0][0]
    bullet(f"Highest residual risk  : {top['system_name']} "
           f"(risk score {top['poam_risk_score']})")
    print("\nThe AO uses this to prioritize conditional ATOs and set deadlines.")


if __name__ == "__main__":
    main()
