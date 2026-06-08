# Demo 01 - Basic FedRAMP Moderate boundary

This scenario models a small FedRAMP **Moderate** SaaS with a classic
three-tier architecture plus a managed database and an external IdP
dependency, and one open POA&M item.

## Input

`boundary.json` describes:

- **Components**: a load balancer / web tier (in the boundary edge),
  an app tier and a managed Postgres DB (internal), and an external
  Okta IdP (outside the authorization boundary).
- **Flows**: internet -> web (HTTPS, encrypted), web -> app (encrypted),
  app -> db (encrypted), and app -> Okta for SSO. One flow is left
  **unencrypted on purpose** so the analyzer flags a boundary crossing.
- **POA&M**: one open high-severity weakness on SC-13 with a past-due
  scheduled date, so the tool flags it as overdue.

## Try it

```sh
# Boundary integrity + control coverage analysis
python -m fedramplens analyze demos/01-basic/boundary.json
python -m fedramplens --format json analyze demos/01-basic/boundary.json

# Authorization boundary diagram (pipe to Graphviz, or paste into draw.io)
python -m fedramplens diagram demos/01-basic/boundary.json | dot -Tpng -o boundary.png

# OSCAL-style SSP and POA&M
python -m fedramplens ssp demos/01-basic/boundary.json
python -m fedramplens poam demos/01-basic/boundary.json
```

## Expected

`analyze` reports an **unencrypted_boundary_crossing** (high) for the
Okta SSO flow and an **overdue_poam** (high), so it prints
`Authorization-ready: NO` and exits **1**. Fix the encryption flag and
the overdue date and it exits **0**.
