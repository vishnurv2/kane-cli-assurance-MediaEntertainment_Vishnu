# Demo script

Fifteen minutes, live terminal, no slides. The payload is `FINDINGS.md` F1: a
requirement that can never be exercised, found by reading one document, before
anyone wrote code.

Read `FINDINGS.md` before you run this. If you cannot explain F1 in your own
words you will not survive the questions in the last section.

## Before the call

```bash
kane-cli whoami                       # expect: Authenticated
kane-cli balance                      # a design pass costs a few hundred credits
python3 -m http.server 8080 --directory app &
kane-cli config set-url http://127.0.0.1:8080
```

Have three things open and ready: `sources/prd-entitlement-playback.md`,
`sources/rights-schedule-2026.md`, and a browser on `http://127.0.0.1:8080`.

If you are demoing a graph that already exists, skip the run and walk the
artifacts - `scripts/demo.sh` drives the whole sequence with pauses if you would
rather not type.

---

## 1 · The problem, in their language (90 seconds)

Do not open a terminal yet. Open the two documents side by side.

> "A streaming service does not own a title everywhere. It licenses it per
> territory, per tier, per window - and the terms live in a contract Legal signs,
> not in a repo Engineering owns."

Point at `sources/prd-entitlement-playback.md`, then at
`sources/rights-schedule-2026.md`.

> "Product wrote this one. Licensing committed to that one. Which of them did
> your QA team get?"

It is always the PRD. Let them say it.

> "So 'is this title playable?' has no single right answer, and 'our tests pass'
> answers nothing useful about it."

That is the whole pitch. Everything after this is proof.

## 2 · Ingest and extract (2 minutes)

```bash
kane-cli context ingest sources/prd-entitlement-playback.md \
    sources/rights-schedule-2026.md --mode ci
kane-cli context extract --mode ci
```

The PRD lands as four use-cases, each citing a line range. The rights schedule
does not land - you will see:

```
CRITERIA_OPS_UNSUPPORTED: needs an extract@5+ binding
```

**Say this out loud. Do not talk over it.**

> "That is a real limit and I am not going to pretend it isn't there. Merging a
> second source into an existing graph needs a newer prompt template than this
> account is bound to. It is raised with the team, and the session ids are in
> the repo."

Two reasons this helps rather than hurts. A prospect who has sat through vendor
demos knows when something is being steered around, and naming a limit before
they find it is the cheapest credibility you will ever buy. And the finding you
are about to show them does not need the second document at all.

## 3 · The graph (90 seconds)

```bash
kane-cli context list --json --inferred | head
kane-cli context view --out site/index.html --no-open && open site/index.html
```

```
2 sources · 4 use-cases · 21 acceptance criteria · 8 scenarios · 8 tests · 9 gaps
```

> "Every node cites the line it came from. This is the traceability spreadsheet
> nobody maintains, except it builds itself and it is queryable."

Pick any node and show its lineage:

```bash
kane-cli context explain uc-1
```

> "No model call. It is replaying what it recorded when it made the decision."

## 4 · The finding (4 minutes - this is the demo)

This is the beat everything else exists to set up. Slow down.

Open `sources/prd-entitlement-playback.md` and read three requirements aloud, in
this order:

| Ref | Line | What it says |
|---|---|---|
| R1 | 19 | Titles not licensed for the viewer's territory **are not shown** in browse. |
| R2 | 25 | Selecting a title **from the browse list** opens its detail page. |
| R4 | 37 | Outside the licensed territory, **Play does not start** and the reason is indicated. |

Then ask the question and wait. Do not fill the silence.

> "R1 hides the title. R2 says the browse list is how you reach a detail page.
> So how does a viewer ever get to the page where R4 happens?"

They cannot. Let that land, then show it is not theoretical - open `app/app.js` at line 182:

```js
function evaluate(title) {
  if (!title.territories.includes(territory())) {
    return {
      allowed: false,
      ground: "territory",
      message: "This title is not available in your region.",
    };
```

> "The engineer implemented R4 correctly. It is dead code. Nothing in the product
> can reach it - and no test suite written from R4 would have told you, because
> the test passes or fails on a page that was never reachable."

Now the commercial framing, which is the part they repeat to their boss:

> "Three individually reasonable requirements, signed off, that cannot all hold.
> Cheap to fix in a document. Expensive to find after a territory launch. This
> was found before anyone wrote a line of code."

`FINDINGS.md` has three resolution options if they ask what to do about it - most
streaming services take option 2, showing the title marked unavailable.

## 5 · Coverage, honestly (2 minutes)

```bash
kane-cli cover gaps
```

```
designed  88% █████████░  19/21 ACs have a verifying test
proven    41% ████░░░░░░   7/21 · 0 failing · 7 blocked · 7 not yet run

UC-3  Change territory and refresh…   100% designed   100% proven
UC-1  Start playback for an entitled…  67% designed    67% proven
UC-2  Browse the catalogue…           100% designed     0% proven
UC-4  View a title's availability     100% designed     0% proven
```

Read the **0 failing** out loud. It is the most important number on screen:

> "Nothing is failing. The gap between 88% designed and 41% proven is *blocked*
> and *not yet run* - the executor stalls on this build, which is an automation
> problem I've raised and documented in FINDINGS.md F3. That is a completely
> different statement from 'the product is broken', and this ribbon is the only
> artifact in the room that can tell the two apart."

That is the argument for a two-axis ribbon in one breath: a single coverage
percentage would have buried the distinction.

If you have the reference evidence pack, show it here:

```bash
kane-cli evidence validate <pack> --profile L1
```

> "When a run does complete, this is what it produces: a sealed pack that says
> what was proven, by which run, against which requirement."

## 6 · The loop closes (3 minutes - the strongest beat)

Sections 1-5 show a defect found before code. This shows what happens when
someone acts on it.

> "Product read that finding and revised the PRD. R1 now shows unlicensed titles
> marked unavailable instead of hiding them - which makes the block reason in R4
> reachable, and makes the licence-window rule writable for the first time. One
> requirements defect had been blocking the entire windows conversation."

Show `sources/prd-entitlement-playback-v2.md`, then run:

```bash
kane-cli maintain reconcile \
  --from sources/prd-entitlement-playback-v2.md \
  --source-id prd-entitlement-playback --mode ci --plan
```

```
head versioned - sha256:8d3ab0dd540c → sha256:06cba50d1f23

changeset: 3 item(s)
  [MODIFY] UC-1 - updated: description, summary, value, criteria (staged)
  [MODIFY] UC-2 - updated: description, summary, value, criteria (staged)
  [MODIFY] UC-3 - updated: description, summary, criteria (staged)

plan: 5 row(s)
  [ADD]    AC-5 - no live test verifies this acceptance criterion
           action: kane-cli design tests --use-case uc-1
  [MODIFY] UC-1 - impact: approving marks 10 item(s) stale
  [MODIFY] UC-2 - impact: approving marks 10 item(s) stale
  [MODIFY] UC-3 - impact: approving marks  7 item(s) stale
```

Land the three numbers, in this order:

> "**Twenty-seven items go stale.** Not 'some tests might need looking at' -
> twenty-seven, named, each traced to the source line that changed. **Two new
> acceptance criteria** appeared with no test covering them, and it tells you the
> command to fix that. And **nothing committed** - it is staged behind a verdict,
> because a document changing is not the same as a team agreeing."

Then the question that sells it:

> "How long does it currently take you to answer 'the PRD changed on Tuesday -
> what does that invalidate?'"

Everyone's honest answer is a person reading a spreadsheet, or nobody asking.

## 7 · The hand-off (60 seconds)

```bash
open site/index.html
```

> "Every run publishes this to Pages. That is a link you send after the call -
> not a CI artifact nobody opens."

Close on the sentence worth rehearsing:

> "The tool did not find bugs in the product. It found a requirement that could
> never be satisfied, and it found it before anyone wrote code."

---

## Questions you will get

**"Did you plant that finding?"**
No - and the repo proves it. `CONFLICTS.md` lists five conflicts that *were*
planted, between the PRD and the rights schedule. F1 is none of them. It is
internal to the PRD, and it surfaced because `design tests` generated a test for
R4 that describes a page the product cannot produce.

**"Why is proven coverage zero?"**
Answered in section 5. Do not improvise a better number.

**"Couldn't a careful human reviewer have caught R1 versus R4?"**
Yes. So could a careful reviewer catch most bugs. The question is whether one
does, on every document, every release, under deadline - and whether you can
prove afterwards which rules were checked and when. That record is the product.

**"What happens when the requirements change?"**
`maintain reconcile` re-reads a changed source and reports the changeset against
the live graph. Not wired into this pipeline yet; it is in the README roadmap.
Do not demo what is not built.

**"How much does a run cost?"**
Ingest, list, view, cover and the checkpoints are local and free. Extract, design
and test execution call the service. A full pass on this repo is a few hundred
credits; `kane-cli balance` is the honest answer to give live.

**"Is this just Playwright with an LLM on top?"**
The test execution is the least interesting part. Nothing in a Playwright suite
tells you that R1 and R4 cannot both hold. The graph is the product; the runner
is a consumer of it.

## What not to claim

- Do not say the graph holds claims from both documents. Today it does not.
- Do not present the five planted conflicts as something the pipeline
  demonstrates on its own right now. They are a design artifact until the
  extract binding is resolved.
- Do not imply the proven axis is zero because the product is broken.
- Do not quote a coverage percentage. Quote the two axes.
