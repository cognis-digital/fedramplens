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
