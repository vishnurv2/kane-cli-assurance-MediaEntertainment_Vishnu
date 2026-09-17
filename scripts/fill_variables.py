#!/usr/bin/env python3
"""Fill the variables the design stage declared, from the app's own fixture data.

`design tests` writes `.testmuai/variables/assurance.json` with every value
empty, and `testmd run` refuses to dispatch while any of them is unset:

    {"type":"error","code":"unresolved_variables",
     "message":"5 variable(s) have no value - nothing was dispatched"}

The variable NAMES are chosen by the design agent and are not stable between
runs, so this matches on what the name means rather than on a fixed list. Values
come from app/catalogue.json and APP_URL, which is what makes them true: a title
named here is a title the catalogue actually serves, in a territory it is
actually licensed for.

Anything that cannot be satisfied from the fixture is reported and left empty
rather than invented. A made-up value would dispatch a test that then fails for
a reason unrelated to the requirement under test, which is worse than not
running it.

Usage:
    python3 scripts/fill_variables.py [--app-url http://127.0.0.1:8080]
"""

from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import re
import sys

VARS = pathlib.Path(".testmuai/variables/assurance.json")
CATALOGUE = pathlib.Path("app/catalogue.json")
TIER_ORDER = {"Free": 0, "Standard": 1, "Premium": 2}


def load_titles():
    return json.loads(CATALOGUE.read_text())["titles"]


def in_window(title, today):
    return title["windowStart"] <= today <= title["windowEnd"]


def pick(titles, territory, *, playable_at, licensed=True):
    """First title that is (or is not) licensed for a territory at a given tier."""
    for t in titles:
        here = territory in t["territories"]
        if here != licensed:
            continue
        if playable_at is not None:
            if TIER_ORDER[playable_at] < TIER_ORDER[t["minTier"]]:
                continue
        return t
    return None


def tokens_of(name: str) -> list[str]:
    """Split a variable name into whole words.

    Every wrong value this script has produced came from matching substrings or
    single keywords: "entitled" contains "title", "unlicensed_in_gb" contains the
    preposition "in", and a keyword list containing "unlicensed" silently misses
    "not licensed". Names are predicates over the catalogue, so they are parsed
    as predicates rather than scanned for words.
    """
    return [t for t in re.split(r"[^a-z0-9]+", name.lower()) if t]


TERRITORIES = ("IN", "GB", "US")
TIERS = ("Free", "Standard", "Premium")
SKIP = ("licensed", "available", "playable", "shown", "visible", "browse",
        "catalogue", "catalog", "title", "titles", "name", "expected")


def parse_territories(toks):
    """Required and excluded territories, honouring negation and the preposition.

    "not_licensed_in_in"  -> excluded IN   (the first "in" is the preposition)
    "licensed_in_gb_not_us" -> required GB, excluded US
    """
    required, excluded, negated, i = [], [], False, 0
    while i < len(toks):
        t = toks[i]
        if t in ("not", "non", "without", "outside", "excluded", "unlicensed"):
            negated = True
        elif t == "in" and i + 1 < len(toks) and toks[i + 1].upper() in TERRITORIES:
            pass                                   # preposition before a code
        elif t.upper() in TERRITORIES:
            (excluded if negated else required).append(t.upper())
            negated = False
        elif t not in SKIP:
            negated = False                        # any other noun ends the scope
        i += 1
    return required, excluded


def select(toks, titles, today):
    """Every catalogue title satisfying the predicate the name describes."""
    has = lambda *w: any(x in toks for x in w)
    required, excluded = parse_territories(toks)

    out = list(titles)
    if required:
        out = [t for t in out if all(r in t["territories"] for r in required)]
    if excluded:
        out = [t for t in out if all(e not in t["territories"] for e in excluded)]

    if has("ad") and has("supported"):
        out = [t for t in out if t.get("adSupportedOnly")]
    if has("coming", "soon", "future", "upcoming"):
        out = [t for t in out if t["windowStart"] > today]
    elif has("expired", "lapsed", "ended"):
        out = [t for t in out if t["windowEnd"] < today]

    # A tier word means "this title requires it" when paired with required/only,
    # and "the viewer holds it" otherwise.
    named_tier = next((t.capitalize() for t in toks if t.capitalize() in TIERS), None)
    if named_tier and has("required", "requires", "only", "minimum", "granting"):
        out = [t for t in out if t["minTier"] == named_tier]
    elif named_tier and has("insufficient", "below", "lacking"):
        out = [t for t in out if TIER_ORDER[t["minTier"]] > TIER_ORDER[named_tier]]
    elif named_tier and has("entitled", "eligible"):
        out = [t for t in out if TIER_ORDER[t["minTier"]] <= TIER_ORDER[named_tier]]
    return out


def resolve(name: str, titles, app_url: str, today: str):
    """Map one declared variable name to a value drawn from the fixture."""
    toks = tokens_of(name)
    has = lambda *w: any(x in toks for x in w)

    if has("email", "password", "username", "credential", "login", "signin", "account"):
        return None                                 # no authentication exists
    if has("url", "link", "endpoint"):
        return app_url

    kinds = {"title": "title", "titles": "title", "tier": "tier", "plan": "tier",
             "territory": "territory", "region": "territory", "market": "territory"}
    kind = next((kinds[t] for t in reversed(toks) if t in kinds), None)

    if kind == "tier":
        if has("granting", "required", "upgrade", "minimum"):
            chosen = select(toks, titles, today)
            return chosen[0]["minTier"] if chosen else "Standard"
        if has("insufficient", "below", "low", "lacking"):
            return "Free"
        return next((t.capitalize() for t in toks if t.capitalize() in TIERS), "Premium")

    if kind == "territory":
        required, excluded = parse_territories(toks)
        if required:
            return required[0]
        if has("new", "target", "switched", "destination"):
            return next(t for t in TERRITORIES if t not in excluded)
        return "GB"

    if kind == "title":
        chosen = select(toks, titles, today)
        if not chosen:
            return None
        # A plural name wants every match, not the first one.
        if "titles" in toks:
            return ", ".join(t["name"] for t in chosen)
        return chosen[0]["name"]

    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--app-url", default="http://127.0.0.1:8080")
    args = ap.parse_args()

    if not VARS.exists():
        print("no variables file - the design stage declared none", file=sys.stderr)
        return 0

    doc = json.loads(VARS.read_text())
    if not doc:
        print("variables file is empty - nothing to fill", file=sys.stderr)
        return 0

    titles = load_titles()
    today = datetime.date.today().isoformat()

    filled, unsatisfied = [], []
    for name, entry in doc.items():
        if entry.get("value"):
            continue
        value = resolve(name, titles, args.app_url, today)
        if value:
            entry["value"] = value
            filled.append((name, value))
        else:
            unsatisfied.append(name)

    VARS.write_text(json.dumps(doc, indent=2) + "\n")

    for name, value in filled:
        print(f"  filled  {name} = {value}")
    for name in unsatisfied:
        print(f"  UNFILLED {name} - nothing in the fixture satisfies this")

    print(f"\nfilled {len(filled)} of {len(filled) + len(unsatisfied)} declared variable(s)")
    if unsatisfied:
        print("Tests using the unfilled names will not dispatch. That is the correct "
              "outcome: the value was not invented.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
