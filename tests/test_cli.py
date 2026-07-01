"""Tests for the fedramplens command-line interface.

Covers every subcommand (analyze/diagram/ssp/poam/feeds), all output formats
(table/json/sarif), exit codes (0 ready, 1 findings, 2 usage/error), and the
error paths for missing files, malformed JSON, invalid boundaries, and
late-validation failures surfaced from analyze. Offline; uses the committed
OSCAL fixture cache. Stdlib only.
"""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

_HERE = os.path.dirname(__file__)
_FIXTURE_CACHE = os.path.join(_HERE, "fixtures", "feedcache")
os.environ["COGNIS_FEEDS_CACHE"] = _FIXTURE_CACHE

from fedramplens import controls  # noqa: E402
from fedramplens.cli import main  # noqa: E402

_ROOT = os.path.abspath(os.path.join(_HERE, ".."))
DEMO = os.path.join(_ROOT, "demos", "01-basic", "boundary.json")
CLEAN = os.path.join(_ROOT, "demos", "02-clean-low-saas", "boundary.json")

VALID = {
    "system_name": "CLI Sys", "system_id": "FR-CLI", "impact": "moderate",
    "components": [{"id": "web", "name": "Web", "zone": "boundary",
                   "controls": ["AC-2", "SC-8"]}],
    "flows": [{"from": "internet", "to": "web", "encrypted": True}],
    "poam": [],
}


def _run(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


def _write(data):
    fh = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    if isinstance(data, str):
        fh.write(data)
    else:
        json.dump(data, fh)
    fh.close()
    return fh.name


class TestAnalyzeCommand(unittest.TestCase):
    def test_analyze_table_findings_exit_1(self):
        code, out, _ = _run(["analyze", DEMO])
        self.assertEqual(code, 1)
        self.assertIn("Authorization-ready", out)

    def test_analyze_clean_exit_0(self):
        code, out, _ = _run(["analyze", CLEAN])
        self.assertEqual(code, 0)

    def test_analyze_json(self):
        code, out, _ = _run(["--format", "json", "analyze", DEMO])
        self.assertEqual(code, 1)
        data = json.loads(out)
        self.assertEqual(data["system_id"], "FR2026ACME01")

    def test_analyze_sarif(self):
        code, out, _ = _run(["--format", "sarif", "analyze", DEMO])
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(out)["version"], "2.1.0")

    def test_analyze_own_valid_file_ready(self):
        path = _write(VALID)
        try:
            code, out, _ = _run(["analyze", path])
            self.assertEqual(code, 0)
            self.assertIn("YES", out)
        finally:
            os.unlink(path)

    def test_analyze_table_prints_coverage(self):
        code, out, _ = _run(["analyze", DEMO])
        self.assertIn("Controls:", out)
        self.assertIn("of baseline", out)


class TestErrorPaths(unittest.TestCase):
    def test_missing_file_exit_2(self):
        code, _, err = _run(["analyze", os.path.join(tempfile.gettempdir(),
                                                      "no-such.json")])
        self.assertEqual(code, 2)
        self.assertIn("file not found", err)

    def test_malformed_json_exit_2(self):
        path = _write("{ bad json")
        try:
            code, _, err = _run(["analyze", path])
            self.assertEqual(code, 2)
            self.assertIn("invalid JSON", err)
        finally:
            os.unlink(path)

    def test_invalid_boundary_exit_2(self):
        path = _write({"system_name": "x", "system_id": "y",
                       "impact": "medium", "components": [{"id": "a"}]})
        try:
            code, _, err = _run(["analyze", path])
            self.assertEqual(code, 2)
            self.assertIn("invalid boundary", err)
        finally:
            os.unlink(path)

    def test_missing_components_exit_2(self):
        path = _write({"system_name": "x", "system_id": "y",
                       "impact": "low", "components": []})
        try:
            code, _, err = _run(["analyze", path])
            self.assertEqual(code, 2)
        finally:
            os.unlink(path)


class TestDiagramCommand(unittest.TestCase):
    def test_diagram_exit_0(self):
        code, out, _ = _run(["diagram", DEMO])
        self.assertEqual(code, 0)
        self.assertIn("digraph", out)

    def test_diagram_missing_file_exit_2(self):
        code, _, err = _run(["diagram", "/no/such/file.json"])
        self.assertEqual(code, 2)


class TestSspPoamCommands(unittest.TestCase):
    def test_ssp_exit_0(self):
        code, out, _ = _run(["ssp", DEMO])
        self.assertEqual(code, 0)
        self.assertIn("system-security-plan", json.loads(out))

    def test_poam_exit_0(self):
        code, out, _ = _run(["poam", DEMO])
        self.assertEqual(code, 0)
        self.assertIn("plan-of-action-and-milestones", json.loads(out))

    def test_ssp_enrich_offline(self):
        controls.reset_cache()
        code, out, _ = _run(["ssp", DEMO, "--enrich", "--offline"])
        self.assertEqual(code, 0)
        # AC-2 title should appear from the fixture catalog
        self.assertIn("Account Management", out)


class TestFeedsCommand(unittest.TestCase):
    def setUp(self):
        os.environ["COGNIS_FEEDS_CACHE"] = _FIXTURE_CACHE
        controls.reset_cache()

    def test_feeds_list_exit_0(self):
        code, out, _ = _run(["feeds", "list"])
        self.assertEqual(code, 0)
        self.assertIn("oscal-800-53-rev5-catalog", out)

    def test_feeds_get_offline(self):
        code, out, _ = _run(["feeds", "get", "oscal-800-53-rev5-catalog",
                             "--offline"])
        self.assertEqual(code, 0)
        self.assertIn("catalog", out)

    def test_feeds_get_unrelated_exit_2(self):
        code, _, err = _run(["feeds", "get", "cisa-kev", "--offline"])
        self.assertEqual(code, 2)
        self.assertIn("not a feed", err)

    def test_feeds_get_unknown_exit_2(self):
        code, _, err = _run(["feeds", "get", "made-up-feed", "--offline"])
        self.assertEqual(code, 2)


class TestVersionAndUsage(unittest.TestCase):
    def test_version_flag(self):
        with self.assertRaises(SystemExit) as cm:
            _run(["--version"])
        self.assertEqual(cm.exception.code, 0)

    def test_no_command_errors(self):
        with self.assertRaises(SystemExit) as cm:
            _run([])
        self.assertNotEqual(cm.exception.code, 0)

    def test_analyze_enrich_offline_shows_titles(self):
        controls.reset_cache()
        path = _write(VALID)
        try:
            code, out, _ = _run(["analyze", path, "--enrich", "--offline"])
            self.assertEqual(code, 0)
            self.assertIn("Account Management", out)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
