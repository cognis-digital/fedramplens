"""Scenario 10 - external-dependency inventory (leveraged / interconnections).

Audience: ISSOs / architects documenting the boundary.

FedRAMP requires every external service and interconnection to be inventoried.
This scenario walks a system with several external dependencies, lists each
one outside the authorization boundary, and shows which data flows cross to
them and whether those crossings are encrypted -- the raw material for the
CIS/interconnection tables in an SSP.
"""
from _common import load, rule, bullet
from fedramplens.core import analyze_boundary


def main() -> None:
    rule("EXTERNAL DEPENDENCY INVENTORY  -  what leaves the boundary")

    b = load("multi_external")
    s = analyze_boundary(b)
    ext = {c["id"]: c for c in b.components if c.get("zone") == "external"}

    print(f"\nSystem: {b.system_name} ({b.system_id}), {b.impact.upper()} impact")
    print(f"External dependencies: {len(ext)}")
    for cid, c in ext.items():
        bullet(f"{c.get('name', cid)} ({cid}) [type={c.get('type', '?')}]")

    rule("CROSSING FLOWS (source -> external dependency)")
    for fl in b.flows:
        if fl["to"] in ext or fl["from"] in ext:
            enc = "encrypted" if fl.get("encrypted") else "UNENCRYPTED"
            bullet(f"{fl['from']} -> {fl['to']}  [{fl.get('data', '?')}] {enc}")

    unenc = [f for f in s["findings"]
             if f["type"] == "unencrypted_boundary_crossing"]
    rule("SC-8 GAPS ON EXTERNAL CROSSINGS")
    if unenc:
        for f in unenc:
            bullet(f"({f['severity']}) {f['detail']}")
    else:
        bullet("none -- every external crossing is encrypted")

    print(f"\nInventory feeds the SSP interconnection table; "
          f"{len(unenc)} crossing(s) need encryption before ATO.")


if __name__ == "__main__":
    main()
