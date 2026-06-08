"""Core engine for FEDRAMPLENS.

No third-party dependencies. The boundary input format (JSON):

{
  "system_name": "Example SaaS",
  "system_id": "FR2026XXXX",
  "impact": "moderate",            # low | moderate | high
  "components": [
    {"id": "web", "name": "Web Tier", "type": "service",
     "zone": "boundary", "controls": ["AC-2", "SC-7"]}
  ],
  "flows": [
    {"from": "internet", "to": "web", "data": "HTTPS", "encrypted": true}
  ],
  "poam": [
    {"id": "V-001", "weakness": "...", "control": "SC-13",
     "severity": "high", "status": "open", "scheduled": "2026-09-30"}
  ]
}

A component with zone == "external" sits outside the authorization boundary;
any flow that crosses the boundary unencrypted is flagged.
"""
from __future__ import annotations

import json
import datetime
from dataclasses import dataclass, field
from typing import Any, Dict, List

# FedRAMP baseline control counts (Rev 5) used for coverage estimates.
BASELINE_CONTROL_COUNTS = {"low": 156, "moderate": 323, "high": 410}

VALID_IMPACTS = ("low", "moderate", "high")
VALID_ZONES = ("boundary", "internal", "external")
VALID_SEVERITIES = ("low", "moderate", "high", "critical")


class BoundaryError(ValueError):
    """Raised when the boundary definition is invalid."""


@dataclass
class Boundary:
    system_name: str
    system_id: str
    impact: str
    components: List[Dict[str, Any]] = field(default_factory=list)
    flows: List[Dict[str, Any]] = field(default_factory=list)
    poam: List[Dict[str, Any]] = field(default_factory=list)

    def component_ids(self) -> set:
        return {c["id"] for c in self.components}

    def in_boundary(self, comp_id: str) -> bool:
        for c in self.components:
            if c["id"] == comp_id:
                return c.get("zone", "internal") != "external"
        # Unknown endpoints (e.g. "internet") are external by definition.
        return False


def load_boundary(path: str) -> Boundary:
    """Load and validate a boundary definition from a JSON file."""
    with open(path, "r", encoding="utf-8") as fh:
        raw = json.load(fh)
    return _build_boundary(raw)


def _build_boundary(raw: Dict[str, Any]) -> Boundary:
    if not isinstance(raw, dict):
        raise BoundaryError("boundary definition must be a JSON object")
    for key in ("system_name", "system_id", "impact"):
        if not raw.get(key):
            raise BoundaryError(f"missing required field: {key}")
    impact = str(raw["impact"]).lower()
    if impact not in VALID_IMPACTS:
        raise BoundaryError(
            f"impact must be one of {VALID_IMPACTS}, got {impact!r}"
        )

    components = raw.get("components", [])
    if not isinstance(components, list) or not components:
        raise BoundaryError("at least one component is required")
    seen = set()
    for c in components:
        cid = c.get("id")
        if not cid:
            raise BoundaryError("component missing 'id'")
        if cid in seen:
            raise BoundaryError(f"duplicate component id: {cid}")
        seen.add(cid)
        zone = c.get("zone", "internal")
        if zone not in VALID_ZONES:
            raise BoundaryError(
                f"component {cid}: zone must be one of {VALID_ZONES}"
            )

    flows = raw.get("flows", [])
    if not isinstance(flows, list):
        raise BoundaryError("'flows' must be a list")
    for f in flows:
        if not f.get("from") or not f.get("to"):
            raise BoundaryError("each flow needs 'from' and 'to'")

    poam = raw.get("poam", [])
    if not isinstance(poam, list):
        raise BoundaryError("'poam' must be a list")
    for p in poam:
        sev = str(p.get("severity", "moderate")).lower()
        if sev not in VALID_SEVERITIES:
            raise BoundaryError(
                f"POA&M {p.get('id')}: severity must be one of {VALID_SEVERITIES}"
            )

    return Boundary(
        system_name=str(raw["system_name"]),
        system_id=str(raw["system_id"]),
        impact=impact,
        components=components,
        flows=flows,
        poam=poam,
    )


def analyze_boundary(b: Boundary) -> Dict[str, Any]:
    """Run boundary-integrity and control-coverage analysis."""
    findings: List[Dict[str, Any]] = []
    comp_ids = b.component_ids()

    # 1. Flows that reference unknown components.
    for fl in b.flows:
        for end in ("from", "to"):
            ref = fl[end]
            if ref not in comp_ids and not _is_external_token(ref):
                findings.append({
                    "severity": "moderate",
                    "type": "dangling_flow",
                    "detail": f"flow {fl['from']}->{fl['to']} references "
                              f"undefined component {ref!r}",
                })

    # 2. Unencrypted flows crossing the authorization boundary (SC-8/SC-13).
    for fl in b.flows:
        crosses = b.in_boundary(fl["from"]) != b.in_boundary(fl["to"])
        if crosses and not fl.get("encrypted", False):
            findings.append({
                "severity": "high",
                "type": "unencrypted_boundary_crossing",
                "control": "SC-8",
                "detail": f"flow {fl['from']}->{fl['to']} ({fl.get('data','?')}) "
                          "crosses the boundary without encryption",
            })

    # 3. Orphan components (in boundary but no flows touch them).
    touched = set()
    for fl in b.flows:
        touched.add(fl["from"])
        touched.add(fl["to"])
    for c in b.components:
        if c.get("zone") != "external" and c["id"] not in touched:
            findings.append({
                "severity": "low",
                "type": "orphan_component",
                "detail": f"component {c['id']} has no data flows defined",
            })

    # 4. Control coverage estimate vs FedRAMP baseline.
    implemented = set()
    for c in b.components:
        for ctl in c.get("controls", []):
            implemented.add(_normalize_control(ctl))
    baseline = BASELINE_CONTROL_COUNTS[b.impact]
    coverage_pct = round(100.0 * len(implemented) / baseline, 1)

    # 5. POA&M risk roll-up + overdue detection.
    today = datetime.date.today()
    sev_weight = {"low": 1, "moderate": 2, "high": 4, "critical": 8}
    risk_score = 0
    overdue = []
    open_items = 0
    for p in b.poam:
        if str(p.get("status", "open")).lower() == "open":
            open_items += 1
            risk_score += sev_weight[str(p.get("severity", "moderate")).lower()]
            sched = p.get("scheduled")
            if sched:
                try:
                    if datetime.date.fromisoformat(sched) < today:
                        overdue.append(p.get("id"))
                except ValueError:
                    findings.append({
                        "severity": "low",
                        "type": "bad_poam_date",
                        "detail": f"POA&M {p.get('id')}: invalid date {sched!r}",
                    })
    for oid in overdue:
        findings.append({
            "severity": "high",
            "type": "overdue_poam",
            "detail": f"POA&M {oid} milestone is past its scheduled date",
        })

    external = [c["id"] for c in b.components if c.get("zone") == "external"]
    in_boundary = [c["id"] for c in b.components if c.get("zone") != "external"]

    summary = {
        "system_name": b.system_name,
        "system_id": b.system_id,
        "impact": b.impact,
        "baseline_controls": baseline,
        "controls_implemented": len(implemented),
        "coverage_pct": coverage_pct,
        "components_in_boundary": len(in_boundary),
        "external_dependencies": external,
        "flows": len(b.flows),
        "poam_open": open_items,
        "poam_overdue": overdue,
        "poam_risk_score": risk_score,
        "findings": findings,
        "finding_counts": _count_by_severity(findings),
        "authorization_ready": not any(
            f["severity"] in ("high", "critical") for f in findings
        ),
    }
    return summary


def generate_dot(b: Boundary) -> str:
    """Render the authorization boundary as Graphviz DOT."""
    lines = [
        "digraph boundary {",
        "  rankdir=LR;",
        "  node [shape=box, style=rounded];",
        f'  label="{_esc(b.system_name)} ({_esc(b.system_id)}) - '
        f'{b.impact.upper()} impact";',
        "  labelloc=t;",
        "  subgraph cluster_boundary {",
        '    label="Authorization Boundary";',
        "    style=dashed; color=blue;",
    ]
    external_nodes = []
    for c in b.components:
        nid = _node_id(c["id"])
        lbl = _esc(c.get("name", c["id"]))
        if c.get("zone") == "external":
            external_nodes.append((nid, lbl))
        else:
            color = "lightblue" if c.get("zone") == "boundary" else "white"
            lines.append(
                f'    {nid} [label="{lbl}", style="rounded,filled", '
                f'fillcolor={color}];'
            )
    lines.append("  }")
    for nid, lbl in external_nodes:
        lines.append(
            f'  {nid} [label="{lbl}", shape=ellipse, '
            'style=filled, fillcolor=lightgrey];'
        )
    # Synthesize external-token nodes referenced only in flows.
    declared = b.component_ids()
    for fl in b.flows:
        for end in (fl["from"], fl["to"]):
            if end not in declared and _is_external_token(end):
                lines.append(
                    f'  {_node_id(end)} [label="{_esc(end)}", shape=ellipse, '
                    'style=filled, fillcolor=lightgrey];'
                )
                declared = declared | {end}
    for fl in b.flows:
        style = "solid" if fl.get("encrypted") else "bold"
        color = "black" if fl.get("encrypted") else "red"
        lbl = _esc(fl.get("data", ""))
        lines.append(
            f'  {_node_id(fl["from"])} -> {_node_id(fl["to"])} '
            f'[label="{lbl}", style={style}, color={color}];'
        )
    lines.append("}")
    return "\n".join(lines)


def generate_ssp(b: Boundary) -> Dict[str, Any]:
    """Build an OSCAL-style System Security Plan skeleton."""
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    components = []
    impls = []
    for c in b.components:
        components.append({
            "uuid": _uuid_like(c["id"]),
            "type": c.get("type", "software"),
            "title": c.get("name", c["id"]),
            "status": {"state": "operational"},
            "props": [{"name": "zone", "value": c.get("zone", "internal")}],
        })
        for ctl in c.get("controls", []):
            impls.append({
                "control-id": _normalize_control(ctl).lower(),
                "uuid": _uuid_like(c["id"] + ctl),
                "by-components": [{
                    "component-uuid": _uuid_like(c["id"]),
                    "uuid": _uuid_like(c["id"] + ctl + "impl"),
                    "description": f"Implemented by {c.get('name', c['id'])}.",
                }],
            })
    return {
        "system-security-plan": {
            "uuid": _uuid_like(b.system_id),
            "metadata": {
                "title": f"{b.system_name} System Security Plan",
                "last-modified": now,
                "version": "1.0.0",
                "oscal-version": "1.1.2",
            },
            "import-profile": {
                "href": f"#fedramp-{b.impact}-baseline",
            },
            "system-characteristics": {
                "system-ids": [{"id": b.system_id}],
                "system-name": b.system_name,
                "security-sensitivity-level": b.impact,
            },
            "system-implementation": {"components": components},
            "control-implementation": {
                "description": f"FedRAMP {b.impact} baseline implementation.",
                "implemented-requirements": impls,
            },
        }
    }


def generate_poam(b: Boundary) -> Dict[str, Any]:
    """Build an OSCAL-style Plan of Action & Milestones."""
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    items = []
    for p in b.poam:
        items.append({
            "uuid": _uuid_like(str(p.get("id", "poam"))),
            "title": p.get("id", "POA&M Item"),
            "description": p.get("weakness", ""),
            "props": [
                {"name": "severity", "value": str(p.get("severity", "moderate"))},
                {"name": "status", "value": str(p.get("status", "open"))},
                {"name": "control", "value": str(p.get("control", ""))},
                {"name": "scheduled-completion",
                 "value": str(p.get("scheduled", ""))},
            ],
        })
    return {
        "plan-of-action-and-milestones": {
            "uuid": _uuid_like(b.system_id + "poam"),
            "metadata": {
                "title": f"{b.system_name} POA&M",
                "last-modified": now,
                "version": "1.0.0",
                "oscal-version": "1.1.2",
            },
            "system-id": {"id": b.system_id},
            "poam-items": items,
        }
    }


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def _is_external_token(name: str) -> bool:
    return name.lower() in {
        "internet", "user", "users", "external", "saas", "public",
    }


def _normalize_control(ctl: str) -> str:
    return str(ctl).strip().upper()


def _count_by_severity(findings: List[Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for f in findings:
        counts[f["severity"]] = counts.get(f["severity"], 0) + 1
    return counts


def _esc(text: str) -> str:
    return str(text).replace('"', "'").replace("\n", " ")


def _node_id(name: str) -> str:
    out = "".join(ch if ch.isalnum() else "_" for ch in str(name))
    return "n_" + out


def _uuid_like(seed: str) -> str:
    import hashlib
    h = hashlib.sha1(seed.encode("utf-8")).hexdigest()
    return f"{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"
