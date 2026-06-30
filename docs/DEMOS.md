# Demos

Five runnable scenarios live in [`../demos/`](../demos/), each written for a
different audience. Every scenario loads a **bundled** boundary fixture (the
`demos/NN-*/boundary.json` packages) and drives the real `fedramplens` API —
no fabricated data, no network. They print narrated output and exit 0, so they
double as smoke tests (`tests/test_demos.py` covers the same code paths).

```bash
# all five, end to end
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

## Notes

- **`demos/_common.py`** loads the bundled fixtures, points the data-feed cache
  at the trimmed-but-real NIST 800-53 rev5 catalog under
  `tests/fixtures/feedcache` (so scenario 5 runs offline), and renders a
  `Boundary` as a Mermaid flowchart for scenario 3.
- The `demos/NN-*/boundary.json` folders are the input fixtures and carry their
  own `SCENARIO.md` describing the situation each one models.
- Every scenario is independent — run them in any order or on their own.
