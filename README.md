# Kane CLI Assurance · OTT Entitlement and Regional Rights

Media and Entertainment capstone. A requirements-to-evidence pipeline built on
`kane-cli` assurance, run in GitHub Actions, against an entitlement problem
where the requirements come from two owners who do not agree.

**Sector:** Media and Entertainment
**Target application:** StreamRights, a self-contained catalogue served on the
runner. No login, no deploy, no external dependency.

## Why entitlement rather than a catalogue search demo

A streaming service does not own a title everywhere. It licenses it per
territory, per tier, per window, and the terms live in a contract that Legal
signs rather than in a repository that Engineering owns. So "is this title
playable?" has no single correct answer, and "our tests pass" answers nothing
useful about it.

This is the shape of problem the assurance lifecycle exists for: the requirement
is a written rule, correct behaviour is conditional, and someone will eventually
ask you to prove which rules were verified and when.

## What makes this repo different

Two requirement documents go into a single `context ingest`:

- `sources/prd-entitlement-playback.md` - what Product specified
- `sources/rights-schedule-2026.md` - what Licensing actually committed to

They contradict each other in five places, deliberately. `CONFLICTS.md` lists
them. The app implements the PRD only, so tests designed from the schedule are
expected to fail, and that failure is the finding rather than a broken demo.

Both documents land, but only the PRD currently extracts: merging a second
source into the graph needs an `extract@5+` template binding this account does
not have (`FINDINGS.md` F2). The run reports that rather than hiding it, and
the finding it does produce - F1 - comes from the PRD alone, so the demo does
not depend on the second document.

Every run also renders the full assurance graph with `kane-cli context view` and
publishes it to GitHub Pages. That is a link you can send a prospect after a
call, instead of a CI artifact nobody will ever open.

## Setup

1. Push this to a GitHub repo.
2. Add two repository secrets under Settings → Secrets and variables → Actions:

   | Secret | Value |
   |---|---|
   | `LT_USERNAME` | TestMu AI username |
   | `LT_ACCESS_KEY` | Dashboard → Credentials |

3. Enable Pages: Settings → Pages → Source → GitHub Actions.
4. Actions → **Assurance · OTT Entitlement and Regional Rights** → Run workflow.

Pushing to `main` also triggers a run when `sources/`, `app/`, `scripts/` or the
workflow itself changes, so the first push runs the pipeline. Set the secrets and
enable Pages before pushing, or that run fails at authentication and the deploy
job has nowhere to publish.

Cost note: `context extract`, `design tests`, `testmd run` and
`maintain reconcile` call the service. Ingest, the checkpoints, `cover`,
`evidence` and `context view` are local and free. Test execution is the largest
line: **50-65 credits per test**, not the smaller figure the per-run field
reports. Budget 500-800 credits for a full run. `skip_design: true` skips design,
the variable fill and reconcile; no tests are minted, so nothing dispatches
either. That is the cheap way to exercise the rest of the pipeline end to end.

## The lifecycle, as this repo runs it

```
ingest (2 sources) → extract → checkpoint 1 → design tests → checkpoint 2
                                                                  ↓
                                                        fill test variables
                                                                  ↓
   graph → Pages ← evidence (merge + L1) ← reconcile ← cover gaps ← run tests
```

Both checkpoints are auto-approved in CI, and the verdict reason written into
the audit trail says so honestly. `scripts/approve.py` builds the verdict files
from the live graph rather than hardcoding ids, because node ids are not stable
between runs.

## Running it locally

```bash
npm install -g @testmuai/kane-cli
kane-cli login --username <user> --access-key <key>

python3 -m http.server 8080 --directory app &
kane-cli config set-url http://127.0.0.1:8080

# Name the two v1 sources. A glob would also pick up prd-...-v2.md, which is a
# revision rather than a third source and belongs to `maintain reconcile`.
kane-cli context ingest sources/prd-entitlement-playback.md \
  sources/rights-schedule-2026.md               # TTY drops you into extract chat
kane-cli context list --json --inferred
kane-cli design tests --use-case <ref> --max 6

# design writes .testmuai/variables/assurance.json with empty values, and
# testmd run refuses to dispatch until they are filled
python3 scripts/fill_variables.py --app-url http://127.0.0.1:8080
python3 scripts/verify_variables.py

kane-cli cover gaps
kane-cli maintain reconcile --from sources/prd-entitlement-playback-v2.md \
  --source-id prd-entitlement-playback --mode ci --plan
kane-cli context view --out site/index.html --no-open
```

Run every command from the repo root. That is where `.context/` lives.

## Demo narrative

1. Show both source documents. Ask which one the QA team was given. It is
   always the PRD.
2. Run ingest and extract. The PRD lands as use-cases, each citing a line range.
   The rights schedule does not - say why, out loud: merging a second source
   needs an `extract@5+` binding (`FINDINGS.md` F2). Being able to name the
   limit is worth more than pretending it isn't there.
3. Walk `FINDINGS.md` F1. The tool did not find bugs in the product. Reading one
   requirements document, it found a requirement that can never be exercised:
   R1 hides out-of-territory titles from browse, R2 makes browse the only route
   to a detail page, and R4 then specifies a blocked state on a page nobody can
   reach. Before anyone wrote code.
4. Show the coverage ribbon. Designed against proven, per requirement. Read the
   **0 failing** out loud: the gap between the two axes is blocked and not-yet-run,
   because the executor stalls (F3), not because the product failed. This is what
   replaces the traceability spreadsheet, and the two axes are the only reason
   that distinction is visible.
5. Open the published graph. Hand over the link.

## What this run actually found

`CONFLICTS.md` lists the five disagreements planted on purpose. `FINDINGS.md`
lists what the pipeline surfaced that nobody planted - chiefly **F1: R1 makes R4
unreachable**, a contradiction inside the PRD alone. R1 hides out-of-territory
titles from browse, R2 makes browse the only route to a detail page, and R4 then
specifies a blocked-playback state on a page no viewer can reach. The app
implements R4 faithfully and the branch is dead code.

That is the demo. Not "our tests pass" - a requirements defect found before
anyone wrote code, with the line cites to prove it.

## Current status, stated plainly

Two things are blocked outside this repo, and the run says so rather than hiding
them (see `FINDINGS.md` F2 and F3):

- **The rights schedule does not extract.** It needs an `extract@5+` template
  binding; this account is bound to an older one. A partial extract no longer
  kills the run - it warns, continues with what did extract, and stamps a notice
  above the coverage numbers saying they are scoped to one source.
- **Test execution stalls**, so the proven axis is partial. The most recent run
  reads **designed 90% (35/40 ACs) · proven 11% (4/40)** with **0 failing** - the
  rest are blocked or not yet run. Nothing is failing; the executor stops
  producing actions with `AP produced no action for 3 consecutive steps`. Those
  numbers are not worked around anywhere here.

  The design stage produces a different number of acceptance criteria each run,
  so the percentages are not comparable between runs. What is comparable: that
  run dispatched 17 tests and sealed 17 evidence packs, which merged into one
  validated bundle.

## Known limitations

Carried forward honestly from the upstream handbook, and worth saying on a call
rather than being caught by:

- Gap detection is a tendency, not a guarantee. Vague requirement wording can
  become a hard assertion instead of a question.
- A test can be tagged against several acceptance criteria while hard-checking
  only one. The rest ride on prose.
- Ids and risk grades are not stable between runs. Always read them from
  `context list --json`.

## Roadmap

Shipped since the first cut: **the drift loop**. `sources/prd-entitlement-playback-v2.md`
is a real revision of the PRD that resolves the R1/R4 contradiction in
`FINDINGS.md` F1 - it relaxes R1 so an unlicensed title is shown and marked
rather than hidden, which makes R4's block reason reachable and, in turn, makes
the licence-window rules expressible (R8). The pipeline runs
`maintain reconcile --from <v2> --source-id <v1>` on every execution whenever a
`-v2` source is present, so a requirement change lands as a reviewable changeset
against the live graph instead of silently diverging.

That closes the arc the whole repo is for: the tool found a requirements defect,
Product revised the requirement, and the suite is told it has gone stale.

Also shipped: the release evidence bundle. Every run now
pre-validates each sealed pack at L1, merges the eligible ones into a single
`release-<run-id>.evidence`, validates the merged bundle, and prints its
diagnostics into the job summary. Merging is the only check that compares packs
against one another - it caught a `l1.failure.status_disagrees` that per-pack
validation cannot see. Collisions abort loudly rather than being discarded,
because `--on-collision discard` resolves them by deleting the contested test
from the bundle.

Not in this cut, sequenced next:

- **Reconcile-on-PR gate.** The reconcile stage runs on every execution; the
  remaining step is to run it on pull requests touching `sources/` and post the
  changeset as a review comment, so drift is caught at review time rather than
  after merge.
