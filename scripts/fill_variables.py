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

    Every wrong value this script has produced came from substring matching:
    "entitled" contains "title", "below_tier" contains "tier", and
    "unlicensed_in_gb" contains the preposition "in". Tokens remove that whole
    class of error, so nothing below may use `in` on the raw string.
    """
    return [t for t in re.split(r"[^a-z0-9]+", name.lower()) if t]


TERRITORIES = ("IN", "GB", "US")


def territory_in(toks: list[str], default="GB", *, avoid=None):
    """The territory a name asks about: the last whole territory token."""
    codes = [t.upper() for t in toks if t.upper() in TERRITORIES]
    if codes:
        return codes[-1]
    # A "new" territory must differ from the "old" one or a territory-change
    # test proves nothing, so allow the caller to exclude one.
    if avoid:
        return next(t for t in TERRITORIES if t != avoid)
    return default


def title_for(toks, titles, terr, today):
    """A title from the fixture that genuinely matches the situation named."""
    has = lambda *w: any(t in toks for t in w)

    if has("unlicensed", "blocked", "outside", "excluded"):
        return pick(titles, terr, playable_at=None, licensed=False)
    if has("expired"):
        return next((x for x in titles
                     if x["windowEnd"] < today and terr in x["territories"]), None)
    if has("future", "coming", "upcoming"):
        return next((x for x in titles
                     if x["windowStart"] > today and terr in x["territories"]), None)
    if has("insufficient", "below", "upgrade", "higher"):
        # licensed here, but needs more than Free, so a Free viewer is blocked
        return next((x for x in titles
                     if terr in x["territories"]
                     and TIER_ORDER[x["minTier"]] > TIER_ORDER["Free"]), None)
    return pick(titles, terr, playable_at="Premium")


def resolve(name: str, titles, app_url: str, today: str):
    """Map one declared variable name to a value drawn from the fixture."""
    toks = tokens_of(name)
    has = lambda *w: any(t in toks for t in w)

    # No authentication exists, so no credential can be true. Refuse.
    if has("email", "password", "username", "credential", "login", "signin", "account"):
        return None

    if has("url", "link", "endpoint"):
        return app_url

    # With tokens, "entitled_viewer_email" yields [entitled, viewer, email] and
    # never contains a "title" token, so the substring guard that used to be
    # needed here would now only do harm: it would reject entitled_title, which
    # plainly does want a title.
    #
    # Several names carry two type nouns: insufficient_tier_territory wants a
    # territory, territory_blocked_viewer_tier wants a tier. The LAST type noun
    # is the one being asked for; earlier ones qualify the situation.
    kinds = {"title": "title", "titles": "title",
             "tier": "tier", "plan": "tier",
             "territory": "territory", "region": "territory", "market": "territory"}
    last_kind = next((kinds[t] for t in reversed(toks) if t in kinds), None)
    wants_title = last_kind == "title"
    wants_territory = last_kind == "territory"
    wants_tier = last_kind == "tier"

    if wants_tier:
        terr = territory_in(toks)
        subject = title_for(toks, titles, terr, today)
        if has("granting", "required", "upgrade", "minimum"):
            # the tier that would grant access to the very title chosen above
            return subject["minTier"] if subject else "Standard"
        if has("insufficient", "below", "low", "lacking"):
            # the viewer's tier, which must be BELOW what the title requires
            return "Free"
        return "Premium"

    if wants_territory and not wants_title:
        if has("new", "target", "switched", "destination"):
            return territory_in(toks, avoid=territory_in(toks, default="GB"))
        return territory_in(toks)

    if wants_title:
        t = title_for(toks, titles, territory_in(toks), today)
        return t["name"] if t else None

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
