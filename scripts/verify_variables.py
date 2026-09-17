#!/usr/bin/env python3
"""Assert that every filled variable is TRUE of the catalogue it came from.

A wrong value is worse than an empty one: it dispatches a test that then fails
for a reason unrelated to the requirement, and the run reports a failure that
looks like a product defect. One run shipped six such values at once - a title
said to be unlicensed in three territories it is licensed in, a "premium
required" title that only needs Standard, and an "ad supported only" title whose
flag is false.

The parsing here is written separately from `fill_variables.py` on purpose. If
both shared one parser, a parsing bug would produce a wrong value and then agree
with itself when checking it.

Run after fill_variables.py. Exits non-zero if any filled value contradicts
app/catalogue.json.
"""

from __future__ import annotations

import datetime
import json
import pathlib
import re
import sys

VARS = pathlib.Path(".testmuai/variables/assurance.json")
CATALOGUE = pathlib.Path("app/catalogue.json")
TIER_ORDER = {"Free": 0, "Standard": 1, "Premium": 2}
TERRITORIES = ("IN", "GB", "US")
TIERS = ("Free", "Standard", "Premium")


def words(name: str) -> list[str]:
    return [w for w in re.split(r"[^a-z0-9]+", name.lower()) if w]


def expected_territories(w: list[str]) -> tuple[set[str], set[str]]:
    """Territories the name says a title must be in, and must not be in."""
    must, must_not, negated = set(), set(), False
    for i, tok in enumerate(w):
        if tok in ("not", "non", "without", "outside", "unlicensed", "excluded"):
            negated = True
            continue
        if tok == "in" and i + 1 < len(w) and w[i + 1].upper() in TERRITORIES:
            continue                      # "in" as a preposition, not a code
        if tok.upper() in TERRITORIES:
            (must_not if negated else must).add(tok.upper())
            negated = False
    return must, must_not


def check(name, value, titles, today):
    """Every way this value can contradict the catalogue. Returns a list."""
    w = words(name)
    problems = []

    named = [v.strip() for v in value.split(",")] if "," in value else [value]
    known = [n for n in named if n in titles]
    if not known:
        return problems                   # not a catalogue title; nothing to check

    must, must_not = expected_territories(w)

    for n in known:
        t = titles[n]
        for terr in must:
            if terr not in t["territories"]:
                problems.append(f"{name} = {n}: not licensed in {terr} ({t['territories']})")
        for terr in must_not:
            if terr in t["territories"]:
                problems.append(f"{name} = {n}: IS licensed in {terr} ({t['territories']})")

        if "ad" in w and "supported" in w and not t.get("adSupportedOnly"):
            problems.append(f"{name} = {n}: adSupportedOnly is false")

        if any(x in w for x in ("coming", "soon", "future", "upcoming")):
            if t["windowStart"] <= today:
                problems.append(f"{name} = {n}: window opened {t['windowStart']}, not future")
        elif any(x in w for x in ("expired", "lapsed", "ended")):
            if t["windowEnd"] >= today:
                problems.append(f"{name} = {n}: window ends {t['windowEnd']}, not expired")

        tier = next((x.capitalize() for x in w if x.capitalize() in TIERS), None)
        if tier and any(x in w for x in ("required", "requires", "only", "minimum")):
            if t["minTier"] != tier:
                problems.append(f"{name} = {n}: minTier is {t['minTier']}, not {tier}")
        elif tier and any(x in w for x in ("entitled", "eligible")):
            if TIER_ORDER[t["minTier"]] > TIER_ORDER[tier]:
                problems.append(f"{name} = {n}: needs {t['minTier']}, above {tier}")

    # A plural name asking for "expected" titles in a territory should list every
    # title licensed there, not one of them.
    if "titles" in w and must:
        for terr in must:
            complete = {n for n, t in titles.items() if terr in t["territories"]}
            missing = complete - set(known)
            if missing:
                problems.append(
                    f"{name}: lists {len(known)} of {len(complete)} titles licensed "
                    f"in {terr}; missing {', '.join(sorted(missing))}")
    return problems


def main() -> int:
    if not VARS.exists():
        print("no variables file to verify")
        return 0

    titles = {t["name"]: t for t in json.loads(CATALOGUE.read_text())["titles"]}
    values = {k: v.get("value") for k, v in json.loads(VARS.read_text()).items()}
    today = datetime.date.today().isoformat()

    bad, checked = [], 0
    for name, value in values.items():
        if not value:
            continue
        found = check(name, value, titles, today)
        if found:
            bad.extend(found)
        if any(v.strip() in titles for v in str(value).split(",")):
            checked += 1

        # shape: a tier variable must hold a tier, a territory variable a territory
        w = words(name)
        kinds = {"tier": "tier", "plan": "tier", "territory": "territory",
                 "region": "territory", "market": "territory"}
        kind = next((kinds[t] for t in reversed(w) if t in kinds), None)
        if kind == "tier" and value not in TIERS:
            bad.append(f"{name} = {value}: not a subscription tier {list(TIERS)}")
        if kind == "territory" and value not in TERRITORIES:
            bad.append(f"{name} = {value}: not a territory {list(TERRITORIES)}")

    for on, ov in [(n, v) for n, v in values.items() if v and "old" in words(n)]:
        prefix = on.rsplit("old", 1)[0]
        for nn, nv in [(n, v) for n, v in values.items() if v and "new" in words(n)]:
            if nn.startswith(prefix) and ov == nv:
                bad.append(f"{on} and {nn} are both {ov}: a change test needs them to differ")

    if bad:
        print("variables that contradict the catalogue:")
        for b in bad:
            print(f"  {b}")
        return 1

    print(f"verified {checked} catalogue-derived value(s); all true of app/catalogue.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
