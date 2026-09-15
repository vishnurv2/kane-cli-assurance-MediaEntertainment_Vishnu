# Findings

What this pipeline actually surfaced, as opposed to what it was built to surface.

`CONFLICTS.md` lists five disagreements planted on purpose between the PRD and the
rights schedule. This file is for findings the run produced that nobody planted.

---

## F1 · R1 makes R4 unreachable

**Severity:** high · **Source:** `sources/prd-entitlement-playback.md` alone ·
**Status:** open, unresolved in the app

Three requirements in the PRD, read together, contradict each other.

| Ref | Line | What it says |
|---|---|---|
| R1 | 19 | Titles not licensed for the viewer's territory **are not shown** in the browse list. |
| R2 | 25 | Selecting a title **from the browse list** opens that title's detail page. |
| R4 | 37 | When the viewer's territory is not among the title's licensed territories, **Play does not start** and the reason is clearly indicated. |

R1 removes out-of-territory titles from the only surface R2 offers as a route to
a detail page. So there is no path to a detail page for a title the viewer is not
licensed for, and R4's blocked-playback state can never be reached by a viewer.

The app implements R4 faithfully - and the branch is dead:

```js
// app/app.js:182
function evaluate(title) {
  if (!title.territories.includes(territory())) {
    return {
      allowed: false,
      ground: "territory",
      message: "This title is not available in your region.",
    };
  }
```

Nothing in the UI can reach that return. `openDetail()` is called only from a
browse card or the hero, and both are filtered through `licensedHere()`
(`app/app.js:49`). Changing territory while on a detail page does not reach it
either - the `change` handler re-renders browse and navigates away.

**How it surfaced.** `design tests` produced
`block-playback-when-the-viewer-is-outside-the-licensed_test.md` from R4. Its
first step asks the runner to *"arrive at the selected title's detail page for a
viewer whose subscription tier includes the title but whose current territory is
outside the title's licensed territories."* No such page exists, so the test
cannot pass against a correct implementation of R1.

**Why it matters.** This is the failure mode the assurance lifecycle exists to
catch: two individually reasonable requirements that cannot both hold. It is
cheap to fix on paper and expensive to fix after a territory launch, and no test
suite written from R4 alone would ever have revealed it - the test passes or
fails on a page that was never reachable.

**Resolution options, for Product to choose between:**

1. R1 wins - delete R4. Out-of-territory titles are invisible, so there is no
   blocked state to indicate. Simplest, and loses the ability to say "not
   available in your region" at all.
2. R4 wins - relax R1 so out-of-territory titles appear in browse, marked
   unavailable. This is what most streaming services actually do, and it makes
   the territory-block message reachable and worth testing.
3. Add a route R1 does not govern - deep links, search, or a shared URL that can
   land a viewer on a title they cannot play. R4 then governs that entry point.

Option 2 or 3 also makes the licence-window rules in
`sources/rights-schedule-2026.md` expressible, since a "coming soon" title is by
definition one you can see but not play.

**Resolved in the document, not yet in the app.**
`sources/prd-entitlement-playback-v2.md` takes option 2: R1 is relaxed so an
unlicensed title is listed and marked unavailable rather than hidden, R4 is
restated to name the territory ground specifically, R7 requires the marking to
carry its reason, and R8 adds the licence-window rule that option 2 makes
expressible. The pipeline reconciles that revision against the live graph on
every run, so the design that was built from v1 is told it has gone stale.

The app still implements v1. That is deliberate: the gap between a revised
requirement and an unchanged build is exactly what the reconcile changeset is
supposed to surface.

---

## F2 · The rights schedule cannot be merged into the graph

**Severity:** blocking for the two-document demo · **Status:** raised, external

`context extract` lands `prd-entitlement-playback.md` cleanly (4 use-cases) and
then fails on `rights-schedule-2026.md`:

```
error: agent failed for rights-schedule-2026: CRITERIA_OPS_UNSUPPORTED:
n1: op-union updated.criteria (keep/set/remove) needs an extract@5+ binding
(this session is bound to an unversioned template)
```

Isolated: the rights schedule extracts fine **alone** in a clean graph
(2 use-cases). It only fails as the *second* source, where the agent must update
use-cases the PRD already created - which emits `updated.criteria` ops. Those
require the session's extract template to be `extract@5` or newer.

**Reproduced outside this repo.** An unrelated project on the same account, with
entirely different requirement documents, was run through the same two steps:
ingest and extract on one source succeeded, and extracting a second source into
the same graph failed with byte-identical text:

```
CRITERIA_OPS_UNSUPPORTED: n1: op-union updated.criteria (keep/set/remove)
needs an extract@5+ binding (this session is bound to an unversioned template)
```

So this is a property of the account's template binding, not of these documents.
The agent trace confirms the trigger: the failing run issues `read node` /
`context read` calls the first-source run never makes. Reading the existing nodes
is what produces the union ops the binding rejects.

This repo's premise is two sources merging into one graph, so the limit hits it
squarely. The workflow degrades honestly rather than dying: a partial extract
warns, continues with whatever extracted, and stamps a notice above the coverage
numbers saying they are scoped to one source.

**There is a way to avoid the code path, and it is not honest here.** Passing a
changed document through `maintain reconcile --source-id <existing>` moves that
source's head instead of landing a second source, so the union path is never
reached. That is the right move when the new document is a *version* of the old
one, and it is what `sources/prd-entitlement-playback-v2.md` does.

It is not available for the rights schedule. The PRD and the schedule are not
revisions of one another - they are two owners who disagree at the same moment in
time. Re-labelling one as a revision of the other would turn the pipeline green
by changing the claim from "two authorities contradict each other" to "a document
changed", which is weaker and untrue.

Session ids for support: `as-20260915T1122-hfwcdbca`, `as-20260915T1127-x6y4pb0k`,
and from the reference repo `as-20260915T1529-01v2nx1x`.

---

## F3 · Variables never reach the agent's objective text

**Severity:** blocks the proven axis · **Status:** open, ours to fix

Runs stall with `AP produced no action for 3 consecutive steps`. Observed across
every variable that can be controlled from this repo:

| Condition | Runs | Passed |
|---|---|---|
| First run, fresh authoring | 1 | 1 |
| Full suite | 8 | 0 |
| Original app markup restored | 2 | 0 |
| Deep-linked start URLs | 2 | 0 |
| Forced re-author (`--author`) | 1 | 0 |
| Accessible names + ambiguous variable fixed | 1 | 0 |
| Stable `data-testid` on every control | 1 | 0 |

The CLI's own verdict engine classifies every one of these as
`automation_bug` / `agent_misstep`, never a product defect - for example:

> The page loaded normally and showed a usable Territory control set to IN. To
> reach the requested GB browse list, the agent needed to select GB, but it
> produced no actions for three steps instead.

**This was initially recorded as a service-wide problem. That was wrong.** Two
unrelated projects were run on this same account on the same day and their tests
executed cleanly - one passed 2 of 3, another passed 4 of 4 first try. The string
`AP produced no action for 3 consecutive steps` does not appear anywhere in
either set of logs. Against one pass in nineteen here, on the same account and
the same CLI build.

The difference is the markup. That repo puts a stable `data-testid` on every
control, so the agent addresses elements by identifier. This app had none, so
the agent had to infer every control from visible text and layout - and the
failure mode is precisely an agent that cannot decide what to act on.

Stable `data-testid` hooks were added across the app (and a
`data-testid="title-card-<id>"` plus `data-title-name` on every browse card).
They are presentation only: no entitlement rule reads them, and a differential
run confirms behaviour is unchanged across all 9 viewer states × 6 titles.

**They did not fix it.** The next run stalled identically. So the markup
hypothesis is not the answer either, and the difference from the projects that pass
remains uncharacterised. Test ids are kept because they are good practice, not
because they helped.

**The cause.** Declared variables load into the run envelope but are never
interpolated into the objective and assertion text handed to the agent. The
agent is asked to act on a literal `{{placeholder}}`, has no target, emits
nothing, and trips the three-step guard.

Fourteen distinct agent-facing strings in our runs still carried raw
placeholders, including:

```
Open {{entitled_playback_start_url}} in the browser, arrive at the selected …
… assert the player opens and reports the same stored {{title_name}} as now playing.
… no title named in {{global.excluded_titles_for_gb}} is visible in the browse list …
```

Meanwhile `context.variables` in the same run shows the values present and
correct (`global.excluded_titles_for_gb = "Monsoon Avenue, The Last Signal"`),
and `navigate` actions *do* substitute properly. It is the objective path
specifically that does not.

**Reproduced independently.** A third unrelated project on this account stalled
with the same `reason_code: agent_error.ap_no_action`, and its verdict names the
mechanism outright:

> **Unresolved product variable leaves agent without a target** - The objective
> contains an unresolved placeholder instead of a real product name. The catalog
> has several choices, so the agent had no way to know which entry to open and
> did not take an action for three steps.

Its variable was loaded correctly too. Two unrelated projects, same account,
same failure, same named cause.

The corroborating case is the project that passed 2 of 3 on this account: its
step text carries literal values, no placeholders.

**Four earlier hypotheses were wrong** and are recorded here so nobody re-runs
them: a service-wide outage (another project passed 2/3 the same day), stale replay
artifacts (`--author` stalls too), missing `data-testid` (added 18, no change),
and state-versus-action step phrasing (the peer's action-phrased steps stalled
identically).

**Inlining the values is not sufficient here, because of a second defect.**

---

## F4 · The runner strips query strings from navigate targets

**Severity:** breaks URL-encoded test state · **Status:** open, external

A test whose step text contained a fully literal URL was run with every
placeholder already substituted. The CLI navigated to the URL with its query
string removed:

```
step text:      http://127.0.0.1:8080/?territory=GB&tier=Premium
recorded nav:   Navigate to http://127.0.0.1:8080
```

The app reads `location.search` on load, so the stripped query silently produced
the default IN/Free catalogue while the objective insisted the viewer was in GB
on Premium. Two of the three titles the step named are not licensed in IN and so
were not on screen. The agent had no valid target and stalled - the same
`ap_no_action` symptom, a completely different cause.

This matters beyond this repo: any test that encodes viewer or fixture state in
a query string will silently run against the wrong state. It also means the
`?territory=&tier=` deep links added earlier as an F3 mitigation cannot work
with this runner, and made matters worse by putting the test text and the actual
page state into disagreement.

The workable shape ought to be the one the passing projects use: a bare URL,
literal values in the step text, and explicit actions that drive the on-page
controls. That was tried - a hand-written test with a bare URL, literal values,
imperative steps, against markup carrying `data-testid` on every control. It
navigated successfully and then stalled again, at *"In the Territory dropdown
select GB"*.

**So neither F3 nor F4 is the whole story, and the remainder is unexplained.**
Nineteen runs, one pass. The one recurring detail across every stall is that the
agent stops at a native `<select>`: the first counterfactual stalled at
*"the agent needed to select GB"*, and so did the last. The passing peer's app
uses text inputs and buttons, not `<select>` elements. That is a pattern worth
testing, not a conclusion - five earlier hypotheses here looked at least this
good and were all disproved by evidence.

The project that passed 4/4 on this account first try carried unresolved
placeholders in its objectives too. The agent inferred the value from the page
and the assertion passed. So the placeholder defect is real but not on its own
sufficient to cause a stall.

**What is established:** the stall is not service-wide (three unrelated projects
ran on this account the same day: 2/3, 4/4 and a stall), not stale replay, not
missing test ids, not step phrasing, and not solely the placeholder defect. F3 and F4 are both real, independently
confirmed defects that our tests hit - they are simply not sufficient to explain
the remaining failures.

The coverage ribbon still reports real numbers, because the runs that did
complete sealed evidence:

```
designed  88% ·  19/21 ACs have a verifying test
proven    41% ·   7/21 ACs · 0 failing · 7 blocked · 7 not yet run
```

Per use-case: UC-3 is 100% designed and 100% proven, UC-1 is 67%/67%, and UC-2
and UC-4 are fully designed but 0% proven. **Nothing is failing** - the 14
unproven ACs are `blocked` or `not yet run`, which is precisely the signature of
an executor that stalls rather than a product that breaks.

That distinction is the point. A stalled run leaves an AC unproven, not failed,
and the ribbon says so.

Two mitigations are in the repo because they are good practice regardless:
`?territory=&tier=` deep links, so a test can open a known viewer state without
driving two dropdowns first; and browse cards whose accessible name is exactly
the title, so they can be addressed by name.
