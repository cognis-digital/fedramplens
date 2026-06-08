"""FEDRAMPLENS - FedRAMP boundary visualizer & OSCAL-format SSP/POAM generator.

Reads a simple JSON description of an authorization boundary (components, data
flows, control implementations, weaknesses) and produces:

  * a boundary diagram (Graphviz DOT) you can render or paste into draw.io,
  * an OSCAL-style System Security Plan (SSP) skeleton,
  * an OSCAL-style Plan of Action & Milestones (POA&M),
  * a control-coverage and boundary-integrity analysis.

In the spirit of GSA/fedramp-automation, but dependency-free (stdlib only).
"""
from .core import (
    Boundary,
    load_boundary,
    analyze_boundary,
    generate_dot,
    generate_ssp,
    generate_poam,
)

TOOL_NAME = "fedramplens"
TOOL_VERSION = "1.0.0"

__all__ = [
    "TOOL_NAME",
    "TOOL_VERSION",
    "Boundary",
    "load_boundary",
    "analyze_boundary",
    "generate_dot",
    "generate_ssp",
    "generate_poam",
]
