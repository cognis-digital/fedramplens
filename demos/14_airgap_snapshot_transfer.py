"""Scenario 14 - air-gap snapshot transfer of the OSCAL catalog.

Audience: teams operating disconnected / classified enclaves.

An air-gapped enclave has no path to NIST's OSCAL content. This scenario shows
the sneakernet workflow: export the cached OSCAL 800-53 catalog to a portable
tarball, import it into a *fresh, empty* cache (simulating the enclave), and
then resolve control titles there with offline=True -- proving enrichment
works with zero network once the snapshot has crossed the gap.
"""
import os
import tempfile

from _common import rule, bullet, use_offline_feed_cache
from fedramplens import controls, datafeeds

FEED = "oscal-800-53-rev5-catalog"


def main() -> None:
    rule("AIR-GAP SNAPSHOT  -  sneakernet the OSCAL catalog across the gap")

    # Source side: the connected cache holding the catalog.
    use_offline_feed_cache()
    src = os.environ["COGNIS_FEEDS_CACHE"]
    print(f"\nSource cache (connected side): {src}")
    bullet(f"catalog cached: {datafeeds.cached_age_hours(FEED) is not None}")

    # Export to a portable archive.
    tmp = tempfile.mkdtemp(prefix="fedramplens_airgap_")
    archive = os.path.join(tmp, "oscal-feeds.tar.gz")
    n = datafeeds.snapshot_export(archive)
    bullet(f"exported {n} feed(s) -> {os.path.basename(archive)} "
           f"({os.path.getsize(archive)} bytes)")

    # Enclave side: a fresh empty cache with no network.
    rule("INSIDE THE ENCLAVE  -  fresh empty cache, no network")
    enclave = tempfile.mkdtemp(prefix="fedramplens_enclave_")
    os.environ["COGNIS_FEEDS_CACHE"] = enclave
    controls.reset_cache()
    print(f"\nEnclave cache: {enclave}")
    print(f"Before import, control_title('SC-8', offline) = "
          f"{controls.control_title('SC-8', offline=True)!r}  (nothing cached)")

    imported = datafeeds.snapshot_import(archive)
    controls.reset_cache()
    bullet(f"imported {imported} feed(s) from the tarball")
    title = controls.control_title("SC-8", offline=True)
    bullet(f"after import, control_title('SC-8', offline) = {title!r}")
    assert title == "Transmission Confidentiality and Integrity"

    # restore the working cache for any later demo in the same process
    use_offline_feed_cache()
    print("\nOSCAL enrichment now works fully offline inside the enclave.")


if __name__ == "__main__":
    main()
