"""Edge-case tests for the SARIF 2.1.0 exporter.

Covers the envelope/schema, rule catalogue de-duplication, severity->level
mapping (including the hardened rule-default escalation), preserved control +
fedramp-severity properties, empty runs, and robustness against findings that
are missing optional keys. Stdlib only, no network.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fedramplens.core import (  # noqa: E402
    TOOL_NAME,
    _build_boundary,
    analyze_boundary,
    to_sarif,
)


def _b(**kw):
    raw = {
        "system_name": "Sarif", "system_id": "FR-SARIF", "impact": "moderate",
        "components": [{"id": "a", "zone": "boundary", "controls": []}],
        "flows": [], "poam": [],
    }
    raw.update(kw)
    return _build_boundary(raw)


def _crossing_boundary():
    comps = [
        {"id": "a", "zone": "internal", "controls": []},
        {"id": "ext", "zone": "external", "controls": []},
    ]
    flows = [{"from": "a", "to": "ext", "data": "d", "encrypted": False}]
    return _b(components=comps, flows=flows)


class TestEnvelope(unittest.TestCase):
    def test_schema_and_version(self):
        s = to_sarif(analyze_boundary(_b()))
        self.assertEqual(s["version"], "2.1.0")
        self.assertIn("sarif-2.1.0", s["$schema"])

    def test_single_run(self):
        s = to_sarif(analyze_boundary(_b()))
        self.assertEqual(len(s["runs"]), 1)

    def test_driver_identity(self):
        driver = to_sarif(analyze_boundary(_b()))["runs"][0]["tool"]["driver"]
        self.assertEqual(driver["name"], TOOL_NAME)
        self.assertTrue(driver["version"])
        self.assertIn("informationUri", driver)

    def test_run_properties(self):
        s = to_sarif(analyze_boundary(_crossing_boundary()))
        props = s["runs"][0]["properties"]
        self.assertEqual(props["system-id"], "FR-SARIF")
        self.assertEqual(props["impact"], "moderate")
        self.assertIn("coverage-pct", props)
        self.assertIn("authorization-ready", props)


class TestRuleCatalogue(unittest.TestCase):
    def test_rules_deduplicated(self):
        # Two dangling flows share one finding-type -> one rule, two results.
        comps = [{"id": "a", "zone": "boundary", "controls": []}]
        flows = [
            {"from": "a", "to": "ghost1", "encrypted": True},
            {"from": "a", "to": "ghost2", "encrypted": True},
        ]
        s = to_sarif(analyze_boundary(_b(components=comps, flows=flows)))
        run = s["runs"][0]
        rule_ids = [r["id"] for r in run["tool"]["driver"]["rules"]]
        self.assertEqual(rule_ids.count("dangling_flow"), 1)
        dangs = [r for r in run["results"] if r["ruleId"] == "dangling_flow"]
        self.assertEqual(len(dangs), 2)

    def test_rule_index_consistent(self):
        s = to_sarif(analyze_boundary(_crossing_boundary()))
        run = s["runs"][0]
        rules = run["tool"]["driver"]["rules"]
        for res in run["results"]:
            self.assertEqual(rules[res["ruleIndex"]]["id"], res["ruleId"])

    def test_rule_has_help_uri_and_descriptions(self):
        s = to_sarif(analyze_boundary(_crossing_boundary()))
        for r in s["runs"][0]["tool"]["driver"]["rules"]:
            self.assertIn("helpUri", r)
            self.assertIn("shortDescription", r)
            self.assertIn("fullDescription", r)

    def test_rule_name_is_pascal_case(self):
        s = to_sarif(analyze_boundary(_crossing_boundary()))
        r = next(r for r in s["runs"][0]["tool"]["driver"]["rules"]
                 if r["id"] == "unencrypted_boundary_crossing")
        self.assertEqual(r["name"], "UnencryptedBoundaryCrossing")


class TestLevelMapping(unittest.TestCase):
    def test_high_maps_to_error(self):
        s = to_sarif(analyze_boundary(_crossing_boundary()))
        res = next(r for r in s["runs"][0]["results"]
                   if r["ruleId"] == "unencrypted_boundary_crossing")
        self.assertEqual(res["level"], "error")

    def test_low_maps_to_note(self):
        # a lone orphan is a low finding -> note
        s = to_sarif(analyze_boundary(_b()))
        res = next(r for r in s["runs"][0]["results"]
                   if r["ruleId"] == "orphan_component")
        self.assertEqual(res["level"], "note")

    def test_rule_default_escalates_to_most_severe(self):
        # Build findings of the same type with differing severity by hand,
        # then confirm the rule default reflects the highest (error).
        summary = {
            "system_id": "X", "system_name": "X",
            "findings": [
                {"type": "t", "severity": "low", "detail": "a"},
                {"type": "t", "severity": "high", "detail": "b"},
            ],
        }
        s = to_sarif(summary)
        rule = s["runs"][0]["tool"]["driver"]["rules"][0]
        self.assertEqual(rule["defaultConfiguration"]["level"], "error")

    def test_unknown_severity_defaults_to_warning(self):
        summary = {
            "findings": [{"type": "t", "severity": "weird", "detail": "x"}],
        }
        s = to_sarif(summary)
        self.assertEqual(s["runs"][0]["results"][0]["level"], "warning")


class TestProperties(unittest.TestCase):
    def test_control_preserved(self):
        s = to_sarif(analyze_boundary(_crossing_boundary()))
        controls = [r["properties"].get("nist-control")
                    for r in s["runs"][0]["results"]]
        self.assertIn("SC-8", controls)

    def test_fedramp_severity_preserved(self):
        s = to_sarif(analyze_boundary(_crossing_boundary()))
        sevs = [r["properties"]["fedramp-severity"]
                for r in s["runs"][0]["results"]]
        self.assertIn("high", sevs)

    def test_result_has_logical_location(self):
        s = to_sarif(analyze_boundary(_crossing_boundary()))
        loc = s["runs"][0]["results"][0]["locations"][0]["logicalLocations"][0]
        self.assertEqual(loc["name"], "FR-SARIF")
        self.assertEqual(loc["kind"], "module")

    def test_no_control_property_when_absent(self):
        # orphan findings carry no control
        s = to_sarif(analyze_boundary(_b()))
        res = next(r for r in s["runs"][0]["results"]
                   if r["ruleId"] == "orphan_component")
        self.assertNotIn("nist-control", res["properties"])


class TestEmptyAndRobust(unittest.TestCase):
    def test_clean_boundary_empty_results(self):
        comps = [{"id": "a", "zone": "boundary", "controls": ["AC-2"]}]
        flows = [{"from": "internet", "to": "a", "encrypted": True}]
        s = to_sarif(analyze_boundary(_b(components=comps, flows=flows)))
        self.assertEqual(s["runs"][0]["results"], [])
        self.assertEqual(s["runs"][0]["tool"]["driver"]["rules"], [])

    def test_missing_findings_key(self):
        s = to_sarif({"system_id": "X"})
        self.assertEqual(s["runs"][0]["results"], [])

    def test_finding_missing_optional_keys(self):
        # No 'severity', no 'detail' — exporter must still produce valid output.
        s = to_sarif({"findings": [{"type": "custom"}]})
        res = s["runs"][0]["results"][0]
        self.assertEqual(res["ruleId"], "custom")
        self.assertEqual(res["level"], "warning")
        self.assertEqual(res["message"]["text"], "")

    def test_finding_missing_type_key(self):
        s = to_sarif({"findings": [{"severity": "high", "detail": "d"}]})
        self.assertEqual(s["runs"][0]["results"][0]["ruleId"], "finding")


if __name__ == "__main__":
    unittest.main()
