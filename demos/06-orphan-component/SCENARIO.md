# Demo 06 - Orphan component (no data flows)

A FedRAMP **Low** telemetry collector with three in-boundary components,
but the **Scheduled Report Generator** (`reporter`) has no data flows
touching it. Either the flow that feeds it (reading from the time-series
DB) was never documented, or the component is dead weight that shouldn't
be in the boundary at all.

## Where this comes from

When a boundary is built component-first, it's easy to declare an asset
and forget to wire its data flows. An orphaned in-boundary component is
both a documentation gap and a hint of unmonitored attack surface.

## Run it

```sh
python -m fedramplens analyze demos/06-orphan-component/boundary.json
python -m fedramplens diagram demos/06-orphan-component/boundary.json
```

## Expected

One **orphan_component** (low) finding for `reporter`.
`Authorization-ready: YES` and **exit 0** (low severity). In the diagram,
`reporter` appears in the boundary cluster with no edges connected to it.

## How to act

If the report generator really reads from `tsdb`, add that flow (it will
also be checked for encryption). If it's no longer used, remove it from
the boundary to shrink scope.
