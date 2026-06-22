# Demo 07 - FedRAMP High, authorization-ready

A FedRAMP **High** case-management system with a five-component boundary:
WAF/TLS edge, web app, services API, FIPS-validated records database, and
a dedicated audit/SIEM aggregator. Every flow is encrypted (including
syslog-over-TLS to the SIEM), there are no orphans or dangling
references, and the single open POA&M item is **low** severity with a
future due date.

## Where this comes from

A mature High-baseline package right before an annual assessment: the
boundary is clean and the only outstanding item is a routine 3PAO
pen-test sign-off. This is what "ready" looks like at the toughest
impact level.

## Run it

```sh
python -m fedramplens analyze demos/07-high-baseline-ready/boundary.json
python -m fedramplens ssp demos/07-high-baseline-ready/boundary.json > ssp.json
python -m fedramplens --format sarif analyze demos/07-high-baseline-ready/boundary.json
```

## Expected

No findings. `poam_open` = 1 (the low-severity `V-201`), risk score 1,
`Authorization-ready: YES` and **exit 0**. Coverage is computed against
the High baseline (410 controls). The generated OSCAL SSP (`ssp.json`)
imports the `#fedramp-high-baseline` profile.

## How to act

Hold this state. Track the open low item to closure, and keep the SARIF
gate in CI so any boundary change at the High level is caught before it
reaches the AO.
