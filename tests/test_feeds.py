"""Offline tests for the OSCAL 800-53 data-feed enrichment layer.

These tests NEVER touch the network. They point COGNIS_FEEDS_CACHE at a trimmed
fixture cache (tests/fixtures/feedcache) holding a small real-shaped slice of the
NIST SP 800-53 rev5 OSCAL catalog, and exercise everything with offline=True.
"""
import io
import json
import os
import sys
import unittest
import contextlib

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

_HERE = os.path.dirname(__file__)
_FIXTURE_CACHE = os.path.join(_HERE, "fixtures", "feedcache")
_FIXTURE_SAMPLE = os.path.join(
    _HERE, "fixtures", "oscal-800-53-rev5-catalog.sample.json"
)

# Point the feed cache at the committed fixture BEFORE importing the modules
# that read it, so no test can reach the live catalog.
os.environ["COGNIS_FEEDS_CACHE"] = _FIXTURE_CACHE

from fedramplens import datafeeds, controls  # noqa: E402
from fedramplens.core import (  # noqa: E402
    _build_boundary,
    analyze_boundary,
    generate_ssp,
)
from fedramplens.cli import main, _relevant_feeds  # noqa: E402

BOUNDARY = {
    "system_name": "Feed Demo",
    "system_id": "FR-FEED-01",
    "impact": "moderate",
    "components": [
        {"id": "web", "name": "Web Tier", "zone": "boundary",
         "controls": ["AC-2", "SC-7"]},
        {"id": "db", "name": "DB", "zone": "internal",
         "controls": ["SC-13", "AC-2(1)"]},
    ],
    # Unencrypted crossing -> a high finding carrying control SC-8.
    "flows": [
        {"from": "internet", "to": "web", "data": "HTTP", "encrypted": False},
        {"from": "web", "to": "db", "data": "TLS", "encrypted": True},
    ],
    "poam": [],
}


class TestCatalogParsing(unittest.TestCase):
    def setUp(self):
        controls.reset_cache()

    def test_fixture_is_real_oscal_shape(self):
        cat = json.load(open(_FIXTURE_SAMPLE, encoding="utf-8"))
        self.assertIn("catalog", cat)
        self.assertIn("groups", cat["catalog"])
        # Title map flattens groups -> controls -> enhancements.
        titles = controls.build_title_map(cat)
        self.assertEqual(titles["ac-2"], "Account Management")
        self.assertEqual(titles["sc-8"], "Transmission Confidentiality and Integrity")
        self.assertEqual(titles["sc-13"], "Cryptographic Protection")
        # nested enhancement was flattened
        self.assertEqual(titles["ac-2.1"], "Automated System Account Management")

    def test_offline_get_serves_from_cache(self):
        data = datafeeds.get("oscal-800-53-rev5-catalog", offline=True)
        self.assertIsInstance(data, dict)
        self.assertIn("catalog", data)

    def test_control_title_offline(self):
        self.assertEqual(
            controls.control_title("SC-8", offline=True),
            "Transmission Confidentiality and Integrity",
        )

    def test_enhancement_falls_back_to_base(self):
        # AC-2(99) is not in the catalog; resolver falls back to AC-2's title.
        self.assertEqual(
            controls.control_title("AC-2(99)", offline=True), "Account Management"
        )

    def test_unknown_control_returns_none(self):
        self.assertIsNone(controls.control_title("ZZ-9", offline=True))


class TestEnrichment(unittest.TestCase):
    def setUp(self):
        controls.reset_cache()

    def test_analyze_enriches_finding_control_title(self):
        b = _build_boundary(BOUNDARY)
        summary = analyze_boundary(b, resolve_titles=True, offline=True)
        self.assertTrue(summary["feed_available"])
        sc8 = [f for f in summary["findings"]
               if f.get("control") == "SC-8"]
        self.assertTrue(sc8)
        self.assertEqual(
            sc8[0]["control_title"],
            "Transmission Confidentiality and Integrity",
        )

    def test_analyze_summary_control_titles(self):
        b = _build_boundary(BOUNDARY)
        summary = analyze_boundary(b, resolve_titles=True, offline=True)
        ct = summary["control_titles"]
        self.assertEqual(ct["ac-2"], "Account Management")
        self.assertEqual(ct["sc-13"], "Cryptographic Protection")

    def test_analyze_without_enrich_has_no_titles(self):
        b = _build_boundary(BOUNDARY)
        summary = analyze_boundary(b)
        self.assertNotIn("control_titles", summary)
        for f in summary["findings"]:
            self.assertNotIn("control_title", f)

    def test_ssp_enrich_adds_title_props(self):
        b = _build_boundary(BOUNDARY)
        ssp = generate_ssp(b, resolve_titles=True, offline=True)
        reqs = ssp["system-security-plan"]["control-implementation"][
            "implemented-requirements"
        ]
        labels = {}
        for r in reqs:
            for p in r.get("props", []):
                if p.get("class") == "nist-800-53-rev5-title":
                    labels[r["control-id"]] = p["value"]
        self.assertEqual(labels.get("sc-13"), "Cryptographic Protection")
        self.assertEqual(labels.get("ac-2"), "Account Management")


class TestGracefulDegrade(unittest.TestCase):
    def test_missing_cache_offline_degrades(self):
        # Point at an empty (temp) cache dir: offline get raises -> resolver {}.
        import tempfile
        empty = tempfile.mkdtemp(prefix="fedramplens-empty-cache-")
        old = os.environ.get("COGNIS_FEEDS_CACHE")
        os.environ["COGNIS_FEEDS_CACHE"] = empty
        controls.reset_cache()
        try:
            self.assertIsNone(controls.control_title("SC-8", offline=True))
            b = _build_boundary(BOUNDARY)
            summary = analyze_boundary(b, resolve_titles=True, offline=True)
            self.assertFalse(summary["feed_available"])
            self.assertEqual(summary["control_titles"], {})
            # analysis itself still succeeds
            self.assertIn("findings", summary)
        finally:
            if old is not None:
                os.environ["COGNIS_FEEDS_CACHE"] = old
            controls.reset_cache()


class TestFeedsCLI(unittest.TestCase):
    def setUp(self):
        os.environ["COGNIS_FEEDS_CACHE"] = _FIXTURE_CACHE
        controls.reset_cache()

    def _run(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_relevant_feeds_is_oscal_only(self):
        ids = {f["id"] for f in _relevant_feeds()}
        self.assertEqual(ids, {"oscal-800-53-rev5-catalog"})

    def test_feeds_list(self):
        code, out, _ = self._run(["feeds", "list"])
        self.assertEqual(code, 0)
        self.assertIn("oscal-800-53-rev5-catalog", out)
        self.assertIn("usnistgov/oscal-content", out)

    def test_feeds_get_offline(self):
        code, out, _ = self._run(
            ["feeds", "get", "oscal-800-53-rev5-catalog", "--offline"]
        )
        self.assertEqual(code, 0)
        self.assertIn("catalog", out)

    def test_feeds_rejects_unrelated_feed(self):
        code, _, err = self._run(["feeds", "get", "cisa-kev", "--offline"])
        self.assertEqual(code, 2)
        self.assertIn("not a feed", err)

    def test_analyze_enrich_cli_offline(self):
        # write a temp boundary file
        import tempfile
        with tempfile.NamedTemporaryFile(
            "w", suffix=".json", delete=False
        ) as fh:
            json.dump(BOUNDARY, fh)
            path = fh.name
        try:
            code, out, _ = self._run(
                ["analyze", path, "--enrich", "--offline"]
            )
            self.assertEqual(code, 1)  # unencrypted crossing -> not ready
            self.assertIn("Transmission Confidentiality", out)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
