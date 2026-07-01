# Demos

Twenty runnable scenarios live in [`../demos/`](../demos/), each written for a
different audience. Every scenario loads a **bundled** boundary fixture (the
`demos/NN-*/boundary.json` packages) and drives the real `fedramplens` API —
no fabricated data, no network. They print narrated output and exit 0, so they
double as smoke tests (`tests/test_demos.py` covers the same code paths).

```bash
# all twenty, end to end
PYTHONUTF8=1 python demos/run_all.py

# or just one
PYTHONUTF8=1 python demos/01_pm_authorization_readiness.py
```

> Set `PYTHONUTF8=1` so the narrated output prints cleanly on every platform.

## Audience table

| # | Scenario | Audience | What it shows | Real API used |
| --- | --- | --- | --- | --- |
| 1 | [`01_pm_authorization_readiness.py`](../demos/01_pm_authorization_readiness.py) | FedRAMP / Agency **Program Managers** | Portfolio ATO-readiness gate: per-system verdict, coverage, POA&M roll-up, escalation list | `analyze_boundary` |
| 2 | [`02_assessor_sarif_review.py`](../demos/02_assessor_sarif_review.py) | **3PAOs / assessors** | Findings as a SARIF 2.1.0 log for code-scanning, with FedRAMP→SARIF level mapping and NIST control preserved | `analyze_boundary`, `to_sarif` |
| 3 | [`03_platform_engineer_boundary_map.py`](../demos/03_platform_engineer_boundary_map.py) | **Cloud platform engineers** | Boundary map as Mermaid + Graphviz DOT; external dependencies and unencrypted boundary crossings (SC-8) to fix | `analyze_boundary`, `generate_dot` |
| 4 | [`04_isso_oscal_packages.py`](../demos/04_isso_oscal_packages.py) | **ISSOs / package authors** | Generate the OSCAL SSP + POA&M, inspect metadata, component inventory, implemented-requirements, POA&M items | `generate_ssp`, `generate_poam` |
| 5 | [`05_offline_control_enrichment.py`](../demos/05_offline_control_enrichment.py) | **ISSOs / assessors in an air-gap** | Resolve official NIST 800-53 rev5 control titles from the bundled OSCAL cache `offline=True`; graceful degrade on empty cache | `analyze_boundary`, `generate_ssp`, `controls.control_title` |
| 6 | [`06_ao_risk_dashboard.py`](../demos/06_ao_risk_dashboard.py) | **Authorizing Officials / risk executives** | Portfolio ranked by POA&M risk score and blocking-finding count; signature guidance for conditional ATOs | `analyze_boundary` |
| 7 | [`07_ci_gate_sarif_upload.py`](../demos/07_ci_gate_sarif_upload.py) | **DevSecOps / CI owners** | CI gate that fails the build on blocking findings and ships the SARIF artifact to code-scanning | `analyze_boundary`, `to_sarif` |
| 8 | [`08_control_coverage_report.py`](../demos/08_control_coverage_report.py) | **Control owners / compliance analysts** | Implemented-vs-baseline coverage, distinct controls with NIST titles, coverage across low/moderate/high baselines | `analyze_boundary`, `controls.control_title` |
| 9 | [`09_poam_tracker.py`](../demos/09_poam_tracker.py) | **ISSOs running remediation** | POA&M as a living backlog: open/closed, overdue, weighted risk, and bad-date data-quality findings | `analyze_boundary`, `generate_poam` |
| 10 | [`10_dependency_inventory.py`](../demos/10_dependency_inventory.py) | **ISSOs / architects** | External-dependency + interconnection inventory and which crossings are encrypted (SC-8) | `analyze_boundary` |
| 11 | [`11_boundary_hygiene_lint.py`](../demos/11_boundary_hygiene_lint.py) | **Engineers maintaining boundary-as-code** | Structural lint (dangling flows, orphan components, bad dates) as a pre-commit pass/fail report | `analyze_boundary` |
| 12 | [`12_high_baseline_walkthrough.py`](../demos/12_high_baseline_walkthrough.py) | **Teams pursuing FedRAMP High** | End-to-end posture of a ready High-impact package against the 410-control baseline + OSCAL SSP header | `analyze_boundary`, `generate_ssp` |
| 13 | [`13_json_pipeline_integration.py`](../demos/13_json_pipeline_integration.py) | **Tooling / integration engineers** | Consume `--format json` downstream: read posture keys, filter findings by severity, verify the exit-code contract | `cli.main` (`--format json`) |
| 14 | [`14_airgap_snapshot_transfer.py`](../demos/14_airgap_snapshot_transfer.py) | **Disconnected / classified enclaves** | Sneakernet the OSCAL catalog: export a tarball, import into a fresh empty cache, resolve titles offline | `datafeeds.snapshot_export/import`, `controls.control_title` |
| 15 | [`15_enrichment_graceful_degrade.py`](../demos/15_enrichment_graceful_degrade.py) | **Integrators using enrichment** | Same boundary enriched vs empty-cache: proves the analysis verdict is identical, only titles differ | `analyze_boundary` |
| 16 | [`16_sarif_rule_catalogue.py`](../demos/16_sarif_rule_catalogue.py) | **Security-tooling engineers** | Aggregate findings across the corpus and print the full SARIF rule catalogue (id, level, fix guidance) | `analyze_boundary`, `to_sarif` |
| 17 | [`17_diagram_export_formats.py`](../demos/17_diagram_export_formats.py) | **Architects producing SSP diagrams** | The same boundary as Graphviz DOT and Mermaid, highlighting encrypted vs unencrypted crossings | `generate_dot`, `boundary_to_mermaid` |
| 18 | [`18_oscal_ssp_deep_inspect.py`](../demos/18_oscal_ssp_deep_inspect.py) | **OSCAL toolers / validators** | Internal-integrity validation of the SSP: resolving links, lowercase control ids, deterministic uuids, title props | `generate_ssp` |
| 19 | [`19_error_handling_showcase.py`](../demos/19_error_handling_showcase.py) | **Anyone feeding untrusted files** | Malformed boundaries fail with precise `BoundaryError`s instead of tracebacks, incl. late validation | `load_boundary`, `analyze_boundary` |
| 20 | [`20_full_package_pipeline.py`](../demos/20_full_package_pipeline.py) | **Package leads** | Capstone: one boundary through analyze → SARIF → diagram → SSP → POA&M, enriched and offline | all of the above |

## Notes

- **`demos/_common.py`** loads the bundled fixtures, points the data-feed cache
  at the trimmed-but-real NIST 800-53 rev5 catalog under
  `tests/fixtures/feedcache` (so scenario 5 runs offline), and renders a
  `Boundary` as a Mermaid flowchart for scenario 3.
- The `demos/NN-*/boundary.json` folders are the input fixtures and carry their
  own `SCENARIO.md` describing the situation each one models.
- Every scenario is independent — run them in any order or on their own.
