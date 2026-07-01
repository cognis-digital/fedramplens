"""Scenario 13 - JSON output as a pipeline integration point.

Audience: tooling / integration engineers.

fedramplens's --format json is a stable machine contract. This scenario runs
the CLI in-process, captures the JSON, and shows how downstream tooling would
consume it: pull the top-level posture keys, filter findings by severity, and
confirm the exit code matches the authorization-ready verdict. No shelling out
-- it calls the real CLI main() and parses its stdout.
"""
import contextlib
import io
import json

from _common import fixture_path, rule, bullet
from fedramplens.cli import main as cli_main


def _analyze_json(path):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = cli_main(["--format", "json", "analyze", path])
    return code, json.loads(buf.getvalue())


def main() -> None:
    rule("JSON PIPELINE  -  consume fedramplens output downstream")

    path = fixture_path("boundary_creep")
    code, data = _analyze_json(path)

    print(f"\nCLI exit code : {code} "
          f"(0=ready, 1=blocking findings)")
    print("Top-level posture keys a pipeline reads:")
    for key in ("system_id", "impact", "coverage_pct", "poam_risk_score",
                "authorization_ready"):
        bullet(f"{key:20} = {data[key]}")

    # Contract check: exit code agrees with the ready flag.
    assert code == (0 if data["authorization_ready"] else 1)
    bullet("exit code matches authorization_ready (contract holds)")

    rule("FILTER FINDINGS BY SEVERITY (downstream triage)")
    for sev in ("critical", "high", "moderate", "low"):
        hits = [f for f in data["findings"] if f["severity"] == sev]
        if hits:
            print(f"  {sev.upper()} ({len(hits)}):")
            for f in hits:
                ctl = f.get("control", "-")
                bullet(f"[{ctl}] {f['type']}: {f['detail']}")

    print("\nThe JSON is the integration seam -- stable keys, no scraping text.")


if __name__ == "__main__":
    main()
