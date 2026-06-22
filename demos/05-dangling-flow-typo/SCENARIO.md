# Demo 05 - Dangling flow (undefined component reference)

A FedRAMP **Moderate** grants-intake service whose diagram references a
component that was never declared. A flow writes from `worker` to the
DynamoDB table, but no component with id `worker` exists in
`components` — a copy/paste typo (the processor is actually part of the
`intake` service, or the worker tier was renamed and the flow wasn't
updated).

## Where this comes from

The most common authoring mistake in hand-maintained boundary docs:
the data-flow diagram and the component inventory drift out of sync.
`fedramplens` cross-checks every flow endpoint against the declared
components.

## Run it

```sh
python -m fedramplens analyze demos/05-dangling-flow-typo/boundary.json
python -m fedramplens --format sarif analyze demos/05-dangling-flow-typo/boundary.json
```

## Expected

One **dangling_flow** (moderate) finding noting that the
`worker -> dynamo` flow references undefined component `'worker'`.
Because it is only moderate, `Authorization-ready: YES` and **exit 0** —
this is a documentation-quality signal, not an authorization blocker.

## How to act

Either add the missing `worker` component to the inventory (with its
zone and controls) or correct the flow's `from` endpoint to the real
component id. Re-run; the finding disappears.
