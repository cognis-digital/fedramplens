"""Edge-case + error-path tests for boundary loading and validation.

Exercises _build_boundary / load_boundary hard against malformed input:
missing/empty fields, wrong types, duplicate ids, bad zones/severities, and
the defensive normalization that keeps analyze_boundary from leaking raw
KeyErrors when a Boundary is constructed directly through the public dataclass.
Stdlib only, no network.
"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fedramplens.core import (  # noqa: E402
    Boundary,
    BoundaryError,
    _build_boundary,
    analyze_boundary,
    load_boundary,
)

BASE = {
    "system_name": "Base",
    "system_id": "FR-BASE",
    "impact": "moderate",
    "components": [
        {"id": "a", "name": "A", "zone": "boundary", "controls": ["AC-2"]},
    ],
    "flows": [],
    "poam": [],
}


def _mut(**changes):
    raw = json.loads(json.dumps(BASE))
    raw.update(changes)
    return raw


class TestTopLevelValidation(unittest.TestCase):
    def test_not_a_dict_rejected(self):
        for bad in ([], "x", 3, None):
            with self.assertRaises(BoundaryError):
                _build_boundary(bad)

    def test_missing_system_name(self):
        raw = _mut()
        del raw["system_name"]
        with self.assertRaises(BoundaryError):
            _build_boundary(raw)

    def test_empty_system_name_rejected(self):
        with self.assertRaises(BoundaryError):
            _build_boundary(_mut(system_name=""))

    def test_missing_system_id(self):
        raw = _mut()
        del raw["system_id"]
        with self.assertRaises(BoundaryError):
            _build_boundary(raw)

    def test_missing_impact(self):
        raw = _mut()
        del raw["impact"]
        with self.assertRaises(BoundaryError):
            _build_boundary(raw)

    def test_impact_case_insensitive(self):
        b = _build_boundary(_mut(impact="MODERATE"))
        self.assertEqual(b.impact, "moderate")

    def test_impact_low_moderate_high_all_valid(self):
        for imp in ("low", "moderate", "high"):
            b = _build_boundary(_mut(impact=imp))
            self.assertEqual(b.impact, imp)

    def test_impact_invalid_value(self):
        for bad in ("medium", "severe", "critical", "unknown", ""):
            with self.assertRaises(BoundaryError):
                _build_boundary(_mut(impact=bad))

    def test_error_message_names_missing_field(self):
        raw = _mut()
        del raw["impact"]
        try:
            _build_boundary(raw)
            self.fail("expected BoundaryError")
        except BoundaryError as exc:
            self.assertIn("impact", str(exc))


class TestComponentValidation(unittest.TestCase):
    def test_components_must_be_present(self):
        with self.assertRaises(BoundaryError):
            _build_boundary(_mut(components=[]))

    def test_components_must_be_a_list(self):
        with self.assertRaises(BoundaryError):
            _build_boundary(_mut(components={"id": "a"}))

    def test_component_not_a_dict(self):
        with self.assertRaises(BoundaryError):
            _build_boundary(_mut(components=["a", "b"]))

    def test_component_missing_id(self):
        with self.assertRaises(BoundaryError):
            _build_boundary(_mut(components=[{"name": "no id"}]))

    def test_component_empty_id(self):
        with self.assertRaises(BoundaryError):
            _build_boundary(_mut(components=[{"id": ""}]))

    def test_duplicate_component_id(self):
        dup = [{"id": "a", "zone": "boundary"}, {"id": "a", "zone": "internal"}]
        with self.assertRaises(BoundaryError):
            _build_boundary(_mut(components=dup))

    def test_bad_zone_rejected(self):
        comps = [{"id": "a", "zone": "dmz"}]
        with self.assertRaises(BoundaryError):
            _build_boundary(_mut(components=comps))

    def test_all_valid_zones_accepted(self):
        for zone in ("boundary", "internal", "external"):
            comps = [{"id": "a", "zone": zone, "controls": []}]
            b = _build_boundary(_mut(components=comps))
            self.assertEqual(b.components[0]["zone"], zone)

    def test_zone_defaults_to_internal(self):
        comps = [{"id": "a", "controls": []}]
        b = _build_boundary(_mut(components=comps))
        # in_boundary treats a missing zone as internal (in boundary)
        self.assertTrue(b.in_boundary("a"))

    def test_controls_must_be_a_list(self):
        comps = [{"id": "a", "zone": "boundary", "controls": "AC-2"}]
        with self.assertRaises(BoundaryError):
            _build_boundary(_mut(components=comps))

    def test_controls_optional(self):
        comps = [{"id": "a", "zone": "boundary"}]
        b = _build_boundary(_mut(components=comps))
        self.assertEqual(b.components[0].get("controls", []), [])


class TestFlowValidation(unittest.TestCase):
    def test_flows_must_be_a_list(self):
        with self.assertRaises(BoundaryError):
            _build_boundary(_mut(flows={"from": "a", "to": "b"}))

    def test_flow_not_a_dict(self):
        with self.assertRaises(BoundaryError):
            _build_boundary(_mut(flows=["a->b"]))

    def test_flow_missing_from(self):
        with self.assertRaises(BoundaryError):
            _build_boundary(_mut(flows=[{"to": "a"}]))

    def test_flow_missing_to(self):
        with self.assertRaises(BoundaryError):
            _build_boundary(_mut(flows=[{"from": "a"}]))

    def test_flow_empty_endpoints(self):
        with self.assertRaises(BoundaryError):
            _build_boundary(_mut(flows=[{"from": "", "to": "a"}]))

    def test_valid_flow_accepted(self):
        b = _build_boundary(
            _mut(flows=[{"from": "internet", "to": "a", "encrypted": True}])
        )
        self.assertEqual(len(b.flows), 1)


class TestPoamValidation(unittest.TestCase):
    def test_poam_must_be_a_list(self):
        with self.assertRaises(BoundaryError):
            _build_boundary(_mut(poam={"id": "P1"}))

    def test_poam_item_not_a_dict(self):
        with self.assertRaises(BoundaryError):
            _build_boundary(_mut(poam=["P1"]))

    def test_poam_bad_severity_rejected(self):
        item = [{"id": "P1", "severity": "showstopper"}]
        with self.assertRaises(BoundaryError):
            _build_boundary(_mut(poam=item))

    def test_poam_all_valid_severities(self):
        for sev in ("low", "moderate", "high", "critical"):
            item = [{"id": "P1", "severity": sev, "status": "open"}]
            b = _build_boundary(_mut(poam=item))
            self.assertEqual(len(b.poam), 1)

    def test_poam_severity_case_insensitive(self):
        item = [{"id": "P1", "severity": "HIGH", "status": "open"}]
        b = _build_boundary(_mut(poam=item))
        self.assertEqual(len(b.poam), 1)

    def test_poam_severity_defaults_to_moderate(self):
        item = [{"id": "P1", "status": "open"}]
        b = _build_boundary(_mut(poam=item))
        self.assertEqual(len(b.poam), 1)


class TestLoadBoundaryFile(unittest.TestCase):
    def _write(self, text):
        fh = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        fh.write(text)
        fh.close()
        self.addCleanup(os.unlink, fh.name)
        return fh.name

    def test_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            load_boundary(os.path.join(tempfile.gettempdir(), "nope-xyz.json"))

    def test_malformed_json_raises(self):
        path = self._write("{ not valid json ]")
        with self.assertRaises(json.JSONDecodeError):
            load_boundary(path)

    def test_valid_file_loads(self):
        path = self._write(json.dumps(BASE))
        b = load_boundary(path)
        self.assertEqual(b.system_id, "FR-BASE")

    def test_json_array_top_level_rejected(self):
        path = self._write("[]")
        with self.assertRaises(BoundaryError):
            load_boundary(path)


class TestDirectDataclassHardening(unittest.TestCase):
    """A Boundary built directly (public API) bypasses _build_boundary;
    analyze_boundary must not leak raw KeyErrors on odd values."""

    def test_uppercase_impact_normalized(self):
        b = Boundary("X", "Y", "HIGH", [{"id": "a", "zone": "boundary"}], [], [])
        s = analyze_boundary(b)
        self.assertEqual(s["impact"], "high")
        self.assertEqual(s["baseline_controls"], 410)

    def test_out_of_range_impact_raises_boundaryerror(self):
        b = Boundary("X", "Y", "medium", [{"id": "a", "zone": "boundary"}], [], [])
        with self.assertRaises(BoundaryError):
            analyze_boundary(b)

    def test_unknown_severity_weighted_as_moderate(self):
        b = Boundary(
            "X", "Y", "low", [{"id": "a", "zone": "boundary"}], [],
            [{"id": "P1", "severity": "bogus", "status": "open"}],
        )
        s = analyze_boundary(b)
        self.assertEqual(s["poam_risk_score"], 2)  # moderate weight

    def test_none_controls_do_not_crash(self):
        b = Boundary(
            "X", "Y", "low",
            [{"id": "a", "zone": "boundary", "controls": None}], [], [],
        )
        s = analyze_boundary(b)
        self.assertEqual(s["controls_implemented"], 0)

    def test_component_helpers(self):
        b = Boundary(
            "X", "Y", "low",
            [{"id": "a", "zone": "boundary"}, {"id": "e", "zone": "external"}],
            [], [],
        )
        self.assertEqual(b.component_ids(), {"a", "e"})
        self.assertTrue(b.in_boundary("a"))
        self.assertFalse(b.in_boundary("e"))
        self.assertFalse(b.in_boundary("unknown"))


if __name__ == "__main__":
    unittest.main()
