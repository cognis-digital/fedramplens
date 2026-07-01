"""Offline tests for the datafeeds layer + controls enrichment edge cases.

Never touches the network: COGNIS_FEEDS_CACHE points at the committed OSCAL
fixture cache and everything runs offline=True. Covers the catalog loader,
cache paths/age metadata, offline get() error contract, snapshot export/import
round-trip, control-id normalization, enhancement fallback, and graceful
degrade to {} on a missing cache. Stdlib only.
"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

_HERE = os.path.dirname(__file__)
_FIXTURE_CACHE = os.path.join(_HERE, "fixtures", "feedcache")
os.environ["COGNIS_FEEDS_CACHE"] = _FIXTURE_CACHE

from fedramplens import controls, datafeeds  # noqa: E402

FEED = "oscal-800-53-rev5-catalog"


class TestCatalog(unittest.TestCase):
    def test_load_catalog_has_feeds(self):
        cat = datafeeds.load_catalog()
        self.assertIn("feeds", cat)
        self.assertTrue(cat["feeds"])

    def test_oscal_feed_present(self):
        ids = {f["id"] for f in datafeeds.list_feeds()}
        self.assertIn(FEED, ids)

    def test_oscal_feed_is_oscal_format(self):
        feed = next(f for f in datafeeds.list_feeds() if f["id"] == FEED)
        self.assertEqual(feed.get("format"), "oscal")

    def test_list_feeds_filter_by_domain(self):
        feed = next(f for f in datafeeds.list_feeds() if f["id"] == FEED)
        domain = feed.get("domain")
        if domain:
            filtered = datafeeds.list_feeds(domain=domain)
            self.assertTrue(all(f.get("domain") == domain for f in filtered))

    def test_load_missing_catalog_returns_empty(self):
        missing = os.path.join(tempfile.gettempdir(), "no-catalog-xyz.json")
        self.assertEqual(datafeeds.load_catalog(missing), {"feeds": []})


class TestCachePaths(unittest.TestCase):
    def setUp(self):
        os.environ["COGNIS_FEEDS_CACHE"] = _FIXTURE_CACHE

    def test_cache_dir_created(self):
        d = datafeeds.cache_dir()
        self.assertTrue(os.path.isdir(d))

    def test_cached_age_for_fixture(self):
        age = datafeeds.cached_age_hours(FEED)
        self.assertIsNotNone(age)
        self.assertGreaterEqual(age, 0)

    def test_cached_age_none_for_unknown(self):
        self.assertIsNone(datafeeds.cached_age_hours("never-fetched-feed"))


class TestOfflineGet(unittest.TestCase):
    def setUp(self):
        os.environ["COGNIS_FEEDS_CACHE"] = _FIXTURE_CACHE

    def test_offline_get_returns_dict(self):
        data = datafeeds.get(FEED, offline=True)
        self.assertIsInstance(data, dict)
        self.assertIn("catalog", data)

    def test_offline_get_missing_raises(self):
        empty = tempfile.mkdtemp(prefix="ff-empty-")
        os.environ["COGNIS_FEEDS_CACHE"] = empty
        try:
            with self.assertRaises(FileNotFoundError):
                datafeeds.get(FEED, offline=True)
        finally:
            os.environ["COGNIS_FEEDS_CACHE"] = _FIXTURE_CACHE


class TestSnapshot(unittest.TestCase):
    def test_export_import_roundtrip(self):
        os.environ["COGNIS_FEEDS_CACHE"] = _FIXTURE_CACHE
        tmp = tempfile.mkdtemp(prefix="ff-snap-")
        archive = os.path.join(tmp, "feeds.tar.gz")
        n = datafeeds.snapshot_export(archive)
        self.assertGreaterEqual(n, 1)
        self.assertTrue(os.path.exists(archive))

        # Import into a fresh empty cache and confirm the feed reads back.
        dest = tempfile.mkdtemp(prefix="ff-dest-")
        os.environ["COGNIS_FEEDS_CACHE"] = dest
        try:
            imported = datafeeds.snapshot_import(archive)
            self.assertGreaterEqual(imported, 1)
            data = datafeeds.get(FEED, offline=True)
            self.assertIn("catalog", data)
        finally:
            os.environ["COGNIS_FEEDS_CACHE"] = _FIXTURE_CACHE


class TestControlNormalization(unittest.TestCase):
    def setUp(self):
        os.environ["COGNIS_FEEDS_CACHE"] = _FIXTURE_CACHE
        controls.reset_cache()

    def test_normalize_forms(self):
        self.assertEqual(controls._normalize("AC-2(1)"), "ac-2.1")
        self.assertEqual(controls._normalize("ac-2.1"), "ac-2.1")
        self.assertEqual(controls._normalize("  SC-8 "), "sc-8")

    def test_title_lookup(self):
        self.assertEqual(
            controls.control_title("SC-8", offline=True),
            "Transmission Confidentiality and Integrity",
        )

    def test_title_lookup_case_insensitive(self):
        self.assertEqual(
            controls.control_title("sc-8", offline=True),
            controls.control_title("SC-8", offline=True),
        )

    def test_enhancement_exact_hit(self):
        self.assertEqual(
            controls.control_title("AC-2(1)", offline=True),
            "Automated System Account Management",
        )

    def test_enhancement_falls_back_to_base(self):
        self.assertEqual(
            controls.control_title("AC-2(99)", offline=True),
            "Account Management",
        )

    def test_unknown_returns_none(self):
        self.assertIsNone(controls.control_title("ZZ-9", offline=True))

    def test_empty_control_returns_none(self):
        self.assertIsNone(controls.control_title("", offline=True))
        self.assertIsNone(controls.control_title(None, offline=True))

    def test_enrich_controls_map(self):
        m = controls.enrich_controls(["AC-2", "ZZ-9"], offline=True)
        self.assertEqual(m["AC-2"], "Account Management")
        self.assertIsNone(m["ZZ-9"])


class TestGracefulDegrade(unittest.TestCase):
    def test_missing_cache_returns_none(self):
        empty = tempfile.mkdtemp(prefix="ff-degrade-")
        os.environ["COGNIS_FEEDS_CACHE"] = empty
        controls.reset_cache()
        try:
            self.assertIsNone(controls.control_title("SC-8", offline=True))
        finally:
            os.environ["COGNIS_FEEDS_CACHE"] = _FIXTURE_CACHE
            controls.reset_cache()

    def test_build_title_map_direct(self):
        cat = datafeeds.get(FEED, offline=True)
        titles = controls.build_title_map(cat)
        self.assertEqual(titles["ac-2"], "Account Management")
        self.assertEqual(titles["sc-13"], "Cryptographic Protection")

    def test_build_title_map_handles_empty(self):
        self.assertEqual(controls.build_title_map({}), {})
        self.assertEqual(controls.build_title_map({"catalog": {}}), {})


if __name__ == "__main__":
    unittest.main()
