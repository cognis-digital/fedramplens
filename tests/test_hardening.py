"""Hardening tests: edge-cases, bad input, and error paths."""
from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import unittest
import contextlib

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fedramplens.core import (  # noqa: E402
    _build_boundary,
    load_boundary,
    BoundaryError,
    analyze_boundary,
)
from fedramplens.cli import main  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_json(tmp_dir: str, data: object, name: str = "b.json") -> str:
    path = os.path.join(tmp_dir, name)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh)
    return path


GOOD = {
    "system_name": "Test System",
    "system_id": "FR-TEST-01",
    "impact": "low",
    "components": [
        {"id": "web", "name": "Web", "zone": "boundary", "controls": ["AC-2"]},
    ],
    "flows": [
        {"from": "internet", "to": "web", "data": "HTTPS", "encrypted": True},
    ],
    "poam": [],
}


class TestBuildBoundaryEdgeCases(unittest.TestCase):
    """Validate that _build_boundary rejects bad inputs with BoundaryError."""

    def test_non_dict_rejected(self):
        with self.assertRaises(BoundaryError):
            _build_boundary([])

    def test_whitespace_only_system_name_rejected(self):
        bad = dict(GOOD, system_name="   ")
        with self.assertRaises(BoundaryError):
            _build_boundary(bad)

    def test_whitespace_only_system_id_rejected(self):
        bad = dict(GOOD, system_id="\t")
        with self.assertRaises(BoundaryError):
            _build_boundary(bad)

    def test_empty_components_list_rejected(self):
        bad = dict(GOOD, components=[])
        with self.assertRaises(BoundaryError):
            _build_boundary(bad)

    def test_component_not_a_dict_rejected(self):
        bad = dict(GOOD, components=["not-a-dict"])
        with self.assertRaises(BoundaryError):
            _build_boundary(bad)

    def test_flow_not_a_dict_rejected(self):
        bad = dict(GOOD, flows=["not-a-dict"])
        with self.assertRaises(BoundaryError):
            _build_boundary(bad)

    def test_poam_not_a_dict_rejected(self):
        bad = dict(GOOD, poam=["not-a-dict"])
        with self.assertRaises(BoundaryError):
            _build_boundary(bad)

    def test_invalid_zone_rejected(self):
        bad = json.loads(json.dumps(GOOD))
        bad["components"][0]["zone"] = "dmz"
        with self.assertRaises(BoundaryError):
            _build_boundary(bad)

    def test_flow_missing_from_rejected(self):
        bad = dict(GOOD, flows=[{"to": "web", "data": "X"}])
        with self.assertRaises(BoundaryError):
            _build_boundary(bad)

    def test_poam_invalid_severity_rejected(self):
        bad = dict(GOOD, poam=[{
            "id": "V-001", "weakness": "x", "control": "AC-1",
            "severity": "catastrophic", "status": "open",
        }])
        with self.assertRaises(BoundaryError):
            _build_boundary(bad)


class TestAnalyzeBoundaryEdgeCases(unittest.TestCase):
    """Validate analyze_boundary handles unusual but valid inputs."""

    def test_no_controls_gives_zero_coverage(self):
        raw = dict(GOOD)
        raw["components"] = [{"id": "web", "name": "Web", "zone": "boundary"}]
        b = _build_boundary(raw)
        summary = analyze_boundary(b)
        self.assertEqual(summary["controls_implemented"], 0)
        self.assertEqual(summary["coverage_pct"], 0.0)

    def test_orphan_component_flagged(self):
        raw = json.loads(json.dumps(GOOD))
        raw["components"].append({"id": "orphan", "name": "Orphan", "zone": "internal"})
        b = _build_boundary(raw)
        summary = analyze_boundary(b)
        types = {f["type"] for f in summary["findings"]}
        self.assertIn("orphan_component", types)

    def test_empty_poam_list_is_fine(self):
        b = _build_boundary(GOOD)
        summary = analyze_boundary(b)
        self.assertEqual(summary["poam_open"], 0)
        self.assertEqual(summary["poam_risk_score"], 0)

    def test_bad_poam_date_flagged(self):
        raw = dict(GOOD, poam=[{
            "id": "V-99", "weakness": "test", "control": "AC-1",
            "severity": "low", "status": "open",
            "scheduled": "not-a-date",
        }])
        b = _build_boundary(raw)
        summary = analyze_boundary(b)
        types = {f["type"] for f in summary["findings"]}
        self.assertIn("bad_poam_date", types)


class TestLoadBoundaryFileErrors(unittest.TestCase):
    """load_boundary raises BoundaryError for OS-level and encoding errors."""

    def test_missing_file_raises_boundary_error(self):
        with self.assertRaises((BoundaryError, FileNotFoundError)):
            load_boundary("/nonexistent/path/boundary.json")

    def test_malformed_json_raises_json_decode_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "bad.json")
            with open(path, "w") as fh:
                fh.write("{not valid json}")
            with self.assertRaises(json.JSONDecodeError):
                load_boundary(path)


class TestCLIHardening(unittest.TestCase):
    """CLI returns exit code 2 for all bad-input scenarios."""

    def _run(self, argv):
        out = io.StringIO()
        err = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_missing_file_exits_2(self):
        code, _, err = self._run(["analyze", "/no/such/file.json"])
        self.assertEqual(code, 2)
        self.assertIn("error", err.lower())

    def test_malformed_json_exits_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "bad.json")
            with open(path, "w") as fh:
                fh.write("{broken")
            code, _, err = self._run(["analyze", path])
        self.assertEqual(code, 2)
        self.assertIn("error", err.lower())

    def test_invalid_boundary_exits_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_json(tmp, {"system_name": "x"})
            code, _, err = self._run(["analyze", path])
        self.assertEqual(code, 2)
        self.assertIn("error", err.lower())

    def test_invalid_impact_exits_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = dict(GOOD, impact="ultra")
            path = _write_json(tmp, bad)
            code, _, err = self._run(["analyze", path])
        self.assertEqual(code, 2)
        self.assertIn("error", err.lower())

    def test_clean_boundary_analyze_exits_0(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_json(tmp, GOOD)
            code, out, _ = self._run(["analyze", path])
        self.assertEqual(code, 0)
        self.assertIn("Authorization-ready", out)

    def test_diagram_bad_file_exits_2(self):
        code, _, err = self._run(["diagram", "/no/such/file.json"])
        self.assertEqual(code, 2)
        self.assertIn("error", err.lower())

    def test_ssp_valid_boundary(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_json(tmp, GOOD)
            code, out, _ = self._run(["ssp", path])
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertIn("system-security-plan", data)

    def test_poam_valid_boundary_empty_poam(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_json(tmp, GOOD)
            code, out, _ = self._run(["poam", path])
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(data["plan-of-action-and-milestones"]["poam-items"], [])


if __name__ == "__main__":
    unittest.main()
