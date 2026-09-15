#!/usr/bin/env python3
"""Summarise `kane-cli evidence validate --json` for the GitHub job summary.

Validating the MERGED pack is the only check that sees packs in relation to one
another, so its diagnostics are worth printing in full rather than reducing to a
valid/invalid bit.
"""

from __future__ import annotations

import json
import sys


def main() -> int:
    try:
        raw = open(sys.argv[1], encoding="utf-8", errors="ignore").read()
    except (IndexError, OSError):
        print("merged pack L1           : could not read validate output")
        return 0

    # the CLI prefixes an update banner on stdout sometimes; take the last JSON line
    lines = [l for l in raw.splitlines() if l.strip().startswith("{")]
    if not lines:
        print("merged pack L1           : no JSON in validate output")
        return 0

    try:
        doc = json.loads(lines[-1])
    except json.JSONDecodeError:
        print("merged pack L1           : validate output was not valid JSON")
        return 0

    verdict = "valid" if doc.get("valid") else "INVALID"
    print(f"merged pack L1           : {verdict} ({doc.get('status', '?')})")

    diagnostics = doc.get("diagnostics") or []
    if not diagnostics:
        print("diagnostics              : none")
        return 0

    print(f"diagnostics              : {len(diagnostics)}")
    for d in diagnostics:
        code = d.get("code", "?")
        sev = d.get("severity", "?")
        msg = str(d.get("message", ""))[:90]
        print(f"  [{sev}] {code}: {msg}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
