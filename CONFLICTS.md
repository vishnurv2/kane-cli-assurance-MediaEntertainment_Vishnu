# The conflicts, on purpose

Two documents go into `context ingest`. They do not agree. That disagreement is
the demo.

> **Status - read before demoing this file.** The disagreements below are real
> and the documents are in `sources/`, but the graph cannot currently hold both:
> `context extract` lands the PRD and fails on the rights schedule, because
> merging a second source needs an `extract@5+` template binding this account
> does not have. See `FINDINGS.md` F2. Until that is resolved the conflicts
> below are a *design* artifact, not something the pipeline demonstrates on its
> own. The finding to demo today is `FINDINGS.md` F1, which comes from the PRD
> alone.

A PRD alone produces a tidy extraction and a tidy suite, which proves nothing a
prospect cares about. Real requirements arrive from more than one owner, and the
owners contradict each other. The assurance graph is the only artifact in the
room that makes that visible before a release rather than after one.

## Where they disagree

| # | PRD says | Rights schedule says | What it does to the graph |
|---|---|---|---|
| 1 | R1: titles not licensed for the territory are not shown | T2: pre-window titles must be shown, marked coming soon | Direct contradiction on browse visibility. Extraction has to surface both claims rather than silently pick one. |
| 2 | R3: licensed territory plus correct tier means playable | T1: the grant only exists inside its window | The PRD has no concept of time. An entire dimension of the entitlement rule is missing from the product document. |
| 3 | R5: a higher tier is what blocks access | T4: some grants are ad-supported only, so a higher tier removes access | Tier is assumed monotonic in the PRD. It is not. Premium viewers lose titles Free viewers keep. |
| 4 | R4: the reason is "clearly indicated" | T5: the specific ground must be named | Vague requirement language against a precise obligation. |
| 5 | R6: territory changes re-evaluate the browse list | T6: territory is evaluated at play time, not browse time | Two different evaluation points for the same rule. |

## What to say when you run it

The coverage ribbon after a first pass shows designed against proven. The
interesting number is not the percentage. It is that requirements 1, 3 and 5
above cannot both be satisfied, and the graph says so with a citation to each
source line rather than an opinion.

(With the extract binding as it stands, say this about `FINDINGS.md` F1 instead:
the same sentence holds, sourced from one document rather than two.)

That is the sentence worth rehearsing: **the tool did not find bugs in the
product, it found a disagreement between two documents that both claim
authority, and it found it before anyone wrote code.**

## Honest caveat

Gap detection is a tendency, not a guarantee. Vague words like "clearly
indicated" in R4 can be turned into hard assertions by the design stage instead
of raising a question. Conflict 4 is in this list precisely because it is the
one most likely to pass silently. If it does, say so on the call. Claiming the
tool catches every ambiguity is how a technical win turns into a churn
conversation six months later.

## The app implements the PRD only

`app/` is built to the PRD, not the schedule. Window rules, coming soon
placement and ad-supported-only grants are deliberately absent from the
implementation. Tests designed from the schedule are expected to fail. That
failure is the finding, not a broken demo.
