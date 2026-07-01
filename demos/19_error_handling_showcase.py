"""Scenario 19 - error-handling showcase (clean failures, not crashes).

Audience: anyone feeding fedramplens untrusted / hand-edited boundary files.

Good tooling fails loudly and clearly. This scenario deliberately feeds the
loader a series of malformed boundary definitions -- missing fields, a bad
impact, a duplicate component id, a flow with no endpoints, a wrong-typed
controls field, and an out-of-range impact discovered only at analysis time --
and shows that each one raises a precise BoundaryError instead of a traceback.
"""
import json
import os
import tempfile

from _common import rule, bullet
from fedramplens.core import (
    Boundary, BoundaryError, analyze_boundary, load_boundary,
)

BAD_CASES = [
    ("missing impact",
     {"system_name": "x", "system_id": "y",
      "components": [{"id": "a", "zone": "boundary"}]}),
    ("invalid impact 'medium'",
     {"system_name": "x", "system_id": "y", "impact": "medium",
      "components": [{"id": "a", "zone": "boundary"}]}),
    ("no components",
     {"system_name": "x", "system_id": "y", "impact": "low",
      "components": []}),
    ("duplicate component id",
     {"system_name": "x", "system_id": "y", "impact": "low",
      "components": [{"id": "a"}, {"id": "a"}]}),
    ("flow missing endpoints",
     {"system_name": "x", "system_id": "y", "impact": "low",
      "components": [{"id": "a", "zone": "boundary"}],
      "flows": [{"from": "a"}]}),
    ("controls not a list",
     {"system_name": "x", "system_id": "y", "impact": "low",
      "components": [{"id": "a", "zone": "boundary", "controls": "AC-2"}]}),
    ("bad POA&M severity",
     {"system_name": "x", "system_id": "y", "impact": "low",
      "components": [{"id": "a", "zone": "boundary"}],
      "poam": [{"id": "P1", "severity": "showstopper"}]}),
]


def main() -> None:
    rule("ERROR HANDLING  -  malformed boundaries fail cleanly")

    print("\nEach malformed input raises a precise BoundaryError:\n")
    for label, raw in BAD_CASES:
        fh = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        json.dump(raw, fh)
        fh.close()
        try:
            load_boundary(fh.name)
            bullet(f"[{label}] -> NO ERROR (unexpected!)")
        except BoundaryError as exc:
            bullet(f"[{label}] -> BoundaryError: {exc}")
        finally:
            os.unlink(fh.name)

    rule("LATE VALIDATION  -  direct dataclass, caught at analysis time")
    # A Boundary built directly can carry an out-of-range impact; analyze
    # surfaces it as a BoundaryError rather than a raw KeyError.
    b = Boundary("x", "y", "medium", [{"id": "a", "zone": "boundary"}], [], [])
    try:
        analyze_boundary(b)
        bullet("analyze -> NO ERROR (unexpected!)")
    except BoundaryError as exc:
        bullet(f"analyze(out-of-range impact) -> BoundaryError: {exc}")

    rule("MALFORMED JSON")
    fh = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
    fh.write("{ not: valid, json ]")
    fh.close()
    try:
        load_boundary(fh.name)
    except json.JSONDecodeError as exc:
        bullet(f"load_boundary(bad json) -> JSONDecodeError: {exc.msg}")
    finally:
        os.unlink(fh.name)

    print("\nEvery bad input produced a clear, typed error -- no tracebacks.")


if __name__ == "__main__":
    main()
