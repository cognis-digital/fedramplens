"""Scenario 17 - boundary diagram in multiple export formats.

Audience: architects producing SSP diagrams.

The authorization-boundary diagram is a required SSP artifact. This scenario
renders the same boundary as both Graphviz DOT (pipe to `dot -Tsvg` for the
SSP) and a Mermaid flowchart (renders inline in GitHub/GitLab), and highlights
how each format visually distinguishes encrypted vs unencrypted crossings and
in-boundary vs external components.
"""
from _common import load, rule, bullet, boundary_to_mermaid
from fedramplens.core import generate_dot


def main() -> None:
    rule("DIAGRAM EXPORT  -  DOT + Mermaid for the SSP boundary figure")

    b = load("basic")
    dot = generate_dot(b)
    mer = boundary_to_mermaid(b)

    in_b = [c["id"] for c in b.components if c.get("zone") != "external"]
    ext = [c["id"] for c in b.components if c.get("zone") == "external"]
    print(f"\nSystem: {b.system_name} ({b.system_id})")
    bullet(f"in-boundary : {', '.join(in_b)}")
    bullet(f"external    : {', '.join(ext)}")

    rule("GRAPHVIZ DOT  (pipe to: dot -Tsvg -o boundary.svg)")
    print()
    for line in dot.splitlines()[:14]:
        print("  " + line)
    print(f"  ... ({len(dot.splitlines())} lines total)")
    bullet(f"unencrypted crossings drawn red: {'color=red' in dot}")
    bullet(f"cluster subgraph for boundary  : {'cluster_boundary' in dot}")

    rule("MERMAID  (paste into a GitHub issue/README to render)")
    print("\n```mermaid")
    print(mer)
    print("```")
    bullet(f"dotted UNENCRYPTED edges present: {'-.->' in mer}")
    bullet(f"authorization-boundary subgraph : "
           f"{'Authorization Boundary' in mer}")

    print("\nSame boundary, two renderers -- one for the SSP, one for the repo.")


if __name__ == "__main__":
    main()
