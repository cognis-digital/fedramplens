# Demo 10 — NIST 800-53 control-title enrichment (edge / air-gap)

FEDRAMPLENS emits NIST SP 800-53 control ids (AC-2, SC-8, SC-13, ...) in its
findings and OSCAL output. This demo shows the **data-feed layer** resolving
those ids to their *official* control titles, fully offline.

The titles come from the authoritative **NIST SP 800-53 rev5 OSCAL catalog**
(`oscal-800-53-rev5-catalog` feed → <https://github.com/usnistgov/oscal-content>),
fetched once, cached to disk, and re-served `--offline` so the tool keeps working
on a disconnected enclave.

## Run it

```bash
# 1. (connected, once) pull + cache the real catalog:
fedramplens feeds update oscal-800-53-rev5-catalog

# 2. (anywhere, offline) analyze with control titles resolved from cache:
fedramplens analyze demos/10-oscal-enrichment/boundary.json --enrich --offline
```

Without `--enrich` you get bare ids:

```
- (high) unencrypted_boundary_crossing [SC-8]: flow internet->web (HTTP) ...
```

With `--enrich --offline` the finding self-describes:

```
- (high) unencrypted_boundary_crossing [SC-8: Transmission Confidentiality and Integrity]: ...
Control titles resolved from NIST OSCAL 800-53 rev5:
  AC-2       Account Management
  SC-7       Boundary Protection
  SC-8       Transmission Confidentiality and Integrity
  SC-13      Cryptographic Protection
```

`fedramplens ssp --enrich --offline ...` likewise annotates every
implemented-requirement with a `nist-800-53-rev5-title` prop.

## Air-gap workflow

```bash
# on a connected jump box:
fedramplens feeds update oscal-800-53-rev5-catalog
python -m fedramplens.datafeeds snapshot-export oscal-feeds.tar.gz

# sneakernet oscal-feeds.tar.gz into the enclave, then:
python -m fedramplens.datafeeds snapshot-import oscal-feeds.tar.gz
fedramplens analyze boundary.json --enrich --offline
```
