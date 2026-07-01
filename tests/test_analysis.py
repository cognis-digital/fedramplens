"""Deep tests for analyze_boundary: SC-8 crossing detection, orphans,
dangling flows, POA&M overdue/risk/date handling, coverage math, and the
authorization-ready gate. Stdlib only, no network.
"""
import datetime
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fedramplens.core import (  # noqa: E402
    BASELINE_CONTROL_COUNTS,
    Boundary,
    _build_boundary,
    _is_external_token,
    _normalize_control,
    analyze_boundary,
)


def _b(**kw):
    raw = {
        "system_name": "S", "system_id": "ID", "impact": "moderate",
        "components": [{"id": "a", "zone": "boundary", "controls": []}],
        "flows": [], "poam": [],
    }
    raw.update(kw)
    return _build_boundary(raw)


def _types(summary):
    return [f["type"] for f in summary["findings"]]


class TestCrossingDetection(unittest.TestCase):
    def _cross(self, encrypted):
        # internal component 'a' <-> external component 'ext'
        comps = [
            {"id": "a", "zone": "internal", "controls": []},
            {"id": "ext", "zone": "external", "controls": []},
        ]
        flows = [{"from": "a", "to": "ext", "data": "d", "encrypted": encrypted}]
        return analyze_boundary(_b(components=comps, flows=flows))

    def test_unencrypted_crossing_flagged(self):
        s = self._cross(False)
        self.assertIn("unencrypted_boundary_crossing", _types(s))

    def test_encrypted_crossing_not_flagged(self):
        s = self._cross(True)
        self.assertNotIn("unencrypted_boundary_crossing", _types(s))

    def test_crossing_carries_sc8_control(self):
        s = self._cross(False)
        f = next(f for f in s["findings"]
                 if f["type"] == "unencrypted_boundary_crossing")
        self.assertEqual(f["control"], "SC-8")
        self.assertEqual(f["severity"], "high")

    def test_internal_to_internal_never_crosses(self):
        comps = [
            {"id": "a", "zone": "internal", "controls": []},
            {"id": "b", "zone": "boundary", "controls": []},
        ]
        flows = [{"from": "a", "to": "b", "encrypted": False}]
        s = analyze_boundary(_b(components=comps, flows=flows))
        self.assertNotIn("unencrypted_boundary_crossing", _types(s))

    def test_internet_token_to_boundary_is_a_crossing(self):
        # "internet" is external-by-definition; unencrypted -> crossing
        comps = [{"id": "web", "zone": "boundary", "controls": []}]
        flows = [{"from": "internet", "to": "web", "encrypted": False}]
        s = analyze_boundary(_b(components=comps, flows=flows))
        self.assertIn("unencrypted_boundary_crossing", _types(s))

    def test_internet_token_encrypted_no_crossing(self):
        comps = [{"id": "web", "zone": "boundary", "controls": []}]
        flows = [{"from": "internet", "to": "web", "encrypted": True}]
        s = analyze_boundary(_b(components=comps, flows=flows))
        self.assertNotIn("unencrypted_boundary_crossing", _types(s))

    def test_missing_encrypted_key_treated_as_unencrypted(self):
        comps = [
            {"id": "a", "zone": "internal", "controls": []},
            {"id": "ext", "zone": "external", "controls": []},
        ]
        flows = [{"from": "a", "to": "ext"}]  # no 'encrypted' key
        s = analyze_boundary(_b(components=comps, flows=flows))
        self.assertIn("unencrypted_boundary_crossing", _types(s))

    def test_reverse_direction_crossing(self):
        comps = [
            {"id": "a", "zone": "internal", "controls": []},
            {"id": "ext", "zone": "external", "controls": []},
        ]
        flows = [{"from": "ext", "to": "a", "encrypted": False}]
        s = analyze_boundary(_b(components=comps, flows=flows))
        self.assertIn("unencrypted_boundary_crossing", _types(s))


class TestDanglingFlows(unittest.TestCase):
    def test_unknown_target_flagged(self):
        comps = [{"id": "a", "zone": "boundary", "controls": []}]
        flows = [{"from": "a", "to": "ghost", "encrypted": True}]
        s = analyze_boundary(_b(components=comps, flows=flows))
        self.assertIn("dangling_flow", _types(s))

    def test_unknown_source_flagged(self):
        comps = [{"id": "a", "zone": "boundary", "controls": []}]
        flows = [{"from": "ghost", "to": "a", "encrypted": True}]
        s = analyze_boundary(_b(components=comps, flows=flows))
        self.assertIn("dangling_flow", _types(s))

    def test_external_token_source_not_dangling(self):
        comps = [{"id": "a", "zone": "boundary", "controls": []}]
        flows = [{"from": "internet", "to": "a", "encrypted": True}]
        s = analyze_boundary(_b(components=comps, flows=flows))
        self.assertNotIn("dangling_flow", _types(s))

    def test_both_endpoints_unknown_yields_two_findings(self):
        comps = [{"id": "a", "zone": "boundary", "controls": []}]
        flows = [{"from": "x", "to": "y", "encrypted": True}]
        s = analyze_boundary(_b(components=comps, flows=flows))
        self.assertEqual(_types(s).count("dangling_flow"), 2)


class TestOrphanComponents(unittest.TestCase):
    def test_orphan_in_boundary_flagged(self):
        comps = [
            {"id": "a", "zone": "boundary", "controls": []},
            {"id": "lonely", "zone": "internal", "controls": []},
        ]
        flows = [{"from": "internet", "to": "a", "encrypted": True}]
        s = analyze_boundary(_b(components=comps, flows=flows))
        detail = " ".join(f["detail"] for f in s["findings"]
                          if f["type"] == "orphan_component")
        self.assertIn("lonely", detail)

    def test_external_component_never_orphan(self):
        comps = [
            {"id": "a", "zone": "boundary", "controls": []},
            {"id": "ext", "zone": "external", "controls": []},
        ]
        flows = [{"from": "internet", "to": "a", "encrypted": True}]
        s = analyze_boundary(_b(components=comps, flows=flows))
        # 'ext' is untouched but external, so it must NOT be an orphan
        detail = " ".join(f["detail"] for f in s["findings"]
                          if f["type"] == "orphan_component")
        self.assertNotIn("ext", detail)

    def test_touched_component_not_orphan(self):
        comps = [{"id": "a", "zone": "boundary", "controls": []}]
        flows = [{"from": "internet", "to": "a", "encrypted": True}]
        s = analyze_boundary(_b(components=comps, flows=flows))
        self.assertNotIn("orphan_component", _types(s))

    def test_orphan_is_low_severity(self):
        comps = [{"id": "a", "zone": "boundary", "controls": []}]
        s = analyze_boundary(_b(components=comps, flows=[]))
        f = next(f for f in s["findings"] if f["type"] == "orphan_component")
        self.assertEqual(f["severity"], "low")


class TestPoamAnalysis(unittest.TestCase):
    def test_open_count(self):
        poam = [
            {"id": "P1", "severity": "high", "status": "open"},
            {"id": "P2", "severity": "low", "status": "completed"},
            {"id": "P3", "severity": "moderate", "status": "open"},
        ]
        s = analyze_boundary(_b(poam=poam))
        self.assertEqual(s["poam_open"], 2)

    def test_risk_score_sums_open_only(self):
        poam = [
            {"id": "P1", "severity": "critical", "status": "open"},   # 8
            {"id": "P2", "severity": "high", "status": "open"},       # 4
            {"id": "P3", "severity": "high", "status": "completed"},  # 0
        ]
        s = analyze_boundary(_b(poam=poam))
        self.assertEqual(s["poam_risk_score"], 12)

    def test_overdue_detected(self):
        poam = [{"id": "P1", "severity": "high", "status": "open",
                 "scheduled": "2000-01-01"}]
        s = analyze_boundary(_b(poam=poam))
        self.assertIn("P1", s["poam_overdue"])
        self.assertIn("overdue_poam", _types(s))

    def test_future_date_not_overdue(self):
        future = (datetime.date.today() + datetime.timedelta(days=365)).isoformat()
        poam = [{"id": "P1", "severity": "high", "status": "open",
                 "scheduled": future}]
        s = analyze_boundary(_b(poam=poam))
        self.assertEqual(s["poam_overdue"], [])

    def test_closed_overdue_item_not_flagged(self):
        poam = [{"id": "P1", "severity": "high", "status": "completed",
                 "scheduled": "2000-01-01"}]
        s = analyze_boundary(_b(poam=poam))
        self.assertEqual(s["poam_overdue"], [])

    def test_bad_date_flagged_for_open_item(self):
        poam = [{"id": "P1", "severity": "high", "status": "open",
                 "scheduled": "31/12/2026"}]
        s = analyze_boundary(_b(poam=poam))
        self.assertIn("bad_poam_date", _types(s))

    def test_bad_date_flagged_even_for_closed_item(self):
        # Hardened behavior: a malformed date is a data-quality issue on ANY item.
        poam = [{"id": "P1", "severity": "high", "status": "completed",
                 "scheduled": "not-a-date"}]
        s = analyze_boundary(_b(poam=poam))
        self.assertIn("bad_poam_date", _types(s))

    def test_no_scheduled_date_is_fine(self):
        poam = [{"id": "P1", "severity": "high", "status": "open"}]
        s = analyze_boundary(_b(poam=poam))
        self.assertNotIn("bad_poam_date", _types(s))
        self.assertEqual(s["poam_overdue"], [])

    def test_empty_poam(self):
        s = analyze_boundary(_b(poam=[]))
        self.assertEqual(s["poam_open"], 0)
        self.assertEqual(s["poam_risk_score"], 0)
        self.assertEqual(s["poam_overdue"], [])


class TestCoverageMath(unittest.TestCase):
    def test_baseline_counts(self):
        self.assertEqual(BASELINE_CONTROL_COUNTS["low"], 156)
        self.assertEqual(BASELINE_CONTROL_COUNTS["moderate"], 323)
        self.assertEqual(BASELINE_CONTROL_COUNTS["high"], 410)

    def test_coverage_percentage(self):
        comps = [{"id": "a", "zone": "boundary",
                  "controls": ["AC-2", "SC-7", "SC-8"]}]
        s = analyze_boundary(_b(components=comps, impact="moderate"))
        # 3 / 323 * 100 = 0.9
        self.assertEqual(s["controls_implemented"], 3)
        self.assertAlmostEqual(s["coverage_pct"], round(300 / 323, 1))

    def test_duplicate_controls_counted_once(self):
        comps = [
            {"id": "a", "zone": "boundary", "controls": ["AC-2", "ac-2"]},
            {"id": "b", "zone": "internal", "controls": ["AC-2"]},
        ]
        flows = [{"from": "a", "to": "b", "encrypted": True}]
        s = analyze_boundary(_b(components=comps, flows=flows))
        self.assertEqual(s["controls_implemented"], 1)

    def test_zero_controls_zero_coverage(self):
        s = analyze_boundary(_b())
        self.assertEqual(s["coverage_pct"], 0.0)


class TestAuthorizationGate(unittest.TestCase):
    def test_high_finding_blocks(self):
        comps = [
            {"id": "a", "zone": "internal", "controls": []},
            {"id": "ext", "zone": "external", "controls": []},
        ]
        flows = [{"from": "a", "to": "ext", "encrypted": False}]
        s = analyze_boundary(_b(components=comps, flows=flows))
        self.assertFalse(s["authorization_ready"])

    def test_only_low_findings_still_ready(self):
        # a lone orphan (low) should not block authorization
        s = analyze_boundary(_b())
        self.assertEqual(_types(s), ["orphan_component"])
        self.assertTrue(s["authorization_ready"])

    def test_clean_system_is_ready(self):
        comps = [{"id": "a", "zone": "boundary", "controls": ["AC-2"]}]
        flows = [{"from": "internet", "to": "a", "encrypted": True}]
        s = analyze_boundary(_b(components=comps, flows=flows))
        self.assertTrue(s["authorization_ready"])
        self.assertEqual(s["findings"], [])

    def test_finding_counts_by_severity(self):
        comps = [
            {"id": "a", "zone": "internal", "controls": []},
            {"id": "ext", "zone": "external", "controls": []},
            {"id": "orphan", "zone": "internal", "controls": []},
        ]
        flows = [{"from": "a", "to": "ext", "encrypted": False}]
        s = analyze_boundary(_b(components=comps, flows=flows))
        counts = s["finding_counts"]
        self.assertEqual(counts.get("high"), 1)
        self.assertEqual(counts.get("low"), 1)


class TestSummaryShape(unittest.TestCase):
    def test_summary_keys_present(self):
        s = analyze_boundary(_b())
        for key in (
            "system_name", "system_id", "impact", "baseline_controls",
            "controls_implemented", "coverage_pct", "components_in_boundary",
            "external_dependencies", "flows", "poam_open", "poam_overdue",
            "poam_risk_score", "findings", "finding_counts",
            "authorization_ready",
        ):
            self.assertIn(key, s)

    def test_no_enrich_keys_by_default(self):
        s = analyze_boundary(_b())
        self.assertNotIn("control_titles", s)
        self.assertNotIn("feed_available", s)

    def test_external_dependencies_listed(self):
        comps = [
            {"id": "a", "zone": "boundary", "controls": []},
            {"id": "ext1", "zone": "external", "controls": []},
            {"id": "ext2", "zone": "external", "controls": []},
        ]
        s = analyze_boundary(_b(components=comps))
        self.assertEqual(set(s["external_dependencies"]), {"ext1", "ext2"})


class TestHelpers(unittest.TestCase):
    def test_normalize_control(self):
        self.assertEqual(_normalize_control("ac-2"), "AC-2")
        self.assertEqual(_normalize_control("  sc-8 "), "SC-8")

    def test_is_external_token(self):
        for tok in ("internet", "USER", "External", "public", "saas"):
            self.assertTrue(_is_external_token(tok))
        self.assertFalse(_is_external_token("web-tier"))


if __name__ == "__main__":
    unittest.main()
