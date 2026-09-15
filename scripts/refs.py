#!/usr/bin/env python3
"""Print use-case refs from `kane-cli context list --json` on stdin.

Ids are not stable between runs, so the pipeline always asks the graph rather
than assuming uc-1 means the same thing twice.
"""

from __future__ import annotations

import json
import re
import sys


def main() -> int:
    raw = sys.stdin.read().strip()
    if not raw:
        return 0

    prefix = sys.argv[1] if len(sys.argv) > 1 else "uc-"

    try:
        blob = json.dumps(json.loads(raw))
    except json.JSONDecodeError:
        blob = raw

    pattern = r'"(?:ref|id)"\s*:\s*"(' + re.escape(prefix) + r'[^"]+)"'
    refs = sorted(set(re.findall(pattern, blob)))
    print(" ".join(refs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
