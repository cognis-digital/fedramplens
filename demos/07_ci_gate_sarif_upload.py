"""Scenario 7 - CI/CD gate that fails the build on blocking findings.

Audience: DevSecOps / platform CI owners.

Wire fedramplens into a pipeline: analyze the boundary, emit SARIF for the
code-scanning dashboard, and fail the job (non-zero) when the package is not
authorization-ready. This scenario mimics that gate exactly -- it computes the
process exit code the CLI would return and shows the SARIF artifact the step
would upload -- without actually calling sys.exit, so it stays runnable.
"""
import json

from _common import load, rule, bullet
from fedramplens.core import analyze_boundary, to_sarif


def _gate(key):
    s = analyze_boundary(load(key))
    sarif = to_sarif(s)
    # This is the exact rule the CLI applies: exit 1 unless ready.
    exit_code = 0 if s["authorization_ready"] else 1
    return s, sarif, exit_code


def main() -> None:
    rule("CI GATE  -  fail the build on blocking FedRAMP findings")

    for key in ("clean_low", "boundary_creep"):
        s, sarif, code = _gate(key)
        errors = sum(1 for r in sarif["runs"][0]["results"]
                     if r["level"] == "error")
        print(f"\n  step: fedramplens analyze {key}")
        bullet(f"authorization-ready : {s['authorization_ready']}")
        bullet(f"SARIF error results : {errors} (uploaded to code-scanning)")
        bullet(f"process exit code   : {code} "
               f"({'build FAILS' if code else 'build passes'})")

    rule("SARIF ARTIFACT (what the upload step ships)")
    _, sarif, _ = _gate("boundary_creep")
    blob = json.dumps(sarif)
    print(f"\n  sarif log: {len(blob)} bytes, "
          f"{len(sarif['runs'][0]['results'])} results, valid JSON")
    assert json.loads(blob)["version"] == "2.1.0"
    bullet("round-trips cleanly -> ready for actions/upload-sarif")
    print("\nDrop this into a workflow step to enforce ATO readiness pre-merge.")


if __name__ == "__main__":
    main()
