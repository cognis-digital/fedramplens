# Demo 03 - Boundary creep (production data leaving the boundary)

A FedRAMP **Moderate** platform that quietly grew a dependency on a
**commercial** (non-GovCloud) Snowflake analytics warehouse. Production
rows flow from the in-boundary customer portal to that external
warehouse **without encryption**, and the warehouse sits outside the
authorization boundary.

## Where this comes from

The classic ConMon finding: an engineering team adds an analytics or
notification integration after the ATO, and production data starts
crossing the boundary edge. `fedramplens` catches the unencrypted
boundary crossing the moment the flow is added to `boundary.json`.

## Run it

```sh
python -m fedramplens analyze demos/03-boundary-creep/boundary.json
python -m fedramplens --format sarif analyze demos/03-boundary-creep/boundary.json
python -m fedramplens diagram demos/03-boundary-creep/boundary.json | dot -Tpng -o creep.png
```

## Expected

One **unencrypted_boundary_crossing** (high) on the
`portal -> warehouse` flow, mapped to **SC-8**. `Authorization-ready: NO`
and **exit 1**. In the diagram the offending edge renders red/bold.

## How to act

Either bring the warehouse inside the boundary (FedRAMP-authorized
service) and encrypt the flow, or treat it as an external interconnection
with an ISA + encrypted transport. Until then, POA&M it and keep CI red.
