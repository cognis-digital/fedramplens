"""Tests for SARIF 2.1.0 export and the demo corpus. Stdlib only."""
import glob
import io
import json
import os
import sys
import unittest
import contextlib

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fedramplens import load_boundary, analyze_boundary  # noqa: E402
from fedramplens.core import to_sarif  # noqa: E402
from fedramplens.cli import main  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEMOS = os.path.join(ROOT, "demos")
DEMO = os.path.join(DEMOS, "01-basic", "boundary.json")


def _demo_files():
    return sorted(glob.glob(os.path.join(DEMOS, "*", "boundary.json")))


class TestSarif(unittest.TestCase):
    def test_sarif_envelope(self):
        sarif = to_sarif(analyze_boundary(load_boundary(DEMO)))
        self.assertEqual(sarif["version"], "2.1.0")
        self.assertIn("$schema", sarif)
        self.assertEqual(len(sarif["runs"]), 1)
        driver = sarif["runs"][0]["tool"]["driver"]
        self.assertEqual(driver["name"], "fedramplens")
        self.assertTrue(driver["version"])

    def test_sarif_results_match_findings(self):
        summary = analyze_boundary(load_boundary(DEMO))
        sarif = to_sarif(summary)
        run = sarif["runs"][0]
        self.assertEqual(len(run["results"]), len(summary["findings"]))
        # Every result's ruleId resolves to a declared rule by index.
        rule_ids = [r["id"] for r in run["tool"]["driver"]["rules"]]
        for res in run["results"]:
            self.assertIn(res["ruleId"], rule_ids)
            self.assertEqual(
                run["tool"]["driver"]["rules"][res["ruleIndex"]]["id"],
                res["ruleId"],
            )
            self.assertIn(res["level"], ("error", "warning", "note"))

    def test_sarif_level_mapping(self):
        summary = analyze_boundary(load_boundary(DEMO))
        sarif = to_sarif(summary)
        # The demo has high findings -> they must map to SARIF "error".
        levels = {r["level"] for r in sarif["runs"][0]["results"]}
        self.assertIn("error", levels)

    def test_sarif_preserves_control(self):
        summary = analyze_boundary(load_boundary(DEMO))
        sarif = to_sarif(summary)
        controls = [
            r["properties"].get("nist-control")
            for r in sarif["runs"][0]["results"]
        ]
        self.assertIn("SC-8", controls)

    def test_clean_boundary_has_empty_results(self):
        clean = os.path.join(DEMOS, "02-clean-low-saas", "boundary.json")
        sarif = to_sarif(analyze_boundary(load_boundary(clean)))
        self.assertEqual(sarif["runs"][0]["results"], [])

    def test_cli_sarif_format(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main(["--format", "sarif", "analyze", DEMO])
        self.assertEqual(code, 1)
        data = json.loads(out.getvalue())
        self.assertEqual(data["version"], "2.1.0")
        self.assertTrue(data["runs"][0]["results"])


class TestDemoCorpus(unittest.TestCase):
    def test_demos_present(self):
        # At least the basic + the eight added scenarios.
        self.assertGreaterEqual(len(_demo_files()), 9)

    def test_every_demo_loads_and_analyzes(self):
        for path in _demo_files():
            with self.subTest(demo=os.path.basename(os.path.dirname(path))):
                summary = analyze_boundary(load_boundary(path))
                self.assertIn("authorization_ready", summary)
                # SARIF round-trips for every demo without raising.
                sarif = to_sarif(summary)
                self.assertEqual(sarif["version"], "2.1.0")

    def test_every_demo_has_scenario(self):
        for path in _demo_files():
            scen = os.path.join(os.path.dirname(path), "SCENARIO.md")
            self.assertTrue(os.path.exists(scen), f"missing {scen}")

    def test_expected_finding_types(self):
        # Spot-check that representative demos produce their headline finding.
        cases = {
            "03-boundary-creep": "unencrypted_boundary_crossing",
            "04-overdue-poam-backlog": "overdue_poam",
            "05-dangling-flow-typo": "dangling_flow",
            "06-orphan-component": "orphan_component",
            "08-bad-poam-date": "bad_poam_date",
        }
        for demo, ftype in cases.items():
            path = os.path.join(DEMOS, demo, "boundary.json")
            summary = analyze_boundary(load_boundary(path))
            types = {f["type"] for f in summary["findings"]}
            self.assertIn(ftype, types, f"{demo} should flag {ftype}")


if __name__ == "__main__":
    unittest.main()
