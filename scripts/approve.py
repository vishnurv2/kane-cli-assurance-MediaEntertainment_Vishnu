#!/usr/bin/env python3
"""Build a kane-cli verdicts file from the live context graph.

Node ids are not stable between runs, so never hardcode uc-1. This reads
`kane-cli context list --json` output on stdin and emits the verdicts shape
`context review --verdicts` expects.

Usage:
    kane-cli context list --json --inferred | \
        python3 scripts/approve.py --types usecase > verdicts/usecases.json

The reason string is written into the audit trail, so it is worth making it
say something true. "Auto-approved in CI" is true. "Reviewed by a human" is
not, and the graph keeps it forever.
"""

from __future__ import annotations

import argparse
import json
import sys


def walk(node, types, out):
    """Collect refs of matching type from whatever shape came back.

    `context list --json` emits one node per line as
    {"id", "cid", "label", "title", "trust", "fresh"} -- the node type lives in
    `label`, and the addressable ref in `id`. Older/other shapes used
    type/kind/ref, so accept all of them.
    """
    if isinstance(node, dict):
        ref = node.get("ref") or node.get("id")
        kind = (node.get("label") or node.get("type")
                or node.get("kind") or "").lower()
        if ref and kind in types:
            out.setdefault(ref, kind)
        for value in node.values():
            walk(value, types, out)
    elif isinstance(node, list):
        for item in node:
            walk(item, types, out)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--types",
        default="usecase",
        help="comma separated node types to approve, e.g. ac,scenario,test",
    )
    parser.add_argument(
        "--reason",
        default="Auto-approved by CI. Source documents were reviewed in the pull "
                "request that introduced them; this run does not add human judgement.",
    )
    parser.add_argument(
        "--allow-empty",
        action="store_true",
        help="exit 0 when the queue holds no node of the requested type",
    )
    args = parser.parse_args()

    types = {t.strip().lower() for t in args.types.split(",") if t.strip()}

    raw = sys.stdin.read().strip()
    if not raw:
        print("[]")
        print("error: context list produced no output at all", file=sys.stderr)
        return 0 if args.allow_empty else 1

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Some builds stream NDJSON. Take whatever lines parse.
        data = []
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    found: dict[str, str] = {}
    walk(data, types, found)

    verdicts = [
        {"ref": ref, "resolution": "approved", "reason": args.reason}
        for ref in sorted(found)
    ]
    print(json.dumps(verdicts, indent=2))
    print(f"approved {len(verdicts)} node(s) of type {sorted(types)}",
          file=sys.stderr)

    # An empty verdicts file is not an error to `context review` -- it prints
    # "nothing changed" and exits 0. That is exactly how a checkpoint silently
    # approves nothing and the run goes green with an empty graph, so refuse.
    if not verdicts and not args.allow_empty:
        print(f"error: no nodes of type {sorted(types)} in the review queue. "
              f"Expected the previous stage to have produced some; pass "
              f"--allow-empty if an empty queue is legitimate here.",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
