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


def _wants_title(n: str) -> bool:
    """True when the name asks for a catalogue title, not merely contains 'title'.

    "entitled_viewer_email" contains the substring "title" without asking for
    one, so look for the word used as a noun instead.
    """
    return ("title_name" in n or n.endswith("_title") or n.startswith("title_")
            or "_title_" in n or "titles" in n)


def resolve(name: str, titles, app_url: str, today: str):
    """Map one declared variable name to a value drawn from the fixture."""
    n = name.lower()
    # Substring matching has to be ordered carefully: "entitled" contains
    # "title", and "below_tier" contains "tier", so the specific cases are
    # tested before the general ones.

    # The catalogue has no authentication, so nothing in the fixture can supply
    # a credential. Refuse rather than invent one.
    if any(w in n for w in ("email", "password", "username", "credential",
                            "login", "signin", "sign_in", "account")):
        return None

    if "url" in n or n.endswith("_link"):
        return app_url

    # territory / tier selections
    if "territory" in n and not any(w in n for w in ("title", "blocked", "excluded")):
        return "GB"
    if ("tier" in n or "plan" in n) and not _wants_title(n):
        if "upgrade" in n or "required" in n:
            # must agree with whatever title the below-tier case selects, or the
            # test asserts an upgrade path to a tier that title never needed
            t = next((x for x in titles
                      if "GB" in x["territories"] and x["minTier"] == "Premium"), None)
            return t["minTier"] if t else "Premium"
        if "below" in n or "low" in n:
            return "Free"
        return "Premium"

    # title names, qualified by the situation the test needs
    if _wants_title(n):
        if "blocked" in n or "outside" in n or "unlicensed" in n:
            t = pick(titles, "IN", playable_at=None, licensed=False)
        elif "below" in n or "upgrade" in n or "higher" in n:
            t = next((x for x in titles
                      if "GB" in x["territories"] and x["minTier"] == "Premium"), None)
        elif "expired" in n:
            t = next((x for x in titles if x["windowEnd"] < today), None)
        elif "future" in n or "coming" in n:
            t = next((x for x in titles if x["windowStart"] > today), None)
        else:
            t = pick(titles, "GB", playable_at="Premium")
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
