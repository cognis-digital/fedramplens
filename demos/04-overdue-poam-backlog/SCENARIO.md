# Demo 04 - Overdue POA&M backlog (FedRAMP High)

A FedRAMP **High** system whose boundary is sound (all flows encrypted,
no orphans) but whose **POA&M backlog has slipped**. Three open items are
past their scheduled completion dates, including a **critical** MFA gap
on break-glass admin accounts. One item is already `completed` and is
correctly excluded from the open count and risk roll-up.

## Where this comes from

A snapshot mid-cycle when remediation fell behind the milestone plan —
exactly what an AO or 3PAO scrutinizes during continuous monitoring. The
dates here are deliberately in the past relative to a mid-2026 review.

## Run it

```sh
python -m fedramplens analyze demos/04-overdue-poam-backlog/boundary.json
python -m fedramplens --format json  analyze demos/04-overdue-poam-backlog/boundary.json | jq '.poam_overdue, .poam_risk_score'
python -m fedramplens poam demos/04-overdue-poam-backlog/boundary.json > poam.json
```

## Expected

Three **overdue_poam** (high) findings for `V-101`, `V-102`, `V-103`.
`poam_open` = 4, `poam_overdue` lists those three, and the risk score
reflects the open severities (critical=8, high=4, moderate=2).
`Authorization-ready: NO` and **exit 1**. The completed `V-099` does not
appear.

## How to act

Triage by severity: close `V-101` (critical MFA) first, then re-baseline
the scan cadence (`V-102`) and image hardening (`V-103`) or re-negotiate
the milestone dates with the AO. The generated OSCAL POA&M (`poam.json`)
is ready to attach to the package.
