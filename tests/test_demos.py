"""Tests for the runnable demo scenarios + the demo-side Mermaid helper.

Each scenario must import, run its ``main()`` without error, and print
narrated output. They drive the real fedramplens API offline. Stdlib only.
"""
import contextlib
import importlib
import io
import os
import sys
import unittest

_HERE = os.path.dirname(__file__)
_REPO = os.path.abspath(os.path.join(_HERE, ".."))
_DEMOS = os.path.join(_REPO, "demos")
sys.path.insert(0, _REPO)
sys.path.insert(0, _DEMOS)

import _common  # noqa: E402

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


class TestCommon(unittest.TestCase):
    def test_all_fixtures_load(self):
        for key in _common.FIXTURES:
            b = _common.load(key)
            self.assertTrue(b.system_id)
            self.assertTrue(b.components)

    def test_mermaid_has_boundary_subgraph_and_edges(self):
        b = _common.load("boundary_creep")
        m = _common.boundary_to_mermaid(b)
        self.assertIn("flowchart LR", m)
        self.assertIn('subgraph AB["Authorization Boundary"]', m)
        # the unencrypted production flow shows up as a dotted UNENCRYPTED edge
        self.assertIn("UNENCRYPTED", m)
        self.assertIn("-.->", m)
        # an external dependency is rendered outside the subgraph
        self.assertIn("n_warehouse", m)

    def test_mermaid_clean_boundary_has_no_unencrypted(self):
        b = _common.load("clean_low")
        m = _common.boundary_to_mermaid(b)
        self.assertNotIn("UNENCRYPTED", m)

    def test_offline_feed_cache_points_at_fixture(self):
        _common.use_offline_feed_cache()
        self.assertTrue(os.path.isdir(os.environ["COGNIS_FEEDS_CACHE"]))


class TestScenariosRun(unittest.TestCase):
    def _run(self, name):
        mod = importlib.import_module(name)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            mod.main()
        return out.getvalue()

    def test_each_scenario_runs_and_narrates(self):
        for name in SCENARIOS:
            with self.subTest(scenario=name):
                text = self._run(name)
                self.assertGreater(len(text), 200, f"{name} printed too little")

    def test_pm_scenario_reports_readiness(self):
        text = self._run("01_pm_authorization_readiness")
        self.assertIn("AUTHORIZATION READINESS", text)
        self.assertIn("READY", text)
        self.assertIn("BLOCKED", text)

    def test_assessor_scenario_emits_sarif(self):
        text = self._run("02_assessor_sarif_review")
        self.assertIn("2.1.0", text)
        self.assertIn("Round-trips cleanly", text)

    def test_platform_scenario_emits_mermaid(self):
        text = self._run("03_platform_engineer_boundary_map")
        self.assertIn("```mermaid", text)
        self.assertIn("digraph boundary", text)

    def test_isso_scenario_emits_oscal(self):
        text = self._run("04_isso_oscal_packages")
        self.assertIn("System Security Plan", text)
        self.assertIn("POA&M", text)

    def test_enrichment_scenario_resolves_titles_offline(self):
        text = self._run("05_offline_control_enrichment")
        self.assertIn("Transmission Confidentiality and Integrity", text)
        self.assertIn("GRACEFUL DEGRADE", text)

    def test_ao_dashboard_ranks_portfolio(self):
        text = self._run("06_ao_risk_dashboard")
        self.assertIn("AO RISK DASHBOARD", text)
        self.assertIn("SIGNATURE GUIDANCE", text)

    def test_ci_gate_reports_exit_codes(self):
        text = self._run("07_ci_gate_sarif_upload")
        self.assertIn("CI GATE", text)
        self.assertIn("build FAILS", text)
        self.assertIn("SARIF ARTIFACT", text)

    def test_coverage_report_lists_titles(self):
        text = self._run("08_control_coverage_report")
        self.assertIn("CONTROL COVERAGE", text)
        self.assertIn("baseline", text)
        self.assertIn("Account Management", text)

    def test_poam_tracker_shows_overdue(self):
        text = self._run("09_poam_tracker")
        self.assertIn("POA&M TRACKER", text)
        self.assertIn("overdue", text)

    def test_dependency_inventory_lists_external(self):
        text = self._run("10_dependency_inventory")
        self.assertIn("EXTERNAL DEPENDENCY INVENTORY", text)
        self.assertIn("SC-8", text)

    def test_hygiene_lint_pass_fail(self):
        text = self._run("11_boundary_hygiene_lint")
        self.assertIn("BOUNDARY HYGIENE LINT", text)
        self.assertIn("PASS", text)
        self.assertIn("FAIL", text)

    def test_high_baseline_walkthrough(self):
        text = self._run("12_high_baseline_walkthrough")
        self.assertIn("HIGH BASELINE WALKTHROUGH", text)
        self.assertIn("oscal-version", text)

    def test_json_pipeline_contract(self):
        text = self._run("13_json_pipeline_integration")
        self.assertIn("JSON PIPELINE", text)
        self.assertIn("contract holds", text)

    def test_airgap_snapshot_transfer(self):
        text = self._run("14_airgap_snapshot_transfer")
        self.assertIn("AIR-GAP SNAPSHOT", text)
        self.assertIn("Transmission Confidentiality and Integrity", text)

    def test_enrichment_degrade_contract(self):
        text = self._run("15_enrichment_graceful_degrade")
        self.assertIn("ENRICHMENT CONTRACT", text)
        self.assertIn("contract holds", text)

    def test_sarif_rule_catalogue(self):
        text = self._run("16_sarif_rule_catalogue")
        self.assertIn("SARIF RULE CATALOGUE", text)
        self.assertIn("unencrypted_boundary_crossing", text)

    def test_diagram_export_formats(self):
        text = self._run("17_diagram_export_formats")
        self.assertIn("DIAGRAM EXPORT", text)
        self.assertIn("```mermaid", text)
        self.assertIn("digraph boundary", text)

    def test_ssp_deep_inspect(self):
        text = self._run("18_oscal_ssp_deep_inspect")
        self.assertIn("OSCAL SSP DEEP INSPECT", text)
        self.assertIn("INTEGRITY CHECKS", text)

    def test_error_handling_showcase(self):
        text = self._run("19_error_handling_showcase")
        self.assertIn("ERROR HANDLING", text)
        self.assertIn("BoundaryError", text)

    def test_full_package_pipeline(self):
        text = self._run("20_full_package_pipeline")
        self.assertIn("FULL PACKAGE PIPELINE", text)
        self.assertIn("PIPELINE COMPLETE", text)


if __name__ == "__main__":
    unittest.main()
