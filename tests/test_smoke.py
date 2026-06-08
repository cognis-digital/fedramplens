"""Smoke tests for FEDRAMPLENS. Stdlib only, no network."""
import io
import json
import os
import sys
import unittest
import contextlib

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fedramplens import (  # noqa: E402
    TOOL_NAME,
    TOOL_VERSION,
    load_boundary,
    analyze_boundary,
    generate_dot,
    generate_ssp,
    generate_poam,
)
from fedramplens.core import _build_boundary, BoundaryError  # noqa: E402
from fedramplens.cli import main  # noqa: E402

DEMO = os.path.join(
    os.path.dirname(__file__), "..", "demos", "01-basic", "boundary.json"
)

GOOD = {
    "system_name": "Good System",
    "system_id": "FR0001",
    "impact": "low",
    "components": [
        {"id": "a", "name": "A", "zone": "boundary", "controls": ["AC-2"]},
        {"id": "b", "name": "B", "zone": "internal", "controls": ["SC-7"]},
    ],
    "flows": [
        {"from": "internet", "to": "a", "data": "HTTPS", "encrypted": True},
        {"from": "a", "to": "b", "data": "TLS", "encrypted": True},
    ],
    "poam": [],
}


class TestMeta(unittest.TestCase):
    def test_tool_meta(self):
        self.assertEqual(TOOL_NAME, "fedramplens")
        self.assertTrue(TOOL_VERSION)


class TestCore(unittest.TestCase):
    def test_load_demo(self):
        b = load_boundary(DEMO)
        self.assertEqual(b.impact, "moderate")
        self.assertEqual(len(b.components), 4)

    def test_analyze_flags_unencrypted_crossing(self):
        b = load_boundary(DEMO)
        summary = analyze_boundary(b)
        types = {f["type"] for f in summary["findings"]}
        self.assertIn("unencrypted_boundary_crossing", types)
        self.assertIn("overdue_poam", types)
        self.assertFalse(summary["authorization_ready"])
        self.assertGreater(summary["coverage_pct"], 0)

    def test_clean_boundary_is_ready(self):
        b = _build_boundary(GOOD)
        summary = analyze_boundary(b)
        self.assertTrue(summary["authorization_ready"])
        self.assertEqual(summary["poam_open"], 0)

    def test_invalid_impact_rejected(self):
        bad = dict(GOOD, impact="medium")
        with self.assertRaises(BoundaryError):
            _build_boundary(bad)

    def test_duplicate_component_rejected(self):
        bad = json.loads(json.dumps(GOOD))
        bad["components"].append({"id": "a", "name": "dup"})
        with self.assertRaises(BoundaryError):
            _build_boundary(bad)

    def test_missing_field_rejected(self):
        with self.assertRaises(BoundaryError):
            _build_boundary({"system_name": "x"})

    def test_dot_output(self):
        b = load_boundary(DEMO)
        dot = generate_dot(b)
        self.assertIn("digraph boundary", dot)
        self.assertIn("cluster_boundary", dot)
        self.assertIn("->", dot)

    def test_ssp_structure(self):
        b = load_boundary(DEMO)
        ssp = generate_ssp(b)
        root = ssp["system-security-plan"]
        self.assertEqual(
            root["system-characteristics"]["security-sensitivity-level"],
            "moderate",
        )
        self.assertTrue(
            root["control-implementation"]["implemented-requirements"]
        )

    def test_poam_structure(self):
        b = load_boundary(DEMO)
        poam = generate_poam(b)
        items = poam["plan-of-action-and-milestones"]["poam-items"]
        self.assertEqual(len(items), 2)


class TestCLI(unittest.TestCase):
    def _run(self, argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = main(argv)
        return code, out.getvalue()

    def test_analyze_exit_nonzero_on_findings(self):
        code, out = self._run(["analyze", DEMO])
        self.assertEqual(code, 1)
        self.assertIn("Authorization-ready", out)

    def test_analyze_json(self):
        code, out = self._run(["--format", "json", "analyze", DEMO])
        self.assertEqual(code, 1)
        data = json.loads(out)
        self.assertEqual(data["system_id"], "FR2026ACME01")

    def test_diagram_cli(self):
        code, out = self._run(["diagram", DEMO])
        self.assertEqual(code, 0)
        self.assertIn("digraph", out)

    def test_ssp_cli(self):
        code, out = self._run(["ssp", DEMO])
        self.assertEqual(code, 0)
        self.assertIn("system-security-plan", json.loads(out))

    def test_missing_file_exits_2(self):
        code, _ = self._run(["analyze", "/nonexistent/x.json"])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
