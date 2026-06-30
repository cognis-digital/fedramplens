"""Scenario 1 - authorization-readiness gate across a portfolio.

Audience: FedRAMP / Agency Program Managers.

A PM does not read OSCAL by hand. The question is portfolio-level: across the
systems I own, which packages are authorization-ready, and which have
high/critical findings or overdue POA&M milestones that block an ATO? This
scenario runs the *real* analyzer over several bundled boundaries and prints a
one-line readiness verdict per system, then a roll-up — the same data a PM
would put in front of an AO.
"""
from _common import load, rule, bullet
from fedramplens.core import analyze_boundary


PORTFOLIO = [
    ("clean_low", "low-impact SaaS, fresh package"),
    ("basic", "moderate three-tier, one SSO gap"),
    ("overdue_poam", "high-impact exchange, POA&M backlog"),
    ("high_ready", "high-impact case mgmt, SIEM-integrated"),
]


def main() -> None:
    rule("AUTHORIZATION READINESS  -  portfolio view for a Program Manager")
    print("\nRunning the boundary analyzer over each system in the portfolio.\n")

    ready, blocked = [], []
    rows = []
    for key, note in PORTFOLIO:
        b = load(key)
        s = analyze_boundary(b)
        verdict = "READY" if s["authorization_ready"] else "BLOCKED"
        (ready if s["authorization_ready"] else blocked).append(s["system_id"])
        rows.append((s, verdict, note))
        counts = s["finding_counts"]
        hi = counts.get("high", 0) + counts.get("critical", 0)
        print(f"  [{verdict:7}] {s['system_name']} ({s['system_id']})")
        print(f"            impact={s['impact'].upper():8} "
              f"coverage={s['coverage_pct']}% of {s['impact']} baseline  "
              f"({s['controls_implemented']}/{s['baseline_controls']} controls)")
        print(f"            POA&M: {s['poam_open']} open, "
              f"{len(s['poam_overdue'])} overdue, risk={s['poam_risk_score']}  |  "
              f"blocking findings (high+critical)={hi}")
        print(f"            note: {note}")

    rule("ATO GATE ROLL-UP")
    print(f"\n  {len(PORTFOLIO)} systems analyzed.")
    bullet(f"Authorization-ready now : {', '.join(ready) or 'none'}")
    bullet(f"Blocked (needs action)  : {', '.join(blocked) or 'none'}")

    # The exact items a PM escalates to the AO / system owner.
    print("\n  Top blockers to escalate:")
    any_blocker = False
    for s, verdict, _ in rows:
        if verdict == "BLOCKED":
            for f in s["findings"]:
                if f["severity"] in ("high", "critical"):
                    any_blocker = True
                    ctl = f" [{f['control']}]" if f.get("control") else ""
                    bullet(f"{s['system_id']}: ({f['severity']}) "
                           f"{f['type']}{ctl} - {f['detail']}")
    if not any_blocker:
        bullet("none — every system is authorization-ready")

    print("\nThis is the readiness snapshot a PM takes into an ATO review,")
    print("derived entirely from the boundary definitions the teams maintain.")


if __name__ == "__main__":
    main()
