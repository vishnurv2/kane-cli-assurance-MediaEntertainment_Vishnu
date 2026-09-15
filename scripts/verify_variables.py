#!/usr/bin/env python3
"""Assert that every filled variable is TRUE of the catalogue it came from.

The filler resolves names by meaning, and a wrong guess is worse than an empty
value: it dispatches a test that then fails for a reason unrelated to the
requirement under test. Two such bugs were shipped before this check existed -
"entitled_viewer_email" matching the title branch because "entitled" contains
"title", and "unlicensed_in_gb" resolving to IN because the name contains the
preposition "in". Both produced confident, wrong values.

Run after fill_variables.py. Exits non-zero if any filled value contradicts
app/catalogue.json.
"""

from __future__ import annotations

import datetime
import json
import pathlib
import sys

VARS = pathlib.Path(".testmuai/variables/assurance.json")
CATALOGUE = pathlib.Path("app/catalogue.json")


def main() -> int:
    if not VARS.exists():
        print("no variables file to verify")
        return 0

    titles = {t["name"]: t for t in json.loads(CATALOGUE.read_text())["titles"]}
    values = {k: v.get("value") for k, v in json.loads(VARS.read_text()).items()}
    today = datetime.date.today().isoformat()

    bad = []
    for name, value in values.items():
        if not value or value not in titles:
            continue
        t = titles[value]
        n = name.lower()
        codes = [x.upper() for x in n.replace("-", "_").split("_") if x in ("in", "gb", "us")]
        terr = codes[-1] if codes else None

        if terr and any(w in n for w in ("unlicensed", "blocked", "outside", "excluded")):
            if terr in t["territories"]:
                bad.append(f"{name} = {value}: licensed in {terr} ({t['territories']})")
        elif terr and "below" in n and "tier" in n:
            if terr not in t["territories"] or t["minTier"] == "Free":
                bad.append(f"{name} = {value}: not a below-tier case in {terr}")
        elif "expired" in n and t["windowEnd"] >= today:
            bad.append(f"{name} = {value}: window ends {t['windowEnd']}, not expired")
        elif ("future" in n or "coming" in n) and t["windowStart"] <= today:
            bad.append(f"{name} = {value}: window opened {t['windowStart']}, not future")

    # Structural check: a name whose last type noun is "tier" must hold a tier,
    # and one ending in "territory" must hold a territory. A tier variable that
    # was handed "GB" shipped once, and reads plausibly in a log.
    import re as _re
    TIERS = {"Free", "Standard", "Premium"}
    TERRS = {"IN", "GB", "US"}
    kinds = {"title": "title", "titles": "title", "tier": "tier", "plan": "tier",
             "territory": "territory", "region": "territory", "market": "territory"}
    for name, value in values.items():
        if not value:
            continue
        toks = [t for t in _re.split(r"[^a-z0-9]+", name.lower()) if t]
        kind = next((kinds[t] for t in reversed(toks) if t in kinds), None)
        if kind == "tier" and value not in TIERS:
            bad.append(f"{name} = {value}: not a subscription tier {sorted(TIERS)}")
        elif kind == "territory" and value not in TERRS:
            bad.append(f"{name} = {value}: not a territory {sorted(TERRS)}")
        elif kind == "title" and value not in titles and value not in TIERS | TERRS:
            pass  # a list of titles, or a name the fixture does not carry

    # old and new territory must differ or a change test proves nothing
    olds = {n: v for n, v in values.items() if v and "old" in n.split("_")}
    news = {n: v for n, v in values.items() if v and "new" in n.split("_")}
    for on, ov in olds.items():
        prefix = on.rsplit("old", 1)[0]
        for nn, nv in news.items():
            if nn.startswith(prefix) and ov == nv:
                bad.append(f"{on} and {nn} are both {ov}: a change test needs them to differ")

    if bad:
        print("variables that contradict the catalogue:")
        for b in bad:
            print(f"  {b}")
        return 1

    checked = sum(1 for v in values.values() if v and v in titles)
    print(f"verified {checked} catalogue-derived value(s); all true of app/catalogue.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
