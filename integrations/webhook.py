#!/usr/bin/env python3
"""Minimal, dependency-free webhook forwarder for Cognis findings.

Reads JSON findings on stdin and POSTs them to a URL (SIEM/Slack/Jira bridge).
Usage:  <tool> scan . --format json | python integrations/webhook.py --url URL
"""
from __future__ import annotations

import argparse
import sys
import urllib.error
import urllib.request


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Forward JSON findings from stdin to a webhook URL.",
    )
    ap.add_argument("--url", required=True, help="Destination URL (http/https)")
    ap.add_argument("--header", action="append", default=[], help="'Key: Value' header")
    args = ap.parse_args()

    # Validate URL scheme before attempting any I/O.
    url: str = args.url.strip()
    if not url.startswith(("http://", "https://")):
        print(
            f"error: --url must start with http:// or https://, got {url!r}",
            file=sys.stderr,
        )
        return 2

    # Parse custom headers; skip malformed ones with a warning.
    headers: list[tuple[str, str]] = []
    for h in args.header:
        if ":" not in h:
            print(
                f"warning: ignoring malformed header (no colon): {h!r}",
                file=sys.stderr,
            )
            continue
        k, _, v = h.partition(":")
        k, v = k.strip(), v.strip()
        if not k:
            print(f"warning: ignoring header with empty name: {h!r}", file=sys.stderr)
            continue
        headers.append((k, v))

    payload = sys.stdin.buffer.read()
    if not payload:
        print(
            "error: no input on stdin — pipe JSON findings to this command",
            file=sys.stderr,
        )
        return 2

    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    for k, v in headers:
        req.add_header(k, v)

    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            print(f"posted {len(payload)} bytes -> {r.status}")
        return 0
    except urllib.error.HTTPError as exc:
        print(f"webhook error: HTTP {exc.code} {exc.reason}", file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"webhook error: {exc.reason}", file=sys.stderr)
        return 1
    except TimeoutError:
        print("webhook error: request timed out", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"webhook error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
