# Demo 09 - Multiple external interconnections

A FedRAMP **Moderate** benefits-eligibility engine that leans on three
external services: **Login.gov** (IdP), the **SSA verification API**, and
a **Treasury disbursement gateway**. Two interconnections are encrypted;
the ACH disbursement instruction to Treasury is **not**, so it trips a
boundary-crossing finding.

## Where this comes from

Federal line-of-business systems rarely live in isolation — they
interconnect with shared services. This demo exercises the tool's
handling of several `external`-zone components at once and shows that
each crossing flow is independently checked for encryption.

## Run it

```sh
python -m fedramplens analyze demos/09-multi-external-deps/boundary.json
python -m fedramplens --format json analyze demos/09-multi-external-deps/boundary.json | jq '.external_dependencies'
python -m fedramplens diagram demos/09-multi-external-deps/boundary.json | dot -Tpng -o benefits.png
```

## Expected

`external_dependencies` lists `okta` (Login.gov), `ssa`, and `pay`. One
**unencrypted_boundary_crossing** (high) on the `engine -> pay` ACH flow,
mapped to **SC-8**. `Authorization-ready: NO` and **exit 1**. The
encrypted OIDC and SSA flows produce no findings.

## How to act

Encrypt the Treasury disbursement flow (TLS / authenticated channel) and
confirm an Interconnection Security Agreement is on file for each
external dependency (see the open `V-401` ISA-renewal POA&M). Re-run; the
crossing finding clears and the system goes authorization-ready.
