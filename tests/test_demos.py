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


if __name__ == "__main__":
    unittest.main()
