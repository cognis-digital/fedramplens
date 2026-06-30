"""Scenario 3 - boundary map + crossing analysis.

Audience: cloud platform / infrastructure engineers.

The engineer's question is architectural: what is inside the authorization
boundary, what external dependencies does it touch, and which data flows cross
the boundary without encryption? This scenario renders the bundled boundary as
both a Mermaid diagram (drawn inline by GitHub) and Graphviz DOT, then uses the
real analyzer to call out boundary-creep: production data leaving to an
external commercial service, and any unencrypted crossing (an SC-8 gap an
engineer fixes in the network config).
"""
from _common import load, rule, bullet, boundary_to_mermaid
from fedramplens.core import analyze_boundary, generate_dot


def main() -> None:
    rule("BOUNDARY MAP  -  the architecture view for a platform engineer")

    b = load("boundary_creep")
    s = analyze_boundary(b)

    in_b = [c["id"] for c in b.components if c.get("zone") != "external"]
    print(f"\nSystem: {b.system_name} ({b.system_id}), {b.impact.upper()} impact")
    print(f"In-boundary components : {', '.join(in_b)}")
    print(f"External dependencies  : {', '.join(s['external_dependencies'])}")
    print(f"Data flows             : {s['flows']}")

    print("\n--- Mermaid (paste into a GitHub README / issue to render) ---\n")
    print("```mermaid")
    print(boundary_to_mermaid(b))
    print("```")

    print("\n--- Graphviz DOT (real generate_dot output; pipe to `dot -Tsvg`) ---\n")
    dot = generate_dot(b)
    # Print a trimmed head so the demo stays readable; note the full length.
    head = "\n".join(dot.splitlines()[:12])
    print(head)
    print(f"   ... ({len(dot.splitlines())} lines of DOT total)")

    rule("BOUNDARY-CROSSING FINDINGS  -  what to fix in the network config")
    crossings = [f for f in s["findings"]
                 if f["type"] == "unencrypted_boundary_crossing"]
    creep = [c for c in b.components if c.get("zone") == "external"]
    print(f"\nExternal services receiving traffic from inside the boundary:")
    for c in creep:
        bullet(f"{c['name']} ({c['id']}) — outside the authorization boundary")
    if crossings:
        print("\nUnencrypted boundary crossings (SC-8 — encrypt these):")
        for f in crossings:
            bullet(f"({f['severity']}) {f['detail']}")
    else:
        print("\nNo unencrypted boundary crossings — every crossing is encrypted.")

    print(f"\nAuthorization-ready: "
          f"{'YES' if s['authorization_ready'] else 'NO'} "
          "(an engineer flips this by encrypting the flagged flow).")


if __name__ == "__main__":
    main()
