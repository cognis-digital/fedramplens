# Demo 02 - Clean FedRAMP Low SaaS (authorization-ready)

A minimal FedRAMP **Low** SaaS running entirely inside AWS GovCloud:
an Application Load Balancer at the boundary edge, a Fargate API tier,
and an Aurora PostgreSQL database. Every data flow is encrypted, every
in-boundary component carries data flows, and there are no open POA&M
items.

## Where this comes from

This is the "happy path" you want before an initial assessment: a tight
boundary with TLS everywhere and a documented control set. Use it as the
template a real `boundary.json` should converge toward.

## Run it

```sh
python -m fedramplens analyze demos/02-clean-low-saas/boundary.json
python -m fedramplens --format json  analyze demos/02-clean-low-saas/boundary.json
python -m fedramplens --format sarif analyze demos/02-clean-low-saas/boundary.json
```

## Expected

No findings. `Authorization-ready: YES` and **exit 0**. The SARIF run has
an empty `results` array, so a CI code-scanning gate stays green.

## How to act

Nothing to remediate. Use this as the regression baseline — wire the
`analyze ... --fail-on` style gate into CI so any future drift (a new
unencrypted flow, an orphaned component) flips the exit code.
