"""Tests for OSCAL SSP + POA&M generation and Graphviz DOT rendering.

Covers the machine-readable artifact shape (metadata, oscal-version,
components, implemented-requirements, poam-items), deterministic UUIDs,
control-id normalization, and DOT structure/escaping. Stdlib only, no network.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fedramplens.core import (  # noqa: E402
    _build_boundary,
    _uuid_like,
    generate_dot,
    generate_poam,
    generate_ssp,
)


def _b(**kw):
    raw = {
        "system_name": "OSCAL Sys", "system_id": "FR-OSCAL", "impact": "high",
        "components": [
            {"id": "web", "name": "Web", "type": "service", "zone": "boundary",
             "controls": ["AC-2", "SC-8"]},
            {"id": "db", "name": "DB", "type": "database", "zone": "internal",
             "controls": ["SC-13"]},
        ],
        "flows": [{"from": "web", "to": "db", "encrypted": True}],
        "poam": [
            {"id": "V-1", "weakness": "weak cipher", "control": "SC-13",
             "severity": "high", "status": "open", "scheduled": "2027-01-01"},
        ],
    }
    raw.update(kw)
    return _build_boundary(raw)


class TestSSP(unittest.TestCase):
    def setUp(self):
        self.ssp = generate_ssp(_b())["system-security-plan"]

    def test_top_level_uuid(self):
        self.assertTrue(self.ssp["uuid"])

    def test_metadata_oscal_version(self):
        self.assertEqual(self.ssp["metadata"]["oscal-version"], "1.1.2")

    def test_metadata_title(self):
        self.assertIn("System Security Plan", self.ssp["metadata"]["title"])

    def test_last_modified_is_iso(self):
        # datetime.fromisoformat parses it back without raising
        import datetime
        datetime.datetime.fromisoformat(self.ssp["metadata"]["last-modified"])

    def test_import_profile_references_baseline(self):
        self.assertEqual(
            self.ssp["import-profile"]["href"], "#fedramp-high-baseline"
        )

    def test_sensitivity_level(self):
        sc = self.ssp["system-characteristics"]
        self.assertEqual(sc["security-sensitivity-level"], "high")
        self.assertEqual(sc["system-ids"][0]["id"], "FR-OSCAL")

    def test_components_inventory(self):
        comps = self.ssp["system-implementation"]["components"]
        self.assertEqual(len(comps), 2)
        titles = {c["title"] for c in comps}
        self.assertEqual(titles, {"Web", "DB"})

    def test_component_zone_prop(self):
        comps = self.ssp["system-implementation"]["components"]
        web = next(c for c in comps if c["title"] == "Web")
        zone = next(p["value"] for p in web["props"] if p["name"] == "zone")
        self.assertEqual(zone, "boundary")

    def test_implemented_requirements(self):
        reqs = self.ssp["control-implementation"]["implemented-requirements"]
        ids = {r["control-id"] for r in reqs}
        self.assertEqual(ids, {"ac-2", "sc-8", "sc-13"})

    def test_control_ids_are_lowercase_oscal(self):
        reqs = self.ssp["control-implementation"]["implemented-requirements"]
        for r in reqs:
            self.assertEqual(r["control-id"], r["control-id"].lower())

    def test_by_components_link(self):
        reqs = self.ssp["control-implementation"]["implemented-requirements"]
        for r in reqs:
            self.assertTrue(r["by-components"][0]["component-uuid"])
            self.assertIn("description", r["by-components"][0])

    def test_component_without_controls_yields_no_reqs(self):
        comps = [{"id": "x", "name": "X", "zone": "boundary"}]
        flows = [{"from": "internet", "to": "x", "encrypted": True}]
        ssp = generate_ssp(_b(components=comps, flows=flows))
        reqs = ssp["system-security-plan"]["control-implementation"][
            "implemented-requirements"]
        self.assertEqual(reqs, [])

    def test_ssp_deterministic(self):
        a = generate_ssp(_b())["system-security-plan"]["uuid"]
        b = generate_ssp(_b())["system-security-plan"]["uuid"]
        self.assertEqual(a, b)


class TestPoamGen(unittest.TestCase):
    def setUp(self):
        self.poam = generate_poam(_b())["plan-of-action-and-milestones"]

    def test_metadata(self):
        self.assertEqual(self.poam["metadata"]["oscal-version"], "1.1.2")
        self.assertIn("POA&M", self.poam["metadata"]["title"])

    def test_system_id(self):
        self.assertEqual(self.poam["system-id"]["id"], "FR-OSCAL")

    def test_item_count(self):
        self.assertEqual(len(self.poam["poam-items"]), 1)

    def test_item_props(self):
        item = self.poam["poam-items"][0]
        props = {p["name"]: p["value"] for p in item["props"]}
        self.assertEqual(props["severity"], "high")
        self.assertEqual(props["status"], "open")
        self.assertEqual(props["control"], "SC-13")
        self.assertEqual(props["scheduled-completion"], "2027-01-01")

    def test_item_description_from_weakness(self):
        item = self.poam["poam-items"][0]
        self.assertEqual(item["description"], "weak cipher")

    def test_empty_poam_yields_no_items(self):
        poam = generate_poam(_b(poam=[]))["plan-of-action-and-milestones"]
        self.assertEqual(poam["poam-items"], [])

    def test_poam_item_missing_fields_default(self):
        raw_poam = [{"id": "V-9", "severity": "low"}]
        poam = generate_poam(_b(poam=raw_poam))["plan-of-action-and-milestones"]
        item = poam["poam-items"][0]
        props = {p["name"]: p["value"] for p in item["props"]}
        self.assertEqual(props["status"], "open")   # default
        self.assertEqual(props["control"], "")       # empty default
        self.assertEqual(item["description"], "")    # no weakness


class TestUuid(unittest.TestCase):
    def test_uuid_shape(self):
        u = _uuid_like("seed")
        parts = u.split("-")
        self.assertEqual([len(p) for p in parts], [8, 4, 4, 4, 12])

    def test_uuid_deterministic(self):
        self.assertEqual(_uuid_like("abc"), _uuid_like("abc"))

    def test_uuid_distinct_seeds(self):
        self.assertNotEqual(_uuid_like("a"), _uuid_like("b"))


class TestDot(unittest.TestCase):
    def test_digraph_header(self):
        dot = generate_dot(_b())
        self.assertIn("digraph boundary", dot)
        self.assertIn("cluster_boundary", dot)

    def test_edges_present(self):
        dot = generate_dot(_b())
        self.assertIn("->", dot)

    def test_label_has_system_and_impact(self):
        dot = generate_dot(_b())
        self.assertIn("FR-OSCAL", dot)
        self.assertIn("HIGH", dot)

    def test_unencrypted_flow_is_red(self):
        comps = [
            {"id": "a", "zone": "internal", "controls": []},
            {"id": "ext", "zone": "external", "controls": []},
        ]
        flows = [{"from": "a", "to": "ext", "data": "x", "encrypted": False}]
        dot = generate_dot(_b(components=comps, flows=flows))
        self.assertIn("color=red", dot)

    def test_encrypted_flow_is_black(self):
        dot = generate_dot(_b())
        self.assertIn("color=black", dot)

    def test_external_node_synthesized_from_flow_token(self):
        comps = [{"id": "web", "zone": "boundary", "controls": []}]
        flows = [{"from": "internet", "to": "web", "encrypted": True}]
        dot = generate_dot(_b(components=comps, flows=flows))
        self.assertIn("internet", dot)

    def test_quotes_escaped_in_labels(self):
        comps = [{"id": "a", "name": 'Web "prod" tier', "zone": "boundary",
                  "controls": []}]
        flows = [{"from": "internet", "to": "a", "encrypted": True}]
        dot = generate_dot(_b(components=comps, flows=flows))
        # double quotes are replaced with single quotes to keep DOT valid
        self.assertNotIn('"prod"', dot)
        self.assertIn("'prod'", dot)

    def test_node_ids_sanitized(self):
        comps = [{"id": "web-tier.01", "zone": "boundary", "controls": []}]
        flows = [{"from": "internet", "to": "web-tier.01", "encrypted": True}]
        dot = generate_dot(_b(components=comps, flows=flows))
        self.assertIn("n_web_tier_01", dot)


if __name__ == "__main__":
    unittest.main()
