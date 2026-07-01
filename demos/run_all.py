"""Run every fedramplens demo scenario end to end.

    python demos/run_all.py

Each scenario loads a bundled boundary fixture and drives the real fedramplens
API offline, so they can be run in any order or on their own. Prints narrated
output and exits 0 — they double as smoke tests.
"""
import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SCENARIOS = [
    "01_pm_authorization_readiness",
    "02_assessor_sarif_review",
    "03_platform_engineer_boundary_map",
    "04_isso_oscal_packages",
    "05_offline_control_enrichment",
    "06_ao_risk_dashboard",
    "07_ci_gate_sarif_upload",
    "08_control_coverage_report",
    "09_poam_tracker",
    "10_dependency_inventory",
    "11_boundary_hygiene_lint",
    "12_high_baseline_walkthrough",
    "13_json_pipeline_integration",
    "14_airgap_snapshot_transfer",
    "15_enrichment_graceful_degrade",
    "16_sarif_rule_catalogue",
    "17_diagram_export_formats",
    "18_oscal_ssp_deep_inspect",
    "19_error_handling_showcase",
    "20_full_package_pipeline",
]


def main() -> None:
    for name in SCENARIOS:
        mod = importlib.import_module(name)
        mod.main()
    print("\n" + "=" * 72)
    print("  All demo scenarios completed.")
    print("=" * 72)


if __name__ == "__main__":
    main()
